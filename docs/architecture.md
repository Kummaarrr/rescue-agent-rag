# Architecture

## v1 query flow (LangGraph)

The graph in `src/rescue_rag/agent/graph.py`, with its routing conditions labelled
(`V1Agent().mermaid()` prints the unlabelled version generated from the code).

```mermaid
flowchart TD
    Q([question]) --> U["understand<br/>small model: companies + fiscal years"]
    U -- "only companies outside the corpus" --> A["abstain<br/>'not found in the filings'"]
    U --> R["retrieve<br/>dense search per company,<br/>filtered to the requested years' filings"]
    R -- "no filing covers the requested years" --> A
    R --> G["answer<br/>small model, grounded-only instructions,<br/>structured output: status, answer, citations, formula"]
    G --> C{"guardrails (code)"}
    C -- "no valid citation" --> NF[not found]
    C -- "figures not in cited excerpts" --> NF
    C -- "formula inputs not in cited excerpts" --> NF
    C -- "ok" --> K["calculator: evaluate formula in Python"]
    K --> OUT(["answer + citations + cost + latency"])
    A --> OUT
    NF --> OUT
```

Answer statuses: `answered`, `not_found`, `premise_false` (the model rejects a premise the
excerpts contradict).

## Ingestion

```mermaid
flowchart LR
    T[companies.yaml] --> M[SEC ticker map + CIK overrides]
    M --> S[submissions API: latest 3 10-Ks]
    S --> MF[(data/manifest.csv, frozen)]
    MF --> DL[download HTML, rate limited]
    DL --> B["block parser: paragraphs + tables as rows<br/>(ingest/blocks.py)"]
    B --> I["Item segmentation<br/>(TOC detection, ingest/parse_html.py)"]
    I --> CH["structured chunks: whole paragraphs within an Item,<br/>tables as own chunks, context header<br/>(ingest/chunk.py)"]
    CH --> E[Voyage voyage-3.5 embeddings, cached]
    E --> QD[(Qdrant, embedded)]
    S --> X[XBRL companyfacts] --> EV[eval set generators]
```

v0 instead strips HTML to plain text and cuts fixed 1,000-token windows (`naive_chunks`).

## Evaluation harness (`src/rag_eval`)

```mermaid
flowchart LR
    DS[(evals/data/dataset.jsonl<br/>150 questions, frozen split)] --> RUN[runner: cost cap, 4 workers]
    RUN --> AD{Pipeline protocol}
    AD --> IP["in-process: v0, ladder steps, v1"]
    AD --> HTTP["HttpPipeline: any /ask endpoint"]
    IP --> RES[(responses.jsonl)]
    HTTP --> RES
    RES --> RD["reader (small model): behaviour + number as written"]
    RD --> CODE["code: tolerance check, retrieval + citation hits"]
    RES --> J["judge (Opus): text answers, faithfulness"]
    CODE --> SUM[summary.json / summary.md / ABLATION_*.md]
    J --> SUM
```

The harness only needs `{answer, contexts?, citations?, cost_usd?}` from a system under test, so
it can evaluate a client's RAG endpoint over HTTP (the "AI Agent Health Check").
