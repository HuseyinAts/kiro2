"""
IRT Calculator
3 Parametreli Lojistik Model ile Item Response Theory hesaplamaları

IRT Parametreleri (CLAUDE.md):
- difficulty: [-4.0, 4.0]
- discrimination: [0.2, 4.0]
- guessing: [0.0, 0.35]
- ZPD optimal: %15-85 başarı olasılığı
"""

import math


class IRTCalculator:
    """
    IRT (Item Response Theory) hesaplayıcı

    3 Parametreli Lojistik Model (3PL):
    P(θ) = c + (1-c) / (1 + exp(-Da(θ-b)))

    Parametreler:
    - a: discrimination (ayırt edicilik) [0.2, 4.0]
    - b: difficulty (zorluk) [-4.0, 4.0]
    - c: guessing (şans) [0.0, 0.35]
    - θ: theta (öğrenci yetenek seviyesi)
    - D: scaling constant (1.7 veya 1.0)
    """

    # Parameter ranges
    DIFFICULTY_MIN = -4.0
    DIFFICULTY_MAX = 4.0
    DISCRIMINATION_MIN = 0.2
    DISCRIMINATION_MAX = 4.0
    GUESSING_MIN = 0.0
    GUESSING_MAX = 0.35

    # ZPD bounds (Zone of Proximal Development)
    ZPD_MIN = 0.15
    ZPD_MAX = 0.85
    ZPD_OPTIMAL_MIN = 0.40
    ZPD_OPTIMAL_MAX = 0.60

    # Scaling constant (typically 1.7 for normal ogive approximation)
    D = 1.7

    def __init__(self, scaling_constant: float = 1.7):
        """
        IRT Calculator başlat

        Args:
            scaling_constant: D sabitesi (varsayılan 1.7)
        """
        self.D = scaling_constant

    def calculate_probability(
        self,
        theta: float,
        difficulty: float,
        discrimination: float,
        guessing: float
    ) -> float:
        """
        3PL modeli ile başarı olasılığı hesapla

        P(θ) = c + (1-c) / (1 + exp(-Da(θ-b)))

        Args:
            theta: Öğrenci yetenek seviyesi
            difficulty: Zorluk parametresi (b)
            discrimination: Ayırt edicilik parametresi (a)
            guessing: Şans parametresi (c)

        Returns:
            float: Başarı olasılığı (0-1)
        """
        # Parameter validation
        difficulty = max(self.DIFFICULTY_MIN, min(self.DIFFICULTY_MAX, difficulty))
        discrimination = max(self.DISCRIMINATION_MIN, min(self.DISCRIMINATION_MAX, discrimination))
        guessing = max(self.GUESSING_MIN, min(self.GUESSING_MAX, guessing))

        # 3PL calculation
        exponent = -self.D * discrimination * (theta - difficulty)

        # Overflow protection
        if exponent > 700:
            prob = guessing
        elif exponent < -700:
            prob = 1.0
        else:
            prob = guessing + (1 - guessing) / (1 + math.exp(exponent))

        # Ensure rounding doesn't violate the 3PL invariant P(θ) >= c
        return max(round(prob, 6), guessing)

    def calculate_information(
        self,
        theta: float,
        difficulty: float,
        discrimination: float,
        guessing: float
    ) -> float:
        """
        Item Information Function (IIF) hesapla

        I(θ) = D²a²(P-c)²(1-P) / ((1-c)²P)

        Args:
            theta: Öğrenci yetenek seviyesi
            difficulty: Zorluk parametresi
            discrimination: Ayırt edicilik parametresi
            guessing: Şans parametresi

        Returns:
            float: Information değeri
        """
        P = self.calculate_probability(theta, difficulty, discrimination, guessing)

        if guessing >= P or P >= 1.0:
            return 0.0

        numerator = (self.D ** 2) * (discrimination ** 2) * ((P - guessing) ** 2) * (1 - P)
        denominator = ((1 - guessing) ** 2) * P

        if denominator == 0:
            return 0.0

        return round(numerator / denominator, 6)

    def check_zpd(
        self,
        difficulty: float,
        discrimination: float,
        guessing: float,
        theta: float = 0.0
    ) -> tuple[bool, float, str]:
        """
        ZPD (Zone of Proximal Development) kontrolü

        Optimal ZPD: %40-60 başarı olasılığı
        Kabul edilebilir ZPD: %15-85 başarı olasılığı

        Args:
            difficulty: Zorluk parametresi
            discrimination: Ayırt edicilik parametresi
            guessing: Şans parametresi
            theta: Hedef öğrenci yetenek seviyesi

        Returns:
            Tuple[bool, float, str]: (ZPD içinde mi, skor, açıklama)
        """
        prob = self.calculate_probability(theta, difficulty, discrimination, guessing)

        if self.ZPD_OPTIMAL_MIN <= prob <= self.ZPD_OPTIMAL_MAX:
            return True, 1.0, f"Optimal ZPD ({prob:.1%} başarı olasılığı)"
        if self.ZPD_MIN <= prob <= self.ZPD_MAX:
            return True, 0.8, f"Kabul edilebilir ZPD ({prob:.1%} başarı olasılığı)"
        return False, 0.5, f"ZPD dışında ({prob:.1%} başarı olasılığı)"

    def estimate_difficulty_from_text(
        self,
        question_text: str,
        target_difficulty: str = "orta"
    ) -> dict[str, float]:
        """
        Soru metninden zorluk parametrelerini tahmin et

        Bu basitleştirilmiş bir tahmindir. Gerçek IRT parametreleri
        öğrenci yanıt verilerinden hesaplanmalıdır.

        Args:
            question_text: Soru metni
            target_difficulty: Hedef zorluk ("kolay", "orta", "zor")

        Returns:
            Dict[str, float]: IRT parametreleri
        """
        # Difficulty mapping
        difficulty_map = {
            "kolay": -1.5,
            "orta": 0.0,
            "zor": 1.5
        }

        base_difficulty = difficulty_map.get(target_difficulty, 0.0)

        # Metin uzunluğuna göre ayarlama
        word_count = len(question_text.split())
        if word_count > 100:
            base_difficulty += 0.3
        elif word_count < 30:
            base_difficulty -= 0.2

        # Matematiksel sembollerin varlığı zorluğu artırır
        math_symbols = ["∑", "∫", "√", "∞", "≤", "≥", "∈", "∀", "∃"]
        math_count = sum(1 for sym in math_symbols if sym in question_text)
        base_difficulty += math_count * 0.1

        # Sınırları kontrol et
        base_difficulty = max(self.DIFFICULTY_MIN, min(self.DIFFICULTY_MAX, base_difficulty))

        return {
            "difficulty": round(base_difficulty, 2),
            "discrimination": 1.0,  # Varsayılan
            "guessing": 0.25  # 4 seçenekli soru için
        }

    def validate_parameters(
        self,
        difficulty: float,
        discrimination: float,
        guessing: float
    ) -> tuple[bool, list[str]]:
        """
        IRT parametrelerini doğrula

        Args:
            difficulty: Zorluk parametresi
            discrimination: Ayırt edicilik parametresi
            guessing: Şans parametresi

        Returns:
            Tuple[bool, List[str]]: (Geçerli mi, Hatalar)
        """
        errors = []

        if not self.DIFFICULTY_MIN <= difficulty <= self.DIFFICULTY_MAX:
            errors.append(
                f"Difficulty {difficulty} aralık dışında "
                f"[{self.DIFFICULTY_MIN}, {self.DIFFICULTY_MAX}]"
            )

        if not self.DISCRIMINATION_MIN <= discrimination <= self.DISCRIMINATION_MAX:
            errors.append(
                f"Discrimination {discrimination} aralık dışında "
                f"[{self.DISCRIMINATION_MIN}, {self.DISCRIMINATION_MAX}]"
            )

        if not self.GUESSING_MIN <= guessing <= self.GUESSING_MAX:
            errors.append(
                f"Guessing {guessing} aralık dışında "
                f"[{self.GUESSING_MIN}, {self.GUESSING_MAX}]"
            )

        return len(errors) == 0, errors

    def calculate_expected_score(
        self,
        theta: float,
        items: list[dict[str, float]]
    ) -> float:
        """
        Beklenen test skoru hesapla

        Args:
            theta: Öğrenci yetenek seviyesi
            items: Soru parametreleri listesi

        Returns:
            float: Beklenen skor
        """
        total = 0.0
        for item in items:
            prob = self.calculate_probability(
                theta,
                item.get("difficulty", 0.0),
                item.get("discrimination", 1.0),
                item.get("guessing", 0.25)
            )
            total += prob

        return round(total, 2)

    def find_optimal_difficulty(
        self,
        theta: float,
        target_probability: float = 0.5
    ) -> float:
        """
        Hedef başarı olasılığı için optimal zorluğu bul

        Args:
            theta: Öğrenci yetenek seviyesi
            target_probability: Hedef başarı olasılığı

        Returns:
            float: Optimal zorluk değeri
        """
        # Binary search for difficulty
        low, high = self.DIFFICULTY_MIN, self.DIFFICULTY_MAX
        discrimination = 1.0
        guessing = 0.25

        for _ in range(50):  # Max iterations
            mid = (low + high) / 2
            prob = self.calculate_probability(theta, mid, discrimination, guessing)

            if abs(prob - target_probability) < 0.01:
                return round(mid, 2)

            if prob > target_probability:
                low = mid
            else:
                high = mid

        return round((low + high) / 2, 2)
