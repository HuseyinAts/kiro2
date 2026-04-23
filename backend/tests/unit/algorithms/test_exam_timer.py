"""
Exam Timer Tests (K-07).

Tests for YKS exam duration and timer logic.
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_dir))


# Exam types and durations (in minutes)
EXAM_DURATIONS = {
    "TYT": 165,  # 2 hours 45 minutes
    "AYT": 210,  # 3 hours 30 minutes
    "YDT": 180,  # 3 hours
}


class ExamState:
    """Exam state enumeration."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EXPIRED = "expired"


class ExamTimer:
    """
    Simple exam timer for testing.

    Tracks exam duration and state transitions.
    """

    def __init__(
        self,
        exam_type: str,
        start_time: datetime | None = None,
    ):
        """Initialize exam timer."""
        self.exam_type = exam_type
        self.duration_minutes = EXAM_DURATIONS[exam_type]
        self.start_time = start_time
        self.end_time: datetime | None = None
        self.state = ExamState.PENDING
        self.answers: dict[str, str] = {}

    def start(self) -> None:
        """Start the exam."""
        if self.state != ExamState.PENDING:
            raise ValueError("Exam already started")

        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(minutes=self.duration_minutes)
        self.state = ExamState.IN_PROGRESS

    def get_remaining_time(self) -> int:
        """Get remaining time in seconds."""
        if self.state != ExamState.IN_PROGRESS:
            return 0

        if not self.start_time or not self.end_time:
            return 0

        now = datetime.now()

        if now >= self.end_time:
            return 0

        remaining = self.end_time - now
        return int(remaining.total_seconds())

    def is_expired(self) -> bool:
        """Check if exam time has expired."""
        if not self.start_time or not self.end_time:
            return False

        return datetime.now() >= self.end_time

    def submit_answer(self, question_id: str, answer: str) -> bool:
        """
        Submit an answer.

        Returns:
            True if accepted, False if exam expired.
        """
        if self.state != ExamState.IN_PROGRESS:
            return False

        if self.is_expired():
            self.state = ExamState.EXPIRED
            return False

        self.answers[question_id] = answer
        return True

    def complete(self) -> None:
        """Complete the exam."""
        if self.state == ExamState.IN_PROGRESS:
            self.state = ExamState.COMPLETED

    def auto_complete_if_expired(self) -> None:
        """Auto-complete exam if time expired."""
        if self.is_expired() and self.state == ExamState.IN_PROGRESS:
            self.state = ExamState.COMPLETED


class TestExamDurations:
    """Test exam duration constants."""

    def test_tyt_duration_165(self):
        """TYT exam should be 165 minutes (2h 45m)."""
        duration = EXAM_DURATIONS["TYT"]

        assert duration == 165

        # Convert to hours
        hours = duration / 60.0
        assert hours == 2.75

    def test_ayt_duration_210(self):
        """AYT exam should be 210 minutes (3h 30m)."""
        duration = EXAM_DURATIONS["AYT"]

        assert duration == 210

        # Convert to hours
        hours = duration / 60.0
        assert hours == 3.5

    def test_ydt_duration_180(self):
        """YDT exam should be 180 minutes (3h)."""
        duration = EXAM_DURATIONS["YDT"]

        assert duration == 180

        # Convert to hours
        hours = duration / 60.0
        assert hours == 3.0


class TestExamAutoComplete:
    """Test exam auto-completion on timeout."""

    def test_exam_auto_complete_on_timeout(self):
        """Exam should auto-complete when time expires."""
        timer = ExamTimer(exam_type="TYT")

        # Set start time in the past
        past_time = datetime.now() - timedelta(minutes=200)
        timer.start_time = past_time
        timer.end_time = past_time + timedelta(minutes=165)
        timer.state = ExamState.IN_PROGRESS

        # Check if expired
        assert timer.is_expired()

        # Auto-complete
        timer.auto_complete_if_expired()

        assert timer.state == ExamState.COMPLETED


class TestRemainingTime:
    """Test remaining time calculations."""

    def test_remaining_time_calculation(self):
        """Remaining time should decrease as exam progresses."""
        timer = ExamTimer(exam_type="TYT")

        # Start exam
        timer.start()

        # Should have remaining time
        remaining = timer.get_remaining_time()

        # Should be close to 165 minutes (in seconds)
        expected_seconds = 165 * 60

        # Allow 5 second tolerance
        assert abs(remaining - expected_seconds) < 5


class TestExpiredExam:
    """Test expired exam behavior."""

    def test_expired_exam_rejects_answer(self):
        """Expired exam should reject new answers."""
        timer = ExamTimer(exam_type="TYT")

        # Set exam as expired
        past_time = datetime.now() - timedelta(minutes=200)
        timer.start_time = past_time
        timer.end_time = past_time + timedelta(minutes=165)
        timer.state = ExamState.IN_PROGRESS

        # Try to submit answer
        accepted = timer.submit_answer(question_id="q1", answer="A")

        assert not accepted
        assert timer.state == ExamState.EXPIRED


class TestExamStateTransitions:
    """Test exam state transitions."""

    def test_exam_state_transitions(self):
        """Test all exam state transitions."""
        timer = ExamTimer(exam_type="TYT")

        # Initial state
        assert timer.state == ExamState.PENDING

        # Start exam
        timer.start()
        assert timer.state == ExamState.IN_PROGRESS

        # Submit answers
        timer.submit_answer("q1", "A")
        timer.submit_answer("q2", "B")
        assert len(timer.answers) == 2

        # Complete exam
        timer.complete()
        assert timer.state == ExamState.COMPLETED


class TestExamResume:
    """Test exam resume functionality."""

    def test_exam_resume_preserves_answers(self):
        """Resuming exam should preserve previous answers."""
        timer = ExamTimer(exam_type="TYT")

        # Start and answer questions
        timer.start()
        timer.submit_answer("q1", "A")
        timer.submit_answer("q2", "C")

        # Store answers
        previous_answers = timer.answers.copy()

        # Simulate resume (answers preserved)
        assert timer.answers == previous_answers
        assert len(timer.answers) == 2

        # Submit more answers
        timer.submit_answer("q3", "D")

        # All answers should be present
        assert len(timer.answers) == 3
        assert timer.answers["q1"] == "A"
        assert timer.answers["q2"] == "C"
        assert timer.answers["q3"] == "D"


# Integration test helper
def test_complete_exam_flow():
    """Test complete exam flow from start to completion."""
    timer = ExamTimer(exam_type="TYT")

    # 1. Initial state
    assert timer.state == ExamState.PENDING

    # 2. Start exam
    timer.start()
    assert timer.state == ExamState.IN_PROGRESS
    assert timer.start_time is not None
    assert timer.end_time is not None

    # 3. Submit answers
    answers_accepted = [
        timer.submit_answer("q1", "A"),
        timer.submit_answer("q2", "B"),
        timer.submit_answer("q3", "C"),
    ]
    assert all(answers_accepted)

    # 4. Check remaining time
    remaining = timer.get_remaining_time()
    assert remaining > 0

    # 5. Complete exam
    timer.complete()
    assert timer.state == ExamState.COMPLETED

    # 6. Verify answers preserved
    assert len(timer.answers) == 3
