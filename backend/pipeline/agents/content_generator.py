"""
Content Generator Agent (Stage 1)
MEB kazanımlarına uygun soru içeriği üretimi

Weight: 25%

Requirements (REQ-1.x):
- REQ-1.1: MEB kazanımını input olarak alır
- REQ-1.2: Bloom taxonomy seviyesini belirler
- REQ-1.3: Öğrenci seviyesine uygun Türkçe kullanır
- REQ-1.4: Günlük hayattan ilişkilendirme yapar
- REQ-1.5: Çoktan seçmeli, doğru-yanlış, eşleştirme formatları
- REQ-1.6: Zemberek-NLP ile Türkçe doğruluk kontrol eder
"""

import time
from typing import Any

from ..stage_base import BasePipelineStage, StageInput, StageOutput
from ..tools.meb_api_client import MEBApiClient
from ..tools.zemberek_client import ZemberekClient


class ContentGeneratorAgent(BasePipelineStage):
    """
    İçerik Üretim Agent'ı (Aşama 1)

    MEB kazanımlarına göre soru içeriği üretir.
    Bloom taxonomy seviyesini belirler ve günlük hayattan bağlam oluşturur.
    """

    STAGE_NAME = "content_generator"
    STAGE_WEIGHT = 0.25  # 25%

    # Bloom Taxonomy Seviyeleri
    BLOOM_LEVELS = [
        "hatırlama",
        "anlama",
        "uygulama",
        "analiz",
        "sentez",
        "değerlendirme"
    ]

    # Desteklenen soru tipleri
    QUESTION_TYPES = ["çoktan_seçmeli", "doğru_yanlış", "eşleştirme"]

    # Bloom seviyesine göre soru kalıpları
    BLOOM_TEMPLATES = {
        "hatırlama": [
            "Aşağıdakilerden hangisi {konu} ile ilgili doğrudur?",
            "{konu} kavramı neyi ifade eder?",
            "Aşağıdakilerden hangisi {konu}'nın özelliğidir?"
        ],
        "anlama": [
            "{konu} ile ilgili verilen bilgiyi yorumlayınız.",
            "Aşağıdaki {konu} örneğini açıklayınız.",
            "{konu} kavramını kendi cümlelerinizle ifade ediniz."
        ],
        "uygulama": [
            "Verilen {konu} problemini çözünüz.",
            "{konu} formülünü kullanarak sonucu bulunuz.",
            "Aşağıdaki {konu} uygulamasında eksik değeri hesaplayınız."
        ],
        "analiz": [
            "{konu} ile ilgili verileri analiz ediniz.",
            "Aşağıdaki {konu} grafiğini yorumlayınız.",
            "{konu} problemindeki değişkenler arasındaki ilişkiyi belirleyiniz."
        ],
        "sentez": [
            "{konu} bilgilerini kullanarak yeni bir çözüm üretiniz.",
            "Verilen {konu} verileriyle bir model oluşturunuz.",
            "{konu} prensiplerini birleştirerek sonuç çıkarınız."
        ],
        "değerlendirme": [
            "{konu} çözümünü değerlendiriniz.",
            "Aşağıdaki {konu} yaklaşımlarından hangisi daha etkilidir?",
            "{konu} sonuçlarını eleştirel olarak inceleyiniz."
        ]
    }

    def __init__(
        self,
        llm_client: Any | None = None,
        meb_api_client: MEBApiClient | None = None,
        zemberek_client: ZemberekClient | None = None,
        config: dict[str, Any] | None = None
    ):
        """
        Content Generator Agent başlat

        Args:
            llm_client: LLM istemcisi (Qwen3-8B)
            meb_api_client: MEB API istemcisi
            zemberek_client: Zemberek NLP istemcisi
            config: Ek konfigürasyon
        """
        super().__init__(self.STAGE_NAME, llm_client, config)
        self.meb_api = meb_api_client or MEBApiClient()
        self.zemberek = zemberek_client or ZemberekClient()

    async def process(self, input_data: StageInput) -> StageOutput:
        """
        Soru içeriği üret

        Args:
            input_data: Pipeline girişi (kazanım, ders, konu vb.)

        Returns:
            StageOutput: Üretilen soru içeriği ve skor
        """
        start_time = time.time()
        errors = []
        warnings = []
        suggestions = []

        try:
            question_data = input_data.question_data

            # 1. Kazanım al ve analiz et (REQ-1.1)
            kazanim = question_data.get("kazanim", "")
            if not kazanim:
                return self._create_error_output(
                    "Kazanım belirtilmedi",
                    input_data,
                    time.time() - start_time
                )

            # 2. Bloom taxonomy seviyesi belirle (REQ-1.2)
            bloom_level = await self._analyze_bloom_level(kazanim)

            # 3. Soru metni üret (REQ-1.3, REQ-1.4)
            target_difficulty = question_data.get("target_difficulty", "orta")
            konu = question_data.get("topic", question_data.get("konu", ""))

            question_text, context = await self._generate_question_content(
                kazanim=kazanim,
                konu=konu,
                bloom_level=bloom_level,
                target_difficulty=target_difficulty
            )

            # 4. Soru tipi seç (REQ-1.5)
            question_type = question_data.get("question_type", "çoktan_seçmeli")
            if question_type not in self.QUESTION_TYPES:
                question_type = "çoktan_seçmeli"
                warnings.append("Geçersiz soru tipi, 'çoktan_seçmeli' kullanıldı")

            # 5. Türkçe doğruluk kontrol et (REQ-1.6)
            is_valid_turkish, turkish_errors, turkish_score = await self._validate_turkish(
                question_text
            )

            if not is_valid_turkish:
                warnings.extend(turkish_errors[:3])

            # 6. Doğru cevabı belirle
            correct_answer = question_data.get("correct_answer")
            if not correct_answer:
                correct_answer = await self._generate_correct_answer(
                    question_text, kazanim, bloom_level
                )

            # Skor hesapla
            score = self._calculate_stage_score(
                has_kazanim=bool(kazanim),
                has_question_text=bool(question_text),
                has_context=bool(context),
                bloom_detected=bloom_level != "anlama",  # Default değil
                turkish_score=turkish_score
            )

            # Output verisi
            output_data = {
                **question_data,
                "question_text": question_text,
                "context": context,
                "bloom_level": bloom_level,
                "question_type": question_type,
                "correct_answer": correct_answer
            }

            return StageOutput(
                question_data=output_data,
                score=score,
                passed=score >= 0.6 and is_valid_turkish,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions,
                metadata={
                    "stage": self.STAGE_NAME,
                    "bloom_level": bloom_level,
                    "turkish_score": turkish_score
                },
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return self._create_error_output(
                f"İçerik üretim hatası: {e!s}",
                input_data,
                time.time() - start_time
            )

    def get_stage_weight(self) -> float:
        """Stage ağırlığı: 25%"""
        return self.STAGE_WEIGHT

    async def _analyze_bloom_level(self, kazanim: str) -> str:
        """
        Kazanımdan Bloom taxonomy seviyesini analiz et

        Args:
            kazanim: Kazanım metni

        Returns:
            str: Bloom seviyesi
        """
        kazanim_lower = kazanim.lower()

        # Anahtar kelime eşleştirme
        bloom_keywords = {
            "hatırlama": ["tanımlar", "listeler", "adlandırır", "tanır", "hatırlar", "bilir"],
            "anlama": ["açıklar", "özetler", "yorumlar", "karşılaştırır", "sınıflandırır", "anlar"],
            "uygulama": ["çözer", "uygular", "hesaplar", "gösterir", "kullanır", "yapar"],
            "analiz": ["analiz eder", "inceler", "ayırır", "ilişkilendirir", "çizer", "belirler"],
            "sentez": ["tasarlar", "oluşturur", "planlar", "üretir", "geliştirir", "birleştirir"],
            "değerlendirme": ["değerlendirir", "eleştirir", "savunur", "yargılar", "karar verir"]
        }

        for level, keywords in bloom_keywords.items():
            for keyword in keywords:
                if keyword in kazanim_lower:
                    return level

        # LLM ile analiz (fallback)
        if self.llm:
            try:
                prompt = f"""
                Aşağıdaki MEB kazanımının Bloom Taxonomy seviyesini belirle.
                Seviyeler: {self.BLOOM_LEVELS}

                Kazanım: {kazanim}

                Sadece seviye ismini döndür (küçük harfle).
                """
                response = await self.llm.generate(prompt)
                level = response.strip().lower()
                if level in self.BLOOM_LEVELS:
                    return level
            except Exception:
                pass

        return "anlama"  # Varsayılan

    async def _generate_question_content(
        self,
        kazanim: str,
        konu: str,
        bloom_level: str,
        target_difficulty: str
    ) -> tuple:
        """
        Soru metni ve bağlam üret

        Args:
            kazanim: MEB kazanımı
            konu: Konu adı
            bloom_level: Bloom seviyesi
            target_difficulty: Hedef zorluk

        Returns:
            tuple: (question_text, context)
        """
        # Template seç
        templates = self.BLOOM_TEMPLATES.get(bloom_level, self.BLOOM_TEMPLATES["anlama"])
        import random
        template = random.choice(templates)

        # LLM ile içerik üret
        if self.llm:
            try:
                prompt = f"""
                Sen bir ÖSYM soru yazarısın. Aşağıdaki kazanıma göre {target_difficulty}
                seviyesinde bir soru yaz.

                Kazanım: {kazanim}
                Konu: {konu}
                Bloom Seviyesi: {bloom_level}
                Hedef Zorluk: {target_difficulty}

                Kurallar:
                - Lise seviyesine uygun Türkçe kullan
                - Maksimum 150 kelime
                - Açık ve anlaşılır ol
                - Günlük hayattan örnek ver (mümkünse)

                Soru metnini yaz:
                """

                question_text = await self.llm.generate(prompt, max_tokens=300)
                question_text = question_text.strip()

                # Bağlam üret
                context_prompt = f"""
                Aşağıdaki soru için kısa bir günlük hayat bağlamı oluştur (1-2 cümle):

                Soru: {question_text}
                Konu: {konu}

                Bağlam:
                """

                context = await self.llm.generate(context_prompt, max_tokens=100)
                context = context.strip()

                return question_text, context

            except Exception:
                pass

        # Fallback: Template kullan
        question_text = template.format(konu=konu if konu else "verilen kavram")
        context = f"Bu soru {konu} konusuyla ilgilidir."

        return question_text, context

    async def _validate_turkish(self, text: str) -> tuple:
        """
        Türkçe metin doğrulama

        Args:
            text: Doğrulanacak metin

        Returns:
            tuple: (is_valid, errors, score)
        """
        return await self.zemberek.validate_turkish_text(text)

    async def _generate_correct_answer(
        self,
        question_text: str,
        kazanim: str,
        bloom_level: str
    ) -> str:
        """
        Doğru cevabı üret

        Args:
            question_text: Soru metni
            kazanim: Kazanım
            bloom_level: Bloom seviyesi

        Returns:
            str: Doğru cevap metni
        """
        if self.llm:
            try:
                prompt = f"""
                Aşağıdaki sorunun doğru cevabını yaz (kısa ve öz):

                Soru: {question_text}
                Kazanım: {kazanim}

                Doğru Cevap:
                """

                response = await self.llm.generate(prompt, max_tokens=100)
                return response.strip()
            except Exception:
                pass

        return "Doğru cevap belirtilmedi"

    def _calculate_stage_score(
        self,
        has_kazanim: bool,
        has_question_text: bool,
        has_context: bool,
        bloom_detected: bool,
        turkish_score: float
    ) -> float:
        """
        Aşama skoru hesapla

        Args:
            has_kazanim: Kazanım var mı
            has_question_text: Soru metni var mı
            has_context: Bağlam var mı
            bloom_detected: Bloom seviyesi tespit edildi mi
            turkish_score: Türkçe doğruluk skoru

        Returns:
            float: Aşama skoru (0-1)
        """
        score = 0.0

        # Kritik gereksinimler
        if not has_kazanim or not has_question_text:
            return 0.3

        # Puanlama
        score += 0.3 if has_kazanim else 0.0
        score += 0.3 if has_question_text else 0.0
        score += 0.1 if has_context else 0.0
        score += 0.1 if bloom_detected else 0.05
        score += 0.2 * turkish_score

        return min(1.0, score)

    def _create_error_output(
        self,
        error_message: str,
        input_data: StageInput,
        execution_time: float
    ) -> StageOutput:
        """Hata output'u oluştur"""
        return StageOutput(
            question_data=input_data.question_data,
            score=0.0,
            passed=False,
            errors=[error_message],
            warnings=[],
            suggestions=["Kazanım ve konu bilgilerini kontrol edin"],
            metadata={"stage": self.STAGE_NAME, "error": True},
            execution_time=execution_time
        )
