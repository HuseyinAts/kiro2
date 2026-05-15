"""Per-row judge aggregation + audit metadata builder.

INPUT: opus_result + pro_result dicts (from client.py)
OUTPUT: audit metadata delta + status decision + RESULT TSV row tuple
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .prompt_v1 import PROMPT_VERSION, aggregate_verdicts


def build_audit_delta(
    *,
    run_id: str,
    opus_result: dict[str, Any],
    pro_result: dict[str, Any],
    book_answer: str,
) -> dict[str, Any]:
    """
    Build pipeline_metadata.judge_v1 delta from two API results.

    Spec §7.1 schema. Caller jsonb_set's this onto question_bank.pipeline_metadata.
    """
    ts = datetime.now(UTC).isoformat(timespec="seconds")

    # If either model failed, combined verdict = ESCALATE (api_error)
    if not opus_result["ok"] or not pro_result["ok"]:
        combined = "ESCALATE"
        agreement = "api_error"
        issue_primary = (
            opus_result.get("error") or pro_result.get("error") or "api_error"
        )
        issue_all = [
            e for e in (opus_result.get("error"), pro_result.get("error")) if e
        ]
    else:
        agg = aggregate_verdicts(
            opus_result["parsed"], pro_result["parsed"], book_answer
        )
        combined = agg["combined"]
        agreement = agg["agreement"]
        issue_primary = agg["issue_primary"]
        issue_all = agg["issue_all"]

    def model_block(result: dict[str, Any]) -> dict[str, Any]:
        if not result["ok"]:
            return {
                "verdict": None,
                "error": result.get("error"),
                "tokens": result.get("tokens", {"in": 0, "out": 0}),
                "latency_ms": result.get("latency_ms", 0),
                "retry_count": result.get("retry_count", 0),
            }
        p = result["parsed"]
        return {
            "verdict": p["verdict"],
            "agreed_answer": p["agreed_answer"],
            "issue": p["issue"],
            "confidence": p["confidence"],
            "reasoning": p["reasoning"][:300],  # cap stored reasoning
            "tokens": result["tokens"],
            "latency_ms": result["latency_ms"],
            "retry_count": result.get("retry_count", 0),
        }

    return {
        "judge_v1": {
            "run_id": run_id,
            "spec_version": PROMPT_VERSION,
            "ts": ts,
            "combined_verdict": combined,
            "agreement": agreement,
            "issue_primary": issue_primary,
            "issue_all": issue_all,
            "opus": model_block(opus_result),
            "pro": model_block(pro_result),
        }
    }


def status_for_verdict(combined: str, current_status: str) -> str:
    """
    Map combined verdict → new quality_review_status.

    Spec §3.3 mapping table.
    """
    if combined == "PASS":
        return "auto_judged_high"
    if combined == "FAIL":
        return "rejected"
    # ESCALATE → no change (stays bronze_clean)
    return current_status


def estimate_call_cost_usd(opus_result: dict, pro_result: dict) -> float:
    """
    Estimate $ cost for a completed call pair (input+output tokens × pricing).

    Pricing constants from cost_projection_judge_v1.md (2026-05).
    """
    OPUS_IN = 15.0 / 1_000_000  # $/token
    OPUS_OUT = 75.0 / 1_000_000
    PRO_IN = 1.25 / 1_000_000
    PRO_OUT = 10.0 / 1_000_000

    opus_t = opus_result.get("tokens", {"in": 0, "out": 0})
    pro_t = pro_result.get("tokens", {"in": 0, "out": 0})

    cost = (
        opus_t["in"] * OPUS_IN
        + opus_t["out"] * OPUS_OUT
        + pro_t["in"] * PRO_IN
        + pro_t["out"] * PRO_OUT
    )
    return round(cost, 6)


def result_tsv_row(
    *,
    id_: str,
    run_id: str,
    audit_delta: dict[str, Any],
    cost_usd: float,
) -> str:
    """Single tab-separated row for batch RESULT TSV."""
    j = audit_delta["judge_v1"]
    opus_v = j["opus"].get("verdict") or "ERR"
    pro_v = j["pro"].get("verdict") or "ERR"
    opus_a = j["opus"].get("agreed_answer", "") or ""
    pro_a = j["pro"].get("agreed_answer", "") or ""

    return "\t".join(
        [
            id_,
            run_id,
            j["combined_verdict"],
            opus_v,
            pro_v,
            opus_a,
            pro_a,
            j["issue_primary"] or "",
            j["agreement"],
            f"{cost_usd:.6f}",
        ]
    )


RESULT_TSV_HEADER = (
    "id\trun_id\tcombined\topus_verdict\tpro_verdict\t"
    "opus_answer\tpro_answer\tissue_primary\tagreement\tcost_usd"
)
