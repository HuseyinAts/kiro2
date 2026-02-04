"""
AES-256 Data Encryption System
Secure encryption for personal and sensitive data

Features:
- AES-256-GCM encryption
- Key rotation support
- Field-level encryption
- Encrypted database fields
- Secure key management
"""

import base64
import hashlib
import json
import logging
import os
import secrets
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class EncryptionAlgorithm(str, Enum):
    """Encryption algorithms"""

    AES_256_GCM = "aes-256-gcm"
    AES_256_CBC = "aes-256-cbc"
    CHACHA20_POLY1305 = "chacha20-poly1305"


class SensitiveDataField(str, Enum):
    """Sensitive data fields that require encryption"""

    # Identity
    TC_NO = "tc_no"
    PASSPORT_NO = "passport_no"
    DRIVER_LICENSE = "driver_license"

    # Contact
    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "address"

    # Financial
    CREDIT_CARD = "credit_card"
    IBAN = "iban"
    BANK_ACCOUNT = "bank_account"

    # Health
    HEALTH_RECORD = "health_record"
    MEDICAL_CONDITION = "medical_condition"

    # Education
    STUDENT_NUMBER = "student_number"
    EXAM_RESULTS = "exam_results"

    # Authentication
    PASSWORD = "password"
    API_KEY = "api_key"
    SECRET_TOKEN = "secret_token"


class EncryptionKey(BaseModel):
    """Encryption key model"""

    key_id: str
    algorithm: EncryptionAlgorithm
    key_material: bytes
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True
    version: int = 1


class EncryptedData(BaseModel):
    """Encrypted data container"""

    ciphertext: str  # Base64 encoded
    algorithm: EncryptionAlgorithm
    key_id: str
    nonce: str  # Base64 encoded (for GCM)
    tag: Optional[str] = None  # Base64 encoded (for GCM)
    version: int = 1


class AES256Encryptor:
    """AES-256-GCM Encryption"""

    def __init__(self, key: bytes):
        """
        Initialize AES-256 encryptor

        Args:
            key: 32-byte encryption key for AES-256
        """
        if len(key) != 32:
            raise ValueError("AES-256 requires a 32-byte key")

        self.key = key
        self.algorithm = EncryptionAlgorithm.AES_256_GCM

    def encrypt(self, plaintext: Union[str, bytes]) -> EncryptedData:
        """
        Encrypt data using AES-256-GCM

        Args:
            plaintext: Data to encrypt

        Returns:
            EncryptedData object
        """
        # Convert to bytes if string
        if isinstance(plaintext, str):
            plaintext = plaintext.encode("utf-8")

        # Generate random nonce (12 bytes for GCM)
        nonce = os.urandom(12)

        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.key), modes.GCM(nonce), backend=default_backend()
        )

        # Encrypt
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()

        # Get authentication tag
        tag = encryptor.tag

        return EncryptedData(
            ciphertext=base64.b64encode(ciphertext).decode("utf-8"),
            algorithm=self.algorithm,
            key_id="default",  # Will be set by EncryptionManager
            nonce=base64.b64encode(nonce).decode("utf-8"),
            tag=base64.b64encode(tag).decode("utf-8"),
        )

    def decrypt(self, encrypted_data: EncryptedData) -> bytes:
        """
        Decrypt data using AES-256-GCM

        Args:
            encrypted_data: EncryptedData object

        Returns:
            Decrypted plaintext as bytes
        """
        # Decode base64
        ciphertext = base64.b64decode(encrypted_data.ciphertext)
        nonce = base64.b64decode(encrypted_data.nonce)
        tag = base64.b64decode(encrypted_data.tag) if encrypted_data.tag else None

        if not tag:
            raise ValueError("Authentication tag is required for GCM mode")

        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.key), modes.GCM(nonce, tag), backend=default_backend()
        )

        # Decrypt
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()

        return plaintext


