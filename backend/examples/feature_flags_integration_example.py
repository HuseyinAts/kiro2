"""
Feature Flags Integration Example

Bu dosya, feature flag sisteminin video öneri servisinde
nasıl kullanılacağını gösterir.
"""

import asyncio

from backend.core.config_utils import (
    get_ab_test_variant,
    get_config_for_user,
    get_performance_config,
    get_quality_thresholds,
    is_feature_enabled,
)
from backend.core.feature_flags import FeatureFlag

# ============================================================================
# Örnek 1: Feature Flag ile Algoritma Seçimi
# ============================================================================


async def search_videos_with_feature_flags(query: str, user_id: str):
    """
    Feature flag'lere göre uygun arama algoritmasını seç
    """

    # Hybrid search aktif mi?
    if is_feature_enabled(FeatureFlag.HYBRID_SEARCH):
        print("Using hybrid search (semantic + advanced)")

        # Her iki algoritmayı paralel çalıştır
        semantic_results = await semantic_search(query)
        advanced_results = await advanced_search(query)

        # Sonuçları birleştir
        results = merge_results(semantic_results, advanced_results)

    # Sadece semantic search
    elif is_feature_enabled(FeatureFlag.SEMANTIC_SEARCH):
        print("Using semantic search only")
        results = await semantic_search(query)

    # Sadece advanced search
    elif is_feature_enabled(FeatureFlag.ADVANCED_SEARCH):
        print("Using advanced search only")
        results = await advanced_search(query)

    else:
        print("No search algorithm enabled, using fallback")
        results = await fallback_search(query)

    return results


# ============================================================================
# Örnek 2: Quality Thresholds ile Filtreleme
# ============================================================================


async def filter_videos_with_thresholds(videos: list[dict]):
    """
    Quality threshold'lara göre videoları filtrele
    """

    # Threshold'ları al
    thresholds = get_quality_thresholds()

    filtered_videos = []

    for video in videos:
        # Language score kontrolü
        if video["language_score"] < thresholds.min_language_score:
            print(f"Video {video['id']} failed language check")
            continue

        # Relevance score kontrolü
        if video["relevance_score"] < thresholds.min_relevance_score:
            print(f"Video {video['id']} failed relevance check")
            continue

        # Difficulty match kontrolü
        if video["difficulty_match"] < thresholds.min_difficulty_match:
            print(f"Video {video['id']} failed difficulty check")
            continue

        # Overall score hesapla
        overall_score = (
            video["language_score"] * thresholds.language_weight
            + video["relevance_score"] * thresholds.relevance_weight
            + video["difficulty_match"] * thresholds.difficulty_weight
        )

        if overall_score >= thresholds.min_overall_score:
            video["overall_score"] = overall_score
            filtered_videos.append(video)
        else:
            print(f"Video {video['id']} failed overall score check")

    return filtered_videos


# ============================================================================
# Örnek 3: Performance Config ile Cache Yönetimi
# ============================================================================


class VideoCache:
    """Video cache with configurable TTL"""

    def __init__(self):
        self.cache = {}
        self.config = get_performance_config()

    async def get(self, key: str):
        """Get from cache"""
        if key in self.cache:
            print(f"Cache hit for key: {key}")
            return self.cache[key]

        print(f"Cache miss for key: {key}")
        return None

    async def set(self, key: str, value: any):
        """Set to cache with configured TTL"""
        ttl = self.config.cache_ttl_seconds
        print(f"Caching key: {key} with TTL: {ttl}s")

        self.cache[key] = value

        # Schedule expiration (simplified)
        # In real implementation, use Redis with TTL
        await asyncio.sleep(ttl)
        if key in self.cache:
            del self.cache[key]
            print(f"Cache expired for key: {key}")


# ============================================================================
# Örnek 4: A/B Testing ile Algoritma Karşılaştırma
# ============================================================================


