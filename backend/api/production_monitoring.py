"""
Production Monitoring API Endpoints

Endpoints for monitoring enhanced template performance in production
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime

from services.production_quality_monitor import get_monitor

router = APIRouter(prefix="/api/v1/monitoring", tags=["Monitoring"])


@router.get("/stats")
async def get_quality_stats():
    """
    Get current quality statistics

    Returns:
        - Total questions generated
        - Average Wave 2B score
        - Approval rate
        - Subject breakdown
    """
    try:
        monitor = get_monitor()
        stats = monitor.get_stats_summary()

        return {"success": True, "data": stats, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report")
async def get_quality_report(last_n: Optional[int] = None):
    """
    Generate detailed quality report

    Args:
        last_n: Only analyze last N questions (None = all)

    Returns:
        Markdown-formatted quality report
    """
    try:
        monitor = get_monitor()
        report = await monitor.generate_report(last_n=last_n)

        return {
            "success": True,
            "report": report,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def monitoring_health():
    """
    Check if monitoring system is active

    Returns:
        System health status
    """
    try:
        monitor = get_monitor()
        stats = monitor.get_stats_summary()

        total = stats.get("total_questions", 0)
        avg_score = stats.get("average_score", 0)
        approval_rate = stats.get("approval_rate", 0)

        # Determine health
        health = "HEALTHY"
        issues = []

        if total == 0:
            health = "WARNING"
            issues.append("No questions logged yet")
        elif avg_score < 0.75:
            health = "WARNING"
            issues.append(f"Low average quality: {avg_score:.3f}")
        elif approval_rate < 60:
            health = "WARNING"
            issues.append(f"Low approval rate: {approval_rate:.1f}%")

        return {
            "success": True,
            "health": health,
            "total_questions": total,
            "average_score": avg_score,
            "approval_rate": approval_rate,
            "issues": issues,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent")
async def get_recent_questions(limit: int = 10):
    """
    Get recent question logs

    Args:
        limit: Number of recent questions to return

    Returns:
        List of recent question logs
    """
    try:
        monitor = get_monitor()
        recent = monitor.logs[-limit:]

        return {
            "success": True,
            "count": len(recent),
            "questions": [
                {
                    "timestamp": log.timestamp,
                    "subject": log.subject,
                    "topic": log.topic,
                    "score": log.wave2b_score,
                    "decision": log.decision,
                    "bloom_level": log.bloom_level,
                    "length": log.length,
                    "enhanced": log.enhanced,
                }
                for log in recent
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
