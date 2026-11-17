"""M1 evidence coverage, rebuild safety and a real FM-03 regression case."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from lab9 import evalset

pytestmark = pytest.mark.student


def test_rebuilding_preserves_tags_and_separate_labels(tmp_path, monkeypatch):
    monkeypatch.setattr(evalset, "ITEMS", tmp_path / "items.jsonl")
    monkeypatch.setattr(evalset, "LABELS", tmp_path / "labels.json")
    assert evalset.build() == (14, 14)
    first = evalset.ITEMS.read_bytes()
    assert evalset.check(evalset.ITEMS, evalset.LABELS) == []
    assert evalset.build() == (14, 14)
    assert evalset.ITEMS.read_bytes() == first
    labels = json.loads(evalset.LABELS.read_text(encoding="utf-8"))
    claims = evalset.load_jsonl(evalset.SOURCE)
    assert labels == {claim["claim_id"]: claim["expected"] for claim in claims}
    assert all("expected" not in item and "label" not in item
               for item in evalset.load_jsonl(evalset.ITEMS))


def test_every_tag_has_trace_evidence_and_a_passing_control():
    evidence = json.loads(evalset.M1_EVIDENCE.read_text(encoding="utf-8"))
    for path, digest in evidence["source_sha256"].items():
        assert hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest() == digest
    covered = set()
    for item in evalset.load_jsonl(evalset.ITEMS):
        group = evidence["claims"][item["claim_id"]]
        assert group["control"]["lab8_pass"] is True
        assert set(item["failure_modes"]) == set(group["faults"])
        assert item["provenance"]["from_trace"] == (
            f"{evalset.M1_EVIDENCE.as_posix()}#/claims/{item['claim_id']}"
        )
        for fm, trial in group["faults"].items():
            covered.add(fm)
            assert trial["claim_id"] == item["claim_id"]
            assert trial["events"]
            # FM-08 is an explicit blind spot of the unchanged Lab 8 grader.
            if fm != "FM-08":
                assert trial["lab8_pass"] is False
    assert covered == {f"FM-{n:02d}" for n in range(1, 9)}


@pytest.mark.parametrize("shape,seed,kept,refund", [
    ("swarm", 55, False, 20000),
    ("seeded_regression", 11, False, 20000),
    ("fixed", 55, True, 0),
    ("fixed", 11, True, 0),
])
def test_c002_ticket_override_is_caught_on_real_trace(shape, seed, kept, refund):
    from lab9.graders import DbFactKept
    from lab9.trace_case import investigate

    trial = investigate(shape, "C-002", seed)["trial"]
    grade = DbFactKept().evaluate(SimpleNamespace(output=trial))
    assert grade.value is kept
    assert trial["snapshot"]["refund_vnd"] == refund
    assert trial["lab8_pass"] is kept
    if not kept:
        assert trial["events"][1]["payload"]["lookup_order"]["order"]["delay_days"] == 2
        assert trial["events"][2] == {"kind": "model_override", "payload": {"delay_days": 5}}


def test_reply_gap_is_visible_despite_lab8_pass():
    evidence = json.loads(evalset.M1_EVIDENCE.read_text(encoding="utf-8"))
    for claim_id, wrong, actual in [("C-008", "35.000đ", "20.000đ"),
                                     ("C-014", "150.000đ", "120.000đ")]:
        group = evidence["claims"][claim_id]
        faulty = group["faults"]["FM-08"]
        assert faulty["lab8_pass"] is True
        assert faulty["snapshot"] == group["control"]["snapshot"]
        assert wrong in faulty["events"][3]["payload"]["text"]
        assert actual in group["control"]["events"][3]["payload"]["text"]
    assert "FM-05" not in evalset.failure_modes_for("C-008")
