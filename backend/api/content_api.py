"""
İçerik Yönetim API'si
Teknofest 2025 Eğitim Eylemci Platformu
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4

from models.content_models import (
    MakaleIcerik,
    VideoIcerik,
    QuizIcerik,
    ContentType,
    ContentStats,
    ContentInteraction,
    InteractionType,
    ContentSearchRequest,
    BulkContentImport,
)

router = APIRouter(prefix="/api/v1/content", tags=["İçerik Yönetimi"])

# Geçici veri deposu (production'da database kullanılacak)
makale_store: Dict[str, MakaleIcerik] = {}
video_store: Dict[str, VideoIcerik] = {}
quiz_store: Dict[str, QuizIcerik] = {}
interaction_store: List[ContentInteraction] = []
stats_store: Dict[str, ContentStats] = {}


# ==================== MAKALE ENDPOINTLERİ ====================


@router.post("/makale", response_model=Dict[str, Any])
async def create_makale(makale: MakaleIcerik):
    """
    Yeni makale oluştur

    - **baslik**: Makale başlığı (3-200 karakter)
    - **icerik**: Makale içeriği (min 50 karakter)
    - **kategori**: Makale kategorisi
    - **yazar**: Makale yazarı
    - **etiketler**: Makale etiketleri (max 10 adet)
    """
    try:
        # ID ve tarih ataması
        if not makale.id:
            makale.id = str(uuid4())
        makale.yayinlanma_tarihi = datetime.now()

        # Store'a kaydet
        makale_store[makale.id] = makale

        # İstatistik oluştur
        stats_store[makale.id] = ContentStats(
            content_id=makale.id, content_type=ContentType.MAKALE
        )

        return {
            "success": True,
            "data": makale.dict(),
            "message": "Makale başarıyla oluşturuldu",
        }
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Makale oluşturma hatası: {str(e)}"
        )


@router.get("/makale/{makale_id}", response_model=Dict[str, Any])
async def get_makale(makale_id: str):
    """
    Makale detayını getir ve görüntüleme sayısını artır
    """
    if makale_id not in makale_store:
        raise HTTPException(status_code=404, detail="Makale bulunamadı")

    makale = makale_store[makale_id]

    # Görüntüleme sayısını artır
    makale.goruntuleme_sayisi += 1

    # İstatistikleri güncelle
    if makale_id in stats_store:
        stats_store[makale_id].total_views += 1
        stats_store[makale_id].last_updated = datetime.now()

    return {"success": True, "data": makale.dict()}


@router.get("/makale", response_model=Dict[str, Any])
async def list_makaleler(
    kategori: Optional[str] = None,
    etiket: Optional[str] = None,
    yazar: Optional[str] = None,
    aktif: Optional[bool] = True,
    skip: int = Query(0, ge=0, description="Atlanacak kayıt sayısı"),
    limit: int = Query(20, ge=1, le=100, description="Getirilecek kayıt sayısı"),
):
    """
    Makale listesini getir (filtreleme ve sayfalama ile)
    """
    # Filtreleme
    makaleler = list(makale_store.values())

    if kategori:
        makaleler = [m for m in makaleler if m.kategori.lower() == kategori.lower()]

    if etiket:
        makaleler = [
            m for m in makaleler if etiket.lower() in [e.lower() for e in m.etiketler]
        ]

    if yazar:
        makaleler = [m for m in makaleler if yazar.lower() in m.yazar.lower()]

    if aktif is not None:
        makaleler = [m for m in makaleler if m.aktif == aktif]

    # Sıralama (en yeni önce)
    makaleler.sort(key=lambda x: x.yayinlanma_tarihi, reverse=True)

    # Pagination
    total = len(makaleler)
    makaleler = makaleler[skip : skip + limit]

    return {
        "success": True,
        "data": [m.dict() for m in makaleler],
        "pagination": {
            "total": total,
            "skip": skip,
            "limit": limit,
            "has_next": skip + limit < total,
        },
    }


@router.put("/makale/{makale_id}", response_model=Dict[str, Any])
async def update_makale(makale_id: str, update_data: Dict[str, Any]):
    """
    Makale güncelle
    """
    if makale_id not in makale_store:
        raise HTTPException(status_code=404, detail="Makale bulunamadı")

    makale = makale_store[makale_id]

    # Güncelleme
    allowed_fields = ["baslik", "icerik", "ozet", "kategori", "etiketler", "aktif"]
    for key, value in update_data.items():
        if key in allowed_fields and hasattr(makale, key):
            setattr(makale, key, value)

    makale.guncellenme_tarihi = datetime.now()

    return {
        "success": True,
        "data": makale.dict(),
        "message": "Makale başarıyla güncellendi",
    }


@router.delete("/makale/{makale_id}", response_model=Dict[str, Any])
async def delete_makale(makale_id: str, soft_delete: bool = True):
    """
    Makale sil (varsayılan olarak soft delete)
    """
    if makale_id not in makale_store:
        raise HTTPException(status_code=404, detail="Makale bulunamadı")

    if soft_delete:
        # Soft delete - sadece aktif durumunu false yap
        makale_store[makale_id].aktif = False
        makale_store[makale_id].guncellenme_tarihi = datetime.now()
        message = "Makale devre dışı bırakıldı"
    else:
        # Hard delete
        del makale_store[makale_id]
        if makale_id in stats_store:
            del stats_store[makale_id]
        message = "Makale kalıcı olarak silindi"

    return {"success": True, "message": message}


@router.post("/makale/{makale_id}/like", response_model=Dict[str, Any])
async def like_makale(makale_id: str, user_id: str):
    """
    Makale beğen/beğenmekten vazgeç
    """
    if makale_id not in makale_store:
        raise HTTPException(status_code=404, detail="Makale bulunamadı")

    makale = makale_store[makale_id]

    # Etkileşim kaydı oluştur
    interaction = ContentInteraction(
        user_id=user_id,
        content_id=makale_id,
        content_type=ContentType.MAKALE,
        interaction_type=InteractionType.LIKE,
    )
    interaction_store.append(interaction)

    # Beğeni sayısını artır
    makale.begeni_sayisi += 1

    # İstatistikleri güncelle
    if makale_id in stats_store:
        stats_store[makale_id].total_likes += 1
        stats_store[makale_id].last_updated = datetime.now()

    return {
        "success": True,
        "data": {"begeni_sayisi": makale.begeni_sayisi},
        "message": "Makale beğenildi",
    }


# ==================== VIDEO ENDPOINTLERİ ====================


@router.post("/video", response_model=Dict[str, Any])
async def create_video(video: VideoIcerik, background_tasks: BackgroundTasks):
    """
    Yeni video oluştur
    """
    try:
        # ID ve tarih ataması
        if not video.id:
            video.id = str(uuid4())
        video.yayinlanma_tarihi = datetime.now()

        # Platform ID çıkar
        platform_id = video.extract_platform_id()
        if platform_id:
            video.platform_id = platform_id

        # Store'a kaydet
        video_store[video.id] = video

        # İstatistik oluştur
        stats_store[video.id] = ContentStats(
            content_id=video.id, content_type=ContentType.VIDEO
        )

        # Arka planda thumbnail oluştur
        background_tasks.add_task(generate_video_thumbnail, video.id, video.video_url)

        return {
            "success": True,
            "data": video.dict(),
            "message": "Video başarıyla oluşturuldu",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Video oluşturma hatası: {str(e)}")


@router.get("/video/{video_id}", response_model=Dict[str, Any])
async def get_video(video_id: str):
    """
    Video detayını getir ve izlenme sayısını artır
    """
    if video_id not in video_store:
        raise HTTPException(status_code=404, detail="Video bulunamadı")

    video = video_store[video_id]

    # İzlenme sayısını artır
    video.izlenme_sayisi += 1

    # İstatistikleri güncelle
    if video_id in stats_store:
        stats_store[video_id].total_views += 1
        stats_store[video_id].last_updated = datetime.now()

    return {"success": True, "data": video.dict()}


@router.get("/video", response_model=Dict[str, Any])
async def list_videolar(
    kategori: Optional[str] = None,
    platform: Optional[str] = None,
    min_sure: Optional[int] = None,
    max_sure: Optional[int] = None,
    kalite: Optional[str] = None,
    aktif: Optional[bool] = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Video listesini getir (filtreleme ve sayfalama ile)
    """
    # Filtreleme
    videolar = list(video_store.values())

    if kategori:
        videolar = [v for v in videolar if v.kategori.lower() == kategori.lower()]

    if platform:
        videolar = [v for v in videolar if v.platform.lower() == platform.lower()]

    if min_sure is not None:
        videolar = [v for v in videolar if v.sure >= min_sure]

    if max_sure is not None:
        videolar = [v for v in videolar if v.sure <= max_sure]

    if kalite:
        videolar = [v for v in videolar if v.kalite == kalite]

    if aktif is not None:
        videolar = [v for v in videolar if v.aktif == aktif]

    # Sıralama (en yeni önce)
    videolar.sort(key=lambda x: x.yayinlanma_tarihi, reverse=True)

    # Pagination
    total = len(videolar)
    videolar = videolar[skip : skip + limit]

    return {
        "success": True,
        "data": [v.dict() for v in videolar],
        "pagination": {
            "total": total,
            "skip": skip,
            "limit": limit,
            "has_next": skip + limit < total,
        },
    }


