"""
Matematik Hata Tespit Servisi
Requirements: REQ-51.36-51.40 (Hata vurgulama)

Bu servis:
- Öğrenci cevaplarındaki hataları tespit eder
- Hata türünü belirler (işlem, kavram, dikkat)
- Düzeltici öneriler sunar
- Tekrarlayan hataları takip eder
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class ErrorType(str, Enum):
    """Hata türleri"""

    OPERATION = "operation"  # İşlem hatası
    CONCEPT = "concept"  # Kavram hatası
    ATTENTION = "attention"  # Dikkat hatası
    SIGN = "sign"  # İşaret hatası
    SYNTAX = "syntax"  # Sözdizimi hatası


@dataclass
class MathError:
    """Matematik hatası"""

    error_type: ErrorType
    description: str
    incorrect_part: str
    correct_part: str
    suggestion: str
    severity: int  # 1-5 arası (5 en ciddi)

    def to_dict(self) -> Dict:
        return {
            "error_type": self.error_type.value,
            "description": self.description,
            "incorrect_part": self.incorrect_part,
            "correct_part": self.correct_part,
            "suggestion": self.suggestion,
            "severity": self.severity,
        }


class ErrorDetectionService:
    """Hata tespit servisi"""

    def __init__(self):
        # Tekrarlayan hataları takip et
        self.student_error_history: Dict[str, List[MathError]] = defaultdict(list)
        logger.info("ErrorDetectionService initialized")

    def detect_error(
        self,
        student_answer: str,
        correct_answer: str,
        step_context: Optional[str] = None,
    ) -> Optional[MathError]:
        """
        Öğrenci cevabındaki hatayı tespit et

        Args:
            student_answer: Öğrenci cevabı
            correct_answer: Doğru cevap
            step_context: Adım bağlamı (opsiyonel)

        Returns:
            MathError veya None
        """
        if student_answer == correct_answer:
            return None

        # Farklı hata türlerini kontrol et
        error = None

        # 1. İşaret hatası kontrolü
        error = self._check_sign_error(student_answer, correct_answer)
        if error:
            return error

        # 2. İşlem hatası kontrolü
        error = self._check_operation_error(student_answer, correct_answer)
        if error:
            return error

        # 3. Sözdizimi hatası kontrolü
        error = self._check_syntax_error(student_answer, correct_answer)
        if error:
            return error

        # 4. Genel kavram hatası
        return self._create_concept_error(student_answer, correct_answer)

    def _check_sign_error(self, student: str, correct: str) -> Optional[MathError]:
        """İşaret hatası kontrolü"""
        # Sayıları çıkar
        student_nums = re.findall(r"-?\d+\.?\d*", student)
        correct_nums = re.findall(r"-?\d+\.?\d*", correct)

        if len(student_nums) != len(correct_nums):
            return None

        # İşaretleri karşılaştır
        for s_num, c_num in zip(student_nums, correct_nums):
            s_val = float(s_num)
            c_val = float(c_num)

            # Mutlak değerler eşit ama işaretler farklı mı?
            if abs(s_val) == abs(c_val) and s_val != c_val:
                return MathError(
                    error_type=ErrorType.SIGN,
                    description="İşaret Hatası",
                    incorrect_part=student,
                    correct_part=correct,
                    suggestion="Pozitif/negatif işaretini kontrol et. Karşıya atarken işaret değişir.",
                    severity=2,
                )

        return None

    def _check_operation_error(self, student: str, correct: str) -> Optional[MathError]:
        """İşlem hatası kontrolü"""
        # Basit sayısal karşılaştırma
        try:
            # Sadece sayıları al
            student_num = self._extract_number(student)
            correct_num = self._extract_number(correct)

            if student_num is not None and correct_num is not None:
                if student_num != correct_num:
                    # Farkı hesapla
                    diff = abs(student_num - correct_num)

                    # Küçük fark = muhtemelen işlem hatası
                    if diff < abs(correct_num) * 0.5:  # %50'den az fark
                        return MathError(
                            error_type=ErrorType.OPERATION,
                            description="İşlem Hatası",
                            incorrect_part=student,
                            correct_part=correct,
                            suggestion="İşlemi adım adım tekrar yap. Hesap makinesini kullanabilirsin.",
                            severity=3,
                        )
        except:
            pass

        return None

    def _check_syntax_error(self, student: str, correct: str) -> Optional[MathError]:
        """Sözdizimi hatası kontrolü"""
        # Parantez dengesi kontrolü
        if student.count("(") != student.count(")"):
            return MathError(
                error_type=ErrorType.SYNTAX,
                description="Sözdizimi Hatası (Parantez)",
                incorrect_part=student,
                correct_part=correct,
                suggestion="Parantezlerin açılıp kapandığını kontrol et.",
                severity=2,
            )

        # Eşitlik işareti kontrolü
        if "=" in correct and "=" not in student:
            return MathError(
                error_type=ErrorType.SYNTAX,
                description="Sözdizimi Hatası (Eşitlik)",
                incorrect_part=student,
                correct_part=correct,
                suggestion="Eşitlik işaretini unutmuş olabilirsin.",
                severity=1,
            )

        return None

    def _create_concept_error(self, student: str, correct: str) -> MathError:
        """Genel kavram hatası oluştur"""
        return MathError(
            error_type=ErrorType.CONCEPT,
            description="Kavram Hatası",
            incorrect_part=student,
            correct_part=correct,
            suggestion="Bu adımda kullanılan yöntemi ve formülü tekrar gözden geçir.",
            severity=4,
        )

    def _extract_number(self, text: str) -> Optional[float]:
        """Metinden sayı çıkar"""
        try:
            # Sadece sayıları ve işaretleri al
            cleaned = re.sub(r"[^0-9.\-]", "", text)
            if cleaned:
                return float(cleaned)
        except:
            pass
        return None

    def track_student_error(self, student_id: str, error: MathError):
        """Öğrenci hatasını kaydet"""
        self.student_error_history[student_id].append(error)
        logger.info(f"Error tracked for student {student_id}: {error.error_type}")

    def get_recurring_errors(
        self, student_id: str, min_occurrences: int = 3
    ) -> List[Tuple[ErrorType, int]]:
        """
        Tekrarlayan hataları getir

        Args:
            student_id: Öğrenci ID'si
            min_occurrences: Minimum tekrar sayısı

        Returns:
            List[(ErrorType, count)]: Hata türü ve sayısı
        """
        errors = self.student_error_history.get(student_id, [])

        # Hata türlerini say
        error_counts = defaultdict(int)
        for error in errors:
            error_counts[error.error_type] += 1

        # Minimum tekrar sayısını aşanları filtrele
        recurring = [
            (error_type, count)
            for error_type, count in error_counts.items()
            if count >= min_occurrences
        ]

        # Sayıya göre sırala (en çok tekrar eden önce)
        recurring.sort(key=lambda x: x[1], reverse=True)

        return recurring

    def get_error_suggestions(self, student_id: str) -> List[str]:
        """
        Öğrenciye özel öneriler oluştur

        Args:
            student_id: Öğrenci ID'si

        Returns:
            List[str]: Öneri listesi
        """
        recurring = self.get_recurring_errors(student_id)

        if not recurring:
            return ["Harika gidiyorsun! Hata yapmadan devam ediyorsun."]

        suggestions = []

        for error_type, count in recurring:
            if error_type == ErrorType.OPERATION:
                suggestions.append(
                    f"İşlem hatalarını azaltmak için hesap makinesi kullanmayı dene. "
                    f"({count} kez tekrarlandı)"
                )
            elif error_type == ErrorType.SIGN:
                suggestions.append(
                    f"İşaret hatalarına dikkat et. Karşıya atarken işaret değişir. "
                    f"({count} kez tekrarlandı)"
                )
            elif error_type == ErrorType.CONCEPT:
                suggestions.append(
                    f"Kavramsal hataların var. Konuyu tekrar gözden geçirmelisin. "
                    f"({count} kez tekrarlandı)"
                )
            elif error_type == ErrorType.ATTENTION:
                suggestions.append(
                    f"Dikkat hatalarını azaltmak için daha yavaş ve dikkatli çalış. "
                    f"({count} kez tekrarlandı)"
                )

        return suggestions

    def clear_student_history(self, student_id: str):
        """Öğrenci hata geçmişini temizle"""
        if student_id in self.student_error_history:
            del self.student_error_history[student_id]
            logger.info(f"Cleared error history for student: {student_id}")


# Global instance
error_detection_service = ErrorDetectionService()
