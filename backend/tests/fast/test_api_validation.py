"""
Fast tests for Validation API endpoints
Tests all validation API routes and request/response models
"""

import pytest
from datetime import datetime
from typing import Dict, Any
from unittest.mock import Mock, patch, AsyncMock

from fastapi import status
from fastapi.testclient import TestClient

from api.validation import (
    router,
    ContentSubmissionRequest,
    ExpertFeedbackSubmission,
    ValidationStatusResponse,
)
from core.expert_content_validation import (
    ContentType,
    ExpertRole,
    ValidationStatus,
    ValidationRequest,
    ValidationFeedback,
    ContentComplianceReport,
    ComplianceLevel,
)


@pytest.fixture
def mock_validation_system():
    """Mock validation system for testing"""
    with patch("api.validation.expert_validation_system") as mock:
        yield mock


@pytest.fixture
def sample_submission_data():
    """Sample content submission data"""
    return {
        "content_id": "q_123",
        "content_type": "question",
        "content_data": {
            "question_text": "Test soru?",
            "options": [
                {"id": "A", "text": "Seçenek A"},
                {"id": "B", "text": "Seçenek B"},
            ],
            "correct_answer": "A",
        },
        "submitter_id": "teacher_456",
        "submitter_name": "Ahmet Öğretmen",
        "grade_level": "9",
        "subject": "Matematik",
        "topic": "Cebir",
        "priority": 5,
    }


@pytest.fixture
def sample_feedback_data():
    """Sample expert feedback data"""
    return {
        "expert_id": "expert_123",
        "expert_name": "Dr. Ayşe Uzman",
        "expert_role": "subject_expert",
        "feedbacks": [
            {
                "criterion": "meb_compliance",
                "passed": True,
                "score": 95.0,
                "comment": "MEB müfredatına uygun",
                "suggestions": [],
            }
        ],
    }


@pytest.fixture
def mock_validation_request():
    """Mock validation request object"""
    return ValidationRequest(
        request_id="req_123",
        content_id="q_123",
        content_type=ContentType.QUESTION,
        content_data={"test": "data"},
        submitter_id="teacher_456",
        submitter_name="Ahmet Öğretmen",
        status=ValidationStatus.PENDING,
        required_expert_roles=[ExpertRole.SUBJECT_EXPERT],
        assigned_experts=[{"expert_id": "exp_1", "expert_role": "subject_expert"}],
        feedbacks=[],
        submitted_at=datetime.utcnow(),
        priority=5,
        grade_level="9",
        subject="Matematik",
    )


@pytest.fixture
def mock_compliance_report():
    """Mock compliance report object"""
    return ContentComplianceReport(
        report_id="report_123",
        content_id="q_123",
        content_type=ContentType.QUESTION,
        meb_compliance=ComplianceLevel.FULLY_COMPLIANT,
        meb_score=95.0,
        meb_standards_matched=["standard1", "standard2"],
        meb_issues=[],
        osym_compliance=ComplianceLevel.PARTIALLY_COMPLIANT,
        osym_score=85.0,
        osym_standards_matched=["osym1"],
        osym_issues=["Minor formatting issue"],
        pedagogy_score=90.0,
        pedagogy_notes=["Good pedagogical approach"],
        quality_score=88.0,
        quality_issues=[],
        overall_compliance=ComplianceLevel.FULLY_COMPLIANT,
        overall_score=89.5,
        recommendations=["Consider adding more examples"],
        generated_at=datetime.utcnow(),
    )


class TestRequestModels:
    """Test request/response models"""

    def test_content_submission_request_model(self, sample_submission_data):
        """Test ContentSubmissionRequest model validation"""
        request = ContentSubmissionRequest(**sample_submission_data)

        assert request.content_id == "q_123"
        assert request.content_type == "question"
        assert request.submitter_id == "teacher_456"
        assert request.grade_level == "9"
        assert request.priority == 5

    def test_content_submission_request_minimal(self):
        """Test ContentSubmissionRequest with minimal data"""
        minimal_data = {
            "content_id": "q_minimal",
            "content_type": "question",
            "content_data": {"test": "data"},
            "submitter_id": "user_1",
            "submitter_name": "User One",
        }

        request = ContentSubmissionRequest(**minimal_data)
        assert request.content_id == "q_minimal"
        assert request.grade_level is None
        assert request.priority == 5  # default

    def test_expert_feedback_submission_model(self, sample_feedback_data):
        """Test ExpertFeedbackSubmission model validation"""
        feedback = ExpertFeedbackSubmission(**sample_feedback_data)

        assert feedback.expert_id == "expert_123"
        assert feedback.expert_role == "subject_expert"
        assert len(feedback.feedbacks) == 1

    def test_validation_status_response_model(self):
        """Test ValidationStatusResponse model"""
        response = ValidationStatusResponse(
            request_id="req_123",
            status="pending",
            overall_score=None,
            completion_percentage=0,
            feedbacks_count=0,
            required_experts=2,
            completed_at=None,
        )

        assert response.request_id == "req_123"
        assert response.status == "pending"
        assert response.completion_percentage == 0


