"""
Veli takip sistemi API endpoint'leri

CODE QUALITY FIX: Improved exception handling, added path validation
"""

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, status
from fastapi.security import HTTPBearer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.dependencies import get_current_user
from models import Kullanici, KullaniciRolu
from models.dashboard import Bildirim
from services.veli_service import VeliOnayTalebi, VeliRaporu, veli_servisi

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/veli",
    tags=["Veli Takip Sistemi (DEPRECATED)"],
    deprecated=True,  # In-memory backend — use /api/v1/parent instead
)
security = HTTPBearer()


async def mevcut_veli_getir(
    current_user=Depends(get_current_user),
):
    r = getattr(current_user, "role", None)
    role = (r.value if hasattr(r, "value") else str(r)).upper()
    if role not in ("PARENT", "ADMIN", "SUPER_ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu islem icin veli yetkisi gerekli",
        )
    # Frozen pydantic yerine duck-typing wrapper kullan
    from types import SimpleNamespace

    veli = SimpleNamespace(
        kullanici_id=str(getattr(current_user, "id", "")),
        rol=KullaniciRolu.VELI,
        email=getattr(current_user, "email", ""),
        id=str(getattr(current_user, "id", "")),
    )
    return veli


async def _require_parent_child(
    db: AsyncSession, veli_id: str, ogrenci_id: str
) -> None:
    """Onaylı parent_child kaydı yoksa veli çocuk verisine erişemez (F4)."""
    row = await db.execute(
        text(
            "SELECT 1 FROM parent_child "
            "WHERE parent_id::text = :p AND child_id::text = :c AND approved = TRUE "
            "LIMIT 1"
        ),
        {"p": str(veli_id), "c": str(ogrenci_id)},
    )
    if row.first() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu öğrencinin verilerine erişim yetkiniz yok",
        )


@router.get("/cocuklar", summary="Çocuk Listesi")
async def cocuk_listesi_getir(
    mevcut_veli=Depends(mevcut_veli_getir),
    db=Depends(__import__("core.database", fromlist=["get_db_session"]).get_db_session),
):
    """
    Velinin çocuklarının listesini getir (DB-direct, in-memory bypass kaldırıldı)
    """
    try:
        from sqlalchemy import text
        veli_id = mevcut_veli.kullanici_id
        result = await db.execute(
            text("""
                SELECT u.id, u.first_name, u.last_name, u.email
                FROM parent_child pc
                JOIN users u ON u.id = pc.child_id
                WHERE pc.parent_id = :veli_id
            """),
            {"veli_id": veli_id},
        )
        rows = result.fetchall()
        cocuklar = [
            {
                "kullanici_id": str(r[0]),
                "ad_soyad": f"{r[1] or ''} {r[2] or ''}".strip(),
                "email": r[3],
            }
            for r in rows
        ]
        return {"success": True, "data": cocuklar, "message": f"{len(cocuklar)} çocuk bulundu"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"cocuk_listesi_getir hata: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Çocuk listesi alınırken hata oluştu",
        )


@router.get(
    "/cocuk/{ogrenci_id}/performans",
    response_model=dict[str, Any],
    summary="Çocuk Performansı",
)
async def cocuk_performansi_getir(
    ogrenci_id: str = Path(
        ...,
        min_length=1,
        max_length=100,
        description="Öğrenci ID'si",
        example="ogrenci_12345",
    ),
    mevcut_veli: Kullanici = Depends(mevcut_veli_getir),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Belirli bir çocuğun detaylı performans verilerini getir

    - **ogrenci_id**: Öğrenci ID'si (validated)
    - **Döndürür**: Detaylı performans analizi ve istatistikler
    """
    try:
        veli_id = mevcut_veli.kullanici_id
        await _require_parent_child(db, veli_id, ogrenci_id)

        performans = await veli_servisi.cocuk_performansini_getir(veli_id, ogrenci_id)

        return {
            "success": True,
            "data": performans,
            "message": "Performans verileri başarıyla alındı",
        }

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu öğrencinin verilerine erişim yetkiniz yok",
        )
    except (ConnectionError, TimeoutError) as e:
        logger.error(f"Database/service connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servis geçici olarak kullanılamıyor",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in cocuk_performansi_getir: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Performans verileri alınırken hata oluştu",
        )


@router.post(
    "/cocuk/{ogrenci_id}/haftalik-rapor",
    response_model=VeliRaporu,
    summary="Haftalık Rapor Oluştur",
)
async def haftalik_rapor_olustur(
    ogrenci_id: str,
    mevcut_veli: Kullanici = Depends(mevcut_veli_getir),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Çocuk için haftalık performans raporu oluştur

    - **ogrenci_id**: Öğrenci ID'si
    - **Döndürür**: Detaylı haftalık rapor
    """
    try:
        veli_id = mevcut_veli.kullanici_id
        await _require_parent_child(db, veli_id, ogrenci_id)

        rapor = await veli_servisi.haftalik_rapor_olustur(veli_id, ogrenci_id)

        return rapor

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Rapor oluşturulurken hata oluştu",
        )


