"""
Response Validation Stop Hook

Bu modül, AI yanıt tamamlandığında tetiklenen Stop Hook'u içerir.

Features:
- AI yanıt tamamlanınca otomatik tetikleme
- Validation orchestrator çağrısı
- Action execution (approve/review/reject)
- Admin notification
- Fail-open: validation hatası yanıtı engellemez

Requirements: REQ-6.1 - REQ-6.6
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

from backend.orchestrator.response_validation_orchestrator import (
    ResponseValidationOrchestrator,
)
from backend.validators.base_response_validator import (
    AgentResponse,
    ValidationAction,
)

logger = logging.getLogger(__name__)


class ResponseValidationHook:
    """
    AI yanıt doğrulama Stop Hook'u.

    AI agent yanıt vermeyi bitirdiğinde otomatik olarak
    doğrulama pipeline'ını çalıştırır.

    Fail-open prensibine göre çalışır: validation hatası
    yanıtın kullanıcıya iletilmesini engellemez.
    """

    def __init__(
        self,
        orchestrator: Optional[ResponseValidationOrchestrator] = None,
        on_approve: Optional[Callable] = None,
        on_review: Optional[Callable] = None,
        on_reject: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        admin_notification_callback: Optional[Callable] = None,
        enabled: bool = True,
    ):
        """
        Args:
            orchestrator: Validation orchestrator
            on_approve: Onay callback'i
            on_review: İnceleme callback'i
            on_reject: Red callback'i
            on_error: Hata callback'i
            admin_notification_callback: Admin bildirim callback'i
            enabled: Hook aktif mi
        """
        self.orchestrator = orchestrator or ResponseValidationOrchestrator()
        self.on_approve = on_approve
        self.on_review = on_review
        self.on_reject = on_reject
        self.on_error = on_error
        self.admin_notification_callback = admin_notification_callback
        self.enabled = enabled

        # İstatistikler
        self._stats = {
            "total_triggered": 0,
            "approved": 0,
            "review": 0,
            "rejected": 0,
            "errors": 0,
        }

    async def on_response_complete(
        self,
        response: AgentResponse,
    ) -> Dict[str, Any]:
        """
        AI yanıt tamamlandığında çağrılır.

        Args:
            response: Tamamlanan agent yanıtı

        Returns:
            Dict: Doğrulama sonucu
        """
        if not self.enabled:
            return {
                "skipped": True,
                "reason": "Hook disabled",
            }

        self._stats["total_triggered"] += 1

        try:
            # Doğrulama yap
            validation_result = await self.orchestrator.validate_response(response)

            # Sonuçları logla
            await self._log_validation(response, validation_result)

            # Aksiyona göre işlem yap
            action = ValidationAction(validation_result["action"])

            if action == ValidationAction.REJECT:
                self._stats["rejected"] += 1
                await self._handle_rejection(response, validation_result)
            elif action == ValidationAction.REVIEW:
                self._stats["review"] += 1
                await self._handle_review(response, validation_result)
            else:
                self._stats["approved"] += 1
                await self._handle_approval(response, validation_result)

            return validation_result

        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Validation hook error: {e}")

            # Fail-open: hata olsa bile yanıtı geçir
            if self.on_error:
                await self._safe_callback(
                    self.on_error, response, str(e)
                )

            return {
                "error": str(e),
                "action": "approve",  # Fail-open
                "confidence_score": 0.5,
                "message": "Validation failed, response approved by default",
            }

    async def _log_validation(
        self,
        response: AgentResponse,
        result: Dict[str, Any],
    ):
        """Doğrulama sonuçlarını logla"""
        logger.info(
            f"Validation complete: "
            f"response_id={response.response_id}, "
            f"agent_type={response.agent_type}, "
            f"confidence={result['confidence_score']:.3f}, "
            f"action={result['action']}, "
            f"duration={result['duration_seconds']:.2f}s"
        )

        # Hatalar varsa logla
        if result["errors"]:
            logger.warning(
                f"Validation errors for {response.response_id}: "
                f"{result['errors']}"
            )

    async def _handle_rejection(
        self,
        response: AgentResponse,
        result: Dict[str, Any],
    ):
        """Red durumunu işle"""
        logger.warning(
            f"Response REJECTED: {response.response_id}, "
            f"confidence={result['confidence_score']:.3f}"
        )

        # Admin'e bildir
        await self._notify_admin(
            response, result, "REJECTED"
        )

        # Callback çağır
        if self.on_reject:
            await self._safe_callback(
                self.on_reject, response, result
            )

    async def _handle_review(
        self,
        response: AgentResponse,
        result: Dict[str, Any],
    ):
        """İnceleme durumunu işle"""
        logger.info(
            f"Response flagged for REVIEW: {response.response_id}, "
            f"confidence={result['confidence_score']:.3f}"
        )

        # Callback çağır
        if self.on_review:
            await self._safe_callback(
                self.on_review, response, result
            )

    async def _handle_approval(
        self,
        response: AgentResponse,
        result: Dict[str, Any],
    ):
        """Onay durumunu işle"""
        logger.debug(
            f"Response APPROVED: {response.response_id}, "
            f"confidence={result['confidence_score']:.3f}"
        )

        # Callback çağır
        if self.on_approve:
            await self._safe_callback(
                self.on_approve, response, result
            )

    async def _notify_admin(
        self,
        response: AgentResponse,
        result: Dict[str, Any],
        status: str,
    ):
        """Admin'e bildirim gönder"""
        if self.admin_notification_callback:
            notification = {
                "type": "validation_alert",
                "status": status,
                "response_id": response.response_id,
                "agent_type": response.agent_type,
                "user_id": response.user_id,
                "confidence_score": result["confidence_score"],
                "errors": result["errors"],
                "warnings": result["warnings"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            await self._safe_callback(
                self.admin_notification_callback, notification
            )

    async def _safe_callback(
        self,
        callback: Callable,
        *args,
        **kwargs,
    ):
        """Callback'i güvenli çalıştır"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args, **kwargs)
            else:
                callback(*args, **kwargs)
        except Exception as e:
            logger.error(f"Callback error: {e}")

    def get_stats(self) -> Dict[str, int]:
        """Hook istatistiklerini al"""
        return self._stats.copy()

    def enable(self):
        """Hook'u etkinleştir"""
        self.enabled = True
        logger.info("Response validation hook enabled")

    def disable(self):
        """Hook'u devre dışı bırak"""
        self.enabled = False
        logger.info("Response validation hook disabled")


# Global hook instance
_global_hook: Optional[ResponseValidationHook] = None


def get_validation_hook() -> ResponseValidationHook:
    """Global hook instance'ı al veya oluştur"""
    global _global_hook
    if _global_hook is None:
        _global_hook = ResponseValidationHook()
    return _global_hook


def set_validation_hook(hook: ResponseValidationHook):
    """Global hook instance'ı ayarla"""
    global _global_hook
    _global_hook = hook


async def validate_on_complete(response: AgentResponse) -> Dict[str, Any]:
    """
    Convenience function: Yanıt tamamlandığında doğrulama yap.

    Bu fonksiyon agent'lar tarafından çağrılabilir.

    Args:
        response: Agent yanıtı

    Returns:
        Dict: Doğrulama sonucu
    """
    hook = get_validation_hook()
    return await hook.on_response_complete(response)
