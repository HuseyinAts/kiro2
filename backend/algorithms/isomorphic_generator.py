import random
import re
from typing import Any, ClassVar


class IsomorphicGenerator:
    """
    Phase 9: FSRS Temelli İzomorfik Soru Üretici.
    Generates an isomorphic (structurally identical but superficially different)
    version of a given question. Replaces names and numbers to prevent rote memorization.
    Note: Currently uses a regex/template approach as a placeholder for an LLM integration.
    """

    NAMES: ClassVar[list[str]] = [
        "Ali",
        "Ayşe",
        "Mehmet",
        "Zeynep",
        "Can",
        "Elif",
        "Burak",
        "Ceren",
        "Deniz",
        "Efe",
    ]
    # Metinde aranan isimler (degistirilecek olanlar); NAMES yeni isim havuzu.
    BILINEN_ISIMLER: ClassVar[tuple[str, ...]] = (
        "Ahmet",
        "Mehmet",
        "Ali",
        "Veli",
        "Ayşe",
        "Fatma",
    )
    OBJECTS: ClassVar[list[str]] = [
        "elma",
        "armut",
        "bilye",
        "kalem",
        "kitap",
        "defter",
        "silgi",
        "ceviz",
    ]

    @classmethod
    def generate_isomorphic_question(cls, question: dict[str, Any]) -> dict[str, Any]:
        """
        Takes a question dict/object and returns a modified copy.
        Modifies content text, updates numerical options if necessary.
        """
        original_text = question.get("content", "")
        if not original_text:
            return question

        # Create a deep-ish copy for mutation
        iso_question = question.copy()
        iso_options = []
        if "options" in question:
            # Assume options is a list of dicts: [{"letter": "A", "text": "10"}, ...]
            iso_options = [opt.copy() for opt in question.get("options", [])]
            iso_question["options"] = iso_options

        # Fallback: if it's a verbal question without numbers, we might just replace names
        text = original_text

        # 1. Replace Names (Simple Heuristic: Capitalized words that might be names)
        # For a robust implementation, NLP NER (Named Entity Recognition) is needed.
        # Here we just replace a few known names if they exist.
        # TEK GECIS (9 Eyl 2026): eski dongu her ismi sirayla degistiriyordu ve
        # yerine konan isim listede daha sonra geliyorsa o da degistiriliyordu --
        # "Mehmet" -> "Ali" -> "Mehmet" geri donebiliyordu (CI'da ~%1 rastgele
        # kirmizi, test_number_replacement). Simdi metindeki isimler once
        # toplanir, yeni isim havuzu ORIJINAL isimlerin hicbirini icermez ve
        # degisim tek regex gecisiyle yapilir; eklenen isim bir daha okunmaz.
        bulunan = [n for n in cls.BILINEN_ISIMLER if n in text]
        if bulunan:
            havuz = [n for n in cls.NAMES if n not in bulunan] or list(cls.NAMES)
            # random: kripto degil, sadece soru varyasyonu (S311/B311 muaf)
            eslesme = {n: random.choice(havuz) for n in bulunan}  # noqa: S311 # nosec B311
            text = re.sub(
                "|".join(re.escape(n) for n in bulunan),
                lambda m: eslesme[m.group()],
                text,
            )

        # 2. Replace Numbers (Very simplistic numeric isomorphic generation)
        # Find integers and apply a random offset
        def num_replacer(match):
            val = int(match.group())
            # Offset the number slightly, keeping it positive
            offset = random.randint(1, 3)  # noqa: S311 # nosec B311 -- kripto degil, soru varyasyonu
            new_val = (
                val + offset
                if random.choice([True, False])  # noqa: S311 # nosec B311
                else max(1, val - offset)
            )
            if new_val == val:  # val=1 ve eksi dali: max(1, ...) sayiyi degistirmezdi
                new_val = val + offset
            return str(new_val)

        # We only do this if it looks like a math/logic problem to avoid breaking years (e.g. 1923)
        # Heuristic: check if the text contains math keywords
        if any(
            keyword in text.lower()
            for keyword in ["tane", "aldı", "verdi", "toplam", "fark", "oran"]
        ):
            text = re.sub(r"\b[1-9]\d{0,2}\b", num_replacer, text)

            # Since we changed numbers in the question, the options are now likely wrong.
            # In a real system, the Math engine / LLM would recalculate the correct answer.
            # Here we just lightly offset the numeric options as a mock simulation.
            for opt in iso_options:
                opt_text = opt.get("text", "")
                if str(opt_text).isdigit():
                    opt_val = int(opt_text)
                    roll = random.randint(1, 3)  # noqa: S311 # nosec B311
                    opt["text"] = str(opt_val + roll)

        iso_question["content"] = text
        iso_question["is_isomorphic"] = (
            True  # Flag to indicate this is not the original
        )

        return iso_question
