"""
Data Encryption Service
TASK 48.3: Data encryption at rest

Fernet (symmetric encryption) kullanarak PII field encryption.
REQ-7.3: Security and Privacy
"""
import logging
import os
from functools import lru_cache
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import String, Text, TypeDecorator

logger = logging.getLogger(__name__)


class EncryptionService:
    """
    Veri şifreleme servisi

    Fernet (symmetric encryption) kullanarak hassas verileri şifreler.
    Key rotation ve multiple key desteği sağlar.
    """

    def __init__(self, primary_key: bytes | None = None):
        """
        Initialize encryption service

        Args:
            primary_key: Ana şifreleme anahtarı (bytes). None ise environment'tan alınır.
        """
        if primary_key is None:
            key_str = os.getenv("ENCRYPTION_KEY")
            if not key_str:
                logger.warning(
                    "ENCRYPTION_KEY environment variable not set. "
                    "Generating temporary key (NOT FOR PRODUCTION!)"
                )
                primary_key = Fernet.generate_key()
            else:
                primary_key = key_str.encode()

        self.primary_key = primary_key
        self.primary_fernet = Fernet(primary_key)

        # Key rotation için eski anahtarlar
        self.old_keys = self._load_old_keys()

        logger.info("Encryption service initialized")

    def _load_old_keys(self) -> list[Fernet]:
        """Eski şifreleme anahtarlarını yükle (key rotation için)"""
        old_keys = []

        # Environment'tan eski anahtarları yükle
        for i in range(1, 6):  # Son 5 eski anahtar
            old_key_str = os.getenv(f"ENCRYPTION_KEY_OLD_{i}")
            if old_key_str:
                try:
                    old_keys.append(Fernet(old_key_str.encode()))
                except Exception as e:
                    logger.error(f"Failed to load old encryption key {i}: {e}")

        return old_keys

    def encrypt(self, plaintext: str) -> str:
        """
        Metni şifrele

        Args:
            plaintext: Şifrelenecek metin

        Returns:
            Şifrelenmiş metin (base64 encoded)
        """
        if not plaintext:
            return plaintext

        try:
            encrypted_bytes = self.primary_fernet.encrypt(plaintext.encode("utf-8"))
            return encrypted_bytes.decode("utf-8")
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(self, ciphertext: str) -> str:
        """
        Şifreli metni çöz

        Args:
            ciphertext: Şifreli metin (base64 encoded)

        Returns:
            Çözülmüş metin
        """
        if not ciphertext:
            return ciphertext

        # Önce primary key ile dene
        try:
            decrypted_bytes = self.primary_fernet.decrypt(ciphertext.encode("utf-8"))
            return decrypted_bytes.decode("utf-8")
        except InvalidToken:
            # Primary key başarısız, eski anahtarları dene (key rotation)
            for old_fernet in self.old_keys:
                try:
                    decrypted_bytes = old_fernet.decrypt(ciphertext.encode("utf-8"))
                    logger.info("Decrypted with old key, consider re-encrypting")
                    return decrypted_bytes.decode("utf-8")
                except InvalidToken:
                    continue

            # Hiçbir anahtar çalışmadı
            logger.error("Decryption failed with all available keys")
            raise ValueError("Unable to decrypt data")
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    def rotate_key(self, new_key: bytes) -> None:
        """
        Şifreleme anahtarını değiştir (key rotation)

        Args:
            new_key: Yeni şifreleme anahtarı
        """
        # Eski primary key'i old_keys listesine ekle
        self.old_keys.insert(0, self.primary_fernet)

        # Yeni primary key'i ayarla
        self.primary_key = new_key
        self.primary_fernet = Fernet(new_key)

        # En fazla 5 eski anahtar tut
        if len(self.old_keys) > 5:
            self.old_keys = self.old_keys[:5]

        logger.info("Encryption key rotated successfully")

    @staticmethod
    def generate_key() -> bytes:
        """Yeni bir şifreleme anahtarı oluştur"""
        return Fernet.generate_key()


# Global encryption service instance
@lru_cache(maxsize=1)
def get_encryption_service() -> EncryptionService:
    """Global encryption service instance'ını al"""
    return EncryptionService()