@router.get(
    "/onay-talepleri", response_model=list[VeliOnayTalebi], summary="Onay Talepleri"
)
async def onay_talepleri_listesi(mevcut_veli: Kullanici = Depends(mevcut_veli_getir)):
    """
    Velinin bekleyen onay taleplerini listele

    - **Döndürür**: Bekleyen onay talepleri listesi
    """
    try:
        veli_id = mevcut_veli.kullanici_id

        # Veliye ait onay taleplerini filtrele
        tum_talepler = list(veli_servisi.veli_onay_talepleri.values())
        veli_talepleri = [t for t in tum_talepler if t.veli_id == veli_id]

        return {
            "success": True,
            "data": veli_talepleri,
            "message": f"{len(veli_talepleri)} onay talebi bulundu",
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Onay talepleri alınırken hata oluştu",
        )


@router.post(
    "/onay-talepleri/{talep_id}/yanitla",
    response_model=VeliOnayTalebi,
    summary="Onay Talebi Yanıtla",
)
async def onay_talebi_yanitla(
    talep_id: str,
    onay: bool,
    not_: str | None = None,
    mevcut_veli: Kullanici = Depends(mevcut_veli_getir),
):
    """
    Onay talebini yanıtla (onayla veya reddet)

    - **talep_id**: Onay talebi ID'si
    - **onay**: True (onayla) veya False (reddet)
    - **not_**: Opsiyonel veli notu
    """
    try:
        veli_id = mevcut_veli.kullanici_id

        talep = await veli_servisi.onay_talebi_yanitla(veli_id, talep_id, onay, not_)

        return talep

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Onay talebi yanıtlanırken hata oluştu",
        )


@router.get("/bildirimler", response_model=list[Bildirim], summary="Veli Bildirimleri")
async def veli_bildirimleri(mevcut_veli: Kullanici = Depends(mevcut_veli_getir)):
    """
    Velinin bildirimlerini getir

    - **Döndürür**: Veli bildirimleri listesi
    """
    try:
        veli_id = mevcut_veli.kullanici_id

        bildirimler = await veli_servisi.veli_bildirimlerini_getir(veli_id)

        return {
            "success": True,
            "data": bildirimler,
            "message": f"{len(bildirimler)} bildirim bulundu",
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bildirimler alınırken hata oluştu",
        )


@router.post("/bildirimler/{bildirim_id}/okundu", summary="Bildirimi Okundu İşaretle")
async def bildirim_okundu_isaretle(
    bildirim_id: str, mevcut_veli: Kullanici = Depends(mevcut_veli_getir)
):
    """
    Bildirimi okundu olarak işaretle

    - **bildirim_id**: Bildirim ID'si
    """
    try:
        veli_id = mevcut_veli.kullanici_id

        basarili = await veli_servisi.bildirim_okundu_isaretle(veli_id, bildirim_id)

        if basarili:
            return {"success": True, "message": "Bildirim okundu olarak işaretlendi"}
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Bildirim bulunamadı"
        )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bildirim güncellenirken hata oluştu",
        )


@router.get(
    "/istatistikler",
    response_model=dict[str, Any],
    summary="Veli Dashboard İstatistikleri",
)
async def veli_dashboard_istatistikleri(
    mevcut_veli: Kullanici = Depends(mevcut_veli_getir),
):
    """
    Veli dashboard için genel istatistikler

    - **Döndürür**: Tüm çocukların genel performans özeti
    """
    try:
        veli_id = mevcut_veli.kullanici_id

        # Çocukları getir
        cocuklar = await veli_servisi.veli_cocuklarini_getir(veli_id)

        # Genel istatistikleri hesapla
        toplam_cocuk = len(cocuklar)
        aktif_cocuk = len(
            [
                c
                for c in cocuklar
                if c.get("son_giris") and (datetime.now(UTC) - c["son_giris"]).days < 7
            ]
        )

        # Mock istatistikler (gerçek implementasyonda database'den hesaplanacak)
        istatistikler = {
            "toplam_cocuk_sayisi": toplam_cocuk,
            "aktif_cocuk_sayisi": aktif_cocuk,
            "bu_hafta_toplam_calisma": 2100,  # dakika
            "ortalama_basari_orani": 76.8,
            "bekleyen_onay_sayisi": len(
                [
                    t
                    for t in veli_servisi.veli_onay_talepleri.values()
                    if t.veli_id == veli_id and t.durum == "beklemede"
                ]
            ),
            "okunmamis_bildirim_sayisi": len(
                [
                    b
                    for b in veli_servisi.veli_bildirimleri.get(veli_id, [])
                    if not b.okundu
                ]
            ),
            "en_basarili_cocuk": cocuklar[0]["ad_soyad"] if cocuklar else None,
            "dikkat_gereken_cocuk": None,  # Performansı düşük olan çocuk
        }

        return {
            "success": True,
            "data": istatistikler,
            "message": "İstatistikler başarıyla alındı",
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="İstatistikler alınırken hata oluştu",
        )


# Öğrenci tarafından kullanılacak endpoint'ler
@router.post(
    "/onay-talebi-olustur", response_model=VeliOnayTalebi, summary="Onay Talebi Oluştur"
)
async def onay_talebi_olustur(
    talep_tipi: str,
    aciklama: str,
    current_user=Depends(get_current_user),
):
    """
    Ogrenci tarafindan veli onay talebi olustur

    - **talep_tipi**: Talep turu (sinav_kayit, ek_ders, vb.)
    - **aciklama**: Talep aciklamasi
    """
    try:
        ogrenci_id = str(current_user.id)
        talep = await veli_servisi.onay_talebi_olustur(ogrenci_id, talep_tipi, aciklama)

        return talep

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Onay talebi oluşturulurken hata oluştu",
        )
