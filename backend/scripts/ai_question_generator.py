"""
AI-Powered Question Generator - Hybrid GPT-5 & Claude 4.5 System
Araştırma temelli best practices ile soru üretimi
"""
import asyncio
import json

# API Keys from environment
import os
from datetime import datetime

import anthropic
import openai
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")  # Claude API key


class QuestionData(BaseModel):
    """Soru verisi modeli"""

    metin: str
    secenekler: dict[str, str]  # {"A": "...", "B": "...", ...}
    dogru_cevap: str
    sinav_tipi: str  # TYT, AYT
    konu: str
    alt_konu: str | None
    kazanim: str
    zorluk: str  # easy, medium, hard
    bloom_level: str  # remember, understand, apply, analyze, evaluate, create
    cozum_adimlari: list[str]
    sure_tahmini: int  # saniye


# ============================================================================
# BEST PRACTICE: Multi-Model Prompt System
# ============================================================================

# GPT-5 İçin Optimize Prompt (Teknik Konular: Matematik, Fizik, Kimya)
GPT5_TECHNICAL_PROMPT = """Sen bir ÖSYM sınav sorusu yazma uzmanısın. TYT/AYT formatında, MEB müfredatına uygun sorular üretiyorsun.

**ÖNEMLİ KURALLAR:**
1. ÖSYM soruları ÖRNEK ALINAMAZ (telif), ama FORMAT ve STİL taklit edilebilir
2. Her soru benzersiz olmalı, plagiarism riski olmamalı
3. Bloom Taxonomy seviyesine dikkat et
4. IRT parametreleri için zorluk seviyesi belirtilmeli

**SORU FORMATI:**
- 5 seçenekli (A, B, C, D, E)
- Net hesaplama: Doğru - (Yanlış/4)
- Çözüm süresi: 60-180 saniye arası

**GİRDİ:**
Konu: {konu}
Alt Konu: {alt_konu}
Kazanım: {kazanim}
Zorluk: {zorluk}
Bloom Seviyesi: {bloom_level}

**ÇIKTI (JSON):**
{{
    "metin": "Soru metni...",
    "secenekler": {{
        "A": "Seçenek A",
        "B": "Seçenek B",
        "C": "Seçenek C",
        "D": "Seçenek D",
        "E": "Seçenek E"
    }},
    "dogru_cevap": "C",
    "cozum_adimlari": ["Adım 1", "Adım 2", "Adım 3"],
    "sure_tahmini": 120,
    "neden_bu_zorluk": "Bu soru [zorluk] seviyesi çünkü...",
    "pedagojik_aciklama": "Bu soru öğrencinin X bilgisini test eder"
}}

**KALİTE KRİTERLERİ:**
1. Seçenekler birbirine yakın zorlukta olmalı (plausible distractors)
2. Doğru cevap açıkça belli olmamalı
3. Türkçe dilbilgisi kusursuz olmalı
4. Görsele gerek varsa "[GÖRSEL GEREKLİ: açıklama]" yaz
"""

# Claude 4.5 İçin Optimize Prompt (Dil & Sosyal: Türkçe, Edebiyat, Tarih)
CLAUDE_CREATIVE_PROMPT = """Sen deneyimli bir Türkçe/Edebiyat/Sosyal Bilimler öğretmenisin ve ÖSYM formatında soru yazıyorsun.

**SENİN ÜSTÜNLÜĞÜN (Claude 4.5):**
- Üstün dil ve anlatım hassasiyeti (200K token context)
- Bağlam anlama ve yaratıcı metin oluşturma
- Empati ve pedagojik yaklaşım
- Türk kültürüne uygunluk
- En gelişmiş muhakeme yetenekleri
- Çok dilli anlama ve kültürel adaptasyon

**GÖREV:**
Verilen kazanım için özgün, yaratıcı ve pedagojik açıdan değerli bir soru üret.

**GİRDİ:**
Konu: {konu}
Alt Konu: {alt_konu}
Kazanım: {kazanim}
Zorluk: {zorluk}
Bloom Seviyesi: {bloom_level}

**ÇIKTI (JSON):**
{{
    "metin": "Soru metni... (gerekirse metin parçası ile)",
    "secenekler": {{
        "A": "Seçenek A",
        "B": "Seçenek B",
        "C": "Seçenek C",
        "D": "Seçenek D",
        "E": "Seçenek E"
    }},
    "dogru_cevap": "B",
    "cozum_adimlari": ["Mantıksal adım 1", "Adım 2", ...],
    "sure_tahmini": 90,
    "pedagojik_deger": "Bu soru öğrencinin eleştirel düşünme becerisini geliştirir çünkü..."
}}

**DİKKAT:**
- Seçenekler semantik olarak yakın olmalı (kolay seçim yapılmamalı)
- Türkçe kullanımı kusursuz olmalı
- Tarihsel/kültürel hassasiyetlere dikkat et
"""


# ============================================================================
# Question Generator Class
# ============================================================================


