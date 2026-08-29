import re
from typing import ClassVar


class OsymValidator:
    """
    Validates question stems (soru kökü) against standard ÖSYM (YKS) language.
    Phase 7 of KIRO2 Master Plan.
    """

    # Valid, approved question stems (or their regex patterns)
    APPROVED_STEMS: ClassVar[list[str]] = [
        r"hangisi söylenemez\?$",
        r"hangisine ulaşılamaz\?$",
        r"asıl anlatılmak istenen nedir\?$",
        r"hangisi çıkarılamaz\?$",
        r"hangisine değinilmemiştir\?$",
        r"hangisi kesin olarak çıkarılabilir\?$",
        r"hangisi yakınılan durumlardan biri değildir\?$",
        r"altı çizili sözle anlatılmak istenen aşağıdakilerden hangisidir\?$",
    ]

    # Non-standard/banned patterns and their recommended alternatives
    BANNED_STEMS: ClassVar[dict[str, str]] = {
        r"hangisi yanlıştır\?": "ÖSYM dilinde 'Hangisi söylenemez?' kalıbı tercih edilir.",
        r"hangisi doğru değildir\?": "ÖSYM dilinde 'Hangisine ulaşılamaz?' veya 'Hangisi söylenemez?' tercih edilir.",
        r"ana fikri nedir\?": "ÖSYM dilinde 'Asıl anlatılmak istenen nedir?' kalıbı kullanılır.",
        r"ne demek istemiştir\?": "ÖSYM dilinde 'Anlatılmak istenen aşağıdakilerden hangisidir?' kullanılır.",
    }

    @classmethod
    def validate_question_stem(cls, stem: str) -> tuple[bool, list[str]]:
        """
        Validates if a given question stem adheres to ÖSYM standard language.
        Returns: (is_valid, list_of_warnings_or_errors)
        """
        normalized_stem = stem.lower().strip()

        errors = []
        is_valid = True

        for banned_pattern, recommendation in cls.BANNED_STEMS.items():
            if re.search(banned_pattern, normalized_stem):
                is_valid = False
                errors.append(
                    f"Standart dışı soru kökü tespit edildi: '{banned_pattern}'. Öneri: {recommendation}"
                )

        if "değildir" in normalized_stem and not any(
            re.search(bp, normalized_stem) for bp in cls.BANNED_STEMS
        ):
            is_valid = False
            errors.append(
                "ÖSYM soru köklerinde genellikle 'değildir' yerine '-mez/-maz' (ulaşılamaz, söylenemez) geniş zaman olumsuzu tercih edilir."
            )

        return is_valid, errors

    @classmethod
    def analyze_vocabulary(cls, text: str, subject: str) -> tuple[bool, list[str]]:
        """
        Phase 13 preview: Detects inter-disciplinary jargon mixing.
        """
        warnings = []
        normalized = text.lower()

        if subject.lower() == "fizik":
            if "çözelti" in normalized:
                warnings.append(
                    "Fizik sorusunda Kimya jargonu ('çözelti') tespit edildi. 'Karışım' kelimesini kullanmayı düşünün."
                )

        elif subject.lower() == "edebiyat" and "kök hücre" in normalized:
            warnings.append(
                "Edebiyat sorusunda Biyoloji jargonu ('kök hücre') tespit edildi."
            )

        return len(warnings) == 0, warnings
