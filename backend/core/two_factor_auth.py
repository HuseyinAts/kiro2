"""
Two-Factor Authentication (2FA) Service
PHASE 2 Sprint 4: Security Hardening

Implements TOTP-based 2FA with:
- Secret key generation
- QR code generation for authenticator apps
- TOTP validation
- Backup codes generation and validation
"""
import pyotp
import qrcode
import io
import base64
import secrets
import hashlib
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from core.structured_logger import get_logger

logger = get_logger(__name__)


class TwoFactorAuthService:
    """Two-Factor Authentication service using TOTP"""
    
    def __init__(self, app_name: str = "Kiro2 Egitim"):
        """
        Initialize 2FA service
        
        Args:
            app_name: Application name shown in authenticator app
        """
        self.app_name = app_name
        
    def generate_secret(self) -> str:
        """
        Generate a new TOTP secret key
        
        Returns:
            Base32 encoded secret key
            
        Example:
            "JBSWY3DPEHPK3PXP"
        """
        secret = pyotp.random_base32()
        logger.info("2fa_secret_generated")
        return secret
    
    def get_provisioning_uri(
        self, 
        secret: str, 
        user_email: str,
        issuer: Optional[str] = None
    ) -> str:
        """
        Generate provisioning URI for authenticator apps
        
        Args:
            secret: TOTP secret key
            user_email: User's email address
            issuer: Optional issuer name
            
        Returns:
            otpauth:// URI for QR code
            
        Example:
            "otpauth://totp/Kiro2:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=Kiro2"
        """
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(
            name=user_email,
            issuer_name=issuer or self.app_name
        )
        logger.info("2fa_provisioning_uri_generated", email=user_email)
        return uri
    
    def generate_qr_code(
        self, 
        secret: str, 
        user_email: str,
        issuer: Optional[str] = None
    ) -> str:
        """
        Generate QR code image as base64 string
        
        Args:
            secret: TOTP secret key
            user_email: User's email
            issuer: Optional issuer name
            
        Returns:
            Base64 encoded PNG image
            
        Usage:
            <img src="data:image/png;base64,{qr_code}" />
        """
        # Get provisioning URI
        uri = self.get_provisioning_uri(secret, user_email, issuer)
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        qr_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        
        logger.info("2fa_qr_code_generated", email=user_email)
        return qr_base64
    
    def verify_token(self, secret: str, token: str, window: int = 1) -> bool:
        """
        Verify TOTP token
        
        Args:
            secret: User's TOTP secret key
            token: 6-digit token from authenticator app
            window: Time window (±30 seconds per window)
            
        Returns:
            True if token is valid
            
        Window explanation:
            - window=0: Only current time
            - window=1: ±30 seconds (recommended)
            - window=2: ±60 seconds
        """
        try:
            totp = pyotp.TOTP(secret)
            is_valid = totp.verify(token, valid_window=window)
            
            if is_valid:
                logger.info("2fa_token_verified_success")
            else:
                logger.warning("2fa_token_verification_failed")
                
            return is_valid
            
        except Exception as e:
            logger.error("2fa_token_verification_error", error=str(e))
            return False
    
    def get_current_token(self, secret: str) -> str:
        """
        Get current TOTP token (for testing)
        
        Args:
            secret: TOTP secret key
            
        Returns:
            Current 6-digit token
        """
        totp = pyotp.TOTP(secret)
        return totp.now()
    
    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """
        Generate backup recovery codes
        
        Args:
            count: Number of backup codes to generate
            
        Returns:
            List of 8-character alphanumeric codes
            
        Example:
            ["A1B2C3D4", "E5F6G7H8", ...]
        """
        backup_codes = []
        for _ in range(count):
            # Generate 8-character code
            code = secrets.token_hex(4).upper()
            backup_codes.append(code)
            
        logger.info("2fa_backup_codes_generated", count=count)
        return backup_codes
    
    def hash_backup_code(self, code: str) -> str:
        """
        Hash backup code for secure storage
        
        Args:
            code: Plain backup code
            
        Returns:
            SHA-256 hashed code
        """
        return hashlib.sha256(code.encode()).hexdigest()
    
    def verify_backup_code(
        self, 
        code: str, 
        hashed_codes: List[str]
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify backup code against hashed codes
        
        Args:
            code: Plain backup code entered by user
            hashed_codes: List of hashed backup codes
            
        Returns:
            (is_valid, matched_hash)
            
        Note: Backup codes are single-use. Remove matched hash after use.
        """
        code_hash = self.hash_backup_code(code)
        
        if code_hash in hashed_codes:
            logger.info("2fa_backup_code_verified")
            return True, code_hash
        else:
            logger.warning("2fa_backup_code_invalid")
            return False, None


# Global instance
two_factor_auth = TwoFactorAuthService()

__all__ = ["TwoFactorAuthService", "two_factor_auth"]
