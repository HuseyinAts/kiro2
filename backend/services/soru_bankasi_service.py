"""
Soru bankası yönetimi servisi
Gelişmiş IRT parametreli soru seçimi ve database entegrasyonu ile
"""

import logging
import math
import random
import unicodedata
from datetime import datetime

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

# PERFORMANCE: Redis cache integration
from core.cache import cache_manager
from core.database import db_manager
from models import SinavTipi
from models.database import ExamType, QuestionDifficulty, SubjectArea
from models.question_bank import QuestionBankItem as Question
from models.question_bank import TopicHierarchy
from services.irt_analysis_service import IRTAnalysisService

logger = logging.getLogger(__name__)

# Türkçe → UPPERCASE konu dönüşüm haritası (DRY: tek tanım)
_KONU_MAP: dict[str, str] = {
    "Matematik": "MATEMATIK",
    "matematik": "MATEMATIK",
    "Mat": "MATEMATIK",
    "mat": "MATEMATIK",
    "Türkçe": "TURKCE",
    "turkce": "TURKCE",
    "Turkce": "TURKCE",
    "Fizik": "FIZIK",
    "fizik": "FIZIK",
    "Fiz": "FIZIK",
    "fiz": "FIZIK",
    "Kimya": "KIMYA",
    "kimya": "KIMYA",
    "Kim": "KIMYA",
    "kim": "KIMYA",
    "Biyoloji": "BIYOLOJI",
    "biyoloji": "BIYOLOJI",
    "Bio": "BIYOLOJI",
    "bio": "BIYOLOJI",
    "Geometri": "GEOMETRI",
    "geometri": "GEOMETRI",
    "Geo": "GEOMETRI",
    "geo": "GEOMETRI",
    "Fen": "FEN",
    "fen": "FEN",
    "Fen Bilimleri": "FEN",
    "fen bilimleri": "FEN",
    "Sosyal": "SOSYAL",
    "sosyal": "SOSYAL",
    "Sosyal Bilimler": "SOSYAL",
    "sosyal bilimler": "SOSYAL",
    "Tarih": "TARIH",
    "tarih": "TARIH",
    "Coğrafya": "COGRAFYA",
    "coğrafya": "COGRAFYA",
    "cografya": "COGRAFYA",
    "Cografya": "COGRAFYA",
    "Edebiyat": "EDEBIYAT",
    "edebiyat": "EDEBIYAT",
    "İngilizce": "INGILIZCE",
    "ingilizce": "INGILIZCE",
    "Ing": "INGILIZCE",
    "ing": "INGILIZCE",
}


def _normalize_topic(topic: str) -> str:
    """
    Türkçe konu adını normalize eder.

    - NFC unicode normalization (karakter birleşimlerini korur)
    - Türkçe lowercase: İ→i, I→ı
    - NOT: ASCII'ye dönüştürme - Türkçe karakterleri koru!
    """
    if not topic:
        return ""

    # NFC normalize (Türkçe karakterler için)
    text = unicodedata.normalize("NFC", topic)

    # Türkçe lowercase mapping (İ→i, I→ı)
    text = text.replace("İ", "i").replace("I", "ı")
    text = text.lower()

    # NOT: ASCII conversion - keep Turkish chars!
    # The DB has Turkish chars, so we need to match them

    return text