class EncryptionKeyManager:
    """Encryption key management with rotation support"""

    def __init__(self, master_key: Optional[bytes] = None):
        """
        Initialize key manager

        Args:
            master_key: Master key for key derivation (32 bytes)
        """
        if master_key is None:
            # Generate from environment or create new
            master_key_hex = os.getenv("ENCRYPTION_MASTER_KEY")
            if master_key_hex:
                master_key = bytes.fromhex(master_key_hex)
            else:
                master_key = secrets.token_bytes(32)
                logger.warning(
                    "No ENCRYPTION_MASTER_KEY found in environment. "
                    "Generated temporary key. Set ENCRYPTION_MASTER_KEY for production!"
                )

        if len(master_key) != 32:
            raise ValueError("Master key must be 32 bytes")

        self.master_key = master_key
        self.keys: Dict[str, EncryptionKey] = {}
        self.active_key_id: Optional[str] = None

        # Create initial key
        self._create_initial_key()

    def _create_initial_key(self):
        """Create initial encryption key"""
        key_id = "key_v1"
        key_material = self._derive_key(key_id)

        key = EncryptionKey(
            key_id=key_id,
            algorithm=EncryptionAlgorithm.AES_256_GCM,
            key_material=key_material,
            created_at=datetime.utcnow(),
            is_active=True,
            version=1,
        )

        self.keys[key_id] = key
        self.active_key_id = key_id

        logger.info(f"Created initial encryption key: {key_id}")

    def _derive_key(self, key_id: str, salt: Optional[bytes] = None) -> bytes:
        """
        Derive encryption key from master key using PBKDF2

        Args:
            key_id: Key identifier
            salt: Optional salt (generated if not provided)

        Returns:
            Derived 32-byte key
        """
        if salt is None:
            # Use key_id as salt component
            salt = hashlib.sha256(key_id.encode()).digest()

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend(),
        )

        return kdf.derive(self.master_key)

    def get_active_key(self) -> EncryptionKey:
        """Get active encryption key"""
        if not self.active_key_id:
            raise ValueError("No active encryption key")

        return self.keys[self.active_key_id]

    def get_key(self, key_id: str) -> Optional[EncryptionKey]:
        """Get encryption key by ID"""
        return self.keys.get(key_id)

    def rotate_key(self) -> str:
        """
        Rotate encryption key

        Returns:
            New key ID
        """
        # Deactivate current key
        if self.active_key_id:
            self.keys[self.active_key_id].is_active = False

        # Create new key
        version = len(self.keys) + 1
        key_id = f"key_v{version}"
        key_material = self._derive_key(key_id)

        key = EncryptionKey(
            key_id=key_id,
            algorithm=EncryptionAlgorithm.AES_256_GCM,
            key_material=key_material,
            created_at=datetime.utcnow(),
            is_active=True,
            version=version,
        )

        self.keys[key_id] = key
        self.active_key_id = key_id

        logger.info(f"Rotated encryption key: {key_id}")

        return key_id

    def list_keys(self) -> List[Dict[str, Any]]:
        """List all encryption keys"""
        return [
            {
                "key_id": key.key_id,
                "algorithm": key.algorithm.value,
                "created_at": key.created_at.isoformat(),
                "is_active": key.is_active,
                "version": key.version,
            }
            for key in self.keys.values()
        ]


