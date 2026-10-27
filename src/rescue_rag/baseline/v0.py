"""v0: a deliberately naive "tutorial RAG" baseline.

Fixed-size chunks, dense top-5, one generic prompt, the large model for everything,
no citations, no abstaining, no metadata. Every weakness here is fixed by a rescue-ladder step.
"""

from __future__ import annotations

import time

from rag_eval.adapters import Context, Response
from rescue_rag import llm
from rescue_rag.config import get_settings, load_yaml
from rescue_rag.embed import PRICE_PER_M_TOKENS, embed
from rescue_rag.ingest.index import dense_search

PROMPT = """Answer the question using the context.

Context:
{context}

Question: {question}"""


class V0Pipeline:
    """model_role: "large_model" (the plan's v0) or "small_model" (the cheap-model baseline
    for the cost-rescue comparison). Everything else is identical."""

    def __init__(self, model_role: str = "large_model", collection: str = "v0_naive") -> None:
        models = load_yaml("models.yaml")
        self.collection = collection
        self.embedding_model = models["embedding_model"]
        self.model = models[model_role]
        self.name = "v0" if model_role == "large_model" else "v0-small"
        self.k = get_settings()["baseline"]["top_k"]

    def __call__(self, question: str) -> Response:
        start = time.perf_counter()
        qvec, q_tokens = embed([question], model=self.embedding_model, input_type="query")
        hits = dense_search(self.collection, qvec[0], self.k)
        retrieval_s = time.perf_counter() - start

        context = "\n\n".join(chunk.text for chunk, _ in hits)
        out = llm.generate(self.model, PROMPT.format(context=context, question=question))
        # count the query embedding at list price even if it came from cache
        embed_cost = max(q_tokens, len(question) // 3) * PRICE_PER_M_TOKENS / 1e6
        return Response(
            answer=out.text,
            contexts=[Context(c.chunk_id, c.text, c.accession) for c, _ in hits],
            cost_usd=out.cost_usd + embed_cost,
            latency_s=retrieval_s + out.latency_s,
            meta={"model": out.model, "usage": out.usage, "cached": out.cached},
        )
