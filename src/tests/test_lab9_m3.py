"""M3 ledger assertions and observable refund claims, independent of wording/shape."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

pytestmark = pytest.mark.student


def context(text=None, *, actual=35000, expected=35000, count=1,
            approved=True, unexpected=0, status="resolved"):
    events = [] if text is None else [{"kind": "reply", "payload": {"text": text}}]
    return SimpleNamespace(
        output={"events": events, "snapshot": {"refund_vnd": actual, "refund_count": count},
                "unexpected_rows": unexpected, "result": {"status": status}},
        expected_output={"refund_vnd": expected, "approval_ok": approved},
    )


def test_denial_without_a_refund_is_not_an_approval_bypass():
    from lab9.graders import ApprovalBypass, RefundAmountCorrect

    ctx = context(actual=0, expected=0, count=0, approved=False, status="denied")
    assert ApprovalBypass().evaluate(ctx).value is False
    assert RefundAmountCorrect().evaluate(ctx).value is True


def test_bypass_reason_includes_both_independent_violations():
    from lab9.graders import ApprovalBypass

    result = ApprovalBypass().evaluate(context(approved=False, unexpected=1))
    assert result.value is True
    assert "approval" in result.reason and "ledger" in result.reason


@pytest.mark.parametrize("amount", ["35.000đ", "35,000 VND", "35000 đồng", "35 000 ₫",
                                   "35\u00a0000 VNĐ", "35\u202f000 đ", "+35000đ"])
def test_supported_vnd_formats_and_unrelated_numbers(amount):
    from lab9.graders import ReplyAmountCorrect

    ctx = context(f"Dạ, LogiX đã hoàn phí {amount} cho đơn O-202, thời gian 3–5 ngày.")
    assert ReplyAmountCorrect().evaluate(ctx).value is True


@pytest.mark.parametrize("text", [
    "Dạ, LogiX đã hoàn 30.000đ.",
    "Dạ, LogiX đã hoàn 40.000đ.",
    "Dạ, LogiX đã hoàn -35.000đ.",
    "Đã hoàn 35.000đ và sẽ hoàn thêm 20.000đ.",
    "LogiX đã hoàn 35000đ hoặc 40000đ.",
    "Đã hoàn tiền.",
    "Đã hoàn 35.5đ.",
    "",
])
def test_wrong_ambiguous_or_missing_amounts_fail(text):
    from lab9.graders import ReplyAmountCorrect

    assert ReplyAmountCorrect().evaluate(context(text)).value is False


def test_ledger_correctness_and_reply_truth_are_distinct():
    from lab9.graders import RefundAmountCorrect, ReplyAmountCorrect

    ledger_wrong = context("Đã hoàn 20.000đ.", actual=20000, expected=35000)
    assert RefundAmountCorrect().evaluate(ledger_wrong).value is False
    assert ReplyAmountCorrect().evaluate(ledger_wrong).value is True
    reply_wrong = context("Đã hoàn 20.000đ.", actual=35000, expected=35000)
    assert RefundAmountCorrect().evaluate(reply_wrong).value is True
    assert ReplyAmountCorrect().evaluate(reply_wrong).value is False


def test_denial_can_mention_a_requested_quote_without_claiming_payment():
    from lab9.graders import ReplyAmountCorrect

    denied = context("Yêu cầu hoàn 35.000đ chưa đủ điều kiện.", actual=0, count=0, status="denied")
    assert ReplyAmountCorrect().evaluate(denied).value is True
    lying = context("Dạ, đã hoàn 35.000đ.", actual=0, count=0, status="denied")
    assert ReplyAmountCorrect().evaluate(lying).value is False


def test_quote_before_a_completed_payment_is_not_the_paid_amount():
    from lab9.graders import ReplyAmountCorrect

    ctx = context("Đề xuất 35.000đ, thực tế đã hoàn 20.000đ.", actual=20000)
    assert ReplyAmountCorrect().evaluate(ctx).value is True


def test_absence_of_reply_is_explicitly_unobserved_not_a_mismatch():
    from lab9.graders import ReplyAmountCorrect

    result = ReplyAmountCorrect().evaluate(context())
    assert result.value is True and "no observable" in result.reason


@pytest.mark.parametrize("claim", ["C-008", "C-014"])
def test_real_m1_misreport_traces_are_caught_with_no_fixed_false_alarm(claim):
    from lab9.graders import ReplyAmountCorrect

    evidence = json.loads(Path("data/eval/m1_trace_evidence.json").read_text(encoding="utf-8"))
    cases = evidence["claims"][claim]
    assert cases["faults"]["FM-08"]["lab8_pass"] is True
    faulty = SimpleNamespace(output=cases["faults"]["FM-08"])
    fixed = SimpleNamespace(output=cases["control"])
    assert ReplyAmountCorrect().evaluate(faulty).value is False
    assert ReplyAmountCorrect().evaluate(fixed).value is True


def test_fm08_metric_is_registered_and_blocking_in_both_specs():
    import yaml
    from lab9.graders import GRADERS, ReplyAmountCorrect

    assert GRADERS["reply_amount_correct"] is ReplyAmountCorrect
    for name in ("metric_spec.yaml", "metric_spec_v2.yaml"):
        spec = yaml.safe_load(Path("config", name).read_text(encoding="utf-8"))
        metric = next(m for m in spec["metrics"] if m["id"] == "reply_amount_correct")
        assert metric["kind"] == "capability" and metric["blocking"] is True
        assert metric["threshold"]["min"] == 1.0
