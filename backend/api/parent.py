"""
Veli (Parent) API endpoint'leri
Türkiye Üniversite Sınavları Hazırlık Platformu için veli takip sistemi
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_user, get_db, AuthenticatedUser, UserRole
from models.parent import (
    ChildPerformanceData,
    ParentChildRelationCreate,
    ParentChildRelationResponse,
    ParentDashboardData,
    ParentNotificationCreate,
    ParentNotificationResponse,
    WeeklyReportData,
)
from services.parent_service import ParentService

router = APIRouter(prefix="/api/v1/parent", tags=["parent"])


@router.post("/children", response_model=ParentChildRelationResponse)
async def create_parent_child_relation(
    relation_data: ParentChildRelationCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Veli-çocuk ilişkisi oluştur

    Veli, çocuğunun email adresini girerek takip isteği gönderir.
    Çocuk bu isteği onaylamalıdır.
    """
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem sadece veli hesapları tarafından yapılabilir",
        )

    try:
        parent_service = ParentService(db)
        result = await parent_service.create_parent_child_relation(
            current_user.id, relation_data
        )
        return result
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
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/children", response_model=list[ParentChildRelationResponse])
async def get_parent_children(
    current_user: AuthenticatedUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Velinin onaylanmış çocuklarını listele
    """
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem sadece veli hesapları tarafından yapılabilir",
        )

    try:
        parent_service = ParentService(db)
        children = await parent_service.get_parent_children(current_user.id)
        return children
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/children/{child_id}/performance", response_model=ChildPerformanceData)
async def get_child_performance(
    child_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Çocuğun performans verilerini getir

    Son 30 günün sınav sonuçları, çalışma süresi ve performans analizi
    """
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem sadece veli hesapları tarafından yapılabilir",
        )

    try:
        parent_service = ParentService(db)
        performance = await parent_service.get_child_performance(
            current_user.id, child_id
        )
        return performance
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/children/{child_id}/weekly-report", response_model=WeeklyReportData)
async def get_weekly_report(
    child_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Çocuğun haftalık raporunu getir

    Bu haftanın çalışma özeti, başarılar ve öneriler
    """
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem sadece veli hesapları tarafından yapılabilir",
        )

    try:
        parent_service = ParentService(db)

        # İlişki kontrolü için önce performans verilerini çek
        await parent_service.get_child_performance(current_user.id, child_id)

        # Haftalık rapor oluştur
        report = await parent_service.generate_weekly_report(child_id)
        return report
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/notifications", response_model=ParentNotificationResponse)
async def create_notification(
    notification_data: ParentNotificationCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Veli bildirimi oluştur

    Sistem tarafından otomatik olarak oluşturulan bildirimler için kullanılır
    """
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem sadece veli hesapları tarafından yapılabilir",
        )

    try:
        parent_service = ParentService(db)
        notification = await parent_service.create_notification(
            current_user.id, notification_data
        )
        return notification
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
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/notifications", response_model=list[ParentNotificationResponse])
async def get_notifications(
    unread_only: bool = False,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Veli bildirimlerini getir

    unread_only=true ile sadece okunmamış bildirimleri getirebilirsiniz
    """
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem sadece veli hesapları tarafından yapılabilir",
        )

    try:
        parent_service = ParentService(db)
        notifications = await parent_service.get_parent_notifications(
            current_user.id, unread_only
        )
        return notifications
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.put("/notifications/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: int,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Bildirimi okundu olarak işaretle
    """
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem sadece veli hesapları tarafından yapılabilir",
        )

    try:
        parent_service = ParentService(db)
        await parent_service.mark_notification_as_read(current_user.id, notification_id)
        return {"success": True, "message": "Bildirim okundu olarak işaretlendi"}
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/dashboard", response_model=ParentDashboardData)
async def get_parent_dashboard(
    current_user: AuthenticatedUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Veli dashboard verilerini getir

    Çocukların performansı, bildirimler ve genel özet
    """
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem sadece veli hesapları tarafından yapılabilir",
        )

    try:
        parent_service = ParentService(db)
        dashboard_data = await parent_service.get_parent_dashboard_data(current_user.id)
        return dashboard_data
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


# Öğrenci tarafından kullanılacak endpoint'ler
@router.put("/approval/{relation_id}")
async def approve_parent_relation(
    relation_id: int,
    approved: bool,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Veli ilişkisini onayla/reddet (Öğrenci tarafından)

    Öğrenci, veli tarafından gönderilen takip isteğini onaylar veya reddeder
    """
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem sadece öğrenci hesapları tarafından yapılabilir",
        )

    try:
        parent_service = ParentService(db)
        await parent_service.approve_parent_child_relation(
            current_user.id, relation_id, approved
        )

        action = "onaylandı" if approved else "reddedildi"
        return {"success": True, "message": f"Veli ilişkisi {action}"}
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
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


