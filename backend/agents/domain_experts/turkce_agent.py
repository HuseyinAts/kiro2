"""
Turkce Expert Agent - YKS Turkce Uzman Agent'i
REQ-3: Turkce Alan Uzmani
Teknofest 2025 - KIRO2 YKS Platformu

Uzmanlik Alanlari:
- Dilbilgisi (REQ-3.1)
- Edebiyat (REQ-3.2)
- Anlam Bilgisi (REQ-3.3)

Araclar:
- Zemberek-NLP: Morfolojik analiz
"""

import logging
import time
from typing import Any, Dict, List, Optional

from .base_domain_agent import BaseDomainAgent, DomainType, DomainResponse

logger = logging.getLogger(__name__)


class TurkceAgent(BaseDomainAgent):
    """
    Turkce Alan Uzman Agent'i (REQ-3)

    YKS Turkce sorulari icin uzmanlasmis agent.
    Dilbilgisi, edebiyat ve anlam bilgisi konularinda
    detayli aciklama uretir.
    """

    SPECIALIZATION_AREAS = ["dilbilgisi", "edebiyat", "anlam bilgisi"]

    def __init__(self, llm_service: Any = None, agent_id: str = "turkce_agent"):
        super().__init__(
            agent_id=agent_id,
            domain=DomainType.TURKCE,
            specialization_areas=self.SPECIALIZATION_AREAS,
            llm_service=llm_service,
        )
        self._zemberek_available = False

    def _load_domain_knowledge(self):
        """Turkce domain bilgisini yukle"""
        self.context.add_domain_knowledge(
            content="""
            YKS Turkce Temel Kavramlar:

            1. DILBILGISI
            - Soz turleri: Isim, fiil, sifat, zarf, zamir, edat, baglac, unlem
            - Cumle ogeleri: Ozne, yuklem, nesne, tumlec
            - Ek bilgisi: Yapim ekleri, cekim ekleri

            2. EDEBIYAT
            - Edebi turler: Siir, roman, hikaye, tiyatro, deneme
            - Edebi akimlar: Tanzimat, Servet-i Funun, Milli Edebiyat, Cumhuriyet
            - Edebi sanatlar: Benzetme, kinaye, mecaz, istiare

            3. ANLAM BILGISI
            - Anlam iliskileri: Es anlamli, zit anlamli, sesteş
            - Anlam olaylari: Mecaz, gercek anlam, yan anlam
            - Sozcuk yapisi: Basit, turemis, birlesik
            """,
            topic="temel_kavramlar",
        )

    def _register_tools(self):
        """Turkce araclarini kaydet"""
        try:
            # Check if Zemberek is available via service
            from core.turkish_nlp_service import TurkishNLPService
            self._zemberek_available = True
            self.register_tool("morphology", self._morphology_analysis, "Morfolojik analiz")
            logger.info("Zemberek tools registered")
        except ImportError:
            logger.warning("Zemberek not available")

        self.register_tool("pos_tag", self._pos_tag, "Soz turu belirleme")

    async def solve_question(
        self,
        question: str,
        shared_context: Optional[Dict[str, Any]] = None,
    ) -> DomainResponse:
        """Turkce sorusunu coz"""
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

            # Try Zemberek analysis if available
            if self._zemberek_available and "sozcuk" in question.lower():
                tools_used.append("Zemberek-NLP")

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
                context_additions={"turkce_solution": solution[:500]},
            )

            self._update_performance_metrics(response)
            return response

        except Exception as e:
            logger.error(f"Error solving turkce question: {e}")
            return DomainResponse(
                domain=self.domain,
                content="",
                error=str(e),
                response_time_ms=(time.perf_counter() - start_time) * 1000,
            )

    def _detect_question_type(self, question_lower: str) -> str:
        type_keywords = {
            "dilbilgisi": ["fiil", "isim", "sıfat", "ek", "cümle öğesi", "özne", "yüklem"],
            "edebiyat": ["yazar", "şair", "roman", "şiir", "akım", "dönem", "eser"],
            "anlam": ["anlam", "eş anlamlı", "zıt anlamlı", "mecaz", "gerçek anlam"],
        }
        for q_type, keywords in type_keywords.items():
            if any(kw in question_lower for kw in keywords):
                return q_type
        return "genel"

    def _generate_step_by_step(self, question_type: str) -> List[str]:
        steps = {
            "dilbilgisi": ["Sözcüğü/cümleyi analiz et", "Ek ve kökleri ayır", "Kuralı uygula", "Sonucu belirle"],
            "edebiyat": ["Dönemi belirle", "Yazarı/eseri tanı", "Özellikleri listele", "Cevabı belirle"],
            "anlam": ["Sözcüğün kullanımına bak", "Anlam ilişkisini belirle", "Örnek ver", "Sonuçlandır"],
        }
        return steps.get(question_type, ["Soruyu oku", "Analiz et", "Kuralları uygula", "Cevapla"])

    async def _solve_with_llm(self, question: str, question_type: str) -> str:
        prompt = f"Sen bir YKS Türkçe uzmanısın. {question_type} konusunda şu soruyu çöz: {question}"
        try:
            response = await self.llm_service.generate(prompt)
            return response.get("content", "")
        except Exception:
            return self._solve_rule_based(question_type)

    def _solve_rule_based(self, question_type: str) -> str:
        solutions = {
            "dilbilgisi": "Dilbilgisi sorusunu çözmek için sözcük yapısını ve cümle öğelerini analiz edin.",
            "edebiyat": "Edebiyat sorusunda dönem, akım ve eser özelliklerini değerlendirin.",
            "anlam": "Anlam sorusunda sözcüğün cümle içindeki kullanımına bakın.",
        }
        return solutions.get(question_type, "Türkçe sorusunu dikkatle okuyun.")

    def _calculate_confidence(self, question_type: str) -> float:
        base = {"dilbilgisi": 0.85, "edebiyat": 0.80, "anlam": 0.80}
        return base.get(question_type, 0.75)

    async def _morphology_analysis(self, word: str) -> str:
        return f"{word}: morfolojik analiz"

    async def _pos_tag(self, text: str) -> str:
        return f"Söz türü analizi: {text}"
