"""
Fast unit tests for KVKK compliance system
Tests: Enums, Models, Basic operations
Coverage target: 60-80% of core.kvkk_compliance
"""


class TestKVKKEnums:
    """Test KVKK enum definitions"""

    def test_data_processing_purpose_enum(self):
        """Test DataProcessingPurpose enum values"""
        from core.kvkk_compliance import DataProcessingPurpose

        assert DataProcessingPurpose.EDUCATION == "education"
        assert DataProcessingPurpose.EXAM_MANAGEMENT == "exam_management"
        assert DataProcessingPurpose.PERFORMANCE_TRACKING == "performance_tracking"
        assert DataProcessingPurpose.COMMUNICATION == "communication"
        assert DataProcessingPurpose.LEGAL_OBLIGATION == "legal_obligation"
        assert DataProcessingPurpose.SECURITY == "security"
        assert DataProcessingPurpose.ANALYTICS == "analytics"
        assert DataProcessingPurpose.MARKETING == "marketing"

    def test_consent_type_enum(self):
        """Test ConsentType enum values"""
        from core.kvkk_compliance import ConsentType

        assert ConsentType.EXPLICIT == "explicit"
        assert ConsentType.IMPLIED == "implied"
        assert ConsentType.LEGAL_BASIS == "legal_basis"
        assert ConsentType.LEGITIMATE_INTEREST == "legitimate_interest"

    def test_data_category_enum(self):
        """Test DataCategory enum values"""
        from core.kvkk_compliance import DataCategory

        assert DataCategory.IDENTITY == "identity"
        assert DataCategory.CONTACT == "contact"
        assert DataCategory.EDUCATION == "education"
        assert DataCategory.HEALTH == "health"
        assert DataCategory.BIOMETRIC == "biometric"
        assert DataCategory.LOCATION == "location"
        assert DataCategory.FINANCIAL == "financial"
        assert DataCategory.BEHAVIORAL == "behavioral"
        assert DataCategory.TECHNICAL == "technical"

    def test_data_subject_right_enum(self):
        """Test DataSubjectRight enum values"""
        from core.kvkk_compliance import DataSubjectRight

        assert DataSubjectRight.ACCESS == "access"
        assert DataSubjectRight.RECTIFICATION == "rectification"
        assert DataSubjectRight.ERASURE == "erasure"
        assert DataSubjectRight.RESTRICTION == "restriction"
        assert DataSubjectRight.OBJECTION == "objection"
        assert DataSubjectRight.PORTABILITY == "portability"
        assert DataSubjectRight.COMPLAINT == "complaint"

    def test_consent_status_enum(self):
        """Test ConsentStatus enum values"""
        from core.kvkk_compliance import ConsentStatus

        assert ConsentStatus.PENDING == "pending"
        assert ConsentStatus.GRANTED == "granted"
        assert ConsentStatus.WITHDRAWN == "withdrawn"
        assert ConsentStatus.EXPIRED == "expired"


class TestKVKKConsentModel:
    """Test KVKKConsent database model"""

    def test_kvkk_consent_table_name(self):
        """Test table name"""
        from core.kvkk_compliance import KVKKConsent

        assert KVKKConsent.__tablename__ == "kvkk_consents"

    def test_kvkk_consent_has_required_columns(self):
        """Test model has required columns"""
        from core.kvkk_compliance import KVKKConsent

        required_columns = [
            "id",
            "consent_id",
            "user_id",
            "purpose",
            "consent_type",
            "status",
            "consent_text",
            "consent_version",
        ]

        for col in required_columns:
            assert hasattr(KVKKConsent, col)


class TestKVKKDataProcessingLog:
    """Test KVKKDataProcessingLog model"""

    def test_data_processing_log_table_name(self):
        """Test table name"""
        from core.kvkk_compliance import KVKKDataProcessingLog

        assert KVKKDataProcessingLog.__tablename__ == "kvkk_data_processing_logs"

    def test_data_processing_log_has_required_columns(self):
        """Test model has required columns"""
        from core.kvkk_compliance import KVKKDataProcessingLog

        required_columns = [
            "id",
            "log_id",
            "user_id",
            "data_category",
            "purpose",
            "operation",
            "data_fields",
            "legal_basis",
        ]

        for col in required_columns:
            assert hasattr(KVKKDataProcessingLog, col)


class TestKVKKDataSubjectRequest:
    """Test KVKKDataSubjectRequest model"""

    def test_data_subject_request_table_name(self):
        """Test table name"""
        from core.kvkk_compliance import KVKKDataSubjectRequest

        assert KVKKDataSubjectRequest.__tablename__ == "kvkk_data_subject_requests"

    def test_data_subject_request_has_required_columns(self):
        """Test model has required columns"""
        from core.kvkk_compliance import KVKKDataSubjectRequest

        required_columns = [
            "id",
            "request_id",
            "user_id",
            "request_type",
            "status",
            "deadline",
        ]

        for col in required_columns:
            assert hasattr(KVKKDataSubjectRequest, col)
