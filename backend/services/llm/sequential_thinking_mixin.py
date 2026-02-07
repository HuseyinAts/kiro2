"""
Sequential Thinking Mixin
Provides common sequential reasoning capabilities to all LLM providers

Author: KIRO AI Team
Date: 2026-01-16
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import json


class ReasoningStepType(str, Enum):
    """Types of reasoning steps"""

    UNDERSTANDING = "understanding"
    DECOMPOSITION = "decomposition"
    CALCULATION = "calculation"
    INFERENCE = "inference"
    VERIFICATION = "verification"
    CONCLUSION = "conclusion"


@dataclass
class ReasoningStep:
    """Represents a single reasoning step"""

    step_number: int
    step_type: ReasoningStepType
    description: str
    reasoning: str
    result: Optional[str] = None
    confidence: float = 1.0
    sub_steps: List["ReasoningStep"] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "step_number": self.step_number,
            "step_type": self.step_type.value,
            "description": self.description,
            "reasoning": self.reasoning,
            "result": self.result,
            "confidence": self.confidence,
            "sub_steps": [s.to_dict() for s in self.sub_steps],
        }


@dataclass
class ReasoningResult:
    """Complete reasoning result"""

    problem: str
    understanding: str
    steps: List[ReasoningStep]
    final_answer: str
    verification: Optional[str] = None
    confidence: float = 1.0
    provider: str = ""
    model: str = ""
    latency_ms: float = 0.0
    thinking_tokens: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "problem": self.problem,
            "understanding": self.understanding,
            "steps": [s.to_dict() for s in self.steps],
            "final_answer": self.final_answer,
            "verification": self.verification,
            "confidence": self.confidence,
            "provider": self.provider,
            "model": self.model,
            "latency_ms": self.latency_ms,
            "thinking_tokens": self.thinking_tokens,
        }


class SequentialThinkingMixin(ABC):
    """
    Mixin providing sequential thinking capabilities

    Add to any LLM provider class to enable step-by-step reasoning.
    """

    # Default prompts for each provider (override in subclass)
    THINKING_PROMPTS: Dict[str, str] = {
        "step_by_step": """Asagidaki problemi adim adim coz.
Her adimda:
1. Ne yaptigini acikla
2. Neden bu adimi attigini soyle
3. Ara sonucu ver

Problem: {problem}

Cozum:""",
        "decomposition": """Asagidaki karmasik problemi alt problemlere ayir.
Her alt problem icin:
1. Aciklama
2. Bagimliliklari
3. Tahmini zorluk

Problem: {problem}

Alt problemler:""",
        "verification": """Asagidaki cozumu dogrula.
1. Her adimi kontrol et
2. Mantik hatalarini bul
3. Sonucu dogrula

Cozum:
{solution}

Dogrulama:""",
        "math_solution": """Matematik problemini coz.
Tum ara adimlari goster.
Her islem icin aciklama yap.

Problem: {problem}

Cozum:""",
    }

    @abstractmethod
    async def generate(self, request: Any) -> Any:
        """Abstract generate method - must be implemented by provider"""
        pass

    def get_thinking_prompt(self, prompt_type: str, **kwargs) -> str:
        """Get formatted thinking prompt"""
        template = self.THINKING_PROMPTS.get(prompt_type, self.THINKING_PROMPTS["step_by_step"])
        return template.format(**kwargs)

    async def sequential_think(
        self,
        problem: str,
        max_steps: int = 10,
        include_verification: bool = True,
        structured_output: bool = True,
    ) -> ReasoningResult:
        """
        Perform sequential thinking on a problem

        Args:
            problem: Problem to solve
            max_steps: Maximum reasoning steps
            include_verification: Include verification step
            structured_output: Request structured JSON output

        Returns:
            ReasoningResult with all steps
        """
        from services.llm.base_llm_provider import LLMRequest

        # Build prompt
        if structured_output:
            prompt = self._build_structured_prompt(problem, max_steps, include_verification)
        else:
            prompt = self.get_thinking_prompt("step_by_step", problem=problem)

        # Generate response
        request = LLMRequest(
            prompt=prompt,
            system_prompt="Sen bir mantik ve matematik uzmanisin. Adim adim dusun.",
            max_tokens=4096,
            temperature=0.3,
        )

        response = await self.generate(request)

        # Parse response
        if structured_output:
            return self._parse_structured_response(response.content, problem, response)
        else:
            return self._parse_unstructured_response(response.content, problem, response)

    def _build_structured_prompt(
        self, problem: str, max_steps: int, include_verification: bool
    ) -> str:
        """Build prompt for structured JSON output"""
        verification_field = '"verification": "Cozumu nasil dogruladigin",' if include_verification else ""
        return f"""Asagidaki problemi adim adim coz.

