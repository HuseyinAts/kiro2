"""
KIRO2 — YKS Tahmini API
=========================
Endpoint'ler:
  GET  /api/v1/estimate/tyt             → TYT puan tahmini
  GET  /api/v1/estimate/ayt/{puan_turu} → AYT puan tahmini
  GET  /api/v1/estimate/full            → Tam rapor (tüm puan türleri)
  POST /api/v1/estimate/impact          → Ders katkısı analizi
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import User, get_current_user, get_db
from app.services.yks_estimator import (
    DersTheta,
    YKSEstimator,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/estimate", tags=["YKS Tahmini"])


async def _kullanici_thetalarini_cek(
    user_id: str,
    db: AsyncSession,
) -> dict[str, DersTheta]:
    """
    Kullanıcının son CAT oturumlarından θ tahminlerini çek.
    subject_id → ders_kodu eşlemesi subjects tablosundan yapılır.
    """
    try:
        result = await db.execute(
            text("""
        SELECT
            cs.subject_id   AS ders_kodu,
            cs.theta_final,
            cs.se_final
        FROM kiro2_cat_sessions cs
        WHERE cs.user_id = :uid
          AND cs.state   = 'completed'
          AND cs.completed_at >= NOW() - INTERVAL '30 days'
        ORDER BY cs.completed_at DESC
    """),
            {"uid": user_id},
        )
    except Exception as e:
        logger.error(
            f"_kullanici_thetalarini_cek DB hatası: user_id={user_id}, hata={e}"
        )
        return {}

    # DB'deki buyuk harf subject_id -> estimator kisa kod eslesmesi
    SUBJECT_MAP = {
        "MATEMATIK": "mat",
        "TURKCE": "turkce",
        "GEOMETRI": "mat",  # TYT mat icinde
        "FIZIK": "fizik",
        "KIMYA": "kimya",
        "BIYOLOJI": "biyoloji",
        "EDEBIYAT": "edebiyat",
        "TARIH": "tarih1",
        "COGRAFYA": "cografya1",
        "FEN": "fen",
        "SOSYAL": "sosyal",
        "GENEL": "sosyal",
        # kucuk harf zaten dogru geldiyse de destekle
        "matematik": "mat",
        "turkce": "turkce",
        "fizik": "fizik",
        "kimya": "kimya",
        "biyoloji": "biyoloji",
    }

    thetalar: dict[str, DersTheta] = {}
    for row in result.fetchall():
        raw_kod = row.ders_kodu
        kod = SUBJECT_MAP.get(raw_kod, raw_kod.lower())  # bilinmeyenler lower()
        if kod not in thetalar:  # en son oturumu al
            thetalar[kod] = DersTheta(
                ders_kodu=kod,
                theta=float(row.theta_final),
                se=float(row.se_final or 0.5),
            )
    return thetalar


@router.get(
    "/tyt",
    summary="TYT puan tahmini",
    description="Son 30 günlük CAT oturumlarından TYT puan tahmini üretir.",
)
async def tyt_tahmini(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    thetalar = await _kullanici_thetalarini_cek(str(current_user.id), db)
    tyt_thetalar = {
        k: v for k, v in thetalar.items() if k in ("turkce", "sosyal", "mat", "fen")
    }

    if not tyt_thetalar:
        raise HTTPException(
            status_code=404,
            detail="Henüz TYT derslerinde CAT oturumu yok. "
            "Önce placement testini tamamlayın.",
        )

    est = YKSEstimator()
    tahmin = est.tyt_raporu(tyt_thetalar)
    return _puan_to_dict(tahmin)


@router.get(
    "/ayt/{puan_turu}",
    summary="AYT puan tahmini",
)
async def ayt_tahmini(
    puan_turu: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    puan_turu = puan_turu.upper()
    if puan_turu not in ("SAY", "EA", "SÖZ", "SOZ", "DİL", "DIL"):
        raise HTTPException(
            status_code=400, detail="Geçersiz puan türü. SAY | EA | SÖZ | DİL"
        )
    puan_turu = puan_turu.replace("SOZ", "SÖZ").replace("DIL", "DİL")

    thetalar = await _kullanici_thetalarini_cek(str(current_user.id), db)
    tyt_thetalar = {
        k: v for k, v in thetalar.items() if k in ("turkce", "sosyal", "mat", "fen")
    }
    ayt_thetalar = {
        k: v
        for k, v in thetalar.items()
        if k
        in (
            "mat",
            "fizik",
            "kimya",
            "biyoloji",
            "edebiyat",
            "tarih1",
            "tarih2",
            "cografya1",
            "cografya2",
            "felsefe",
            "din",
        )
    }

    if not tyt_thetalar:
        raise HTTPException(status_code=404, detail="TYT oturumu bulunamadı.")

    est = YKSEstimator()
    tahmin = est.ayt_raporu(puan_turu, tyt_thetalar, ayt_thetalar)
    return _puan_to_dict(tahmin)


@router.get(
    "/full",
    summary="Tam YKS tahmin raporu",
)
async def tam_rapor(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    thetalar = await _kullanici_thetalarini_cek(str(current_user.id), db)
    tyt_thetalar = {
        k: v for k, v in thetalar.items() if k in ("turkce", "sosyal", "mat", "fen")
    }
    ayt_thetalar = {
        k: v for k, v in thetalar.items() if k not in ("turkce", "sosyal", "fen")
    }

    if not tyt_thetalar:
        raise HTTPException(status_code=404, detail="Henüz CAT oturumu bulunamadı.")

    est = YKSEstimator()
    rapor = est.tam_rapor(tyt_thetalar, ayt_thetalar if ayt_thetalar else None)

    return {
        "tyt": _puan_to_dict(rapor.tyt) if rapor.tyt else None,
        "say": _puan_to_dict(rapor.say) if rapor.say else None,
        "ea": _puan_to_dict(rapor.ea) if rapor.ea else None,
        "soz": _puan_to_dict(rapor.soz) if rapor.soz else None,
        "dil": _puan_to_dict(rapor.dil) if rapor.dil else None,
        "oneriler": rapor.oneriler,
    }


class KatkiRequest(BaseModel):
    puan_turu: str = Field(..., description="SAY | EA | SÖZ | TYT")
    ders_kodu: str = Field(..., description="mat | fizik | turkce ...")
    hedef_theta: float = Field(..., description="Hedef IRT θ değeri")


@router.post(
    "/impact",
    summary="Ders katkısı analizi",
    description="Bu derste θ'yı artırırsam puanım ne kadar değişir?",
)
async def ders_katkisi(
    body: KatkiRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    thetalar = await _kullanici_thetalarini_cek(str(current_user.id), db)
    mevcut = thetalar.get(body.ders_kodu)
    if mevcut is None:
        raise HTTPException(
            status_code=404, detail=f"'{body.ders_kodu}' dersi için oturum yok."
        )

    est = YKSEstimator()
    sonuc = est.tek_ders_katkisi(
        puan_turu=body.puan_turu.upper(),
        ders_kodu=body.ders_kodu,
        mevcut_theta=mevcut.theta,
        hedef_theta=body.hedef_theta,
        diger_thetalar=thetalar,
    )
    return {
        "ders_kodu": body.ders_kodu,
        "mevcut_theta": mevcut.theta,
        "hedef_theta": body.hedef_theta,
        "tahmini_puan_artisi": sonuc["puan_artisi"],
        "siralama_degisimi": sonuc["siralama_degisimi"],
        "yorum": (
            f"θ'yı {mevcut.theta:.1f} → {body.hedef_theta:.1f} "
            f"artırırsan {body.puan_turu} puanın yaklaşık "
            f"{abs(sonuc['puan_artisi']):.1f} puan "
            f"{'artar' if sonuc['puan_artisi'] > 0 else 'azalır'}."
        ),
    }


@router.get(
    "/thetas",
    summary="Kullanıcı ders theta listesi",
    description="Her ders için son CAT oturumundan theta ve seviye döndürür.",
)
async def ders_thetalar(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    thetalar = await _kullanici_thetalarini_cek(str(current_user.id), db)
    THETA_LABEL = {
        range(-100, -15): "Temel",
        range(-15, -5): "Orta-Temel",
        range(-5, 5): "Orta",
        range(5, 15): "Orta-İleri",
        range(15, 100): "İleri",
    }

    def theta_label(theta: float) -> str:
        t10 = int(theta * 10)
        for r, label in THETA_LABEL.items():
            if t10 in r:
                return label
        return "İleri" if theta > 1.5 else "Temel"

    DERS_ADI = {
        "mat": "Matematik",
        "turkce": "Türkçe",
        "fizik": "Fizik",
        "kimya": "Kimya",
        "biyoloji": "Biyoloji",
        "fen": "Fen Bilimleri",
        "sosyal": "Sosyal Bilimler",
        "edebiyat": "Edebiyat",
        "tarih1": "Tarih",
        "cografya1": "Coğrafya",
    }
    return [
        {
            "ders_kodu": kod,
            "ders_adi": DERS_ADI.get(kod, kod),
            "theta": round(dt.theta, 3),
            "se": round(dt.se, 3),
            "seviye": theta_label(dt.theta),
        }
        for kod, dt in thetalar.items()
    ]


def _puan_to_dict(t) -> dict:
    if t is None:
        return {}
    return {
        "puan_turu": t.puan_turu,
        "puan": t.puan,
        "alt_sinir": t.alt_sinir,
        "ust_sinir": t.ust_sinir,
        "tahmini_siralama": t.tahmini_siralama,
        "siralama_alt": t.siralama_alt,
        "siralama_ust": t.siralama_ust,
        "yuzdelik": t.yuzdelik,
        "guvenilik": t.guvenilik,
    }
