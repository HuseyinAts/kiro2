"""
Otomatik Soru Üretim Sistemi
ÖSYM formatında müfredata uyumlu soru üretimi
"""

import json
import logging
import random
import re
from typing import Any

from models.curriculum import ExamType, MEBCurriculumStandard, OSYMStandard, SubjectType
from models.question_generation import (
    CognitiveLevel,
    DifficultyLevel,
    GeneratedQuestion,
    OSYMQuestionFormat,
    QuestionBankStatus,
    QuestionGenerationRequest,
    QuestionTemplate,
    QuestionType,
    QuestionValidationResult,
)

logger = logging.getLogger(__name__)


class AutomatedQuestionGenerator:
    """
    Otomatik Soru Üretim Sistemi

    Özellikler:
    - ÖSYM formatında soru üretimi
    - MEB müfredat uyumluluğu
    - 1000+ soru per konu hedefi
    - AI destekli içerik üretimi
    - Kalite kontrol ve doğrulama
    - Öncelik bazlı üretim
    """

    def __init__(
        self,
        curriculum_service=None,
        llm_service=None,
        database_service=None,
        cache_service=None,
    ):
        self.curriculum_service = curriculum_service
        self.llm_service = llm_service
        self.db = database_service
        self.cache = cache_service

        # Üretim parametreleri
        self.target_questions_per_topic = 1000  # Gereksinim 3.2
        self.min_osym_compliance_score = 0.8
        self.min_meb_compliance_score = 0.8
        self.min_quality_score = 0.7

        # Şablon cache
        self.question_templates: dict[str, list[QuestionTemplate]] = {}

        # Üretim istatistikleri
        self.generation_stats = {
            "total_generated": 0,
            "total_validated": 0,
            "total_approved": 0,
            "success_rate": 0.0,
        }

        # ÖSYM format kontrol kuralları
        self.osym_format_rules = {
            "max_question_length": 500,
            "min_options": 4,
            "max_options": 5,
            "option_length_range": (10, 100),
            "required_elements": ["question_text", "options", "correct_answer"],
        }

    async def initialize(self) -> bool:
        """Sistemi başlat ve şablonları yükle"""
        try:
            logger.info("Otomatik soru üretim sistemi başlatılıyor...")

            # Soru şablonlarını yükle
            await self._load_question_templates()

            # Mevcut soru bankası durumunu analiz et
            await self._analyze_current_question_bank()

            logger.info("Otomatik soru üretim sistemi başarıyla başlatıldı")
            return True

        except Exception as e:
            logger.error(f"Soru üretim sistemi başlatma hatası: {e}")
            return False

    # Ana Soru Üretim Metodları

    async def generate_questions_for_topic(
        self,
        topic_id: str,
        subject: SubjectType,
        exam_type: ExamType,
        target_count: int | None = None,
    ) -> list[GeneratedQuestion]:
        """
        Belirli bir konu için soru üret
        Gereksinim 3.2: Her konu için en az 1000 ÖSYM tarzı soru
        """
        try:
            logger.info(f"Konu için soru üretimi başlatılıyor: {topic_id}")

            # Hedef soru sayısını belirle
            if target_count is None:
                target_count = self.target_questions_per_topic

            # Mevcut soru sayısını kontrol et
            current_count = await self._get_current_question_count(topic_id)
            needed_count = max(0, target_count - current_count)

            if needed_count == 0:
                logger.info(f"Konu {topic_id} için yeterli soru mevcut")
                return []

            logger.info(f"Konu {topic_id} için {needed_count} soru üretilecek")

            # MEB ve ÖSYM standartlarını getir
            meb_standards = await self._get_meb_standards_for_topic(topic_id, subject)
            osym_standards = await self._get_osym_standards_for_topic(
                topic_id, subject, exam_type
            )

            # Üretim planını oluştur
            generation_plan = await self._create_generation_plan(
                topic_id,
                subject,
                exam_type,
                needed_count,
                meb_standards,
                osym_standards,
            )

            # Soruları üret
            generated_questions = []
            for plan_item in generation_plan:
                questions = await self._generate_questions_batch(plan_item)
                generated_questions.extend(questions)

            # Kalite kontrolü
            validated_questions = []
            for question in generated_questions:
                validation_result = await self.validate_question(question)
                if validation_result.is_valid:
                    question.is_validated = True
                    validated_questions.append(question)
                else:
                    logger.warning(f"Soru doğrulama başarısız: {question.id}")

            # Veritabanına kaydet
            for question in validated_questions:
                await self._save_generated_question(question)

            logger.info(
                f"Konu {topic_id} için {len(validated_questions)} soru başarıyla üretildi"
            )
            return validated_questions

        except Exception as e:
            logger.error(f"Konu için soru üretimi hatası: {e}")
            return []

    async def process_generation_request(
        self, request: QuestionGenerationRequest
    ) -> dict[str, Any]:
        """Soru üretim talebini işle"""
        try:
            logger.info(f"Soru üretim talebi işleniyor: {request.id}")

            # Talebi kaydet
            await self._save_generation_request(request)

            # Soruları üret
            generated_questions = await self.generate_questions_for_topic(
                request.topic_id,
                request.subject,
                request.exam_type,
                request.question_count,
            )

            # Sonuçları analiz et
            result = {
                "request_id": request.id,
                "requested_count": request.question_count,
                "generated_count": len(generated_questions),
                "success_rate": len(generated_questions) / request.question_count
                if request.question_count > 0
                else 0,
                "questions": [q.id for q in generated_questions],
                "status": "completed" if generated_questions else "failed",
            }

            # Talebi güncelle
            await self._update_generation_request(request.id, result["status"])

            logger.info(f"Soru üretim talebi tamamlandı: {request.id}")
            return result

        except Exception as e:
            logger.error(f"Soru üretim talebi işleme hatası: {e}")
            return {"request_id": request.id, "status": "error", "error": str(e)}

    # Soru Üretim Planlaması

    async def _create_generation_plan(
        self,
        topic_id: str,
        subject: SubjectType,
        exam_type: ExamType,
        target_count: int,
        meb_standards: list[MEBCurriculumStandard],
        osym_standards: list[OSYMStandard],
    ) -> list[dict[str, Any]]:
        """Soru üretim planı oluştur"""
        try:
            plan = []

            # Zorluk dağılımı (ÖSYM standartlarına göre)
            difficulty_distribution = {
                DifficultyLevel.KOLAY: 0.3,
                DifficultyLevel.ORTA: 0.5,
                DifficultyLevel.ZOR: 0.2,
            }

            # Bilişsel seviye dağılımı
            cognitive_distribution = {
                CognitiveLevel.BILGI: 0.2,
                CognitiveLevel.KAVRAMA: 0.3,
                CognitiveLevel.UYGULAMA: 0.3,
                CognitiveLevel.ANALIZ: 0.15,
                CognitiveLevel.SENTEZ: 0.05,
            }

            # Soru türü dağılımı
            type_distribution = {
                QuestionType.MULTIPLE_CHOICE: 0.8,
                QuestionType.TRUE_FALSE: 0.1,
                QuestionType.FILL_IN_BLANK: 0.1,
            }

            # Her kombinasyon için plan oluştur
            for difficulty, diff_ratio in difficulty_distribution.items():
                for cognitive, cog_ratio in cognitive_distribution.items():
                    for question_type, type_ratio in type_distribution.items():
                        # Bu kombinasyon için soru sayısı
                        count = int(target_count * diff_ratio * cog_ratio * type_ratio)

                        if count > 0:
                            plan_item = {
                                "topic_id": topic_id,
                                "subject": subject,
                                "exam_type": exam_type,
                                "question_type": question_type,
                                "difficulty_level": difficulty,
                                "cognitive_level": cognitive,
                                "count": count,
                                "meb_standards": meb_standards,
                                "osym_standards": osym_standards,
                            }
                            plan.append(plan_item)

            return plan

        except Exception as e:
            logger.error(f"Üretim planı oluşturma hatası: {e}")
            return []

    async def _generate_questions_batch(
        self, plan_item: dict[str, Any]
    ) -> list[GeneratedQuestion]:
        """Belirli kriterlere göre soru grubu üret"""
        try:
            questions = []

            # Şablonları getir
            templates = await self._get_templates_for_criteria(
                plan_item["subject"],
                plan_item["question_type"],
                plan_item["difficulty_level"],
                plan_item["cognitive_level"],
            )

            if not templates:
                # Şablon yoksa AI ile üret
                questions = await self._generate_with_ai(plan_item)
            else:
                # Şablon tabanlı üretim
                questions = await self._generate_with_templates(plan_item, templates)

            return questions

        except Exception as e:
            logger.error(f"Soru grubu üretimi hatası: {e}")
            return []

    async def _generate_with_templates(
        self, plan_item: dict[str, Any], templates: list[QuestionTemplate]
    ) -> list[GeneratedQuestion]:
        """Şablon tabanlı soru üretimi"""
        try:
            questions = []
            target_count = plan_item["count"]

            for i in range(target_count):
                # Rastgele şablon seç
                template = random.choice(templates)

                # Şablonu doldur
                question = await self._fill_template(template, plan_item)

                if question:
                    questions.append(question)

            return questions

        except Exception as e:
            logger.error(f"Şablon tabanlı üretim hatası: {e}")
            return []

    async def _generate_with_ai(
        self, plan_item: dict[str, Any]
    ) -> list[GeneratedQuestion]:
        """AI tabanlı soru üretimi"""
        try:
            if not self.llm_service:
                logger.warning("LLM servisi mevcut değil, AI üretim atlanıyor")
                return []

            questions = []
            target_count = plan_item["count"]

            # AI prompt oluştur
            prompt = await self._create_ai_generation_prompt(plan_item)

            # AI ile soru üret
            for i in range(min(target_count, 10)):  # Batch olarak üret
                try:
                    response = await self.llm_service.generate(
                        prompt=prompt, temperature=0.7, max_tokens=1000
                    )

                    if response.get("success"):
                        question = await self._parse_ai_response(
                            response["text"], plan_item
                        )
                        if question:
                            questions.append(question)

                except Exception as e:
                    logger.error(f"AI soru üretimi hatası: {e}")
                    continue

            return questions

        except Exception as e:
            logger.error(f"AI tabanlı üretim hatası: {e}")
            return []

    async def _create_ai_generation_prompt(self, plan_item: dict[str, Any]) -> str:
        """AI için soru üretim prompt'u oluştur"""
        try:
            subject_name = {
                SubjectType.MATEMATIK: "Matematik",
                SubjectType.TURKCE: "Türkçe",
                SubjectType.FEN_BILIMLERI: "Fen Bilimleri",
                SubjectType.FIZIK: "Fizik",
                SubjectType.KIMYA: "Kimya",
                SubjectType.BIYOLOJI: "Biyoloji",
            }.get(plan_item["subject"], plan_item["subject"].value)

            difficulty_name = {
                DifficultyLevel.KOLAY: "kolay",
                DifficultyLevel.ORTA: "orta",
                DifficultyLevel.ZOR: "zor",
            }.get(plan_item["difficulty_level"], "orta")

            cognitive_name = {
                CognitiveLevel.BILGI: "bilgi düzeyinde",
                CognitiveLevel.KAVRAMA: "kavrama düzeyinde",
                CognitiveLevel.UYGULAMA: "uygulama düzeyinde",
                CognitiveLevel.ANALIZ: "analiz düzeyinde",
                CognitiveLevel.SENTEZ: "sentez düzeyinde",
            }.get(plan_item["cognitive_level"], "kavrama düzeyinde")

            prompt = f"""
{subject_name} dersi için ÖSYM formatında çoktan seçmeli soru oluştur.

Konu: {plan_item["topic_id"]}
Zorluk Seviyesi: {difficulty_name}
Bilişsel Seviye: {cognitive_name}
Sınav Türü: {plan_item["exam_type"].value.upper()}

Gereksinimler:
1. Soru metni açık ve anlaşılır olmalı
2. 4 seçenek (A, B, C, D) olmalı
3. Sadece bir doğru cevap olmalı
4. Çeldirici seçenekler mantıklı olmalı
5. ÖSYM soru formatına uygun olmalı
6. Türkçe dil kurallarına uygun olmalı
7. MEB müfredat standartlarına uygun olmalı

Format:
SORU: [Soru metni]

A) [Seçenek A]
B) [Seçenek B]
C) [Seçenek C]
D) [Seçenek D]

DOĞRU CEVAP: [A, B, C veya D]

AÇIKLAMA: [Çözüm açıklaması]

Lütfen yukarıdaki formatta bir soru oluştur:
"""

            return prompt

        except Exception as e:
            logger.error(f"AI prompt oluşturma hatası: {e}")
            return ""

    async def _parse_ai_response(
        self, ai_response: str, plan_item: dict[str, Any]
    ) -> GeneratedQuestion | None:
        """AI yanıtını parse et ve soru objesi oluştur"""
        try:
            # Regex ile soru bileşenlerini çıkar
            question_pattern = r"SORU:\s*(.+?)(?=\n\n|\nA\))"
            options_pattern = r"([A-D])\)\s*(.+?)(?=\n[A-D]\)|\nDOĞRU|\n\n|$)"
            answer_pattern = r"DOĞRU CEVAP:\s*([A-D])"
            explanation_pattern = r"AÇIKLAMA:\s*(.+?)(?=\n\n|$)"

            # Soru metnini çıkar
            question_match = re.search(question_pattern, ai_response, re.DOTALL)
            if not question_match:
                logger.warning("AI yanıtında soru metni bulunamadı")
                return None

            question_text = question_match.group(1).strip()

            # Seçenekleri çıkar
            options_matches = re.findall(options_pattern, ai_response, re.DOTALL)
            if len(options_matches) != 4:
                logger.warning(
                    f"AI yanıtında 4 seçenek bulunamadı: {len(options_matches)}"
                )
                return None

            options = [match[1].strip() for match in options_matches]

            # Doğru cevabı çıkar
            answer_match = re.search(answer_pattern, ai_response)
            if not answer_match:
                logger.warning("AI yanıtında doğru cevap bulunamadı")
                return None

            correct_answer = answer_match.group(1).strip()

            # Açıklamayı çıkar
            explanation_match = re.search(explanation_pattern, ai_response, re.DOTALL)
            explanation = (
                explanation_match.group(1).strip()
                if explanation_match
                else "Açıklama mevcut değil"
            )

            # ÖSYM format objesi oluştur
            osym_format = OSYMQuestionFormat(
                question_number=1,
                question_text=question_text,
                options=options,
                correct_answer=correct_answer,
                explanation=explanation,
            )

            # Soru objesi oluştur
            question = GeneratedQuestion(
                subject=plan_item["subject"],
                topic_id=plan_item["topic_id"],
                topic_name=plan_item.get("topic_name", "Bilinmeyen Konu"),
                question_type=plan_item["question_type"],
                question_text=question_text,
                options=options,
                correct_answer=correct_answer,
                explanation=explanation,
                difficulty_level=plan_item["difficulty_level"],
                cognitive_level=plan_item["cognitive_level"],
                osym_format=osym_format,
                generation_method="ai_assisted",
                generation_parameters={
                    "model": "llm_service",
                    "temperature": 0.7,
                    "prompt_version": "v1.0",
                },
            )

            return question

        except Exception as e:
            logger.error(f"AI yanıt parse etme hatası: {e}")
            return None

    # Soru Doğrulama ve Kalite Kontrolü

    async def validate_question(
        self, question: GeneratedQuestion
    ) -> QuestionValidationResult:
        """
        Soru doğrulama ve kalite kontrolü
        Gereksinim 3.5: ÖSYM format uyumluluk doğrulaması
        """
        try:
            validation_checks = {}
            errors = []
            warnings = []
            suggestions = []

            # ÖSYM format kontrolü
            osym_score = await self._validate_osym_format(
                question, validation_checks, errors, warnings
            )

            # MEB uyumluluk kontrolü
            meb_score = await self._validate_meb_compliance(
                question, validation_checks, errors, warnings
            )

            # Kalite kontrolü
            quality_score = await self._validate_question_quality(
                question, validation_checks, warnings, suggestions
            )

            # Okunabilirlik kontrolü
            readability_score = await self._validate_readability(
                question, validation_checks, suggestions
            )

            # Genel doğrulama skoru
            overall_score = (
                osym_score + meb_score + quality_score + readability_score
            ) / 4
            is_valid = (
                osym_score >= self.min_osym_compliance_score
                and meb_score >= self.min_meb_compliance_score
                and quality_score >= self.min_quality_score
                and len(errors) == 0
            )

            # Skorları güncelle
            question.osym_compliance_score = osym_score
            question.meb_compliance_score = meb_score
            question.quality_score = quality_score
            question.readability_score = readability_score

            result = QuestionValidationResult(
                question_id=question.id,
                is_valid=is_valid,
                osym_compliance_score=osym_score,
                meb_compliance_score=meb_score,
                quality_score=quality_score,
                readability_score=readability_score,
                validation_checks=validation_checks,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions,
                validated_by="AutomatedQuestionGenerator",
                validation_method="automated",
            )

            return result

        except Exception as e:
            logger.error(f"Soru doğrulama hatası: {e}")
            return QuestionValidationResult(
                question_id=question.id,
                is_valid=False,
                osym_compliance_score=0.0,
                meb_compliance_score=0.0,
                quality_score=0.0,
                readability_score=0.0,
                errors=[f"Doğrulama hatası: {e!s}"],
                validated_by="AutomatedQuestionGenerator",
                validation_method="automated",
            )

    async def _validate_osym_format(
        self,
        question: GeneratedQuestion,
        validation_checks: dict[str, bool],
        errors: list[str],
        warnings: list[str],
    ) -> float:
        """ÖSYM format uyumluluğunu kontrol et"""
        try:
            score = 0.0
            total_checks = 0

            # Soru metni uzunluğu kontrolü
            total_checks += 1
            if (
                len(question.question_text)
                <= self.osym_format_rules["max_question_length"]
            ):
                validation_checks["question_length_ok"] = True
                score += 1
            else:
                validation_checks["question_length_ok"] = False
                errors.append(
                    f"Soru metni çok uzun: {len(question.question_text)} karakter"
                )

            # Seçenek sayısı kontrolü
            total_checks += 1
            option_count = len(question.options)
            if (
                self.osym_format_rules["min_options"]
                <= option_count
                <= self.osym_format_rules["max_options"]
            ):
                validation_checks["option_count_ok"] = True
                score += 1
            else:
                validation_checks["option_count_ok"] = False
                errors.append(f"Geçersiz seçenek sayısı: {option_count}")

            # Seçenek uzunluğu kontrolü
            total_checks += 1
            option_lengths_ok = True
            for i, option in enumerate(question.options):
                min_len, max_len = self.osym_format_rules["option_length_range"]
                if not (min_len <= len(option) <= max_len):
                    option_lengths_ok = False
                    warnings.append(
                        f"Seçenek {i+1} uzunluğu uygun değil: {len(option)} karakter"
                    )

            validation_checks["option_lengths_ok"] = option_lengths_ok
            if option_lengths_ok:
                score += 1

            # Doğru cevap kontrolü
            total_checks += 1
            valid_answers = ["A", "B", "C", "D", "E"][: len(question.options)]
            if question.correct_answer in valid_answers:
                validation_checks["correct_answer_valid"] = True
                score += 1
            else:
                validation_checks["correct_answer_valid"] = False
                errors.append(f"Geçersiz doğru cevap: {question.correct_answer}")

            # Açıklama kontrolü
            total_checks += 1
            if question.explanation and len(question.explanation.strip()) > 10:
                validation_checks["explanation_exists"] = True
                score += 1
            else:
                validation_checks["explanation_exists"] = False
                warnings.append("Açıklama eksik veya çok kısa")

            return score / total_checks if total_checks > 0 else 0.0

        except Exception as e:
            logger.error(f"ÖSYM format doğrulama hatası: {e}")
            return 0.0

    async def _validate_meb_compliance(
        self,
        question: GeneratedQuestion,
        validation_checks: dict[str, bool],
        errors: list[str],
        warnings: list[str],
    ) -> float:
        """MEB uyumluluk kontrolü"""
        try:
            score = 0.0
            total_checks = 0

            # MEB standardı bağlantısı kontrolü
            total_checks += 1
            if question.meb_standard_id:
                validation_checks["meb_standard_linked"] = True
                score += 1
            else:
                validation_checks["meb_standard_linked"] = False
                warnings.append("MEB standardı bağlantısı eksik")

            # Öğrenme kazanımı kontrolü
            total_checks += 1
            if question.learning_outcome_ids:
                validation_checks["learning_outcomes_linked"] = True
                score += 1
            else:
                validation_checks["learning_outcomes_linked"] = False
                warnings.append("Öğrenme kazanımı bağlantısı eksik")

            # Bilişsel seviye uygunluğu
            total_checks += 1
            valid_cognitive_levels = [level.value for level in CognitiveLevel]
            if question.cognitive_level.value in valid_cognitive_levels:
                validation_checks["cognitive_level_valid"] = True
                score += 1
            else:
                validation_checks["cognitive_level_valid"] = False
                errors.append(f"Geçersiz bilişsel seviye: {question.cognitive_level}")

            # Konu uygunluğu (basit kontrol)
            total_checks += 1
            if question.topic_id and question.topic_name:
                validation_checks["topic_alignment"] = True
                score += 1
            else:
                validation_checks["topic_alignment"] = False
                warnings.append("Konu bilgileri eksik")

            return score / total_checks if total_checks > 0 else 0.0

        except Exception as e:
            logger.error(f"MEB uyumluluk doğrulama hatası: {e}")
            return 0.0

    async def _validate_question_quality(
        self,
        question: GeneratedQuestion,
        validation_checks: dict[str, bool],
        warnings: list[str],
        suggestions: list[str],
    ) -> float:
        """Soru kalitesi kontrolü"""
        try:
            score = 0.0
            total_checks = 0

            # Soru netliği kontrolü
            total_checks += 1
            question_clarity = await self._check_question_clarity(
                question.question_text
            )
            validation_checks["question_clarity"] = question_clarity
            if question_clarity:
                score += 1
            else:
                warnings.append("Soru metni belirsiz veya karmaşık")

            # Seçenek kalitesi kontrolü
            total_checks += 1
            options_quality = await self._check_options_quality(
                question.options, question.correct_answer
            )
            validation_checks["options_quality"] = options_quality
            if options_quality:
                score += 1
            else:
                warnings.append("Seçenekler arasında kalite sorunları var")

            # Çeldirici kalitesi kontrolü
            total_checks += 1
            distractors_quality = await self._check_distractors_quality(
                question.options, question.correct_answer
            )
            validation_checks["distractors_quality"] = distractors_quality
            if distractors_quality:
                score += 1
            else:
                suggestions.append("Çeldirici seçenekler daha mantıklı olabilir")

            # Dil ve yazım kontrolü
            total_checks += 1
            language_quality = await self._check_language_quality(question)
            validation_checks["language_quality"] = language_quality
            if language_quality:
                score += 1
            else:
                warnings.append("Dil ve yazım sorunları tespit edildi")

            return score / total_checks if total_checks > 0 else 0.0

        except Exception as e:
            logger.error(f"Kalite kontrolü hatası: {e}")
            return 0.0

    async def _validate_readability(
        self,
        question: GeneratedQuestion,
        validation_checks: dict[str, bool],
        suggestions: list[str],
    ) -> float:
        """Okunabilirlik kontrolü"""
        try:
            # Basit okunabilirlik metrikleri
            text = question.question_text + " " + " ".join(question.options)

            # Ortalama kelime uzunluğu
            words = text.split()
            avg_word_length = (
                sum(len(word) for word in words) / len(words) if words else 0
            )

            # Ortalama cümle uzunluğu
            sentences = text.split(".")
            avg_sentence_length = len(words) / len(sentences) if sentences else 0

            # Karmaşık kelime oranı (5+ harf)
            complex_words = [word for word in words if len(word) > 5]
            complex_ratio = len(complex_words) / len(words) if words else 0

            # Okunabilirlik skoru hesapla (basitleştirilmiş)
            readability_score = 1.0

            if avg_word_length > 8:
                readability_score -= 0.2
                suggestions.append("Daha kısa kelimeler kullanılabilir")

            if avg_sentence_length > 20:
                readability_score -= 0.2
                suggestions.append("Daha kısa cümleler kullanılabilir")

            if complex_ratio > 0.3:
                readability_score -= 0.2
                suggestions.append("Daha basit kelimeler tercih edilebilir")

            validation_checks["readability_ok"] = readability_score >= 0.6

            return max(0.0, readability_score)

        except Exception as e:
            logger.error(f"Okunabilirlik kontrolü hatası: {e}")
            return 0.0

    # Yardımcı Metodlar

    async def _check_question_clarity(self, question_text: str) -> bool:
        """Soru netliği kontrolü"""
        try:
            # Basit netlik kontrolleri
            if len(question_text.strip()) < 10:
                return False

            # Soru işareti kontrolü
            if (
                not question_text.strip().endswith("?")
                and "hangisi" not in question_text.lower()
            ):
                return False

            # Belirsiz ifadeler kontrolü
            unclear_phrases = ["belki", "muhtemelen", "sanırım", "galiba"]
            for phrase in unclear_phrases:
                if phrase in question_text.lower():
                    return False

            return True

        except Exception as e:
            logger.error(f"Soru netliği kontrolü hatası: {e}")
            return False

    async def _check_options_quality(
        self, options: list[str], correct_answer: str
    ) -> bool:
        """Seçenek kalitesi kontrolü"""
        try:
            if len(options) < 4:
                return False

            # Seçenekler arasında uzunluk farkı kontrolü
            lengths = [len(option) for option in options]
            max_length = max(lengths)
            min_length = min(lengths)

            if max_length > min_length * 3:  # Çok büyük fark varsa
                return False

            # Tekrar eden seçenek kontrolü
            if len(set(options)) != len(options):
                return False

            return True

        except Exception as e:
            logger.error(f"Seçenek kalitesi kontrolü hatası: {e}")
            return False

    async def _check_distractors_quality(
        self, options: list[str], correct_answer: str
    ) -> bool:
        """Çeldirici kalitesi kontrolü"""
        try:
            # Doğru cevap indeksini bul
            correct_index = (
                ord(correct_answer) - ord("A") if correct_answer in "ABCDE" else -1
            )

            if correct_index < 0 or correct_index >= len(options):
                return False

            correct_option = options[correct_index]
            distractors = [opt for i, opt in enumerate(options) if i != correct_index]

            # Çeldiriciler çok benzer olmamalı
            for distractor in distractors:
                similarity = self._calculate_text_similarity(correct_option, distractor)
                if similarity > 0.8:  # Çok benzer
                    return False

            return True

        except Exception as e:
            logger.error(f"Çeldirici kalitesi kontrolü hatası: {e}")
            return False

    async def _check_language_quality(self, question: GeneratedQuestion) -> bool:
        """Dil ve yazım kalitesi kontrolü"""
        try:
            # Basit Türkçe yazım kontrolleri
            text = question.question_text + " " + " ".join(question.options)

            # Büyük harf kontrolü
            if not text[0].isupper():
                return False

            # Noktalama kontrolü
            if text.count("..") > 0 or text.count("??") > 0:
                return False

            # Türkçe karakter kontrolü
            turkish_chars = "çğıöşüÇĞIİÖŞÜ"
            has_turkish = any(char in text for char in turkish_chars)

            return True  # Basit kontroller geçti

        except Exception as e:
            logger.error(f"Dil kalitesi kontrolü hatası: {e}")
            return False

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """İki metin arasındaki benzerlik oranını hesapla"""
        try:
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())

            intersection = words1.intersection(words2)
            union = words1.union(words2)

            return len(intersection) / len(union) if union else 0.0

        except Exception as e:
            logger.error(f"Metin benzerliği hesaplama hatası: {e}")
            return 0.0

    # Soru Bankası Analizi ve Raporlama

    async def analyze_question_bank_status(
        self, subject: SubjectType | None = None
    ) -> list[QuestionBankStatus]:
        """
        Soru bankası durumunu analiz et
        Gereksinim 3.2: Her konu için 1000+ soru kontrolü
        """
        try:
            logger.info("Soru bankası durumu analiz ediliyor...")

            status_list = []

            # Konuları getir
            if subject:
                topics = await self._get_topics_by_subject(subject)
            else:
                topics = await self._get_all_topics()

            for topic in topics:
                # Mevcut soru sayılarını getir
                question_counts = await self._get_detailed_question_counts(topic["id"])

                # Tamamlanma yüzdesini hesapla
                completion_percentage = min(
                    100.0,
                    (question_counts["approved"] / self.target_questions_per_topic)
                    * 100,
                )

                # Durumu belirle
                if question_counts["approved"] >= self.target_questions_per_topic:
                    status = "completed"
                elif (
                    question_counts["approved"] >= self.target_questions_per_topic * 0.8
                ):
                    status = "nearly_complete"
                elif (
                    question_counts["approved"] >= self.target_questions_per_topic * 0.5
                ):
                    status = "in_progress"
                else:
                    status = "insufficient"

                # Kalite metriklerini hesapla
                quality_metrics = await self._calculate_topic_quality_metrics(
                    topic["id"]
                )

                # Dağılımları getir
                distributions = await self._get_topic_distributions(topic["id"])

                topic_status = QuestionBankStatus(
                    topic_id=topic["id"],
                    topic_name=topic["name"],
                    subject=topic["subject"],
                    total_questions=question_counts["total"],
                    validated_questions=question_counts["validated"],
                    approved_questions=question_counts["approved"],
                    target_question_count=self.target_questions_per_topic,
                    completion_percentage=completion_percentage,
                    average_quality_score=quality_metrics["quality"],
                    average_osym_compliance=quality_metrics["osym"],
                    average_meb_compliance=quality_metrics["meb"],
                    difficulty_distribution=distributions["difficulty"],
                    cognitive_distribution=distributions["cognitive"],
                    type_distribution=distributions["type"],
                    status=status,
                )

                status_list.append(topic_status)

            # Öncelik sırasına göre sırala (eksik olanlar önce)
            status_list.sort(key=lambda x: (x.completion_percentage, x.topic_name))

            logger.info(f"Soru bankası analizi tamamlandı: {len(status_list)} konu")
            return status_list

        except Exception as e:
            logger.error(f"Soru bankası analizi hatası: {e}")
            return []

    async def generate_priority_based_questions(
        self, max_topics: int = 10
    ) -> dict[str, Any]:
        """
        Öncelik bazlı soru üretimi
        Gereksinim 3.5: ÖSYM standartlarına göre önceliklendirme
        """
        try:
            logger.info("Öncelik bazlı soru üretimi başlatılıyor...")

            # Soru bankası durumunu analiz et
            bank_status = await self.analyze_question_bank_status()

            # Öncelikli konuları belirle
            priority_topics = []
            for status in bank_status:
                if status.status in ["insufficient", "in_progress"]:
                    # ÖSYM öncelik skorunu hesapla
                    osym_priority = await self._calculate_osym_priority_score(
                        status.topic_id, status.subject
                    )

                    priority_topics.append(
                        {
                            "topic_id": status.topic_id,
                            "topic_name": status.topic_name,
                            "subject": status.subject,
                            "needed_questions": self.target_questions_per_topic
                            - status.approved_questions,
                            "osym_priority": osym_priority,
                            "completion_percentage": status.completion_percentage,
                        }
                    )

            # Öncelik skoruna göre sırala
            priority_topics.sort(
                key=lambda x: (-x["osym_priority"], x["completion_percentage"])
            )

            # En öncelikli konular için soru üret
            generation_results = []
            for i, topic in enumerate(priority_topics[:max_topics]):
                logger.info(f"Öncelikli konu için soru üretimi: {topic['topic_name']}")

                questions = await self.generate_questions_for_topic(
                    topic["topic_id"],
                    topic["subject"],
                    ExamType.TYT,  # Default olarak TYT
                    min(topic["needed_questions"], 100),  # Batch olarak üret
                )

                generation_results.append(
                    {
                        "topic_id": topic["topic_id"],
                        "topic_name": topic["topic_name"],
                        "generated_count": len(questions),
                        "needed_count": topic["needed_questions"],
                        "osym_priority": topic["osym_priority"],
                    }
                )

            # Sonuçları özetle
            total_generated = sum(
                result["generated_count"] for result in generation_results
            )

            summary = {
                "total_priority_topics": len(priority_topics),
                "processed_topics": len(generation_results),
                "total_questions_generated": total_generated,
                "generation_results": generation_results,
                "next_priority_topics": priority_topics[max_topics : max_topics + 5]
                if len(priority_topics) > max_topics
                else [],
            }

            logger.info(
                f"Öncelik bazlı üretim tamamlandı: {total_generated} soru üretildi"
            )
            return summary

        except Exception as e:
            logger.error(f"Öncelik bazlı üretim hatası: {e}")
            return {"error": str(e)}

    # Veritabanı İşlemleri (Mock)

    async def _get_current_question_count(self, topic_id: str) -> int:
        """Mevcut soru sayısını getir"""
        try:
            if self.db:
                query = "SELECT COUNT(*) FROM questions WHERE topic_id = %s AND is_approved = true"
                result = await self.db.fetch_one(query, [topic_id])
                return result[0] if result else 0

            # Mock data
            return random.randint(200, 800)

        except Exception as e:
            logger.error(f"Soru sayısı getirme hatası: {e}")
            return 0

    async def _save_generated_question(self, question: GeneratedQuestion) -> bool:
        """Üretilen soruyu kaydet"""
        try:
            if self.db:
                # Veritabanına kaydet
                query = """
                INSERT INTO generated_questions (
                    id, subject, topic_id, question_type, question_text,
                    options, correct_answer, explanation, difficulty_level,
                    cognitive_level, osym_compliance_score, meb_compliance_score,
                    quality_score, is_validated, is_approved, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """

                values = (
                    question.id,
                    question.subject.value,
                    question.topic_id,
                    question.question_type.value,
                    question.question_text,
                    json.dumps(question.options),
                    question.correct_answer,
                    question.explanation,
                    question.difficulty_level.value,
                    question.cognitive_level.value,
                    question.osym_compliance_score,
                    question.meb_compliance_score,
                    question.quality_score,
                    question.is_validated,
                    question.is_approved,
                    question.created_at,
                )

                await self.db.execute(query, values)

            # İstatistikleri güncelle
            self.generation_stats["total_generated"] += 1
            if question.is_validated:
                self.generation_stats["total_validated"] += 1
            if question.is_approved:
                self.generation_stats["total_approved"] += 1

            return True

        except Exception as e:
            logger.error(f"Soru kaydetme hatası: {e}")
            return False

    # Diğer yardımcı metodlar için placeholder'lar

    async def _load_question_templates(self):
        """Soru şablonlarını yükle"""

    async def _analyze_current_question_bank(self):
        """Mevcut soru bankasını analiz et"""

    async def _get_meb_standards_for_topic(self, topic_id: str, subject: SubjectType):
        """Konu için MEB standartlarını getir"""
        return []

    async def _get_osym_standards_for_topic(
        self, topic_id: str, subject: SubjectType, exam_type: ExamType
    ):
        """Konu için ÖSYM standartlarını getir"""
        return []

    async def _get_templates_for_criteria(
        self, subject, question_type, difficulty, cognitive
    ):
        """Kriterlere uygun şablonları getir"""
        return []

    async def _fill_template(
        self, template: QuestionTemplate, plan_item: dict[str, Any]
    ):
        """Şablonu doldur"""
        return

    async def _save_generation_request(self, request: QuestionGenerationRequest):
        """Üretim talebini kaydet"""

    async def _update_generation_request(self, request_id: str, status: str):
        """Üretim talebini güncelle"""

    async def _get_topics_by_subject(self, subject: SubjectType):
        """Derse göre konuları getir"""
        return []

    async def _get_all_topics(self):
        """Tüm konuları getir"""
        return []

    async def _get_detailed_question_counts(self, topic_id: str):
        """Detaylı soru sayılarını getir"""
        return {"total": 0, "validated": 0, "approved": 0}

    async def _calculate_topic_quality_metrics(self, topic_id: str):
        """Konu kalite metriklerini hesapla"""
        return {"quality": 0.0, "osym": 0.0, "meb": 0.0}

    async def _get_topic_distributions(self, topic_id: str):
        """Konu dağılımlarını getir"""
        return {"difficulty": {}, "cognitive": {}, "type": {}}

    async def _calculate_osym_priority_score(self, topic_id: str, subject: SubjectType):
        """ÖSYM öncelik skorunu hesapla"""
        return random.uniform(0.5, 1.0)