class EncryptedString(TypeDecorator):
    """
    SQLAlchemy TypeDecorator for encrypted string fields

    Kullanım:
        class User(Base):
            email = Column(EncryptedString(255))
    """

    impl = String
    cache_ok = True

    def __init__(self, length: int = 255, *args, **kwargs):
        """
        Initialize encrypted string column

        Args:
            length: Maksimum string uzunluğu (şifrelenmiş veri için yeterli olmalı)
        """
        super().__init__(length, *args, **kwargs)
        self.encryption_service = get_encryption_service()

    def process_bind_param(self, value: str | None, dialect) -> str | None:
        """Veritabanına yazarken şifrele"""
        if value is not None:
            return self.encryption_service.encrypt(value)
        return value

    def process_result_value(self, value: str | None, dialect) -> str | None:
        """Veritabanından okurken şifreyi çöz"""
        if value is not None:
            try:
                return self.encryption_service.decrypt(value)
            except Exception as e:
                logger.error(f"Failed to decrypt value: {e}")
                return None
        return value


class EncryptedText(TypeDecorator):
    """
    SQLAlchemy TypeDecorator for encrypted text fields (longer content)

    Kullanım:
        class User(Base):
            address = Column(EncryptedText)
    """

    impl = Text
    cache_ok = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.encryption_service = get_encryption_service()

    def process_bind_param(self, value: str | None, dialect) -> str | None:
        """Veritabanına yazarken şifrele"""
        if value is not None:
            return self.encryption_service.encrypt(value)
        return value

    def process_result_value(self, value: str | None, dialect) -> str | None:
        """Veritabanından okurken şifreyi çöz"""
        if value is not None:
            try:
                return self.encryption_service.decrypt(value)
            except Exception as e:
                logger.error(f"Failed to decrypt value: {e}")
                return None
        return value


# Utility functions
def encrypt_dict(data: dict[str, Any], fields_to_encrypt: list[str]) -> dict[str, Any]:
    """
    Dictionary içindeki belirli field'ları şifrele

    Args:
        data: Şifrelenecek dictionary
        fields_to_encrypt: Şifrelenecek field isimleri

    Returns:
        Şifrelenmiş field'ları içeren dictionary
    """
    encryption_service = get_encryption_service()
    encrypted_data = data.copy()

    for field in fields_to_encrypt:
        if encrypted_data.get(field):
            encrypted_data[field] = encryption_service.encrypt(
                str(encrypted_data[field])
            )

    return encrypted_data


def decrypt_dict(data: dict[str, Any], fields_to_decrypt: list[str]) -> dict[str, Any]:
    """
    Dictionary içindeki belirli field'ların şifresini çöz

    Args:
        data: Şifresi çözülecek dictionary
        fields_to_decrypt: Şifresi çözülecek field isimleri

    Returns:
        Şifresi çözülmüş field'ları içeren dictionary
    """
    encryption_service = get_encryption_service()
    decrypted_data = data.copy()

    for field in fields_to_decrypt:
        if decrypted_data.get(field):
            try:
                decrypted_data[field] = encryption_service.decrypt(
                    decrypted_data[field]
                )
            except Exception as e:
                logger.error(f"Failed to decrypt field {field}: {e}")
                decrypted_data[field] = None

    return decrypted_data


if __name__ == "__main__":
    # Test encryption service
    print("Testing Encryption Service...")

    # Generate a test key
    test_key = Fernet.generate_key()
    print(f"Generated test key: {test_key.decode()}")

    # Create encryption service
    service = EncryptionService(test_key)

    # Test encryption/decryption
    plaintext = "test@example.com"
    encrypted = service.encrypt(plaintext)
    decrypted = service.decrypt(encrypted)

    print(f"Plaintext: {plaintext}")
    print(f"Encrypted: {encrypted}")
    print(f"Decrypted: {decrypted}")
    print(f"Match: {plaintext == decrypted}")

    # Test key rotation
    new_key = Fernet.generate_key()
    service.rotate_key(new_key)

    # Old encrypted data should still be decryptable
    decrypted_after_rotation = service.decrypt(encrypted)
    print(f"Decrypted after rotation: {decrypted_after_rotation}")
    print(f"Match after rotation: {plaintext == decrypted_after_rotation}")

    print("\n✅ Encryption service test completed!")
