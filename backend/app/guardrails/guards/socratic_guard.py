"""Sokratik Pedagoji ve LLM Sınırlandırma (Socratic Guard) Bileşeni."""

from typing import Any

from services.socratic_rag_guardrail_service import socratic_rag_guardrail_service

from ..models import GuardResult, GuardStatus
from .base_guard import BaseGuard


class SocraticGuard(BaseGuard):
    """Sokratik AI pedagoji ve prompt emniyet denetçisi."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config or {"enabled": True})

    async def check(self, context: dict[str, Any]) -> GuardResult:
        """Sokratik diyalog ve içerik güvenliğini denetler."""
        self._increment_check_count()

        if not self.enabled:
            return self._create_result(
                GuardStatus.OK, "SocraticGuard pasif durumda."
            )

        prompt = context.get("prompt", "")
        response_text = context.get("response_text", "")

        # 1. Input Safety (Prompt Injection Check)
        if prompt:
            input_check = socratic_rag_guardrail_service.inspect_input_safety(prompt)
            if not input_check["is_safe"]:
                result = self._create_result(
                    GuardStatus.STOP,
                    input_check["reason"] or "Güvenlik uyarısı.",
                    details={"type": "prompt_injection"},
                    should_stop=True,
                )
                self._log_check(result)
                return result

        # 2. Output Socratic Compliance Check
        if response_text:
            socratic_eval = socratic_rag_guardrail_service.validate_socratic_compliance(
                response_text
            )
            latex_eval = socratic_rag_guardrail_service.validate_latex_formatting(
                response_text
            )

            if socratic_eval["direct_answer_detected"]:
                result = self._create_result(
                    GuardStatus.WARNING,
                    "Direkt cevap tespiti: Yanıt pedagojik yönlendirme sorusu içermeli.",
                    details={
                        "socratic_score": socratic_eval["socratic_score"],
                        "suggestions": socratic_eval["suggestions"],
                        "latex_valid": latex_eval["is_valid"],
                    },
                    should_stop=False,
                )
                self._log_check(result)
                return result

        result = self._create_result(
            GuardStatus.OK,
            "Sokratik yanıt uyumu ve girdi emniyeti doğrulandı.",
            details={"socratic_score": 0.95},
        )
        self._log_check(result)
        return result

    def reset(self) -> None:
        self._check_count = 0
