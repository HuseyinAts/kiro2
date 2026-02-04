"""
Müfredat Uyumluluk Sistemi
MEB ve ÖSYM müfredat standartlarına uyumluluk kontrolü ve yönetimi
"""

import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from models.curriculum import (
    CurriculumAlignment,
    CurriculumComplianceReport,
    CurriculumUpdateRequest,
    ExamType,
    GradeLevel,
    LearningOutcome,
    MEBCurriculumStandard,
    OSYMStandard,
    QuestionBankCompliance,
    SubjectType,
)

logger = logging.getLogger(__name__)


class CurriculumComplianceSystem:
    """
    MEB ve ÖSYM Müfredat Uyumluluk Sistemi

    Özellikler:
    - MEB müfredat standartları yönetimi
    - ÖSYM sınav standartları entegrasyonu
    - Öğrenme kazanımları eşleştirme
    - Soru bankası uyumluluk kontrolü
    - Otomatik uyumluluk raporlama
    """

    def __init__(self, database_service=None, cache_service=None):
        self.db = database_service
        self.cache = cache_service

        # MEB ve ÖSYM standartları cache
        self.meb_standards_cache: dict[str, MEBCurriculumStandard] = {}
        self.osym_standards_cache: dict[str, OSYMStandard] = {}
        self.alignment_cache: dict[str, CurriculumAlignment] = {}

        # Uyumluluk skorları
        self.compliance_thresholds = {
            "excellent": 0.9,
            "good": 0.8,
            "acceptable": 0.7,
            "needs_improvement": 0.6,
            "insufficient": 0.0,
        }

        # Minimum soru sayısı gereksinimleri (Gereksinim 3.2)
        self.minimum_questions_per_topic = 1000

    async def initialize(self) -> bool:
        """Sistemi başlat ve temel verileri yükle"""
        try:
            logger.info("Müfredat uyumluluk sistemi başlatılıyor...")

            # MEB standartlarını yükle
            await self._load_meb_standards()

            # ÖSYM standartlarını yükle
            await self._load_osym_standards()

            # Mevcut eşleştirmeleri yükle
            await self._load_existing_alignments()

            logger.info("Müfredat uyumluluk sistemi başarıyla başlatıldı")
            return True

        except Exception as e:
            logger.error(f"Müfredat uyumluluk sistemi başlatma hatası: {e}")
            return False

    # MEB Müfredat Standartları Yönetimi

    async def add_meb_standard(self, standard: MEBCurriculumStandard) -> bool:
        """
        MEB müfredat standardı ekle
        Gereksinim 3.1: MEB müfredat standartlarına uygun konular
        """
        try:
            # Veritabanına kaydet
            if self.db:
                await self.db.save_meb_standard(standard)

            # Cache'e ekle
            self.meb_standards_cache[standard.id] = standard

            logger.info(f"MEB standardı eklendi: {standard.topic_name}")
            return True

        except Exception as e:
            logger.error(f"MEB standardı ekleme hatası: {e}")
            return False

    async def get_meb_standards_by_subject(
        self, subject: SubjectType, grade_level: GradeLevel | None = None
    ) -> list[MEBCurriculumStandard]:
        """Derse göre MEB standartlarını getir"""
        try:
            standards = []

            for standard in self.meb_standards_cache.values():
                if standard.subject == subject and standard.is_active:
                    if grade_level is None or standard.grade_level == grade_level:
                        standards.append(standard)

            # Veritabanından da kontrol et
            if self.db and not standards:
                standards = await self.db.get_meb_standards_by_subject(
                    subject, grade_level
                )

            return standards

        except Exception as e:
            logger.error(f"MEB standartları getirme hatası: {e}")
            return []

    async def get_learning_outcomes(
        self, meb_standard_id: str
    ) -> list[LearningOutcome]:
        """
        Öğrenme kazanımlarını getir
        Gereksinim 3.3: MEB'in belirlediği kazanımlarla eşleşme
        """
        try:
            if self.db:
                outcomes = await self.db.get_learning_outcomes_by_standard(
                    meb_standard_id
                )
                return outcomes

            return []

        except Exception as e:
            logger.error(f"Öğrenme kazanımları getirme hatası: {e}")
            return []

    # ÖSYM Standartları Yönetimi

    async def add_osym_standard(self, standard: OSYMStandard) -> bool:
        """ÖSYM sınav standardı ekle"""
        try:
            # Veritabanına kaydet
            if self.db:
                await self.db.save_osym_standard(standard)

            # Cache'e ekle
            self.osym_standards_cache[standard.id] = standard

            logger.info(f"ÖSYM standardı eklendi: {standard.topic_name}")
            return True

        except Exception as e:
            logger.error(f"ÖSYM standardı ekleme hatası: {e}")
            return False

    async def get_osym_standards_by_priority(
        self, exam_type: ExamType, subject: SubjectType | None = None
    ) -> list[OSYMStandard]:
        """
        ÖSYM standartlarını öncelik sırasına göre getir
        Gereksinim 3.5: ÖSYM'nin belirlediği öncelik sırası
        """
        try:
            standards = []

            for standard in self.osym_standards_cache.values():
                if standard.exam_type == exam_type and standard.is_active:
                    if subject is None or standard.subject == subject:
                        standards.append(standard)

            # Öncelik seviyesine göre sırala (1 = en yüksek öncelik)
            standards.sort(key=lambda x: x.priority_level)

            return standards

        except Exception as e:
            logger.error(f"ÖSYM standartları getirme hatası: {e}")
            return []

    # Uyumluluk Analizi ve Eşleştirme

    async def analyze_curriculum_alignment(
        self, subject: SubjectType, exam_type: ExamType
    ) -> CurriculumAlignment:
        """MEB ve ÖSYM standartları arasında uyumluluk analizi yap"""
        try:
            # MEB standartlarını getir
            meb_standards = await self.get_meb_standards_by_subject(subject)

            # ÖSYM standartlarını getir
            osym_standards = await self.get_osym_standards_by_priority(
                exam_type, subject
            )

            # Uyumluluk skorunu hesapla
            alignment_score = await self._calculate_alignment_score(
                meb_standards, osym_standards
            )

            # Boşlukları tespit et
            gaps = await self._identify_curriculum_gaps(meb_standards, osym_standards)

            # Önerileri oluştur
            recommendations = await self._generate_alignment_recommendations(gaps)

            alignment = CurriculumAlignment(
                id=str(uuid4()),
                meb_standard_id=f"{subject}_{exam_type}_meb",
                osym_standard_id=f"{subject}_{exam_type}_osym",
                alignment_score=alignment_score,
                alignment_type="subject_exam_alignment",
                gaps_identified=gaps,
                recommendations=recommendations,
            )

            # Cache'e kaydet
            self.alignment_cache[alignment.id] = alignment

            return alignment

        except Exception as e:
            logger.error(f"Uyumluluk analizi hatası: {e}")
            return None

    async def _calculate_alignment_score(
        self,
        meb_standards: list[MEBCurriculumStandard],
        osym_standards: list[OSYMStandard],
    ) -> float:
        """MEB ve ÖSYM standartları arasında uyumluluk skoru hesapla"""
        try:
            if not meb_standards or not osym_standards:
                return 0.0

            # Konu eşleştirmesi
            meb_topics = {std.topic_name.lower() for std in meb_standards}
            osym_topics = {std.topic_name.lower() for std in osym_standards}

            # Kesişim ve birleşim
            intersection = meb_topics.intersection(osym_topics)
            union = meb_topics.union(osym_topics)

            # Jaccard benzerlik katsayısı
            if len(union) == 0:
                return 0.0

            basic_score = len(intersection) / len(union)

            # Öğrenme kazanımları uyumluluğu
            outcome_score = await self._calculate_learning_outcomes_alignment(
                meb_standards
            )

            # Ağırlıklı ortalama
            final_score = (basic_score * 0.6) + (outcome_score * 0.4)

            return min(1.0, max(0.0, final_score))

        except Exception as e:
            logger.error(f"Uyumluluk skoru hesaplama hatası: {e}")
            return 0.0

    async def _calculate_learning_outcomes_alignment(
        self, meb_standards: list[MEBCurriculumStandard]
    ) -> float:
        """Öğrenme kazanımları uyumluluk skoru hesapla"""
        try:
            total_outcomes = 0
            aligned_outcomes = 0

            for standard in meb_standards:
                outcomes = await self.get_learning_outcomes(standard.id)
                total_outcomes += len(outcomes)

                # Her kazanım için uyumluluk kontrol et
                for outcome in outcomes:
                    if await self._is_outcome_osym_aligned(outcome):
                        aligned_outcomes += 1

            if total_outcomes == 0:
                return 0.0

            return aligned_outcomes / total_outcomes

        except Exception as e:
            logger.error(f"Öğrenme kazanımları uyumluluk hesaplama hatası: {e}")
            return 0.0

    async def _is_outcome_osym_aligned(self, outcome: LearningOutcome) -> bool:
        """Öğrenme kazanımının ÖSYM ile uyumlu olup olmadığını kontrol et"""
        try:
            # ÖSYM sınav formatına uygun bilişsel seviye kontrolü
            osym_cognitive_levels = [
                "bilgi",
                "kavrama",
                "uygulama",
                "analiz",
                "sentez",
                "değerlendirme",
            ]

            return outcome.cognitive_level.lower() in osym_cognitive_levels

        except Exception as e:
            logger.error(f"Kazanım uyumluluk kontrolü hatası: {e}")
            return False

    async def _identify_curriculum_gaps(
        self,
        meb_standards: list[MEBCurriculumStandard],
        osym_standards: list[OSYMStandard],
    ) -> list[str]:
        """Müfredat boşluklarını tespit et"""
        try:
            gaps = []

            # MEB'de olup ÖSYM'de olmayan konular
            meb_topics = {std.topic_name for std in meb_standards}
            osym_topics = {std.topic_name for std in osym_standards}

            meb_only = meb_topics - osym_topics
            osym_only = osym_topics - meb_topics

            if meb_only:
                gaps.append(f"MEB'de var ÖSYM'de yok: {', '.join(meb_only)}")

            if osym_only:
                gaps.append(f"ÖSYM'de var MEB'de yok: {', '.join(osym_only)}")

            return gaps

        except Exception as e:
            logger.error(f"Müfredat boşlukları tespit etme hatası: {e}")
            return []

    async def _generate_alignment_recommendations(self, gaps: list[str]) -> list[str]:
        """Uyumluluk önerileri oluştur"""
        try:
            recommendations = []

            for gap in gaps:
                if "MEB'de var ÖSYM'de yok" in gap:
                    recommendations.append(
                        "MEB müfredatındaki konuların ÖSYM sınav formatına uyarlanması önerilir"
                    )
                elif "ÖSYM'de var MEB'de yok" in gap:
                    recommendations.append(
                        "ÖSYM sınavlarında çıkan konuların MEB müfredatına eklenmesi önerilir"
                    )

            if not recommendations:
                recommendations.append("Müfredat uyumluluğu yeterli seviyededir")

            return recommendations

        except Exception as e:
            logger.error(f"Öneriler oluşturma hatası: {e}")
            return []

    # Soru Bankası Uyumluluk Kontrolü

    async def validate_question_bank_compliance(
        self, subject: SubjectType, topic_id: str
    ) -> QuestionBankCompliance:
        """
        Soru bankası uyumluluk kontrolü
        Gereksinim 3.2: Her konu için en az 1000 ÖSYM tarzı soru
        """
        try:
            # Mevcut soru sayılarını getir
            question_counts = await self._get_question_counts_by_topic(topic_id)

            # Uyumluluk skorunu hesapla
            compliance_score = await self._calculate_question_compliance_score(
                question_counts
            )

            # Uyumluluk durumunu belirle
            compliance_status = self._determine_compliance_status(compliance_score)

            compliance = QuestionBankCompliance(
                id=str(uuid4()),
                topic_id=topic_id,
                subject=subject,
                total_questions=question_counts.get("total", 0),
                osym_format_questions=question_counts.get("osym_format", 0),
                meb_aligned_questions=question_counts.get("meb_aligned", 0),
                difficulty_distribution=question_counts.get("difficulty_dist", {}),
                compliance_score=compliance_score,
                minimum_required=self.minimum_questions_per_topic,
                compliance_status=compliance_status,
                next_review_date=datetime.now() + timedelta(days=30),
            )

            return compliance

        except Exception as e:
            logger.error(f"Soru bankası uyumluluk kontrolü hatası: {e}")
            return None

    async def _get_question_counts_by_topic(self, topic_id: str) -> dict[str, Any]:
        """Konuya göre soru sayılarını getir"""
        try:
            if self.db:
                return await self.db.get_question_statistics(topic_id)

            # Mock data for testing
            return {
                "total": 850,
                "osym_format": 720,
                "meb_aligned": 800,
                "difficulty_dist": {"kolay": 300, "orta": 400, "zor": 150},
            }

        except Exception as e:
            logger.error(f"Soru sayıları getirme hatası: {e}")
            return {}

    async def _calculate_question_compliance_score(
        self, question_counts: dict[str, Any]
    ) -> float:
        """Soru uyumluluk skorunu hesapla"""
        try:
            total_questions = question_counts.get("total", 0)
            osym_format = question_counts.get("osym_format", 0)
            meb_aligned = question_counts.get("meb_aligned", 0)

            # Minimum soru sayısı kontrolü
            quantity_score = min(
                1.0, total_questions / self.minimum_questions_per_topic
            )

            # ÖSYM format uyumluluk
            osym_score = osym_format / total_questions if total_questions > 0 else 0

            # MEB uyumluluk
            meb_score = meb_aligned / total_questions if total_questions > 0 else 0

            # Ağırlıklı ortalama
            final_score = (
                (quantity_score * 0.4) + (osym_score * 0.3) + (meb_score * 0.3)
            )

            return min(1.0, max(0.0, final_score))

        except Exception as e:
            logger.error(f"Soru uyumluluk skoru hesaplama hatası: {e}")
            return 0.0

    def _determine_compliance_status(self, score: float) -> str:
        """Uyumluluk durumunu belirle"""
        for status, threshold in self.compliance_thresholds.items():
            if score >= threshold:
                return status
        return "insufficient"

    # Uyumluluk Raporlama

    async def generate_compliance_report(
        self, subject: SubjectType | None = None, exam_type: ExamType | None = None
    ) -> CurriculumComplianceReport:
        """Kapsamlı uyumluluk raporu oluştur"""
        try:
            logger.info("Müfredat uyumluluk raporu oluşturuluyor...")

            # Genel uyumluluk skorları
            meb_score = await self._calculate_overall_meb_compliance(subject)
            osym_score = await self._calculate_overall_osym_compliance(
                exam_type, subject
            )
            overall_score = (meb_score + osym_score) / 2

            # Uyumlu ve uyumsuz konuları tespit et
            (
                compliant_topics,
                non_compliant_topics,
            ) = await self._analyze_topic_compliance(subject, exam_type)

            # Eksik konuları tespit et
            missing_topics = await self._identify_missing_topics(subject, exam_type)

            # Soru bankası durumu
            question_bank_status = await self._analyze_question_bank_status(subject)

            # Öneriler oluştur
            recommendations = await self._generate_compliance_recommendations(
                meb_score, osym_score, non_compliant_topics, missing_topics
            )

            # Öncelikli aksiyonlar
            priority_actions = await self._generate_priority_actions(
                non_compliant_topics, missing_topics
            )

            report = CurriculumComplianceReport(
                id=str(uuid4()),
                report_type="comprehensive_compliance",
                subject=subject,
                exam_type=exam_type,
                overall_compliance_score=overall_score,
                meb_compliance_score=meb_score,
                osym_compliance_score=osym_score,
                compliant_topics=compliant_topics,
                non_compliant_topics=non_compliant_topics,
                missing_topics=missing_topics,
                question_bank_status=question_bank_status,
                recommendations=recommendations,
                priority_actions=priority_actions,
                generated_by="CurriculumComplianceSystem",
                report_period={
                    "start": datetime.now() - timedelta(days=30),
                    "end": datetime.now(),
                },
            )

            logger.info("Müfredat uyumluluk raporu başarıyla oluşturuldu")
            return report

        except Exception as e:
            logger.error(f"Uyumluluk raporu oluşturma hatası: {e}")
            return None

    async def _calculate_overall_meb_compliance(
        self, subject: SubjectType | None = None
    ) -> float:
        """Genel MEB uyumluluk skoru hesapla"""
        try:
            if subject:
                standards = await self.get_meb_standards_by_subject(subject)
            else:
                standards = list(self.meb_standards_cache.values())

            if not standards:
                return 0.0

            total_score = 0.0
            for standard in standards:
                # Her standart için uyumluluk skoru hesapla
                outcomes = await self.get_learning_outcomes(standard.id)
                outcome_score = (
                    len(outcomes) / 10 if outcomes else 0
                )  # Normalize to 0-1
                total_score += min(1.0, outcome_score)

            return total_score / len(standards)

        except Exception as e:
            logger.error(f"MEB uyumluluk skoru hesaplama hatası: {e}")
            return 0.0

    async def _calculate_overall_osym_compliance(
        self, exam_type: ExamType | None = None, subject: SubjectType | None = None
    ) -> float:
        """Genel ÖSYM uyumluluk skoru hesapla"""
        try:
            standards = []

            for standard in self.osym_standards_cache.values():
                if exam_type and standard.exam_type != exam_type:
                    continue
                if subject and standard.subject != subject:
                    continue
                standards.append(standard)

            if not standards:
                return 0.0

            # Öncelik seviyesi ve sınav sıklığına göre ağırlıklı skor
            total_weighted_score = 0.0
            total_weight = 0.0

            for standard in standards:
                # Yüksek öncelik = düşük sayı, bu yüzden ters çevir
                priority_weight = (6 - standard.priority_level) / 5
                frequency_weight = standard.exam_frequency

                weight = (priority_weight + frequency_weight) / 2
                total_weighted_score += weight
                total_weight += 1

            return total_weighted_score / total_weight if total_weight > 0 else 0.0

        except Exception as e:
            logger.error(f"ÖSYM uyumluluk skoru hesaplama hatası: {e}")
            return 0.0

    async def _analyze_topic_compliance(
        self, subject: SubjectType | None = None, exam_type: ExamType | None = None
    ) -> tuple[list[str], list[str]]:
        """Konu uyumluluğunu analiz et"""
        try:
            compliant_topics = []
            non_compliant_topics = []

            # Her konu için uyumluluk kontrolü
            if subject:
                meb_standards = await self.get_meb_standards_by_subject(subject)

                for standard in meb_standards:
                    compliance = await self.validate_question_bank_compliance(
                        subject, standard.id
                    )

                    if compliance and compliance.compliance_score >= 0.7:
                        compliant_topics.append(standard.topic_name)
                    else:
                        non_compliant_topics.append(standard.topic_name)

            return compliant_topics, non_compliant_topics

        except Exception as e:
            logger.error(f"Konu uyumluluk analizi hatası: {e}")
            return [], []

    async def _identify_missing_topics(
        self, subject: SubjectType | None = None, exam_type: ExamType | None = None
    ) -> list[str]:
        """Eksik konuları tespit et"""
        try:
            missing_topics = []

            if subject and exam_type:
                # ÖSYM'de olup MEB'de olmayan konular
                osym_standards = await self.get_osym_standards_by_priority(
                    exam_type, subject
                )
                meb_standards = await self.get_meb_standards_by_subject(subject)

                osym_topics = {std.topic_name for std in osym_standards}
                meb_topics = {std.topic_name for std in meb_standards}

                missing_topics = list(osym_topics - meb_topics)

            return missing_topics

        except Exception as e:
            logger.error(f"Eksik konular tespit etme hatası: {e}")
            return []

    async def _analyze_question_bank_status(
        self, subject: SubjectType | None = None
    ) -> dict[str, QuestionBankCompliance]:
        """Soru bankası durumunu analiz et"""
        try:
            status = {}

            if subject:
                meb_standards = await self.get_meb_standards_by_subject(subject)

                for standard in meb_standards:
                    compliance = await self.validate_question_bank_compliance(
                        subject, standard.id
                    )
                    if compliance:
                        status[standard.topic_name] = compliance

            return status

        except Exception as e:
            logger.error(f"Soru bankası durumu analizi hatası: {e}")
            return {}

    async def _generate_compliance_recommendations(
        self,
        meb_score: float,
        osym_score: float,
        non_compliant_topics: list[str],
        missing_topics: list[str],
    ) -> list[str]:
        """Uyumluluk önerileri oluştur"""
        try:
            recommendations = []

            if meb_score < 0.7:
                recommendations.append(
                    "MEB müfredat standartlarına uyumluluk artırılmalı"
                )

            if osym_score < 0.7:
                recommendations.append(
                    "ÖSYM sınav standartlarına uyumluluk artırılmalı"
                )

            if non_compliant_topics:
                recommendations.append(
                    f"Şu konularda soru sayısı artırılmalı: {', '.join(non_compliant_topics[:3])}"
                )

            if missing_topics:
                recommendations.append(
                    f"Şu konular müfredata eklenmeli: {', '.join(missing_topics[:3])}"
                )

            if not recommendations:
                recommendations.append("Müfredat uyumluluğu yeterli seviyededir")

            return recommendations

        except Exception as e:
            logger.error(f"Öneriler oluşturma hatası: {e}")
            return []

    async def _generate_priority_actions(
        self, non_compliant_topics: list[str], missing_topics: list[str]
    ) -> list[str]:
        """Öncelikli aksiyonlar oluştur"""
        try:
            actions = []

            if non_compliant_topics:
                actions.append(
                    f"Acil: {non_compliant_topics[0]} konusunda 1000 soru hedefine ulaşın"
                )

            if missing_topics:
                actions.append(
                    f"Kritik: {missing_topics[0]} konusu müfredata eklenmeli"
                )

            actions.append("Haftalık uyumluluk kontrolü yapın")

            return actions

        except Exception as e:
            logger.error(f"Öncelikli aksiyonlar oluşturma hatası: {e}")
            return []

    # Müfredat Güncelleme Yönetimi

    async def handle_curriculum_update(
        self, update_request: CurriculumUpdateRequest
    ) -> bool:
        """
        Müfredat güncelleme talebini işle
        Gereksinim 3.4: Müfredat güncellendiğinde sistem uyum sağlamalı
        """
        try:
            logger.info(f"Müfredat güncelleme talebi işleniyor: {update_request.id}")

            # Güncelleme talebini kaydet
            if self.db:
                await self.db.save_curriculum_update_request(update_request)

            # Etkilenen standartları güncelle
            for standard_id in update_request.affected_standards:
                await self._update_standard(standard_id, update_request)

            # Cache'i temizle
            await self._clear_alignment_cache()

            # Yeni uyumluluk analizi başlat
            await self.analyze_curriculum_alignment(
                update_request.subject, ExamType.TYT  # Default exam type
            )

            logger.info("Müfredat güncelleme başarıyla tamamlandı")
            return True

        except Exception as e:
            logger.error(f"Müfredat güncelleme hatası: {e}")
            return False

    async def _update_standard(
        self, standard_id: str, update_request: CurriculumUpdateRequest
    ) -> bool:
        """Belirli bir standardı güncelle"""
        try:
            # MEB standardı mı kontrol et
            if standard_id in self.meb_standards_cache:
                standard = self.meb_standards_cache[standard_id]
                standard.updated_at = datetime.now()

                # Veritabanını güncelle
                if self.db:
                    await self.db.update_meb_standard(standard)

                return True

            # ÖSYM standardı mı kontrol et
            if standard_id in self.osym_standards_cache:
                standard = self.osym_standards_cache[standard_id]
                standard.updated_at = datetime.now()

                # Veritabanını güncelle
                if self.db:
                    await self.db.update_osym_standard(standard)

                return True

            return False

        except Exception as e:
            logger.error(f"Standart güncelleme hatası: {e}")
            return False

    async def _clear_alignment_cache(self):
        """Uyumluluk cache'ini temizle"""
        try:
            self.alignment_cache.clear()

            if self.cache:
                await self.cache.clear_pattern("curriculum_alignment_*")

        except Exception as e:
            logger.error(f"Cache temizleme hatası: {e}")

    # Yardımcı Metodlar

    async def _load_meb_standards(self):
        """MEB standartlarını yükle"""
        try:
            if self.db:
                standards = await self.db.get_all_meb_standards()
                for standard in standards:
                    self.meb_standards_cache[standard.id] = standard

            logger.info(f"{len(self.meb_standards_cache)} MEB standardı yüklendi")

        except Exception as e:
            logger.error(f"MEB standartları yükleme hatası: {e}")

    async def _load_osym_standards(self):
        """ÖSYM standartlarını yükle"""
        try:
            if self.db:
                standards = await self.db.get_all_osym_standards()
                for standard in standards:
                    self.osym_standards_cache[standard.id] = standard

            logger.info(f"{len(self.osym_standards_cache)} ÖSYM standardı yüklendi")

        except Exception as e:
            logger.error(f"ÖSYM standartları yükleme hatası: {e}")

    async def _load_existing_alignments(self):
        """Mevcut eşleştirmeleri yükle"""
        try:
            if self.db:
                alignments = await self.db.get_all_curriculum_alignments()
                for alignment in alignments:
                    self.alignment_cache[alignment.id] = alignment

            logger.info(f"{len(self.alignment_cache)} uyumluluk eşleştirmesi yüklendi")

        except Exception as e:
            logger.error(f"Uyumluluk eşleştirmeleri yükleme hatası: {e}")

    async def get_compliance_summary(self) -> dict[str, Any]:
        """Uyumluluk özeti getir"""
        try:
            return {
                "meb_standards_count": len(self.meb_standards_cache),
                "osym_standards_count": len(self.osym_standards_cache),
                "alignments_count": len(self.alignment_cache),
                "last_updated": datetime.now().isoformat(),
                "system_status": "active",
            }

        except Exception as e:
            logger.error(f"Uyumluluk özeti hatası: {e}")
            return {}