Problem: {problem}

ONEMLI: Yanitini asagidaki JSON formatinda ver:

{{
    "understanding": "Problemi nasil anladigin",
    "steps": [
        {{
            "step_number": 1,
            "step_type": "understanding|decomposition|calculation|inference|verification|conclusion",
            "description": "Bu adimda ne yapiyorsun",
            "reasoning": "Neden bu adimi atiyorsun",
            "result": "Bu adimin sonucu",
            "confidence": 0.95
        }}
    ],
    "final_answer": "Son cevap",
    {verification_field}
    "confidence": 0.95
}}

Maksimum {max_steps} adim kullan.
Sadece JSON formatinda yanit ver, baska bir sey ekleme."""

    def _parse_structured_response(
        self, content: str, problem: str, response: Any
    ) -> ReasoningResult:
        """Parse structured JSON response"""
        try:
            # Extract JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            data = json.loads(content.strip())

            # Parse steps
            steps = []
            for step_data in data.get("steps", []):
                step = ReasoningStep(
                    step_number=step_data.get("step_number", len(steps) + 1),
                    step_type=ReasoningStepType(
                        step_data.get("step_type", "inference")
                    ),
                    description=step_data.get("description", ""),
                    reasoning=step_data.get("reasoning", ""),
                    result=step_data.get("result"),
                    confidence=step_data.get("confidence", 1.0),
                )
                steps.append(step)

            return ReasoningResult(
                problem=problem,
                understanding=data.get("understanding", ""),
                steps=steps,
                final_answer=data.get("final_answer", ""),
                verification=data.get("verification"),
                confidence=data.get("confidence", 1.0),
                provider=getattr(response, "provider", "unknown"),
                model=getattr(response, "model_name", "unknown"),
                latency_ms=getattr(response, "latency_ms", 0),
                thinking_tokens=getattr(response, "tokens_used", 0),
            )

        except (json.JSONDecodeError, KeyError, ValueError):
            # Fallback to unstructured parsing
            return self._parse_unstructured_response(content, problem, response)

    def _parse_unstructured_response(
        self, content: str, problem: str, response: Any
    ) -> ReasoningResult:
        """Parse unstructured text response"""
        # Simple parsing - split by numbered steps
        lines = content.strip().split("\n")
        steps = []
        current_step = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for step indicators
            if any(line.startswith(f"{i}.") or line.startswith(f"Adim {i}") for i in range(1, 20)):
                if current_step:
                    steps.append(current_step)
                current_step = ReasoningStep(
                    step_number=len(steps) + 1,
                    step_type=ReasoningStepType.INFERENCE,
                    description=line,
                    reasoning="",
                )
            elif current_step:
                current_step.reasoning += " " + line

        if current_step:
            steps.append(current_step)

        # If no steps found, create single step
        if not steps:
            steps = [
                ReasoningStep(
                    step_number=1,
                    step_type=ReasoningStepType.CONCLUSION,
                    description=content[:500],
                    reasoning="Direct response",
                )
            ]

        return ReasoningResult(
            problem=problem,
            understanding="Parsed from unstructured response",
            steps=steps,
            final_answer=content,
            provider=getattr(response, "provider", "unknown"),
            model=getattr(response, "model_name", "unknown"),
            latency_ms=getattr(response, "latency_ms", 0),
        )

    async def decompose(self, problem: str) -> Dict[str, Any]:
        """
        Decompose complex problem into sub-problems

        Args:
            problem: Complex problem to decompose

        Returns:
            Dictionary with sub-problems and dependencies
        """
        from services.llm.base_llm_provider import LLMRequest

        prompt = f"""Asagidaki karmasik problemi alt problemlere ayir.

