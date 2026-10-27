"""v1 as a LangGraph agent graph (rescue step S6: orchestration).

Nodes reuse the measured ladder components (S2 index, S4 query understanding and filtered
retrieval, S7 calculator, S8 grounded answers and guardrails). The graph adds explicit routing:

    understand --(only companies outside the corpus)--> abstain
        |
    retrieve ----(no filing covers the requested years)--> abstain
        |
    answer (grounded, calculator, citation + numeric checks) --> END

S6 was planned as a decomposition agent for multi-company questions; per-company retrieval in
S4 already solved those (100% on dev comparisons), so the graph orchestrates instead of
decomposing.
"""

from __future__ import annotations

import time
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from rag_eval.adapters import Context, Response
from rescue_rag.agent import grounded
from rescue_rag.embed import PRICE_PER_M_TOKENS, embed
from rescue_rag.ingest.chunk import Chunk
from rescue_rag.pipeline import LadderConfig, RescuePipeline
from rescue_rag.retrieval.query import QueryPlan, allowed_years, understand

V1_CONFIG = LadderConfig("v1", "s2_tables", k=10, filters=True, grounded=True, calculator=True)


class State(TypedDict, total=False):
    question: str
    plan: QueryPlan
    hits: list[Chunk]
    result: grounded.Grounded
    cost_usd: float
    latency_s: float
    trace: list[str]


class V1Agent:
    name = "v1"

    def __init__(self, config: LadderConfig = V1_CONFIG, api_key: str | None = None) -> None:
        # a visitor's own key (demo): passed explicitly to every model call, never cached
        self.api_key = api_key
        self.base = RescuePipeline(config)  # shares models, collection and _retrieve
        self.config = config
        self.graph = self._build()

    # --- nodes ---------------------------------------------------------------------------------
    def _understand(self, state: State) -> State:
        plan, call = understand(state["question"], self.base.small_model, self.api_key)
        return {
            "plan": plan,
            "cost_usd": state.get("cost_usd", 0.0) + call.cost_usd,
            "latency_s": state.get("latency_s", 0.0) + call.latency_s,
            "trace": [*state.get("trace", []), "understand"],
        }

    def _retrieve(self, state: State) -> State:
        start = time.perf_counter()
        question, plan = state["question"], state["plan"]
        qvec, q_tokens = embed([question], model=self.base.embedding_model, input_type="query")
        hits: list[Chunk] = []
        if not plan.companies:
            found, _, _ = self.base._retrieve(question, qvec[0], None, None, self.config.k)
            hits = [c for c, _ in found]
        else:
            per = (
                self.config.k
                if len(plan.companies) <= 2
                else max(4, 2 * self.config.k // len(plan.companies))
            )
            for t in plan.companies:
                fys = allowed_years(t, plan.fiscal_years)
                if fys is not None and not fys:
                    continue  # no corpus filing covers the requested year(s)
                found, _, _ = self.base._retrieve(question, qvec[0], t, fys, per)
                hits += [c for c, _ in found]
        embed_cost = max(q_tokens, len(question) // 3) * PRICE_PER_M_TOKENS / 1e6
        return {
            "hits": hits,
            "cost_usd": state.get("cost_usd", 0.0) + embed_cost,
            "latency_s": state.get("latency_s", 0.0) + time.perf_counter() - start,
            "trace": [*state.get("trace", []), "retrieve"],
        }

    def _answer(self, state: State) -> State:
        g = grounded.answer(
            state["question"],
            state["hits"],
            self.base.model,
            calculator=self.config.calculator,
            api_key=self.api_key,
        )
        return {
            "result": g,
            "cost_usd": state.get("cost_usd", 0.0) + (g.call.cost_usd if g.call else 0.0),
            "latency_s": state.get("latency_s", 0.0) + (g.call.latency_s if g.call else 0.0),
            "trace": [*state.get("trace", []), "answer"],
        }

    def _abstain(self, state: State) -> State:
        g = grounded.Grounded(grounded.NOT_FOUND_EMPTY, "not_found", [], "empty_context", None)
        return {"result": g, "trace": [*state.get("trace", []), "abstain"]}

    # --- routing -------------------------------------------------------------------------------
    @staticmethod
    def _after_understand(state: State) -> str:
        plan = state["plan"]
        return "abstain" if not plan.companies and plan.mentions_other_companies else "retrieve"

    @staticmethod
    def _after_retrieve(state: State) -> str:
        return "answer" if state["hits"] else "abstain"

    def _build(self) -> Any:
        g = StateGraph(State)
        g.add_node("understand", self._understand)
        g.add_node("retrieve", self._retrieve)
        g.add_node("answer", self._answer)
        g.add_node("abstain", self._abstain)
        g.add_edge(START, "understand")
        g.add_conditional_edges("understand", self._after_understand, ["retrieve", "abstain"])
        g.add_conditional_edges("retrieve", self._after_retrieve, ["answer", "abstain"])
        g.add_edge("answer", END)
        g.add_edge("abstain", END)
        return g.compile()

    def mermaid(self) -> str:
        return str(self.graph.get_graph().draw_mermaid())

    # --- Pipeline protocol -----------------------------------------------------------------------
    def __call__(self, question: str) -> Response:
        out: State = self.graph.invoke({"question": question})
        g, hits = out["result"], out.get("hits", [])
        return Response(
            answer=g.text,
            contexts=[Context(c.chunk_id, c.text, c.accession) for c in hits],
            citations=g.citations,
            cost_usd=out.get("cost_usd", 0.0),
            latency_s=out.get("latency_s", 0.0),
            meta={
                "status": g.status,
                "guardrail": g.guardrail,
                "trace": out.get("trace", []),
                "plan": out["plan"].model_dump() if "plan" in out else None,
            },
        )
