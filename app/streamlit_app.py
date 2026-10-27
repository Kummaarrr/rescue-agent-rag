"""Public demo (Streamlit Community Cloud), free to host and free to run for the owner.

- Highlights and "browse all 150 questions": answers pre-computed from the evaluation runs
  (scripts/build_demo_examples.py) - no API calls at all.
- Ask your own question: runs v1 live on the visitor's own Anthropic API key, which is passed
  explicitly to each model call and never cached, stored or logged. The app holds no Anthropic
  key; only a Voyage key (app secret) for the ~20-token query embedding, which is reached only
  after the visitor's Anthropic key has been used for query understanding.

Run locally:  uv run streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("RESCUE_RAG_INDEX_DIR", str(ROOT / "app" / "index"))

import streamlit as st  # noqa: E402

MAX_QUESTION_CHARS = 300
SYSTEM_LABELS = {
    "v0": "v0 - naive RAG, Claude Opus 5.5",
    "v0-small": "v0-small - naive RAG, Claude Haiku 5.5",
    "v1": "v1 - rescued, Claude Haiku 5.5",
}
HEADLINE = """
**A naive RAG prototype, rebuilt so a model ~40x cheaper beats a frontier model.** Held-out
test split (50 questions, 3 runs per system; numbers checked against the SEC's XBRL data):

| | v0: naive, Claude Opus 5.5 | v1: rescued, Claude Haiku 5.5 |
|---|---|---|
| Accuracy | 95.3% | **98.7%** |
| Hallucinations on unanswerable questions | 0% | **0%** |
| Faithfulness (claims supported by the filings) | 93.7% | **100%** |
| Cost per 1,000 questions | $37.73 | **$0.88** |
"""


@st.cache_data
def load_data() -> dict:
    data = json.loads((ROOT / "app" / "examples.json").read_text(encoding="utf-8"))
    data["by_id"] = {x["id"]: x for x in data["items"]}
    return data


@st.cache_resource
def companies() -> str:
    from rescue_rag.config import get_corpus

    return ", ".join(f"{c.name} ({c.ticker})" for c in get_corpus().companies)


def quote(text: str) -> str:
    return "> " + text.replace("\n", "\n> ")


def show_item(ex: dict) -> None:
    if ex["lesson"]:
        st.markdown(f"**What this shows:** {ex['lesson']}")
    st.markdown(f"**{ex['type']}** · {ex['split']} split · **Expected:** {ex['expected']}")
    for col, key in zip(st.columns(3), ("v0", "v0-small", "v1"), strict=True):
        s = ex["systems"][key]
        with col:
            cost = f"${s['cost_usd']:.4f}" if s.get("cost_usd") is not None else "n/a"
            lat = f"{s['latency_s']:.1f} s" if s.get("latency_s") else "n/a"
            st.markdown(f"#### {SYSTEM_LABELS[key]}")
            (st.success if s["correct"] else st.error)(
                f"{'Correct' if s['correct'] else 'Wrong / missed'} · {cost} · {lat}"
            )
            st.markdown(s["answer"])
            if s["citations"]:
                with st.expander(f"Cited excerpts ({len(s['citations'])})"):
                    for c in s["citations"]:
                        st.caption(c["id"])
                        st.markdown(quote(c["text"]))


def highlights_tab(data: dict) -> None:
    st.caption(
        "Eight questions where the systems differ - the last one is a v1 miss. Answers are the "
        "ones each system gave in the evaluation runs."
    )
    by_id = data["by_id"]
    choice = st.selectbox(
        "Example question", data["highlights"], format_func=lambda i: by_id[i]["question"]
    )
    show_item(by_id[choice])


def browse_tab(data: dict) -> None:
    st.caption(
        "The full evaluation set with every answer from the runs reported above - including "
        "all misses."
    )
    c1, c2, c3 = st.columns([1, 1, 1])
    split = c1.radio("Split", ["all", "dev", "test"], horizontal=True)
    types = ["all", *sorted({x["type"] for x in data["items"]})]
    qtype = c2.selectbox("Question type", types)
    disagree = c3.checkbox("Only where the systems disagree")
    rows = [
        x for x in data["items"]
        if (split == "all" or x["split"] == split)
        and (qtype == "all" or x["type"] == qtype)
        and (not disagree or len({s["correct"] for s in x["systems"].values()}) > 1)
    ]  # fmt: skip
    if not rows:
        st.info("No questions match these filters.")
        return
    ex = st.selectbox(
        f"Question ({len(rows)} matching)", rows,
        format_func=lambda x: f"[{x['type']}] {x['question']}",
    )  # fmt: skip
    show_item(ex)


def ask_tab() -> None:
    st.markdown(
        f"Ask v1 about **{companies()}** - their last three 10-K filings (fiscal years "
        "2023-2026 depending on the company). Name the company and fiscal year for best "
        'results. Questions the filings can\'t answer should get "not found", not a guess.'
    )
    with st.form("ask"):
        key = st.text_input(
            "Your Anthropic API key (used only for this request; never stored or logged)",
            type="password",
        )
        question = st.text_input(
            "Question", placeholder="What was Walmart's total revenue for fiscal year 2026?"
        )
        submitted = st.form_submit_button("Ask", type="primary")
    if not submitted:
        st.caption(
            "This free demo has no API key of its own: live questions run on your key "
            "(about $0.001 each). Or browse the 150 pre-computed questions."
        )
        return
    key, question = key.strip(), question.strip()
    if not key:
        st.warning("Paste an Anthropic API key to ask live questions.")
        return
    if not question or len(question) > MAX_QUESTION_CHARS:
        st.warning(f"Type a question (up to {MAX_QUESTION_CHARS} characters).")
        return

    from rescue_rag.agent.graph import V1Agent

    try:
        with st.spinner("Understanding, retrieving, answering..."):
            r = V1Agent(api_key=key)(question)
    except Exception as e:  # never echo the key; show the error type only
        name = type(e).__name__
        if "Authentication" in name or "Permission" in name:
            st.error("That API key was rejected by Anthropic. Check it and try again.")
        elif "RateLimit" in name:
            st.error("Rate limited (your key or the demo's search quota). Try again shortly.")
        else:
            st.error(f"The request failed ({name}).")
        return
    finally:
        del key

    st.markdown(r.answer)
    plan = r.meta.get("plan") or {}
    status = r.meta.get("status")
    guard = f" (guardrail: {r.meta['guardrail']})" if r.meta.get("guardrail") else ""
    st.caption(
        f"Status: {status}{guard} · cost on your key: ${r.cost_usd or 0:.4f} · "
        f"latency {r.latency_s or 0:.1f} s · agent path: {' -> '.join(r.meta.get('trace', []))} · "
        f"understood as companies {plan.get('companies', [])}, fiscal years "
        f"{plan.get('fiscal_years', [])}"
    )
    cited = [c for c in r.contexts if c.chunk_id in set(r.citations)]
    if cited:
        with st.expander(f"Cited excerpts ({len(cited)})"):
            for c in cited:
                st.caption(c.chunk_id)
                st.markdown(quote(c.text[:800]))


def how_tab() -> None:
    repo = os.environ.get("DEMO_REPO_URL", "https://github.com/Kummaarrr/rescue-agent-rag")
    st.markdown(
        "**v1 pipeline (LangGraph):** understand the question (companies, fiscal years) -> "
        "retrieve per company from structure-aware chunks, filtered to the right filings -> "
        "grounded answer with citations -> code checks (citations must be retrieved excerpts, "
        "figures must appear in them, calculations done in Python) -> 'not found' if anything "
        "fails.\n\n"
        "**Measured and left out:** hybrid keyword search (lowered evidence recall) and "
        "reranking (no gain, +24% cost).\n\n"
        "**Known limits:** v1 is cheaper and more accurate, not faster (two model calls in "
        "sequence); occasionally too cautious when a sentence is split across chunks."
        + (f"\n\nCode, evaluation set and full report: {repo}" if repo else "")
    )


def main() -> None:
    st.set_page_config(page_title="Rescue Agent - RAG", layout="wide")
    st.title("Rescue Agent - RAG over 30 SEC 10-K filings")
    st.markdown(HEADLINE)
    data = load_data()
    tabs = st.tabs(["Highlights", "Browse all 150 questions", "Ask your own question",
                    "How it works"])  # fmt: skip
    with tabs[0]:
        highlights_tab(data)
    with tabs[1]:
        browse_tab(data)
    with tabs[2]:
        ask_tab()
    with tabs[3]:
        how_tab()


main()
