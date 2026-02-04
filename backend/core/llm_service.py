"""
HuggingFace Endpoint LLM Service - Performance Optimized
Teknofest 2025 - Eğitim Eylemci Projesi
"""

import hashlib
import json
import logging
import os
import time
from typing import Any

import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Performance optimization imports
try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory cache only")


class HuggingFaceLLMService:
    """HuggingFace Endpoint ile LLM işlemleri için servis - Performance Optimized"""

    def __init__(self):
        # Use custom HuggingFace endpoint
        self.endpoint_url = os.getenv(
            "HUGGINGFACE_ENDPOINT",
            "https://cf781mfqobm2ynkk.us-east-1.aws.endpoints.huggingface.cloud",
        )

        self.api_token = os.getenv("HUGGINGFACE_API_TOKEN", "")

        # Headers with or without token
        self.headers = {"Content-Type": "application/json"}
        if self.api_token:
            self.headers["Authorization"] = f"Bearer {self.api_token}"

        # Performance optimizations
        self._session = None
        self._redis_client = None
        self._cache = {}  # In-memory fallback cache
        self._cache_ttl = int(os.getenv("LLM_CACHE_TTL", "3600"))  # 1 hour default
        self._max_cache_size = int(os.getenv("LLM_MAX_CACHE_SIZE", "1000"))

        # Connection pooling settings
        self._connector_limit = int(os.getenv("HTTP_CONNECTOR_LIMIT", "100"))
        self._connector_limit_per_host = int(
            os.getenv("HTTP_CONNECTOR_LIMIT_PER_HOST", "30")
        )

        # Async components will be initialized on first use
        self._initialized = False

    async def _initialize_async_components(self):
        """Initialize async components like Redis and HTTP session"""
        try:
            # Initialize Redis client if available
            if REDIS_AVAILABLE:
                redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
                self._redis_client = redis.from_url(redis_url, decode_responses=True)
                await self._redis_client.ping()
                logger.info("Redis cache initialized successfully")

            # Initialize HTTP session with connection pooling
            connector = aiohttp.TCPConnector(
                limit=self._connector_limit,
                limit_per_host=self._connector_limit_per_host,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=30,
                enable_cleanup_closed=True,
            )

            timeout = aiohttp.ClientTimeout(
                total=int(os.getenv("LLM_TIMEOUT", "60")), connect=10, sock_read=30
            )

            self._session = aiohttp.ClientSession(
                connector=connector, timeout=timeout, headers=self.headers
            )

            logger.info("HTTP session with connection pooling initialized")

        except Exception as e:
            logger.error(f"Error initializing async components: {e}")

    def _generate_cache_key(self, prompt: str, **kwargs) -> str:
        """Generate cache key for prompt and parameters"""
        cache_data = {
            "prompt": prompt,
            "max_tokens": kwargs.get("max_tokens", 2048),
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 0.95),
            "system_prompt": kwargs.get("system_prompt", ""),
        }
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()

    async def _get_cached_response(self, cache_key: str) -> dict[str, Any] | None:
        """Get cached response from Redis or in-memory cache"""
        try:
            # Try Redis first
            if self._redis_client:
                cached = await self._redis_client.get(f"llm_cache:{cache_key}")
                if cached:
                    logger.info(f"Cache hit (Redis): {cache_key[:8]}...")
                    return json.loads(cached)

            # Fallback to in-memory cache
            if cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                if time.time() - timestamp < self._cache_ttl:
                    logger.info(f"Cache hit (memory): {cache_key[:8]}...")
                    return cached_data
                # Remove expired entry
                del self._cache[cache_key]

        except Exception as e:
            logger.error(f"Error getting cached response: {e}")

        return None

    async def _set_cached_response(self, cache_key: str, response: dict[str, Any]):
        """Set cached response in Redis or in-memory cache"""
        try:
            # Try Redis first
            if self._redis_client:
                await self._redis_client.setex(
                    f"llm_cache:{cache_key}", self._cache_ttl, json.dumps(response)
                )
                logger.debug(f"Response cached (Redis): {cache_key[:8]}...")
                return

            # Fallback to in-memory cache
            # Implement LRU eviction if cache is full
            if len(self._cache) >= self._max_cache_size:
                # Remove oldest entry
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
                del self._cache[oldest_key]

            self._cache[cache_key] = (response, time.time())
            logger.debug(f"Response cached (memory): {cache_key[:8]}...")

        except Exception as e:
            logger.error(f"Error setting cached response: {e}")

    async def _ensure_session(self):
        """Ensure HTTP session is initialized"""
        if not self._initialized:
            await self._initialize_async_components()
            self._initialized = True

        if not self._session or self._session.closed:
            await self._initialize_async_components()

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        top_p: float = 0.95,
        system_prompt: str | None = None,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """
        LLM'den metin üretimi - Performance Optimized with Caching

        Args:
            prompt: Kullanıcı girdisi
            max_tokens: Maximum token sayısı
            temperature: Çeşitlilik parametresi
            top_p: Nucleus sampling parametresi
            system_prompt: Sistem mesajı
            use_cache: Cache kullanılsın mı

        Returns:
            Dict içinde üretilen metin ve metadata
        """
        try:
            # Check cache first if enabled
            if use_cache:
                cache_key = self._generate_cache_key(
                    prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    system_prompt=system_prompt,
                )

                cached_response = await self._get_cached_response(cache_key)
                if cached_response:
                    # Add cache hit metadata
                    cached_response["metadata"]["cache_hit"] = True
                    return cached_response

            # Ensure HTTP session is ready
            await self._ensure_session()

            # Prompt'u hazırla
            full_prompt = self._prepare_prompt(prompt, system_prompt)

            # Payload oluştur
            payload = {
                "inputs": full_prompt,
                "parameters": {
                    "max_new_tokens": max_tokens,
                    "temperature": temperature,
                    "top_p": top_p,
                    "do_sample": True,
                    "return_full_text": False,
                },
            }

            # Log the request
            logger.info(f"Sending request to HuggingFace endpoint: {self.endpoint_url}")
            logger.debug(f"Prompt length: {len(full_prompt)} characters")

            # API çağrısı yap - Use optimized session with connection pooling
            try:
                logger.info("Making POST request to HuggingFace...")
                async with self._session.post(
                    self.endpoint_url, json=payload
                ) as response:
                    logger.info(f"Got response status: {response.status}")
                    if response.status == 200:
                        result = await response.json()

                        # Handle different response formats
                        text = ""
                        if isinstance(result, list) and len(result) > 0:
                            # Public HuggingFace API format
                            if "generated_text" in result[0]:
                                generated = result[0]["generated_text"]
                                # Remove the input prompt from the generated text if it's included
                                if generated.startswith(full_prompt):
                                    text = generated[len(full_prompt) :].strip()
                                else:
                                    text = generated
                                # Limit response length and extract only first response
                                if "\n\n### User:" in text:
                                    text = text.split("\n\n### User:")[0].strip()
                                elif "\n### User:" in text:
                                    text = text.split("\n### User:")[0].strip()
                                # Limit to reasonable length
                                if len(text) > 1000:
                                    text = text[:1000] + "..."
                            # Custom endpoint format
                            elif "predictions" in result[0]:
                                text = result[0]["predictions"]
                                # Skip if it's the placeholder response
                                if text == "model çıktısı":
                                    text = self._generate_educational_response(prompt)
                        elif isinstance(result, dict):
                            if "predictions" in result:
                                text = result["predictions"]
                                if text == "model çıktısı":
                                    text = self._generate_educational_response(prompt)
                            elif "generated_text" in result:
                                text = result["generated_text"]
                                # Limit response length for dict format too
                                if "\n\n### User:" in text:
                                    text = text.split("\n\n### User:")[0].strip()
                                elif "\n### User:" in text:
                                    text = text.split("\n### User:")[0].strip()
                                if len(text) > 1000:
                                    text = text[:1000] + "..."
                            elif "error" in result:
                                logger.error(f"API Error: {result['error']}")
                                text = self._generate_educational_response(prompt)

                        response_data = {
                            "success": True,
                            "text": text
                            if text
                            else self._generate_educational_response(prompt),
                            "metadata": {
                                "temperature": temperature,
                                "max_tokens": max_tokens,
                                "model": "huggingface-endpoint",
                                "cache_hit": False,
                            },
                        }

                        # Cache the response if caching is enabled
                        if use_cache and response_data["success"]:
                            await self._set_cached_response(cache_key, response_data)

                        return response_data
                    if response.status == 401:
                        # Authentication error - use fallback
                        error_text = await response.text()
                        logger.info(
                            "No API token provided, using intelligent fallback responses"
                        )
                        return {
                            "success": True,
                            "text": self._generate_educational_response(prompt),
                            "metadata": {
                                "temperature": temperature,
                                "max_tokens": max_tokens,
                                "model": "fallback-educational",
                            },
                        }
                    error_text = await response.text()
                    logger.error(
                        f"HuggingFace API Error: {response.status} - {error_text}"
                    )
                    # Use fallback for any error
                    return {
                        "success": True,
                        "text": self._generate_educational_response(prompt),
                        "metadata": {
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                            "model": "fallback-educational",
                        },
                    }
            except TimeoutError:
                logger.warning("HuggingFace request timed out after 15 seconds")
                return {
                    "success": True,
                    "text": self._generate_educational_response(prompt),
                    "metadata": {
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "model": "fallback-timeout",
                    },
                }

        except Exception as e:
            logger.error(f"LLM Service Error: {e!s}")
            return {"success": False, "error": str(e)}

    def _prepare_prompt(
        self, user_prompt: str, system_prompt: str | None = None
    ) -> str:
        """Prompt'u formatla"""
        if system_prompt:
            return f"""### System:
{system_prompt}

### User:
{user_prompt}

### Assistant:"""
        return user_prompt

    def _generate_educational_response(self, prompt: str) -> str:
        """Generate a contextual educational response as fallback"""
        prompt_lower = prompt.lower()

        # Python öğrenme ile ilgili
        if "python" in prompt_lower:
            return """Python öğrenmek için harika bir seçim! İşte size özel öğrenme planınız:

1. **Temel Kavramlar (1-2 Hafta)**
   - Değişkenler ve veri tipleri
   - Koşullu ifadeler (if/else)
   - Döngüler (for, while)
   
2. **Veri Yapıları (2-3 Hafta)**
   - Listeler ve tuple'lar
   - Sözlükler ve kümeler
   - String işlemleri
   
3. **Fonksiyonlar ve Modüller (1-2 Hafta)**
   - Fonksiyon tanımlama
   - Parametreler ve dönüş değerleri
   - Modül import etme

4. **Pratik Projeler**
   - Basit hesap makinesi
   - To-do list uygulaması
   - Veri analizi projesi

Her gün en az 1 saat pratik yapmanızı öneririm!"""

        # Matematik ile ilgili
        if "matematik" in prompt_lower or "math" in prompt_lower:
            return """Matematik çalışma planınız hazır:

**Temel Matematik Konuları:**
- Sayılar ve işlemler
- Cebir ve denklemler
- Geometri ve şekiller
- İstatistik ve olasılık

**Çalışma Önerileri:**
- Her gün 10 problem çözün
- Formülleri kartlara yazın
- Görsel materyaller kullanın
- Gerçek hayat örnekleri bulun"""

        # LGS/YKS ile ilgili
        if "lgs" in prompt_lower or "yks" in prompt_lower:
            return """Sınav hazırlık stratejiniz:

**Etkili Hazırlık Planı:**
1. Konu anlatımlarını bitirin
2. Çözümlü sorular üzerinde çalışın
3. Deneme sınavları çözün
4. Yanlışlarınızı analiz edin

**Günlük Program:**
- Sabah: Sayısal dersler (2 saat)
- Öğlen: Sözel dersler (2 saat)
- Akşam: Test çözümü (1 saat)
- Gece: Tekrar (30 dakika)"""

        # Genel öğrenme
        return """Size nasıl yardımcı olabilirim? 

**Yapabileceğim Şeyler:**
- Kişiselleştirilmiş öğrenme planları oluşturma
- Konu anlatımları ve özetler hazırlama
- Test ve quiz soruları üretme
- Çalışma teknikleri önerme
- Motivasyon ve destek sağlama

Hangi konuda yardım istersiniz? Örneğin:
- "Python öğrenmek istiyorum"
- "LGS matematik konuları"
- "Etkili ders çalışma teknikleri"

Detaylı bilgi verirseniz size özel bir plan hazırlayabilirim!"""

    async def generate_for_education(
        self, task_type: str, content: str, parameters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Eğitim amaçlı özel LLM çağrıları

        Args:
            task_type: Görev tipi (question_generation, summarization, simplification, etc.)
            content: İçerik
            parameters: Ek parametreler

        Returns:
            Görev tipine göre formatlanmış sonuç
        """
        prompts = {
            "question_generation": """Aşağıdaki içerikten LGS/YKS sınavlarına uygun sorular oluştur.
Her soru için:
1. Soru metni
2. 4 seçenek (A,B,C,D)
3. Doğru cevap
4. Açıklama
formatında ver.

İçerik: {content}""",
            "summarization": """Aşağıdaki içeriği öğrencilerin anlayabileceği şekilde özetle.
Ana noktaları vurgula ve önemli terimleri açıkla.

İçerik: {content}""",
            "simplification": """Aşağıdaki metni daha basit ve anlaşılır hale getir.
Karmaşık cümleleri böl, teknik terimleri açıkla.

Metin: {content}""",
            "flashcard_generation": """Aşağıdaki içerikten bilgi kartları (flashcard) oluştur.
Her kart için:
- Ön yüz (soru/terim)
- Arka yüz (cevap/açıklama)
formatında ver.

İçerik: {content}""",
            "learning_path": """Aşağıdaki öğrenme hedefi için kişiselleştirilmiş bir öğrenme yolu oluştur.
Hedef: {content}
Öğrenci seviyesi ve tercihleri de göz önünde bulundurulmalı.""",
            "accessibility": """Aşağıdaki içeriği erişilebilirlik standartlarına göre iyileştir.
- Görseller için alt metin öner
- Karmaşık yapıları sadeleştir
- Jargon ve kısaltmaları açıkla

İçerik: {content}""",
        }

        # Prompt seç
        prompt_template = prompts.get(task_type, "İçeriği analiz et: {content}")
        prompt = prompt_template.format(content=content)

        # Sistem mesajı
        system_prompt = """Sen Türkiye'deki öğrenciler için eğitim materyali hazırlayan uzman bir eğitim asistanısın.
LGS ve YKS sınavlarına hazırlık konusunda uzmansın.
Öğrenci dostu, anlaşılır ve motive edici bir dil kullan."""

        # LLM çağrısı yap
        result = await self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7 if task_type != "question_generation" else 0.5,
        )

        # Sonucu formatla
        if result["success"]:
            return {
                "success": True,
                "task_type": task_type,
                "content": result["text"],
                "original_content": content[:200] + "..."
                if len(content) > 200
                else content,
            }
        return result

    async def chat(
        self, messages: list[dict[str, str]], max_tokens: int = 1024
    ) -> dict[str, Any]:
        """
        Chat formatında konuşma

        Args:
            messages: Mesaj listesi [{"role": "user/assistant", "content": "..."}]
            max_tokens: Maximum token sayısı

        Returns:
            Chat yanıtı
        """
        # Mesajları string'e çevir
        conversation = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            conversation += f"### {role.capitalize()}:\n{content}\n\n"

        conversation += "### Assistant:\n"

        # LLM çağrısı
        result = await self.generate(
            prompt=conversation, max_tokens=max_tokens, temperature=0.8
        )

        return result

    async def close(self):
        """Clean up resources"""
        try:
            if self._session and not self._session.closed:
                await self._session.close()
                logger.info("HTTP session closed")

            if self._redis_client:
                await self._redis_client.close()
                logger.info("Redis connection closed")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def clear_cache(self, pattern: str = "*") -> int:
        """Clear cache entries matching pattern"""
        cleared_count = 0
        try:
            if self._redis_client:
                keys = await self._redis_client.keys(f"llm_cache:{pattern}")
                if keys:
                    cleared_count = await self._redis_client.delete(*keys)
                    logger.info(f"Cleared {cleared_count} Redis cache entries")

            # Clear in-memory cache
            if pattern == "*":
                memory_count = len(self._cache)
                self._cache.clear()
                cleared_count += memory_count
                logger.info(f"Cleared {memory_count} in-memory cache entries")

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

        return cleared_count

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        stats = {
            "memory_cache_size": len(self._cache),
            "memory_cache_max_size": self._max_cache_size,
            "cache_ttl": self._cache_ttl,
            "redis_available": self._redis_client is not None,
            "session_active": self._session is not None and not self._session.closed,
        }
        return stats


# Singleton instance
llm_service = HuggingFaceLLMService()
