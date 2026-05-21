"""
Property-based testing for BKT/IRT/FSRS algorithms — İleri Düzey Audit

Hypothesis ile algoritma invariant'larını binlerce random input'la test eder.
Her invariant ihlali concrete counter-example üretir (Hypothesis shrinking).

Usage:
    python backend/_pilots/audit_property_based_algorithms.py
"""

from __future__ import annotations

import math
import statistics
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Hypothesis setup
from hypothesis import assume, given, settings
from hypothesis import strategies as st

# ============================================================
# BKT (Bayesian Knowledge Tracing) — INVARIANT TESTING
# ============================================================
# Standard BKT formula:
#   posterior = p_L_prior * (1 - p_S) / [ p_L_prior * (1 - p_S) + (1 - p_L_prior) * p_G ]   if correct
#   posterior = p_L_prior * p_S       / [ p_L_prior * p_S       + (1 - p_L_prior) * (1 - p_G) ] if wrong
#   new_p_L = posterior + (1 - posterior) * p_T


def bkt_update(p_L: float, p_T: float, p_G: float, p_S: float, correct: bool) -> float:
    """Standard BKT update. p_L=prior knowledge, p_T=transition, p_G=guess, p_S=slip."""
    if correct:
        numer = p_L * (1 - p_S)
        denom = numer + (1 - p_L) * p_G
    else:
        numer = p_L * p_S
        denom = numer + (1 - p_L) * (1 - p_G)
    if denom < 1e-12:
        posterior = p_L  # no update
    else:
        posterior = numer / denom
    new_p_L = posterior + (1 - posterior) * p_T
    return max(0.001, min(0.999, new_p_L))


# Invariant 1: Output bounded in [0, 1]
@given(
    p_L=st.floats(0.0, 1.0),
    p_T=st.floats(0.0, 1.0),
    p_G=st.floats(0.0, 1.0),
    p_S=st.floats(0.0, 1.0),
    correct=st.booleans(),
)
@settings(max_examples=500, deadline=None)
def inv_bkt_bounded(p_L, p_T, p_G, p_S, correct):
    """BKT-INV-1: Output must be in [0.001, 0.999] (after clamping)."""
    result = bkt_update(p_L, p_T, p_G, p_S, correct)
    assert 0.001 <= result <= 0.999, (
        f"BOUND VIOLATED: input={(p_L, p_T, p_G, p_S, correct)} → {result}"
    )


# Invariant 2: Correct answer → posterior should increase (or transition handles regression)
@given(
    p_L=st.floats(0.1, 0.9),
    p_G=st.floats(0.05, 0.3),  # reasonable guess
    p_S=st.floats(0.05, 0.2),  # reasonable slip
)
@settings(max_examples=500, deadline=None)
def inv_bkt_correct_monotonic(p_L, p_G, p_S):
    """BKT-INV-2: With p_T=0 (no learning transition), correct answer should NEVER decrease posterior.

    Counter-example expected if: p_G > p_L (yani guess olasılığı bilme olasılığından yüksek).
    """
    assume(p_G < 0.5)  # reasonable guess range
    assume(p_S < 0.5)  # reasonable slip range
    result = bkt_update(p_L, 0.0, p_G, p_S, True)
    # With p_T=0, posterior = p_L * (1-p_S) / [p_L*(1-p_S) + (1-p_L)*p_G]
    # When p_L*(1-p_S) > (1-p_L)*p_G, posterior > p_L
    # Approximate: when p_L > p_G/(p_G+1-p_S)
    threshold = p_G / (p_G + 1 - p_S)
    if p_L > threshold:
        # Posterior should NOT decrease
        assert result >= p_L - 0.01, (
            f"MONOTONIC VIOLATED: p_L={p_L:.3f} > thr={threshold:.3f}, but result={result:.3f}"
        )


# Invariant 3: Symmetry — high p_S + low p_G is "noisy" — posterior should approach 0.5
@given(p_L=st.floats(0.2, 0.8))
@settings(max_examples=100, deadline=None)
def inv_bkt_noisy_pulls_toward_half(p_L):
    """BKT-INV-3: With extreme noise (p_G=0.5, p_S=0.5), posterior should ≈ p_L (no information gained).

    Math: p_G=0.5, p_S=0.5, correct → numer=0.5*p_L, denom=0.5*p_L+0.5*(1-p_L)=0.5
    posterior = 0.5*p_L / 0.5 = p_L
    Bu bir mathematical invariant.
    """
    p_G, p_S = 0.5, 0.5
    result = bkt_update(p_L, 0.0, p_G, p_S, True)
    # With p_T=0, posterior must == p_L (mathematical identity)
    assert abs(result - p_L) < 0.01, (
        f"NOISE INVARIANT VIOLATED: p_L={p_L:.3f}, result={result:.3f}, diff={abs(result - p_L):.3f}"
    )


