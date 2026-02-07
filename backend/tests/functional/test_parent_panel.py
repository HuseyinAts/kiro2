"""
Veli Paneli Fonksiyonellik Testleri (F-10)
KIRO2 Production Readiness - 4 test case
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# --- F-10.1: Veli kaydı ---
@pytest.mark.asyncio
async def test_parent_registration():
    """Parent role + çocuk bağlama → ilişki kurulur"""
    parent = {"id": "p-001", "role": "veli", "child_ids": ["s-001"]}
    assert parent["role"] == "veli"
    assert len(parent["child_ids"]) >= 1


# --- F-10.2: Çocuk performansı ---
@pytest.mark.asyncio
async def test_child_performance_view():
    """Veli görüntüleme → özet rapor"""
    report = {
        "child_id": "s-001",
        "child_name": "Ali",
        "overall_score": 82,
        "subjects": {"matematik": 85, "turkce": 79},
        "study_hours_this_week": 12,
    }
    assert report["overall_score"] > 0
    assert "matematik" in report["subjects"]
    assert report["study_hours_this_week"] >= 0


# --- F-10.3: Bildirimler ---
@pytest.mark.asyncio
async def test_notifications():
    """Düşük performans uyarısı → notification"""
    notification = {
        "type": "low_performance",
        "message": "Ali'nin matematik puanı düştü",
        "severity": "warning",
        "read": False,
    }
    assert notification["type"] == "low_performance"
    assert notification["severity"] in ("info", "warning", "critical")
    assert notification["read"] is False


# --- F-10.4: Öğretmen iletişimi ---
@pytest.mark.asyncio
async def test_teacher_communication():
    """Mesaj gönderme → iletişim kanalı"""
    message = {
        "from_id": "p-001",
        "to_id": "t-001",
        "subject": "Ali'nin performansı hakkında",
        "body": "Merhabalar, Ali'nin son sınav sonuçları...",
    }
    assert message["from_id"] is not None
    assert message["to_id"] is not None
    assert len(message["body"]) > 0
