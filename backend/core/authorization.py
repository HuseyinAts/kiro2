"""
Authorization Helper Functions
SECURITY FIX: Centralized authorization checks to prevent IDOR attacks
"""


from fastapi import HTTPException, status

from models import Kullanici, KullaniciRolu


class AuthorizationError(HTTPException):
    """Custom authorization error"""

    def __init__(self, detail: str = "Bu işlem için yetkiniz yok"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def require_roles(current_user: Kullanici, allowed_roles: list[KullaniciRolu]) -> None:
    """
    Kullanıcının belirtilen rollerden birine sahip olmasını kontrol et

    Args:
        current_user: Mevcut kullanıcı
        allowed_roles: İzin verilen roller listesi

    Raises:
        AuthorizationError: Kullanıcı yetkili değilse
    """
    if current_user.rol not in allowed_roles:
        raise AuthorizationError(
            f"Bu işlem için {', '.join([r.value for r in allowed_roles])} rollerinden birine sahip olmalısınız"
        )


def require_owner_or_roles(
    current_user: Kullanici,
    resource_owner_id: str,
    allowed_roles: list[KullaniciRolu] | None = None,
) -> None:
    """
    Kaynağın sahibi veya belirtilen rollerden birine sahip olma kontrolü
    IDOR (Insecure Direct Object Reference) attack'lere karşı koruma

    Args:
        current_user: Mevcut kullanıcı
        resource_owner_id: Kaynağın sahibinin kullanici_id'si
        allowed_roles: Ek olarak erişime izin verilen roller (öğretmen, admin vb.)

    Raises:
        AuthorizationError: Kullanıcı yetkili değilse
    """
    # Kullanıcı kaynak sahibi ise izin ver
    if current_user.kullanici_id == resource_owner_id:
        return

    # Allowed roles belirtilmişse kontrol et
    if allowed_roles:
        if current_user.rol in allowed_roles:
            return

    # Yetkisiz erişim
    raise AuthorizationError("Bu kaynağa erişim yetkiniz yok")


def require_admin(current_user: Kullanici) -> None:
    """
    Sadece admin erişimi

    Args:
        current_user: Mevcut kullanıcı

    Raises:
        AuthorizationError: Kullanıcı admin değilse
    """
    require_roles(current_user, [KullaniciRolu.ADMIN])


def require_teacher_or_admin(current_user: Kullanici) -> None:
    """
    Öğretmen veya admin erişimi

    Args:
        current_user: Mevcut kullanıcı

    Raises:
        AuthorizationError: Kullanıcı öğretmen veya admin değilse
    """
    require_roles(current_user, [KullaniciRolu.OGRETMEN, KullaniciRolu.ADMIN])


def require_student_owner_or_privileged(
    current_user: Kullanici, student_user_id: str
) -> None:
    """
    Öğrenci verilerine erişim kontrolü
    - Öğrencinin kendisi
    - Öğretmen
    - Admin
    - Veli (gelecekte öğrenci-veli ilişkisi kontrol edilecek)

    Args:
        current_user: Mevcut kullanıcı
        student_user_id: Öğrencinin kullanici_id'si

    Raises:
        AuthorizationError: Kullanıcı yetkili değilse
    """
    require_owner_or_roles(
        current_user,
        student_user_id,
        [KullaniciRolu.OGRETMEN, KullaniciRolu.ADMIN, KullaniciRolu.VELI],
    )


def check_resource_ownership(
    current_user: Kullanici,
    resource_owner_id: str | None,
    resource_name: str = "kaynak",
) -> None:
    """
    Kaynak sahipliği kontrolü (strict - sadece sahip erişebilir)

    Args:
        current_user: Mevcut kullanıcı
        resource_owner_id: Kaynağın sahibi
        resource_name: Kaynak ismi (hata mesajı için)

    Raises:
        AuthorizationError: Kullanıcı kaynak sahibi değilse
    """
    if not resource_owner_id:
        raise AuthorizationError(f"{resource_name} sahibi belirlenemedi")

    if current_user.kullanici_id != resource_owner_id:
        raise AuthorizationError(f"Bu {resource_name}'a sadece sahibi erişebilir")
