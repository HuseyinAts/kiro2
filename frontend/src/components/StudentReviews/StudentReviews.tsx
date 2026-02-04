/**
 * Task 105: Student Reviews Component
 *
 * Review submission, display, filtering, and voting system
 */

import React, { useState, useEffect } from 'react';
import './StudentReviews.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// ============================================================
// Types
// ============================================================

interface Review {
  id: string;
  user_id: string;
  review_type: string;
  title: string;
  content: string;
  overall_rating: number;
  university_id?: string;
  department_id?: string;
  status: string;
  is_verified: boolean;
  helpful_count: number;
  not_helpful_count: number;
  view_count: number;
  created_at: string;
}

interface ReviewStatistics {
  total_reviews: number;
  verified_reviews: number;
  average_rating: number | null;
  rating_1_count: number;
  rating_2_count: number;
  rating_3_count: number;
  rating_4_count: number;
  rating_5_count: number;
  category_averages: {[key: string]: number} | null;
  top_tags: string[] | null;
}

interface StudentReviewsProps {
  reviewType: 'university' | 'department' | 'dormitory';
  targetId: string;
  userId?: string;  // For submitting reviews and voting
  allowSubmit?: boolean;
}

// ============================================================
// Component
// ============================================================

export const StudentReviews: React.FC<StudentReviewsProps> = ({
  reviewType,
  targetId,
  userId,
  allowSubmit = true
}) => {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [statistics, setStatistics] = useState<ReviewStatistics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [minRating, setMinRating] = useState<number | null>(null);
  const [verifiedOnly, setVerifiedOnly] = useState(false);
  const [sortBy, setSortBy] = useState<'recent' | 'helpful' | 'rating'>('recent');

  // Submission form
  const [showSubmitForm, setShowSubmitForm] = useState(false);
  const [submitFormData, setSubmitFormData] = useState({
    title: '',
    content: '',
    overall_rating: 5,
    pros: '',
    cons: '',
    tags: ''
  });

  useEffect(() => {
    fetchReviews();
    fetchStatistics();
  }, [targetId, reviewType, minRating, verifiedOnly, sortBy]);

  const fetchReviews = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        review_type: reviewType,
        sort_by: sortBy,
        limit: '20',
        offset: '0'
      });

      if (reviewType === 'university') {
        params.append('university_id', targetId);
      } else if (reviewType === 'department') {
        params.append('department_id', targetId);
      }

      if (minRating) {
        params.append('min_rating', minRating.toString());
      }

      if (verifiedOnly) {
        params.append('verified_only', 'true');
      }

      const response = await fetch(`${API_BASE}/api/reviews?${params}`);

      if (!response.ok) {
        throw new Error('Failed to fetch reviews');
      }

      const data = await response.json();
      setReviews(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async () => {
    try {
      const params = new URLSearchParams({});

      if (reviewType === 'university') {
        params.append('university_id', targetId);
      } else if (reviewType === 'department') {
        params.append('department_id', targetId);
      }

      const response = await fetch(
        `${API_BASE}/api/reviews/statistics/${reviewType}?${params}`
      );

      if (response.ok) {
        const data = await response.json();
        setStatistics(data);
      }
    } catch (err) {
      console.error('Failed to fetch statistics:', err);
    }
  };

  const handleSubmitReview = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!userId) {
      alert('You must be logged in to submit a review');
      return;
    }

    try {
      const requestBody = {
        review_type: reviewType,
        title: submitFormData.title,
        content: submitFormData.content,
        overall_rating: submitFormData.overall_rating,
        pros: submitFormData.pros.split(',').map(p => p.trim()).filter(p => p),
        cons: submitFormData.cons.split(',').map(c => c.trim()).filter(c => c),
        tags: submitFormData.tags.split(',').map(t => t.trim()).filter(t => t),
        is_current_student: true
      };

      if (reviewType === 'university') {
        (requestBody as any).university_id = targetId;
      } else if (reviewType === 'department') {
        (requestBody as any).department_id = targetId;
      }

      const response = await fetch(
        `${API_BASE}/api/reviews?user_id=${userId}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestBody)
        }
      );

      if (!response.ok) {
        throw new Error('Failed to submit review');
      }

      // Reset form and refresh reviews
      setSubmitFormData({
        title: '',
        content: '',
        overall_rating: 5,
        pros: '',
        cons: '',
        tags: ''
      });
      setShowSubmitForm(false);
      fetchReviews();
      fetchStatistics();

      alert('Review submitted successfully! It will be reviewed by moderators.');
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to submit review');
    }
  };

  const handleVote = async (reviewId: string, isHelpful: boolean) => {
    if (!userId) {
      alert('You must be logged in to vote');
      return;
    }

    try {
      const response = await fetch(
        `${API_BASE}/api/reviews/${reviewId}/vote?user_id=${userId}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ is_helpful: isHelpful })
        }
      );

      if (response.ok) {
        // Refresh reviews to get updated counts
        fetchReviews();
      }
    } catch (err) {
      console.error('Failed to vote:', err);
    }
  };

  const handleReport = async (reviewId: string) => {
    if (!userId) {
      alert('You must be logged in to report');
      return;
    }

    const reason = prompt('Report reason (spam/inappropriate/offensive/fake/misleading/off_topic/other):');
    if (!reason) return;

    const description = prompt('Additional details (optional):');

    try {
      const response = await fetch(
        `${API_BASE}/api/reviews/${reviewId}/report?reporter_id=${userId}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ reason, description })
        }
      );

      if (response.ok) {
        alert('Report submitted successfully');
      }
    } catch (err) {
      alert('Failed to submit report');
    }
  };

  return (
    <div className="student-reviews">
      {/* Statistics Section */}
      {statistics && (
        <div className="review-statistics">
          <div className="stats-header">
            <h2>Reviews</h2>
            <div className="overall-rating">
              <span className="rating-number">{statistics.average_rating?.toFixed(1) || 'N/A'}</span>
              <div className="stars">{renderStars(statistics.average_rating || 0)}</div>
              <span className="total-reviews">{statistics.total_reviews} reviews</span>
            </div>
          </div>

          <div className="rating-distribution">
            {[5, 4, 3, 2, 1].map(rating => {
              const count = (statistics as any)[`rating_${rating}_count`] || 0;
              const percentage = statistics.total_reviews > 0
                ? (count / statistics.total_reviews) * 100
                : 0;

              return (
                <div key={rating} className="rating-bar">
                  <span className="rating-label">{rating} ⭐</span>
                  <div className="bar">
                    <div className="bar-fill" style={{ width: `${percentage}%` }}></div>
                  </div>
                  <span className="rating-count">{count}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Filters and Submit Button */}
      <div className="review-controls">
        <div className="filters">
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value as any)}>
            <option value="recent">Most Recent</option>
            <option value="helpful">Most Helpful</option>
            <option value="rating">Highest Rated</option>
          </select>

          <select value={minRating || ''} onChange={(e) => setMinRating(e.target.value ? Number(e.target.value) : null)}>
            <option value="">All Ratings</option>
            <option value="4">4+ Stars</option>
            <option value="3">3+ Stars</option>
            <option value="2">2+ Stars</option>
          </select>

          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={verifiedOnly}
              onChange={(e) => setVerifiedOnly(e.target.checked)}
            />
            Verified Only
          </label>
        </div>

        {allowSubmit && userId && (
          <button
            className="btn-submit-review"
            onClick={() => setShowSubmitForm(!showSubmitForm)}
          >
            {showSubmitForm ? 'Cancel' : 'Write a Review'}
          </button>
        )}
      </div>

      {/* Submit Review Form */}
      {showSubmitForm && (
        <div className="submit-review-form">
          <h3>Write Your Review</h3>
          <form onSubmit={handleSubmitReview}>
            <div className="form-group">
              <label>Title *</label>
              <input
                type="text"
                value={submitFormData.title}
                onChange={(e) => setSubmitFormData({...submitFormData, title: e.target.value})}
                required
                minLength={10}
                maxLength={255}
              />
            </div>

            <div className="form-group">
              <label>Rating *</label>
              <div className="rating-input">
                {[1, 2, 3, 4, 5].map(rating => (
                  <span
                    key={rating}
                    className={`star ${rating <= submitFormData.overall_rating ? 'filled' : ''}`}
                    onClick={() => setSubmitFormData({...submitFormData, overall_rating: rating})}
                  >
                    ⭐
                  </span>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label>Your Review * (min 50 characters)</label>
              <textarea
                value={submitFormData.content}
                onChange={(e) => setSubmitFormData({...submitFormData, content: e.target.value})}
                required
                minLength={50}
                rows={6}
              />
            </div>

            <div className="form-group">
              <label>Pros (comma-separated)</label>
              <input
                type="text"
                value={submitFormData.pros}
                onChange={(e) => setSubmitFormData({...submitFormData, pros: e.target.value})}
                placeholder="Good faculty, Nice campus, etc."
              />
            </div>

            <div className="form-group">
              <label>Cons (comma-separated)</label>
              <input
                type="text"
                value={submitFormData.cons}
                onChange={(e) => setSubmitFormData({...submitFormData, cons: e.target.value})}
                placeholder="Expensive, Crowded, etc."
              />
            </div>

            <div className="form-group">
              <label>Tags (comma-separated)</label>
              <input
                type="text"
                value={submitFormData.tags}
                onChange={(e) => setSubmitFormData({...submitFormData, tags: e.target.value})}
                placeholder="good-faculty, nice-campus, etc."
              />
            </div>

            <button type="submit" className="btn-submit">Submit Review</button>
          </form>
        </div>
      )}

      {/* Reviews List */}
      <div className="reviews-list">
        {loading && <div className="loading">Loading reviews...</div>}

        {error && <div className="error">{error}</div>}

        {!loading && reviews.length === 0 && (
          <div className="empty-state">
            No reviews yet. Be the first to review!
          </div>
        )}

        {reviews.map(review => (
          <div key={review.id} className="review-card">
            <div className="review-header">
              <div className="review-rating">
                <span className="rating-number">{review.overall_rating.toFixed(1)}</span>
                <div className="stars">{renderStars(review.overall_rating)}</div>
              </div>
              <div className="review-meta">
                {review.is_verified && (
                  <span className="verified-badge">✓ Verified</span>
                )}
                <span className="review-date">{formatDate(review.created_at)}</span>
              </div>
            </div>

            <h4 className="review-title">{review.title}</h4>
            <p className="review-content">{review.content}</p>

            <div className="review-actions">
              <button
                className="btn-vote helpful"
                onClick={() => handleVote(review.id, true)}
              >
                👍 Helpful ({review.helpful_count})
              </button>
              <button
                className="btn-vote not-helpful"
                onClick={() => handleVote(review.id, false)}
              >
                👎 Not Helpful ({review.not_helpful_count})
              </button>
              <button
                className="btn-report"
                onClick={() => handleReport(review.id)}
              >
                🚩 Report
              </button>
              <span className="view-count">👁️ {review.view_count} views</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ============================================================
// Utility Functions
// ============================================================

function renderStars(rating: number): React.ReactNode {
  const stars = [];
  const fullStars = Math.floor(rating);
  const hasHalfStar = rating % 1 >= 0.5;

  for (let i = 0; i < fullStars; i++) {
    stars.push(<span key={`full-${i}`} className="star filled">⭐</span>);
  }

  if (hasHalfStar && stars.length < 5) {
    stars.push(<span key="half" className="star half">⭐</span>);
  }

  while (stars.length < 5) {
    stars.push(<span key={`empty-${stars.length}`} className="star empty">☆</span>);
  }

  return <>{stars}</>;
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
  if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
  return `${Math.floor(diffDays / 365)} years ago`;
}

export type { StudentReviewsProps, Review, ReviewStatistics };
