"""
Fizik Expert Agent - YKS Fizik Uzman Agent'i
REQ-2: Fizik Alan Uzmani
Teknofest 2025 - KIRO2 YKS Platformu

Uzmanlik Alanlari:
- Mekanik (REQ-2.1)
- Elektrik (REQ-2.2)
- Optik (REQ-2.3)
- Termodinamik (REQ-2.4)
"""

import logging
import time
from typing import Any, Dict, List, Optional

from .base_domain_agent import BaseDomainAgent, DomainType, DomainResponse

logger = logging.getLogger(__name__)


class FizikAgent(BaseDomainAgent):
    """
    Fizik Alan Uzman Agent'i (REQ-2)

    YKS fizik sorulari icin uzmanlasmis agent.
    Mekanik, elektrik, optik ve termodinamik konularinda
    adim adim cozum uretir.
    """

    SPECIALIZATION_AREAS = ["mekanik", "elektrik", "optik", "termodinamik"]

    def __init__(self, llm_service: Any = None, agent_id: str = "fizik_agent"):
        super().__init__(
            agent_id=agent_id,
            domain=DomainType.FIZIK,
            specialization_areas=self.SPECIALIZATION_AREAS,
            llm_service=llm_service,
        )

    def _load_domain_knowledge(self):
        """Fizik domain bilgisini yukle"""
        self.context.add_domain_knowledge(
            content="""
            YKS Fizik Temel Kavramlar:

            1. MEKANIK
            - Newton Yasalari: F = m*a
            - Hareket denklemleri: v = v0 + at, x = v0*t + (1/2)*a*t^2
            - Is-Enerji: W = F*d*cos(θ), E = (1/2)*m*v^2
            - Momentum: p = m*v

            2. ELEKTRIK
            - Coulomb Yasasi: F = k*q1*q2/r^2
            - Ohm Yasasi: V = I*R
            - Guc: P = V*I = I^2*R = V^2/R
            - Kapasite: C = Q/V

            3. OPTIK
            - Isik hizi: c = 3*10^8 m/s
            - Kirilma: n1*sin(θ1) = n2*sin(θ2)
            - Mercek denklemi: 1/f = 1/do + 1/di

            4. TERMODINAMIK
            - Isi: Q = m*c*ΔT
            - Ideal gaz: PV = nRT
            - Entropi: ΔS = Q/T
            """,
            topic="temel_kavramlar",
        )

    def _register_tools(self):
        """Fizik araclarini kaydet"""
        self.register_tool("unit_converter", self._unit_converter, "Birim donusturme")
        self.register_tool("physics_formula", self._physics_formula, "Fizik formulu")

    async def solve_question(
        self,
        question: str,
        shared_context: Optional[Dict[str, Any]] = None,
    ) -> DomainResponse:
        """Fizik sorusunu coz"""
        start_time = time.perf_counter()

        try:
            if shared_context:
                await self.update_context_from_blackboard(shared_context)

            question_tokens = self._count_tokens(question)
            self.context.add_tokens(question_tokens)

            question_type = self._detect_question_type(question.lower())
            step_by_step = self._generate_step_by_step(question_type)

            if self.llm_service:
                solution = await self._solve_with_llm(question, question_type)
            else:
                solution = self._solve_rule_based(question_type)

            confidence = self._calculate_confidence(question_type)
            response_time_ms = (time.perf_counter() - start_time) * 1000

            response = DomainResponse(
                domain=self.domain,
                content=solution,
                confidence=confidence,
                tools_used=[],
                step_by_step_solution=step_by_step,
                response_time_ms=response_time_ms,
                tokens_used=question_tokens + self._count_tokens(solution),
                context_additions={"fizik_solution": solution[:500]},
            )

            self._update_performance_metrics(response)
            return response

        except Exception as e:
            logger.error(f"Error solving fizik question: {e}")
            return DomainResponse(
                domain=self.domain,
                content="",
                error=str(e),
                response_time_ms=(time.perf_counter() - start_time) * 1000,
            )

    def _detect_question_type(self, question_lower: str) -> str:
        type_keywords = {
            "mekanik": ["hareket", "hız", "ivme", "kuvvet", "newton", "momentum"],
            "elektrik": ["akım", "voltaj", "direnç", "ohm", "devre", "elektrik"],
            "optik": ["ışık", "mercek", "ayna", "kırılma", "yansıma"],
            "termodinamik": ["ısı", "sıcaklık", "basınç", "gaz", "entropi"],
        }
        for q_type, keywords in type_keywords.items():
            if any(kw in question_lower for kw in keywords):
                return q_type
        return "genel"

    def _generate_step_by_step(self, question_type: str) -> List[str]:
        steps = {
            "mekanik": ["Verilenleri belirle", "Uygun formülü seç", "Birim kontrolü yap", "Hesapla"],
            "elektrik": ["Devre şemasını çiz", "Seri/paralel belirle", "Ohm yasasını uygula", "Hesapla"],
            "optik": ["Işın diyagramı çiz", "Formülü uygula", "İşaret kurallarına dikkat et", "Sonucu yorumla"],
            "termodinamik": ["Sistem sınırlarını belirle", "Hal değişimini analiz et", "Formülü uygula", "Hesapla"],
        }
        return steps.get(question_type, ["Soruyu analiz et", "Formül seç", "Hesapla", "Kontrol et"])

    async def _solve_with_llm(self, question: str, question_type: str) -> str:
        prompt = f"Sen bir YKS fizik uzmanısın. {question_type} konusunda şu soruyu çöz: {question}"
        try:
            response = await self.llm_service.generate(prompt)
            return response.get("content", "")
        except Exception:
            return self._solve_rule_based(question_type)

    def _solve_rule_based(self, question_type: str) -> str:
        solutions = {
            "mekanik": "Mekanik problemlerinde Newton yasalarını ve hareket denklemlerini kullanın.",
            "elektrik": "Elektrik problemlerinde Ohm yasası ve Kirchhoff kurallarını uygulayın.",
            "optik": "Optik problemlerinde ışın diyagramı çizin ve formülleri uygulayın.",
            "termodinamik": "Termodinamik problemlerinde hal denklemlerini kullanın.",
        }
        return solutions.get(question_type, "Fizik problemini analiz edin.")

    def _calculate_confidence(self, question_type: str) -> float:
        base = {"mekanik": 0.85, "elektrik": 0.80, "optik": 0.75, "termodinamik": 0.75}
        return base.get(question_type, 0.70)

    async def _unit_converter(self, value: float, from_unit: str, to_unit: str) -> str:
        return f"{value} {from_unit} = ? {to_unit}"

    async def _physics_formula(self, formula_name: str) -> str:
        formulas = {
            "newton": "F = m*a",
            "ohm": "V = I*R",
            "kinetik_enerji": "E = (1/2)*m*v^2",
        }
        return formulas.get(formula_name, "Formul bulunamadi")
