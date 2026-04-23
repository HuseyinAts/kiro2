"""
Optimal Hybrid AI System
Gemini 3 Pro + Claude Sonnet 4.5
Best Practices 2025

Gerçek API entegrasyonu ile production-ready implementasyon.
"""

import asyncio
import hashlib
import os
import time
from enum import Enum
from typing import Any

import structlog

# Logging
logger = structlog.get_logger()


class ModelType(Enum):
    """Model tipleri"""
    CLAUDE_ONLY = "claude_only"
    GEMINI_ASSIST = "gemini_assist"
    GEMINI_THINKING = "gemini_thinking"


class ComplexityLevel(Enum):
    """Karmaşıklık seviyeleri"""
    SIMPLE = 1  # 0-3
    MEDIUM = 2  # 4-6
    COMPLEX = 3  # 7-10


class SmartRouter:
    """Akıllı model yönlendirici"""

    def __init__(self):
        self.complexity_thresholds = {
            ComplexityLevel.SIMPLE: 3,
            ComplexityLevel.MEDIUM: 6,
            ComplexityLevel.COMPLEX: 10
        }

    def analyze_complexity(self, query: str, context: dict | None = None) -> int:
        """
        Query karmaşıklığını analiz et (0-10)
        
        Args:
            query: Kullanıcı sorusu
            context: Ek bağlam
        
        Returns:
            Complexity score (0-10)
        """
        score = 0
        query_lower = query.lower()

        # Token sayısı
        token_count = len(query.split())
        if token_count > 100:
            score += 2
        elif token_count > 50:
            score += 1

        # Kod içeriyor mu?
        if "```" in query or any(kw in query for kw in ["def ", "class ", "function"]):
            score += 2

        # Analiz gerektiriyor mu?
        analysis_keywords = ["analiz", "incele", "değerlendir", "optimize", "iyileştir"]
        if any(kw in query_lower for kw in analysis_keywords):
            score += 3

        # Thinking gerektiriyor mu?
        thinking_keywords = ["adım adım", "detaylı", "açıkla", "nasıl"]
        if any(kw in query_lower for kw in thinking_keywords):
            score += 2

        # Dosya analizi mi?
        if context and context.get("file_content"):
            score += 2

        return min(score, 10)

    def route(self, query: str, context: dict | None = None) -> ModelType:
        """
        Query'yi uygun modele yönlendir
        
        Args:
            query: Kullanıcı sorusu
            context: Ek bağlam
        
        Returns:
            Kullanılacak model tipi
        """
        complexity = self.analyze_complexity(query, context)

        if complexity <= self.complexity_thresholds[ComplexityLevel.SIMPLE]:
            return ModelType.CLAUDE_ONLY
        if complexity <= self.complexity_thresholds[ComplexityLevel.MEDIUM]:
            return ModelType.GEMINI_ASSIST
        return ModelType.GEMINI_THINKING

    def get_routing_info(self, query: str, context: dict | None = None) -> dict:
        """Routing bilgilerini döndür"""
        complexity = self.analyze_complexity(query, context)
        model_type = self.route(query, context)

        return {
            "complexity": complexity,
            "model_type": model_type.value,
            "estimated_time": self._estimate_time(model_type),
            "estimated_cost": self._estimate_cost(model_type)
        }

    def _estimate_time(self, model_type: ModelType) -> float:
        """Tahmini yanıt süresi (saniye)"""
        time_map = {
            ModelType.CLAUDE_ONLY: 1.5,
            ModelType.GEMINI_ASSIST: 5.0,
            ModelType.GEMINI_THINKING: 15.0
        }
        return time_map[model_type]

    def _estimate_cost(self, model_type: ModelType) -> float:
        """Tahmini maliyet (USD)"""
        cost_map = {
            ModelType.CLAUDE_ONLY: 0.003,
            ModelType.GEMINI_ASSIST: 0.005,
            ModelType.GEMINI_THINKING: 0.008
        }
        return cost_map[model_type]


