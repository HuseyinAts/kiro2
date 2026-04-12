"""
Task 105: Student Review Service

Service layer for review management, moderation, and statistics
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.student_review import (
    ModerationQueue,
    RatingCategory,
    ReportReason,
    ReviewRating,
    ReviewReport,
    ReviewStatistics,
    ReviewStatus,
    ReviewType,
    ReviewVote,
    StudentReview,
)


class StudentReviewService:
    """Service for student review operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # Task 105.1: Review Submission and Display
    # ============================================================

    async def create_review(
        self,
        user_id: UUID,
        review_type: ReviewType,
        title: str,
        content: str,
        overall_rating: float,
        university_id: UUID | None = None,
        department_id: UUID | None = None,
        **kwargs,
    ) -> StudentReview:
        """Create a new review"""
        # Auto-moderation checks
        spam_score = self._calculate_spam_score(content, title)
        quality_score = self._calculate_quality_score(content, title)
        contains_profanity = self._check_profanity(content + " " + title)
        contains_contact_info = self._check_contact_info(content)
        is_too_short = len(content.strip()) < 50

        # Determine initial status
        status = ReviewStatus.PENDING
        if spam_score > 0.7 or contains_profanity or is_too_short:
            status = ReviewStatus.FLAGGED
        elif quality_score > 0.7 and spam_score < 0.3:
            status = ReviewStatus.APPROVED

        review = StudentReview(
            user_id=user_id,
            review_type=review_type,
            title=title,
            content=content,
            overall_rating=overall_rating,
            university_id=university_id,
            department_id=department_id,
            status=status,
            spam_score=spam_score,
            quality_score=quality_score,
            contains_profanity=contains_profanity,
            contains_contact_info=contains_contact_info,
            is_too_short=is_too_short,
            **kwargs,
        )

        self.db.add(review)
        await self.db.commit()
        await self.db.refresh(review)

        # Add to moderation queue if flagged or pending
        if status in [ReviewStatus.PENDING, ReviewStatus.FLAGGED]:
            await self._add_to_moderation_queue(review)

        return review

    async def get_reviews(
        self,
        review_type: ReviewType | None = None,
        university_id: UUID | None = None,
        department_id: UUID | None = None,
        status: ReviewStatus | None = None,
        min_rating: float | None = None,
        verified_only: bool = False,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "recent",  # "recent", "helpful", "rating"
    ) -> list[StudentReview]:
        """Get reviews with filters"""
        conditions = []

        if review_type:
            conditions.append(StudentReview.review_type == review_type)
        if university_id:
            conditions.append(StudentReview.university_id == university_id)
        if department_id:
            conditions.append(StudentReview.department_id == department_id)
        if status:
            conditions.append(StudentReview.status == status)
        else:
            # By default, only show approved reviews
            conditions.append(StudentReview.status == ReviewStatus.APPROVED)
        if min_rating:
            conditions.append(StudentReview.overall_rating >= min_rating)
        if verified_only:
            conditions.append(StudentReview.is_verified == True)

        query = select(StudentReview)
        if conditions:
            query = query.where(and_(*conditions))

        # Sorting
        if sort_by == "helpful":
            query = query.order_by(desc(StudentReview.helpful_count))
        elif sort_by == "rating":
            query = query.order_by(desc(StudentReview.overall_rating))
        else:  # recent
            query = query.order_by(desc(StudentReview.created_at))

        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_review_by_id(self, review_id: UUID) -> StudentReview | None:
        """Get specific review by ID"""
        query = select(StudentReview).where(StudentReview.id == review_id)
        result = await self.db.execute(query)
        review = result.scalar_one_or_none()

        # Increment view count
        if review:
            review.view_count += 1
            await self.db.commit()

        return review

    async def update_review(self, review_id: UUID, **updates) -> StudentReview | None:
        """Update a review"""
        query = select(StudentReview).where(StudentReview.id == review_id)
        result = await self.db.execute(query)
        review = result.scalar_one_or_none()

        if not review:
            return None

        for key, value in updates.items():
            if hasattr(review, key):
                setattr(review, key, value)

        await self.db.commit()
        await self.db.refresh(review)
        return review

    async def delete_review(self, review_id: UUID) -> bool:
        """Delete a review"""
        query = select(StudentReview).where(StudentReview.id == review_id)
        result = await self.db.execute(query)
        review = result.scalar_one_or_none()

        if not review:
            return False

        await self.db.delete(review)
        await self.db.commit()
        return True

    # ============================================================
    # Task 105.2: Multi-criteria Ratings
    # ============================================================

    async def add_review_ratings(
        self, review_id: UUID, ratings: dict[RatingCategory, float]
    ) -> list[ReviewRating]:
        """Add multi-criteria ratings to a review"""
        rating_objects = []

        for category, rating in ratings.items():
            rating_obj = ReviewRating(
                review_id=review_id, category=category, rating=rating
            )
            self.db.add(rating_obj)
            rating_objects.append(rating_obj)

        await self.db.commit()

        # FIX N+1: Fetch all ratings at once instead of N refreshes
        result = await self.db.execute(
            select(ReviewRating).where(ReviewRating.review_id == review_id)
        )
        return result.scalars().all()

    async def get_review_ratings(self, review_id: UUID) -> list[ReviewRating]:
        """Get multi-criteria ratings for a review"""
        query = select(ReviewRating).where(ReviewRating.review_id == review_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def vote_review(
        self, review_id: UUID, user_id: UUID, is_helpful: bool
    ) -> ReviewVote:
        """Vote on a review (helpful/not helpful)"""
        # Check if user already voted
        existing_vote = await self._get_user_vote(review_id, user_id)

        if existing_vote:
            # Update existing vote
            if existing_vote.is_helpful != is_helpful:
                # Update counts
                review = await self.get_review_by_id(review_id)
                if existing_vote.is_helpful:
                    review.helpful_count -= 1
                    review.not_helpful_count += 1
                else:
                    review.not_helpful_count -= 1
                    review.helpful_count += 1

                existing_vote.is_helpful = is_helpful
                await self.db.commit()
                await self.db.refresh(existing_vote)
            return existing_vote

        # Create new vote
        vote = ReviewVote(review_id=review_id, user_id=user_id, is_helpful=is_helpful)
        self.db.add(vote)

        # Update review counts
        review = await self.get_review_by_id(review_id)
        if is_helpful:
            review.helpful_count += 1
        else:
            review.not_helpful_count += 1

        await self.db.commit()
        await self.db.refresh(vote)
        return vote

    async def _get_user_vote(self, review_id: UUID, user_id: UUID) -> ReviewVote | None:
        """Get user's vote for a review"""
        query = select(ReviewVote).where(
            and_(ReviewVote.review_id == review_id, ReviewVote.user_id == user_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # ============================================================
    # Task 105.3: Moderation and Reports
    # ============================================================

    async def report_review(
        self,
        review_id: UUID,
        reporter_id: UUID,
        reason: ReportReason,
        description: str | None = None,
    ) -> ReviewReport:
        """Report a review"""
        report = ReviewReport(
            review_id=review_id,
            reporter_id=reporter_id,
            reason=reason,
            description=description,
        )
        self.db.add(report)

        # Update review report count
        review = await self.get_review_by_id(review_id)
        review.report_count += 1

        # Auto-flag if many reports
        if review.report_count >= 3 and review.status == ReviewStatus.APPROVED:
            review.status = ReviewStatus.FLAGGED
            await self._add_to_moderation_queue(review, priority=5)

        await self.db.commit()
        await self.db.refresh(report)
        return report

    async def moderate_review(
        self,
        review_id: UUID,
        moderator_id: str,
        new_status: ReviewStatus,
        notes: str | None = None,
    ) -> StudentReview | None:
        """Moderate a review (approve/reject)"""
        review = await self.get_review_by_id(review_id)
        if not review:
            return None

        review.status = new_status
        review.moderation_notes = notes
        review.moderated_by = moderator_id
        review.moderated_at = datetime.now(UTC)

        if new_status == ReviewStatus.APPROVED:
            review.published_at = datetime.now(UTC)

        await self.db.commit()
        await self.db.refresh(review)

        # Remove from moderation queue
        await self._remove_from_moderation_queue(review_id)

        return review

    async def get_moderation_queue(
        self, status: str = "pending", limit: int = 50
    ) -> list[StudentReview]:
        """Get reviews in moderation queue"""
        # Get queue entries
        queue_query = (
            select(ModerationQueue)
            .where(ModerationQueue.status == status)
            .order_by(desc(ModerationQueue.priority), ModerationQueue.created_at)
            .limit(limit)
        )

        queue_result = await self.db.execute(queue_query)
        queue_entries = queue_result.scalars().all()

        if not queue_entries:
            return []

        # Get reviews
        review_ids = [entry.review_id for entry in queue_entries]
        review_query = select(StudentReview).where(StudentReview.id.in_(review_ids))
        review_result = await self.db.execute(review_query)
        return review_result.scalars().all()

    async def _add_to_moderation_queue(self, review: StudentReview, priority: int = 0):
        """Add review to moderation queue"""
        # Check if already in queue
        query = select(ModerationQueue).where(ModerationQueue.review_id == review.id)
        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            # Update priority if higher
            if priority > existing.priority:
                existing.priority = priority
                await self.db.commit()
            return

        # Determine priority and flag reasons
        flag_reasons = []
        if review.contains_profanity:
            flag_reasons.append("profanity")
            priority = max(priority, 8)
        if review.spam_score > 0.7:
            flag_reasons.append("spam")
            priority = max(priority, 7)
        if review.contains_contact_info:
            flag_reasons.append("contact_info")
            priority = max(priority, 6)
        if review.is_too_short:
            flag_reasons.append("too_short")
            priority = max(priority, 3)

        queue_entry = ModerationQueue(
            review_id=review.id, priority=priority, flag_reasons=flag_reasons
        )
        self.db.add(queue_entry)
        await self.db.commit()

    async def _remove_from_moderation_queue(self, review_id: UUID):
        """Remove review from moderation queue"""
        query = select(ModerationQueue).where(ModerationQueue.review_id == review_id)
        result = await self.db.execute(query)
        queue_entry = result.scalar_one_or_none()

        if queue_entry:
            await self.db.delete(queue_entry)
            await self.db.commit()

    # ============================================================
    # Task 105.4: Statistics and Filtering
    # ============================================================

    async def get_review_statistics(
        self,
        review_type: ReviewType,
        university_id: UUID | None = None,
        department_id: UUID | None = None,
    ) -> ReviewStatistics | None:
        """Get review statistics"""
        conditions = [ReviewStatistics.review_type == review_type]

        if university_id:
            conditions.append(ReviewStatistics.university_id == university_id)
        if department_id:
            conditions.append(ReviewStatistics.department_id == department_id)

        query = select(ReviewStatistics).where(and_(*conditions))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def generate_review_statistics(
        self,
        review_type: ReviewType,
        university_id: UUID | None = None,
        department_id: UUID | None = None,
    ) -> ReviewStatistics:
        """Generate or update review statistics"""
        # Get all approved reviews
        reviews = await self.get_reviews(
            review_type=review_type,
            university_id=university_id,
            department_id=department_id,
            status=ReviewStatus.APPROVED,
            limit=10000,
        )

        total_reviews = len(reviews)
        verified_reviews = sum(1 for r in reviews if r.is_verified)

        # Calculate average rating
        avg_rating = (
            sum(r.overall_rating for r in reviews) / total_reviews
            if total_reviews > 0
            else 0
        )

        # Rating distribution
        rating_dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for review in reviews:
            rating_int = int(round(review.overall_rating))
            rating_dist[rating_int] = rating_dist.get(rating_int, 0) + 1

        # Engagement
        total_helpful = sum(r.helpful_count for r in reviews)
        total_views = sum(r.view_count for r in reviews)

        # Get category averages
        category_averages = await self._calculate_category_averages(
            review_type, university_id, department_id
        )

        # Get top tags
        top_tags = self._get_top_tags(reviews)

        # Check if statistics exist
        existing_stats = await self.get_review_statistics(
            review_type, university_id, department_id
        )

        if existing_stats:
            # Update existing
            existing_stats.total_reviews = total_reviews
            existing_stats.verified_reviews = verified_reviews
            existing_stats.average_rating = avg_rating
            existing_stats.rating_1_count = rating_dist[1]
            existing_stats.rating_2_count = rating_dist[2]
            existing_stats.rating_3_count = rating_dist[3]
            existing_stats.rating_4_count = rating_dist[4]
            existing_stats.rating_5_count = rating_dist[5]
            existing_stats.category_averages = category_averages
            existing_stats.total_helpful_votes = total_helpful
            existing_stats.total_views = total_views
            existing_stats.top_tags = top_tags

            await self.db.commit()
            await self.db.refresh(existing_stats)
            return existing_stats
        # Create new
        stats = ReviewStatistics(
            review_type=review_type,
            university_id=university_id,
            department_id=department_id,
            total_reviews=total_reviews,
            verified_reviews=verified_reviews,
            average_rating=avg_rating,
            rating_1_count=rating_dist[1],
            rating_2_count=rating_dist[2],
            rating_3_count=rating_dist[3],
            rating_4_count=rating_dist[4],
            rating_5_count=rating_dist[5],
            category_averages=category_averages,
            total_helpful_votes=total_helpful,
            total_views=total_views,
            top_tags=top_tags,
        )
        self.db.add(stats)
        await self.db.commit()
        await self.db.refresh(stats)
        return stats

    async def _calculate_category_averages(
        self,
        review_type: ReviewType,
        university_id: UUID | None,
        department_id: UUID | None,
    ) -> dict[str, float]:
        """Calculate average ratings for each category"""
        # Get all reviews
        reviews = await self.get_reviews(
            review_type=review_type,
            university_id=university_id,
            department_id=department_id,
            status=ReviewStatus.APPROVED,
            limit=10000,
        )

        if not reviews:
            return {}

        # Get all ratings for these reviews
        review_ids = [r.id for r in reviews]
        query = select(ReviewRating).where(ReviewRating.review_id.in_(review_ids))
        result = await self.db.execute(query)
        ratings = result.scalars().all()

        # Calculate averages by category
        category_sums = {}
        category_counts = {}

        for rating in ratings:
            category = rating.category
            if category not in category_sums:
                category_sums[category] = 0
                category_counts[category] = 0
            category_sums[category] += rating.rating
            category_counts[category] += 1

        category_averages = {}
        for category in category_sums:
            category_averages[category] = round(
                category_sums[category] / category_counts[category], 2
            )

        return category_averages

    def _get_top_tags(self, reviews: list[StudentReview], limit: int = 10) -> list[str]:
        """Get most common tags from reviews"""
        tag_counts = {}

        for review in reviews:
            if review.tags:
                for tag in review.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Sort by count and get top N
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        return [tag for tag, count in sorted_tags[:limit]]

    # ============================================================
    # Auto-moderation Helper Methods
    # ============================================================

    def _calculate_spam_score(self, content: str, title: str) -> float:
        """Calculate spam probability score (0.0 - 1.0)"""
        score = 0.0
        text = (content + " " + title).lower()

        # Check for spam indicators
        spam_keywords = [
            "click here",
            "buy now",
            "limited offer",
            "guaranteed",
            "free money",
        ]
        for keyword in spam_keywords:
            if keyword in text:
                score += 0.2

        # Excessive capitalization
        if sum(1 for c in text if c.isupper()) / max(len(text), 1) > 0.5:
            score += 0.3

        # Excessive punctuation
        if text.count("!") + text.count("?") > 5:
            score += 0.2

        # URL count
        url_count = text.count("http://") + text.count("https://") + text.count("www.")
        if url_count > 2:
            score += 0.3

        return min(score, 1.0)

    def _calculate_quality_score(self, content: str, title: str) -> float:
        """Calculate content quality score (0.0 - 1.0)"""
        score = 0.5  # Start at neutral

        # Length bonus
        if len(content) > 200:
            score += 0.2
        if len(content) > 500:
            score += 0.1

        # Sentence structure
        sentence_count = content.count(".") + content.count("!") + content.count("?")
        if sentence_count >= 3:
            score += 0.1

        # Vocabulary diversity (simple measure)
        words = content.lower().split()
        if len(words) > 0:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio > 0.6:
                score += 0.1

        return min(score, 1.0)

    def _check_profanity(self, text: str) -> bool:
        """Check if text contains profanity"""
        # Simple profanity check (would use a proper library in production)
        profanity_list = ["badword1", "badword2"]  # Placeholder
        text_lower = text.lower()
        return any(word in text_lower for word in profanity_list)

    def _check_contact_info(self, text: str) -> bool:
        """Check if text contains contact information"""
        import re

        # Check for email patterns
        if re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text):
            return True

        # Check for phone number patterns
        if re.search(r"\d{10,}", text.replace(" ", "").replace("-", "")):
            return True

        return False