async def get_recommendations_with_ab_test(user_id: str, query: str):
    """
    A/B test varyantına göre farklı algoritma kullan
    """

    # A/B test varyantını al
    variant = get_ab_test_variant("relevance_scoring_v2", user_id)

    if variant:
        print(f"User {user_id} is in variant: {variant.name}")

        if variant.name == "treatment":
            # Yeni AI-based scoring kullan
            print("Using AI-based relevance scoring")
            results = await ai_relevance_scoring(query)
        else:
            # Mevcut algoritma kullan
            print("Using standard relevance scoring")
            results = await standard_relevance_scoring(query)

        # Variant bilgisini sonuçlara ekle
        for result in results:
            result["ab_test_variant"] = variant.name

    else:
        # A/B test aktif değil, default algoritma kullan
        print("No active A/B test, using default algorithm")
        results = await standard_relevance_scoring(query)

    return results


# ============================================================================
# Örnek 5: Kullanıcıya Özel Tam Konfigürasyon
# ============================================================================


async def get_personalized_recommendations(user_id: str, query: str):
    """
    Kullanıcıya özel konfigürasyonla öneri al
    """

    # Kullanıcıya özel tam config al (A/B test overrides dahil)
    config = get_config_for_user(user_id)

    print(f"User {user_id} configuration:")
    print(f"  - Feature flags: {config['feature_flags']}")
    print(f"  - A/B test variants: {config['ab_test_variants']}")

    # Config'e göre işlem yap
    if config["feature_flags"].get("ai_relevance_scoring"):
        print("Using AI relevance scoring for this user")
        results = await ai_relevance_scoring(query)
    else:
        print("Using standard relevance scoring for this user")
        results = await standard_relevance_scoring(query)

    # Quality thresholds uygula
    thresholds = config["quality_thresholds"]
    min_relevance = thresholds["relevance"]["min_score"]

    filtered_results = [r for r in results if r["relevance_score"] >= min_relevance]

    return filtered_results


# ============================================================================
# Örnek 6: Conditional Feature Execution
# ============================================================================


async def process_video_recommendations(videos: list[dict], user_id: str):
    """
    Feature flag'lere göre farklı işlemler uygula
    """

    # Turkish content filtering
    if is_feature_enabled(FeatureFlag.TURKISH_CONTENT_FILTER):
        print("Applying Turkish content filter")
        videos = await filter_turkish_content(videos)

    # Relevance filtering
    if is_feature_enabled(FeatureFlag.RELEVANCE_FILTER):
        print("Applying relevance filter")
        videos = await filter_by_relevance(videos)

    # Difficulty filtering
    if is_feature_enabled(FeatureFlag.DIFFICULTY_FILTER):
        print("Applying difficulty filter")
        videos = await filter_by_difficulty(videos)

    # Quality scoring
    if is_feature_enabled(FeatureFlag.QUALITY_SCORING):
        print("Calculating quality scores")
        videos = await calculate_quality_scores(videos)

    # Trusted channels boost
    if is_feature_enabled(FeatureFlag.TRUSTED_CHANNELS_BOOST):
        print("Boosting trusted channels")
        videos = await boost_trusted_channels(videos)

    # Personalized ranking (experimental)
    if is_feature_enabled(FeatureFlag.PERSONALIZED_RANKING):
        print("Applying personalized ranking")
        videos = await personalize_ranking(videos, user_id)

    return videos


# ============================================================================
# Örnek 7: Parallel Processing with Config
# ============================================================================


async def parallel_video_discovery(subjects: list[str]):
    """
    Performance config'e göre paralel arama yap
    """

    config = get_performance_config()
    max_parallel = config.max_parallel_searches
    timeout = config.search_timeout_seconds

    print(f"Running parallel discovery with max={max_parallel}, timeout={timeout}s")

    # Batch'lere böl
    batches = [
        subjects[i : i + max_parallel] for i in range(0, len(subjects), max_parallel)
    ]

    all_results = []

    for batch in batches:
        # Batch içindeki aramaları paralel çalıştır
        tasks = [
            asyncio.wait_for(search_videos(subject), timeout=timeout)
            for subject in batch
        ]

        try:
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Hataları filtrele
            valid_results = [r for r in batch_results if not isinstance(r, Exception)]

            all_results.extend(valid_results)

        except TimeoutError:
            print(f"Batch timed out after {timeout}s")

    return all_results


