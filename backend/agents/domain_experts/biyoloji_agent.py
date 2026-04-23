"""
Biyoloji Expert Agent - YKS Biyoloji Uzman Agent'i
REQ-5: Biyoloji Alan Uzmani
Teknofest 2025 - KIRO2 YKS Platformu

Uzmanlik Alanlari:
- Hucre (REQ-5.1)
- Genetik (REQ-5.2)
- Ekoloji (REQ-5.3)
- Anatomi (REQ-5.4)
"""

import logging
import time
from typing import Any

from .base_domain_agent import BaseDomainAgent, DomainResponse, DomainType

logger = logging.getLogger(__name__)


class BiyolojiAgent(BaseDomainAgent):
    """
    Biyoloji Alan Uzman Agent'i (REQ-5)

    YKS biyoloji sorulari icin uzmanlasmis agent.
    Hucre, genetik, ekoloji ve anatomi konularinda
    detayli aciklama uretir.
    """

    SPECIALIZATION_AREAS = ["hücre", "genetik", "ekoloji", "anatomi"]

    def __init__(self, llm_service: Any = None, agent_id: str = "biyoloji_agent"):
        super().__init__(
            agent_id=agent_id,
            domain=DomainType.BIYOLOJI,
            specialization_areas=self.SPECIALIZATION_AREAS,
            llm_service=llm_service,
        )

    def _load_domain_knowledge(self):
        """Biyoloji domain bilgisini yukle"""
        self.context.add_domain_knowledge(
            content="""
            YKS Biyoloji Temel Kavramlar:

            1. HUCRE
            - Organeller: Çekirdek, Mitokondri, Ribozom, Endoplazmik retikulum
            - Hücre zarı: Seçici geçirgenlik, Aktif/Pasif taşıma
            - Hücre bölünmesi: Mitoz, Mayoz

            2. GENETIK
            - DNA: Yapısı, Replikasyon, Protein sentezi
            - Kalıtım: Mendel kuralları, Çaprazlama
            - Mutasyon: Gen mutasyonları, Kromozom mutasyonları

            3. EKOLOJI
            - Ekosistem: Üreticiler, Tüketiciler, Ayrıştırıcılar
            - Besin zinciri: Enerji akışı, Madde döngüleri
            - Popülasyon: Büyüme, Taşıma kapasitesi

            4. ANATOMI
            - Sistemler: Sindirim, Solunum, Dolaşım, Boşaltım, Sinir
            - Organlar: Kalp, Akciğer, Böbrek, Beyin
            - Dokular: Epitel, Bağ, Kas, Sinir
            """,
            topic="temel_kavramlar",
        )

    def _register_tools(self):
        """Biyoloji araclarini kaydet"""
        self.register_tool("punnett_square", self._punnett_square, "Punnett karesi")
        self.register_tool("cell_diagram", self._cell_diagram, "Hücre diyagramı")

    async def solve_question(
        self,
        question: str,
        shared_context: dict[str, Any] | None = None,
    ) -> DomainResponse:
        """Biyoloji sorusunu coz"""
        start_time = time.perf_counter()

        try:
            if shared_context:
                await self.update_context_from_blackboard(shared_context)

            question_tokens = self._count_tokens(question)
            self.context.add_tokens(question_tokens)

            question_type = self._detect_question_type(question.lower())
            step_by_step = self._generate_step_by_step(question_type)
            tools_used = []

            if self.llm_service:
                solution = await self._solve_with_llm(question, question_type)
            else:
                solution = self._solve_rule_based(question_type)

            # Check if Punnett square needed
            if "çaprazlama" in question.lower() or "kalıtım" in question.lower():
                tools_used.append("Punnett Square")

            confidence = self._calculate_confidence(question_type)
            response_time_ms = (time.perf_counter() - start_time) * 1000

            response = DomainResponse(
                domain=self.domain,
                content=solution,
                confidence=confidence,
                tools_used=tools_used,
                step_by_step_solution=step_by_step,
                response_time_ms=response_time_ms,
                tokens_used=question_tokens + self._count_tokens(solution),
                context_additions={"biyoloji_solution": solution[:500]},
            )

            self._update_performance_metrics(response)
            return response

        except Exception as e:
            logger.error(f"Error solving biyoloji question: {e}")
            return DomainResponse(
                domain=self.domain,
                content="",
                error=str(e),
                response_time_ms=(time.perf_counter() - start_time) * 1000,
            )

    def _detect_question_type(self, question_lower: str) -> str:
        type_keywords = {
            "hucre": ["hücre", "organel", "mitokondri", "çekirdek", "zar", "bölünme"],
            "genetik": ["gen", "dna", "rna", "kalıtım", "çaprazlama", "mutasyon"],
            "ekoloji": ["ekosistem", "besin", "popülasyon", "habitat", "çevre"],
            "anatomi": ["organ", "sistem", "sindirim", "solunum", "dolaşım", "sinir"],
        }
        for q_type, keywords in type_keywords.items():
            if any(kw in question_lower for kw in keywords):
                return q_type
        return "genel"

    def _generate_step_by_step(self, question_type: str) -> list[str]:
        steps = {
            "hucre": ["Organeli/yapıyı belirle", "Fonksiyonunu açıkla", "İlişkileri kur", "Sonuçla"],
            "genetik": ["Genleri belirle", "Alelleri tanımla", "Punnett karesi çiz", "Oranları hesapla"],
            "ekoloji": ["Bileşenleri belirle", "İlişkileri analiz et", "Enerji akışını izle", "Sonuçla"],
            "anatomi": ["Sistemi/organı tanımla", "Yapıyı açıkla", "Fonksiyonu belirt", "Cevapla"],
        }
        return steps.get(question_type, ["Konuyu belirle", "Analiz et", "İlişkilendir", "Cevapla"])

    async def _solve_with_llm(self, question: str, question_type: str) -> str:
        prompt = f"Sen bir YKS biyoloji uzmanısın. {question_type} konusunda şu soruyu çöz: {question}"
        try:
            response = await self.llm_service.generate(prompt)
            return response.get("content", "")
        except Exception:
            return self._solve_rule_based(question_type)

    def _solve_rule_based(self, question_type: str) -> str:
        solutions = {
            "hucre": "Hücre sorusunda organellerin yapı ve fonksiyonlarını değerlendirin.",
            "genetik": "Genetik sorusunda alelleri belirleyin ve çaprazlama yapın.",
            "ekoloji": "Ekoloji sorusunda besin zinciri ve enerji akışını analiz edin.",
            "anatomi": "Anatomi sorusunda organ ve sistemlerin fonksiyonlarını değerlendirin.",
        }
        return solutions.get(question_type, "Biyoloji sorusunu dikkatle analiz edin.")

    def _calculate_confidence(self, question_type: str) -> float:
        base = {"hucre": 0.85, "genetik": 0.80, "ekoloji": 0.80, "anatomi": 0.75}
        return base.get(question_type, 0.75)

    async def _punnett_square(self, parent1: str, parent2: str) -> str:
        return f"Punnett karesi: {parent1} x {parent2}"

    async def _cell_diagram(self, cell_type: str) -> str:
        return f"Hücre diyagramı: {cell_type}"
