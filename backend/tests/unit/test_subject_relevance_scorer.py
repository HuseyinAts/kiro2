"""
Subject Relevance Scorer Unit Tests
Video içeriğinin ders ve konu ile uygunluğunu skorlayan servisi test eder
All external dependencies are mocked.
"""

import os

import pytest

from services.subject_relevance_scorer import (
    RelevanceScore,
    SubjectRelevanceScorer,
)


class TestSubjectRelevanceScorer:
    """Subject Relevance Scorer test sınıfı"""

    @pytest.fixture
    def scorer_service(self):
        """Test için scorer instance'ı oluştur - mock SentenceTransformer"""
        # Ensure TESTING env var is set to prevent model loading
        os.environ["TESTING"] = "true"

        # Create scorer instance (should skip model loading due to TESTING=true)
        scorer = SubjectRelevanceScorer()

        # Double-check that model wasn't loaded
        assert scorer._sentence_transformers_available is False
        assert scorer._model is None

        return scorer

    # ==================== Yüksek Uygunluk Skorlama Testleri ====================

    @pytest.mark.asyncio
    async def test_high_relevance_matematik_turev(self, scorer_service):
        """Matematik türev konusu için yüksek uygunluk skoru"""
        result = await scorer_service.calculate_relevance_score(
            video_title="Matematik Türev Konu Anlatımı - Türev Alma Kuralları",
            video_description="Bu videoda türev konusunu detaylı şekilde işliyoruz. Türev alma kuralları, diferansiyel hesaplama ve teğet eğimi konularını örneklerle açıklıyoruz.",
            video_tags=["matematik", "türev", "diferansiyel", "konu anlatımı"],
            target_subject="matematik",
            target_topic="türev",
        )

        assert result.overall_score >= 0.7  # Semantic similarity olmadan 0.7+ yeterli
        assert result.subject_match >= 0.7
        assert result.topic_match >= 0.7
        assert result.keyword_overlap >= 0.5

    @pytest.mark.asyncio
    async def test_high_relevance_fizik_hareket(self, scorer_service):
        """Fizik hareket konusu için yüksek uygunluk skoru"""
        result = await scorer_service.calculate_relevance_score(
            video_title="Fizik Hareket Konusu - Hız İvme Hesaplamaları",
            video_description="Fizik dersinde hareket konusunu işliyoruz. Hız, ivme, yol ve zaman hesaplamaları. Kinematik problemleri çözüyoruz.",
            video_tags=["fizik", "hareket", "hız", "ivme", "kinematik"],
            target_subject="fizik",
            target_topic="hareket",
        )

        assert result.overall_score >= 0.7
        assert result.subject_match >= 0.6
        assert result.topic_match >= 0.6

    @pytest.mark.asyncio
    async def test_high_relevance_kimya_atom(self, scorer_service):
        """Kimya atom konusu için yüksek uygunluk skoru"""
        result = await scorer_service.calculate_relevance_score(
            video_title="Kimya Atom Yapısı - Proton Nötron Elektron",
            video_description="Atom yapısını öğreniyoruz. Proton, nötron, elektron ve periyodik tablo konularını işliyoruz.",
            video_tags=["kimya", "atom", "proton", "elektron", "periyodik"],
            target_subject="kimya",
            target_topic="atom",
        )

        assert result.overall_score >= 0.7
        assert result.subject_match >= 0.6
        assert result.topic_match >= 0.6

    @pytest.mark.asyncio
    async def test_high_relevance_without_topic(self, scorer_service):
        """Konu belirtilmeden yüksek uygunluk skoru"""
        result = await scorer_service.calculate_relevance_score(
            video_title="Matematik Dersi - Sayılar ve Fonksiyonlar",
            video_description="Matematik dersinde sayılar, fonksiyonlar ve cebir konularını işliyoruz.",
            video_tags=["matematik", "sayı", "fonksiyon", "cebir"],
            target_subject="matematik",
            target_topic=None,
        )

        # Konu belirtilmediği için topic_match 0.5 olmalı (nötr)
        assert result.overall_score >= 0.6
        assert result.subject_match >= 0.7
        assert result.topic_match == 0.5  # Nötr skor

    @pytest.mark.asyncio
    async def test_high_relevance_multiple_keywords(self, scorer_service):
        """Çoklu anahtar kelime ile yüksek uygunluk"""
        result = await scorer_service.calculate_relevance_score(
            video_title="Matematik İntegral - Alan Hacim Hesaplama",
            video_description="İntegral konusunu işliyoruz. Belirsiz integral, belirli integral, alan ve hacim hesaplamaları. İntegrasyon teknikleri.",
            video_tags=[
                "matematik",
                "integral",
                "alan",
                "hacim",
                "belirsiz",
                "belirli",
            ],
            target_subject="matematik",
            target_topic="integral",
        )

        assert result.overall_score >= 0.5
        assert result.keyword_overlap >= 0.5

    # ==================== Düşük Uygunluk Filtreleme Testleri ====================

    @pytest.mark.asyncio
    async def test_low_relevance_wrong_subject(self, scorer_service):
        """Yanlış ders için düşük uygunluk skoru"""
        result = await scorer_service.calculate_relevance_score(
            video_title="Fizik Hareket Konusu",
            video_description="Fizik dersinde hareket, hız ve ivme konularını işliyoruz.",
            video_tags=["fizik", "hareket", "hız"],
            target_subject="matematik",
            target_topic="türev",
        )

        assert result.overall_score < 0.4
        assert result.subject_match < 0.5

    @pytest.mark.asyncio
    async def test_low_relevance_wrong_topic(self, scorer_service):
        """Yanlış konu için düşük uygunluk skoru"""
        result = await scorer_service.calculate_relevance_score(
            video_title="Matematik Geometri - Üçgenler",
            video_description="Geometri konusunda üçgenler, açılar ve alan hesaplamaları.",
            video_tags=["matematik", "geometri", "üçgen"],
            target_subject="matematik",
            target_topic="türev",
        )

        # Ders doğru ama konu yanlış
        assert result.overall_score < 0.6
        assert result.subject_match >= 0.5  # Ders eşleşiyor
        assert result.topic_match < 0.5  # Konu eşleşmiyor

    @pytest.mark.asyncio
    async def test_low_relevance_no_keywords(self, scorer_service):
        """Anahtar kelime olmadan düşük uygunluk"""
        result = await scorer_service.calculate_relevance_score(
            video_title="Eğitim Videosu",
            video_description="Genel eğitim içeriği",
            video_tags=["eğitim", "video"],
            target_subject="matematik",
            target_topic="türev",
        )

        assert result.overall_score < 0.4
        assert result.keyword_overlap < 0.3

    @pytest.mark.asyncio
    async def test_low_relevance_unrelated_content(self, scorer_service):
        """İlgisiz içerik için düşük uygunluk"""
        result = await scorer_service.calculate_relevance_score(
            video_title="Yemek Tarifi - Kek Yapımı",
            video_description="Bu videoda kek tarifi anlatıyoruz.",
            video_tags=["yemek", "tarif", "kek"],
            target_subject="matematik",
            target_topic="türev",
        )

        assert result.overall_score < 0.2
        assert result.subject_match < 0.3
        assert result.topic_match < 0.3

    @pytest.mark.asyncio
    async def test_low_relevance_partial_match(self, scorer_service):
        """Kısmi eşleşme ile düşük uygunluk"""
        result = await scorer_service.calculate_relevance_score(
            video_title="Matematik Dersi",
            video_description="Genel matematik konuları",
            video_tags=["matematik"],
            target_subject="matematik",
            target_topic="türev",
        )

        # Ders adı var ama detay yok
        assert result.overall_score < 0.7
        assert result.keyword_overlap < 0.5

    # ==================== Konu-Video Eşleştirme Testleri ====================

    @pytest.mark.asyncio
    async def test_subject_video_matching_matematik(self, scorer_service):
        """Matematik dersi video eşleştirme"""
        result = await scorer_service.calculate_relevance_score(
            video_title="TYT Matematik - Fonksiyonlar",
            video_description="Fonksiyon grafikleri ve denklem çözme",
            video_tags=["matematik", "fonksiyon", "tyt"],
            target_subject="matematik",
            target_topic="fonksiyon",
        )

        assert result.overall_score >= 0.6
        assert result.subject_match >= 0.5
        assert result.topic_match >= 0.5

    @pytest.mark.asyncio
    async def test_subject_video_matching_fizik(self, scorer_service):
        """Fizik dersi video eşleştirme"""
        result = await scorer_service.calculate_relevance_score(
            video_title="Fizik Enerji Konusu",
            video_description="İş, güç, potansiyel ve kinetik enerji",
            video_tags=["fizik", "enerji", "iş", "güç"],
            target_subject="fizik",
            target_topic="enerji",
        )

        assert result.overall_score >= 0.6
        assert result.subject_match >= 0.5

    @pytest.mark.asyncio
    async def test_subject_video_matching_kimya(self, scorer_service):
        """Kimya dersi video eşleştirme"""
        result = await scorer_service.calculate_relevance_score(
            video_title="Kimya Reaksiyonlar",
            video_description="Asit baz reaksiyonları ve oksidasyon",
            video_tags=["kimya", "reaksiyon", "asit", "baz"],
            target_subject="kimya",
            target_topic="reaksiyon",
        )

        assert result.overall_score >= 0.6

    @pytest.mark.asyncio
    async def test_subject_video_matching_biyoloji(self, scorer_service):
        """Biyoloji dersi video eşleştirme"""
        result = await scorer_service.calculate_relevance_score(
            video_title="Biyoloji Hücre Yapısı",
            video_description="Hücre organelleri ve çekirdek yapısı",
            video_tags=["biyoloji", "hücre", "organelle"],
            target_subject="biyoloji",
            target_topic="hücre",
        )

        assert result.overall_score >= 0.6

    @pytest.mark.asyncio
    async def test_subject_video_matching_cross_subject(self, scorer_service):
        """Çapraz ders eşleştirme (negatif test)"""
        result = await scorer_service.calculate_relevance_score(
            video_title="Tarih Osmanlı Dönemi",
            video_description="Osmanlı İmparatorluğu tarihi",
            video_tags=["tarih", "osmanlı"],
            target_subject="matematik",
            target_topic="türev",
        )

        assert result.overall_score < 0.3

    @pytest.mark.asyncio
    async def test_subject_video_matching_with_exam_keywords(self, scorer_service):
        """Sınav anahtar kelimeleri ile eşleştirme"""
        result = await scorer_service.calculate_relevance_score(
            video_title="TYT Matematik Limit Konusu",
            video_description="TYT sınavı için limit konusu anlatımı. Süreklilik ve yakınsama.",
            video_tags=["tyt", "matematik", "limit", "sınav"],
            target_subject="matematik",
            target_topic="limit",
        )

        assert result.overall_score >= 0.6
        assert result.topic_match >= 0.5

    # ==================== Anahtar Kelime Örtüşme Testleri ====================

    def test_keyword_overlap_high(self, scorer_service):
        """Yüksek anahtar kelime örtüşme"""
        video_text = "matematik türev diferansiyel eğim teğet türev alma kuralları"
        score = scorer_service._calculate_keyword_overlap(
            video_text, "matematik", "türev"
        )

        assert score >= 0.5

    def test_keyword_overlap_medium(self, scorer_service):
        """Orta anahtar kelime örtüşme"""
        video_text = "matematik fonksiyon grafik"
        score = scorer_service._calculate_keyword_overlap(
            video_text, "matematik", "türev"
        )

        assert 0.1 <= score <= 0.5

    def test_keyword_overlap_low(self, scorer_service):
        """Düşük anahtar kelime örtüşme"""
        video_text = "genel eğitim videosu"
        score = scorer_service._calculate_keyword_overlap(
            video_text, "matematik", "türev"
        )

        assert score < 0.4

    def test_keyword_overlap_no_topic(self, scorer_service):
        """Konu olmadan anahtar kelime örtüşme"""
        video_text = "matematik sayı fonksiyon cebir"
        score = scorer_service._calculate_keyword_overlap(video_text, "matematik", None)

        # Konu yok, kısmi puan almalı
        assert score >= 0.4

    def test_keyword_overlap_unknown_subject(self, scorer_service):
        """Bilinmeyen ders için anahtar kelime örtüşme"""
        video_text = "test video content"
        score = scorer_service._calculate_keyword_overlap(
            video_text, "unknown_subject", None
        )

        # Bilinmeyen ders, düşük skor
        assert score <= 0.3

    # ==================== Ders Eşleşme Testleri ====================

    def test_subject_match_direct_name(self, scorer_service):
        """Ders adı direkt geçiyor"""
        video_text = "matematik dersi konu anlatımı"
        score = scorer_service._calculate_subject_match(video_text, "matematik")

        assert score >= 0.5

    def test_subject_match_core_keywords(self, scorer_service):
        """Core keywords ile ders eşleşme"""
        video_text = "sayı fonksiyon türev integral limit"
        score = scorer_service._calculate_subject_match(video_text, "matematik")

        # Çoklu core keyword
        assert score >= 0.3

    def test_subject_match_related_words(self, scorer_service):
        """İlgili kelimeler ile ders eşleşme"""
        video_text = "sayısal problem hesaplama"
        score = scorer_service._calculate_subject_match(video_text, "matematik")

        assert score > 0.0

    def test_subject_match_no_match(self, scorer_service):
        """Eşleşme olmayan durum"""
        video_text = "yemek tarifi kek yapımı"
        score = scorer_service._calculate_subject_match(video_text, "matematik")

        assert score < 0.3

    # ==================== Konu Eşleşme Testleri ====================

    def test_topic_match_direct_name(self, scorer_service):
        """Konu adı direkt geçiyor"""
        video_text = "türev konusu anlatımı"
        score = scorer_service._calculate_topic_match(video_text, "matematik", "türev")

        assert score >= 0.6

    def test_topic_match_keywords(self, scorer_service):
        """Konu anahtar kelimeleri ile eşleşme"""
        video_text = "diferansiyel eğim teğet türev alma"
        score = scorer_service._calculate_topic_match(video_text, "matematik", "türev")

        assert score >= 0.5

    def test_topic_match_no_topic(self, scorer_service):
        """Konu belirtilmemiş"""
        video_text = "matematik dersi"
        score = scorer_service._calculate_topic_match(video_text, "matematik", None)

        # Nötr skor
        assert score == 0.5

    def test_topic_match_wrong_topic(self, scorer_service):
        """Yanlış konu"""
        video_text = "geometri üçgen açı"
        score = scorer_service._calculate_topic_match(video_text, "matematik", "türev")

        assert score < 0.5

    # ==================== Yardımcı Metodlar Testleri ====================

    def test_get_subject_keywords(self, scorer_service):
        """Ders anahtar kelimelerini alma"""
        keywords = scorer_service.get_subject_keywords("matematik")

        assert keywords is not None
        assert "core" in keywords
        assert "topics" in keywords
        assert len(keywords["core"]) > 0

    def test_get_topic_keywords(self, scorer_service):
        """Konu anahtar kelimelerini alma"""
        keywords = scorer_service.get_topic_keywords("matematik", "türev")

        assert isinstance(keywords, list)
        assert len(keywords) > 0
        assert "türev" in keywords or "diferansiyel" in keywords

    def test_get_all_subjects(self, scorer_service):
        """Tüm dersleri alma"""
        subjects = scorer_service.get_all_subjects()

        assert isinstance(subjects, list)
        assert len(subjects) > 0
        assert "matematik" in subjects
        assert "fizik" in subjects
        assert "kimya" in subjects

    def test_get_topics_for_subject(self, scorer_service):
        """Ders için konuları alma"""
        topics = scorer_service.get_topics_for_subject("matematik")

        assert isinstance(topics, list)
        assert len(topics) > 0
        assert "türev" in topics
        assert "integral" in topics

    def test_get_topics_for_unknown_subject(self, scorer_service):
        """Bilinmeyen ders için konuları alma"""
        topics = scorer_service.get_topics_for_subject("unknown_subject")

        assert isinstance(topics, list)
        assert len(topics) == 0

    # ==================== Edge Case Testleri ====================

    @pytest.mark.asyncio
    async def test_empty_inputs(self, scorer_service):
        """Boş girdi testi"""
        result = await scorer_service.calculate_relevance_score(
            video_title="",
            video_description="",
            video_tags=[],
            target_subject="matematik",
            target_topic="türev",
        )

        assert result.overall_score < 0.3
        assert isinstance(result, RelevanceScore)

    @pytest.mark.asyncio
    async def test_very_long_text(self, scorer_service):
        """Çok uzun metin testi"""
        long_text = "matematik türev " * 500
        result = await scorer_service.calculate_relevance_score(
            video_title="Test",
            video_description=long_text,
            video_tags=["matematik"],
            target_subject="matematik",
            target_topic="türev",
        )

        # Uzun metin handle edilmeli
        assert isinstance(result, RelevanceScore)
        assert 0.0 <= result.overall_score <= 1.0

    @pytest.mark.asyncio
    async def test_special_characters(self, scorer_service):
        """Özel karakterler testi"""
        result = await scorer_service.calculate_relevance_score(
            video_title="Matematik!!! Türev??? @#$%",
            video_description="Türev konusu... !!!",
            video_tags=["matematik", "türev"],
            target_subject="matematik",
            target_topic="türev",
        )

        # Özel karakterler skoru etkilememeli
        assert result.overall_score >= 0.5

    @pytest.mark.asyncio
    async def test_case_insensitive_matching(self, scorer_service):
        """Büyük/küçük harf duyarsız eşleştirme"""
        result = await scorer_service.calculate_relevance_score(
            video_title="MATEMATİK TÜREV KONU ANLATIMI",
            video_description="TÜREV ALMA KURALLARI",
            video_tags=["MATEMATİK", "TÜREV"],
            target_subject="matematik",
            target_topic="türev",
        )

        # Büyük harfler küçük harfe çevrilmeli
        assert result.overall_score >= 0.4

    @pytest.mark.asyncio
    async def test_unicode_characters(self, scorer_service):
        """Unicode karakterler testi"""
        result = await scorer_service.calculate_relevance_score(
            video_title="Matematik Türev Çözüm Öğrenci İçin",
            video_description="Türkçe karakterler: ç ğ ı ö ş ü",
            video_tags=["matematik", "türev"],
            target_subject="matematik",
            target_topic="türev",
        )

        # Unicode karakterler handle edilmeli
        assert isinstance(result, RelevanceScore)
        assert result.overall_score >= 0.5

    # ==================== Performans Testleri ====================

    @pytest.mark.asyncio
    async def test_multiple_scorings_performance(self, scorer_service):
        """Çoklu skorlama performans testi"""
        test_cases = [
            (
                "Matematik Türev",
                "Türev konusu",
                ["matematik", "türev"],
                "matematik",
                "türev",
            ),
            (
                "Fizik Hareket",
                "Hareket konusu",
                ["fizik", "hareket"],
                "fizik",
                "hareket",
            ),
            ("Kimya Atom", "Atom yapısı", ["kimya", "atom"], "kimya", "atom"),
            (
                "Biyoloji Hücre",
                "Hücre yapısı",
                ["biyoloji", "hücre"],
                "biyoloji",
                "hücre",
            ),
            (
                "Tarih Osmanlı",
                "Osmanlı dönemi",
                ["tarih", "osmanlı"],
                "tarih",
                "osmanlı",
            ),
        ]

        results = []
        for title, desc, tags, subject, topic in test_cases:
            result = await scorer_service.calculate_relevance_score(
                title, desc, tags, subject, topic
            )
            results.append(result)

        # Tüm sonuçlar başarıyla dönmeli
        assert len(results) == len(test_cases)
        assert all(isinstance(r, RelevanceScore) for r in results)
        assert all(0.0 <= r.overall_score <= 1.0 for r in results)

    # ==================== Integration Testleri ====================

    @pytest.mark.asyncio
    async def test_real_world_high_relevance(self, scorer_service):
        """Gerçek dünya yüksek uygunluk örneği"""
        result = await scorer_service.calculate_relevance_score(
            video_title="TYT Matematik - Türev Konu Anlatımı ve Soru Çözümü",
            video_description="Bu videomuzda TYT matematik müfredatındaki türev konusunu işliyoruz. Türev alma kuralları, diferansiyel hesaplama, teğet eğimi ve türev uygulamaları. Öğrencilerimiz için hazırladığımız çözümlü örnekler ile konuyu pekiştiriyoruz.",
            video_tags=[
                "tyt",
                "matematik",
                "türev",
                "diferansiyel",
                "konu anlatımı",
                "soru çözümü",
            ],
            target_subject="matematik",
            target_topic="türev",
        )

        assert result.overall_score >= 0.5
        assert result.subject_match >= 0.5
        assert result.topic_match >= 0.5
        assert result.keyword_overlap >= 0.5

    @pytest.mark.asyncio
    async def test_real_world_low_relevance(self, scorer_service):
        """Gerçek dünya düşük uygunluk örneği"""
        result = await scorer_service.calculate_relevance_score(
            video_title="Yemek Tarifi - Çikolatalı Kek Nasıl Yapılır",
            video_description="Bu videoda çikolatalı kek tarifini anlatıyoruz. Malzemeler ve yapılışı adım adım gösteriyoruz.",
            video_tags=["yemek", "tarif", "kek", "çikolata"],
            target_subject="matematik",
            target_topic="türev",
        )

        assert result.overall_score < 0.3
        assert result.subject_match < 0.3
        assert result.topic_match < 0.3

    @pytest.mark.asyncio
    async def test_real_world_partial_relevance(self, scorer_service):
        """Gerçek dünya kısmi uygunluk örneği"""
        result = await scorer_service.calculate_relevance_score(
            video_title="Matematik Dersi - Genel Konu Tekrarı",
            video_description="Matematik dersinde genel konu tekrarı yapıyoruz. Sayılar, fonksiyonlar ve geometri.",
            video_tags=["matematik", "konu tekrarı", "genel"],
            target_subject="matematik",
            target_topic="türev",
        )

        # Ders doğru ama konu spesifik değil
        assert 0.4 <= result.overall_score <= 0.7
        assert result.subject_match >= 0.5
        assert result.topic_match < 0.6

    # ==================== Skor Bileşenleri Testleri ====================

    @pytest.mark.asyncio
    async def test_score_components_balance(self, scorer_service):
        """Skor bileşenlerinin dengesi"""
        result = await scorer_service.calculate_relevance_score(
            video_title="Matematik Türev Konusu",
            video_description="Türev alma kuralları ve diferansiyel hesaplama",
            video_tags=["matematik", "türev"],
            target_subject="matematik",
            target_topic="türev",
        )

        # Tüm bileşenler 0-1 arasında olmalı
        assert 0.0 <= result.subject_match <= 1.0
        assert 0.0 <= result.topic_match <= 1.0
        assert 0.0 <= result.keyword_overlap <= 1.0
        assert 0.0 <= result.semantic_similarity <= 1.0
        assert 0.0 <= result.overall_score <= 1.0

    @pytest.mark.asyncio
    async def test_score_components_contribution(self, scorer_service):
        """Skor bileşenlerinin katkısı"""
        result = await scorer_service.calculate_relevance_score(
            video_title="Matematik Türev",
            video_description="Türev konusu",
            video_tags=["matematik", "türev"],
            target_subject="matematik",
            target_topic="türev",
        )

        # Overall score, bileşenlerin ağırlıklı ortalaması olmalı
        # keyword_overlap * 0.40 + subject_match * 0.25 + topic_match * 0.20 + semantic * 0.15
        expected_score = (
            result.keyword_overlap * 0.40
            + result.subject_match * 0.25
            + result.topic_match * 0.20
            + result.semantic_similarity * 0.15
        )

        # Floating point toleransı ile karşılaştır
        assert abs(result.overall_score - expected_score) < 0.01