# ============================================================================
# Örnek 8: Circuit Breaker with Feature Flag
# ============================================================================


class CircuitBreakerWrapper:
    """Circuit breaker with feature flag control"""

    def __init__(self):
        self.failure_count = 0
        self.is_open = False

    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker if enabled"""

        if not is_feature_enabled(FeatureFlag.CIRCUIT_BREAKER):
            # Circuit breaker disabled, direct call
            return await func(*args, **kwargs)

        # Circuit breaker enabled
        config = get_performance_config()
        threshold = config.circuit_breaker_failure_threshold

        if self.is_open:
            print("Circuit breaker is OPEN, rejecting request")
            raise Exception("Circuit breaker open")

        try:
            result = await func(*args, **kwargs)

            # Success, reset failure count
            self.failure_count = 0

            return result

        except Exception as e:
            self.failure_count += 1
            print(f"Circuit breaker failure count: {self.failure_count}")

            if self.failure_count >= threshold:
                self.is_open = True
                print("Circuit breaker OPENED")

            raise e


# ============================================================================
# Mock Functions (for demonstration)
# ============================================================================


async def semantic_search(query: str):
    """Mock semantic search"""
    await asyncio.sleep(0.1)
    return [{"id": 1, "title": "Semantic result", "score": 0.9}]


async def advanced_search(query: str):
    """Mock advanced search"""
    await asyncio.sleep(0.1)
    return [{"id": 2, "title": "Advanced result", "score": 0.8}]


async def fallback_search(query: str):
    """Mock fallback search"""
    return [{"id": 3, "title": "Fallback result", "score": 0.5}]


def merge_results(results1, results2):
    """Mock merge results"""
    return results1 + results2


async def ai_relevance_scoring(query: str):
    """Mock AI scoring"""
    await asyncio.sleep(0.1)
    return [{"id": 4, "title": "AI result", "relevance_score": 0.95}]


async def standard_relevance_scoring(query: str):
    """Mock standard scoring"""
    await asyncio.sleep(0.1)
    return [{"id": 5, "title": "Standard result", "relevance_score": 0.85}]


async def filter_turkish_content(videos):
    """Mock Turkish filter"""
    return videos


async def filter_by_relevance(videos):
    """Mock relevance filter"""
    return videos


async def filter_by_difficulty(videos):
    """Mock difficulty filter"""
    return videos


async def calculate_quality_scores(videos):
    """Mock quality scoring"""
    return videos


async def boost_trusted_channels(videos):
    """Mock channel boost"""
    return videos


async def personalize_ranking(videos, user_id):
    """Mock personalized ranking"""
    return videos


async def search_videos(subject: str):
    """Mock video search"""
    await asyncio.sleep(0.1)
    return [{"subject": subject, "videos": []}]


# ============================================================================
# Main Demo
# ============================================================================


async def main():
    """Run examples"""

    print("=" * 60)
    print("Feature Flags Integration Examples")
    print("=" * 60)

    # Example 1
    print("\n1. Feature Flag ile Algoritma Seçimi:")
    results = await search_videos_with_feature_flags("matematik", "user_123")
    print(f"Results: {len(results)} videos")

    # Example 2
    print("\n2. Quality Thresholds ile Filtreleme:")
    test_videos = [
        {
            "id": 1,
            "language_score": 0.9,
            "relevance_score": 0.8,
            "difficulty_match": 0.7,
        },
        {
            "id": 2,
            "language_score": 0.6,  # Too low
            "relevance_score": 0.8,
            "difficulty_match": 0.7,
        },
    ]
    filtered = await filter_videos_with_thresholds(test_videos)
    print(f"Filtered: {len(filtered)} videos passed")

    # Example 4
    print("\n4. A/B Testing ile Algoritma Karşılaştırma:")
    results = await get_recommendations_with_ab_test("user_123", "fizik")
    print(f"Results: {len(results)} videos")

    # Example 5
    print("\n5. Kullanıcıya Özel Konfigürasyon:")
    results = await get_personalized_recommendations("user_456", "kimya")
    print(f"Results: {len(results)} videos")

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
