"""M2 calibration decisions, numerical edge cases and input validation."""
from __future__ import annotations

import csv
import math
from pathlib import Path

import pytest

from lab9 import judge, stats

pytestmark = pytest.mark.student


def write_labels(path, pairs):
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.writer(target)
        writer.writerow(["item_id", "reply", "human", "judge"])
        for n, (human, verdict) in enumerate(pairs):
            writer.writerow([f"T-{n}", "fixture", human, verdict])
    return path


def test_fail_is_the_positive_class():
    human = ["FAIL", "FAIL", "FAIL", "PASS", "PASS"]
    verdict = ["FAIL", "FAIL", "PASS", "FAIL", "PASS"]
    assert stats.confusion(human, verdict) == {"tp": 2, "fp": 1, "fn": 1, "tn": 1}


@pytest.mark.parametrize("human,verdict", [(["PASS"], []), (["PASS"], ["MAYBE"])])
def test_confusion_rejects_invalid_or_unpaired_labels(human, verdict):
    with pytest.raises(ValueError):
        stats.confusion(human, verdict)


@pytest.mark.parametrize("human,verdict,expected", [
    ([], [], (0.0, 0.0)),
    (["PASS"], ["PASS"], (0.0, 0.0)),
    (["FAIL"], ["PASS"], (0.0, 0.0)),
])
def test_zero_denominators_do_not_create_perfect_scores(human, verdict, expected):
    assert stats.precision_recall(human, verdict) == expected


@pytest.mark.parametrize("human,verdict,expected", [
    (["FAIL", "PASS"], ["PASS", "FAIL"], -1.0),
    (["FAIL", "PASS"], ["PASS", "PASS"], 0.0),
    (["FAIL", "PASS"], ["FAIL", "PASS"], 1.0),
])
def test_kappa_distinguishes_disagreement_constant_and_perfect(human, verdict, expected):
    assert stats.cohen_kappa(human, verdict) == expected


@pytest.mark.parametrize("labels", [[], ["FAIL", "FAIL"]])
def test_degenerate_kappa_is_undefined(labels):
    with pytest.raises(ValueError):
        stats.cohen_kappa(labels, labels)


@pytest.mark.parametrize("rates", [
    (float("nan"), 0.8, 0.9),
    (0.3, float("inf"), 0.9),
    (0.3, 0.8, -0.1),
    (0.3, 0.2, 0.8),
    (0.3, 0.1, 0.8),
])
def test_rogan_gladen_rejects_invalid_rates_or_no_positive_signal(rates):
    with pytest.raises(ValueError):
        stats.rogan_gladen(*rates)


def test_rogan_gladen_clips_the_upper_bound():
    assert stats.rogan_gladen(1.0, 0.8, 0.9) == 1.0


@pytest.mark.parametrize("name,passed,confusion,kappa,precision,recall,observed", [
    ("tone", True, {"tp": 24, "fp": 4, "fn": 6, "tn": 66}, 0.757, 0.857, 0.8, 0.28),
    ("helpful", False, {"tp": 9, "fp": 0, "fn": 21, "tn": 70}, 0.375, 1.0, 0.3, 0.09),
])
def test_public_judge_decisions(name, passed, confusion, kappa, precision, recall, observed):
    result = judge.calibrate(Path(f"data/eval/judge_{name}_public.csv"))
    assert result["n"] == 100
    assert result["passed"] is passed
    assert result["confusion"] == confusion
    assert (result["kappa"], result["precision"], result["recall"]) == (kappa, precision, recall)
    assert result["observed_fail_rate"] == observed
    assert result["corrected_fail_rate"] == 0.3
    assert result["calibration_errors"] == []


@pytest.mark.parametrize("label", ["PASS", "FAIL"])
def test_constant_calibration_fails_without_crashing(tmp_path, capsys, label):
    path = write_labels(tmp_path / "constant.csv", [(label, label)] * 5)
    result = judge.calibrate(path)
    assert math.isnan(result["kappa"])
    assert result["corrected_fail_rate"] is None
    assert result["passed"] is False
    assert result["calibration_errors"]
    assert judge.main(["--csv", str(path)]) == 1
    assert "FAIL floors" in capsys.readouterr().out


def test_empty_calibration_fails_with_a_clear_reason(tmp_path, capsys):
    path = write_labels(tmp_path / "empty.csv", [])
    assert judge.main(["--csv", str(path)]) == 1
    assert "no observations" in capsys.readouterr().out


def test_floor_uses_full_precision_instead_of_display_rounding(tmp_path):
    # P=1999/2500=0.7996 displays as 0.800; R and kappa meet their floors.
    pairs = ([ ("FAIL", "FAIL") ] * 1999 + [ ("PASS", "FAIL") ] * 501
             + [ ("FAIL", "PASS") ] * 100 + [ ("PASS", "PASS") ] * 4000)
    path = write_labels(tmp_path / "boundary.csv", pairs)
    result = judge.calibrate(path)
    assert result["precision"] == 0.8
    assert result["recall"] >= 0.7 and result["kappa"] >= 0.6
    assert result["passed"] is False
