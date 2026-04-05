"""
Admin Panel Backend API'leri
Kullanıcı yönetimi, dashboard istatistikleri ve içerik yönetimi

CODE QUALITY FIX: Removed sensitive data exposure in error messages
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from models.enums import KullaniciRolu
from models.user import Kullanici, KullaniciOlustur
from services.admin_service import admin_servisi
from services.user_service import kullanici_servisi
# FIX 2026-04-01: in-memory auth kaldirildi, JWT auth eklendi
from core.dependencies import get_current_user, AuthenticatedUser, UserRole, get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text as _sql_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["Admin Panel"])
security = HTTPBearer()


async def admin_kullanici_getir(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    """Admin kullanicisini JWT token'dan dogrula.

    KALDIRILAN KOD: kullanici_servisi.token_dogrula(token)
    - In-memory dict'te JWT token bulunamiyor -> her zaman None -> 401
    - 58 DB kullanicisi admin paneline higbir zaman giremiyordu

    YENI: core.dependencies.get_current_user() (Bearer + httpOnly cookie)
    DB rolleri buyuk harf saklanir (ADMIN, SUPER_ADMIN).
    str Enum: UserRole.ADMIN == 'admin' == 'ADMIN' degil,
    ama JWT payload 'admin' (lowercase) tasidigindan UserRole.ADMIN eslesir.
    """
    if current_user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu islem icin admin yetkisi gerekli",
        )
    return current_user


# ==================== KULLANICI YÖNETİMİ API'LERİ ====================


@router.get(
    "/users", response_model=List[Any], summary="Tüm Kullanıcıları Listele"
)
async def kullanicilari_listele(
    rol: Optional[str] = Query(None, description="Rol filtresi (STUDENT, TEACHER, PARENT, ADMIN)"),
    aktif: Optional[bool] = Query(None, description="Aktiflik durumu filtresi"),
    sayfa: int = Query(1, ge=1, description="Sayfa numarası"),
    sayfa_boyutu: int = Query(20, ge=1, le=50, description="Sayfa boyutu (max 50)"),
    _: AuthenticatedUser = Depends(admin_kullanici_getir),
    db: AsyncSession = Depends(get_db),
) -> List[Any]:
    """
    Tüm kullanıcıları listele - DB sorgusu (Admin yetkisi gerekli)
    FIX 2026-04-01: admin_servisi mock data yerine dogrudan DB sorgusu.
    """
    try:
        where_clauses = []
        params: Dict[str, Any] = {}
        if rol:
            where_clauses.append("role = :rol")
            params["rol"] = rol.upper()
        if aktif is not None:
            where_clauses.append("is_active = :aktif")
            params["aktif"] = aktif
        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        params["limit"] = sayfa_boyutu
        params["offset"] = (sayfa - 1) * sayfa_boyutu
        result = await db.execute(_sql_text(f"""
            SELECT id, email, username, first_name, last_name,
                   role, is_active, created_at, last_login, total_xp, level
            FROM users {where_sql}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """), params)
        return [dict(r) for r in result.mappings().all()]
    except Exception as e:
        logger.error(f"Error in kullanicilari_listele: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kullanici listesi alinirken hata olustu",
        )


@router.post("/users", response_model=Dict[str, Any], summary="Yeni Kullanıcı Oluştur")
async def kullanici_olustur(
    kullanici_data: Dict[str, Any],
    _: AuthenticatedUser = Depends(admin_kullanici_getir),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Yeni kullanici olustur — auth servisi uzerinden kayit."""
    # Kayit islemi auth.py /kayit endpointinde yapiliyor.
    # Admin panelinden kullanici olusturmak icin oraya yonlendir.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Kullanici olusturmak icin /api/v1/auth/kayit endpoint'ini kullanin.",
    )


@router.get("/users/{kullanici_id}", response_model=Dict[str, Any], summary="Kullanıcı Detayı")
async def kullanici_detay(
    kullanici_id: str,
    _: AuthenticatedUser = Depends(admin_kullanici_getir),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Belirli kullanicinin detay bilgilerini DB'den getir."""
    try:
        result = await db.execute(_sql_text("""
            SELECT id, email, username, first_name, last_name,
                   role, is_active, created_at, last_login,
                   total_xp, level, phone
            FROM users WHERE id = :uid
        """), {"uid": kullanici_id})
        row = result.mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Kullanici bulunamadi")
        return dict(row)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"kullanici_detay error: {e}", exc_info=True)
        raise HTTPException(500, detail="Kullanici bilgisi alinamadi")