class HybridQuestionGenerator:
    """
    GPT-5 + Claude 4.5 hibrit soru üretici
    BEST PRACTICE: Model selection based on subject
    """

    def __init__(self):
        self.gpt_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        self.claude_client = (
            anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            if ANTHROPIC_API_KEY
            else None
        )

        # Model seçim stratejisi
        self.technical_subjects = [
            "matematik",
            "fizik",
            "kimya",
            "biyoloji",
            "geometri",
        ]
        self.creative_subjects = ["türkçe", "edebiyat", "tarih", "coğrafya", "felsefe"]

    def select_model(self, konu: str) -> str:
        """
        BEST PRACTICE: Subject-based model selection
        Araştırma: GPT-5 teknikte, Claude Pro yaratıcılıkta daha iyi
        """
        konu_lower = konu.lower()

        if any(subj in konu_lower for subj in self.technical_subjects):
            return "gpt-5"
        if any(subj in konu_lower for subj in self.creative_subjects):
            return "claude"
        # Default: GPT-5 (daha hızlı ve güçlü)
        return "gpt-5"

    async def generate_with_gpt5(
        self, konu: str, alt_konu: str, kazanim: str, zorluk: str, bloom_level: str
    ) -> dict:
        """GPT-5 ile soru üretimi"""
        prompt = GPT5_TECHNICAL_PROMPT.format(
            konu=konu,
            alt_konu=alt_konu,
            kazanim=kazanim,
            zorluk=zorluk,
            bloom_level=bloom_level,
        )

        try:
            response = self.gpt_client.chat.completions.create(
                model="gpt-5-turbo-preview",  # GPT-5 model
                messages=[
                    {
                        "role": "system",
                        "content": "Sen bir eğitim teknolojisi soru üretim uzmanısın.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,  # Yaratıcılık için biraz yüksek
                max_tokens=2000,
                response_format={"type": "json_object"},  # JSON formatı zorunlu
            )

            result = json.loads(response.choices[0].message.content)
            result["ai_model"] = "gpt-5"
            result["generation_timestamp"] = datetime.now().isoformat()

            return result

        except Exception as e:
            print(f"GPT-5 Error: {e}")
            return {"error": str(e)}

    async def generate_with_claude(
        self, konu: str, alt_konu: str, kazanim: str, zorluk: str, bloom_level: str
    ) -> dict:
        """Claude AI Pro ile soru üretimi"""
        if not self.claude_client:
            print("Claude API key not configured, falling back to GPT-5")
            return await self.generate_with_gpt5(
                konu, alt_konu, kazanim, zorluk, bloom_level
            )

        prompt = CLAUDE_CREATIVE_PROMPT.format(
            konu=konu,
            alt_konu=alt_konu,
            kazanim=kazanim,
            zorluk=zorluk,
            bloom_level=bloom_level,
        )

        try:
            response = self.claude_client.messages.create(
                model="claude-sonnet-4-5-20250929",  # En güçlü Claude 4.5 model
                max_tokens=2000,
                temperature=0.8,  # Daha yaratıcı
                messages=[{"role": "user", "content": prompt}],
            )

            # Claude response'u parse et
            content = response.content[0].text
            result = json.loads(content)
            result["ai_model"] = "claude-4.5"
            result["generation_timestamp"] = datetime.now().isoformat()

            return result

        except Exception as e:
            print(f"Claude Error: {e}")
            return {"error": str(e)}

    async def generate_question(
        self,
        konu: str,
        alt_konu: str,
        kazanim: str,
        zorluk: str = "medium",
        bloom_level: str = "apply",
        force_model: str | None = None,
    ) -> dict:
        """
        Ana soru üretim fonksiyonu
        BEST PRACTICE: Otomatik model seçimi
        """
        # Model seçimi
        if force_model:
            model = force_model
        else:
            model = self.select_model(konu)

        print(f"🤖 {model.upper()} ile soru üretiliyor: {konu} - {alt_konu}")

        if model == "gpt-5":
            result = await self.generate_with_gpt5(
                konu, alt_konu, kazanim, zorluk, bloom_level
            )
        else:
            result = await self.generate_with_claude(
                konu, alt_konu, kazanim, zorluk, bloom_level
            )

        # Metadata ekle
        result["input_params"] = {
            "konu": konu,
            "alt_konu": alt_konu,
            "kazanim": kazanim,
            "zorluk": zorluk,
            "bloom_level": bloom_level,
        }

        return result

    async def generate_batch(
        self, specifications: list[dict], concurrent_limit: int = 5
    ) -> list[dict]:
        """
        Toplu soru üretimi (paralel)
        BEST PRACTICE: Rate limiting ile API limitleri aşılmaz
        """
        semaphore = asyncio.Semaphore(concurrent_limit)

        async def generate_with_limit(spec):
            async with semaphore:
                return await self.generate_question(**spec)

        tasks = [generate_with_limit(spec) for spec in specifications]
        results = await asyncio.gather(*tasks)

        return results


# ============================================================================
# ÖRNEK KULLANIM
# ============================================================================


async def main_example():
    """Örnek kullanım"""
    generator = HybridQuestionGenerator()

    # Tek soru örneği
    print("=== TEK SORU ÜRETİMİ ===")
    question = await generator.generate_question(
        konu="Matematik",
        alt_konu="Türev",
        kazanim="Türev kurallarını kullanarak fonksiyonların türevini alabilme",
        zorluk="medium",
        bloom_level="apply",
    )
    print(json.dumps(question, indent=2, ensure_ascii=False))

    # Toplu soru örneği (10 soru)
    print("\n=== TOPLU SORU ÜRETİMİ (10 SORU) ===")
    batch_specs = [
        {
            "konu": "Matematik",
            "alt_konu": "Türev",
            "kazanim": "Türev kurallarını uygulama",
            "zorluk": "medium",
            "bloom_level": "apply",
        },
        {
            "konu": "Türkçe",
            "alt_konu": "Cümle Bilgisi",
            "kazanim": "Cümle türlerini ayırt etme",
            "zorluk": "easy",
            "bloom_level": "understand",
        },
        # ... 8 tane daha ekle
    ]

    batch_results = await generator.generate_batch(batch_specs, concurrent_limit=3)
    print(f"✅ {len(batch_results)} soru üretildi")

    # Sonuçları dosyaya kaydet
    with open("generated_questions.json", "w", encoding="utf-8") as f:
        json.dump(batch_results, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    asyncio.run(main_example())