class DataEncryptionManager:
    """Main data encryption manager"""

    def __init__(self, key_manager: Optional[EncryptionKeyManager] = None):
        """
        Initialize encryption manager

        Args:
            key_manager: Optional key manager (created if not provided)
        """
        self.key_manager = key_manager or EncryptionKeyManager()
        self.encryptors: Dict[str, AES256Encryptor] = {}

        # Create encryptor for active key
        self._initialize_encryptors()

    def _initialize_encryptors(self):
        """Initialize encryptors for all keys"""
        for key_id, key in self.key_manager.keys.items():
            if key.algorithm == EncryptionAlgorithm.AES_256_GCM:
                self.encryptors[key_id] = AES256Encryptor(key.key_material)

    def encrypt(
        self,
        plaintext: Union[str, bytes],
        field_name: Optional[SensitiveDataField] = None,
    ) -> EncryptedData:
        """
        Encrypt data

        Args:
            plaintext: Data to encrypt
            field_name: Optional field name for logging

        Returns:
            EncryptedData object
        """
        # Get active key
        active_key = self.key_manager.get_active_key()

        # Get encryptor
        encryptor = self.encryptors.get(active_key.key_id)
        if not encryptor:
            raise ValueError(f"No encryptor for key: {active_key.key_id}")

        # Encrypt
        encrypted_data = encryptor.encrypt(plaintext)
        encrypted_data.key_id = active_key.key_id

        if field_name:
            logger.debug(f"Encrypted field: {field_name.value}")

        return encrypted_data

    def decrypt(self, encrypted_data: EncryptedData) -> str:
        """
        Decrypt data

        Args:
            encrypted_data: EncryptedData object

        Returns:
            Decrypted plaintext as string
        """
        # Get key
        key = self.key_manager.get_key(encrypted_data.key_id)
        if not key:
            raise ValueError(f"Key not found: {encrypted_data.key_id}")

        # Get encryptor
        encryptor = self.encryptors.get(encrypted_data.key_id)
        if not encryptor:
            raise ValueError(f"No encryptor for key: {encrypted_data.key_id}")

        # Decrypt
        plaintext_bytes = encryptor.decrypt(encrypted_data)

        return plaintext_bytes.decode("utf-8")

    def encrypt_dict(
        self, data: Dict[str, Any], fields_to_encrypt: List[str]
    ) -> Dict[str, Any]:
        """
        Encrypt specific fields in a dictionary

        Args:
            data: Dictionary with data
            fields_to_encrypt: List of field names to encrypt

        Returns:
            Dictionary with encrypted fields
        """
        encrypted_data = data.copy()

        for field in fields_to_encrypt:
            if field in encrypted_data and encrypted_data[field]:
                # Convert to string if not already
                value = str(encrypted_data[field])

                # Encrypt
                encrypted = self.encrypt(value)

                # Store as JSON string
                encrypted_data[field] = json.dumps(
                    {
                        "encrypted": True,
                        "ciphertext": encrypted.ciphertext,
                        "algorithm": encrypted.algorithm.value,
                        "key_id": encrypted.key_id,
                        "nonce": encrypted.nonce,
                        "tag": encrypted.tag,
                        "version": encrypted.version,
                    }
                )

        return encrypted_data

    def decrypt_dict(
        self, data: Dict[str, Any], fields_to_decrypt: List[str]
    ) -> Dict[str, Any]:
        """
        Decrypt specific fields in a dictionary

        Args:
            data: Dictionary with encrypted data
            fields_to_decrypt: List of field names to decrypt

        Returns:
            Dictionary with decrypted fields
        """
        decrypted_data = data.copy()

        for field in fields_to_decrypt:
            if field in decrypted_data and decrypted_data[field]:
                try:
                    # Parse JSON
                    encrypted_json = json.loads(decrypted_data[field])

                    if not encrypted_json.get("encrypted"):
                        continue

                    # Create EncryptedData object
                    encrypted = EncryptedData(
                        ciphertext=encrypted_json["ciphertext"],
                        algorithm=EncryptionAlgorithm(encrypted_json["algorithm"]),
                        key_id=encrypted_json["key_id"],
                        nonce=encrypted_json["nonce"],
                        tag=encrypted_json.get("tag"),
                        version=encrypted_json.get("version", 1),
                    )

                    # Decrypt
                    decrypted_data[field] = self.decrypt(encrypted)

                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    logger.error(f"Failed to decrypt field {field}: {e}")
                    # Keep original value on error

        return decrypted_data

    def encrypt_sensitive_fields(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt all sensitive fields in user data

        Args:
            user_data: User data dictionary

        Returns:
            Dictionary with encrypted sensitive fields
        """
        sensitive_fields = [
            "tc_no",
            "passport_no",
            "phone",
            "address",
            "email",  # Optional: email might need to be searchable
            "credit_card",
            "iban",
            "health_record",
        ]

        return self.encrypt_dict(user_data, sensitive_fields)

    def decrypt_sensitive_fields(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt all sensitive fields in user data

        Args:
            user_data: User data dictionary with encrypted fields

        Returns:
            Dictionary with decrypted sensitive fields
        """
        sensitive_fields = [
            "tc_no",
            "passport_no",
            "phone",
            "address",
            "email",
            "credit_card",
            "iban",
            "health_record",
        ]

        return self.decrypt_dict(user_data, sensitive_fields)

    def rotate_encryption_key(self) -> str:
        """
        Rotate encryption key

        Returns:
            New key ID
        """
        new_key_id = self.key_manager.rotate_key()

        # Create encryptor for new key
        new_key = self.key_manager.get_key(new_key_id)
        if new_key.algorithm == EncryptionAlgorithm.AES_256_GCM:
            self.encryptors[new_key_id] = AES256Encryptor(new_key.key_material)

        logger.info(f"Encryption key rotated: {new_key_id}")

        return new_key_id

    def re_encrypt_data(self, encrypted_data: EncryptedData) -> EncryptedData:
        """
        Re-encrypt data with active key (for key rotation)

        Args:
            encrypted_data: Data encrypted with old key

        Returns:
            Data encrypted with active key
        """
        # Decrypt with old key
        plaintext = self.decrypt(encrypted_data)

        # Encrypt with active key
        return self.encrypt(plaintext)

    def hash_for_search(self, value: str) -> str:
        """
        Create searchable hash of encrypted value

        Args:
            value: Value to hash

        Returns:
            SHA-256 hash (hex)
        """
        return hashlib.sha256(value.encode("utf-8")).hexdigest()


# Global instance
encryption_manager: Optional[DataEncryptionManager] = None


def get_encryption_manager() -> DataEncryptionManager:
    """Get global encryption manager instance"""
    global encryption_manager

    if encryption_manager is None:
        encryption_manager = DataEncryptionManager()

    return encryption_manager


# Utility functions


def encrypt_personal_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Encrypt personal data fields"""
    manager = get_encryption_manager()
    return manager.encrypt_sensitive_fields(data)


def decrypt_personal_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Decrypt personal data fields"""
    manager = get_encryption_manager()
    return manager.decrypt_sensitive_fields(data)


def mask_sensitive_data(value: str, visible_chars: int = 4) -> str:
    """
    Mask sensitive data for display

    Args:
        value: Value to mask
        visible_chars: Number of characters to show at end

    Returns:
        Masked value
    """
    if not value or len(value) <= visible_chars:
        return "*" * len(value) if value else ""

    return "*" * (len(value) - visible_chars) + value[-visible_chars:]


# Example usage
if __name__ == "__main__":
    # Initialize manager
    manager = get_encryption_manager()

    # Example: Encrypt user data
    user_data = {
        "name": "Ahmet Yılmaz",
        "tc_no": "12345678901",
        "email": "ahmet@example.com",
        "phone": "+905551234567",
        "address": "İstanbul, Türkiye",
    }

    print("Original data:")
    print(json.dumps(user_data, indent=2, ensure_ascii=False))

    # Encrypt
    encrypted = manager.encrypt_sensitive_fields(user_data)
    print("\nEncrypted data:")
    print(json.dumps(encrypted, indent=2, ensure_ascii=False))

    # Decrypt
    decrypted = manager.decrypt_sensitive_fields(encrypted)
    print("\nDecrypted data:")
    print(json.dumps(decrypted, indent=2, ensure_ascii=False))

    # Mask for display
    print("\nMasked data:")
    print(f"TC No: {mask_sensitive_data(user_data['tc_no'])}")
    print(f"Phone: {mask_sensitive_data(user_data['phone'])}")
