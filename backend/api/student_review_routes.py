"""
Task 105: Student Review API Routes

REST API for review submission, display, moderation, and filtering
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import AuthenticatedUser, get_current_user
from models.student_review import RatingCategory, ReportReason, ReviewStatus, ReviewType
from services.student_review_service import StudentReviewService

router = APIRouter(prefix="/api/v1/reviews", tags=["Student Reviews"])


# ============================================================
# Request/Response Models
# ============================================================


class ReviewCreateRequest(BaseModel):
    """Request model for creating a review"""

    review_type: ReviewType
    title: str = Field(..., min_length=10, max_length=255)
    content: str = Field(..., min_length=50, max_length=10000)
    overall_rating: float = Field(..., ge=1.0, le=5.0)
    university_id: UUID | None = None
    department_id: UUID | None = None
    dormitory_id: UUID | None = None
    pros: list[str] | None = None
    cons: list[str] | None = None
    tags: list[str] | None = None
    student_year: int | None = None
    enrollment_year: int | None = None
    is_current_student: bool = True


class ReviewRatingsRequest(BaseModel):
    """Request model for multi-criteria ratings"""

    ratings: dict[RatingCategory, float]


class ReviewVoteRequest(BaseModel):
    """Request model for voting on a review"""

    is_helpful: bool


class ReviewReportRequest(BaseModel):
    """Request model for reporting a review"""

    reason: ReportReason
    description: str | None = Field(None, max_length=2000)


class ReviewModerationRequest(BaseModel):
    """Request model for moderating a review"""

    new_status: ReviewStatus
    notes: str | None = Field(None, max_length=2000)


class ReviewResponse(BaseModel):
    """Response model for review"""

    id: UUID
    user_id: UUID
    review_type: str
    title: str
    content: str
    overall_rating: float
    university_id: UUID | None
    department_id: UUID | None
    status: str
    is_verified: bool
    helpful_count: int
    not_helpful_count: int
    view_count: int
    created_at: Any

    model_config = ConfigDict(from_attributes=True)


class ReviewStatisticsResponse(BaseModel):
    """Response model for review statistics"""

    total_reviews: int
    verified_reviews: int
    average_rating: float | None
    rating_1_count: int
    rating_2_count: int
    rating_3_count: int
    rating_4_count: int
    rating_5_count: int
    category_averages: dict[str, float] | None
    top_tags: list[str] | None

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Task 105.1: Review Submission and Display
# ============================================================


@router.post("/", response_model=ReviewResponse)
async def create_review(
    request: ReviewCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new review

    Automatically runs spam detection and quality checks
    """
    user_id = UUID(current_user.user_id)
    service = StudentReviewService(db)

    review = await service.create_review(
        user_id=user_id,
        review_type=request.review_type,
        title=request.title,
        content=request.content,
        overall_rating=request.overall_rating,
        university_id=request.university_id,
        department_id=request.department_id,
        dormitory_id=request.dormitory_id,
        pros=request.pros,
        cons=request.cons,
        tags=request.tags,
        student_year=request.student_year,
        enrollment_year=request.enrollment_year,
        is_current_student=request.is_current_student,
    )

    return ReviewResponse(
        id=review.id,
        user_id=review.user_id,
        review_type=review.review_type.value,
        title=review.title,
        content=review.content,
        overall_rating=review.overall_rating,
        university_id=review.university_id,
        department_id=review.department_id,
        status=review.status.value,
        is_verified=review.is_verified,
        helpful_count=review.helpful_count,
        not_helpful_count=review.not_helpful_count,
        view_count=review.view_count,
        created_at=review.created_at,
    )


