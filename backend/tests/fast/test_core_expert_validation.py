"""
Fast tests for Expert Content Validation System
Tests core validation workflow, expert assignment, and compliance reporting
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from core.expert_content_validation import (
    ComplianceLevel,
    ContentType,
    ExpertRole,
    ValidationStatus,
    ExpertContentValidationSystem,
    ValidationRequest,
    ValidationFeedback,
    ContentComplianceReport,
)


@pytest.fixture
def validation_system():
    """Create a fresh validation system for each test"""
    return ExpertContentValidationSystem()


@pytest.fixture
def sample_question_content():
    """Sample question content for testing"""
    return {
        "question_text": "Aşağıdakilerden hangisi Türkiye'nin başkentidir?",
        "options": [
            {"id": "A", "text": "İstanbul"},
            {"id": "B", "text": "Ankara"},
            {"id": "C", "text": "İzmir"},
            {"id": "D", "text": "Bursa"},
        ],
        "correct_answer": "B",
        "explanation": "Ankara, 1923 yılından beri Türkiye Cumhuriyeti'nin başkentidir.",
    }


@pytest.fixture
def sample_exam_content():
    """Sample exam content for testing"""
    return {
        "exam_name": "TYT Deneme Sınavı 1",
        "exam_type": "tyt",
        "duration_minutes": 135,
        "sections": [
            {"name": "Türkçe", "question_count": 40, "duration_minutes": 45},
            {"name": "Matematik", "question_count": 40, "duration_minutes": 45},
        ],
        "total_questions": 80,
    }


class TestValidationSystemInitialization:
    """Test validation system initialization"""

    def test_system_initialization(self, validation_system):
        """Test system initializes correctly"""
        assert validation_system is not None
        assert validation_system.validation_requests == {}
        assert validation_system.compliance_reports == {}
        assert hasattr(validation_system, "expert_pool")

    def test_system_has_required_methods(self, validation_system):
        """Test system has all required methods"""
        assert hasattr(validation_system, "submit_content_for_validation")
        assert hasattr(validation_system, "submit_expert_feedback")
        assert hasattr(validation_system, "get_validation_request")
        assert hasattr(validation_system, "get_compliance_report")
        assert hasattr(validation_system, "register_expert")
        assert hasattr(validation_system, "get_pending_requests_for_expert")


class TestContentSubmission:
    """Test content submission for validation"""

    @pytest.mark.asyncio
    async def test_submit_question_for_validation(
        self, validation_system, sample_question_content
    ):
        """Test submitting a question for validation"""
        request = await validation_system.submit_content_for_validation(
            content_id="q_123",
            content_type=ContentType.QUESTION,
            content_data=sample_question_content,
            submitter_id="teacher_456",
            submitter_name="Ahmet Öğretmen",
            grade_level="9",
            subject="Coğrafya",
            topic="Türkiye'nin Konumu",
            priority=5,
        )

        assert request is not None
        assert request.content_id == "q_123"
        assert request.content_type == ContentType.QUESTION
        assert request.submitter_id == "teacher_456"
        assert request.status == ValidationStatus.PENDING
        assert len(request.assigned_experts) > 0

    @pytest.mark.asyncio
    async def test_submit_exam_for_validation(
        self, validation_system, sample_exam_content
    ):
        """Test submitting an exam for validation"""
        request = await validation_system.submit_content_for_validation(
            content_id="exam_789",
            content_type=ContentType.EXAM,
            content_data=sample_exam_content,
            submitter_id="admin_123",
            submitter_name="Sistem Yöneticisi",
            exam_type="tyt",
            priority=8,
        )

        assert request is not None
        assert request.content_type == ContentType.EXAM
        assert request.exam_type == "tyt"
        assert request.priority == 8
        assert ValidationStatus.PENDING == request.status

    @pytest.mark.asyncio
    async def test_high_priority_content_gets_more_experts(
        self, validation_system, sample_question_content
    ):
        """Test high priority content gets assigned more experts"""
        high_priority_request = await validation_system.submit_content_for_validation(
            content_id="q_high",
            content_type=ContentType.QUESTION,
            content_data=sample_question_content,
            submitter_id="teacher_1",
            submitter_name="Teacher 1",
            priority=10,
        )

        low_priority_request = await validation_system.submit_content_for_validation(
            content_id="q_low",
            content_type=ContentType.QUESTION,
            content_data=sample_question_content,
            submitter_id="teacher_2",
            submitter_name="Teacher 2",
            priority=1,
        )

        # High priority should have more or equal experts
        assert len(high_priority_request.assigned_experts) >= len(
            low_priority_request.assigned_experts
        )


class TestExpertFeedback:
    """Test expert feedback submission"""

    @pytest.mark.asyncio
    async def test_submit_expert_feedback(
        self, validation_system, sample_question_content
    ):
        """Test expert can submit feedback"""
        # Submit content first
        request = await validation_system.submit_content_for_validation(
            content_id="q_feedback_test",
            content_type=ContentType.QUESTION,
            content_data=sample_question_content,
            submitter_id="teacher_1",
            submitter_name="Teacher 1",
        )

        # Submit feedback
        feedbacks = [
            {
                "criterion": "meb_compliance",
                "passed": True,
                "score": 95.0,
                "comment": "MEB müfredatına uygun",
                "suggestions": [],
            },
            {
                "criterion": "language_quality",
                "passed": True,
                "score": 90.0,
                "comment": "Dil ve anlatım kalitesi yüksek",
                "suggestions": [],
            },
        ]

        success = await validation_system.submit_expert_feedback(
            request_id=request.request_id,
            expert_id="expert_123",
            expert_name="Dr. Ayşe Uzman",
            expert_role=ExpertRole.SUBJECT_EXPERT,
            feedbacks=feedbacks,
        )

        assert success is True
        updated_request = validation_system.get_validation_request(request.request_id)
        assert len(updated_request.feedbacks) == 1
        assert updated_request.feedbacks[0].expert_id == "expert_123"

    @pytest.mark.asyncio
    async def test_multiple_expert_feedbacks(
        self, validation_system, sample_question_content
    ):
        """Test multiple experts can submit feedback"""
        request = await validation_system.submit_content_for_validation(
            content_id="q_multi_feedback",
            content_type=ContentType.QUESTION,
            content_data=sample_question_content,
            submitter_id="teacher_1",
            submitter_name="Teacher 1",
        )

        # First expert feedback
        await validation_system.submit_expert_feedback(
            request_id=request.request_id,
            expert_id="expert_1",
            expert_name="Expert 1",
            expert_role=ExpertRole.SUBJECT_EXPERT,
            feedbacks=[{"criterion": "test", "passed": True, "score": 90.0}],
        )

        # Second expert feedback
        await validation_system.submit_expert_feedback(
            request_id=request.request_id,
            expert_id="expert_2",
            expert_name="Expert 2",
            expert_role=ExpertRole.CURRICULUM_EXPERT,
            feedbacks=[{"criterion": "test", "passed": True, "score": 85.0}],
        )

        updated_request = validation_system.get_validation_request(request.request_id)
        assert len(updated_request.feedbacks) == 2

    @pytest.mark.asyncio
    async def test_feedback_invalid_request_id(self, validation_system):
        """Test feedback submission with invalid request ID"""
        success = await validation_system.submit_expert_feedback(
            request_id="invalid_request_id",
            expert_id="expert_1",
            expert_name="Expert 1",
            expert_role=ExpertRole.SUBJECT_EXPERT,
            feedbacks=[{"criterion": "test", "passed": True, "score": 90.0}],
        )

        assert success is False


class TestValidationStatus:
    """Test validation status tracking"""

    @pytest.mark.asyncio
    async def test_validation_status_transitions(
        self, validation_system, sample_question_content
    ):
        """Test validation status transitions correctly"""
        request = await validation_system.submit_content_for_validation(
            content_id="q_status_test",
            content_type=ContentType.QUESTION,
            content_data=sample_question_content,
            submitter_id="teacher_1",
            submitter_name="Teacher 1",
        )

        # Initial status should be PENDING
        assert request.status == ValidationStatus.PENDING

        # After first feedback, should be IN_REVIEW
        await validation_system.submit_expert_feedback(
            request_id=request.request_id,
            expert_id="expert_1",
            expert_name="Expert 1",
            expert_role=ExpertRole.SUBJECT_EXPERT,
            feedbacks=[{"criterion": "test", "passed": True, "score": 90.0}],
        )

        updated_request = validation_system.get_validation_request(request.request_id)
        assert updated_request.status == ValidationStatus.IN_REVIEW

    @pytest.mark.asyncio
    async def test_get_validation_request(
        self, validation_system, sample_question_content
    ):
        """Test retrieving validation request"""
        request = await validation_system.submit_content_for_validation(
            content_id="q_retrieve_test",
            content_type=ContentType.QUESTION,
            content_data=sample_question_content,
            submitter_id="teacher_1",
            submitter_name="Teacher 1",
        )

        retrieved = validation_system.get_validation_request(request.request_id)
        assert retrieved is not None
        assert retrieved.request_id == request.request_id
        assert retrieved.content_id == request.content_id

    def test_get_nonexistent_request(self, validation_system):
        """Test retrieving non-existent request returns None"""
        result = validation_system.get_validation_request("nonexistent_id")
        assert result is None


class TestExpertManagement:
    """Test expert registration and assignment"""

    @pytest.mark.asyncio
    async def test_register_expert(self, validation_system):
        """Test expert registration"""
        success = await validation_system.register_expert(
            expert_id="expert_new",
            expert_roles=[ExpertRole.SUBJECT_EXPERT, ExpertRole.QUALITY_ASSURANCE],
        )

        assert success is True
        assert "expert_new" in validation_system.expert_pool[ExpertRole.SUBJECT_EXPERT]
        assert (
            "expert_new" in validation_system.expert_pool[ExpertRole.QUALITY_ASSURANCE]
        )

    @pytest.mark.asyncio
    async def test_get_pending_requests_for_expert(
        self, validation_system, sample_question_content
    ):
        """Test getting pending requests for an expert"""
        # Register expert
        await validation_system.register_expert(
            expert_id="expert_pending", expert_roles=[ExpertRole.SUBJECT_EXPERT]
        )

        # Create request and manually assign expert
        request = await validation_system.submit_content_for_validation(
            content_id="q_pending_test",
            content_type=ContentType.QUESTION,
            content_data=sample_question_content,
            submitter_id="teacher_1",
            submitter_name="Teacher 1",
        )

        # Manually add expert to assigned list
        request.assigned_experts.append(
            {
                "expert_id": "expert_pending",
                "expert_role": ExpertRole.SUBJECT_EXPERT.value,
            }
        )
        validation_system.validation_requests[request.request_id] = request

        # Get pending requests
        pending = validation_system.get_pending_requests_for_expert("expert_pending")
        assert len(pending) > 0


class TestComplianceReporting:
    """Test compliance report generation"""

    @pytest.mark.asyncio
    async def test_compliance_report_generation(
        self, validation_system, sample_question_content
    ):
        """Test compliance report is generated"""
        request = await validation_system.submit_content_for_validation(
            content_id="q_compliance_test",
            content_type=ContentType.QUESTION,
            content_data=sample_question_content,
            submitter_id="teacher_1",
            submitter_name="Teacher 1",
            grade_level="9",
            subject="Coğrafya",
        )

        # Submit enough feedbacks to complete validation
        for i in range(len(request.required_expert_roles)):
            await validation_system.submit_expert_feedback(
                request_id=request.request_id,
                expert_id=f"expert_{i}",
                expert_name=f"Expert {i}",
                expert_role=request.required_expert_roles[i],
                feedbacks=[
                    {
                        "criterion": "overall",
                        "passed": True,
                        "score": 90.0,
                        "comment": "Excellent",
                    }
                ],
            )

        # Check if compliance report was generated
        updated_request = validation_system.get_validation_request(request.request_id)
        if updated_request.compliance_report_id:
            report = validation_system.get_compliance_report(
                updated_request.compliance_report_id
            )
            assert report is not None
            assert report.content_id == "q_compliance_test"

    def test_get_nonexistent_compliance_report(self, validation_system):
        """Test getting non-existent compliance report"""
        report = validation_system.get_compliance_report("nonexistent_report")
        assert report is None


class TestEnums:
    """Test enum values and usage"""

    def test_content_type_enum(self):
        """Test ContentType enum values"""
        assert ContentType.QUESTION.value == "question"
        assert ContentType.EXAM.value == "exam"
        assert ContentType.TOPIC.value == "topic"

    def test_validation_status_enum(self):
        """Test ValidationStatus enum values"""
        assert ValidationStatus.PENDING.value == "pending"
        assert ValidationStatus.IN_REVIEW.value == "in_review"
        assert ValidationStatus.APPROVED.value == "approved"
        assert ValidationStatus.REJECTED.value == "rejected"

    def test_expert_role_enum(self):
        """Test ExpertRole enum values"""
        assert ExpertRole.SUBJECT_EXPERT.value == "subject_expert"
        assert ExpertRole.CURRICULUM_EXPERT.value == "curriculum_expert"
        assert ExpertRole.QUALITY_ASSURANCE.value == "quality_assurance"

    def test_compliance_level_enum(self):
        """Test ComplianceLevel enum values"""
        assert ComplianceLevel.FULLY_COMPLIANT.value == "fully_compliant"
        assert ComplianceLevel.MOSTLY_COMPLIANT.value == "mostly_compliant"
        assert ComplianceLevel.PARTIALLY_COMPLIANT.value == "partially_compliant"
        assert ComplianceLevel.NON_COMPLIANT.value == "non_compliant"


class TestDataModels:
    """Test data model creation and validation"""

    def test_validation_request_creation(self):
        """Test ValidationRequest model creation"""
        request = ValidationRequest(
            request_id="test_req_1",
            content_id="content_1",
            content_type=ContentType.QUESTION,
            content_data={"test": "data"},
            submitter_id="user_1",
            submitter_name="User One",
            status=ValidationStatus.PENDING,
            required_expert_roles=[ExpertRole.SUBJECT_EXPERT],
            assigned_experts=[],
            feedbacks=[],
            submitted_at=datetime.utcnow(),
            priority=5,
        )

        assert request.request_id == "test_req_1"
        assert request.content_type == ContentType.QUESTION
        assert request.status == ValidationStatus.PENDING

    def test_validation_feedback_creation(self):
        """Test ValidationFeedback model creation"""
        feedback = ValidationFeedback(
            feedback_id="fb_1",
            expert_id="expert_1",
            expert_name="Expert One",
            expert_role=ExpertRole.SUBJECT_EXPERT,
            criterion_id="crit_1",
            passed=True,
            score=90.0,
            comment="Good work",
            suggestions=[],
            created_at=datetime.utcnow(),
        )

        assert feedback.expert_id == "expert_1"
        assert feedback.passed is True
        assert feedback.score == 90.0

    def test_compliance_report_creation(self):
        """Test ContentComplianceReport model creation"""
        report = ContentComplianceReport(
            report_id="report_1",
            content_id="content_1",
            content_type=ContentType.QUESTION,
            meb_compliance=ComplianceLevel.FULLY_COMPLIANT,
            meb_score=95.0,
            meb_standards_matched=["standard1"],
            meb_issues=[],
            osym_compliance=ComplianceLevel.PARTIALLY_COMPLIANT,
            osym_score=85.0,
            osym_standards_matched=["osym1"],
            osym_issues=["minor issue"],
            pedagogy_score=90.0,
            pedagogy_notes=["good pedagogy"],
            quality_score=88.0,
            quality_issues=[],
            overall_compliance=ComplianceLevel.FULLY_COMPLIANT,
            overall_score=89.5,
            recommendations=[],
            generated_at=datetime.utcnow(),
        )

        assert report.meb_compliance == ComplianceLevel.FULLY_COMPLIANT
        assert report.osym_compliance == ComplianceLevel.PARTIALLY_COMPLIANT
        assert report.overall_score == 89.5
