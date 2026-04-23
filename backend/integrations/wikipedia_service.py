"""
Wikipedia API Entegrasyonu
Ansiklopedik bilgi erişimi
Teknofest 2025 - Eğitim Eylemci Projesi
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class WikipediaArticle:
    """Wikipedia makale modeli"""

    page_id: int
    title: str
    summary: str
    content: str
    url: str
    categories: list[str]
    images: list[str]
    references: list[str]
    language: str
    last_modified: datetime
    word_count: int
    educational_relevance: float  # 0-1 arası eğitim ilgililik skoru


class WikipediaService:
    """Wikipedia API servisi"""

    def __init__(self):
        self.base_urls = {
            "tr": "https://tr.wikipedia.org/api/rest_v1",
            "en": "https://en.wikipedia.org/api/rest_v1",
        }
        self.api_endpoint = "https://{lang}.wikipedia.org/w/api.php"

    async def search_articles(
        self,
        query: str,
        language: str = "tr",
        limit: int = 10,
        educational_filter: bool = True,
    ) -> list[WikipediaArticle]:
        """
        Wikipedia makalelerini ara

        Args:
            query: Arama sorgusu
            language: Dil kodu
            limit: Maksimum sonuç sayısı
            educational_filter: Eğitim filtresi

        Returns:
            Makale listesi
        """
        try:
            # API URL
            url = self.api_endpoint.format(lang=language)

            # Parametreler
            params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": query,
                "srlimit": limit * 2,  # Filtreleme için fazla al
                "srprop": "snippet|titlesnippet|size|wordcount|timestamp",
            }

            # Simüle edilmiş API çağrısı
            articles = await self._simulate_search(query, language, limit)

            # Eğitim filtresi uygula
            if educational_filter:
                articles = [a for a in articles if a.educational_relevance > 0.5]

            # Sırala ve limitle
            articles.sort(key=lambda a: a.educational_relevance, reverse=True)

            logger.info(f"Found {len(articles)} Wikipedia articles for '{query}'")
            return articles[:limit]

        except Exception as e:
            logger.error(f"Wikipedia search error: {e!s}")
            return []

    async def _simulate_search(
        self, query: str, language: str, limit: int
    ) -> list[WikipediaArticle]:
        """Arama sonuçlarını simüle et"""
        # Örnek makaleler
        sample_articles = [
            WikipediaArticle(
                page_id=12345,
                title="Hücre bölünmesi",
                summary="Hücre bölünmesi, bir hücrenin iki veya daha fazla yavru hücreye bölündüğü süreçtir.",
                content="Hücre bölünmesi detaylı içerik...",
                url="https://tr.wikipedia.org/wiki/Hücre_bölünmesi",
                categories=["Biyoloji", "Hücre biyolojisi", "Genetik"],
                images=["https://example.com/cell_division.jpg"],
                references=["ref1", "ref2"],
                language=language,
                last_modified=datetime.now(),
                word_count=1500,
                educational_relevance=0.9,
            ),
            WikipediaArticle(
                page_id=23456,
                title="Mitoz",
                summary="Mitoz, ökaryotik hücrelerde gerçekleşen hücre bölünmesi türüdür.",
                content="Mitoz süreci detayları...",
                url="https://tr.wikipedia.org/wiki/Mitoz",
                categories=["Biyoloji", "Hücre döngüsü"],
                images=["https://example.com/mitosis.jpg"],
                references=["ref3", "ref4"],
                language=language,
                last_modified=datetime.now(),
                word_count=2000,
                educational_relevance=0.95,
            ),
            WikipediaArticle(
                page_id=34567,
                title="Matematik",
                summary="Matematik, sayılar, yapılar, uzay ve değişim gibi konularla ilgilenen bilim dalıdır.",
                content="Matematik tarihi ve dalları...",
                url="https://tr.wikipedia.org/wiki/Matematik",
                categories=["Matematik", "Bilim"],
                images=["https://example.com/math.jpg"],
                references=["ref5", "ref6"],
                language=language,
                last_modified=datetime.now(),
                word_count=3000,
                educational_relevance=1.0,
            ),
        ]

        # Sorguya göre filtrele
        filtered = []
        query_lower = query.lower()
        for article in sample_articles:
            if (
                query_lower in article.title.lower()
                or query_lower in article.summary.lower()
            ):
                filtered.append(article)

        return filtered

    async def get_article(
        self, title: str, language: str = "tr", extract_length: int = 500
    ) -> WikipediaArticle | None:
        """
        Makale detaylarını getir

        Args:
            title: Makale başlığı
            language: Dil kodu
            extract_length: Özet uzunluğu

        Returns:
            Makale detayları
        """
        try:
            # API URL
            url = f"{self.base_urls[language]}/page/summary/{title}"

            # Simüle edilmiş veri
            article = WikipediaArticle(
                page_id=99999,
                title=title,
                summary=f"{title} hakkında özet bilgi...",
                content=f"{title} detaylı içerik...",
                url=f"https://{language}.wikipedia.org/wiki/{title}",
                categories=["Kategori1", "Kategori2"],
                images=[],
                references=[],
                language=language,
                last_modified=datetime.now(),
                word_count=1000,
                educational_relevance=self._calculate_educational_relevance(title),
            )

            logger.info(f"Retrieved Wikipedia article: {title}")
            return article

        except Exception as e:
            logger.error(f"Get article error: {e!s}")
            return None

    def _calculate_educational_relevance(self, title: str) -> float:
        """
        Eğitim ilgililik skorunu hesapla

        Args:
            title: Makale başlığı

        Returns:
            İlgililik skoru (0-1)
        """
        # Eğitimle ilgili anahtar kelimeler
        educational_keywords = [
            "matematik",
            "fizik",
            "kimya",
            "biyoloji",
            "tarih",
            "coğrafya",
            "edebiyat",
            "felsefe",
            "bilim",
            "teknoloji",
            "sanat",
            "müzik",
            "astronomi",
            "jeoloji",
            "psikoloji",
            "sosyoloji",
            "ekonomi",
            "hücre",
            "atom",
            "molekül",
            "denklem",
            "formül",
            "teori",
            "kanun",
            "ilke",
            "kural",
            "yöntem",
            "teknik",
            "algoritma",
        ]

        title_lower = title.lower()

        # Anahtar kelime eşleşmesi
        keyword_matches = sum(1 for kw in educational_keywords if kw in title_lower)
        keyword_score = min(keyword_matches / 3, 1.0)

        # Başlık uzunluğu (çok kısa veya çok uzun başlıklar genelde az eğitimsel)
        title_length = len(title.split())
        if 2 <= title_length <= 5:
            length_score = 1.0
        elif 1 <= title_length <= 7:
            length_score = 0.7
        else:
            length_score = 0.5

        # Final skor
        return keyword_score * 0.7 + length_score * 0.3

    async def get_article_sections(
        self, title: str, language: str = "tr"
    ) -> list[dict[str, Any]]:
        """
        Makale bölümlerini getir

        Args:
            title: Makale başlığı
            language: Dil kodu

        Returns:
            Bölüm listesi
        """
        try:
            # Simüle edilmiş bölümler
            sections = [
                {
                    "level": 1,
                    "title": "Giriş",
                    "content": "Giriş bölümü içeriği...",
                    "subsections": [],
                },
                {
                    "level": 1,
                    "title": "Tarihçe",
                    "content": "Tarihçe bölümü içeriği...",
                    "subsections": [
                        {
                            "level": 2,
                            "title": "Erken dönem",
                            "content": "Erken dönem detayları...",
                        }
                    ],
                },
                {
                    "level": 1,
                    "title": "Özellikler",
                    "content": "Özellikler bölümü içeriği...",
                    "subsections": [],
                },
            ]

            return sections

        except Exception as e:
            logger.error(f"Get sections error: {e!s}")
            return []

    async def get_related_articles(
        self, title: str, language: str = "tr", limit: int = 5
    ) -> list[str]:
        """
        İlgili makaleleri getir

        Args:
            title: Makale başlığı
            language: Dil kodu
            limit: Maksimum sayı

        Returns:
            İlgili makale başlıkları
        """
        try:
            # Simüle edilmiş ilgili makaleler
            related_map = {
                "Hücre bölünmesi": [
                    "Mitoz",
                    "Mayoz",
                    "Hücre döngüsü",
                    "DNA replikasyonu",
                ],
                "Matematik": [
                    "Cebir",
                    "Geometri",
                    "Analiz",
                    "İstatistik",
                    "Sayılar teorisi",
                ],
                "Fizik": [
                    "Mekanik",
                    "Termodinamik",
                    "Elektromanyetizma",
                    "Kuantum fiziği",
                ],
            }

            related = related_map.get(title, ["İlgili makale 1", "İlgili makale 2"])

            return related[:limit]

        except Exception as e:
            logger.error(f"Get related articles error: {e!s}")
            return []

    def extract_key_concepts(self, content: str) -> list[str]:
        """
        İçerikten anahtar kavramları çıkar

        Args:
            content: Makale içeriği

        Returns:
            Anahtar kavram listesi
        """
        try:
            # Basit bir yaklaşım: Büyük harfle başlayan kelimeler
            words = content.split()
            concepts = []

            for word in words:
                # Temizle
                clean_word = re.sub(r"[^\w\s]", "", word)

                # Büyük harfle başlayan ve en az 3 karakter
                if clean_word and clean_word[0].isupper() and len(clean_word) >= 3:
                    if clean_word not in concepts:
                        concepts.append(clean_word)

            # En sık geçenleri al
            return concepts[:20]

        except Exception as e:
            logger.error(f"Extract concepts error: {e!s}")
            return []

    def simplify_content(self, content: str, target_level: str = "beginner") -> str:
        """
        İçeriği basitleştir

        Args:
            content: Orijinal içerik
            target_level: Hedef seviye

        Returns:
            Basitleştirilmiş içerik
        """
        try:
            # Basit bir yaklaşım
            sentences = content.split(".")
            simplified = []

            for sentence in sentences:
                words = sentence.split()

                # Çok uzun cümleleri böl
                if len(words) > 20:
                    # İlk 15 kelimeyi al
                    simplified.append(" ".join(words[:15]) + ".")
                    # Kalanı ekle
                    if len(words) > 15:
                        simplified.append(" ".join(words[15:]) + ".")
                else:
                    simplified.append(sentence + ".")

            result = " ".join(simplified)

            # Karmaşık kelimeleri basitleştir (örnek)
            replacements = {
                "münasebetiyle": "nedeniyle",
                "ehemmiyetli": "önemli",
                "vasıtasıyla": "aracılığıyla",
                "muktedir": "güçlü",
                "mütemadiyen": "sürekli",
            }

            for old, new in replacements.items():
                result = result.replace(old, new)

            return result

        except Exception as e:
            logger.error(f"Simplify content error: {e!s}")
            return content

    async def get_daily_featured(
        self, language: str = "tr"
    ) -> WikipediaArticle | None:
        """
        Günün öne çıkan makalesini getir

        Args:
            language: Dil kodu

        Returns:
            Öne çıkan makale
        """
        try:
            # Simüle edilmiş öne çıkan makale
            return WikipediaArticle(
                page_id=11111,
                title="Günün Makalesi: Güneş Sistemi",
                summary="Güneş Sistemi, Güneş'in kütleçekim etkisi altında bulunan gök cisimlerinin oluşturduğu sistemdir.",
                content="Detaylı içerik...",
                url=f"https://{language}.wikipedia.org/wiki/Güneş_Sistemi",
                categories=["Astronomi", "Güneş Sistemi"],
                images=["solar_system.jpg"],
                references=[],
                language=language,
                last_modified=datetime.now(),
                word_count=2500,
                educational_relevance=0.95,
            )

        except Exception as e:
            logger.error(f"Get daily featured error: {e!s}")
            return None

    async def search_by_category(
        self, category: str, language: str = "tr", limit: int = 10
    ) -> list[WikipediaArticle]:
        """
        Kategoriye göre makale ara

        Args:
            category: Kategori adı
            language: Dil kodu
            limit: Maksimum sayı

        Returns:
            Makale listesi
        """
        try:
            # Kategori haritası
            category_map = {
                "matematik": ["Matematik", "Cebir", "Geometri", "Analiz"],
                "fizik": ["Fizik", "Mekanik", "Termodinamik", "Optik"],
                "kimya": ["Kimya", "Organik kimya", "İnorganik kimya"],
                "biyoloji": ["Biyoloji", "Hücre biyolojisi", "Genetik", "Ekoloji"],
                "tarih": ["Tarih", "Osmanlı tarihi", "Türk tarihi", "Dünya tarihi"],
                "coğrafya": ["Coğrafya", "Fiziki coğrafya", "Beşeri coğrafya"],
            }

            titles = category_map.get(category.lower(), [category])
            articles = []

            for title in titles[:limit]:
                article = await self.get_article(title, language)
                if article:
                    articles.append(article)

            return articles

        except Exception as e:
            logger.error(f"Search by category error: {e!s}")
            return []


# Singleton instance
wikipedia_service = WikipediaService()