Problem: {problem}

JSON formatinda yanit ver:
{{
    "main_problem": "Ana problem ozeti",
    "sub_problems": [
        {{
            "id": 1,
            "title": "Alt problem basligi",
            "description": "Detayli aciklama",
            "dependencies": [],
            "difficulty": 0.5,
            "estimated_steps": 3
        }}
    ],
    "solving_order": [1, 2, 3],
    "total_steps": 10
}}"""

        request = LLMRequest(
            prompt=prompt,
            system_prompt="Sen bir problem analiz uzmanisin.",
            max_tokens=2048,
            temperature=0.3,
        )

        response = await self.generate(request)

        try:
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content.strip())
        except json.JSONDecodeError:
            return {
                "main_problem": problem,
                "sub_problems": [],
                "error": "Parse error",
            }

    async def verify_reasoning(
        self, problem: str, solution: str, steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Verify reasoning steps for logical consistency

        Args:
            problem: Original problem
            solution: Proposed solution
            steps: Reasoning steps to verify

        Returns:
            Verification result with issues found
        """
        from services.llm.base_llm_provider import LLMRequest

        steps_text = "\n".join(
            [f"{i+1}. {s.get('description', s)}" for i, s in enumerate(steps)]
        )

        prompt = f"""Asagidaki cozumu mantiksal tutarlilik acisindan dogrula.

Problem: {problem}

Cozum Adimlari:
{steps_text}

Son Cevap: {solution}

Dogrulama (JSON):
{{
    "is_valid": true/false,
    "issues": [
        {{
            "step": 1,
            "type": "logic_error|missing_step|wrong_calculation|circular_reasoning",
            "description": "Hata aciklamasi",
            "suggestion": "Duzeltme onerisi"
        }}
    ],
    "confidence": 0.95,
    "verified_answer": "Dogrulanan cevap (eger farkli ise)"
}}"""

        request = LLMRequest(
            prompt=prompt,
            system_prompt="Sen bir mantik dogrulama uzmanisin.",
            max_tokens=2048,
            temperature=0.2,
        )

        response = await self.generate(request)

        try:
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content.strip())
        except json.JSONDecodeError:
            return {
                "is_valid": True,
                "issues": [],
                "confidence": 0.5,
                "error": "Parse error",
            }


# Provider-specific prompt templates
PROVIDER_THINKING_PROMPTS = {
    "gemini": {
        "prefix": "Lutfen adim adim dusun ve her adimi acikla:\n",
        "thinking_mode_hint": "(Thinking mode aktif)",
    },
    "openai": {
        "prefix": "Let's think step by step:\n",
        "chain_of_thought": "Show your reasoning for each step.\n",
    },
    "claude": {
        "prefix": "I'll work through this step by step:\n",
        "scratchpad": "<scratchpad>\n",
    },
    "qwen": {
        "prefix": "Adim adim coz:\n",
        "thinking": "Her adimi acikla.\n",
    },
}


def get_provider_thinking_prompt(provider: str) -> Dict[str, str]:
    """Get thinking prompt template for specific provider"""
    return PROVIDER_THINKING_PROMPTS.get(
        provider, PROVIDER_THINKING_PROMPTS["gemini"]
    )
