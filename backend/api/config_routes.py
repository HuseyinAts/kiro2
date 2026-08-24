"""
Configuration API Routes

Feature flag ve configuration bilgilerini expose eden API endpoint'leri.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.config_utils import get_config_for_user
from core.dependencies import (
    STUDENT_DATA_ACCESS_ROLES,
    AuthenticatedUser,
    get_current_user,
)
from core.feature_flags import (
    FeatureFlag,
    get_feature_flag_manager,
)

router = APIRouter(prefix="/api/v1/config", tags=["configuration"])


def _verify_user_access(current_user: AuthenticatedUser, user_id: str) -> None:
    """IDOR: user own config only, admin/teacher any."""
    if current_user.role in STUDENT_DATA_ACCESS_ROLES:
        return
    if str(current_user.id) != user_id:
        raise HTTPException(
            status_code=403,
            detail="Bu kullanici verisine erisim yetkiniz yok",
        )


class FeatureFlagResponse(BaseModel):
    """Feature flag response model"""

    flag: str
    enabled: bool
    description: str


class ConfigSummaryResponse(BaseModel):
    """Configuration summary response"""

    environment: str
    enabled_features: list
    disabled_features: list
    quality_thresholds: dict[str, Any]
    performance_config: dict[str, Any]
    active_ab_tests: list


class UserConfigResponse(BaseModel):
    """User-specific configuration response"""

    user_id: str
    quality_thresholds: dict[str, Any]
    performance_config: dict[str, Any]
    feature_flags: dict[str, bool]
    ab_test_variants: dict[str, Any]


@router.get("/summary", response_model=ConfigSummaryResponse)
async def get_config_summary(
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Sistem konfigürasyon özetini al

    Returns:
        - Environment bilgisi
        - Aktif/inaktif feature'lar
        - Quality threshold'lar
        - Performance config
        - Aktif A/B testler
    """
    manager = get_feature_flag_manager()
    summary = manager.get_config_summary()

    return ConfigSummaryResponse(**summary)


