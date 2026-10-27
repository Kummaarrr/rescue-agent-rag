"""Guards the committed eval set: schema-valid, expected composition, frozen split."""

from collections import Counter

from rag_eval.schema import read_jsonl
from rescue_rag.config import project_path

EXPECTED = {
    "numeric_lookup": (30, 15),
    "numeric_compute": (13, 7),
    "comparison": (10, 5),
    "factual_text": (27, 13),
    "unanswerable": (20, 10),
}


def test_dataset_composition_and_split():
    items = read_jsonl(project_path("evals/data/dataset.jsonl"))  # validates every record
    assert len(items) == 150
    assert len({i.id for i in items}) == 150
    counts = Counter((i.type, i.split) for i in items)
    for t, (dev, test) in EXPECTED.items():
        assert (counts[(t, "dev")], counts[(t, "test")]) == (dev, test), t


def test_answerable_items_have_evidence():
    for i in read_jsonl(project_path("evals/data/dataset.jsonl")):
        if i.type != "unanswerable":
            assert i.gold.accessions and i.gold.evidence, i.id
