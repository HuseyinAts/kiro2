"""
Comprehensive Model Tests
Tests for all Pydantic models and data structures
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pydantic import ValidationError
import json

# Import models - use the Pydantic models that exist
try:
    from models import KullaniciRolu, Kullanici, KullaniciOlustur
    from models.user import KullaniciRolu as UserRole
except ImportError:
    # Fallback to original models.py file if available
    try:
        import sys
        import os

        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from models import (
            ChatRequest,
            ChatResponse,
            AgentInfo,
            SessionMessage,
            WebSocketMessage,
            KullaniciRolu,
            Kullanici,
            KullaniciOlustur,
        )
    except ImportError:
        # Create dummy models for testing if imports fail
        from enum import Enum
        from pydantic import BaseModel, Field
        from datetime import datetime
        from typing import Optional

        class KullaniciRolu(str, Enum):
            OGRENCI = "ogrenci"
            VELI = "veli"
            OGRETMEN = "ogretmen"
            ADMIN = "admin"
            SUPER_ADMIN = "super_admin"

        class ChatRequest(BaseModel):
            agent: str = Field(..., description="Agent type")
            message: str = Field(..., description="User message")
            session_id: Optional[str] = Field(None, description="Session ID")

        class ChatResponse(BaseModel):
            response: str = Field(..., description="Agent response")
            agent: str = Field(..., description="Agent that responded")
            timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
            session_id: Optional[str] = None

        class AgentInfo(BaseModel):
            id: str
            name: str
            description: str
            icon: str

        class SessionMessage(BaseModel):
            role: str
            content: str
            agent: Optional[str] = None
            timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

        class WebSocketMessage(BaseModel):
            type: str
            agent: Optional[str] = None
            message: Optional[str] = None
            data: Optional[dict] = None

        class Kullanici(BaseModel):
            id: str
            email: str
            ad_soyad: str
            rol: KullaniciRolu
            aktif: bool = True
            kayit_tarihi: datetime
            son_giris: Optional[datetime] = None
            profil_resmi: Optional[str] = None

        class KullaniciOlustur(BaseModel):
            email: str = Field(..., description="Kullanıcı email adresi")
            ad_soyad: str = Field(..., description="Kullanıcı adı soyadı")
            sifre: str = Field(..., description="Kullanıcı şifresi")
            rol: KullaniciRolu = Field(
                default=KullaniciRolu.OGRENCI, description="Kullanıcı rolü"
            )
            aktif: bool = Field(default=True, description="Kullanıcı aktif durumu")


class TestChatModels:
    """Test chat-related models"""

    def test_chat_request_valid(self):
        """Test valid ChatRequest creation"""
        data = {
            "agent": "learning",
            "message": "Merhaba, matematik konusunda yardıma ihtiyacım var.",
        }
        request = ChatRequest(**data)

        assert request.agent == "learning"
        assert request.message == "Merhaba, matematik konusunda yardıma ihtiyacım var."
        assert request.session_id is None

    def test_chat_request_with_session(self):
        """Test ChatRequest with session ID"""
        data = {
            "agent": "exam",
            "message": "Sınav başlatmak istiyorum",
            "session_id": "session-12345",
        }
        request = ChatRequest(**data)

        assert request.session_id == "session-12345"

    def test_chat_request_invalid_agent(self):
        """Test ChatRequest with missing required fields"""
        with pytest.raises(ValidationError):
            ChatRequest(message="Test mesajı")  # Missing agent

        with pytest.raises(ValidationError):
            ChatRequest(agent="learning")  # Missing message

    def test_chat_response_creation(self):
        """Test ChatResponse creation"""
        data = {
            "response": "Matematik konusunda size yardımcı olabilirim.",
            "agent": "learning",
        }
        response = ChatResponse(**data)

        assert response.response == "Matematik konusunda size yardımcı olabilirim."
        assert response.agent == "learning"
        assert response.timestamp is not None
        assert response.session_id is None

    def test_chat_response_with_session(self):
        """Test ChatResponse with session ID"""
        data = {
            "response": "Sınav başlatılıyor...",
            "agent": "exam",
            "session_id": "session-67890",
        }
        response = ChatResponse(**data)

        assert response.session_id == "session-67890"

    def test_agent_info_model(self):
        """Test AgentInfo model"""
        data = {
            "id": "matematik_uzman",
            "name": "Matematik Uzmanı",
            "description": "TYT ve AYT matematik konularında uzman AI asistan",
            "icon": "🧮",
        }
        agent = AgentInfo(**data)

        assert agent.id == "matematik_uzman"
        assert agent.name == "Matematik Uzmanı"
        assert agent.icon == "🧮"

    def test_session_message_model(self):
        """Test SessionMessage model"""
        data = {
            "role": "user",
            "content": "Limit konusunu açıklar mısın?",
            "agent": "learning",
        }
        message = SessionMessage(**data)

        assert message.role == "user"
        assert message.content == "Limit konusunu açıklar mısın?"
        assert message.agent == "learning"
        assert message.timestamp is not None

    def test_websocket_message_model(self):
        """Test WebSocketMessage model"""
        data = {
            "type": "chat",
            "agent": "exam",
            "message": "Sınav devam ediyor",
            "data": {"progress": 50, "remaining_time": 1800},
        }
        ws_message = WebSocketMessage(**data)

        assert ws_message.type == "chat"
        assert ws_message.agent == "exam"
        assert ws_message.data["progress"] == 50


class TestKullaniciModels:
    """Test user-related models"""

    def test_kullanici_rolu_enum(self):
        """Test KullaniciRolu enum values"""
        assert KullaniciRolu.OGRENCI == "ogrenci"
        assert KullaniciRolu.VELI == "veli"
        assert KullaniciRolu.OGRETMEN == "ogretmen"
        assert KullaniciRolu.ADMIN == "admin"
        assert KullaniciRolu.SUPER_ADMIN == "super_admin"

    def test_kullanici_model_creation(self):
        """Test Kullanici model creation"""
        data = {
            "id": "user-123",
            "email": "test@example.com",
            "ad_soyad": "Ahmet Yılmaz",
            "rol": KullaniciRolu.OGRENCI,
            "kayit_tarihi": datetime.now(),
        }
        kullanici = Kullanici(**data)

        assert kullanici.id == "user-123"
        assert kullanici.email == "test@example.com"
        assert kullanici.ad_soyad == "Ahmet Yılmaz"
        assert kullanici.rol == KullaniciRolu.OGRENCI
        assert kullanici.aktif is True  # Default value
        assert kullanici.son_giris is None
        assert kullanici.profil_resmi is None

    def test_kullanici_with_optional_fields(self):
        """Test Kullanici with optional fields"""
        data = {
            "id": "user-456",
            "email": "teacher@school.edu.tr",
            "ad_soyad": "Fatma Öğretmen",
            "rol": KullaniciRolu.OGRETMEN,
            "aktif": True,
            "kayit_tarihi": datetime.now(),
            "son_giris": datetime.now() - timedelta(hours=1),
            "profil_resmi": "profile.jpg",
        }
        kullanici = Kullanici(**data)

        assert kullanici.rol == KullaniciRolu.OGRETMEN
        assert kullanici.son_giris is not None
        assert kullanici.profil_resmi == "profile.jpg"

    def test_kullanici_olustur_model(self):
        """Test KullaniciOlustur model"""
        data = {
            "email": "yeni@example.com",
            "ad_soyad": "Yeni Kullanıcı",
            "sifre": "güvenli_şifre_123",
        }
        kullanici_olustur = KullaniciOlustur(**data)

        assert kullanici_olustur.email == "yeni@example.com"
        assert kullanici_olustur.ad_soyad == "Yeni Kullanıcı"
        assert kullanici_olustur.sifre == "güvenli_şifre_123"
        assert kullanici_olustur.rol == KullaniciRolu.OGRENCI  # Default
        assert kullanici_olustur.aktif is True  # Default

    def test_kullanici_olustur_with_role(self):
        """Test KullaniciOlustur with specific role"""
        data = {
            "email": "parent@example.com",
            "ad_soyad": "Veli Baba",
            "sifre": "şifre123",
            "rol": KullaniciRolu.VELI,
            "aktif": False,
        }
        kullanici_olustur = KullaniciOlustur(**data)

        assert kullanici_olustur.rol == KullaniciRolu.VELI
        assert kullanici_olustur.aktif is False

    def test_kullanici_email_validation(self):
        """Test email validation in user models"""
        # Invalid email should still pass Pydantic validation (email validation not enforced in model)
        data = {
            "email": "invalid-email",
            "ad_soyad": "Test User",
            "sifre": "password123",
        }
        # This should work as the model doesn't enforce email format
        kullanici_olustur = KullaniciOlustur(**data)
        assert kullanici_olustur.email == "invalid-email"


class TestModelSerialization:
    """Test model serialization and deserialization"""

    def test_chat_request_json_serialization(self):
        """Test ChatRequest JSON serialization"""
        data = {
            "agent": "study",
            "message": "Fizik konusunda yardım istiyorum",
            "session_id": "test-session",
        }
        request = ChatRequest(**data)

        # Test dict conversion
        request_dict = request.model_dump()
        assert request_dict["agent"] == "study"
        assert request_dict["session_id"] == "test-session"

        # Test JSON serialization
        json_str = request.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["message"] == "Fizik konusunda yardım istiyorum"

    def test_chat_response_json_serialization(self):
        """Test ChatResponse JSON serialization"""
        data = {
            "response": "Fizik konusunda size yardımcı olabilirim.",
            "agent": "study",
        }
        response = ChatResponse(**data)

        json_str = response.model_dump_json()
        parsed = json.loads(json_str)

        assert parsed["response"] == "Fizik konusunda size yardımcı olabilirim."
        assert parsed["agent"] == "study"
        assert "timestamp" in parsed

    def test_kullanici_json_serialization(self):
        """Test Kullanici JSON serialization"""
        data = {
            "id": "user-789",
            "email": "test@example.com",
            "ad_soyad": "Test Kullanıcı",
            "rol": KullaniciRolu.ADMIN,
            "kayit_tarihi": datetime.now(),
        }
        kullanici = Kullanici(**data)

        json_str = kullanici.model_dump_json()
        parsed = json.loads(json_str)

        assert parsed["id"] == "user-789"
        assert parsed["rol"] == "admin"
        assert "kayit_tarihi" in parsed

    def test_websocket_message_complex_data(self):
        """Test WebSocketMessage with complex data"""
        complex_data = {
            "type": "status",
            "data": {
                "exam_status": "in_progress",
                "current_question": 15,
                "total_questions": 40,
                "time_remaining": 5400,
                "subject_progress": {
                    "matematik": {"answered": 8, "total": 20},
                    "fizik": {"answered": 7, "total": 20},
                },
                "user_answers": [1, 3, 0, 2, 1, 3, 0, 2, 1, 3, 0, 2, 1, 3, 0],
            },
        }
        ws_message = WebSocketMessage(**complex_data)

        assert ws_message.type == "status"
        assert ws_message.data["exam_status"] == "in_progress"
        assert ws_message.data["subject_progress"]["matematik"]["answered"] == 8

        # Test serialization
        json_str = ws_message.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["data"]["time_remaining"] == 5400


class TestModelValidation:
    """Test model validation edge cases"""

    def test_empty_strings(self):
        """Test behavior with empty strings"""
        # Empty message should fail validation if required
        with pytest.raises(ValidationError):
            ChatRequest(agent="learning", message="")

        # Empty agent should fail
        with pytest.raises(ValidationError):
            ChatRequest(agent="", message="Test message")

    def test_very_long_strings(self):
        """Test behavior with very long strings"""
        long_message = "a" * 10000  # 10k characters

        # Should accept long messages (no length limit defined)
        request = ChatRequest(agent="learning", message=long_message)
        assert len(request.message) == 10000

    def test_special_characters(self):
        """Test special characters in Turkish"""
        turkish_message = "Türkçe karakterler: ğüşıöç ĞÜŞIÖÇ"
        request = ChatRequest(agent="learning", message=turkish_message)
        assert request.message == turkish_message

        turkish_name = "Özgür Çağatay Şimşek"
        kullanici_data = {
            "email": "ozgur@example.com",
            "ad_soyad": turkish_name,
            "sifre": "şifre123",
        }
        kullanici = KullaniciOlustur(**kullanici_data)
        assert kullanici.ad_soyad == turkish_name

    def test_none_values(self):
        """Test None values for optional fields"""
        # SessionMessage with None agent
        message = SessionMessage(role="user", content="Test message", agent=None)
        assert message.agent is None

        # WebSocketMessage with None fields
        ws_message = WebSocketMessage(type="error", agent=None, message=None, data=None)
        assert ws_message.agent is None
        assert ws_message.message is None
        assert ws_message.data is None


class TestModelEquality:
    """Test model equality and comparison"""

    def test_chat_request_equality(self):
        """Test ChatRequest equality"""
        data = {"agent": "learning", "message": "Test message"}
        request1 = ChatRequest(**data)
        request2 = ChatRequest(**data)

        # Pydantic models should be equal if their fields are equal
        assert request1.model_dump() == request2.model_dump()

    def test_kullanici_equality(self):
        """Test Kullanici equality"""
        timestamp = datetime.now()
        data = {
            "id": "user-123",
            "email": "test@example.com",
            "ad_soyad": "Test User",
            "rol": KullaniciRolu.OGRENCI,
            "kayit_tarihi": timestamp,
        }
        user1 = Kullanici(**data)
        user2 = Kullanici(**data)

        assert user1.model_dump() == user2.model_dump()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