@router.get("/features", response_model=list[FeatureFlagResponse])
async def get_all_features(current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    Tüm feature flag'leri listele

    Returns:
        Feature flag listesi (name, enabled, description)
    """
    manager = get_feature_flag_manager()

    feature_descriptions = {
        FeatureFlag.SEMANTIC_SEARCH: "Embedding tabanlı semantik video arama",
        FeatureFlag.ADVANCED_SEARCH: "Gelişmiş filtreli video arama",
        FeatureFlag.HYBRID_SEARCH: "Semantic + Advanced search kombinasyonu",
        FeatureFlag.TURKISH_CONTENT_FILTER: "Türkçe içerik filtreleme",
        FeatureFlag.RELEVANCE_FILTER: "Konu alakalılık filtreleme",
        FeatureFlag.DIFFICULTY_FILTER: "Zorluk seviyesi filtreleme",
        FeatureFlag.MULTI_LAYER_CACHE: "Multi-layer (Memory + Redis) cache",
        FeatureFlag.CACHE_WARMING: "Cache ön yükleme",
        FeatureFlag.AGGRESSIVE_CACHING: "Agresif cache stratejisi",
        FeatureFlag.PARALLEL_DISCOVERY: "Paralel video discovery",
        FeatureFlag.CIRCUIT_BREAKER: "Circuit breaker pattern",
        FeatureFlag.RATE_LIMITING: "API rate limiting",
        FeatureFlag.QUALITY_SCORING: "Video kalite skorlama",
        FeatureFlag.TRUSTED_CHANNELS_BOOST: "Güvenilir kanallara bonus",
        FeatureFlag.DETAILED_LOGGING: "Detaylı log toplama",
        FeatureFlag.METRICS_COLLECTION: "Metrik toplama",
        FeatureFlag.AI_RELEVANCE_SCORING: "AI tabanlı alakalılık skorlama (Experimental)",
        FeatureFlag.PERSONALIZED_RANKING: "Kişiselleştirilmiş sıralama (Experimental)",
    }

    features = []
    for flag in FeatureFlag:
        features.append(
            FeatureFlagResponse(
                flag=flag.value,
                enabled=manager.is_enabled(flag),
                description=feature_descriptions.get(flag, ""),
            )
        )

    return features


@router.get("/features/{flag_name}")
async def get_feature_status(
    flag_name: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Belirli bir feature flag'in durumunu al

    Args:
        flag_name: Feature flag adı

    Returns:
        Feature flag durumu
    """
    try:
        flag = FeatureFlag(flag_name)
    except ValueError:
        raise HTTPException(
            status_code=404, detail=f"Feature flag '{flag_name}' bulunamadı"
        )

    manager = get_feature_flag_manager()

    return {"flag": flag.value, "enabled": manager.is_enabled(flag)}


@router.get("/quality-thresholds")
async def get_quality_thresholds(
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Quality threshold değerlerini al

    Returns:
        Quality threshold konfigürasyonu
    """
    manager = get_feature_flag_manager()
    thresholds = manager.get_quality_thresholds()

    return thresholds.to_dict()


@router.get("/performance")
async def get_performance_config(
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Performance konfigürasyonunu al

    Returns:
        Performance config
    """
    manager = get_feature_flag_manager()
    config = manager.get_performance_config()

    return config.to_dict()


@router.get("/ab-tests")
async def get_ab_tests(
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Aktif A/B testleri listele

    Returns:
        A/B test listesi
    """
    manager = get_feature_flag_manager()

    ab_tests = []
    for test_id, test in manager.ab_tests.items():
        if test.enabled:
            ab_tests.append(
                {
                    "test_id": test.test_id,
                    "name": test.name,
                    "description": test.description,
                    "variants": [
                        {
                            "name": v.name,
                            "description": v.description,
                            "traffic_percentage": v.traffic_percentage,
                        }
                        for v in test.variants
                    ],
                    "start_date": test.start_date.isoformat(),
                    "end_date": test.end_date.isoformat() if test.end_date else None,
                }
            )

    return ab_tests


@router.get("/user/{user_id}", response_model=UserConfigResponse)
async def get_user_config(
    user_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Kullanıcıya özel konfigürasyonu al (A/B test overrides dahil)

    Args:
        user_id: Kullanıcı ID

    Returns:
        Kullanıcıya özel tam konfigürasyon
    """
    _verify_user_access(current_user, user_id)
    config = get_config_for_user(user_id)

    return UserConfigResponse(user_id=user_id, **config)


@router.get("/ab-tests/{test_id}/variant/{user_id}")
async def get_user_ab_test_variant(
    test_id: str,
    user_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Kullanıcının A/B test varyantını al

    Args:
        test_id: A/B test ID
        user_id: Kullanıcı ID

    Returns:
        Kullanıcının atandığı variant
    """
    _verify_user_access(current_user, user_id)
    manager = get_feature_flag_manager()
    variant = manager.get_ab_test_variant(test_id, user_id)

    if not variant:
        raise HTTPException(
            status_code=404, detail=f"A/B test '{test_id}' bulunamadı veya aktif değil"
        )

    return {
        "test_id": test_id,
        "user_id": user_id,
        "variant_name": variant.name,
        "variant_description": variant.description,
        "config_overrides": variant.config_overrides,
    }


@router.get("/health")
async def config_health_check():
    """
    Configuration sistemi sağlık kontrolü

    Returns:
        Sağlık durumu
    """
    try:
        manager = get_feature_flag_manager()
        summary = manager.get_config_summary()

        return {
            "status": "healthy",
            "environment": summary["environment"],
            "features_loaded": len(summary["enabled_features"])
            + len(summary["disabled_features"]),
            "ab_tests_active": len(summary["active_ab_tests"]),
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
