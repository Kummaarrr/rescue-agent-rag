"""The contract between the harness and any RAG system under test.

A system only has to turn a question into a Response. In-process pipelines implement the
Pipeline protocol directly; external systems (e.g. a client's /ask endpoint) go through
HttpPipeline. Fields a system can't provide (contexts, cost) are left empty and the metrics
that need them are reported as n/a.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx


@dataclass
class Context:
    chunk_id: str
    text: str
    accession: str | None = None  # source document id, when the system exposes it


@dataclass
class Response:
    answer: str
    contexts: list[Context] = field(default_factory=list)
    citations: list[str] = field(default_factory=list)  # chunk ids the answer cites
    cost_usd: float | None = None
    latency_s: float | None = None
    meta: dict[str, Any] = field(default_factory=dict)


class Pipeline(Protocol):
    name: str

    def __call__(self, question: str) -> Response: ...


class HttpPipeline:
    """POSTs {"question": ...} to an endpoint; maps the JSON reply onto Response.

    Expected reply: {"answer": str, "contexts"?: [{"id", "text", "source"?}],
                     "citations"?: [str], "cost_usd"?: float}
    """

    def __init__(self, name: str, url: str, headers: dict[str, str] | None = None) -> None:
        self.name = name
        self._url = url
        self._http = httpx.Client(headers=headers or {}, timeout=120)

    def __call__(self, question: str) -> Response:
        start = time.perf_counter()
        r = self._http.post(self._url, json={"question": question})
        r.raise_for_status()
        data = r.json()
        return Response(
            answer=data.get("answer", ""),
            contexts=[
                Context(c.get("id", str(i)), c.get("text", ""), c.get("source"))
                for i, c in enumerate(data.get("contexts", []))
            ],
            citations=list(data.get("citations", [])),
            cost_usd=data.get("cost_usd"),
            latency_s=time.perf_counter() - start,
        )