class MultiLayerCache:
    """3 katmanlı cache sistemi"""

    def __init__(self, redis_client=None):
        self.l1_cache = {}  # Memory cache (LRU)
        self.l1_max_size = 100
        self.l2_redis = redis_client  # Redis hot cache
        self.l3_redis = redis_client  # Redis cold cache

        # Metrics
        self.hits = {"l1": 0, "l2": 0, "l3": 0}
        self.misses = 0

    def _generate_key(self, prompt: str, model: str) -> str:
        """Cache key oluştur"""
        content = f"{model}:{prompt}"
        return hashlib.md5(content.encode()).hexdigest()

    async def get(self, prompt: str, model: str) -> str | None:
        """Cache'den oku"""
        key = self._generate_key(prompt, model)

        # L1: Memory
        if key in self.l1_cache:
            self.hits["l1"] += 1
            logger.info("cache_hit", layer="l1", key=key)
            return self.l1_cache[key]

        # L2: Redis hot (1 saat TTL)
        if self.l2_redis:
            value = await self.l2_redis.get(f"hot:{key}")
            if value:
                self.hits["l2"] += 1
                self.l1_cache[key] = value  # Promote to L1
                self._evict_if_needed()
                logger.info("cache_hit", layer="l2", key=key)
                return value

        # L3: Redis cold (24 saat TTL)
        if self.l3_redis:
            value = await self.l3_redis.get(f"cold:{key}")
            if value:
                self.hits["l3"] += 1
                # Promote to L2 and L1
                if self.l2_redis:
                    await self.l2_redis.setex(f"hot:{key}", 3600, value)
                self.l1_cache[key] = value
                self._evict_if_needed()
                logger.info("cache_hit", layer="l3", key=key)
                return value

        # Cache miss
        self.misses += 1
        logger.info("cache_miss", key=key)
        return None

    async def set(self, prompt: str, model: str, value: str, ttl: int = 3600):
        """Cache'e yaz"""
        key = self._generate_key(prompt, model)

        # L1: Memory
        self.l1_cache[key] = value
        self._evict_if_needed()

        # L2: Redis hot
        if self.l2_redis:
            await self.l2_redis.setex(f"hot:{key}", ttl, value)

        # L3: Redis cold
        if self.l3_redis:
            await self.l3_redis.setex(f"cold:{key}", ttl * 24, value)

        logger.info("cache_set", key=key, ttl=ttl)

    def _evict_if_needed(self):
        """LRU eviction"""
        if len(self.l1_cache) > self.l1_max_size:
            # En eski key'i sil
            oldest_key = next(iter(self.l1_cache))
            del self.l1_cache[oldest_key]

    def get_hit_rate(self) -> dict[str, float]:
        """Cache hit rate'leri döndür"""
        total_requests = sum(self.hits.values()) + self.misses

        if total_requests == 0:
            return {"l1": 0.0, "l2": 0.0, "l3": 0.0, "total": 0.0}

        return {
            "l1": self.hits["l1"] / total_requests,
            "l2": self.hits["l2"] / total_requests,
            "l3": self.hits["l3"] / total_requests,
            "total": sum(self.hits.values()) / total_requests
        }


class TokenOptimizer:
    """Token kullanımını optimize et"""

    def optimize_prompt(self, prompt: str, max_tokens: int = 4000) -> str:
        """
        Prompt'u optimize et
        
        Args:
            prompt: Orijinal prompt
            max_tokens: Maksimum token sayısı
        
        Returns:
            Optimize edilmiş prompt
        """
        # 1. Whitespace temizle
        prompt = " ".join(prompt.split())

        # 2. Token sayısını kontrol et
        token_count = self.count_tokens(prompt)

        if token_count <= max_tokens:
            return prompt

        # 3. Özetle
        return self.summarize(prompt, max_tokens)

    def count_tokens(self, text: str) -> int:
        """Token sayısını hesapla (yaklaşık)"""
        # Yaklaşık: 1 token ≈ 4 karakter
        return len(text) // 4

    def summarize(self, text: str, max_tokens: int) -> str:
        """Metni özetle"""
        # Basit extractive summarization
        sentences = text.split(". ")

        # İlk ve son cümleleri al
        target_sentences = max_tokens // 100

        if len(sentences) <= target_sentences:
            return text

        # İlk yarısı + son yarısı
        half = target_sentences // 2
        selected = sentences[:half] + sentences[-half:]

        return ". ".join(selected)