class SoruBankasiServisi:
    """
    Gelişmiş soru bankası yönetimi servisi
    - Database entegrasyonu
    - IRT parametreli soru seçimi
    - Adaptif zorluk ayarlama
    - Konu bazlı dağılım algoritması
    """

    def __init__(self) -> None:
        """Soru bankası servisini başlatır."""
        self.irt_service = IRTAnalysisService()

        # IRT parametreleri için varsayılan değerler
        self.default_irt_params = {
            "difficulty_range": (-3.0, 3.0),
            "discrimination_range": (0.5, 2.5),
            "guessing_parameter": 0.25,  # 4 seçenekli sorular için
            "target_information": 1.0,  # Hedef bilgi fonksiyonu değeri
        }

        # Konu dağılım şablonları (ÖSYM standartlarına göre)
        self.konu_dagilim_sablonlari = {
            SinavTipi.TYT: {"Matematik": 40, "Türkçe": 40, "Fen": 20, "Sosyal": 20},
            SinavTipi.AYT: {"Matematik": 40, "Fizik": 14, "Kimya": 13, "Biyoloji": 13},
            SinavTipi.YDT: {"İngilizce": 80},
        }

    async def _enum_donusturucu(
        self, exam_type: str, difficulty: str, subject: str
    ) -> tuple[ExamType, QuestionDifficulty, SubjectArea]:
        """Enum dönüştürücü yardımcı fonksiyonu"""
        # ExamType dönüştürme
        exam_type_map = {"TYT": ExamType.TYT, "AYT": ExamType.AYT, "YDT": ExamType.YDT}

        # QuestionDifficulty dönüştürme
        difficulty_map = {
            "kolay": QuestionDifficulty.EASY,
            "orta": QuestionDifficulty.MEDIUM,
            "zor": QuestionDifficulty.HARD,
        }

        # SubjectArea dönüştürme
        subject_map = {
            "Matematik": SubjectArea.MATEMATIK,
            "Türkçe": SubjectArea.TURKCE,
            "Fen": SubjectArea.FEN,
            "Sosyal": SubjectArea.SOSYAL,
            "Fizik": SubjectArea.FIZIK,
            "Kimya": SubjectArea.KIMYA,
            "Biyoloji": SubjectArea.BIYOLOJI,
            "İngilizce": SubjectArea.INGILIZCE,
        }

        return (
            exam_type_map.get(exam_type, ExamType.TYT),
            difficulty_map.get(difficulty, QuestionDifficulty.MEDIUM),
            subject_map.get(subject, SubjectArea.MATEMATIK),
        )

    async def soru_ekle(self, soru_data: dict) -> Question:
        """
        Yeni soru ekle - Database entegrasyonu ile

        Args:
            soru_data: Soru bilgileri dictionary

        Returns:
            Question: Oluşturulan soru objesi
        """
        async with db_manager.get_session() as session:
            try:
                # Enum dönüştürmeleri
                exam_type, difficulty, subject_area = await self._enum_donusturucu(
                    soru_data.get("sinav_tipi", "TYT"),
                    soru_data.get("zorluk_seviyesi", "orta"),
                    soru_data.get("konu", "Matematik"),
                )

                # IRT parametrelerini hesapla
                irt_params = await self._hesapla_irt_parametreleri(
                    difficulty.value, soru_data.get("konu", "Matematik")
                )

                # Yeni soru oluştur
                yeni_soru = Question(
                    question_text=soru_data["soru_metni"],
                    option_a=soru_data["secenekler"][0].replace("A) ", ""),
                    option_b=soru_data["secenekler"][1].replace("B) ", ""),
                    option_c=soru_data["secenekler"][2].replace("C) ", ""),
                    option_d=soru_data["secenekler"][3].replace("D) ", ""),
                    option_e=soru_data["secenekler"][4].replace("E) ", "")
                    if len(soru_data["secenekler"]) > 4
                    else None,
                    correct_answer=soru_data["dogru_cevap"],
                    explanation=soru_data.get("cozum_aciklamasi"),
                    exam_type=exam_type,
                    subject_area=subject_area,
                    topic=soru_data.get("konu", "Genel"),
                    subtopic=soru_data.get("alt_konu"),
                    difficulty=difficulty,
                    irt_difficulty=irt_params["difficulty"],
                    irt_discrimination=irt_params["discrimination"],
                    irt_guessing=irt_params["guessing"],
                    morphology_complexity=await self._hesapla_morfoloji_karmasikligi(
                        soru_data["soru_metni"]
                    ),
                    readability_score=await self._hesapla_okunabilirlik(
                        soru_data["soru_metni"]
                    ),
                    created_by=soru_data.get("created_by"),
                )

                session.add(yeni_soru)
                await session.commit()
                await session.refresh(yeni_soru)

                return yeni_soru

            except Exception as e:
                await session.rollback()
                raise Exception(f"Soru eklenirken hata oluştu: {e!s}")

    async def _hesapla_irt_parametreleri(
        self, zorluk: str, konu: str
    ) -> dict[str, float]:
        """IRT parametrelerini hesapla"""
        # Zorluk seviyesine göre IRT difficulty parametresi
        zorluk_map = {"easy": -1.0, "medium": 0.0, "hard": 1.0}

        # Konu bazlı ayarlama
        konu_ayarlama = {
            "Matematik": 0.2,
            "Fizik": 0.3,
            "Kimya": 0.1,
            "Türkçe": -0.1,
            "İngilizce": 0.0,
        }

        base_difficulty = zorluk_map.get(zorluk, 0.0)
        konu_bonus = konu_ayarlama.get(konu, 0.0)

        return {
            "difficulty": base_difficulty + konu_bonus,
            "discrimination": random.uniform(
                0.8, 2.0
            ),  # Gerçek verilerle kalibre edilecek
            "guessing": 0.25,  # 4 seçenekli sorular için
        }

    async def _hesapla_morfoloji_karmasikligi(self, metin: str) -> float:
        """Türkçe morfolojik karmaşıklık hesapla"""
        # Basit implementasyon - gerçek Zemberek entegrasyonu ile geliştirilecek
        kelime_sayisi = len(metin.split())
        ortalama_kelime_uzunlugu = (
            sum(len(kelime) for kelime in metin.split()) / kelime_sayisi
        )

        # Karmaşık yapıları tespit et
        karmasik_yapilar = ["-dığı", "-diği", "-duğu", "-düğü", "-arak", "-erek"]
        karmasiklik_skoru = sum(1 for yapi in karmasik_yapilar if yapi in metin)

        # 0-1 arası normalize et
        return min(1.0, (ortalama_kelime_uzunlugu / 10 + karmasiklik_skoru / 5))

    async def _hesapla_okunabilirlik(self, metin: str) -> float:
        """Türkçe okunabilirlik skoru hesapla"""
        # Basit Flesch-Kincaid benzeri hesaplama
        cumle_sayisi = metin.count(".") + metin.count("!") + metin.count("?")
        if cumle_sayisi == 0:
            cumle_sayisi = 1

        kelime_sayisi = len(metin.split())
        hece_sayisi = sum(self._hece_say(kelime) for kelime in metin.split())

        # Türkçe için uyarlanmış formül
        okunabilirlik = (
            206.835
            - (1.015 * (kelime_sayisi / cumle_sayisi))
            - (84.6 * (hece_sayisi / kelime_sayisi))
        )

        # 0-1 arası normalize et
        return max(0.0, min(1.0, okunabilirlik / 100))

    def _hece_say(self, kelime: str) -> int:
        """Basit hece sayma algoritması"""
        sesli_harfler = "aeiouüöıAEIOUÜÖI"
        hece_sayisi = sum(1 for harf in kelime if harf in sesli_harfler)
        return max(1, hece_sayisi)  # En az 1 hece

    async def soru_getir(self, soru_id: str) -> Question | None:
        """Soru ID ile soru getir - Database'den (with cache)"""
        # PERFORMANCE: Check cache first
        cache_key = f"soru:{soru_id}"
        cached_soru = await cache_manager.get(cache_key)
        if cached_soru:
            logger.debug(f"Soru cache hit: {soru_id}")
            return cached_soru

        async with db_manager.get_session() as session:
            try:
                stmt = select(Question).where(
                    Question.id == soru_id,
                    Question.is_active == True,
                )
                result = await session.execute(stmt)
                soru = result.scalar_one_or_none()

                # PERFORMANCE: Cache the result (2 hours TTL)
                if soru:
                    await cache_manager.set(cache_key, soru, ttl=7200)

                return soru
            except Exception as e:
                logger.error(f"Soru getirme hatası: {e}")
                return None

    async def sorular_listele(
        self,
        sinav_tipi: str | None = None,
        konu: str | None = None,
        zorluk_seviyesi: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Question]:
        """
        Filtrelere göre soru listesi getir - Database'den (questions tablosu)

        Args:
            sinav_tipi: Sınav türü filtresi (tyt, ayt, ydt, deneme)
            konu: Konu filtresi (matematik, turkce, fizik, kimya, biyoloji, fen, sosyal, ingilizce)
            zorluk_seviyesi: Zorluk filtresi (easy, medium, hard)
            limit: Maksimum soru sayısı
            offset: Başlangıç offset'i

        Returns:
            List[Question]: Filtrelenmiş soru listesi
        """
        # PERFORMANCE: Cache question listings (5 min TTL)
        cache_key = (
            f"sorular_liste:{sinav_tipi}:{konu}:{zorluk_seviyesi}:{limit}:{offset}"
        )
        cached = await cache_manager.get(cache_key)
        if cached is not None:
            return cached

        async with db_manager.get_session() as session:
            try:
                # Base query - questions tablosundan (Question modeli)
                stmt = select(Question).where(
                    (Question.is_active == True) | (Question.is_active == None)
                )

                # Sınav tipi filtresi — DB UPPERCASE: "TYT", "AYT"
                if sinav_tipi:
                    stmt = stmt.where(Question.exam_type == sinav_tipi.upper())

                # Konu filtresi — DB UPPERCASE: "MATEMATIK", "TURKCE", "FIZIK" vb.
                if konu:
                    subject = _KONU_MAP.get(
                        konu, _KONU_MAP.get(konu.lower(), konu.upper())
                    )
                    stmt = stmt.where(Question.subject_area == subject)

                # Zorluk filtresi (difficulty: easy, medium, hard)
                if zorluk_seviyesi:
                    zorluk_lower = zorluk_seviyesi.lower()
                    stmt = stmt.where(Question.difficulty_level == zorluk_lower)

                # Sıralama ve limit
                stmt = (
                    stmt.order_by(Question.created_at.desc())
                    .offset(offset)
                    .limit(limit)
                )

                result = await session.execute(stmt)
                questions = result.scalars().all()

                # PERFORMANCE: Cache result for 5 minutes
                if questions:
                    await cache_manager.set(cache_key, questions, ttl=300)

                return questions

            except Exception as e:
                logger.error(f"Soru listeleme hatası: {e}")
                return []

    async def rastgele_sorular_sec(
        self,
        sinav_tipi: str,
        soru_sayisi: int,
        konu_dagilimi: dict[str, int] | None = None,
    ) -> list[Question]:
        """
        Rastgele soru seçimi yap - Gelişmiş algoritma ile

        FIX N+1: Tüm konular için tek sorguda sorular getirilir,
        sonra memory'de dağıtılır.

        Args:
            sinav_tipi: Sınav türü (TYT, AYT, YDT)
            soru_sayisi: Toplam soru sayısı
            konu_dagilimi: Konu bazlı dağılım (opsiyonel)

        Returns:
            List[Question]: Seçilen sorular
        """
        async with db_manager.get_session() as session:
            try:
                # Konu dağılımı belirtilmemişse - küçük veri setleri için basit seçim
                if not konu_dagilimi:
                    # Önce sınav tipindeki tüm soruları getir
                    logger.debug(
                        f"Konu dağılımı yok, tüm sorular getiriliyor: sinav_tipi={sinav_tipi}"
                    )
                    tum_sorular = await self.sorular_listele(
                        sinav_tipi=sinav_tipi, limit=soru_sayisi * 3
                    )
                    logger.debug(f"Toplam bulunan: {len(tum_sorular)} soru")

                    # Yeterli soru varsa rastgele seç, yoksa tümünü döndür
                    if len(tum_sorular) >= soru_sayisi:
                        return random.sample(tum_sorular, soru_sayisi)
                    logger.debug(
                        f"İstenen: {soru_sayisi}, Mevcut: {len(tum_sorular)} - Tümü döndürülüyor"
                    )
                    return tum_sorular

                # FIX N+1: Konu dağılımı varsa - tek sorguda tüm konuların sorularını getir
                # Toplam ihtiyaç duyulan soru sayısını hesapla
                toplam_ihtiyac = sum(sayi * 3 for sayi in konu_dagilimi.values())

                # Konu listesini hazırla (DB UPPERCASE formatında)
                konu_listesi = [
                    _KONU_MAP.get(konu, konu.upper()) for konu in konu_dagilimi
                ]

                # FIX N+1: Tek sorguda tüm konuların sorularını getir
                sinav_upper = sinav_tipi.upper() if sinav_tipi else None
                stmt = select(Question).where(
                    (Question.is_active == True) | (Question.is_active == None)
                )
                if sinav_upper:
                    stmt = stmt.where(Question.exam_type == sinav_upper)

                # Konu filtresi - IN clause ile tek sorgu
                if konu_listesi:
                    stmt = stmt.where(Question.subject_area.in_(konu_listesi))

                stmt = stmt.order_by(func.random()).limit(toplam_ihtiyac)

                result = await session.execute(stmt)
                tum_sorular = result.scalars().all()

                logger.debug(f"FIX N+1: Tek sorguda {len(tum_sorular)} soru getirildi")

                # Soruları konulara göre grupla (memory'de)
                konu_gruplari: dict[str, list[Question]] = {}
                for soru in tum_sorular:
                    subject = soru.subject_area if soru.subject_area else "diger"
                    if subject not in konu_gruplari:
                        konu_gruplari[subject] = []
                    konu_gruplari[subject].append(soru)

                # Her konu için istenen sayıda soru seç
                secilen_sorular = []
                for konu, sayi in konu_dagilimi.items():
                    subject_key = _KONU_MAP.get(konu, konu.upper())
                    konu_sorulari = konu_gruplari.get(subject_key, [])

                    logger.debug(
                        f"Konu: {konu} ({subject_key}), İstenen: {sayi}, Mevcut: {len(konu_sorulari)}"
                    )

                    if len(konu_sorulari) >= sayi:
                        # Rastgele seçim yap
                        secilen = random.sample(konu_sorulari, sayi)
                        secilen_sorular.extend(secilen)
                    else:
                        # Yeterli soru yoksa mevcut tümünü al
                        secilen_sorular.extend(konu_sorulari)
                        logger.warning(
                            f"{konu} konusunda yeterli soru yok. İstenen: {sayi}, Mevcut: {len(konu_sorulari)}"
                        )

                return secilen_sorular

            except Exception as e:
                logger.error(f"Rastgele soru seçimi hatası: {e}")
                return []

    async def get_interleaved_questions(
        self,
        subjects: list[str],
        count: int = 10,
        difficulty_levels: list[str] | None = None,
        exam_type: str = "TYT",
    ) -> list[Question]:
        """
        Interleaved practice: Birden fazla konudan karışık sırada soru seç.

        Bilimsel dayanak: Rohrer et al. RCT — interleaving d=1.21.
        Her konudan eşit sayıda soru, rastgele sırada döndürülür.

        Args:
            subjects: Konu listesi (Türkçe veya UPPERCASE — her ikisi de kabul edilir)
            count: Toplam soru sayısı
            difficulty_levels: Zorluk filtresi listesi (ZPD bandından), None ise tümü
            exam_type: Sınav tipi ("TYT", "AYT")

        Returns:
            Karışık sırada sorular
        """
        if not subjects:
            logger.debug(
                "get_interleaved_questions: subjects listesi boş, boş liste döndürülüyor"
            )
            return []

        cache_key = (
            f"interleaved:{exam_type}:{','.join(sorted(subjects))}"
            f":{count}:{','.join(sorted(difficulty_levels or []))}"
        )
        cached = await cache_manager.get(cache_key)
        if cached is not None:
            logger.debug(f"get_interleaved_questions: cache hit — {cache_key}")
            return cached

        subjects_upper = [_KONU_MAP.get(s, s.upper()) for s in subjects]
        exam_type_upper = exam_type.upper()
        pool_size = count * 3

        async with db_manager.get_session() as session:
            try:
                stmt = select(Question).where(
                    Question.is_active == True,
                    Question.subject_area.in_(subjects_upper),
                    Question.exam_type == exam_type_upper,
                )
                if difficulty_levels:
                    stmt = stmt.where(Question.difficulty_level.in_(difficulty_levels))

                stmt = stmt.order_by(func.random()).limit(pool_size)

                result = await session.execute(stmt)
                pool: list[Question] = list(result.scalars().all())

                logger.debug(
                    f"get_interleaved_questions: havuzdan {len(pool)} soru çekildi "
                    f"(konular={subjects_upper}, exam_type={exam_type_upper})"
                )

                # Konulara göre bellek içinde grupla
                groups: dict[str, list[Question]] = {s: [] for s in subjects_upper}
                for q in pool:
                    key = q.subject_area if q.subject_area else ""
                    if key in groups:
                        groups[key].append(q)

                # Her konudan eşit sayıda seç
                per_subject = count // len(subjects_upper)
                remainder = count % len(subjects_upper)

                selected: list[Question] = []
                for subj in subjects_upper:
                    bucket = groups.get(subj, [])
                    take = per_subject
                    if bucket:
                        selected.extend(bucket[:take])
                    else:
                        logger.warning(
                            f"get_interleaved_questions: '{subj}' konusunda soru bulunamadı"
                        )

                # Kalan kontenjanı havuzdan tamamla (konudan bağımsız)
                if remainder > 0:
                    used_ids = {q.id for q in selected}
                    extras = [q for q in pool if q.id not in used_ids]
                    selected.extend(extras[:remainder])

                random.shuffle(selected)
                result_list = selected[:count]

                await cache_manager.set(cache_key, result_list, ttl=60)
                logger.debug(
                    f"get_interleaved_questions: {len(result_list)} soru döndürülüyor, cache yazıldı"
                )
                return result_list

            except Exception as e:
                logger.error(f"get_interleaved_questions hatası: {e}")
                return []

    async def get_exit_quiz_questions(
        self,
        subject: str,
        count: int = 5,
        difficulty_levels: list[str] | None = None,
        exam_type: str = "TYT",
        topic: str | None = None,
    ) -> list[Question]:
        """
        Çıkış testi: Tamamlanan konudan retrieval practice soruları.

        Bilimsel dayanak: Retrieval practice d=0.5-1.24.

        Args:
            subject: Ders adı (Türkçe veya UPPERCASE) - örn: "matematik"
            count: Soru sayısı
            difficulty_levels: Zorluk filtresi listesi, None ise tümü
            exam_type: Sınav tipi ("TYT", "AYT")
            topic: Konu adı (opsiyonel) - örn: "Türev", "Fonksiyonlar"

        Returns:
            Rastgele sırada sorular
        """
        cache_key = (
            f"exit_quiz:{exam_type}:{subject}:{topic or 'none'}"
            f":{count}:{','.join(sorted(difficulty_levels or []))}"
        )
        cached = await cache_manager.get(cache_key)
        if cached is not None:
            logger.debug(f"get_exit_quiz_questions: cache hit — {cache_key}")
            return cached

        # Fallback iyileştirme: bilinmeyen konu gelirse ders bazlı fallback
        if subject in _KONU_MAP:
            subject_upper = _KONU_MAP[subject]
        else:
            subject_lower = subject.lower()
            if subject_lower in _KONU_MAP:
                subject_upper = _KONU_MAP[subject_lower]
            else:
                subject_upper = "MATEMATIK"
                logger.warning(f"Bilinmeyen konu: {subject}, default MATEMATIK")

        exam_type_upper = exam_type.upper()

        async with db_manager.get_session() as session:
            try:
                # Önce topic filtresi ile dene
                use_topic_filter = bool(topic)

                # Topic normalization (Türkçe karakter desteği)
                normalized_topic = _normalize_topic(topic) if topic else None

                stmt = select(Question).where(
                    Question.is_active == True,
                    Question.subject_area == subject_upper,
                )

                # Topic varsa exam_type filtresi uygulanmaz (Türev=AYT, Çarpan=TYT olabilir)
                if not topic:
                    stmt = stmt.where(Question.exam_type == exam_type_upper)

                # Konu bazlı filtre: topic_hierarchy tablosundan ID bul
                if normalized_topic:
                    # Önce topic_hierarchy'de konuyu bul
                    topic_name = normalized_topic.title()  # "türev" -> "Türev"

                    # ASCII fallback
                    ascii_topic = (
                        normalized_topic.replace("ü", "u")
                        .replace("ş", "s")
                        .replace("ğ", "g")
                        .replace("ö", "o")
                        .replace("ç", "c")
                        .title()
                    )

                    # Konu ID'sini bul
                    topic_stmt = (
                        select(TopicHierarchy.id)
                        .where(
                            TopicHierarchy.is_active == True,
                            or_(
                                TopicHierarchy.name_tr.ilike(f"%{topic_name}%"),
                                TopicHierarchy.name_tr.ilike(f"%{normalized_topic}%"),
                                TopicHierarchy.name_tr.ilike(f"%{ascii_topic}%"),
                            ),
                        )
                        .limit(1)
                    )

                    topic_result = await session.execute(topic_stmt)
                    topic_id = topic_result.scalar_one_or_none()

                    if topic_id:
                        # Konu bulundu, primary_topic_id ile filtrele
                        stmt = stmt.where(Question.primary_topic_id == topic_id)
                        logger.debug(
                            f"Konu filtresi uygulanıyor: {topic} -> topic_id={topic_id}"
                        )
                    else:
                        # Konu bulunamadı — anahtar kelime bazlı metin araması
                        logger.warning(
                            f"Konu '{topic}' topic_hierarchy'de bulunamadı, anahtar kelime araması deneniyor"
                        )
                        # Konu adını kelimelere böl ve her birini ara
                        # "Çarpanlara Ayırma" → ["çarpan", "ayır"]
                        keywords = [
                            w
                            for w in normalized_topic.split()
                            if len(w) >= 3  # Çok kısa kelimeleri atla
                        ]
                        if keywords:
                            conditions = []
                            for kw in keywords:
                                # Kök bazlı arama: kelimenin ilk 4+ harfini kullan
                                stem = kw[: max(4, len(kw) - 2)]
                                pattern = f"%{stem}%"
                                conditions.append(Question.question_text.ilike(pattern))
                            # En az bir kelime eşleşmesi yeterli
                            stmt = stmt.where(or_(*conditions))

                if difficulty_levels:
                    stmt = stmt.where(Question.difficulty_level.in_(difficulty_levels))

                stmt = stmt.order_by(func.random()).limit(count)

                result = await session.execute(stmt)
                questions: list[Question] = list(result.scalars().all())

                # Fallback: Topic bulunamazsa, topic filtresiz tekrar dene
                if use_topic_filter and len(questions) == 0 and normalized_topic:
                    logger.warning(
                        f"Konu '{topic}' için soru bulunamadı, fallback: sadece ders filtresi"
                    )

                    stmt_fallback = select(Question).where(
                        Question.is_active == True,
                        Question.subject_area == subject_upper,
                        Question.exam_type == exam_type_upper,
                    )
                    if difficulty_levels:
                        stmt_fallback = stmt_fallback.where(
                            Question.difficulty_level.in_(difficulty_levels)
                        )

                    stmt_fallback = stmt_fallback.order_by(func.random()).limit(count)
                    result_fallback = await session.execute(stmt_fallback)
                    questions = list(result_fallback.scalars().all())

                    logger.info(
                        f"Fallback: {len(questions)} soru (ders={subject_upper}, konu yok)"
                    )

                logger.debug(
                    f"get_exit_quiz_questions: {len(questions)} soru döndürülüyor "
                    f"(ders={subject_upper}, konu={topic or 'none'}, exam_type={exam_type_upper})"
                )

                await cache_manager.set(cache_key, questions, ttl=60)
                return questions

            except Exception as e:
                logger.error(f"get_exit_quiz_questions hatası: {e}")
                return []

    async def irt_parametreli_soru_sec(
        self,
        ogrenci_yetenek: float,
        sinav_tipi: str,
        soru_sayisi: int,
        hedef_bilgi: float = 1.0,
    ) -> list[Question]:
        """
        IRT parametreli soru seçimi - Adaptif algoritma

        Args:
            ogrenci_yetenek: Öğrenci yetenek parametresi (-3 ile +3 arası)
            sinav_tipi: Sınav türü
            soru_sayisi: Seçilecek soru sayısı
            hedef_bilgi: Hedef bilgi fonksiyonu değeri

        Returns:
            List[Question]: IRT'ye göre optimize edilmiş sorular
        """
        try:
            # Tüm uygun soruları getir
            tum_sorular = await self.sorular_listele(
                sinav_tipi=sinav_tipi,
                limit=1000,  # Geniş havuz
            )

            if not tum_sorular:
                return []

            # Her soru için bilgi fonksiyonu hesapla
            soru_bilgi_listesi = []

            for soru in tum_sorular:
                bilgi_degeri = await self._hesapla_bilgi_fonksiyonu(
                    ogrenci_yetenek,
                    soru.irt_difficulty,
                    soru.irt_discrimination,
                    soru.irt_guessing,
                )

                soru_bilgi_listesi.append(
                    {
                        "soru": soru,
                        "bilgi_degeri": bilgi_degeri,
                        "zorluk_farki": abs(soru.irt_difficulty - ogrenci_yetenek),
                    }
                )

            # Bilgi değerine göre sırala (yüksekten düşüğe)
            soru_bilgi_listesi.sort(key=lambda x: x["bilgi_degeri"], reverse=True)

            # En iyi soruları seç
            secilen_sorular = []
            konu_sayaclari: dict[str, int] = {}

            for item in soru_bilgi_listesi:
                soru = item["soru"]
                konu = str(soru.subject_area)

                # Konu dağılımını kontrol et
                if konu not in konu_sayaclari:
                    konu_sayaclari[konu] = 0

                # Konu başına maksimum soru sınırı
                max_konu_soru = max(
                    1, soru_sayisi // 4
                )  # Her konudan en az 1, en fazla 1/4

                if (
                    konu_sayaclari[konu] < max_konu_soru
                    and len(secilen_sorular) < soru_sayisi
                ):
                    secilen_sorular.append(soru)
                    konu_sayaclari[konu] += 1

            # Eksik kalan soruları tamamla
            while len(secilen_sorular) < soru_sayisi and len(soru_bilgi_listesi) > len(
                secilen_sorular
            ):
                for item in soru_bilgi_listesi:
                    if item["soru"] not in secilen_sorular:
                        secilen_sorular.append(item["soru"])
                        if len(secilen_sorular) >= soru_sayisi:
                            break

            return secilen_sorular

        except Exception as e:
            logger.error(f"IRT parametreli soru seçimi hatası: {e}")
            # Fallback: Normal rastgele seçim
            return await self.rastgele_sorular_sec(sinav_tipi, soru_sayisi)

    async def _hesapla_bilgi_fonksiyonu(
        self, yetenek: float, zorluk: float, ayiricilik: float, tahmin: float
    ) -> float:
        """
        IRT bilgi fonksiyonu hesapla

        Args:
            yetenek: Öğrenci yetenek parametresi
            zorluk: Soru zorluk parametresi
            ayiricilik: Soru ayırıcılık parametresi
            tahmin: Tahmin parametresi

        Returns:
            float: Bilgi fonksiyonu değeri
        """
        try:
            # 3PL IRT modeli için bilgi fonksiyonu
            # I(θ) = a²[(P(θ)(1-P(θ))) / (1-c)²] * [(1-c) / (P(θ)-c)]²

            # Doğru cevap verme olasılığı hesapla
            p_theta = await self._hesapla_dogru_cevap_olasiligi(
                yetenek, zorluk, ayiricilik, tahmin
            )

            if p_theta <= tahmin or p_theta >= 1.0:
                return 0.0

            # Bilgi fonksiyonu hesapla
            bilgi = (ayiricilik**2) * (p_theta * (1 - p_theta)) / ((1 - tahmin) ** 2)
            bilgi *= ((1 - tahmin) / (p_theta - tahmin)) ** 2

            return max(0.0, bilgi)

        except Exception as e:
            logger.error(f"Bilgi fonksiyonu hesaplama hatası: {e}")
            return 0.0

    async def _hesapla_dogru_cevap_olasiligi(
        self, yetenek: float, zorluk: float, ayiricilik: float, tahmin: float
    ) -> float:
        """
        3PL IRT modeli ile doğru cevap verme olasılığı hesapla

        P(θ) = c + (1-c) * [1 / (1 + e^(-a(θ-b)))]
        """
        try:
            exponent = -ayiricilik * (yetenek - zorluk)

            # Overflow kontrolü
            if exponent > 700:
                return tahmin
            if exponent < -700:
                return 1.0

            olaslik = tahmin + (1 - tahmin) * (1 / (1 + math.exp(exponent)))
            return max(tahmin, min(1.0, olaslik))

        except Exception as e:
            logger.error(f"Olasılık hesaplama hatası: {e}")
            return 0.5

    async def soru_guncelle(
        self, soru_id: str, guncelleme_verisi: dict
    ) -> Question | None:
        """
        Soru güncelle - Database'de

        Args:
            soru_id: Güncellenecek soru ID'si
            guncelleme_verisi: Güncelleme verileri

        Returns:
            Question: Güncellenmiş soru objesi
        """
        async with db_manager.get_session() as session:
            try:
                # Mevcut soruyu getir
                stmt = select(Question).where(
                    Question.id == soru_id,
                    Question.is_active == True,
                )
                result = await session.execute(stmt)
                soru = result.scalar_one_or_none()

                if not soru:
                    return None

                # Güncelleme verilerini uygula
                for alan, deger in guncelleme_verisi.items():
                    if hasattr(soru, alan):
                        # Enum dönüştürmeleri
                        if alan == "exam_type" and isinstance(deger, str):
                            exam_type, _, _ = await self._enum_donusturucu(
                                deger, "orta", "Matematik"
                            )
                            setattr(soru, alan, exam_type)
                        elif alan == "difficulty" and isinstance(deger, str):
                            _, difficulty, _ = await self._enum_donusturucu(
                                "TYT", deger, "Matematik"
                            )
                            setattr(soru, alan, difficulty)
                        elif alan == "subject_area" and isinstance(deger, str):
                            _, _, subject_area = await self._enum_donusturucu(
                                "TYT", "orta", deger
                            )
                            setattr(soru, alan, subject_area)
                        else:
                            setattr(soru, alan, deger)

                soru.updated_at = datetime.now()

                await session.commit()
                await session.refresh(soru)

                return soru

            except Exception as e:
                await session.rollback()
                logger.error(f"Soru güncelleme hatası: {e}")
                return None

    async def soru_sil(self, soru_id: str) -> bool:
        """
        Soru sil (soft delete) - Database'de

        Args:
            soru_id: Silinecek soru ID'si

        Returns:
            bool: Silme işlemi başarılı mı
        """
        async with db_manager.get_session() as session:
            try:
                # Mevcut soruyu getir
                stmt = select(Question).where(
                    Question.id == soru_id,
                    Question.is_active == True,
                )
                result = await session.execute(stmt)
                soru = result.scalar_one_or_none()

                if not soru:
                    return False

                # Soft delete - is_active = False
                soru.is_active = False
                soru.updated_at = datetime.now()

                await session.commit()
                return True

            except Exception as e:
                await session.rollback()
                logger.error(f"Soru silme hatası: {e}")
                return False

    async def konu_listesi_getir(self, sinav_tipi: str | None = None) -> list[str]:
        """
        Mevcut konuları listele - Database'den

        Args:
            sinav_tipi: Sınav türü filtresi (opsiyonel)

        Returns:
            List[str]: Konu listesi
        """
        async with db_manager.get_session() as session:
            try:
                # Base query
                stmt = (
                    select(Question.subject_area)
                    .distinct()
                    .where(Question.is_active == True)
                )

                # Sınav tipi filtresi
                if sinav_tipi:
                    exam_type, _, _ = await self._enum_donusturucu(
                        sinav_tipi, "orta", "Matematik"
                    )
                    stmt = stmt.where(Question.exam_type == exam_type)

                result = await session.execute(stmt)
                subject_areas = result.scalars().all()

                # Enum değerlerini string'e çevir
                return sorted([subject.value for subject in subject_areas])

            except Exception as e:
                logger.error(f"Konu listesi getirme hatası: {e}")
                return []

    async def istatistikler_getir(self) -> dict:
        """
        Soru bankası istatistikleri - Database'den

        Returns:
            Dict: Detaylı istatistikler
        """
        async with db_manager.get_session() as session:
            try:
                # Toplam soru sayısı
                toplam_stmt = select(func.count(Question.id)).where(
                    Question.is_active == True
                )
                toplam_result = await session.execute(toplam_stmt)
                toplam_soru = toplam_result.scalar()

                # Sınav tipi dağılımı
                sinav_tipi_stmt = (
                    select(Question.exam_type, func.count(Question.id))
                    .where(Question.is_active == True)
                    .group_by(Question.exam_type)
                )
                sinav_tipi_result = await session.execute(sinav_tipi_stmt)
                sinav_tipi_dagilimi = {
                    exam_type.value: count
                    for exam_type, count in sinav_tipi_result.all()
                }

                # Konu dağılımı
                konu_stmt = (
                    select(Question.subject_area, func.count(Question.id))
                    .where(Question.is_active == True)
                    .group_by(Question.subject_area)
                )
                konu_result = await session.execute(konu_stmt)
                konu_dagilimi = {
                    subject.value: count for subject, count in konu_result.all()
                }

                # Zorluk dağılımı
                zorluk_stmt = (
                    select(Question.difficulty_level, func.count(Question.id))
                    .where(Question.is_active == True)
                    .group_by(Question.difficulty_level)
                )
                zorluk_result = await session.execute(zorluk_stmt)
                zorluk_dagilimi = {
                    difficulty.value: count for difficulty, count in zorluk_result.all()
                }

                # IRT parametreleri istatistikleri
                irt_stmt = select(
                    func.avg(Question.irt_difficulty).label("avg_difficulty"),
                    func.min(Question.irt_difficulty).label("min_difficulty"),
                    func.max(Question.irt_difficulty).label("max_difficulty"),
                    func.avg(Question.irt_discrimination).label("avg_discrimination"),
                    func.avg(Question.morphology_complexity).label("avg_morphology"),
                    func.avg(Question.readability_score).label("avg_readability"),
                ).where(Question.is_active == True)
                irt_result = await session.execute(irt_stmt)
                irt_stats = irt_result.first()

                return {
                    "toplam_soru_sayisi": toplam_soru,
                    "sinav_tipi_dagilimi": sinav_tipi_dagilimi,
                    "konu_dagilimi": konu_dagilimi,
                    "zorluk_dagilimi": zorluk_dagilimi,
                    "irt_istatistikleri": {
                        "ortalama_zorluk": float(irt_stats.avg_difficulty or 0),
                        "min_zorluk": float(irt_stats.min_difficulty or 0),
                        "max_zorluk": float(irt_stats.max_difficulty or 0),
                        "ortalama_ayiricilik": float(irt_stats.avg_discrimination or 0),
                        "ortalama_morfoloji_karmasikligi": float(
                            irt_stats.avg_morphology or 0
                        ),
                        "ortalama_okunabilirlik": float(irt_stats.avg_readability or 0),
                    },
                    "kalite_metrikleri": {
                        "yuksek_ayiricilik_orani": await self._hesapla_yuksek_ayiricilik_orani(
                            session
                        ),
                        "dengeli_zorluk_dagilimi": await self._hesapla_zorluk_dengesi(
                            session
                        ),
                        "morfoloji_kapsami": await self._hesapla_morfoloji_kapsami(
                            session
                        ),
                    },
                }

            except Exception as e:
                logger.error(f"İstatistik hesaplama hatası: {e}")
                return {
                    "toplam_soru_sayisi": 0,
                    "sinav_tipi_dagilimi": {},
                    "konu_dagilimi": {},
                    "zorluk_dagilimi": {},
                    "irt_istatistikleri": {},
                    "kalite_metrikleri": {},
                }

    async def _hesapla_yuksek_ayiricilik_orani(self, session: AsyncSession) -> float:
        """Yüksek ayırıcılık parametresine sahip soruların oranını hesapla"""
        try:
            toplam_stmt = select(func.count(Question.id)).where(
                Question.is_active == True
            )
            toplam_result = await session.execute(toplam_stmt)
            toplam = toplam_result.scalar()

            if toplam == 0:
                return 0.0

            yuksek_stmt = select(func.count(Question.id)).where(
                and_(Question.is_active == True, Question.irt_discrimination >= 1.5)
            )
            yuksek_result = await session.execute(yuksek_stmt)
            yuksek = yuksek_result.scalar()

            return (yuksek / toplam) * 100

        except Exception:
            return 0.0

    async def _hesapla_zorluk_dengesi(self, session: AsyncSession) -> float:
        """Zorluk dağılımının dengesini hesapla (0-100 arası)"""
        try:
            zorluk_stmt = (
                select(Question.difficulty_level, func.count(Question.id))
                .where(Question.is_active == True)
                .group_by(Question.difficulty_level)
            )
            zorluk_result = await session.execute(zorluk_stmt)
            zorluk_counts = dict(zorluk_result.all())

            if not zorluk_counts:
                return 0.0

            toplam = sum(zorluk_counts.values())

            # İdeal dağılım: %30 kolay, %40 orta, %30 zor
            ideal_dagilim = {
                QuestionDifficulty.EASY: 0.30,
                QuestionDifficulty.MEDIUM: 0.40,
                QuestionDifficulty.HARD: 0.30,
            }

            # Mevcut dağılımı hesapla
            mevcut_dagilim = {
                zorluk: count / toplam for zorluk, count in zorluk_counts.items()
            }

            # Sapma hesapla
            toplam_sapma = 0
            for zorluk, ideal_oran in ideal_dagilim.items():
                mevcut_oran = mevcut_dagilim.get(zorluk, 0)
                toplam_sapma += abs(ideal_oran - mevcut_oran)

            # Denge skoru (düşük sapma = yüksek denge)
            denge_skoru = max(0, 100 - (toplam_sapma * 100))
            return denge_skoru

        except Exception:
            return 0.0

    async def _hesapla_morfoloji_kapsami(self, session: AsyncSession) -> float:
        """Morfolojik karmaşıklık kapsamını hesapla"""
        try:
            # Farklı karmaşıklık seviyelerindeki soru sayıları
            seviyeler = [(0.0, 0.3, "düşük"), (0.3, 0.7, "orta"), (0.7, 1.0, "yüksek")]

            toplam_stmt = select(func.count(Question.id)).where(
                Question.is_active == True
            )
            toplam_result = await session.execute(toplam_stmt)
            toplam = toplam_result.scalar()

            if toplam == 0:
                return 0.0

            kapsam_sayisi = 0
            for min_val, max_val, _ in seviyeler:
                seviye_stmt = select(func.count(Question.id)).where(
                    and_(
                        Question.is_active == True,
                        Question.morphology_complexity >= min_val,
                        Question.morphology_complexity < max_val,
                    )
                )
                seviye_result = await session.execute(seviye_stmt)
                seviye_count = seviye_result.scalar()

                if seviye_count > 0:
                    kapsam_sayisi += 1

            # Tüm seviyelerde soru varsa %100 kapsam
            return (kapsam_sayisi / len(seviyeler)) * 100

        except Exception:
            return 0.0

    async def zorluk_seviyesi_filtrele(
        self, ogrenci_yetenek: float, sinav_tipi: str, tolerans: float = 1.0
    ) -> list[Question]:
        """
        Öğrenci yetenek seviyesine göre uygun zorlukta sorular filtrele

        Args:
            ogrenci_yetenek: Öğrenci yetenek parametresi
            sinav_tipi: Sınav türü
            tolerans: Zorluk toleransı (±)

        Returns:
            List[Question]: Uygun zorlukta sorular
        """
        async with db_manager.get_session() as session:
            try:
                min_zorluk = ogrenci_yetenek - tolerans
                max_zorluk = ogrenci_yetenek + tolerans

                exam_type, _, _ = await self._enum_donusturucu(
                    sinav_tipi, "orta", "Matematik"
                )

                stmt = (
                    select(Question)
                    .where(
                        and_(
                            Question.is_active == True,
                            Question.exam_type == exam_type,
                            Question.irt_difficulty >= min_zorluk,
                            Question.irt_difficulty <= max_zorluk,
                        )
                    )
                    .order_by(Question.irt_discrimination.desc())
                )

                result = await session.execute(stmt)
                return result.scalars().all()

            except Exception as e:
                logger.error(f"Zorluk filtrele hatası: {e}")
                return []

    async def toplu_soru_ekle(self, sorular_listesi: list[dict]) -> dict[str, int]:
        """
        Toplu soru ekleme işlemi - Batch insert ile N+1 query fix

        Args:
            sorular_listesi: Soru verilerinin listesi

        Returns:
            Dict: Ekleme sonuç istatistikleri
        """
        basarili = 0
        basarisiz = 0
        hatalar = []

        # FIX N+1: Batch insert instead of loop
        async with db_manager.get_session() as session:
            questions_to_add = []

            for i, soru_data in enumerate(sorular_listesi):
                try:
                    # Enum dönüştürmeleri
                    exam_type, difficulty, subject_area = await self._enum_donusturucu(
                        soru_data.get("sinav_tipi", "TYT"),
                        soru_data.get("zorluk_seviyesi", "orta"),
                        soru_data.get("konu", "Matematik"),
                    )

                    # IRT parametrelerini hesapla
                    irt_params = await self._hesapla_irt_parametreleri(
                        difficulty.value, soru_data.get("konu", "Matematik")
                    )

                    # Question object oluştur
                    yeni_soru = Question(
                        question_text=soru_data["soru_metni"],
                        option_a=soru_data["secenekler"][0].replace("A) ", ""),
                        option_b=soru_data["secenekler"][1].replace("B) ", ""),
                        option_c=soru_data["secenekler"][2].replace("C) ", ""),
                        option_d=soru_data["secenekler"][3].replace("D) ", ""),
                        option_e=soru_data["secenekler"][4].replace("E) ", "")
                        if len(soru_data["secenekler"]) > 4
                        else None,
                        correct_answer=soru_data["dogru_cevap"],
                        explanation=soru_data.get("cozum_aciklamasi"),
                        exam_type=exam_type,
                        subject_area=subject_area,
                        topic=soru_data.get("konu", "Genel"),
                        subtopic=soru_data.get("alt_konu"),
                        difficulty=difficulty,
                        irt_difficulty=irt_params["difficulty"],
                        irt_discrimination=irt_params["discrimination"],
                        irt_guessing=irt_params["guessing"],
                        morphology_complexity=await self._hesapla_morfoloji_karmasikligi(
                            soru_data["soru_metni"]
                        ),
                        readability_score=await self._hesapla_okunabilirlik(
                            soru_data["soru_metni"]
                        ),
                        created_by=soru_data.get("created_by"),
                    )
                    questions_to_add.append(yeni_soru)
                    basarili += 1

                except Exception as e:
                    basarisiz += 1
                    hatalar.append(f"Soru {i + 1}: {e!s}")

            # Batch insert - single commit for all questions
            if questions_to_add:
                try:
                    session.add_all(questions_to_add)
                    await session.commit()
                except Exception as e:
                    await session.rollback()
                    # Rollback durumunda tüm sorular başarısız sayılır
                    basarisiz = len(sorular_listesi)
                    basarili = 0
                    hatalar.append(f"Batch insert hatası: {e!s}")

        return {
            "basarili": basarili,
            "basarisiz": basarisiz,
            "toplam": len(sorular_listesi),
            "hatalar": hatalar,
        }

    async def soru_performans_guncelle(
        self, soru_id: str, dogru_cevap: bool, cevap_suresi: float
    ) -> bool:
        """
        Soru performans istatistiklerini güncelle

        Args:
            soru_id: Soru ID'si
            dogru_cevap: Cevap doğru mu
            cevap_suresi: Cevaplama süresi (saniye)

        Returns:
            bool: Güncelleme başarılı mı
        """
        async with db_manager.get_session() as session:
            try:
                stmt = select(Question).where(
                    Question.id == soru_id,
                    Question.is_active == True,
                )
                result = await session.execute(stmt)
                soru = result.scalar_one_or_none()

                if not soru:
                    return False

                # İstatistikleri güncelle
                soru.times_asked += 1
                if dogru_cevap:
                    soru.times_correct += 1

                # Ortalama cevap süresini güncelle
                if soru.average_response_time == 0:
                    soru.average_response_time = cevap_suresi
                else:
                    # Hareketli ortalama
                    soru.average_response_time = (
                        soru.average_response_time * (soru.times_asked - 1)
                        + cevap_suresi
                    ) / soru.times_asked

                await session.commit()
                return True

            except Exception as e:
                await session.rollback()
                logger.error(f"Performans güncelleme hatası: {e}")
                return False

    async def irt_parametrelerini_yeniden_hesapla(self, soru_id: str) -> bool:
        """
        Soru performans verilerine göre IRT parametrelerini yeniden hesapla

        Args:
            soru_id: Soru ID'si

        Returns:
            bool: Hesaplama başarılı mı
        """
        async with db_manager.get_session() as session:
            try:
                stmt = select(Question).where(
                    Question.id == soru_id,
                    Question.is_active == True,
                )
                result = await session.execute(stmt)
                soru = result.scalar_one_or_none()

                if not soru or soru.times_asked < 10:  # Minimum 10 cevap gerekli
                    return False

                # Başarı oranına göre zorluk parametresini ayarla
                basari_orani = soru.times_correct / soru.times_asked

                # Logit dönüşümü ile zorluk hesapla
                if basari_orani <= 0.01:
                    basari_orani = 0.01
                elif basari_orani >= 0.99:
                    basari_orani = 0.99

                yeni_zorluk = -math.log(basari_orani / (1 - basari_orani))

                # Zorluk parametresini güncelle
                soru.irt_difficulty = max(-3.0, min(3.0, yeni_zorluk))

                # Ayırıcılık parametresini cevap süresi varyansına göre ayarla
                if soru.average_response_time > 0:
                    # Hızlı cevaplanan sorular daha az ayırıcı olabilir
                    sure_faktoru = min(
                        2.0, soru.average_response_time / 60
                    )  # 60 saniye referans
                    soru.irt_discrimination = max(0.5, min(2.5, sure_faktoru))

                await session.commit()
                return True

            except Exception as e:
                await session.rollback()
                logger.error(f"IRT parametresi güncelleme hatası: {e}")
                return False


# Global servis instance
soru_bankasi_servisi = SoruBankasiServisi()