# ==================== GENEL ENDPOINTLERİ ====================


@router.post("/search", response_model=Dict[str, Any])
async def search_content(search_request: ContentSearchRequest):
    """
    İçeriklerde gelişmiş arama yap
    """
    query = search_request.query.lower()
    results = []

    # Makalelerde ara
    if (
        not search_request.filters
        or not search_request.filters.content_types
        or ContentType.MAKALE in search_request.filters.content_types
    ):
        for makale in makale_store.values():
            if not makale.aktif:
                continue

            score = 0
            highlighted_title = makale.baslik
            highlighted_content = makale.icerik[:200] + "..."

            # Başlıkta arama
            if query in makale.baslik.lower():
                score += 10
                if search_request.highlight:
                    highlighted_title = makale.baslik.replace(
                        query, f"<mark>{query}</mark>"
                    )

            # İçerikte arama
            if query in makale.icerik.lower():
                score += 5
                if search_request.highlight:
                    # Basit highlighting
                    highlighted_content = (
                        makale.icerik[:200].replace(query, f"<mark>{query}</mark>")
                        + "..."
                    )

            # Etiketlerde arama
            if any(query in etiket.lower() for etiket in makale.etiketler):
                score += 7

            if score > 0:
                results.append(
                    {
                        "type": "makale",
                        "score": score,
                        "data": makale.dict(),
                        "highlights": {
                            "title": highlighted_title,
                            "content": highlighted_content,
                        },
                    }
                )

    # Videolarda ara
    if (
        not search_request.filters
        or not search_request.filters.content_types
        or ContentType.VIDEO in search_request.filters.content_types
    ):
        for video in video_store.values():
            if not video.aktif:
                continue

            score = 0
            highlighted_title = video.baslik
            highlighted_desc = video.aciklama or ""

            if query in video.baslik.lower():
                score += 10
                if search_request.highlight:
                    highlighted_title = video.baslik.replace(
                        query, f"<mark>{query}</mark>"
                    )

            if video.aciklama and query in video.aciklama.lower():
                score += 5
                if search_request.highlight:
                    highlighted_desc = video.aciklama.replace(
                        query, f"<mark>{query}</mark>"
                    )

            if score > 0:
                results.append(
                    {
                        "type": "video",
                        "score": score,
                        "data": video.dict(),
                        "highlights": {
                            "title": highlighted_title,
                            "description": highlighted_desc,
                        },
                    }
                )

    # Sıralama
    if search_request.sort_by == "relevance":
        results.sort(key=lambda x: x["score"], reverse=True)
    elif search_request.sort_by == "date":
        results.sort(
            key=lambda x: x["data"]["yayinlanma_tarihi"],
            reverse=(search_request.sort_order == "desc"),
        )
    elif search_request.sort_by == "popularity":
        results.sort(
            key=lambda x: x["data"].get("goruntuleme_sayisi", 0)
            + x["data"].get("izlenme_sayisi", 0),
            reverse=(search_request.sort_order == "desc"),
        )

    # Pagination
    total = len(results)
    start_idx = (search_request.page - 1) * search_request.page_size
    end_idx = start_idx + search_request.page_size
    results = results[start_idx:end_idx]

    return {
        "success": True,
        "data": results,
        "pagination": {
            "total": total,
            "page": search_request.page,
            "page_size": search_request.page_size,
            "total_pages": (total + search_request.page_size - 1)
            // search_request.page_size,
        },
        "query": search_request.query,
    }


