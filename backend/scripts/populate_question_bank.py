"""
Soru bankası veri yükleme scripti
Gerçek soru verilerini database'e yükler ve IRT kalibrasyonu yapar
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Backend modüllerini import edebilmek için path ekle
sys.path.append(str(Path(__file__).parent.parent))

from core.database import get_db_session
from data.question_bank_data import QuestionBankData
from models.database import ExamType, QuestionDifficulty, SubjectArea
from models.question_bank import QuestionBankItem as Question
from services.irt_calibration_service import IRTCalibrationService
from services.soru_bankasi_service import SoruBankasiServisi

# Logging konfigürasyonu
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("question_bank_population.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class QuestionBankPopulator:
    """Soru bankası veri yükleme sınıfı"""

    def __init__(self):
        self.question_data = QuestionBankData()
        self.irt_service = IRTCalibrationService()
        self.soru_bankasi_service = SoruBankasiServisi()

        # Enum mapping'leri
        self.exam_type_map = {
            "TYT": ExamType.TYT,
            "AYT": ExamType.AYT,
            "YDT": ExamType.YDT,
        }

        self.difficulty_map = {
            "kolay": QuestionDifficulty.EASY,
            "orta": QuestionDifficulty.MEDIUM,
            "zor": QuestionDifficulty.HARD,
        }

        self.subject_map = {
            "Matematik": SubjectArea.MATEMATIK,
            "Türkçe": SubjectArea.TURKCE,
            "Fen": SubjectArea.FEN,
            "Sosyal": SubjectArea.SOSYAL,
            "Fizik": SubjectArea.FIZIK,
            "Kimya": SubjectArea.KIMYA,
            "Biyoloji": SubjectArea.BIYOLOJI,
            "İngilizce": SubjectArea.INGILIZCE,
        }

    async def populate_all_questions(self) -> dict[str, Any]:
        """Tüm soruları database'e yükle"""

        logger.info("Soru bankası veri yükleme işlemi başlatıldı")

        results = {
            "total_questions_processed": 0,
            "successful_insertions": 0,
            "failed_insertions": 0,
            "calibration_results": {},
            "processing_time": 0,
            "errors": [],
        }

        start_time = datetime.now()

        try:
            # Tüm soruları al
            all_questions = self.question_data.get_all_questions()
            results["total_questions_processed"] = len(all_questions)

            logger.info(f"Toplam {len(all_questions)} soru işlenecek")

            # Batch'ler halinde işle
            batch_size = 100
            for i in range(0, len(all_questions), batch_size):
                batch = all_questions[i : i + batch_size]
                batch_results = await self._process_question_batch(
                    batch, i // batch_size + 1
                )

                results["successful_insertions"] += batch_results["successful"]
                results["failed_insertions"] += batch_results["failed"]
                results["errors"].extend(batch_results["errors"])

                logger.info(
                    f"Batch {i // batch_size + 1} tamamlandı - Başarılı: {batch_results['successful']}, Hatalı: {batch_results['failed']}"
                )

            # IRT kalibrasyonu
            logger.info("IRT kalibrasyon işlemi başlatılıyor...")
            calibration_results = await self._perform_irt_calibration(all_questions)
            results["calibration_results"] = calibration_results

            # İstatistikler
            stats = await self._generate_statistics()
            results["final_statistics"] = stats

        except Exception as e:
            logger.error(f"Genel hata: {e!s}")
            results["errors"].append(f"Genel hata: {e!s}")

        finally:
            end_time = datetime.now()
            results["processing_time"] = (end_time - start_time).total_seconds()

            logger.info(
                f"Soru bankası yükleme tamamlandı - Süre: {results['processing_time']:.2f} saniye"
            )
            logger.info(
                f"Başarılı: {results['successful_insertions']}, Hatalı: {results['failed_insertions']}"
            )

        return results

    async def _process_question_batch(
        self, questions: list[dict[str, Any]], batch_number: int
    ) -> dict[str, Any]:
        """Soru batch'ini işle"""

        batch_results = {"successful": 0, "failed": 0, "errors": []}

        async with get_db_session() as session:
            try:
                for question_data in questions:
                    try:
                        # IRT kalibrasyonu
                        irt_params = await self.irt_service.calibrate_question_irt(
                            question_text=question_data["soru_metni"],
                            options=question_data["secenekler"],
                            subject=question_data["konu"],
                            initial_difficulty=question_data["zorluk_seviyesi"],
                        )

                        # Database modeli oluştur
                        question = Question(
                            question_text=question_data["soru_metni"],
                            option_a=question_data["secenekler"][0].replace("A) ", ""),
                            option_b=question_data["secenekler"][1].replace("B) ", ""),
                            option_c=question_data["secenekler"][2].replace("C) ", ""),
                            option_d=question_data["secenekler"][3].replace("D) ", ""),
                            option_e=question_data["secenekler"][4].replace("E) ", "")
                            if len(question_data["secenekler"]) > 4
                            else None,
                            correct_answer=question_data["dogru_cevap"],
                            explanation=question_data.get("cozum_aciklamasi"),
                            exam_type=self.exam_type_map[question_data["sinav_tipi"]],
                            subject_area=self.subject_map[question_data["konu"]],
                            topic=question_data.get("alt_konu", question_data["konu"]),
                            subtopic=question_data.get("alt_konu"),
                            difficulty=self.difficulty_map[
                                question_data["zorluk_seviyesi"]
                            ],
                            irt_difficulty=irt_params.difficulty,
                            irt_discrimination=irt_params.discrimination,
                            irt_guessing=irt_params.guessing,
                            morphology_complexity=irt_params.morphology_complexity,
                            readability_score=irt_params.readability_score,
                            is_active=True,
                            created_by="system_import",
                        )

                        session.add(question)
                        batch_results["successful"] += 1

                    except Exception as e:
                        error_msg = f"Soru işleme hatası (ID: {question_data.get('soru_id', 'unknown')}): {e!s}"
                        batch_results["errors"].append(error_msg)
                        batch_results["failed"] += 1
                        logger.warning(error_msg)

                # Batch'i commit et
                await session.commit()
                logger.info(f"Batch {batch_number} database'e kaydedildi")

            except Exception as e:
                await session.rollback()
                error_msg = f"Batch {batch_number} commit hatası: {e!s}"
                batch_results["errors"].append(error_msg)
                logger.error(error_msg)

        return batch_results

    async def _perform_irt_calibration(
        self, questions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """IRT kalibrasyon işlemini gerçekleştir"""

        try:
            # Batch kalibrasyon
            calibrated_params = await self.irt_service.batch_calibrate_questions(
                questions
            )

            # Parametreleri doğrula
            questions_with_params = list(zip(questions, calibrated_params))
            validation_results = await self.irt_service.validate_irt_parameters(
                questions_with_params
            )

            logger.info("IRT kalibrasyon tamamlandı")
            return {
                "calibrated_question_count": len(calibrated_params),
                "validation_results": validation_results,
                "average_difficulty": sum(p.difficulty for p in calibrated_params)
                / len(calibrated_params),
                "average_discrimination": sum(
                    p.discrimination for p in calibrated_params
                )
                / len(calibrated_params),
                "average_morphology_complexity": sum(
                    p.morphology_complexity for p in calibrated_params
                )
                / len(calibrated_params),
            }

        except Exception as e:
            logger.error(f"IRT kalibrasyon hatası: {e!s}")
            return {"error": str(e)}

    async def _generate_statistics(self) -> dict[str, Any]:
        """Final istatistikleri oluştur"""

        try:
            stats = await self.soru_bankasi_service.istatistikler_getir()

            # Ek istatistikler
            tyt_count = len(self.question_data.get_questions_by_exam_type("TYT"))
            ayt_count = len(self.question_data.get_questions_by_exam_type("AYT"))
            ydt_count = len(self.question_data.get_questions_by_exam_type("YDT"))

            stats["hedef_soru_sayilari"] = {
                "TYT": {
                    "hedef": 1000,
                    "mevcut": tyt_count,
                    "tamamlanma_orani": tyt_count / 1000,
                },
                "AYT": {
                    "hedef": 800,
                    "mevcut": ayt_count,
                    "tamamlanma_orani": ayt_count / 800,
                },
                "YDT": {
                    "hedef": 500,
                    "mevcut": ydt_count,
                    "tamamlanma_orani": ydt_count / 500,
                },
            }

            return stats

        except Exception as e:
            logger.error(f"İstatistik oluşturma hatası: {e!s}")
            return {"error": str(e)}

    async def populate_specific_exam_type(self, exam_type: str) -> dict[str, Any]:
        """Belirli sınav tipinin sorularını yükle"""

        logger.info(f"{exam_type} soruları yükleniyor...")

        questions = self.question_data.get_questions_by_exam_type(exam_type)
        if not questions:
            return {"error": f"{exam_type} için soru bulunamadı"}

        results = {
            "exam_type": exam_type,
            "total_questions": len(questions),
            "successful_insertions": 0,
            "failed_insertions": 0,
            "errors": [],
        }

        # Batch'ler halinde işle
        batch_size = 50
        for i in range(0, len(questions), batch_size):
            batch = questions[i : i + batch_size]
            batch_results = await self._process_question_batch(
                batch, i // batch_size + 1
            )

            results["successful_insertions"] += batch_results["successful"]
            results["failed_insertions"] += batch_results["failed"]
            results["errors"].extend(batch_results["errors"])

        logger.info(
            f"{exam_type} soruları yükleme tamamlandı - Başarılı: {results['successful_insertions']}"
        )
        return results

    async def verify_question_counts(self) -> dict[str, Any]:
        """Soru sayılarını doğrula"""

        verification = {
            "TYT": {
                "hedef": 1000,
                "matematik": {"hedef": 300, "mevcut": 0},
                "turkce": {"hedef": 300, "mevcut": 0},
                "fen": {"hedef": 200, "mevcut": 0},
                "sosyal": {"hedef": 200, "mevcut": 0},
            },
            "AYT": {
                "hedef": 800,
                "matematik": {"hedef": 300, "mevcut": 0},
                "fizik": {"hedef": 200, "mevcut": 0},
                "kimya": {"hedef": 150, "mevcut": 0},
                "biyoloji": {"hedef": 150, "mevcut": 0},
            },
            "YDT": {"hedef": 500, "ingilizce": {"hedef": 500, "mevcut": 0}},
        }

        # Mevcut sayıları hesapla
        for exam_type in ["TYT", "AYT", "YDT"]:
            questions = self.question_data.get_questions_by_exam_type(exam_type)

            for question in questions:
                subject = question["konu"].lower()

                if exam_type == "TYT":
                    if subject == "matematik":
                        verification["TYT"]["matematik"]["mevcut"] += 1
                    elif subject == "türkçe":
                        verification["TYT"]["turkce"]["mevcut"] += 1
                    elif subject == "fen":
                        verification["TYT"]["fen"]["mevcut"] += 1
                    elif subject == "sosyal":
                        verification["TYT"]["sosyal"]["mevcut"] += 1

                elif exam_type == "AYT":
                    if subject == "matematik":
                        verification["AYT"]["matematik"]["mevcut"] += 1
                    elif subject == "fizik":
                        verification["AYT"]["fizik"]["mevcut"] += 1
                    elif subject == "kimya":
                        verification["AYT"]["kimya"]["mevcut"] += 1
                    elif subject == "biyoloji":
                        verification["AYT"]["biyoloji"]["mevcut"] += 1

                elif exam_type == "YDT":
                    if subject == "i̇ngilizce":
                        verification["YDT"]["ingilizce"]["mevcut"] += 1

        # Tamamlanma oranlarını hesapla
        for exam_type, data in verification.items():
            for subject, counts in data.items():
                if isinstance(counts, dict) and "hedef" in counts:
                    counts["tamamlanma_orani"] = (
                        counts["mevcut"] / counts["hedef"] if counts["hedef"] > 0 else 0
                    )

        return verification


async def main():
    """Ana fonksiyon"""

    print("[ROCKET] Türkiye Üniversite Sınavları Soru Bankası Yükleme Sistemi")
    print("=" * 60)

    populator = QuestionBankPopulator()

    # Komut satırı argümanları
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "verify":
            print("[CHART] Soru sayıları doğrulanıyor...")
            verification = await populator.verify_question_counts()

            for exam_type, data in verification.items():
                print(f"\n{exam_type} Sınavı:")
                for subject, counts in data.items():
                    if isinstance(counts, dict) and "hedef" in counts:
                        print(
                            f"  {subject.title()}: {counts['mevcut']}/{counts['hedef']} (%{counts['tamamlanma_orani'] * 100:.1f})"
                        )

            return

        if command in ["tyt", "ayt", "ydt"]:
            print(f"[BOOKS] {command.upper()} soruları yükleniyor...")
            results = await populator.populate_specific_exam_type(command.upper())
            print(
                f"[CHECK] Tamamlandı: {results['successful_insertions']} soru yüklendi"
            )
            return

    # Tüm soruları yükle
    print("[BOOKS] Tüm sorular yükleniyor...")
    print("⏳ Bu işlem birkaç dakika sürebilir...")

    results = await populator.populate_all_questions()

    print("\n" + "=" * 60)
    print("[CHART] SONUÇLAR:")
    print(f"[CHECK] Başarılı: {results['successful_insertions']} soru")
    print(f"[X] Hatalı: {results['failed_insertions']} soru")
    print(f"⏱️  Süre: {results['processing_time']:.2f} saniye")

    if results.get("calibration_results"):
        cal_results = results["calibration_results"]
        print(
            f"[TARGET] IRT Kalibrasyon: {cal_results.get('calibrated_question_count', 0)} soru"
        )
        print(
            f"[TRENDING_UP] Ortalama Zorluk: {cal_results.get('average_difficulty', 0):.3f}"
        )
        print(
            f"[CHART] Ortalama Ayırıcılık: {cal_results.get('average_discrimination', 0):.3f}"
        )

    if results.get("final_statistics"):
        stats = results["final_statistics"]
        if "hedef_soru_sayilari" in stats:
            print("\n[CLIPBOARD] HEDEF TAMAMLANMA ORANLARI:")
            for exam_type, data in stats["hedef_soru_sayilari"].items():
                print(
                    f"{exam_type}: %{data['tamamlanma_orani'] * 100:.1f} ({data['mevcut']}/{data['hedef']})"
                )

    if results["errors"]:
        print(f"\n⚠️  {len(results['errors'])} hata oluştu (detaylar log dosyasında)")


if __name__ == "__main__":
    asyncio.run(main())
