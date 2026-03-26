"""
3 Seviyeli Türkçe Metin Basitleştirme Sistemi
Dünyada ilk 3 seviyeli Türkçe metin basitleştirme sistemi

Level 1: Lexical (Kelime seviyesi)
Level 2: Syntactic (Cümle yapısı seviyesi)  
Level 3: Semantic (Anlam seviyesi)

Requirements: 10.5, 12.5
"""

import asyncio
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Tuple


@dataclass
class SimplificationResult:
    """Basitleştirme sonucu"""

    original_text: str
    level1_lexical: str
    level2_syntactic: str
    level3_semantic: str
    complexity_reduction: float  # 0-1 arası
    readability_score: float  # 0-10 arası
    processing_time_ms: float
    applied_rules: List[str]


@dataclass
class LexicalReplacement:
    """Kelime değiştirme kuralı"""

    original: str
    replacement: str
    category: str  # "ottoman", "academic", "foreign"
    confidence: float


@dataclass
class SyntacticPattern:
    """Cümle yapısı kalıbı"""

    pattern: str
    replacement_template: str
    description: str
    complexity_reduction: float


class ThreeLevelTurkishSimplification:
    """
    Level 1: Lexical (Kelime seviyesi)
    Level 2: Syntactic (Cümle yapısı seviyesi)
    Level 3: Semantic (Anlam seviyesi)
    """

    def __init__(self):
        # Osmanlıca/akademik kelime sözlüğü
        self.ottoman_academic_replacements = {
            "mütalaa": "okuma",
            "tetkik": "inceleme",
            "müzakere": "görüşme",
            "istifade": "yararlanma",
            "istihsal": "üretim",
            "münasebet": "ilişki",
            "mütalaasında": "görüşünde",
            "teşebbüs": "girişim",
            "müdahale": "karışma",
            "muvaffakiyet": "başarı",
            "müşkülat": "zorluk",
            "müsaade": "izin",
            "müracaat": "başvuru",
            "mütehassıs": "uzman",
            "müessese": "kurum",
            "müdür": "yönetici",
            "müfettiş": "denetçi",
            "müteahhit": "yüklenici",
            "müşteri": "alıcı",
            "müze": "müze",  # Bu değişmez
            "müzik": "müzik",  # Bu değişmez
        }

        # Yabancı kökenli kelimeler
        self.foreign_replacements = {
            "implementasyon": "uygulama",
            "optimizasyon": "eniyileme",
            "performans": "başarım",
            "analiz": "çözümleme",
            "sentez": "birleştirme",
            "hipotez": "varsayım",
            "metodoloji": "yöntem bilimi",
            "algoritma": "işlem dizisi",
            "parametr": "değişken",
            "koordinasyon": "eşgüdüm",
            "organizasyon": "örgütlenme",
            "transformasyon": "dönüşüm",
            "adaptasyon": "uyarlama",
            "integrasyon": "bütünleşme",
            "konfigürasyon": "yapılandırma",
        }

        # Karmaşık cümle kalıpları
        self.complex_sentence_patterns = [
            SyntacticPattern(
                pattern=r"(.+?)(da|de|ta|te)\s+(.+?)(dığı|diği|duğu|düğü)\s+(.+)",
                replacement_template="{3}. {1}{2} {5}.",
                description="Sıfat cümlesi ayrıştırma",
                complexity_reduction=0.3,
            ),
            SyntacticPattern(
                pattern=r"(.+?)(arak|erek)\s+(.+)",
                replacement_template="{1}. {3}.",
                description="Zarf-fiil ayrıştırma",
                complexity_reduction=0.2,
            ),
            SyntacticPattern(
                pattern=r"(.+?)(ince|ınca|unca|ünce)\s+(.+)",
                replacement_template="{1}. Sonra {3}.",
                description="Zaman cümlesi ayrıştırma",
                complexity_reduction=0.25,
            ),
            SyntacticPattern(
                pattern=r"(.+?)(ken|iken)\s+(.+)",
                replacement_template="{1}. Bu sırada {3}.",
                description="Hal cümlesi ayrıştırma",
                complexity_reduction=0.2,
            ),
        ]

        # Okuma seviyesi hedefleri
        self.target_levels = {
            "elementary": {"max_syllables": 3, "max_sentence_length": 10},
            "intermediate": {"max_syllables": 4, "max_sentence_length": 15},
            "advanced": {"max_syllables": 5, "max_sentence_length": 20},
        }

    async def revolutionary_simplification(
        self, text: str, target_level: str = "intermediate"
    ) -> SimplificationResult:
        """3 seviyeli devrimsel basitleştirme"""

        start_time = datetime.now()
        applied_rules = []

        # Orijinal karmaşıklık hesapla
        original_complexity = self._calculate_text_complexity(text)

        # SEVİYE 1: Lexical (Kelime değiştirme)
        level1_text, lexical_rules = await self._lexical_simplification(text)
        applied_rules.extend(lexical_rules)

        # SEVİYE 2: Syntactic (Cümle yapısı)
        level2_text, syntactic_rules = await self._syntactic_simplification(level1_text)
        applied_rules.extend(syntactic_rules)

        # SEVİYE 3: Semantic (Anlam korunumu ile yeniden yazma)
        level3_text, semantic_rules = await self._semantic_restructuring(
            level2_text, target_level
        )
        applied_rules.extend(semantic_rules)

        # Final karmaşıklık hesapla
        final_complexity = self._calculate_text_complexity(level3_text)
        complexity_reduction = (
            original_complexity - final_complexity
        ) / original_complexity

        # Okunabilirlik skoru hesapla
        readability_score = self._calculate_turkish_readability(level3_text)

        # İşlem süresi
        processing_time = max(
            0.1, (datetime.now() - start_time).total_seconds() * 1000
        )  # Minimum 0.1ms

        return SimplificationResult(
            original_text=text,
            level1_lexical=level1_text,
            level2_syntactic=level2_text,
            level3_semantic=level3_text,
            complexity_reduction=max(0.0, complexity_reduction),
            readability_score=readability_score,
            processing_time_ms=processing_time,
            applied_rules=applied_rules,
        )

    async def _lexical_simplification(self, text: str) -> Tuple[str, List[str]]:
        """Seviye 1: Kelime değiştirme"""

        simplified_text = text
        applied_rules = []

        # Osmanlıca/akademik kelimeleri değiştir
        for complex_word, simple_word in self.ottoman_academic_replacements.items():
            if complex_word in simplified_text:
                simplified_text = simplified_text.replace(complex_word, simple_word)
                applied_rules.append(
                    f"Ottoman/Academic: {complex_word} → {simple_word}"
                )

        # Yabancı kökenli kelimeleri Türkçe karşılıklarıyla değiştir
        for foreign_word, turkish_word in self.foreign_replacements.items():
            if foreign_word in simplified_text:
                simplified_text = simplified_text.replace(foreign_word, turkish_word)
                applied_rules.append(f"Foreign: {foreign_word} → {turkish_word}")

        # Uzun kelimeleri basitleştir
        long_word_replacements = await self._find_long_word_replacements(
            simplified_text
        )
        for original, replacement in long_word_replacements.items():
            simplified_text = simplified_text.replace(original, replacement)
            applied_rules.append(f"Long word: {original} → {replacement}")

        return simplified_text, applied_rules

    async def _syntactic_simplification(self, text: str) -> Tuple[str, List[str]]:
        """Seviye 2: Cümle yapısı basitleştirme"""

        sentences = self._split_sentences(text)
        simplified_sentences = []
        applied_rules = []

        for sentence in sentences:
            if len(sentence.strip()) == 0:
                continue

            # Karmaşık cümle yapılarını tespit et ve böl
            if self._is_complex_sentence(sentence):
                split_sentences, rules = await self._split_complex_turkish_sentence(
                    sentence
                )
                simplified_sentences.extend(split_sentences)
                applied_rules.extend(rules)
            else:
                simplified_sentences.append(sentence.strip())

        # Pasif cümleleri aktif yap
        active_sentences = []
        for sentence in simplified_sentences:
            active_sentence, passive_rules = self._convert_passive_to_active(sentence)
            active_sentences.append(active_sentence)
            applied_rules.extend(passive_rules)

        return ". ".join(active_sentences) + ".", applied_rules

    async def _split_complex_turkish_sentence(
        self, sentence: str
    ) -> Tuple[List[str], List[str]]:
        """Karmaşık Türkçe cümleleri böl"""

        split_sentences = []
        applied_rules = []

        # Kalıp tabanlı bölme
        for pattern in self.complex_sentence_patterns:
            match = re.search(pattern.pattern, sentence, re.IGNORECASE)
            if match:
                try:
                    # Kalıp uygulaması (basitleştirilmiş)
                    groups = match.groups()
                    if len(groups) >= 3:
                        # İlk cümle
                        first_part = groups[0].strip()
                        if first_part:
                            split_sentences.append(first_part)

                        # İkinci cümle
                        if len(groups) > 2:
                            second_part = groups[2].strip()
                            if second_part:
                                split_sentences.append(second_part)

                        applied_rules.append(f"Pattern applied: {pattern.description}")
                        return split_sentences, applied_rules
                except Exception:
                    continue

        # Kalıp bulunamazsa bağlaçlarla böl
        conjunction_split, conj_rules = await self._split_by_conjunctions(sentence)
        split_sentences.extend(conjunction_split)
        applied_rules.extend(conj_rules)

        return split_sentences if split_sentences else [sentence], applied_rules

    async def _split_by_conjunctions(
        self, sentence: str
    ) -> Tuple[List[str], List[str]]:
        """Bağlaçlarla cümle bölme"""

        conjunctions = [
            "ve",
            "ama",
            "fakat",
            "ancak",
            "lakin",
            "çünkü",
            "için",
            "böylece",
        ]
        applied_rules = []

        for conjunction in conjunctions:
            if f" {conjunction} " in sentence:
                parts = sentence.split(f" {conjunction} ", 1)
                if len(parts) == 2:
                    applied_rules.append(f"Split by conjunction: {conjunction}")
                    return [parts[0].strip(), parts[1].strip()], applied_rules

        return [sentence], applied_rules

    async def _semantic_restructuring(
        self, text: str, target_level: str
    ) -> Tuple[str, List[str]]:
        """Seviye 3: Anlam korunumu ile yeniden yazma"""

        applied_rules = []

        # Metaforları somut ifadelere çevir
        metaphor_text, metaphor_rules = self._simplify_metaphors(text)
        applied_rules.extend(metaphor_rules)

        # Soyut kavramları somut örneklerle açıkla
        concrete_text, concrete_rules = self._add_concrete_examples(metaphor_text)
        applied_rules.extend(concrete_rules)

        # Uzun cümleleri kısa cümlelere böl
        short_text, length_rules = self._shorten_sentences(concrete_text, target_level)
        applied_rules.extend(length_rules)

        # Teknik terimleri açıkla
        explained_text, explanation_rules = self._explain_technical_terms(short_text)
        applied_rules.extend(explanation_rules)

        return explained_text, applied_rules

    def _simplify_metaphors(self, text: str) -> Tuple[str, List[str]]:
        """Metaforları basitleştir"""

        metaphor_replacements = {
            "kalbi kırılmak": "üzülmek",
            "gözü yükseklerde": "hırslı olmak",
            "dili tutulmak": "konuşamamak",
            "eli açık": "cömert",
            "ayağı kaymak": "hata yapmak",
            "başı dönmek": "şaşırmak",
            "gözü kapalı": "güvenerek",
            "kulağı çınlamak": "hakkında konuşulmak",
        }

        simplified_text = text
        applied_rules = []

        for metaphor, simple_form in metaphor_replacements.items():
            if metaphor in simplified_text:
                simplified_text = simplified_text.replace(metaphor, simple_form)
                applied_rules.append(f"Metaphor simplified: {metaphor} → {simple_form}")

        return simplified_text, applied_rules

    def _add_concrete_examples(self, text: str) -> Tuple[str, List[str]]:
        """Soyut kavramlara somut örnekler ekle"""

        abstract_concepts = {
            "demokrasi": "demokrasi (halkın yönetimi)",
            "özgürlük": "özgürlük (istediğini yapabilme)",
            "adalet": "adalet (herkese eşit davranma)",
            "barış": "barış (savaşın olmaması)",
            "kültür": "kültür (yaşam biçimi)",
            "medeniyet": "medeniyet (gelişmiş toplum)",
            "sanat": "sanat (güzel eserler)",
            "bilim": "bilim (araştırma ve keşif)",
        }

        explained_text = text
        applied_rules = []

        for concept, explanation in abstract_concepts.items():
            if concept in explained_text and explanation not in explained_text:
                explained_text = explained_text.replace(concept, explanation)
                applied_rules.append(f"Abstract concept explained: {concept}")

        return explained_text, applied_rules

    def _shorten_sentences(self, text: str, target_level: str) -> Tuple[str, List[str]]:
        """Cümleleri kısalt"""

        target_config = self.target_levels.get(
            target_level, self.target_levels["intermediate"]
        )
        max_length = target_config["max_sentence_length"]

        sentences = self._split_sentences(text)
        shortened_sentences = []
        applied_rules = []

        for sentence in sentences:
            words = sentence.split()
            if len(words) > max_length:
                # Cümleyi ortadan böl
                mid_point = len(words) // 2
                first_half = " ".join(words[:mid_point])
                second_half = " ".join(words[mid_point:])

                shortened_sentences.append(first_half)
                shortened_sentences.append(second_half)
                applied_rules.append(
                    f"Long sentence split: {len(words)} words → 2 sentences"
                )
            else:
                shortened_sentences.append(sentence)

        return ". ".join(shortened_sentences), applied_rules

    def _explain_technical_terms(self, text: str) -> Tuple[str, List[str]]:
        """Teknik terimleri açıkla"""

        technical_terms = {
            "algoritma": "algoritma (problem çözme adımları)",
            "veri": "veri (bilgi)",
            "sistem": "sistem (düzen)",
            "analiz": "analiz (inceleme)",
            "sentez": "sentez (birleştirme)",
            "hipotez": "hipotez (varsayım)",
            "teori": "teori (açıklama)",
            "model": "model (örnek)",
        }

        explained_text = text
        applied_rules = []

        for term, explanation in technical_terms.items():
            if term in explained_text and explanation not in explained_text:
                explained_text = explained_text.replace(term, explanation)
                applied_rules.append(f"Technical term explained: {term}")

        return explained_text, applied_rules

    def _convert_passive_to_active(self, sentence: str) -> Tuple[str, List[str]]:
        """Pasif cümleleri aktif yap"""

        applied_rules = []

        # Basit pasif yapı tespiti
        passive_patterns = [
            (r"(.+?)\s+(yapıldı|edildi|alındı|verildi)", r"\1 yapıldı"),
            (r"(.+?)\s+tarafından\s+(.+)", r"\2 \1"),
        ]

        active_sentence = sentence

        for pattern, replacement in passive_patterns:
            if re.search(pattern, sentence):
                active_sentence = re.sub(pattern, replacement, sentence)
                applied_rules.append("Passive to active conversion")
                break

        return active_sentence, applied_rules

    async def _find_long_word_replacements(self, text: str) -> Dict[str, str]:
        """Uzun kelimelerin kısa karşılıklarını bul"""

        words = re.findall(r"\b\w+\b", text)
        replacements = {}

        for word in words:
            if len(word) > 10:  # 10 karakterden uzun kelimeler
                # Basit kısaltma stratejileri
                if word.endswith("leştirmek"):
                    short_form = word.replace("leştirmek", "lamak")
                    replacements[word] = short_form
                elif word.endswith("landırmak"):
                    short_form = word.replace("landırmak", "lamak")
                    replacements[word] = short_form

        return replacements

    def _split_sentences(self, text: str) -> List[str]:
        """Metni cümlelere böl"""
        sentences = re.split(r"[.!?]+", text)
        return [s.strip() for s in sentences if s.strip()]

    def _is_complex_sentence(self, sentence: str) -> bool:
        """Cümle karmaşık mı kontrol et"""

        # Karmaşıklık göstergeleri
        complexity_indicators = [
            len(sentence.split()) > 15,  # 15+ kelime
            sentence.count(",") > 2,  # 2+ virgül
            any(
                pattern.pattern in sentence
                for pattern in self.complex_sentence_patterns
            ),
            "ki " in sentence,  # Ki bağlacı
            "ise" in sentence,  # Şart eki
            "olarak" in sentence,  # Zarf-fiil
        ]

        return sum(complexity_indicators) >= 2

    def _calculate_text_complexity(self, text: str) -> float:
        """Metin karmaşıklığı hesapla"""

        if not text.strip():
            return 0.0

        words = text.split()
        sentences = self._split_sentences(text)

        if not sentences:
            return 0.0

        # Karmaşıklık faktörleri
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        avg_sentence_length = len(words) / len(sentences)
        long_words_ratio = (
            sum(1 for word in words if len(word) > 6) / len(words) if words else 0
        )

        # Toplam karmaşıklık skoru (0-10 arası)
        complexity = (
            (avg_word_length / 10) * 3
            + (avg_sentence_length / 20) * 4
            + long_words_ratio * 3
        )

        return min(10.0, complexity)

    def _calculate_turkish_readability(self, text: str) -> float:
        """Türkçe okunabilirlik skoru hesapla"""

        if not text.strip():
            return 0.0

        words = text.split()
        sentences = self._split_sentences(text)

        if not sentences or not words:
            return 0.0

        # Türkçe'ye uyarlanmış okunabilirlik formülü
        avg_sentence_length = len(words) / len(sentences)
        avg_syllables = sum(self._count_syllables(word) for word in words) / len(words)

        # Flesch-Kincaid benzeri formül (Türkçe'ye uyarlanmış)
        readability = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables)

        # 0-10 arası normalize et
        normalized_score = max(0, min(10, readability / 20))

        return normalized_score

    def _count_syllables(self, word: str) -> int:
        """Türkçe kelimede hece sayısı"""

        vowels = "aeiouıöüAEIOUIÖÜ"
        syllable_count = 0
        prev_was_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                syllable_count += 1
            prev_was_vowel = is_vowel

        return max(1, syllable_count)  # En az 1 hece

    async def batch_simplify(
        self, texts: List[str], target_level: str = "intermediate"
    ) -> List[SimplificationResult]:
        """Toplu basitleştirme"""

        tasks = [
            self.revolutionary_simplification(text, target_level) for text in texts
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Hataları filtrele
        valid_results = []
        for result in results:
            if isinstance(result, SimplificationResult):
                valid_results.append(result)
            else:
                # Hata durumunda boş sonuç
                valid_results.append(
                    SimplificationResult(
                        original_text="",
                        level1_lexical="",
                        level2_syntactic="",
                        level3_semantic="",
                        complexity_reduction=0.0,
                        readability_score=0.0,
                        processing_time_ms=0.0,
                        applied_rules=["Error occurred"],
                    )
                )

        return valid_results

    def get_simplification_statistics(
        self, result: SimplificationResult
    ) -> Dict[str, Any]:
        """Basitleştirme istatistikleri"""

        original_words = len(result.original_text.split())
        final_words = len(result.level3_semantic.split())

        original_sentences = len(self._split_sentences(result.original_text))
        final_sentences = len(self._split_sentences(result.level3_semantic))

        return {
            "word_count_change": final_words - original_words,
            "sentence_count_change": final_sentences - original_sentences,
            "complexity_reduction_percent": result.complexity_reduction * 100,
            "readability_improvement": result.readability_score,
            "processing_time_ms": result.processing_time_ms,
            "rules_applied_count": len(result.applied_rules),
            "levels_processed": 3,
        }


# Test ve örnek kullanım
async def test_simplification_system():
    """Test fonksiyonu"""

    simplifier = ThreeLevelTurkishSimplification()

    test_texts = [
        "Çekoslovakyalılaştıramadıklarımızdanmısınız sorusunun mütalaa edilmesi gerekiyor.",
        "Bu müessesede yapılan tetkikler neticesinde muvaffakiyet elde edilmiştir.",
        "Okulda okuduğum kitabı eve gelince tekrar okuyarak anlamaya çalıştım.",
    ]

    print("3 Seviyeli Türkçe Metin Basitleştirme Sistemi Test")
    print("=" * 60)

    for i, text in enumerate(test_texts, 1):
        print(f"\nTest {i}:")
        print(f"Orijinal: {text}")

        result = await simplifier.revolutionary_simplification(text, "intermediate")

        print(f"Level 1 (Lexical): {result.level1_lexical}")
        print(f"Level 2 (Syntactic): {result.level2_syntactic}")
        print(f"Level 3 (Semantic): {result.level3_semantic}")
        print(f"Karmaşıklık Azalması: {result.complexity_reduction:.2%}")
        print(f"Okunabilirlik Skoru: {result.readability_score:.1f}/10")
        print(f"İşlem Süresi: {result.processing_time_ms:.1f}ms")
        print(f"Uygulanan Kurallar: {len(result.applied_rules)}")


if __name__ == "__main__":
    asyncio.run(test_simplification_system())