@router.get("/recommendations/{user_id}", response_model=Dict[str, Any])
async def get_recommendations(
    user_id: str,
    content_type: Optional[ContentType] = None,
    limit: int = Query(10, ge=1, le=50),
):
    """
    Kullanıcı için kişiselleştirilmiş öneriler
    """
    # Basit öneri algoritması (gerçek uygulamada ML modeli kullanılacak)
    recommendations = []

    # Kullanıcının geçmiş etkileşimlerini al
    user_interactions = [i for i in interaction_store if i.user_id == user_id]

    # Etkileşim geçmişi varsa benzer içerikleri öner
    if user_interactions:
        # En çok etkileşim kurduğu kategorileri bul
        categories = {}
        for interaction in user_interactions:
            if (
                interaction.content_type == ContentType.MAKALE
                and interaction.content_id in makale_store
            ):
                cat = makale_store[interaction.content_id].kategori
                categories[cat] = categories.get(cat, 0) + 1
            elif (
                interaction.content_type == ContentType.VIDEO
                and interaction.content_id in video_store
            ):
                cat = video_store[interaction.content_id].kategori
                categories[cat] = categories.get(cat, 0) + 1

        # En popüler kategorilerden öneriler
        top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[
            :3
        ]

        for category, _ in top_categories:
            # Makale önerileri
            if not content_type or content_type == ContentType.MAKALE:
                category_articles = [
                    m
                    for m in makale_store.values()
                    if m.kategori == category and m.aktif
                ]
                category_articles.sort(key=lambda x: x.begeni_sayisi, reverse=True)
                recommendations.extend(
                    [
                        {
                            "type": "makale",
                            "data": m.dict(),
                            "reason": f"'{category}' kategorisindeki popüler içerik",
                        }
                        for m in category_articles[:2]
                    ]
                )

            # Video önerileri
            if not content_type or content_type == ContentType.VIDEO:
                category_videos = [
                    v
                    for v in video_store.values()
                    if v.kategori == category and v.aktif
                ]
                category_videos.sort(key=lambda x: x.izlenme_sayisi, reverse=True)
                recommendations.extend(
                    [
                        {
                            "type": "video",
                            "data": v.dict(),
                            "reason": f"'{category}' kategorisindeki popüler içerik",
                        }
                        for v in category_videos[:2]
                    ]
                )

    # Etkileşim geçmişi yoksa genel popüler içerikleri öner
    if not recommendations:
        # Popüler makaleler
        if not content_type or content_type == ContentType.MAKALE:
            popular_articles = sorted(
                [m for m in makale_store.values() if m.aktif],
                key=lambda x: x.goruntuleme_sayisi + x.begeni_sayisi,
                reverse=True,
            )[:5]
            recommendations.extend(
                [
                    {"type": "makale", "data": m.dict(), "reason": "Popüler içerik"}
                    for m in popular_articles
                ]
            )

        # Popüler videolar
        if not content_type or content_type == ContentType.VIDEO:
            popular_videos = sorted(
                [v for v in video_store.values() if v.aktif],
                key=lambda x: x.izlenme_sayisi + x.begeni_sayisi,
                reverse=True,
            )[:5]
            recommendations.extend(
                [
                    {"type": "video", "data": v.dict(), "reason": "Popüler içerik"}
                    for v in popular_videos
                ]
            )

    # Limit uygula
    recommendations = recommendations[:limit]

    return {
        "success": True,
        "data": recommendations,
        "user_id": user_id,
        "total": len(recommendations),
    }


