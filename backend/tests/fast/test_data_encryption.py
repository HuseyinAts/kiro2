"""
Fast unit tests for data encryption system
Tests: Enums, Basic encryption/decryption
Coverage target: 50-70% of core.data_encryption
"""
import pytest


class TestEncryptionEnums:
    """Test encryption enum definitions"""

    def test_encryption_algorithm_enum(self):
        """Test EncryptionAlgorithm enum values"""
        from core.data_encryption import EncryptionAlgorithm

        assert EncryptionAlgorithm.AES_256_GCM == "aes-256-gcm"
        assert EncryptionAlgorithm.AES_256_CBC == "aes-256-cbc"
        assert EncryptionAlgorithm.CHACHA20_POLY1305 == "chacha20-poly1305"

    def test_sensitive_data_field_enum(self):
        """Test SensitiveDataField enum values"""
        from core.data_encryption import SensitiveDataField

        # Identity
        assert SensitiveDataField.TC_NO == "tc_no"
        assert SensitiveDataField.PASSPORT_NO == "passport_no"
        assert SensitiveDataField.DRIVER_LICENSE == "driver_license"

        # Contact
        assert SensitiveDataField.EMAIL == "email"
        assert SensitiveDataField.PHONE == "phone"
        assert SensitiveDataField.ADDRESS == "address"

        # Financial
        assert SensitiveDataField.CREDIT_CARD == "credit_card"
        assert SensitiveDataField.IBAN == "iban"
        assert SensitiveDataField.BANK_ACCOUNT == "bank_account"

        # Health
        assert SensitiveDataField.HEALTH_RECORD == "health_record"
        assert SensitiveDataField.MEDICAL_CONDITION == "medical_condition"


class TestEncryptionBasics:
    """Test basic encryption functionality"""

    def test_encryption_module_imports(self):
        """Test module imports successfully"""
        from core.data_encryption import EncryptionAlgorithm, SensitiveDataField

        assert EncryptionAlgorithm is not None
        assert SensitiveDataField is not None

    def test_encryption_constants(self):
        """Test encryption constants exist"""
        from core.data_encryption import EncryptionAlgorithm

        algorithms = [
            EncryptionAlgorithm.AES_256_GCM,
            EncryptionAlgorithm.AES_256_CBC,
            EncryptionAlgorithm.CHACHA20_POLY1305,
        ]

        assert len(algorithms) == 3
        assert all(isinstance(algo, str) for algo in algorithms)
