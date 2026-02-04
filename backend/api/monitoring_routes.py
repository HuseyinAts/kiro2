"""
Monitoring API Routes
Token usage tracking and A/B test results endpoints
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
from backend.monitoring.token_usage_tracker import get_tracker
from services.ab_testing import get_ab_test_manager
import io

router = APIRouter(prefix="/api/monitoring", tags=["Monitoring"])


@router.get("/token-stats")
async def get_token_stats(
    days: int = Query(default=7, description="Number of days to look back"),
    provider: str = Query(default="all", description="Filter by provider"),
):
    """
    Get token usage statistics
    """
    try:
        tracker = get_tracker()

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Get stats
        stats = tracker.get_stats(
            start_date=start_date,
            end_date=end_date,
            provider=provider if provider != "all" else None,
        )

        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/token-projection")
async def get_token_projection():
    """
    Get monthly and annual cost projections
    """
    try:
        tracker = get_tracker()
        projection = tracker.get_monthly_projection()

        return projection

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export-csv")
async def export_csv(
    days: int = Query(default=30, description="Number of days to look back")
):
    """
    Export token usage data as CSV
    """
    try:
        tracker = get_tracker()

        # Create in-memory CSV file
        output = io.StringIO()
        filename = f"token_usage_{days}days.csv"

        tracker.export_csv(output, days=days)

        # Convert to bytes
        output.seek(0)
        csv_content = output.getvalue()

        return StreamingResponse(
            io.BytesIO(csv_content.encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ab-test-results")
async def get_ab_test_results(
    provider: str = Query(default="all", description="Filter by provider"),
    days: int = Query(default=7, description="Number of days to look back"),
):
    """
    Get A/B test results and analysis
    """
    try:
        manager = get_ab_test_manager()

        # Get analysis
        analysis = manager.analyze_results(
            provider=provider if provider != "all" else None, days=days
        )

        if not analysis:
            return {
                "error": "No A/B test data available",
                "total_requests": 0,
                "versions": {},
                "winner": None,
                "statistical_significance": {
                    "tokens_p_value": 1.0,
                    "quality_p_value": 1.0,
                    "is_significant": False,
                },
            }

        # Format response
        response = {
            "provider": provider,
            "test_period_days": days,
            "total_requests": sum(v["requests"] for v in analysis["versions"].values()),
            "versions": analysis["versions"],
            "winner": analysis.get("winner"),
            "statistical_significance": analysis.get(
                "statistical_significance",
                {
                    "tokens_p_value": 1.0,
                    "quality_p_value": 1.0,
                    "is_significant": False,
                },
            ),
        }

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ab-test-report")
async def get_ab_test_report(
    provider: str = Query(default="all", description="Filter by provider"),
    days: int = Query(default=7, description="Number of days to look back"),
):
    """
    Get human-readable A/B test report
    """
    try:
        manager = get_ab_test_manager()

        report = manager.generate_report(
            provider=provider if provider != "all" else None, days=days
        )

        return {"report": report}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    try:
        tracker = get_tracker()
        manager = get_ab_test_manager()

        return {
            "status": "healthy",
            "tracker_initialized": tracker is not None,
            "ab_test_manager_initialized": manager is not None,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