@router.get("/trending", response_model=Dict[str, Any])
async def get_trending_content(
    period: str = Query("week", regex="^(day|week|month)$"),
    content_type: Optional[ContentType] = None,
    limit: int = Query(20, ge=1, le=100),
):
    """
    Trend içerikleri getir
    """
    # Basit trend algoritması (gerçek uygulamada zaman bazlı analiz yapılacak)
    trending = []

    # Makaleler için trend hesaplama
    if not content_type or content_type == ContentType.MAKALE:
        articles = [m for m in makale_store.values() if m.aktif]
        # Trend skoru: görüntüleme + beğeni * 2
        for article in articles:
            trend_score = article.goruntuleme_sayisi + (article.begeni_sayisi * 2)
            trending.append(
                {"type": "makale", "data": article.dict(), "trend_score": trend_score}
            )

    # Videolar için trend hesaplama
    if not content_type or content_type == ContentType.VIDEO:
        videos = [v for v in video_store.values() if v.aktif]
        for video in videos:
            trend_score = video.izlenme_sayisi + (video.begeni_sayisi * 2)
            trending.append(
                {"type": "video", "data": video.dict(), "trend_score": trend_score}
            )

    # Trend skoruna göre sırala
    trending.sort(key=lambda x: x["trend_score"], reverse=True)
    trending = trending[:limit]

    return {"success": True, "data": trending, "period": period, "total": len(trending)}


