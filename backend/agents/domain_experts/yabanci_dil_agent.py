"""
Yabanci Dil Expert Agent - YKS Ingilizce Uzman Agent'i
REQ-6: Yabanci Dil Alan Uzmani
Teknofest 2025 - KIRO2 YKS Platformu

Uzmanlik Alanlari:
- Grammar (REQ-6.1)
- Vocabulary (REQ-6.2)
- Reading (REQ-6.3)
- Writing (REQ-6.4)
"""

import logging
import time
from typing import Any

from .base_domain_agent import BaseDomainAgent, DomainResponse, DomainType

logger = logging.getLogger(__name__)


class YabanciDilAgent(BaseDomainAgent):
    """
    Yabanci Dil (Ingilizce) Alan Uzman Agent'i (REQ-6)

    YKS Ingilizce sorulari icin uzmanlasmis agent.
    Grammar, vocabulary, reading ve writing konularinda
    detayli aciklama uretir.
    """

    SPECIALIZATION_AREAS = ["grammar", "vocabulary", "reading", "writing"]

    def __init__(self, llm_service: Any = None, agent_id: str = "yabanci_dil_agent"):
        super().__init__(
            agent_id=agent_id,
            domain=DomainType.YABANCI_DIL,
            specialization_areas=self.SPECIALIZATION_AREAS,
            llm_service=llm_service,
        )

    def _load_domain_knowledge(self):
        """Yabanci dil domain bilgisini yukle"""
        self.context.add_domain_knowledge(
            content="""
            YKS English Key Concepts:

            1. GRAMMAR
            - Tenses: Simple, Continuous, Perfect, Perfect Continuous
            - Modals: can, could, may, might, must, should, would
            - Conditionals: Type 0, 1, 2, 3, Mixed
            - Passive Voice: be + past participle
            - Reported Speech: Direct to Indirect

            2. VOCABULARY
            - Word Formation: Prefix, Suffix, Root
            - Collocations: make/do, have/take
            - Phrasal Verbs: look up, give up, take off
            - Idioms: Common expressions

            3. READING
            - Main Idea: Topic sentence, Supporting details
            - Inference: Reading between the lines
            - Reference: Pronouns, Demonstratives
            - Vocabulary in Context

            4. WRITING
            - Essay Structure: Introduction, Body, Conclusion
            - Paragraph Unity: Topic sentence, Supporting sentences
            - Coherence: Transitions, Connectors
            """,
            topic="temel_kavramlar",
        )

    def _register_tools(self):
        """Yabanci dil araclarini kaydet"""
        self.register_tool("grammar_check", self._grammar_check, "Gramer kontrolu")
        self.register_tool("word_definition", self._word_definition, "Kelime tanimi")

    async def solve_question(
        self,
        question: str,
        shared_context: dict[str, Any] | None = None,
    ) -> DomainResponse:
        """Yabanci dil sorusunu coz"""
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
                context_additions={"english_solution": solution[:500]},
            )

            self._update_performance_metrics(response)
            return response

        except Exception as e:
            logger.error(f"Error solving yabanci_dil question: {e}")
            return DomainResponse(
                domain=self.domain,
                content="",
                error=str(e),
                response_time_ms=(time.perf_counter() - start_time) * 1000,
            )

    def _detect_question_type(self, question_lower: str) -> str:
        type_keywords = {
            "grammar": ["tense", "verb", "modal", "passive", "conditional", "reported"],
            "vocabulary": ["word", "meaning", "synonym", "antonym", "definition"],
            "reading": ["passage", "paragraph", "text", "author", "main idea"],
            "writing": ["essay", "write", "composition", "paragraph"],
        }
        for q_type, keywords in type_keywords.items():
            if any(kw in question_lower for kw in keywords):
                return q_type
        return "genel"

    def _generate_step_by_step(self, question_type: str) -> list[str]:
        steps = {
            "grammar": ["Identify the grammar point", "Recall the rule", "Apply to the sentence", "Check"],
            "vocabulary": ["Read the context", "Identify word form", "Find the meaning", "Verify"],
            "reading": ["Skim the passage", "Identify key information", "Analyze the question", "Find the answer"],
            "writing": ["Plan your response", "Write the introduction", "Develop body paragraphs", "Conclude"],
        }
        return steps.get(question_type, ["Read carefully", "Analyze", "Apply rules", "Answer"])

    async def _solve_with_llm(self, question: str, question_type: str) -> str:
        prompt = f"You are a YKS English expert. Solve this {question_type} question: {question}"
        try:
            response = await self.llm_service.generate(prompt)
            return response.get("content", "")
        except Exception:
            return self._solve_rule_based(question_type)

    def _solve_rule_based(self, question_type: str) -> str:
        solutions = {
            "grammar": "For grammar questions, identify the tense/structure and apply the appropriate rule.",
            "vocabulary": "For vocabulary questions, consider the context and word formation.",
            "reading": "For reading questions, skim for main ideas and scan for specific details.",
            "writing": "For writing questions, plan your structure and use appropriate connectors.",
        }
        return solutions.get(question_type, "Analyze the English question carefully.")

    def _calculate_confidence(self, question_type: str) -> float:
        base = {"grammar": 0.85, "vocabulary": 0.80, "reading": 0.80, "writing": 0.75}
        return base.get(question_type, 0.75)

    async def _grammar_check(self, sentence: str) -> str:
        return f"Grammar check: {sentence}"

    async def _word_definition(self, word: str) -> str:
        return f"Definition of '{word}'"
