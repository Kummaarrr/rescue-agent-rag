"""Claude access: structured outputs, token + cost accounting, and an on-disk response cache.

One small interface for the rest of the code base, so other providers can be plugged in later.
The cache keys on the full request, so re-running an unchanged step costs nothing; it also keeps
development runs comparable, since the API no longer accepts sampling parameters like temperature.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from dataclasses import dataclass, field
from functools import cache
from typing import Any, Literal

import anthropic
import yaml
from pydantic import BaseModel

from rescue_rag.config import CONFIG_DIR, project_path

Effort = Literal["low", "medium", "high", "xhigh", "max"]

CACHE_DIR = project_path("data/cache/llm")
# Server-side refusal fallback: supported on Opus 5.5 / Sonnet 5.5, not on Haiku.
FALLBACK_MODELS = {"claude-opus-5-5", "claude-sonnet-5-5"}
FALLBACK_BETA = "server-side-fallback-2026-07-01"


class LLMRefusal(RuntimeError):
    pass


@dataclass
class Ledger:
    """Running token and cost totals for a process (e.g. one eval run)."""

    calls: int = 0
    cached_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    by_model: dict[str, float] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def add(self, model: str, usage: dict[str, int], cached: bool) -> None:
        with self._lock:
            self.calls += 1
            if cached:
                self.cached_calls += 1
                return
            cost = price(model, usage)
            self.input_tokens += usage.get("input_tokens", 0)
            self.output_tokens += usage.get("output_tokens", 0)
            self.cost_usd += cost
            self.by_model[model] = self.by_model.get(model, 0.0) + cost

    def summary(self) -> str:
        return (
            f"{self.calls} calls ({self.cached_calls} cached), "
            f"{self.input_tokens:,} in / {self.output_tokens:,} out tokens, ${self.cost_usd:.4f}"
        )


LEDGER = Ledger()


@cache
def _prices() -> dict[str, dict[str, float]]:
    with (CONFIG_DIR / "prices.yaml").open(encoding="utf-8") as f:
        prices: dict[str, dict[str, float]] = yaml.safe_load(f)["models"]
    return prices


def price(model: str, usage: dict[str, int]) -> float:
    p = _prices().get(model)
    if p is None:
        raise KeyError(f"No price for {model} in config/prices.yaml")
    per = 1e6
    return (
        usage.get("input_tokens", 0) * p["input"] / per
        + usage.get("cache_creation_input_tokens", 0) * p["input"] * 1.25 / per
        + usage.get("cache_read_input_tokens", 0) * p.get("cache_read", p["input"] * 0.1) / per
        + usage.get("output_tokens", 0) * p["output"] / per
    )


def _client_for(api_key: str | None) -> anthropic.Anthropic:
    """The shared client, or a short-lived one for a caller-supplied key. Deliberately not
    memoised: a cache here would keep visitors' keys in memory."""
    return client() if api_key is None else anthropic.Anthropic(api_key=api_key, max_retries=2)


@cache
def client() -> anthropic.Anthropic:
    return anthropic.Anthropic(max_retries=4)


_NAMESPACE = ""


def set_cache_namespace(namespace: str) -> None:
    """Independent repeats: a non-empty namespace gives every call a fresh cache entry, so a
    repeated run gets new answers instead of replaying the first run. "" = the shared cache."""
    global _NAMESPACE
    _NAMESPACE = namespace


def _cache_key(payload: dict[str, Any]) -> str:
    if _NAMESPACE:
        payload = {**payload, "_namespace": _NAMESPACE}
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:32]


def parse[T: BaseModel](
    model: str,
    prompt: str,
    schema: type[T],
    *,
    system: str | None = None,
    effort: Effort = "medium",
    max_tokens: int = 16000,
    use_cache: bool = True,
) -> T:
    """One structured-output call. Returns a validated instance of `schema`."""
    return parse_full(
        model, prompt, schema, system=system, effort=effort, max_tokens=max_tokens,
        use_cache=use_cache,
    )[0]  # fmt: skip


@dataclass(frozen=True)
class CallInfo:
    model: str
    usage: dict[str, int]
    cost_usd: float  # list price, also for cache hits
    latency_s: float  # of the original API call (0.0 for cache records made before it was kept)
    cached: bool