@router.get("/stats", response_model=Dict[str, Any])
async def get_content_stats():
    """
    İçerik istatistikleri (admin için)
    """
    # Kategori dağılımı
    categories = {}
    for makale in makale_store.values():
        categories[makale.kategori] = categories.get(makale.kategori, 0) + 1
    for video in video_store.values():
        categories[video.kategori] = categories.get(video.kategori, 0) + 1

    # Toplam istatistikler
    total_views = sum(m.goruntuleme_sayisi for m in makale_store.values())
    total_views += sum(v.izlenme_sayisi for v in video_store.values())

    total_likes = sum(m.begeni_sayisi for m in makale_store.values())
    total_likes += sum(v.begeni_sayisi for v in video_store.values())

    return {
        "success": True,
        "data": {
            "content_counts": {
                "total_makale": len(makale_store),
                "total_video": len(video_store),
                "total_quiz": len(quiz_store),
                "total_content": len(makale_store) + len(video_store) + len(quiz_store),
            },
            "engagement": {
                "total_views": total_views,
                "total_likes": total_likes,
                "total_interactions": len(interaction_store),
            },
            "categories": categories,
            "active_content": {
                "active_makale": len([m for m in makale_store.values() if m.aktif]),
                "active_video": len([v for v in video_store.values() if v.aktif]),
            },
        },
    }


@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """
    İçerik API sağlık kontrolü
    """
    return {
        "status": "healthy",
        "service": "content_api",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "data_status": {
            "makale_count": len(makale_store),
            "video_count": len(video_store),
            "interaction_count": len(interaction_store),
        },
    }


# ==================== YARDIMCI FONKSİYONLAR ====================


async def generate_video_thumbnail(video_id: str, video_url: str):
    """
    Video thumbnail oluşturma (arka plan görevi)
    """
    # Gerçek uygulamada video işleme kütüphanesi kullanılacak
    # Şimdilik basit bir placeholder
    if video_id in video_store:
        # YouTube thumbnail URL'i oluştur
        if "youtube.com" in video_url or "youtu.be" in video_url:
            video = video_store[video_id]
            platform_id = video.extract_platform_id()
            if platform_id:
                thumbnail_url = (
                    f"https://img.youtube.com/vi/{platform_id}/maxresdefault.jpg"
                )
                video.thumbnail_url = thumbnail_url

        print(f"Thumbnail oluşturuldu: {video_id}")


# ==================== BULK IMPORT ENDPOINTLERİ ====================


@router.post("/bulk-import", response_model=Dict[str, Any])
async def start_bulk_import(
    file_data: Dict[str, Any], user_id: str, background_tasks: BackgroundTasks
):
    """
    Toplu içerik yükleme başlat
    """
    bulk_import = BulkContentImport(
        user_id=user_id,
        file_name=file_data.get("file_name", "unknown.csv"),
        file_type=file_data.get("file_type", "csv"),
        total_records=len(file_data.get("records", [])),
    )

    # Arka planda işleme başlat
    background_tasks.add_task(
        process_bulk_import, bulk_import.task_id, file_data.get("records", [])
    )

    return {
        "success": True,
        "data": bulk_import.dict(),
        "message": "Toplu yükleme başlatıldı",
    }


async def process_bulk_import(task_id: str, records: List[Dict[str, Any]]):
    """
    Toplu yükleme işleme (arka plan görevi)
    """
    # Gerçek uygulamada database'e kaydedilecek
    print(f"Toplu yükleme işleniyor: {task_id}")

    for i, record in enumerate(records):
        try:
            # Makale oluştur
            if record.get("type") == "makale":
                makale = MakaleIcerik(**record)
                makale_store[makale.id] = makale
            # Video oluştur
            elif record.get("type") == "video":
                video = VideoIcerik(**record)
                video_store[video.id] = video

            print(f"İşlendi: {i+1}/{len(records)}")

        except Exception as e:
            print(f"Hata: {record} - {str(e)}")

    print(f"Toplu yükleme tamamlandı: {task_id}")
