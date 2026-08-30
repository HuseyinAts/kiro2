import logging

from services.llm.base_llm_provider import LLMRequest
from services.llm.ensemble_manager import MultiLLMEnsembleManager
from services.llm.multi_llm_config import LLMProvider

logger = logging.getLogger(__name__)


class AIMentorService:
    """
    Service for generating AI-driven motivational nudges and feedback
    using the Qwen3-8B model (or fallback).
    """

    def __init__(self, ensemble_manager: MultiLLMEnsembleManager | None = None):
        # Lazy (bkz. services/sequential_reasoning_service.py'deki aynı desen):
        # MultiLLMEnsembleManager() en az bir LLM sağlayıcı anahtarı bulamazsa
        # `RuntimeError` fırlatır. Bu dosyanın sonundaki modül-seviyesi
        # `ai_mentor_service` singleton'ı import ANINDA değil, ilk gerçek
        # kullanımda kurulmalı -- yoksa hiçbir sağlayıcı anahtarı olmayan bir
        # ortamda salt `import` bile uygulamayı çökertir.
        self._ensemble_manager = ensemble_manager

    @property
    def ensemble_manager(self) -> MultiLLMEnsembleManager:
        """Get or create ensemble manager (lazy)."""
        if self._ensemble_manager is None:
            self._ensemble_manager = MultiLLMEnsembleManager()
        return self._ensemble_manager

    async def generate_nudge(
        self,
        student_name: str,
        topic_name: str,
        score: float,
        missing_concepts: list[str],
    ) -> str:
        """
        Generates a short, encouraging nudge for the student based on test performance.
        """
        prompt = (
            f"Sen YKS'ye hazırlanan bir öğrencinin motivasyon koçusun. "
            f"Öğrencinin adı {student_name}. Az önce '{topic_name}' testini %{int(score * 100)} başarıyla bitirdi. "
        )

        if missing_concepts:
            concepts_str = ", ".join(missing_concepts)
            prompt += f"Şu konularda eksikleri var: {concepts_str}. "
        else:
            prompt += "Tüm konularda çok başarılıydı! "

        prompt += (
            "Sadece 2-3 cümlelik, cesaretlendirici, arkadaş canlısı ve "
            "ne yapması gerektiğini söyleyen Türkçe bir geri bildirim ver. "
            "Öğrencinin adını kullanarak motive et."
        )

        request = LLMRequest(
            prompt=prompt,
            system_prompt="Sen sıcakkanlı ve motive edici bir yapay zeka eğitim mentorusun.",
            max_tokens=150,
            temperature=0.7,
        )

        try:
            # We prefer QWEN as stated in the AGENTS.md (Qwen3-8B fine-tuned)
            # If it's not available, it will fallback to other providers
            response = await self.ensemble_manager.generate_with_fallback(
                request, preferred_provider=LLMProvider.QWEN
            )
            nudge_text: str = response.text
            return nudge_text
        except Exception as e:
            logger.error(f"Failed to generate AI nudge: {e}")
            # Fallback static message
            if missing_concepts:
                return f"Harika bir efor {student_name}! {topic_name} konusunda biraz daha pratiğe ihtiyacımız var, özellikle eksik olduğun noktalara odaklanalım."
            return f"Tebrikler {student_name}! {topic_name} konusunda harika iş çıkardın, aynen böyle devam!"


ai_mentor_service = AIMentorService()
