"""Statistics students implement (M2 judge calibration, M4 paired bootstrap).

Rules: a judge is a classifier -- measure it like one. A higher mean is not
"better" until the paired CI of the difference excludes 0.
Reference values to self-check are in tests/test_lab9_stats.py.
"""

from __future__ import annotations

from collections.abc import Sequence
import math

POS = "FAIL"   # the judge's job is to FIND failures, so FAIL is the positive class


def confusion(human: Sequence[str], judge: Sequence[str]) -> dict[str, int]:
    """tp/fp/fn/tn with FAIL as positive."""
    if len(human) != len(judge):
        raise ValueError("human and judge must contain the same number of labels")
    counts = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    for h, j in zip(human, judge):
        if h not in {"PASS", "FAIL"} or j not in {"PASS", "FAIL"}:
            raise ValueError("labels must be PASS or FAIL")
        key = ("tp" if j == POS else "fn") if h == POS else ("fp" if j == POS else "tn")
        counts[key] += 1
    return counts


def precision_recall(human: Sequence[str], judge: Sequence[str]) -> tuple[float, float]:
    cm = confusion(human, judge)
    predicted = cm["tp"] + cm["fp"]
    actual = cm["tp"] + cm["fn"]
    return (cm["tp"] / predicted if predicted else 0.0,
            cm["tp"] / actual if actual else 0.0)


def cohen_kappa(human: Sequence[str], judge: Sequence[str]) -> float:
    """kappa = (p_o - p_e) / (1 - p_e). Raise ValueError when undefined (p_e == 1):
    a constant judge has no signal and must FAIL calibration, not pass on a technicality."""
    cm = confusion(human, judge)
    n = sum(cm.values())
    if not n:
        raise ValueError("kappa is undefined without observations")
    # Integer counts avoid rounding p_e to 1 before checking degeneracy.
    expected_matches = ((cm["tp"] + cm["fn"]) * (cm["tp"] + cm["fp"])
                        + (cm["tn"] + cm["fp"]) * (cm["tn"] + cm["fn"]))
    denominator = n * n - expected_matches
    if denominator == 0:
        raise ValueError("kappa is undefined when expected agreement is 1")
    return (n * (cm["tp"] + cm["tn"]) - expected_matches) / denominator


def rogan_gladen(observed_rate: float, sensitivity: float, specificity: float) -> float:
    """Correct an observed failure rate for judge error; clip to [0, 1]."""
    for value in (observed_rate, sensitivity, specificity):
        if not math.isfinite(value) or not 0.0 <= value <= 1.0:
            raise ValueError("rates must be finite values in [0, 1]")
    signal = sensitivity + specificity - 1
    if signal <= 0:
        raise ValueError("Rogan-Gladen requires sensitivity + specificity > 1")
    estimate = (observed_rate + specificity - 1) / signal
    return min(1.0, max(0.0, estimate))


def paired_bootstrap(a: Sequence[float], b: Sequence[float], *, n_resamples: int = 1000,
                     rng: int = 2027, confidence: float = 0.95) -> tuple[float, float, float]:
    """a[i], b[i] = per-item mean over seeds, SAME items, SAME order.
    Return (mean(a)-mean(b), lo, hi) with scipy.stats.bootstrap(paired=True, method="percentile",
    rng=numpy.random.default_rng(rng)). If a == b everywhere return (0.0, 0.0, 0.0)."""
    import numpy as np
    from scipy.stats import bootstrap

    x, y = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if x.ndim != 1 or y.ndim != 1 or x.shape != y.shape or not x.size:
        raise ValueError("paired samples must be nonempty one-dimensional arrays of equal length")
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("paired samples must contain only finite values")
    if isinstance(n_resamples, bool) or not isinstance(n_resamples, (int, np.integer)) or n_resamples <= 0:
        raise ValueError("n_resamples must be a positive integer")
    if not math.isfinite(confidence) or not 0 < confidence < 1:
        raise ValueError("confidence must be finite and strictly between 0 and 1")
    difference = x - y
    delta = float(np.mean(difference))
    # The empirical paired distribution is constant for identical samples or
    # a constant per-pair shift, including a single observation.
    if np.all(difference == difference[0]):
        return delta, delta, delta

    def mean_difference(left, right, axis=-1):
        return np.mean(left - right, axis=axis)

    result = bootstrap((x, y), mean_difference, paired=True, vectorized=True,
                       n_resamples=int(n_resamples), confidence_level=confidence,
                       method="percentile", rng=np.random.default_rng(rng))
    return delta, float(result.confidence_interval.low), float(result.confidence_interval.high)


def pass_at_k(n: int, c: int, k: int) -> float:
    """Probability that AT LEAST ONE of k trials drawn from n (c of them passing) passes.
    Unbiased estimator (Chen et al. 2021): 1 - C(n-c, k) / C(n, k). Raise ValueError if k > n."""
    # TODO M6
    raise NotImplementedError


def pass_hat_k(n: int, c: int, k: int) -> float:
    """pass^k (tau-bench, Yao et al. 2024): probability that ALL k trials drawn from n pass.
    Unbiased estimator: C(c, k) / C(n, k). Raise ValueError if k > n.
    pass^k <= pass@1 <= pass@k; a reliable agent keeps pass^k close to pass@1."""
    # TODO M6
    raise NotImplementedError