# ============================================================
# IRT 3PL (Item Response Theory) — INVARIANT TESTING
# ============================================================
# P(theta) = c + (1-c) / (1 + exp(-D * a * (theta - b)))
#   D = 1.702 (scaling)
#   a = discrimination ∈ [0.5, 3.0]
#   b = difficulty ∈ [-4, 4]
#   c = guess ∈ [0, 0.5]
#   theta = ability ∈ [-4, 4]

D = 1.702


def irt_3pl_prob(theta: float, a: float, b: float, c: float) -> float:
    """Standard 3PL IRT probability."""
    z = D * a * (theta - b)
    z_clipped = max(-20, min(20, z))  # overflow protection
    return c + (1 - c) / (1 + math.exp(-z_clipped))


# Invariant 4: P(theta) in [c, 1] (asymptotic bounds)
@given(
    theta=st.floats(-4.0, 4.0),
    a=st.floats(0.5, 3.0),
    b=st.floats(-4.0, 4.0),
    c=st.floats(0.0, 0.5),
)
@settings(max_examples=1000, deadline=None)
def inv_irt_bounded(theta, a, b, c):
    """IRT-INV-1: P(theta) ∈ [c, 1] (lower asymptote c, upper 1)."""
    p = irt_3pl_prob(theta, a, b, c)
    assert c <= p <= 1.0, (
        f"IRT BOUND VIOLATED: theta={theta:.2f}, abc=({a:.2f},{b:.2f},{c:.2f}) → {p:.4f}"
    )


# Invariant 5: Monotonicity — P(theta) strictly increasing in theta (for fixed item)
@given(
    a=st.floats(0.5, 3.0),
    b=st.floats(-4.0, 4.0),
    c=st.floats(0.0, 0.5),
    theta1=st.floats(-4.0, 0.0),
    delta=st.floats(0.01, 4.0),
)
@settings(max_examples=500, deadline=None)
def inv_irt_monotonic_theta(a, b, c, theta1, delta):
    """IRT-INV-2: ∀ a>0, P(theta+delta) > P(theta) for delta>0 (strict monotone)."""
    theta2 = theta1 + delta
    p1 = irt_3pl_prob(theta1, a, b, c)
    p2 = irt_3pl_prob(theta2, a, b, c)
    assert p2 > p1 - 1e-9, (
        f"IRT MONOTONIC VIOLATED: theta1={theta1:.2f}, theta2={theta2:.2f}, p1={p1:.6f}, p2={p2:.6f}"
    )


# Invariant 6: At theta = b, P = (1+c)/2 (midpoint for c=0; with c>0 weighted)
@given(
    a=st.floats(0.5, 3.0),
    b=st.floats(-4.0, 4.0),
    c=st.floats(0.0, 0.5),
)
@settings(max_examples=200, deadline=None)
def inv_irt_midpoint(a, b, c):
    """IRT-INV-3: P(theta=b) = c + (1-c)/2 = (1+c)/2."""
    p = irt_3pl_prob(b, a, b, c)
    expected = (1 + c) / 2
    assert abs(p - expected) < 1e-6, (
        f"IRT MIDPOINT VIOLATED: b={b}, c={c}, P(b)={p:.6f}, expected={expected:.6f}"
    )


# Invariant 7: Fisher Information ≥ 0 (always non-negative)
def irt_fisher_info(theta: float, a: float, b: float, c: float) -> float:
    """Fisher Information for 3PL."""
    p = irt_3pl_prob(theta, a, b, c)
    if p <= c or p >= 1 - 1e-9:
        return 0.0
    q = 1 - p
    # I(theta) = (D*a)^2 * (P-c)^2 * Q / [(1-c)^2 * P]
    numer = (D * a) ** 2 * (p - c) ** 2 * q
    denom = (1 - c) ** 2 * p
    if denom < 1e-12:
        return 0.0
    return numer / denom


@given(
    theta=st.floats(-4.0, 4.0),
    a=st.floats(0.5, 3.0),
    b=st.floats(-4.0, 4.0),
    c=st.floats(0.0, 0.5),
)
@settings(max_examples=500, deadline=None)
def inv_irt_fisher_nonneg(theta, a, b, c):
    """IRT-INV-4: Fisher Information always ≥ 0."""
    info = irt_fisher_info(theta, a, b, c)
    assert info >= -1e-9, (
        f"FISHER NEGATIVE: theta={theta:.2f}, abc=({a:.2f},{b:.2f},{c:.2f}) → I={info}"
    )


