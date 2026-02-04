"""
Math Genius Agent Plugin
Advanced mathematics tutoring with step-by-step solutions
"""

import logging
import re
from typing import Any, Dict, List, Optional

from core.plugin_architecture import BaseAgentPlugin

logger = logging.getLogger(__name__)


class MathGeniusAgent(BaseAgentPlugin):
    """Math Genius agent for advanced mathematics tutoring"""

    async def initialize(self, context_manager, content_generator, analytics):
        """Initialize the agent"""
        await super().initialize(context_manager, content_generator, analytics)

        # Math-specific initialization
        self.problem_patterns = {
            "equation": r"([0-9x\+\-\*\/\=\s]+)",
            "word_problem": r"(.*?)\?",
            "geometry": r"(üçgen|kare|daire|dikdörtgen|alan|çevre)",
        }

        logger.info("Math Genius Agent initialized")

    async def process_message(
        self, message: str, session_id: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Process mathematics questions"""

        # Detect problem type
        problem_type = self._detect_problem_type(message)

        # Generate solution based on type
        if problem_type == "equation":
            return await self._solve_equation(message)
        elif problem_type == "word_problem":
            return await self._solve_word_problem(message)
        elif problem_type == "geometry":
            return await self._solve_geometry(message)
        else:
            return await self._provide_math_help(message)

    def _detect_problem_type(self, message: str) -> str:
        """Detect the type of math problem"""
        message_lower = message.lower()

        # Check for equation patterns
        if re.search(r"\d+\s*[+\-*/]\s*\d+", message):
            return "equation"

        # Check for geometry keywords
        geometry_keywords = ["üçgen", "kare", "daire", "alan", "çevre", "açı"]
        if any(keyword in message_lower for keyword in geometry_keywords):
            return "geometry"

        # Check for word problem indicators
        if "?" in message and any(
            word in message_lower for word in ["kaç", "ne kadar", "toplam"]
        ):
            return "word_problem"

        return "general"

    async def _solve_equation(self, message: str) -> str:
        """Solve mathematical equations with steps"""

        # Extract equation
        equation_match = re.search(r"([0-9x\+\-\*\/\=\s]+)", message)
        if not equation_match:
            return "Denklemi anlayamadım. Lütfen tekrar yazın."

        equation = equation_match.group(1).strip()

        # Simple equation solver (in production, use sympy)
        try:
            # Basic arithmetic
            if "x" not in equation and "=" not in equation:
                result = eval(equation.replace("^", "**"))
                return f"""
                📐 **Problem:** {equation}
                
                [CHECK] **Çözüm:** {result}
                
                **Adımlar:**
                1. İşlem sırasına göre çözüm yapıldı
                2. Sonuç: {result}
                
                [BULB] **İpucu:** İşlem önceliği kurallarını unutmayın!
                """
            else:
                # For equations with variables
                return f"""
                📐 **Denklem:** {equation}
                
                **Çözüm Adımları:**
                1. Denklemi sadeleştir
                2. Bilinmeyeni yalnız bırak
                3. Her iki tarafa aynı işlemi uygula
                4. Sonucu kontrol et
                
                [BULB] **Pratik:** Benzer problemler çözerek pratik yapın!
                """

        except Exception as e:
            logger.error(f"Equation solving error: {e}")
            return "Bu denklemi çözerken bir hata oluştu. Daha basit bir şekilde yazabilir misiniz?"

    async def _solve_word_problem(self, message: str) -> str:
        """Solve word problems with explanation"""

        # Analyze word problem
        numbers = re.findall(r"\d+", message)

        if not numbers:
            return "Problemde sayısal değer bulamadım. Lütfen problemi tekrar yazın."

        return f"""
        [BOOKS] **Problem Analizi:**
        {message}
        
        **Çözüm Yaklaşımı:**
        1. **Verilenler:** {', '.join(numbers)} değerleri verilmiş
        2. **İstenen:** Problemde sorulan değer
        3. **Strateji:** Uygun işlem seçimi
        
        **Adım Adım Çözüm:**
        • Önce verilenleri organize edin
        • Hangi işlemi kullanacağınıza karar verin
        • İşlemi yapın ve kontrol edin
        
        [BULB] **Öğrenme Notu:** Problem çözerken her zaman:
        - Verilenleri belirleyin
        - Ne sorulduğunu anlayın
        - Uygun stratejiyi seçin
        """

    async def _solve_geometry(self, message: str) -> str:
        """Solve geometry problems"""

        message_lower = message.lower()

        if "alan" in message_lower:
            return self._area_formula_help()
        elif "çevre" in message_lower:
            return self._perimeter_formula_help()
        else:
            return self._general_geometry_help()

    def _area_formula_help(self) -> str:
        """Provide area formulas"""
        return """
        📐 **Alan Formülleri:**
        
        **Kare:** Alan = kenar × kenar = a²
        **Dikdörtgen:** Alan = uzun kenar × kısa kenar = a × b
        **Üçgen:** Alan = (taban × yükseklik) / 2
        **Daire:** Alan = π × r²
        
        **Örnek Problemler:**
        • Kenarı 5 cm olan karenin alanı = 5² = 25 cm²
        • 4x6 dikdörtgenin alanı = 4 × 6 = 24 cm²
        
        [TARGET] **Pratik:** Her şekil için birer örnek çözün!
        """

    def _perimeter_formula_help(self) -> str:
        """Provide perimeter formulas"""
        return """
        📏 **Çevre Formülleri:**
        
        **Kare:** Çevre = 4 × kenar = 4a
        **Dikdörtgen:** Çevre = 2 × (uzun + kısa) = 2(a + b)
        **Üçgen:** Çevre = a + b + c
        **Daire:** Çevre = 2 × π × r
        
        **Örnek Problemler:**
        • Kenarı 3 cm olan karenin çevresi = 4 × 3 = 12 cm
        • 5x8 dikdörtgenin çevresi = 2 × (5 + 8) = 26 cm
        
        [TARGET] **İpucu:** Çevre = tüm kenarların toplamı!
        """

    def _general_geometry_help(self) -> str:
        """Provide general geometry help"""
        return """
        📐 **Geometri Yardımı:**
        
        **Temel Şekiller:**
        • Kare: 4 eşit kenar, 4 dik açı
        • Dikdörtgen: Karşılıklı kenarlar eşit
        • Üçgen: 3 kenar, iç açılar toplamı 180°
        • Daire: Merkeze eşit uzaklıktaki noktalar
        
        **Önemli Kavramlar:**
        • Alan: Yüzeyin kapladığı yer
        • Çevre: Kenarların toplamı
        • Açı: İki doğrunun kesişimi
        
        Ne hakkında yardım istersiniz?
        """

    async def _provide_math_help(self, message: str) -> str:
        """Provide general math help"""

        topics = {
            "toplama": "Toplama işlemi: sayıları bir araya getirme",
            "çıkarma": "Çıkarma işlemi: bir sayıdan diğerini eksiltme",
            "çarpma": "Çarpma işlemi: tekrarlı toplama",
            "bölme": "Bölme işlemi: eşit parçalara ayırma",
            "kesir": "Kesirler: bir bütünün parçaları",
            "ondalık": "Ondalık sayılar: virgüllü sayılar",
            "yüzde": "Yüzde: 100'e göre oran",
        }

        message_lower = message.lower()

        for topic, description in topics.items():
            if topic in message_lower:
                return f"""
                [BOOKS] **{topic.title()} Konusu:**
                
                {description}
                
                **Temel Bilgiler:**
                • Tanım ve özellikler
                • Kullanım alanları
                • Örnek problemler
                
                Detaylı açıklama ister misiniz?
                """

        return """
        🧮 **Matematik Yardımcınız:**
        
        Şu konularda yardımcı olabilirim:
        • Temel işlemler (toplama, çıkarma, çarpma, bölme)
        • Denklem çözme
        • Geometri (alan, çevre, açılar)
        • Problem çözme
        • Kesirler ve ondalık sayılar
        
        Hangi konuda yardım istersiniz?
        """

    async def get_capabilities(self) -> List[str]:
        """Return agent capabilities"""
        return [cap.value for cap in self.manifest.capabilities]

    async def shutdown(self):
        """Clean up resources"""
        logger.info("Math Genius Agent shutting down")