class TestSubmitContentEndpoint:
    """Test POST /validation/submit endpoint"""

    @pytest.mark.asyncio
    async def test_submit_content_success(
        self, mock_validation_system, sample_submission_data, mock_validation_request
    ):
        """Test successful content submission"""
        mock_validation_system.submit_content_for_validation = AsyncMock(
            return_value=mock_validation_request
        )

        from api.validation import submit_content_for_validation

        request = ContentSubmissionRequest(**sample_submission_data)
        response = await submit_content_for_validation(request)

        assert response["success"] is True
        assert response["request_id"] == "req_123"
        assert response["status"] == "pending"
        assert "assigned_experts" in response

    @pytest.mark.asyncio
    async def test_submit_content_invalid_type(self, sample_submission_data):
        """Test submission with invalid content type"""
        from api.validation import submit_content_for_validation
        from fastapi import HTTPException

        sample_submission_data["content_type"] = "invalid_type"
        request = ContentSubmissionRequest(**sample_submission_data)

        with pytest.raises(HTTPException) as exc_info:
            await submit_content_for_validation(request)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_submit_content_system_error(
        self, mock_validation_system, sample_submission_data
    ):
        """Test submission when system raises error"""
        from api.validation import submit_content_for_validation
        from fastapi import HTTPException

        mock_validation_system.submit_content_for_validation = AsyncMock(
            side_effect=Exception("System error")
        )

        request = ContentSubmissionRequest(**sample_submission_data)

        with pytest.raises(HTTPException) as exc_info:
            await submit_content_for_validation(request)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestSubmitFeedbackEndpoint:
    """Test POST /validation/feedback/{request_id} endpoint"""

    @pytest.mark.asyncio
    async def test_submit_feedback_success(
        self, mock_validation_system, sample_feedback_data
    ):
        """Test successful feedback submission"""
        mock_validation_system.submit_expert_feedback = AsyncMock(return_value=True)

        from api.validation import submit_expert_feedback

        feedback = ExpertFeedbackSubmission(**sample_feedback_data)
        response = await submit_expert_feedback("req_123", feedback)

        assert response["success"] is True
        assert response["request_id"] == "req_123"
        assert "message" in response

    @pytest.mark.asyncio
    async def test_submit_feedback_invalid_role(self, sample_feedback_data):
        """Test feedback with invalid expert role"""
        from api.validation import submit_expert_feedback
        from fastapi import HTTPException

        sample_feedback_data["expert_role"] = "invalid_role"
        feedback = ExpertFeedbackSubmission(**sample_feedback_data)

        with pytest.raises(HTTPException) as exc_info:
            await submit_expert_feedback("req_123", feedback)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_submit_feedback_not_found(
        self, mock_validation_system, sample_feedback_data
    ):
        """Test feedback for non-existent request"""
        from api.validation import submit_expert_feedback
        from fastapi import HTTPException

        mock_validation_system.submit_expert_feedback = AsyncMock(return_value=False)

        feedback = ExpertFeedbackSubmission(**sample_feedback_data)

        with pytest.raises(HTTPException) as exc_info:
            await submit_expert_feedback("invalid_req_id", feedback)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestGetStatusEndpoint:
    """Test GET /validation/status/{request_id} endpoint"""

    @pytest.mark.asyncio
    async def test_get_status_success(
        self, mock_validation_system, mock_validation_request
    ):
        """Test getting validation status"""
        mock_validation_system.get_validation_request = Mock(
            return_value=mock_validation_request
        )

        from api.validation import get_validation_status

        response = await get_validation_status("req_123")

        assert response.request_id == "req_123"
        assert response.status == "pending"
        assert response.completion_percentage >= 0

    @pytest.mark.asyncio
    async def test_get_status_not_found(self, mock_validation_system):
        """Test getting status for non-existent request"""
        from api.validation import get_validation_status
        from fastapi import HTTPException

        mock_validation_system.get_validation_request = Mock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await get_validation_status("invalid_req_id")

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_status_completion_percentage(self, mock_validation_system):
        """Test completion percentage calculation"""
        from api.validation import get_validation_status

        # Create request with 2 required experts and 1 feedback
        request = ValidationRequest(
            request_id="req_comp",
            content_id="q_comp",
            content_type=ContentType.QUESTION,
            content_data={},
            submitter_id="user_1",
            submitter_name="User One",
            status=ValidationStatus.IN_REVIEW,
            required_expert_roles=[
                ExpertRole.SUBJECT_EXPERT,
                ExpertRole.CURRICULUM_EXPERT,
            ],
            assigned_experts=[],
            feedbacks=[
                ValidationFeedback(
                    feedback_id="fb_1",
                    request_id="req_comp",
                    expert_id="exp_1",
                    expert_name="Expert 1",
                    expert_role=ExpertRole.SUBJECT_EXPERT,
                    passed=True,
                    score=90.0,
                    criteria_scores={},
                    comment="Good",
                    suggestions=[],
                    created_at=datetime.utcnow(),
                )
            ],
            submitted_at=datetime.utcnow(),
            priority=5,
        )

        mock_validation_system.get_validation_request = Mock(return_value=request)

        response = await get_validation_status("req_comp")
        assert response.completion_percentage == 50  # 1 out of 2 experts