# Invariant 8: Newton-Raphson MLE convergence under reasonable inputs
def irt_mle_theta(
    responses: list[tuple[bool, float, float, float]], max_iter: int = 50
) -> tuple[float, int]:
    """Newton-Raphson MLE for theta. Returns (theta, iterations_used)."""
    theta = 0.0  # initial guess
    for it in range(max_iter):
        first_deriv = 0.0
        second_deriv = 0.0
        for correct, a, b, c in responses:
            p = irt_3pl_prob(theta, a, b, c)
            if not (c < p < 1 - 1e-9):
                continue
            P_minus_c = p - c
            one_minus_c = 1 - c
            score = D * a * P_minus_c * (1 - p) / (one_minus_c * p)
            if correct:
                first_deriv += score
            else:
                first_deriv -= D * a * P_minus_c / one_minus_c
            info = irt_fisher_info(theta, a, b, c)
            second_deriv -= info  # negative of Fisher info
        if abs(second_deriv) < 1e-10:
            break
        theta_new = theta - first_deriv / second_deriv
        theta_new = max(-4.0, min(4.0, theta_new))
        if abs(theta_new - theta) < 1e-6:
            return theta_new, it + 1
        theta = theta_new
    return theta, max_iter


# Run all invariants
def run_invariants():
    print("=" * 60)
    print("ALGORITHM INVARIANT TESTING (Hypothesis)")
    print("=" * 60)

    invariants = [
        ("BKT-INV-1 Output bounded [0,1]", inv_bkt_bounded),
        ("BKT-INV-2 Correct answer monotonic increase", inv_bkt_correct_monotonic),
        (
            "BKT-INV-3 Noise (p_G=0.5, p_S=0.5) → posterior=p_L",
            inv_bkt_noisy_pulls_toward_half,
        ),
        ("IRT-INV-1 P(theta) bounded [c,1]", inv_irt_bounded),
        ("IRT-INV-2 P(theta) strictly increasing in theta", inv_irt_monotonic_theta),
        ("IRT-INV-3 P(b)=(1+c)/2 midpoint", inv_irt_midpoint),
        ("IRT-INV-4 Fisher Info ≥ 0", inv_irt_fisher_nonneg),
    ]
    results = []
    for name, fn in invariants:
        t0 = time.time()
        try:
            fn()
            dt = time.time() - t0
            print(f"  PASS  {name:<55} ({dt * 1000:.0f}ms)")
            results.append((name, "PASS", dt, None))
        except AssertionError as e:
            dt = time.time() - t0
            msg = str(e).split("\n")[0][:80]
            print(f"  FAIL  {name:<55} {msg}")
            results.append((name, "FAIL", dt, str(e)))
        except Exception as e:
            print(f"  ERR   {name:<55} {type(e).__name__}: {e}")
            results.append((name, "ERR", 0, str(e)))

    # IRT MLE empirical convergence
    print()
    print("=" * 60)
    print("IRT MLE CONVERGENCE EMPIRICAL (1000 random sessions)")
    print("=" * 60)
    import random

    random.seed(42)
    iter_counts = []
    bounded_counts = 0
    for _ in range(1000):
        n_items = random.randint(5, 20)
        responses = []
        true_theta = random.uniform(-3, 3)
        for _ in range(n_items):
            a = random.uniform(0.5, 2.5)
            b = random.uniform(-3, 3)
            c = random.uniform(0, 0.3)
            p = irt_3pl_prob(true_theta, a, b, c)
            correct = random.random() < p
            responses.append((correct, a, b, c))
        theta_est, iters = irt_mle_theta(responses)
        iter_counts.append(iters)
        if -4.0 <= theta_est <= 4.0:
            bounded_counts += 1
    print(
        f"  Convergence iterations: mean={statistics.mean(iter_counts):.2f}, "
        f"p50={statistics.median(iter_counts):.0f}, p95={sorted(iter_counts)[950]:.0f}, "
        f"max={max(iter_counts)}"
    )
    print(f"  Theta bounded [-4,4]: {bounded_counts}/1000 ({bounded_counts / 10:.1f}%)")
    print(f"  Max-iter (50) hit: {sum(1 for i in iter_counts if i == 50)}/1000")

    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, status, _, _ in results if status == "PASS")
    failed = sum(1 for _, status, _, _ in results if status == "FAIL")
    print(f"  Invariants: {passed} PASS / {failed} FAIL / {len(results)} total")

    # Failed details
    if failed:
        print("\n  FAILED INVARIANTS (concrete counter-examples):")
        for name, status, _, msg in results:
            if status == "FAIL":
                print(f"\n  ❌ {name}")
                print(f"     {msg[:300]}")


if __name__ == "__main__":
    run_invariants()