@router.get("/", response_model=list[ReviewResponse])
async def get_reviews(
    review_type: ReviewType | None = Query(None, description="Filter by review type"),
    university_id: UUID | None = Query(None, description="Filter by university"),
    department_id: UUID | None = Query(None, description="Filter by department"),
    min_rating: float | None = Query(
        None, ge=1.0, le=5.0, description="Minimum rating"
    ),
    verified_only: bool = Query(False, description="Show only verified reviews"),
    sort_by: str = Query("recent", description="Sort by: recent, helpful, rating"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Get reviews with filters

    Returns approved reviews by default
    """
    service = StudentReviewService(db)

    reviews = await service.get_reviews(
        review_type=review_type,
        university_id=university_id,
        department_id=department_id,
        min_rating=min_rating,
        verified_only=verified_only,
        sort_by=sort_by,
        limit=limit,
        offset=offset,
    )

    return [
        ReviewResponse(
            id=r.id,
            user_id=r.user_id,
            review_type=r.review_type.value,
            title=r.title,
            content=r.content,
            overall_rating=r.overall_rating,
            university_id=r.university_id,
            department_id=r.department_id,
            status=r.status.value,
            is_verified=r.is_verified,
            helpful_count=r.helpful_count,
            not_helpful_count=r.not_helpful_count,
            view_count=r.view_count,
            created_at=r.created_at,
        )
        for r in reviews
    ]


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review_by_id(review_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Get specific review by ID

    Increments view count
    """
    service = StudentReviewService(db)
    review = await service.get_review_by_id(review_id)

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    return ReviewResponse(
        id=review.id,
        user_id=review.user_id,
        review_type=review.review_type.value,
        title=review.title,
        content=review.content,
        overall_rating=review.overall_rating,
        university_id=review.university_id,
        department_id=review.department_id,
        status=review.status.value,
        is_verified=review.is_verified,
        helpful_count=review.helpful_count,
        not_helpful_count=review.not_helpful_count,
        view_count=review.view_count,
        created_at=review.created_at,
    )


@router.delete("/{review_id}")
async def delete_review(
    review_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a review (user must own the review)"""
    user_id = UUID(current_user.user_id)
    service = StudentReviewService(db)

    # Check ownership
    review = await service.get_review_by_id(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.user_id != user_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this review"
        )

    success = await service.delete_review(review_id)

    if not success:
        raise HTTPException(status_code=404, detail="Review not found")

    return {"message": "Review deleted successfully"}


# ============================================================
# Task 105.2: Multi-criteria Ratings and Voting
# ============================================================


@router.post("/{review_id}/ratings")
async def add_review_ratings(
    review_id: UUID, request: ReviewRatingsRequest, db: AsyncSession = Depends(get_db)
):
    """
    Add multi-criteria ratings to a review

    Categories: education_quality, faculty, campus_facilities, etc.
    """
    service = StudentReviewService(db)

    ratings = await service.add_review_ratings(review_id, request.ratings)

    return {
        "message": "Ratings added successfully",
        "ratings": [
            {"category": r.category.value, "rating": r.rating} for r in ratings
        ],
    }


@router.get("/{review_id}/ratings")
async def get_review_ratings(review_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get multi-criteria ratings for a review"""
    service = StudentReviewService(db)

    ratings = await service.get_review_ratings(review_id)

    return {
        "ratings": [
            {"category": r.category.value, "rating": r.rating, "comment": r.comment}
            for r in ratings
        ]
    }


@router.post("/{review_id}/vote")
async def vote_review(
    review_id: UUID,
    request: ReviewVoteRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Vote on a review (helpful/not helpful)

    Users can change their vote
    """
    user_id = UUID(current_user.user_id)
    service = StudentReviewService(db)

    vote = await service.vote_review(review_id, user_id, request.is_helpful)

    return {"message": "Vote recorded successfully", "is_helpful": vote.is_helpful}


# ============================================================
# Task 105.3: Reporting and Moderation
# ============================================================


@router.post("/{review_id}/report")
async def report_review(
    review_id: UUID,
    request: ReviewReportRequest,
    reporter_id: UUID = Query(..., description="Reporter user ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Report a review for moderation

    Reasons: spam, inappropriate, offensive, fake, misleading, off_topic, other
    """
    service = StudentReviewService(db)

    report = await service.report_review(
        review_id=review_id,
        reporter_id=reporter_id,
        reason=request.reason,
        description=request.description,
    )

    return {"message": "Report submitted successfully", "report_id": report.id}


@router.post("/{review_id}/moderate")
async def moderate_review(
    review_id: UUID,
    request: ReviewModerationRequest,
    moderator_id: UUID = Query(..., description="Moderator user ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Moderate a review (approve/reject/flag/remove)

    Requires moderator privileges (not checked in this endpoint)
    """
    service = StudentReviewService(db)

    review = await service.moderate_review(
        review_id=review_id,
        moderator_id=moderator_id,
        new_status=request.new_status,
        notes=request.notes,
    )

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    return {
        "message": "Review moderated successfully",
        "review_id": review.id,
        "new_status": review.status.value,
    }


@router.get("/moderation/queue", response_model=list[ReviewResponse])
async def get_moderation_queue(
    status: str = Query(
        "pending", description="Queue status: pending, in_review, completed"
    ),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Get reviews in moderation queue

    Returns reviews needing moderation, sorted by priority
    """
    service = StudentReviewService(db)

    reviews = await service.get_moderation_queue(status=status, limit=limit)

    return [
        ReviewResponse(
            id=r.id,
            user_id=r.user_id,
            review_type=r.review_type.value,
            title=r.title,
            content=r.content,
            overall_rating=r.overall_rating,
            university_id=r.university_id,
            department_id=r.department_id,
            status=r.status.value,
            is_verified=r.is_verified,
            helpful_count=r.helpful_count,
            not_helpful_count=r.not_helpful_count,
            view_count=r.view_count,
            created_at=r.created_at,
        )
        for r in reviews
    ]


# ============================================================
# Task 105.4: Statistics and Filtering
# ============================================================


@router.get("/statistics/{review_type}", response_model=ReviewStatisticsResponse)
async def get_review_statistics(
    review_type: ReviewType,
    university_id: UUID | None = Query(None, description="Filter by university"),
    department_id: UUID | None = Query(None, description="Filter by department"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get review statistics

    Returns aggregate statistics for reviews
    """
    service = StudentReviewService(db)

    stats = await service.get_review_statistics(
        review_type=review_type,
        university_id=university_id,
        department_id=department_id,
    )

    if not stats:
        # Return empty statistics
        return ReviewStatisticsResponse(
            total_reviews=0,
            verified_reviews=0,
            average_rating=None,
            rating_1_count=0,
            rating_2_count=0,
            rating_3_count=0,
            rating_4_count=0,
            rating_5_count=0,
            category_averages=None,
            top_tags=None,
        )

    return ReviewStatisticsResponse(
        total_reviews=stats.total_reviews,
        verified_reviews=stats.verified_reviews,
        average_rating=stats.average_rating,
        rating_1_count=stats.rating_1_count,
        rating_2_count=stats.rating_2_count,
        rating_3_count=stats.rating_3_count,
        rating_4_count=stats.rating_4_count,
        rating_5_count=stats.rating_5_count,
        category_averages=stats.category_averages,
        top_tags=stats.top_tags,
    )


@router.post(
    "/statistics/{review_type}/generate", response_model=ReviewStatisticsResponse
)
async def generate_review_statistics(
    review_type: ReviewType,
    university_id: UUID | None = Query(None, description="Filter by university"),
    department_id: UUID | None = Query(None, description="Filter by department"),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate or update review statistics

    Recalculates statistics from current reviews
    """
    service = StudentReviewService(db)

    stats = await service.generate_review_statistics(
        review_type=review_type,
        university_id=university_id,
        department_id=department_id,
    )

    return ReviewStatisticsResponse(
        total_reviews=stats.total_reviews,
        verified_reviews=stats.verified_reviews,
        average_rating=stats.average_rating,
        rating_1_count=stats.rating_1_count,
        rating_2_count=stats.rating_2_count,
        rating_3_count=stats.rating_3_count,
        rating_4_count=stats.rating_4_count,
        rating_5_count=stats.rating_5_count,
        category_averages=stats.category_averages,
        top_tags=stats.top_tags,
    )


# ============================================================
# Convenience Endpoints
# ============================================================


@router.get("/university/{university_id}/summary")
async def get_university_review_summary(
    university_id: UUID, db: AsyncSession = Depends(get_db)
):
    """
    Get review summary for a university

    Returns statistics and recent reviews
    """
    service = StudentReviewService(db)

    # Get statistics
    stats = await service.get_review_statistics(
        review_type=ReviewType.UNIVERSITY, university_id=university_id
    )

    # Get recent reviews
    recent_reviews = await service.get_reviews(
        review_type=ReviewType.UNIVERSITY,
        university_id=university_id,
        limit=5,
        sort_by="recent",
    )

    # Get top-rated reviews
    top_reviews = await service.get_reviews(
        review_type=ReviewType.UNIVERSITY,
        university_id=university_id,
        limit=5,
        sort_by="rating",
    )

    return {
        "statistics": {
            "total_reviews": stats.total_reviews if stats else 0,
            "average_rating": stats.average_rating if stats else None,
            "verified_reviews": stats.verified_reviews if stats else 0,
            "category_averages": stats.category_averages if stats else {},
        },
        "recent_reviews": [
            {
                "id": r.id,
                "title": r.title,
                "overall_rating": r.overall_rating,
                "is_verified": r.is_verified,
                "created_at": r.created_at,
            }
            for r in recent_reviews
        ],
        "top_reviews": [
            {
                "id": r.id,
                "title": r.title,
                "overall_rating": r.overall_rating,
                "helpful_count": r.helpful_count,
                "is_verified": r.is_verified,
            }
            for r in top_reviews
        ],
    }


@router.get("/department/{department_id}/summary")
async def get_department_review_summary(
    department_id: UUID, db: AsyncSession = Depends(get_db)
):
    """
    Get review summary for a department

    Returns statistics and recent reviews
    """
    service = StudentReviewService(db)

    # Get statistics
    stats = await service.get_review_statistics(
        review_type=ReviewType.DEPARTMENT, department_id=department_id
    )

    # Get recent reviews
    recent_reviews = await service.get_reviews(
        review_type=ReviewType.DEPARTMENT,
        department_id=department_id,
        limit=5,
        sort_by="recent",
    )

    return {
        "statistics": {
            "total_reviews": stats.total_reviews if stats else 0,
            "average_rating": stats.average_rating if stats else None,
            "verified_reviews": stats.verified_reviews if stats else 0,
            "category_averages": stats.category_averages if stats else {},
        },
        "recent_reviews": [
            {
                "id": r.id,
                "title": r.title,
                "overall_rating": r.overall_rating,
                "is_verified": r.is_verified,
                "created_at": r.created_at,
            }
            for r in recent_reviews
        ],
    }
