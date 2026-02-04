"""
KVKK Compliance System Tests
Comprehensive test suite for Turkish GDPR compliance

Test Coverage:
- Consent management (grant, withdraw, check)
- Data processing logging
- Data subject requests (access, rectification, erasure, portability)
- Data breach reporting
- User data export and anonymization
- Compliance reporting
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from core.kvkk_compliance import (
    KVKKComplianceManager,
    DataProcessingPurpose,
    ConsentType,
    DataCategory,
    DataSubjectRight,
    ConsentStatus,
    ConsentRequest,
    ConsentResponse,
    DataProcessingLogRequest,
    DataSubjectRequestModel,
    DataBreachReport,
    KVKKConsent,
    KVKKDataProcessingLog,
    KVKKDataSubjectRequest,
    KVKKDataBreach,
    get_kvkk_manager,
)


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = AsyncMock()
    session.add = Mock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.query = Mock()
    return session


@pytest.fixture
def kvkk_manager(mock_db_session):
    """KVKK Compliance Manager fixture"""
    return KVKKComplianceManager(mock_db_session)


@pytest.fixture
def sample_consent_request():
    """Sample consent request"""
    return ConsentRequest(
        user_id=1,
        purpose=DataProcessingPurpose.EDUCATION,
        consent_type=ConsentType.EXPLICIT,
        consent_text="Eğitim hizmetleri için kişisel verilerimin işlenmesine onay veriyorum.",
        consent_version="1.0",
        expires_in_days=365,
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0",
        consent_method="web",
    )


@pytest.fixture
def sample_data_processing_log():
    """Sample data processing log request"""
    return DataProcessingLogRequest(
        user_id=1,
        data_category=DataCategory.EDUCATION,
        purpose=DataProcessingPurpose.EXAM_MANAGEMENT,
        operation="create",
        data_fields=["exam_score", "subject_performance"],
        legal_basis="KVKK Madde 5/2-c - Sözleşmenin ifası",
        consent_id=str(uuid4()),
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0",
        service_name="exam_service",
    )


class TestConsentManagement:
    """Test consent management functionality"""

    @pytest.mark.asyncio
    async def test_grant_consent_success(
        self, kvkk_manager, sample_consent_request, mock_db_session
    ):
        """Test successful consent granting"""
        # Mock database operations
        mock_consent = Mock()
        mock_consent.consent_id = str(uuid4())
        mock_consent.granted_at = datetime.utcnow()
        mock_consent.expires_at = datetime.utcnow() + timedelta(days=365)

        mock_db_session.refresh.side_effect = lambda obj: setattr(
            obj, "consent_id", mock_consent.consent_id
        )

        # Grant consent
        response = await kvkk_manager.grant_consent(sample_consent_request)

        # Assertions
        assert isinstance(response, ConsentResponse)
        assert response.status == ConsentStatus.GRANTED
        assert response.granted_at is not None
        assert response.expires_at is not None

        # Verify database operations
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_grant_consent_without_expiry(self, kvkk_manager, mock_db_session):
        """Test consent granting without expiry date"""
        request = ConsentRequest(
            user_id=1,
            purpose=DataProcessingPurpose.EDUCATION,
            consent_type=ConsentType.EXPLICIT,
            consent_text="Test consent",
            consent_version="1.0",
            expires_in_days=None,
        )

        mock_consent = Mock()
        mock_consent.consent_id = str(uuid4())
        mock_consent.granted_at = datetime.utcnow()
        mock_consent.expires_at = None

        mock_db_session.refresh.side_effect = lambda obj: setattr(
            obj, "consent_id", mock_consent.consent_id
        )

        response = await kvkk_manager.grant_consent(request)

        assert response.status == ConsentStatus.GRANTED
        assert response.expires_at is None

    @pytest.mark.asyncio
    async def test_withdraw_consent_success(self, kvkk_manager, mock_db_session):
        """Test successful consent withdrawal"""
        user_id = 1
        consent_id = str(uuid4())

        # Mock existing consent
        mock_consent = Mock()
        mock_consent.consent_id = consent_id
        mock_consent.user_id = user_id
        mock_consent.status = ConsentStatus.GRANTED.value

        mock_query = Mock()
        mock_query.filter.return_value.first = AsyncMock(return_value=mock_consent)
        mock_db_session.query.return_value = mock_query

        # Withdraw consent
        result = await kvkk_manager.withdraw_consent(user_id, consent_id)

        # Assertions
        assert result is True
        assert mock_consent.status == ConsentStatus.WITHDRAWN.value
        assert mock_consent.withdrawn_at is not None
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_withdraw_consent_not_found(self, kvkk_manager, mock_db_session):
        """Test consent withdrawal when consent not found"""
        user_id = 1
        consent_id = str(uuid4())

        mock_query = Mock()
        mock_query.filter.return_value.first = AsyncMock(return_value=None)
        mock_db_session.query.return_value = mock_query

        result = await kvkk_manager.withdraw_consent(user_id, consent_id)

        assert result is False
        mock_db_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_consent_valid(self, kvkk_manager, mock_db_session):
        """Test checking valid consent"""
        user_id = 1
        purpose = DataProcessingPurpose.EDUCATION

        # Mock valid consent
        mock_consent = Mock()
        mock_consent.status = ConsentStatus.GRANTED.value
        mock_consent.expires_at = datetime.utcnow() + timedelta(days=30)

        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.first = AsyncMock(
            return_value=mock_consent
        )
        mock_db_session.query.return_value = mock_query

        result = await kvkk_manager.check_consent(user_id, purpose)

        assert result is True

    @pytest.mark.asyncio
    async def test_check_consent_expired(self, kvkk_manager, mock_db_session):
        """Test checking expired consent"""
        user_id = 1
        purpose = DataProcessingPurpose.EDUCATION

        # Mock expired consent
        mock_consent = Mock()
        mock_consent.status = ConsentStatus.GRANTED.value
        mock_consent.expires_at = datetime.utcnow() - timedelta(days=1)

        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.first = AsyncMock(
            return_value=mock_consent
        )
        mock_db_session.query.return_value = mock_query

        result = await kvkk_manager.check_consent(user_id, purpose)

        assert result is False
        assert mock_consent.status == ConsentStatus.EXPIRED.value
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_consent_not_found(self, kvkk_manager, mock_db_session):
        """Test checking non-existent consent"""
        user_id = 1
        purpose = DataProcessingPurpose.EDUCATION

        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.first = AsyncMock(
            return_value=None
        )
        mock_db_session.query.return_value = mock_query

        result = await kvkk_manager.check_consent(user_id, purpose)

        assert result is False


class TestDataProcessingLogging:
    """Test data processing logging functionality"""

    @pytest.mark.asyncio
    async def test_log_data_processing_success(
        self, kvkk_manager, sample_data_processing_log, mock_db_session
    ):
        """Test successful data processing logging"""
        mock_log = Mock()
        mock_log.log_id = str(uuid4())

        mock_db_session.refresh.side_effect = lambda obj: setattr(
            obj, "log_id", mock_log.log_id
        )

        log_id = await kvkk_manager.log_data_processing(sample_data_processing_log)

        assert log_id is not None
        assert isinstance(log_id, str)
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_data_processing_all_categories(
        self, kvkk_manager, mock_db_session
    ):
        """Test logging for all data categories"""
        for category in DataCategory:
            request = DataProcessingLogRequest(
                user_id=1,
                data_category=category,
                purpose=DataProcessingPurpose.EDUCATION,
                operation="read",
                data_fields=["test_field"],
                legal_basis="Test basis",
            )

            mock_log = Mock()
            mock_log.log_id = str(uuid4())
            mock_db_session.refresh.side_effect = lambda obj: setattr(
                obj, "log_id", mock_log.log_id
            )

            log_id = await kvkk_manager.log_data_processing(request)
            assert log_id is not None


class TestDataSubjectRequests:
    """Test data subject request functionality"""

    @pytest.mark.asyncio
    async def test_create_data_subject_request(self, kvkk_manager, mock_db_session):
        """Test creating data subject request"""
        request = DataSubjectRequestModel(
            user_id=1,
            request_type=DataSubjectRight.ACCESS,
            description="Kişisel verilerimi görmek istiyorum",
        )

        mock_request = Mock()
        mock_request.request_id = str(uuid4())
        mock_db_session.refresh.side_effect = lambda obj: setattr(
            obj, "request_id", mock_request.request_id
        )

        request_id = await kvkk_manager.create_data_subject_request(request)

        assert request_id is not None
        assert isinstance(request_id, str)
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_all_request_types(self, kvkk_manager, mock_db_session):
        """Test creating all types of data subject requests"""
        for right in DataSubjectRight:
            request = DataSubjectRequestModel(
                user_id=1,
                request_type=right,
                description=f"Test request for {right.value}",
            )

            mock_request = Mock()
            mock_request.request_id = str(uuid4())
            mock_db_session.refresh.side_effect = lambda obj: setattr(
                obj, "request_id", mock_request.request_id
            )

            request_id = await kvkk_manager.create_data_subject_request(request)
            assert request_id is not None

    @pytest.mark.asyncio
    async def test_process_data_subject_request_success(
        self, kvkk_manager, mock_db_session
    ):
        """Test processing data subject request"""
        request_id = str(uuid4())
        response_text = "Talebiniz işleme alınmıştır"

        mock_request = Mock()
        mock_request.request_id = request_id
        mock_request.status = "pending"

        mock_query = Mock()
        mock_query.filter.return_value.first = AsyncMock(return_value=mock_request)
        mock_db_session.query.return_value = mock_query

        result = await kvkk_manager.process_data_subject_request(
            request_id, response_text, "completed"
        )

        assert result is True
        assert mock_request.status == "completed"
        assert mock_request.response == response_text
        assert mock_request.response_date is not None
        assert mock_request.completed_at is not None
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_data_subject_request_not_found(
        self, kvkk_manager, mock_db_session
    ):
        """Test processing non-existent request"""
        request_id = str(uuid4())

        mock_query = Mock()
        mock_query.filter.return_value.first = AsyncMock(return_value=None)
        mock_db_session.query.return_value = mock_query

        result = await kvkk_manager.process_data_subject_request(
            request_id, "Response", "completed"
        )

        assert result is False
        mock_db_session.commit.assert_not_called()


class TestDataBreachReporting:
    """Test data breach reporting functionality"""

    @pytest.mark.asyncio
    async def test_report_data_breach_low_severity(self, kvkk_manager, mock_db_session):
        """Test reporting low severity data breach"""
        report = DataBreachReport(
            severity="low",
            description="Minor data exposure",
            affected_users_count=5,
            data_categories=[DataCategory.TECHNICAL],
            detected_at=datetime.utcnow(),
            mitigation_actions=["Password reset", "User notification"],
        )

        mock_breach = Mock()
        mock_breach.breach_id = str(uuid4())
        mock_db_session.refresh.side_effect = lambda obj: setattr(
            obj, "breach_id", mock_breach.breach_id
        )

        breach_id = await kvkk_manager.report_data_breach(report)

        assert breach_id is not None
        assert isinstance(breach_id, str)
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_report_data_breach_critical_severity(
        self, kvkk_manager, mock_db_session
    ):
        """Test reporting critical severity data breach"""
        report = DataBreachReport(
            severity="critical",
            description="Major data breach with identity theft risk",
            affected_users_count=10000,
            data_categories=[DataCategory.IDENTITY, DataCategory.FINANCIAL],
            detected_at=datetime.utcnow(),
            mitigation_actions=[
                "System lockdown",
                "KVKK notification",
                "User notification",
            ],
        )

        mock_breach = Mock()
        mock_breach.breach_id = str(uuid4())
        mock_db_session.refresh.side_effect = lambda obj: setattr(
            obj, "breach_id", mock_breach.breach_id
        )

        with patch("backend.core.kvkk_compliance.logger") as mock_logger:
            breach_id = await kvkk_manager.report_data_breach(report)

            assert breach_id is not None
            mock_logger.critical.assert_called_once()


class TestUserDataManagement:
    """Test user data export and anonymization"""

    @pytest.mark.asyncio
    async def test_get_user_data_export(self, kvkk_manager, mock_db_session):
        """Test user data export"""
        user_id = 1

        # Mock consents
        mock_consent = Mock()
        mock_consent.consent_id = str(uuid4())
        mock_consent.purpose = "education"
        mock_consent.status = "granted"
        mock_consent.granted_at = datetime.utcnow()
        mock_consent.withdrawn_at = None

        # Mock logs
        mock_log = Mock()
        mock_log.log_id = str(uuid4())
        mock_log.data_category = "education"
        mock_log.purpose = "exam_management"
        mock_log.operation = "create"
        mock_log.processed_at = datetime.utcnow()

        # Mock requests
        mock_request = Mock()
        mock_request.request_id = str(uuid4())
        mock_request.request_type = "access"
        mock_request.status = "completed"
        mock_request.requested_at = datetime.utcnow()
        mock_request.completed_at = datetime.utcnow()

        # Setup query mocks
        def query_side_effect(model):
            mock_query = Mock()
            if model == KVKKConsent:
                mock_query.filter.return_value.all = AsyncMock(
                    return_value=[mock_consent]
                )
            elif model == KVKKDataProcessingLog:
                mock_query.filter.return_value.all = AsyncMock(return_value=[mock_log])
            elif model == KVKKDataSubjectRequest:
                mock_query.filter.return_value.all = AsyncMock(
                    return_value=[mock_request]
                )
            return mock_query

        mock_db_session.query.side_effect = query_side_effect

        user_data = await kvkk_manager.get_user_data_export(user_id)

        assert user_data["user_id"] == user_id
        assert "export_date" in user_data
        assert len(user_data["consents"]) == 1
        assert len(user_data["processing_logs"]) == 1
        assert len(user_data["requests"]) == 1

    @pytest.mark.asyncio
    async def test_anonymize_user_data(self, kvkk_manager, mock_db_session):
        """Test user data anonymization"""
        user_id = 1

        # Mock consents
        mock_consent = Mock()
        mock_consent.ip_address = "192.168.1.100"
        mock_consent.user_agent = "Mozilla/5.0"

        # Mock logs
        mock_log = Mock()
        mock_log.ip_address = "192.168.1.100"
        mock_log.user_agent = "Mozilla/5.0"

        # Setup query mocks
        def query_side_effect(model):
            mock_query = Mock()
            if model == KVKKConsent:
                mock_query.filter.return_value.all = AsyncMock(
                    return_value=[mock_consent]
                )
            elif model == KVKKDataProcessingLog:
                mock_query.filter.return_value.all = AsyncMock(return_value=[mock_log])
            return mock_query

        mock_db_session.query.side_effect = query_side_effect

        result = await kvkk_manager.anonymize_user_data(user_id)

        assert result is True
        assert mock_consent.ip_address == "192.168.1.0"
        assert mock_consent.user_agent == "ANONYMIZED"
        assert mock_log.ip_address == "192.168.1.0"
        assert mock_log.user_agent == "ANONYMIZED"
        mock_db_session.commit.assert_called_once()

    def test_anonymize_ip_ipv4(self, kvkk_manager):
        """Test IPv4 anonymization"""
        ip = "192.168.1.100"
        anonymized = kvkk_manager._anonymize_ip(ip)
        assert anonymized == "192.168.1.0"

    def test_anonymize_ip_ipv6(self, kvkk_manager):
        """Test IPv6 anonymization"""
        ip = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        anonymized = kvkk_manager._anonymize_ip(ip)
        assert anonymized == "2001:0db8:85a3:0000::0"

    def test_anonymize_ip_none(self, kvkk_manager):
        """Test None IP anonymization"""
        anonymized = kvkk_manager._anonymize_ip(None)
        assert anonymized == "0.0.0.0"


class TestComplianceReporting:
    """Test compliance reporting functionality"""

    @pytest.mark.asyncio
    async def test_get_compliance_report(self, kvkk_manager, mock_db_session):
        """Test compliance report generation"""
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()

        # Mock consents
        mock_consent_granted = Mock()
        mock_consent_granted.status = ConsentStatus.GRANTED.value

        mock_consent_withdrawn = Mock()
        mock_consent_withdrawn.status = ConsentStatus.WITHDRAWN.value

        # Mock logs
        mock_log = Mock()
        mock_log.purpose = "education"
        mock_log.data_category = "education"

        # Mock requests
        mock_request_pending = Mock()
        mock_request_pending.status = "pending"
        mock_request_pending.deadline = datetime.utcnow() + timedelta(days=10)

        mock_request_completed = Mock()
        mock_request_completed.status = "completed"

        # Mock breaches
        mock_breach = Mock()
        mock_breach.severity = "low"
        mock_breach.reported_to_kvkk = True

        # Setup query mocks
        def query_side_effect(model):
            mock_query = Mock()
            if model == KVKKConsent:
                mock_query.filter.return_value.all = AsyncMock(
                    return_value=[mock_consent_granted, mock_consent_withdrawn]
                )
            elif model == KVKKDataProcessingLog:
                mock_query.filter.return_value.all = AsyncMock(return_value=[mock_log])
            elif model == KVKKDataSubjectRequest:
                mock_query.filter.return_value.all = AsyncMock(
                    return_value=[mock_request_pending, mock_request_completed]
                )
            elif model == KVKKDataBreach:
                mock_query.filter.return_value.all = AsyncMock(
                    return_value=[mock_breach]
                )
            return mock_query

        mock_db_session.query.side_effect = query_side_effect

        report = await kvkk_manager.get_compliance_report(start_date, end_date)

        assert report["consents"]["total"] == 2
        assert report["consents"]["granted"] == 1
        assert report["consents"]["withdrawn"] == 1
        assert report["data_processing"]["total_operations"] == 1
        assert report["data_subject_requests"]["total"] == 2
        assert report["data_subject_requests"]["pending"] == 1
        assert report["data_subject_requests"]["completed"] == 1
        assert report["data_breaches"]["total"] == 1
        assert report["data_breaches"]["reported_to_kvkk"] == 1


class TestConsentTexts:
    """Test consent text templates"""

    def test_consent_texts_exist(self, kvkk_manager):
        """Test that consent texts are defined"""
        assert DataProcessingPurpose.EDUCATION in kvkk_manager.consent_texts
        assert DataProcessingPurpose.EXAM_MANAGEMENT in kvkk_manager.consent_texts
        assert DataProcessingPurpose.MARKETING in kvkk_manager.consent_texts

    def test_consent_texts_turkish(self, kvkk_manager):
        """Test that consent texts are in Turkish"""
        for purpose, text in kvkk_manager.consent_texts.items():
            # Check for Turkish GDPR keywords
            text_lower = text.lower()
            has_kvkk_keywords = (
                "kvkk" in text
                or "kişisel veri" in text_lower
                or "kisisel veri" in text_lower
                or "verileriniz" in text_lower
            )
            assert (
                has_kvkk_keywords
            ), f"Text for {purpose} doesn't contain KVKK keywords"
            assert len(text) > 50  # Meaningful text


class TestEnums:
    """Test enum definitions"""

    def test_data_processing_purpose_enum(self):
        """Test DataProcessingPurpose enum"""
        assert DataProcessingPurpose.EDUCATION.value == "education"
        assert DataProcessingPurpose.EXAM_MANAGEMENT.value == "exam_management"
        assert DataProcessingPurpose.MARKETING.value == "marketing"

    def test_consent_type_enum(self):
        """Test ConsentType enum"""
        assert ConsentType.EXPLICIT.value == "explicit"
        assert ConsentType.IMPLIED.value == "implied"

    def test_data_category_enum(self):
        """Test DataCategory enum"""
        assert DataCategory.IDENTITY.value == "identity"
        assert DataCategory.EDUCATION.value == "education"
        assert DataCategory.HEALTH.value == "health"

    def test_data_subject_right_enum(self):
        """Test DataSubjectRight enum"""
        assert DataSubjectRight.ACCESS.value == "access"
        assert DataSubjectRight.ERASURE.value == "erasure"
        assert DataSubjectRight.PORTABILITY.value == "portability"

    def test_consent_status_enum(self):
        """Test ConsentStatus enum"""
        assert ConsentStatus.PENDING.value == "pending"
        assert ConsentStatus.GRANTED.value == "granted"
        assert ConsentStatus.WITHDRAWN.value == "withdrawn"
        assert ConsentStatus.EXPIRED.value == "expired"


class TestGlobalInstance:
    """Test global instance management"""

    def test_get_kvkk_manager(self, mock_db_session):
        """Test get_kvkk_manager function"""
        manager = get_kvkk_manager(mock_db_session)
        assert isinstance(manager, KVKKComplianceManager)
        assert manager.db == mock_db_session


class TestPydanticModels:
    """Test Pydantic model validation"""

    def test_consent_request_validation(self):
        """Test ConsentRequest validation"""
        request = ConsentRequest(
            user_id=1,
            purpose=DataProcessingPurpose.EDUCATION,
            consent_text="Test consent",
        )
        assert request.user_id == 1
        assert request.consent_version == "1.0"
        assert request.consent_method == "web"

    def test_data_processing_log_request_validation(self):
        """Test DataProcessingLogRequest validation"""
        request = DataProcessingLogRequest(
            user_id=1,
            data_category=DataCategory.EDUCATION,
            purpose=DataProcessingPurpose.EDUCATION,
            operation="create",
            data_fields=["field1", "field2"],
            legal_basis="Test basis",
        )
        assert request.user_id == 1
        assert len(request.data_fields) == 2

    def test_data_subject_request_validation(self):
        """Test DataSubjectRequestModel validation"""
        request = DataSubjectRequestModel(
            user_id=1, request_type=DataSubjectRight.ACCESS
        )
        assert request.user_id == 1
        assert request.description is None

    def test_data_breach_report_validation(self):
        """Test DataBreachReport validation"""
        report = DataBreachReport(
            severity="high",
            description="Test breach",
            affected_users_count=100,
            data_categories=[DataCategory.IDENTITY],
            detected_at=datetime.utcnow(),
        )
        assert report.severity == "high"
        assert report.affected_users_count == 100


if __name__ == "__main__":
    pytest.main(
        [
            __file__,
            "-v",
            "--cov=backend.core.kvkk_compliance",
            "--cov-report=term-missing",
        ]
    )