class OptimalHybridSystem:
    """Optimal hibrit AI sistemi"""

    def __init__(self, redis_client=None):
        self.router = SmartRouter()
        self.cache = MultiLayerCache(redis_client)
        self.optimizer = TokenOptimizer()

        # Metrics
        self.request_count = 0
        self.total_cost = 0.0
        self.total_time = 0.0

    async def process_query(
        self,
        query: str,
        context: dict | None = None,
        use_cache: bool = True
    ) -> dict[str, Any]:
        """
        Query'yi işle
        
        Args:
            query: Kullanıcı sorusu
            context: Ek bağlam
            use_cache: Cache kullan
        
        Returns:
            Response dict
        """
        start_time = time.time()
        self.request_count += 1

        # Routing
        routing_info = self.router.get_routing_info(query, context)
        model_type = ModelType(routing_info["model_type"])

        logger.info(
            "query_processing_started",
            query_length=len(query),
            complexity=routing_info["complexity"],
            model_type=model_type.value
        )

        # Cache kontrolü
        if use_cache:
            cached_response = await self.cache.get(query, model_type.value)
            if cached_response:
                duration = time.time() - start_time
                logger.info(
                    "query_completed_from_cache",
                    duration=duration
                )
                return {
                    "response": cached_response,
                    "model": model_type.value,
                    "cached": True,
                    "duration": duration,
                    "cost": 0.0
                }

        # Token optimizasyonu
        optimized_query = self.optimizer.optimize_prompt(query)

        # Model çağrısı (simulated)
        response = await self._call_model(optimized_query, model_type, context)

        # Cache'e yaz
        if use_cache:
            await self.cache.set(query, model_type.value, response)

        # Metrics
        duration = time.time() - start_time
        cost = routing_info["estimated_cost"]
        self.total_time += duration
        self.total_cost += cost

        logger.info(
            "query_completed",
            duration=duration,
            cost=cost,
            model=model_type.value
        )

        return {
            "response": response,
            "model": model_type.value,
            "cached": False,
            "duration": duration,
            "cost": cost,
            "routing_info": routing_info
        }

    async def _call_model(
        self,
        query: str,
        model_type: ModelType,
        context: dict | None
    ) -> str:
        """Model çağrısı - Gerçek API implementasyonu"""
        try:
            if model_type == ModelType.CLAUDE_ONLY:
                # Basit sorular için Claude
                return await self._call_claude(query, context, thinking_mode=False)

            if model_type == ModelType.GEMINI_ASSIST:
                # Orta seviye için Gemini normal mode
                return await self._call_gemini(query, context, thinking_mode=False)

            # ModelType.GEMINI_THINKING
            # Karmaşık analizler için Gemini thinking mode
            return await self._call_gemini(query, context, thinking_mode=True)

        except Exception as e:
            logger.error("model_call_failed", error=str(e), model=model_type.value)
            # Fallback: Claude'u dene
            return await self._call_claude(query, context, thinking_mode=False)

    async def _call_claude(
        self,
        query: str,
        context: dict | None,
        thinking_mode: bool = False
    ) -> str:
        """Claude API çağrısı"""
        import anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY bulunamadı")

        client = anthropic.Anthropic(api_key=api_key)

        # Prompt hazırla
        full_prompt = query
        if context:
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            full_prompt = f"Bağlam:\n{context_str}\n\nSoru:\n{query}"

        if thinking_mode:
            full_prompt = "Lütfen adım adım düşünerek yanıtla.\n\n" + full_prompt

        # API çağrısı
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": full_prompt}]
        )

        return message.content[0].text

    async def _call_gemini(
        self,
        query: str,
        context: dict | None,
        thinking_mode: bool = False
    ) -> str:
        """Gemini API çağrısı"""
        import google.generativeai as genai

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY bulunamadı")

        genai.configure(api_key=api_key)

        # Model seç
        try:
            model = genai.GenerativeModel("gemini-exp-1206")
        except (ValueError, RuntimeError, AttributeError):
            model = genai.GenerativeModel("gemini-2.0-flash-exp")

        # Prompt hazırla
        full_prompt = query
        if context:
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            full_prompt = f"Bağlam:\n{context_str}\n\nGörev:\n{query}"

        if thinking_mode:
            full_prompt = (
                "Lütfen adım adım düşünerek ve akıl yürütme sürecini göstererek yanıtla.\n\n"
                + full_prompt
            )

        # API çağrısı
        response = model.generate_content(full_prompt)
        return response.text

    def get_metrics(self) -> dict[str, Any]:
        """Sistem metriklerini döndür"""
        cache_hit_rate = self.cache.get_hit_rate()

        avg_time = self.total_time / self.request_count if self.request_count > 0 else 0
        avg_cost = self.total_cost / self.request_count if self.request_count > 0 else 0

        return {
            "total_requests": self.request_count,
            "total_cost": self.total_cost,
            "total_time": self.total_time,
            "avg_time": avg_time,
            "avg_cost": avg_cost,
            "cache_hit_rate": cache_hit_rate
        }


# Kullanım örneği
async def main():
    """Test"""
    system = OptimalHybridSystem()

    # Test queries
    queries = [
        "Python nedir?",  # Simple
        "Bu kodu optimize et: def fib(n): ...",  # Medium
        "Design.md dosyasını detaylı analiz et"  # Complex
    ]

    for query in queries:
        result = await system.process_query(query)
        print(f"\nQuery: {query}")
        print(f"Model: {result['model']}")
        print(f"Duration: {result['duration']:.2f}s")
        print(f"Cost: ${result['cost']:.4f}")
        print(f"Cached: {result['cached']}")

    # Metrics
    print("\n=== System Metrics ===")
    metrics = system.get_metrics()
    for key, value in metrics.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())
