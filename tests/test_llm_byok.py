"""A visitor-supplied API key must never read or write the on-disk response cache."""

from types import SimpleNamespace

from pydantic import BaseModel

from rescue_rag import llm


class Out(BaseModel):
    x: int


def _fake_client(calls):
    def parse(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(
            stop_reason="end_turn",
            parsed_output=Out(x=1),
            model="claude-haiku-5-5",
            usage=SimpleNamespace(
                input_tokens=10, output_tokens=2,
                cache_creation_input_tokens=0, cache_read_input_tokens=0,
            ),
        )  # fmt: skip

    return SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(parse=parse)))


def test_visitor_key_bypasses_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(llm, "CACHE_DIR", tmp_path)
    calls: list = []
    seen_keys: list = []

    def client_for(key):
        seen_keys.append(key)
        return _fake_client(calls)

    monkeypatch.setattr(llm, "_client_for", client_for)
    for _ in range(2):
        out, info = llm.parse_full("claude-haiku-5-5", "q", Out, api_key="sk-visitor")
        assert out.x == 1 and not info.cached
    assert len(calls) == 2  # no cache hit on the second call
    assert list(tmp_path.iterdir()) == []  # nothing written
    assert seen_keys == ["sk-visitor", "sk-visitor"]

    llm.parse_full("claude-haiku-5-5", "q", Out)  # owner key: cached as usual
    assert len(list(tmp_path.iterdir())) == 1