def parse_full[T: BaseModel](
    model: str,
    prompt: str,
    schema: type[T],
    *,
    system: str | None = None,
    effort: Effort = "medium",
    max_tokens: int = 16000,
    use_cache: bool = True,
    api_key: str | None = None,
) -> tuple[T, CallInfo]:
    """Structured-output call plus usage, cost and latency (for pipelines that report them).

    api_key: a caller-supplied key (demo "bring your own key"). Such calls never read or write
    the on-disk cache and use a client that lives only for this call."""
    use_cache = use_cache and api_key is None
    payload = {
        "model": model,
        "system": system,
        "prompt": prompt,
        "schema": schema.model_json_schema(),
        "effort": effort,
    }
    path = CACHE_DIR / f"{_cache_key(payload)}.json"
    if use_cache and path.exists():
        record = json.loads(path.read_text(encoding="utf-8"))
        served, usage = record["served_model"], record["usage"]
        LEDGER.add(served, usage, cached=True)
        info = CallInfo(served, usage, price(served, usage), record.get("latency_s", 0.0), True)
        return schema.model_validate(record["output"]), info

    kwargs: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
        "output_format": schema,
        "output_config": {"effort": effort},
    }
    if system:
        kwargs["system"] = system
    if model in FALLBACK_MODELS:
        kwargs["betas"] = [FALLBACK_BETA]
        kwargs["fallbacks"] = "default"
    start = time.perf_counter()
    response = _client_for(api_key).beta.messages.parse(**kwargs)
    latency = time.perf_counter() - start

    if response.stop_reason == "refusal":
        raise LLMRefusal(f"{model} refused: {response.stop_details}")
    if response.stop_reason == "max_tokens" or response.parsed_output is None:
        raise RuntimeError(f"{model}: no parsed output (stop_reason={response.stop_reason})")

    u = response.usage
    usage = {
        "input_tokens": u.input_tokens or 0,
        "output_tokens": u.output_tokens or 0,
        "cache_creation_input_tokens": u.cache_creation_input_tokens or 0,
        "cache_read_input_tokens": u.cache_read_input_tokens or 0,
    }
    served = response.model if response.model in _prices() else model
    LEDGER.add(served, usage, cached=False)
    output = response.parsed_output.model_dump()
    info = CallInfo(served, usage, price(served, usage), latency, False)
    if api_key is not None:
        return schema.model_validate(output), info
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {"served_model": served, "usage": usage, "output": output, "latency_s": latency},
            indent=1,
        ),
        encoding="utf-8",
    )
    info = CallInfo(served, usage, price(served, usage), latency, False)
    return schema.model_validate(output), info


@dataclass(frozen=True)
class Completion:
    text: str
    model: str  # model that actually served the request (differs if a fallback ran)
    usage: dict[str, int]
    cost_usd: float  # what this call costs at list price, even when served from cache
    latency_s: float  # wall-clock of the original API call (also reported for cache hits)
    cached: bool


def generate(
    model: str,
    prompt: str,
    *,
    system: str | None = None,
    effort: Effort | None = None,
    max_tokens: int = 16000,
    use_cache: bool = True,
) -> Completion:
    """One plain-text call. effort=None leaves the model's default (used by the naive v0)."""
    payload = {"model": model, "system": system, "prompt": prompt, "effort": effort, "kind": "text"}
    path = CACHE_DIR / f"{_cache_key(payload)}.json"
    if use_cache and path.exists():
        r = json.loads(path.read_text(encoding="utf-8"))
        LEDGER.add(r["served_model"], r["usage"], cached=True)
        return Completion(
            r["output"], r["served_model"], r["usage"], price(r["served_model"], r["usage"]),
            r["latency_s"], cached=True,
        )  # fmt: skip

    kwargs: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system
    if effort:
        kwargs["output_config"] = {"effort": effort}
    if model in FALLBACK_MODELS:
        kwargs["betas"] = [FALLBACK_BETA]
        kwargs["fallbacks"] = "default"
    start = time.perf_counter()
    response = client().beta.messages.create(**kwargs)
    latency = time.perf_counter() - start

    if response.stop_reason == "refusal":
        raise LLMRefusal(f"{model} refused: {response.stop_details}")
    text = "".join(b.text for b in response.content if b.type == "text").strip()
    u = response.usage
    usage = {
        "input_tokens": u.input_tokens or 0,
        "output_tokens": u.output_tokens or 0,
        "cache_creation_input_tokens": u.cache_creation_input_tokens or 0,
        "cache_read_input_tokens": u.cache_read_input_tokens or 0,
    }
    served = response.model if response.model in _prices() else model
    LEDGER.add(served, usage, cached=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {"served_model": served, "usage": usage, "output": text, "latency_s": latency},
            indent=1,
        ),
        encoding="utf-8",
    )
    return Completion(text, served, usage, price(served, usage), latency, cached=False)
