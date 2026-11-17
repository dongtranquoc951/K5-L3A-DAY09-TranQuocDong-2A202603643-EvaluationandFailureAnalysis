"""M4 paired resampling, input boundaries and stable eval-set bytes."""
from __future__ import annotations

import pytest

from lab9 import evalset, stats

pytestmark = pytest.mark.student


def test_constant_shift_resamples_pairs_together():
    # Independent resampling would invent uncertainty despite identical deltas.
    assert stats.paired_bootstrap([101, 201, 301], [100, 200, 300]) == (1.0, 1.0, 1.0)


def test_reversing_samples_reverses_the_interval():
    a, b = [1, 0.8, 0.4, 1, 0.2], [0.2, 0.4, 1, 0.6, 0.2]
    delta, lo, hi = stats.paired_bootstrap(a, b)
    reverse = stats.paired_bootstrap(b, a)
    assert reverse == pytest.approx((-delta, -hi, -lo))
    assert stats.paired_bootstrap(a, b) == (delta, lo, hi)


def test_confidence_level_changes_the_requested_interval():
    a, b = [1, 1, 0.8, 1, 0.6], [1, 0.8, 0.8, 0.6, 0.6]
    _, low80, high80 = stats.paired_bootstrap(a, b, confidence=0.8)
    _, low99, high99 = stats.paired_bootstrap(a, b, confidence=0.99)
    assert low99 <= low80 <= high80 <= high99


@pytest.mark.parametrize("a,b", [([], []), ([1], []), ([[1]], [[1]]),
                                ([float("nan")], [0]), ([0], [float("inf")])])
def test_invalid_pairs_are_rejected(a, b):
    with pytest.raises(ValueError):
        stats.paired_bootstrap(a, b)


@pytest.mark.parametrize("kwargs", [{"n_resamples": 0}, {"n_resamples": 1.5},
                                    {"n_resamples": True}, {"confidence": 0},
                                    {"confidence": 1}, {"confidence": float("nan")}])
def test_invalid_bootstrap_settings_are_rejected(kwargs):
    with pytest.raises(ValueError):
        stats.paired_bootstrap([1, 0], [0, 0], **kwargs)


def test_builder_writes_lf_bytes_for_the_committed_eval_set(tmp_path, monkeypatch):
    monkeypatch.setattr(evalset, "ITEMS", tmp_path / "items.jsonl")
    monkeypatch.setattr(evalset, "LABELS", tmp_path / "labels.json")
    evalset.build()
    assert b"\r\n" not in evalset.ITEMS.read_bytes()
    assert b"\r\n" not in evalset.LABELS.read_bytes()
    assert evalset.ITEMS.read_bytes().endswith(b"\n")
