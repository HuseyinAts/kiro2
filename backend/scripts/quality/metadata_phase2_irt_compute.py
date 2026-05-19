#!/usr/bin/env python3
"""
Phase 2: Compute IRT SE, Fisher info, canonical_form_id, variant_id.

For each KESIN_DOGRU row:
  - irt_se_a/b/c: SE estimate from N + parameter values (Bayesian posterior approximation)
  - fisher_info_max: peak Fisher info value
  - fisher_info_theta: θ that maximizes Fisher info (≈ b for 2PL, or shifted for 3PL)
  - canonical_form_id: hash(question_text + options) for duplicate detection
  - variant_id: random A/B test group
"""

import argparse
import hashlib
import os
import random
import sys
import unicodedata
from math import exp, sqrt

from sqlalchemy import create_engine, text

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
random.seed(42)

eng = create_engine(
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
)


def fisher_info_3pl(theta: float, a: float, b: float, c: float) -> float:
    """Fisher information for 3PL IRT model."""
    if a <= 0:
        return 0.0
    z = a * (theta - b)
    try:
        p_star = 1.0 / (1.0 + exp(-z))  # 2PL probability
    except OverflowError:
        p_star = 1.0 if z > 0 else 0.0
    p = c + (1.0 - c) * p_star  # 3PL probability
    if p <= 0 or p >= 1:
        return 0.0
    q = 1.0 - p
    # Birnbaum 1968: I(θ) = a² * ((p-c)/(1-c))² * (q/p)
    base = ((p - c) / (1.0 - c)) ** 2 * (q / p)
    return a * a * base


def fisher_info_peak(a: float, b: float, c: float) -> tuple[float, float]:
    """Find θ that maximizes Fisher info, and the peak value."""
    if c == 0:
        # 2PL peak at θ = b
        return b, fisher_info_3pl(b, a, b, c)
    # 3PL peak shifted right of b; numerical search
    best_theta = b
    best_info = fisher_info_3pl(b, a, b, c)
    for delta in range(1, 31):
        for sign in (-1, 1):
            theta = b + sign * delta * 0.1
            info = fisher_info_3pl(theta, a, b, c)
            if info > best_info:
                best_info = info
                best_theta = theta
    return best_theta, best_info


def estimate_se(
    a: float, b: float, c: float, n_responses: int
) -> tuple[float, float, float]:
    """
    Approximate SE estimates for 3PL parameters.

    Bayesian posterior SE rule of thumb:
      - SE(a) ≈ 0.4 / sqrt(n) for typical exam items
      - SE(b) ≈ 1.0 / sqrt(n * I_max) where I_max is peak Fisher info
      - SE(c) ≈ 0.05 / sqrt(n) (lower bound, c-parameter is fragile)
    """
    if n_responses < 10:
        # Below calibration threshold — use uninformative wide priors
        return 0.5, 1.5, 0.1
    _, i_max = fisher_info_peak(a, b, c)
    se_a = 0.4 / sqrt(n_responses)
    se_b = 1.0 / sqrt(max(1.0, n_responses * i_max))
    se_c = 0.05 / sqrt(n_responses) if c > 0.01 else 0.0
    return round(se_a, 4), round(se_b, 4), round(se_c, 4)


def canonical_hash(q_text: str, options: tuple) -> str:
    """Hash for duplicate detection: normalized question + sorted options."""
    parts = [unicodedata.normalize("NFC", q_text or "").strip().lower()]
    for opt in options:
        norm = unicodedata.normalize("NFC", opt or "").strip().lower()
        parts.append(norm)
    blob = "|".join(parts).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:24]


def assign_variant() -> str:
    """A/B test group: 70% control (A), 20% treatment (B), 10% holdout (C)."""
    r = random.random()
    if r < 0.7:
        return "A"
    if r < 0.9:
        return "B"
    return "C"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--batch", type=int, default=2000)
    args = ap.parse_args()

    print("[query] active rows with IRT params...")
    with eng.connect() as c:
        rows = c.execute(
            text("""
            SELECT id::text,
                   irt_discrimination AS a,
                   irt_difficulty AS b,
                   irt_guessing AS c,
                   COALESCE(irt_n_responses, 0) AS n,
                   question_text,
                   option_a, option_b, option_c, option_d, option_e,
                   irt_se_a IS NOT NULL AS has_se,
                   canonical_form_id IS NOT NULL AS has_canon
            FROM question_bank
            WHERE is_active = true
            """)
        ).fetchall()
    print(f"[scan] {len(rows):,} active rows\n")

    updates = []
    skipped_no_irt = 0
    for r in rows:
        if r.a is None or r.b is None:
            skipped_no_irt += 1
            continue

        se_a, se_b, se_c = estimate_se(
            float(r.a), float(r.b), float(r.c or 0.0), int(r.n)
        )
        theta_peak, info_peak = fisher_info_peak(
            float(r.a), float(r.b), float(r.c or 0.0)
        )
        canon = canonical_hash(
            r.question_text,
            (r.option_a, r.option_b, r.option_c, r.option_d, r.option_e),
        )
        variant = assign_variant()
        method = "EAP_approx_3PL" if (r.c or 0) > 0 else "EAP_approx_2PL"

        updates.append(
            (
                r.id,
                se_a,
                se_b,
                se_c,
                method,
                round(info_peak, 4),
                round(theta_peak, 4),
                canon,
                variant,
            )
        )

    print(f"[plan] {len(updates):,} updates  (skipped no-IRT: {skipped_no_irt:,})")

    if args.apply and updates:
        print(f"\n[apply] UPDATE {len(updates):,} satır...")
        for i in range(0, len(updates), args.batch):
            batch = updates[i : i + args.batch]
            with eng.begin() as c:
                for u in batch:
                    qid, se_a, se_b, se_c, method, ip, tp, canon, variant = u
                    c.execute(
                        text("""
                        UPDATE question_bank
                        SET irt_se_a = :se_a,
                            irt_se_b = :se_b,
                            irt_se_c = :se_c,
                            irt_method_used = :method,
                            fisher_info_max = :ip,
                            fisher_info_theta = :tp,
                            canonical_form_id = :canon,
                            variant_id = :variant,
                            metadata_filled_at = NOW()
                        WHERE id::text = :qid
                        """),
                        {
                            "qid": qid,
                            "se_a": se_a,
                            "se_b": se_b,
                            "se_c": se_c,
                            "method": method,
                            "ip": ip,
                            "tp": tp,
                            "canon": canon,
                            "variant": variant,
                        },
                    )
            if (i // args.batch + 1) % 10 == 0:
                print(
                    f"  batch {i // args.batch + 1}/{(len(updates) + args.batch - 1) // args.batch}"
                )
        print("[done]")
    else:
        print("\n[dry-run] Pass --apply to commit")


if __name__ == "__main__":
    main()
