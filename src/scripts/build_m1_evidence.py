"""Replay public M1 fault probes and fixed controls without changing Lab 8.

Run from src/: python -m scripts.build_m1_evidence
This exports raw trace evidence, not scores or a baseline from lab9.eval.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from lab8.shapes import SHAPES
from lab9.evalset import M1_EVIDENCE, M1_PROBES, SOURCE, load_jsonl
from lab9.trace_case import investigate
from lab9.variant_agent import make_shape


def replay(shape: str, claim_id: str, seed: int = 11) -> dict:
    trial = investigate(shape, claim_id, seed)["trial"]
    if not trial["events"] or trial["result"]["status"] == "error":
        raise RuntimeError(f"No usable trace: {shape} {claim_id}@{seed}")
    # Keep the original events and ledger snapshot; omit the duplicated blob.
    return {"shape": shape, "claim_id": claim_id, "seed": seed,
            **{key: value for key, value in trial.items() if key != "blob"}}


def main() -> int:
    claims = load_jsonl(SOURCE)
    evidence = {
        "schema_version": "m1-trace-evidence.v1",
        "generator": "python -m scripts.build_m1_evidence",
        "llm": "MockLLM",
        "method": "One public bug switch plus no_override; fresh store for every trial.",
        "review": {"reviewer_type": "assistant", "human_verified": False},
        "source_sha256": {
            path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
            for path in ("data/public_claims.jsonl", "data/public_world_state.json",
                         "lab9/variant_agent.py", "lab8/shapes/swarm_reference.py")
        },
        "claims": {},
    }
    for claim in claims:
        claim_id = claim["claim_id"]
        control = replay("fixed", claim_id)
        if not control["lab8_pass"]:
            raise RuntimeError(f"Fixed control failed: {claim_id}: {control['lab8_reason']}")
        evidence["claims"][claim_id] = {"control": control, "faults": {}}
    probes = 0
    for fm, bug, claim_ids in M1_PROBES:
        name = f"m1_{bug}"
        # Register new in-memory shapes through the supplied public factory.
        # Never edit variant_agent.py, variants.py, or lab8/ to obtain evidence.
        SHAPES[name] = make_shape(name, {"no_override", bug})
        for claim_id in claim_ids:
            evidence["claims"][claim_id]["faults"][fm] = replay(name, claim_id)
            probes += 1
    evidence["reference_cases"] = {
        "swarm_C-002_55": replay("swarm", "C-002", 55),
        "seeded_regression_C-002_11": replay("seeded_regression", "C-002"),
        "seeded_regression_C-007_11": replay("seeded_regression", "C-007"),
        "seeded_regression_C-014_11": replay("seeded_regression", "C-014"),
    }
    M1_EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    M1_EVIDENCE.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {M1_EVIDENCE}: {len(claims)} fixed controls, {probes} fault probes, 4 reference cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
