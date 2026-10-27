"""Rate-limited SEC EDGAR HTTP client.

SEC fair-access policy: declare a User-Agent with contact details and stay under 10 requests/second.
https://www.sec.gov/os/accessing-edgar-data
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

RETRY_STATUS = {429, 500, 502, 503, 504}


class RateLimiter:
    """Enforces a minimum interval between calls (thread-safe)."""

    def __init__(self, max_per_second: float, clock=time.monotonic, sleep=time.sleep) -> None:
        if max_per_second <= 0:
            raise ValueError("max_per_second must be positive")
        self.min_interval = 1.0 / max_per_second
        self._clock = clock
        self._sleep = sleep
        self._last: float | None = None
        self._lock = threading.Lock()

    def wait(self) -> None:
        with self._lock:
            now = self._clock()
            if self._last is not None:
                delay = self._last + self.min_interval - now
                if delay > 0:
                    self._sleep(delay)
                    now += delay
            self._last = now


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in RETRY_STATUS
    return isinstance(exc, httpx.TransportError)


class SecClient:
    def __init__(self, user_agent: str, max_per_second: float = 8, timeout: float = 30.0) -> None:
        if not user_agent or "@" not in user_agent:
            raise ValueError(
                "SEC_USER_AGENT must be set to 'Name email@example.com' (SEC fair-access policy)"
            )
        self._limiter = RateLimiter(max_per_second)
        self._http = httpx.Client(
            headers={"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate"},
            timeout=timeout,
            follow_redirects=True,
        )

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> SecClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    @retry(
        retry=retry_if_exception(_is_retryable),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    def get(self, url: str) -> bytes:
        self._limiter.wait()
        response = self._http.get(url)
        response.raise_for_status()
        return response.content

    def get_json(self, url: str) -> Any:
        return json.loads(self.get(url))

    def download(self, url: str, dest: Path, overwrite: bool = False) -> Path:
        """Download to dest unless it already exists (acts as an on-disk cache)."""
        if dest.exists() and not overwrite:
            return dest
        dest.parent.mkdir(parents=True, exist_ok=True)
        content = self.get(url)
        tmp = dest.with_suffix(dest.suffix + ".part")
        tmp.write_bytes(content)
        tmp.replace(dest)
        return dest
