"""
XSS (Cross-Site Scripting) Prevention Modülü
Task 23: Security Hardening - XSS prevention

Bu modül XSS saldırılarını önlemek için output encoding ve
content sanitization sağlar.
"""
import html
import re
from typing import Any, Dict, List
from fastapi import Response
from fastapi.responses import JSONResponse


class XSSPrevention:
    """XSS prevention utilities"""

    # Tehlikeli HTML tag'leri ve attribute'ları
    DANGEROUS_TAGS = [
        "script",
        "iframe",
        "object",
        "embed",
        "applet",
        "meta",
        "link",
        "style",
        "base",
        "form",
    ]

    DANGEROUS_ATTRIBUTES = [
        "onclick",
        "onload",
        "onerror",
        "onmouseover",
        "onmouseout",
        "onfocus",
        "onblur",
        "onchange",
        "onsubmit",
        "onkeydown",
        "onkeyup",
        "onkeypress",
    ]

    DANGEROUS_PROTOCOLS = ["javascript:", "data:", "vbscript:", "file:", "about:"]

    @staticmethod
    def escape_html(text: str) -> str:
        """
        HTML karakterlerini escape et

        Args:
            text: Escape edilecek text

        Returns:
            Escape edilmiş text
        """
        if not text:
            return ""

        return html.escape(str(text), quote=True)

    @staticmethod
    def remove_dangerous_tags(html_content: str) -> str:
        """
        Tehlikeli HTML tag'lerini kaldır

        Args:
            html_content: HTML içerik

        Returns:
            Temizlenmiş içerik
        """
        if not html_content:
            return ""

        # Tehlikeli tag'leri kaldır
        for tag in XSSPrevention.DANGEROUS_TAGS:
            # Opening tag
            html_content = re.sub(
                f"<{tag}[^>]*>.*?</{tag}>",
                "",
                html_content,
                flags=re.IGNORECASE | re.DOTALL,
            )

            # Self-closing tag
            html_content = re.sub(
                f"<{tag}[^>]*/>", "", html_content, flags=re.IGNORECASE
            )

        return html_content

    @staticmethod
    def remove_dangerous_attributes(html_content: str) -> str:
        """
        Tehlikeli HTML attribute'larını kaldır

        Args:
            html_content: HTML içerik

        Returns:
            Temizlenmiş içerik
        """
        if not html_content:
            return ""

        # Event handler attribute'larını kaldır
        for attr in XSSPrevention.DANGEROUS_ATTRIBUTES:
            html_content = re.sub(
                f"{attr}\\s*=\\s*[\"'][^\"']*[\"']",
                "",
                html_content,
                flags=re.IGNORECASE,
            )

        return html_content

    @staticmethod
    def remove_dangerous_protocols(url: str) -> str:
        """
        Tehlikeli protocol'leri kaldır

        Args:
            url: URL string

        Returns:
            Temizlenmiş URL veya boş string
        """
        if not url:
            return ""

        url_lower = url.lower().strip()

        # Tehlikeli protocol kontrolü
        for protocol in XSSPrevention.DANGEROUS_PROTOCOLS:
            if url_lower.startswith(protocol):
                return ""  # Tehlikeli URL'i kaldır

        return url

    @staticmethod
    def sanitize_text(text: str, allow_html: bool = False) -> str:
        """
        Text içeriği temizle

        Args:
            text: Temizlenecek text
            allow_html: HTML'e izin ver mi?

        Returns:
            Temizlenmiş text
        """
        if not text:
            return ""

        if allow_html:
            # HTML'e izin veriliyorsa sadece tehlikeli kısımları kaldır
            text = XSSPrevention.remove_dangerous_tags(text)
            text = XSSPrevention.remove_dangerous_attributes(text)
        else:
            # HTML'e izin verilmiyorsa tüm HTML'i escape et
            text = XSSPrevention.escape_html(text)

        return text

    @staticmethod
    def sanitize_dict(data: Dict[str, Any], allow_html: bool = False) -> Dict[str, Any]:
        """
        Dictionary içindeki tüm string değerleri temizle

        Args:
            data: Temizlenecek dictionary
            allow_html: HTML'e izin ver mi?

        Returns:
            Temizlenmiş dictionary
        """
        if not data:
            return {}

        sanitized = {}

        for key, value in data.items():
            # Key'i temizle
            clean_key = XSSPrevention.sanitize_text(str(key), allow_html=False)

            # Value'yu temizle
            if isinstance(value, str):
                clean_value = XSSPrevention.sanitize_text(value, allow_html=allow_html)
            elif isinstance(value, dict):
                clean_value = XSSPrevention.sanitize_dict(value, allow_html=allow_html)
            elif isinstance(value, list):
                clean_value = XSSPrevention.sanitize_list(value, allow_html=allow_html)
            else:
                clean_value = value

            sanitized[clean_key] = clean_value

        return sanitized

    @staticmethod
    def sanitize_list(data: List[Any], allow_html: bool = False) -> List[Any]:
        """
        List içindeki tüm string değerleri temizle

        Args:
            data: Temizlenecek list
            allow_html: HTML'e izin ver mi?

        Returns:
            Temizlenmiş list
        """
        if not data:
            return []

        sanitized = []

        for item in data:
            if isinstance(item, str):
                clean_item = XSSPrevention.sanitize_text(item, allow_html=allow_html)
            elif isinstance(item, dict):
                clean_item = XSSPrevention.sanitize_dict(item, allow_html=allow_html)
            elif isinstance(item, list):
                clean_item = XSSPrevention.sanitize_list(item, allow_html=allow_html)
            else:
                clean_item = item

            sanitized.append(clean_item)

        return sanitized


class SecureJSONResponse(JSONResponse):
    """
    XSS-safe JSON response

    Tüm string değerleri otomatik olarak escape eder.
    """

    def render(self, content: Any) -> bytes:
        """
        Content'i XSS-safe şekilde render et

        Args:
            content: Response content

        Returns:
            Rendered bytes
        """
        # Content'i sanitize et
        if isinstance(content, dict):
            content = XSSPrevention.sanitize_dict(content, allow_html=False)
        elif isinstance(content, list):
            content = XSSPrevention.sanitize_list(content, allow_html=False)

        # Security headers ekle
        self.headers["X-Content-Type-Options"] = "nosniff"
        self.headers["X-Frame-Options"] = "DENY"
        self.headers["X-XSS-Protection"] = "1; mode=block"
        self.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )

        return super().render(content)


def add_security_headers(response: Response) -> Response:
    """
    Response'a güvenlik header'ları ekle

    Args:
        response: FastAPI Response

    Returns:
        Header'ları eklenmiş response
    """
    # XSS Protection
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Content Security Policy
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none';"
    )

    # Referrer Policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Permissions Policy
    response.headers["Permissions-Policy"] = (
        "geolocation=(), "
        "microphone=(), "
        "camera=(), "
        "payment=(), "
        "usb=(), "
        "magnetometer=(), "
        "gyroscope=(), "
        "accelerometer=()"
    )

    return response


# Example usage:
"""
from fastapi import APIRouter
from core.xss_prevention import SecureJSONResponse, add_security_headers

router = APIRouter()

@router.get("/api/data")
async def get_data():
    data = {
        "title": "<script>alert('XSS')</script>",
        "description": "Normal text"
    }
    
    # Otomatik XSS prevention
    return SecureJSONResponse(content=data)

# Veya manuel header ekleme
@router.get("/api/other")
async def get_other_data():
    response = JSONResponse(content={"data": "value"})
    return add_security_headers(response)
"""