@router.put("/users/{kullanici_id}", response_model=Dict[str, Any], summary="Kullanıcı Güncelle")
async def kullanici_guncelle(
    kullanici_id: str,
    kullanici_data: Dict[str, Any],
    _: AuthenticatedUser = Depends(admin_kullanici_getir),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Kullanici is_active / role guncelle. Diger alanlar ignora edilir."""
    try:
        updates, params = [], {"uid": kullanici_id}
        if "is_active" in kullanici_data:
            updates.append("is_active = :is_active")
            params["is_active"] = bool(kullanici_data["is_active"])
        if "role" in kullanici_data:
            new_role = str(kullanici_data["role"]).upper()
            if new_role not in ("STUDENT", "TEACHER", "PARENT", "ADMIN"):
                raise HTTPException(400, detail="Gecersiz rol")
            updates.append("role = :role")
            params["role"] = new_role
        if not updates:
            raise HTTPException(400, detail="Guncellenecek alan yok")
        await db.execute(_sql_text(
            f"UPDATE users SET {', '.join(updates)} WHERE id = :uid"
        ), params)
        await db.commit()
        result = await db.execute(
            _sql_text("SELECT id, email, role, is_active FROM users WHERE id = :uid"),
            {"uid": kullanici_id}
        )
        row = result.mappings().first()
        if not row:
            raise HTTPException(404, detail="Kullanici bulunamadi")
        return {"success": True, "data": dict(row)}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"kullanici_guncelle error: {e}", exc_info=True)
        raise HTTPException(500, detail="Guncelleme basarisiz")


@router.delete("/users/{kullanici_id}", summary="Kullanıcı Deaktive Et")
async def kullanici_sil(
    kullanici_id: str,
    _: AuthenticatedUser = Depends(admin_kullanici_getir),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Hard delete yerine soft delete: is_active=False yapar."""
    try:
        result = await db.execute(_sql_text(
            "UPDATE users SET is_active=FALSE WHERE id=:uid RETURNING id, email"
        ), {"uid": kullanici_id})
        await db.commit()
        row = result.mappings().first()
        if not row:
            raise HTTPException(404, detail="Kullanici bulunamadi")
        return {"success": True, "message": f"{row['email']} deaktive edildi"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"kullanici_sil error: {e}", exc_info=True)
        raise HTTPException(500, detail="Islem basarisiz")


# ==================== DASHBOARD İSTATİSTİKLERİ ====================


@router.get("/dashboard/stats", summary="Admin Dashboard İstatistikleri")
async def dashboard_istatistikleri(
    _: AuthenticatedUser = Depends(admin_kullanici_getir),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Admin dashboard genel istatistikleri — dogrudan DB sorgusu.
    FIX 2026-04-01: mock data kaldirildi.
    """
    try:
        result = await db.execute(_sql_text("""
            SELECT
                COUNT(*)                                          AS toplam_kullanici,
                SUM(CASE WHEN is_active THEN 1 ELSE 0 END)       AS aktif_kullanici,
                SUM(CASE WHEN role='STUDENT' THEN 1 ELSE 0 END)  AS ogrenci,
                SUM(CASE WHEN role='TEACHER' THEN 1 ELSE 0 END)  AS ogretmen,
                SUM(CASE WHEN role='PARENT'  THEN 1 ELSE 0 END)  AS veli,
                SUM(CASE WHEN role='ADMIN'   THEN 1 ELSE 0 END)  AS admin,
                SUM(CASE WHEN created_at >= NOW() - INTERVAL '30 days' THEN 1 ELSE 0 END)
                                                                  AS son_30_gun_kayit
            FROM users
        """))
        u = dict(result.mappings().one())

        q = await db.execute(_sql_text("""
            SELECT
                COUNT(*)                                                    AS toplam_soru,
                SUM(CASE WHEN is_active THEN 1 ELSE 0 END)                 AS aktif_soru,
                SUM(CASE WHEN is_calibrated THEN 1 ELSE 0 END)             AS kalibre_soru,
                SUM(CASE WHEN is_calib_pool THEN 1 ELSE 0 END)             AS calib_pool,
                COUNT(DISTINCT subject_area)                                AS ders_sayisi
            FROM question_bank
        """))
        s = dict(q.mappings().one())

        cat = await db.execute(_sql_text(
            "SELECT COUNT(*) AS session_sayisi FROM kiro2_cat_sessions"
        ))
        c = dict(cat.mappings().one())

        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "kullanicilar": u,
                "sorular": s,
                "cat_sessions": c,
            },
        }
    except Exception as e:
        logger.error(f"dashboard_istatistikleri error: {e}", exc_info=True)
        raise HTTPException(500, detail="Istatistikler alinamadi")


# ==================== İÇERİK YÖNETİMİ - SORULAR ====================


@router.get("/content/questions", summary="Soru Bankası Listesi")
async def soru_bankasi_listesi(
    konu: Optional[str] = Query(None),
    zorluk: Optional[str] = Query(None),
    sinav_tipi: Optional[str] = Query(None),
    sayfa: int = Query(1, ge=1),
    sayfa_boyutu: int = Query(20, ge=1, le=50),
    _: AuthenticatedUser = Depends(admin_kullanici_getir),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Soru bankasini listele — dogrudan question_bank DB sorgusu."""
    try:
        clauses, params = [], {}
        if konu:
            clauses.append("LOWER(subject_area) = LOWER(:konu)")
            params["konu"] = konu
        if zorluk:
            clauses.append("difficulty_level = :zorluk")
            params["zorluk"] = zorluk
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        params.update({"limit": sayfa_boyutu, "offset": (sayfa - 1) * sayfa_boyutu})
        rows = await db.execute(_sql_text(f"""
            SELECT id, question_text, subject_area, difficulty_level,
                   correct_answer, is_calibrated, is_calib_pool,
                   irt_difficulty, irt_discrimination
            FROM question_bank {where}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """), params)
        cnt = await db.execute(
            _sql_text(f"SELECT COUNT(*) FROM question_bank {where}"),
            {k: v for k, v in params.items() if k not in ("limit", "offset")},
        )
        return {
            "success": True,
            "data": [dict(r) for r in rows.mappings().all()],
            "total_count": cnt.scalar(),
        }
    except Exception as e:
        logger.error(f"soru_bankasi_listesi error: {e}", exc_info=True)
        raise HTTPException(500, detail="Sorular alinamadi")


@router.post("/content/questions", summary="Yeni Soru Ekle")
async def soru_ekle(
    soru_data: Dict[str, Any], _: Kullanici = Depends(admin_kullanici_getir)
) -> Dict[str, Any]:
    """
    Soru bankasına yeni soru ekle (Admin yetkisi gerekli)

    Gerekli alanlar:
    - soru_metni: Soru metni
    - secenekler: A, B, C, D seçenekleri
    - dogru_cevap: Doğru seçenek
    - konu: Konu adı
    - zorluk_seviyesi: Kolay/Orta/Zor
    - sinav_tipi: TYT/AYT/YDT
    """
    try:
        soru = await admin_servisi.soru_ekle(soru_data)
        return {"success": True, "data": soru, "message": "Soru başarıyla eklendi"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Islem basarisiz. Lutfen tekrar deneyin.")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.put("/content/questions/{soru_id}", summary="Soru Güncelle")
async def soru_guncelle(
    soru_id: str,
    soru_data: Dict[str, Any],
    _: Kullanici = Depends(admin_kullanici_getir),
) -> Dict[str, Any]:
    """
    Mevcut soruyu güncelle (Admin yetkisi gerekli)
    """
    try:
        soru = await admin_servisi.soru_guncelle(soru_id, soru_data)
        return {"success": True, "data": soru, "message": "Soru başarıyla güncellendi"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Islem basarisiz. Lutfen tekrar deneyin.")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.delete("/content/questions/{soru_id}", summary="Soru Sil")
async def soru_sil(
    soru_id: str, _: Kullanici = Depends(admin_kullanici_getir)
) -> Dict[str, Any]:
    """
    Soruyu sil (Admin yetkisi gerekli)
    """
    try:
        basarili = await admin_servisi.soru_sil(soru_id)

        if basarili:
            return {"success": True, "message": "Soru başarıyla silindi"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Soru bulunamadı"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


# ==================== İÇERİK YÖNETİMİ - EĞİTİM MATERYALLERİ ====================


@router.get("/content/educational", summary="Eğitim Materyalleri Listesi")
async def egitim_materyalleri_listesi(
    tur: Optional[str] = Query(None),
    konu: Optional[str] = Query(None),
    onay_durumu: Optional[str] = Query(None),
    sayfa: int = Query(1, ge=1),
    sayfa_boyutu: int = Query(20, ge=1, le=50),
    _: AuthenticatedUser = Depends(admin_kullanici_getir),
) -> Dict[str, Any]:
    """Egitim materyalleri — DB tablosu henuz yok, bos liste dondur."""
    return {"success": True, "data": [], "total_count": 0,
            "message": "educational_materials tablosu henuz olusturulmadi"}


@router.post("/content/educational", summary="Yeni Eğitim Materyali Ekle")
async def egitim_materyali_ekle(
    materyal_data: Dict[str, Any], _: AuthenticatedUser = Depends(admin_kullanici_getir)
) -> Dict[str, Any]:
    raise HTTPException(501, detail="educational_materials tablosu henuz olusturulmadi")


@router.put("/content/educational/{materyal_id}", summary="Eğitim Materyali Güncelle")
async def egitim_materyali_guncelle(
    materyal_id: str, materyal_data: Dict[str, Any],
    _: AuthenticatedUser = Depends(admin_kullanici_getir),
) -> Dict[str, Any]:
    raise HTTPException(501, detail="educational_materials tablosu henuz olusturulmadi")


@router.delete("/content/educational/{materyal_id}", summary="Eğitim Materyali Sil")
async def egitim_materyali_sil(
    materyal_id: str, _: AuthenticatedUser = Depends(admin_kullanici_getir)
) -> Dict[str, Any]:
    raise HTTPException(501, detail="educational_materials tablosu henuz olusturulmadi")


@router.put("/content/educational/{materyal_id}/approve", summary="Eğitim Materyali Onayla")
async def egitim_materyali_onayla(
    materyal_id: str, onay_data: Dict[str, Any],
    _: AuthenticatedUser = Depends(admin_kullanici_getir),
) -> Dict[str, Any]:
    raise HTTPException(501, detail="educational_materials tablosu henuz olusturulmadi")


# ==================== TOPLU İŞLEMLER ====================


@router.post("/content/questions/bulk-upload", summary="Toplu Soru Yükleme")
async def toplu_soru_yukle(
    sorular_data: List[Dict[str, Any]], _: AuthenticatedUser = Depends(admin_kullanici_getir)
) -> Dict[str, Any]:
    raise HTTPException(501, detail="Toplu soru yukleme henuz implement edilmedi")


@router.get("/content/search", summary="İçerik Arama")
async def icerik_ara(
    q: str = Query(..., min_length=2),
    tur: Optional[str] = Query(None),
    sayfa: int = Query(1, ge=1),
    sayfa_boyutu: int = Query(20, ge=1, le=50),
    _: AuthenticatedUser = Depends(admin_kullanici_getir),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """question_bank'ta full-text arama."""
    try:
        params: Dict[str, Any] = {
            "q": f"%{q}%", "limit": sayfa_boyutu,
            "offset": (sayfa - 1) * sayfa_boyutu,
        }
        rows = await db.execute(_sql_text("""
            SELECT id, question_text, subject_area, difficulty_level, correct_answer
            FROM question_bank
            WHERE is_active=TRUE
              AND (LOWER(question_text) LIKE LOWER(:q)
                   OR LOWER(subject_area) LIKE LOWER(:q))
            ORDER BY id LIMIT :limit OFFSET :offset
        """), params)
        cnt = await db.execute(_sql_text("""
            SELECT COUNT(*) FROM question_bank
            WHERE is_active=TRUE
              AND (LOWER(question_text) LIKE LOWER(:q)
                   OR LOWER(subject_area) LIKE LOWER(:q))
        """), {"q": f"%{q}%"})
        return {
            "success": True, "query": q,
            "data": [dict(r) for r in rows.mappings().all()],
            "total_count": cnt.scalar(),
        }
    except Exception as e:
        logger.error(f"icerik_ara error: {e}", exc_info=True)
        raise HTTPException(500, detail="Arama basarisiz")