class TestGetRequestEndpoint:
    """Test GET /validation/request/{request_id} endpoint"""

    @pytest.mark.asyncio
    async def test_get_request_success(
        self, mock_validation_system, mock_validation_request
    ):
        """Test getting full validation request"""
        mock_validation_system.get_validation_request = Mock(
            return_value=mock_validation_request
        )

        from api.validation import get_validation_request

        response = await get_validation_request("req_123")

        assert response["request_id"] == "req_123"
        assert response["content_id"] == "q_123"
        assert "submitter" in response
        assert "metadata" in response
        assert "workflow" in response
        assert "timeline" in response

    @pytest.mark.asyncio
    async def test_get_request_not_found(self, mock_validation_system):
        """Test getting non-existent request"""
        from api.validation import get_validation_request
        from fastapi import HTTPException

        mock_validation_system.get_validation_request = Mock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await get_validation_request("invalid_req_id")

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestGetComplianceReportEndpoint:
    """Test GET /validation/compliance/{report_id} endpoint"""

    @pytest.mark.asyncio
    async def test_get_compliance_report_success(
        self, mock_validation_system, mock_compliance_report
    ):
        """Test getting compliance report"""
        mock_validation_system.get_compliance_report = Mock(
            return_value=mock_compliance_report
        )

        from api.validation import get_compliance_report

        response = await get_compliance_report("report_123")

        assert response["report_id"] == "report_123"
        assert response["content_id"] == "q_123"
        assert "meb_compliance" in response
        assert "osym_compliance" in response
        assert "pedagogy" in response
        assert "quality" in response
        assert "overall" in response

    @pytest.mark.asyncio
    async def test_get_compliance_report_structure(
        self, mock_validation_system, mock_compliance_report
    ):
        """Test compliance report response structure"""
        mock_validation_system.get_compliance_report = Mock(
            return_value=mock_compliance_report
        )

        from api.validation import get_compliance_report

        response = await get_compliance_report("report_123")

        # Check MEB compliance structure
        assert response["meb_compliance"]["level"] == "fully_compliant"
        assert response["meb_compliance"]["score"] == 95.0
        assert isinstance(response["meb_compliance"]["standards_matched"], list)

        # Check ÖSYM compliance structure
        assert response["osym_compliance"]["level"] == "partially_compliant"
        assert response["osym_compliance"]["score"] == 85.0

        # Check overall structure
        assert response["overall"]["compliance"] == "fully_compliant"
        assert response["overall"]["score"] == 89.5

    @pytest.mark.asyncio
    async def test_get_compliance_report_not_found(self, mock_validation_system):
        """Test getting non-existent compliance report"""
        from api.validation import get_compliance_report
        from fastapi import HTTPException

        mock_validation_system.get_compliance_report = Mock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await get_compliance_report("invalid_report_id")

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestRegisterExpertEndpoint:
    """Test POST /validation/experts/register endpoint"""

    @pytest.mark.asyncio
    async def test_register_expert_success(self, mock_validation_system):
        """Test successful expert registration"""
        mock_validation_system.register_expert = AsyncMock(return_value=True)

        from api.validation import register_expert

        response = await register_expert(
            expert_id="expert_new", expert_roles=["subject_expert", "quality_assurance"]
        )

        assert response["success"] is True
        assert response["expert_id"] == "expert_new"
        assert len(response["roles"]) == 2

    @pytest.mark.asyncio
    async def test_register_expert_invalid_role(self):
        """Test registration with invalid role"""
        from api.validation import register_expert
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await register_expert(expert_id="expert_new", expert_roles=["invalid_role"])

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_register_expert_multiple_roles(self, mock_validation_system):
        """Test registration with multiple valid roles"""
        mock_validation_system.register_expert = AsyncMock(return_value=True)

        from api.validation import register_expert

        roles = ["subject_expert", "curriculum_expert", "quality_assurance"]
        response = await register_expert(expert_id="expert_multi", expert_roles=roles)

        assert response["success"] is True
        assert len(response["roles"]) == 3


