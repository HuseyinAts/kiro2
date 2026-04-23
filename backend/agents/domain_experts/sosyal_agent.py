"""
Sosyal Expert Agent - YKS Sosyal Bilimler Uzman Agent'i
REQ-4: Sosyal Alan Uzmani
Teknofest 2025 - KIRO2 YKS Platformu

Uzmanlik Alanlari:
- Tarih (REQ-4.1)
- Cografya (REQ-4.2)
- Felsefe (REQ-4.3)
- Din Kulturu (REQ-4.4)
"""

import logging
import time
from typing import Any

from .base_domain_agent import BaseDomainAgent, DomainResponse, DomainType

logger = logging.getLogger(__name__)


class SosyalAgent(BaseDomainAgent):
    """
    Sosyal Bilimler Alan Uzman Agent'i (REQ-4)

    YKS sosyal bilimler sorulari icin uzmanlasmis agent.
    Tarih, cografya, felsefe ve din kulturu konularinda
    detayli aciklama uretir.
    """

    SPECIALIZATION_AREAS = ["tarih", "coğrafya", "felsefe", "din kültürü"]

    def __init__(self, llm_service: Any = None, agent_id: str = "sosyal_agent"):
        super().__init__(
            agent_id=agent_id,
            domain=DomainType.SOSYAL,
            specialization_areas=self.SPECIALIZATION_AREAS,
            llm_service=llm_service,
        )

    def _load_domain_knowledge(self):
        """Sosyal bilimler domain bilgisini yukle"""
        self.context.add_domain_knowledge(
            content="""
            YKS Sosyal Bilimler Temel Kavramlar:

            1. TARIH
            - Osmanli: Kuruluş, Yükseliş, Duraklama, Gerileme, Dağılma dönemleri
            - Cumhuriyet: Kurtuluş Savaşı, İnkılaplar, Çok Partili Dönem
            - Dünya Tarihi: Sanayi Devrimi, Fransız İhtilali, Dünya Savaşları

            2. COGRAFYA
            - Fiziki: İklim, Yer şekilleri, Toprak, Bitki örtüsü
            - Beşeri: Nüfus, Göç, Yerleşme, Ekonomik faaliyetler
            - Türkiye: Bölgeler, Akarsular, Göller, Dağlar

            3. FELSEFE
            - Varlık: Ontoloji, Metafizik
            - Bilgi: Epistemoloji, Bilgi türleri
            - Ahlak: Etik, Değerler
            - Mantık: Akıl yürütme, Çıkarım

            4. DIN KULTURU
            - İslam: İnanç, İbadet, Ahlak
            - Diğer dinler: Hristiyanlık, Yahudilik, Budizm
            - Laiklik: Din-devlet ilişkisi
            """,
            topic="temel_kavramlar",
        )

    def _register_tools(self):
        """Sosyal bilimler araclarini kaydet"""
        self.register_tool("timeline", self._timeline, "Tarih zaman çizelgesi")
        self.register_tool("map_info", self._map_info, "Coğrafi bilgi")

    async def solve_question(
        self,
        question: str,
        shared_context: dict[str, Any] | None = None,
    ) -> DomainResponse:
        """Sosyal bilimler sorusunu coz"""
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
                context_additions={"sosyal_solution": solution[:500]},
            )

            self._update_performance_metrics(response)
            return response

        except Exception as e:
            logger.error(f"Error solving sosyal question: {e}")
            return DomainResponse(
                domain=self.domain,
                content="",
                error=str(e),
                response_time_ms=(time.perf_counter() - start_time) * 1000,
            )

    def _detect_question_type(self, question_lower: str) -> str:
        type_keywords = {
            "tarih": ["osmanlı", "cumhuriyet", "savaş", "antlaşma", "inkılap", "padişah"],
            "cografya": ["iklim", "nüfus", "bölge", "harita", "göç", "tarım"],
            "felsefe": ["felsefe", "düşünür", "akıl", "bilgi", "varlık", "etik"],
            "din": ["din", "ibadet", "inanç", "islam", "peygamber", "ahlak"],
        }
        for q_type, keywords in type_keywords.items():
            if any(kw in question_lower for kw in keywords):
                return q_type
        return "genel"

    def _generate_step_by_step(self, question_type: str) -> list[str]:
        steps = {
            "tarih": ["Dönemi belirle", "Olayı tanımla", "Neden-sonuç ilişkisini kur", "Cevapla"],
            "cografya": ["Konuyu belirle", "Verileri analiz et", "Harita bilgisini kullan", "Sonuçla"],
            "felsefe": ["Kavramı tanımla", "Düşünürleri hatırla", "Görüşleri karşılaştır", "Sonuçlandır"],
            "din": ["Konuyu belirle", "Kaynağı tanımla", "Yorumla", "Cevapla"],
        }
        return steps.get(question_type, ["Konuyu belirle", "Analiz et", "Değerlendir", "Cevapla"])

    async def _solve_with_llm(self, question: str, question_type: str) -> str:
        prompt = f"Sen bir YKS sosyal bilimler uzmanısın. {question_type} konusunda şu soruyu çöz: {question}"
        try:
            response = await self.llm_service.generate(prompt)
            return response.get("content", "")
        except Exception:
            return self._solve_rule_based(question_type)

    def _solve_rule_based(self, question_type: str) -> str:
        solutions = {
            "tarih": "Tarih sorusunda dönem, olay ve neden-sonuç ilişkilerini değerlendirin.",
            "cografya": "Coğrafya sorusunda fiziki ve beşeri faktörleri birlikte değerlendirin.",
            "felsefe": "Felsefe sorusunda kavramları ve düşünürlerin görüşlerini karşılaştırın.",
            "din": "Din kültürü sorusunda inanç, ibadet ve ahlak boyutlarını değerlendirin.",
        }
        return solutions.get(question_type, "Sosyal bilimler sorusunu dikkatle analiz edin.")

    def _calculate_confidence(self, question_type: str) -> float:
        base = {"tarih": 0.80, "cografya": 0.80, "felsefe": 0.75, "din": 0.75}
        return base.get(question_type, 0.70)

    async def _timeline(self, event: str) -> str:
        return f"Zaman çizelgesi: {event}"

    async def _map_info(self, location: str) -> str:
        return f"Coğrafi bilgi: {location}"
