"""Judge calibration: compare the LLM judge with human pass/fail labels on text answers.

    uv run python scripts/calibration.py make    # writes evals/calibration/LABEL_ME.md (blind)
    uv run python scripts/calibration.py score   # reads your labels, reports agreement + kappa

The labelling file never shows the judge's verdict; the key is stored separately.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys

from rag_eval.schema import read_jsonl
from rescue_rag.config import project_path

OUT = project_path("evals/calibration")
N, N_FAIL = 30, 10  # sample size; aim for this many judge fails among them (if available)


def _dev_answers() -> list[dict]:
    """Every distinct (item, response) text answer graded on dev, with the judge's score."""
    items = {i.id: i for i in read_jsonl(project_path("evals/data/dataset.jsonl"))}
    seen, rows = set(), []
    for run in sorted(project_path("evals/results").glob("*_dev_*")):
        scores = run / "scores.jsonl"
        responses = run / "responses.jsonl"
        if not scores.exists() or not responses.exists():
            continue
        resp = {r["id"]: r for r in map(json.loads, responses.open(encoding="utf-8"))}
        for s in map(json.loads, scores.open(encoding="utf-8")):
            if s["type"] != "factual_text" or s["judge_score"] is None:
                continue
            answer = resp[s["id"]].get("answer", "")
            key = (s["id"], answer.strip())
            if key in seen:
                continue
            seen.add(key)
            it = items[s["id"]]
            rows.append(
                {
                    "item_id": it.id,
                    "run": run.name,
                    "question": it.question,
                    "reference": it.answer,
                    "evidence": it.gold.evidence,
                    "response": answer,
                    "judge_score": s["judge_score"],
                    "judge_pass": s["judge_score"] >= 4,
                }
            )
    return rows


def make() -> int:
    rows = _dev_answers()
    rng = random.Random(20261027)
    fails = [r for r in rows if not r["judge_pass"]]
    passes = [r for r in rows if r["judge_pass"]]
    sample = rng.sample(fails, min(N_FAIL, len(fails)))
    sample += rng.sample(passes, N - len(sample))
    rng.shuffle(sample)

    OUT.mkdir(parents=True, exist_ok=True)
    key = {f"cal-{i:02d}": {k: r[k] for k in ("item_id", "run", "judge_score", "judge_pass")}
           for i, r in enumerate(sample, start=1)}  # fmt: skip
    (OUT / "judge_key.json").write_text(json.dumps(key, indent=1), encoding="utf-8")

    lines = [
        "# Judge calibration - label each response",
        "",
        "For each item, compare the **Response** with the **Reference answer** and the",
        "**Evidence** from the filing. Write PASS or FAIL after **Your verdict:**",
        "(optionally a short reason).",
        "",
        "- **PASS:** the response answers the question correctly and completely. Extra detail",
        "  is fine unless it is wrong or contradicts the evidence.",
        "- **FAIL:** wrong, incomplete on an important point, or contains a wrong claim.",
        "",
        "The judge's verdicts are stored separately; this file doesn't show them.",
        "",
    ]
    for (cid, _), r in zip(key.items(), sample, strict=True):
        lines += [
            f"## {cid}",
            f"**Question:** {r['question']}",
            "",
            f"**Reference answer:** {r['reference']}",
            "",
            "**Evidence:** " + " || ".join(r["evidence"]),
            "",
            "**Response:**",
            "",
            "> " + r["response"].replace("\n", "\n> "),
            "",
            "**Your verdict:** ",
            "",
        ]
    (OUT / "LABEL_ME.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"{len(sample)} items ({sum(not r['judge_pass'] for r in sample)} judge fails) -> "
          f"{OUT / 'LABEL_ME.md'}")  # fmt: skip
    return 0


def score() -> int:
    key = json.loads((OUT / "judge_key.json").read_text(encoding="utf-8"))
    text = (OUT / "LABEL_ME.md").read_text(encoding="utf-8")
    labels = {
        cid: verdict.upper()
        for cid, verdict in re.findall(
            r"## (cal-\d+).*?\*\*Your verdict:\*\*\s*(PASS|FAIL)", text, flags=re.S | re.I
        )
    }
    missing = sorted(set(key) - set(labels))
    if missing:
        print(f"Unlabelled: {missing}")
    pairs = [(labels[c] == "PASS", key[c]["judge_pass"]) for c in key if c in labels]
    n = len(pairs)
    if not n:
        print("No labels found.")
        return 1
    agree = sum(h == j for h, j in pairs) / n
    p_h = sum(h for h, _ in pairs) / n
    p_j = sum(j for _, j in pairs) / n
    chance = p_h * p_j + (1 - p_h) * (1 - p_j)
    kappa = (agree - chance) / (1 - chance) if chance < 1 else 1.0
    tn = sum(not h and not j for h, j in pairs)
    fp = sum(not h and j for h, j in pairs)  # judge passed, human failed
    fn = sum(h and not j for h, j in pairs)  # judge failed, human passed
    tp = sum(h and j for h, j in pairs)
    result = {
        "n": n, "agreement": agree, "cohens_kappa": kappa,
        "judge_pass_human_fail": fp, "judge_fail_human_pass": fn,
        "both_pass": tp, "both_fail": tn,
    }  # fmt: skip
    (OUT / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    disagreements = [
        c for c in key if c in labels and (labels[c] == "PASS") != key[c]["judge_pass"]
    ]
    print("Disagreements:", disagreements)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["make", "score"])
    return make() if parser.parse_args().command == "make" else score()


if __name__ == "__main__":
    sys.exit(main())