class TestGetPendingRequestsEndpoint:
    """Test GET /validation/experts/{expert_id}/pending endpoint"""

    @pytest.mark.asyncio
    async def test_get_pending_requests_success(
        self, mock_validation_system, mock_validation_request
    ):
        """Test getting pending requests for expert"""
        mock_validation_system.get_pending_requests_for_expert = Mock(
            return_value=[mock_validation_request]
        )

        from api.validation import get_pending_requests_for_expert

        response = await get_pending_requests_for_expert("expert_123")

        assert response["expert_id"] == "expert_123"
        assert response["pending_count"] == 1
        assert len(response["requests"]) == 1
        assert response["requests"][0]["request_id"] == "req_123"

    @pytest.mark.asyncio
    async def test_get_pending_requests_empty(self, mock_validation_system):
        """Test getting pending requests when none exist"""
        mock_validation_system.get_pending_requests_for_expert = Mock(return_value=[])

        from api.validation import get_pending_requests_for_expert

        response = await get_pending_requests_for_expert("expert_no_pending")

        assert response["pending_count"] == 0
        assert len(response["requests"]) == 0

    @pytest.mark.asyncio
    async def test_get_pending_requests_structure(self, mock_validation_system):
        """Test pending requests response structure"""
        requests = [
            ValidationRequest(
                request_id=f"req_{i}",
                content_id=f"q_{i}",
                content_type=ContentType.QUESTION,
                content_data={},
                submitter_id="user_1",
                submitter_name="User One",
                status=ValidationStatus.PENDING,
                required_expert_roles=[ExpertRole.SUBJECT_EXPERT],
                assigned_experts=[],
                feedbacks=[],
                submitted_at=datetime.utcnow(),
                priority=5 + i,
                subject="Math",
                topic=f"Topic {i}",
            )
            for i in range(3)
        ]

        mock_validation_system.get_pending_requests_for_expert = Mock(
            return_value=requests
        )

        from api.validation import get_pending_requests_for_expert

        response = await get_pending_requests_for_expert("expert_123")

        assert response["pending_count"] == 3
        for i, req in enumerate(response["requests"]):
            assert "request_id" in req
            assert "content_id" in req
            assert "content_type" in req
            assert "subject" in req
            assert "topic" in req
            assert "priority" in req
            assert "submitted_at" in req


class TestErrorHandling:
    """Test error handling across all endpoints"""

    @pytest.mark.asyncio
    async def test_submit_content_exception_logging(
        self, mock_validation_system, sample_submission_data
    ):
        """Test that exceptions are properly logged"""
        from api.validation import submit_content_for_validation
        from fastapi import HTTPException

        mock_validation_system.submit_content_for_validation = AsyncMock(
            side_effect=Exception("Database error")
        )

        request = ContentSubmissionRequest(**sample_submission_data)

        with pytest.raises(HTTPException):
            await submit_content_for_validation(request)

    @pytest.mark.asyncio
    async def test_feedback_submission_exception_handling(
        self, mock_validation_system, sample_feedback_data
    ):
        """Test feedback submission error handling"""
        from api.validation import submit_expert_feedback
        from fastapi import HTTPException

        mock_validation_system.submit_expert_feedback = AsyncMock(
            side_effect=ValueError("Invalid feedback data")
        )

        feedback = ExpertFeedbackSubmission(**sample_feedback_data)

        with pytest.raises(HTTPException) as exc_info:
            await submit_expert_feedback("req_123", feedback)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestRouterConfiguration:
    """Test router configuration"""

    def test_router_prefix(self):
        """Test router has correct prefix"""
        assert router.prefix == "/validation"

    def test_router_tags(self):
        """Test router has correct tags"""
        assert "validation" in router.tags
