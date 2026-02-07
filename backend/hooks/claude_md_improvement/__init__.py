"""
CLAUDE.md Self-Improvement Hook System.

Boris Cherny verification feedback loops ile CLAUDE.md
otomatik iyileştirme mekanizması.

Bu modül:
- Feedback toplama (success/failure)
- Pattern detection trigger
- Rule evolution tetikleme
- Exit Code 2 mekanizması (Daisy Stanton)

Kullanım:
    from backend.hooks.claude_md_improvement import FeedbackHook, ImprovementOrchestrator

    hook = FeedbackHook()
    result = await hook.record_outcome(task_id, success=True)
"""

from __future__ import annotations

from .cache import CacheConfig, ImprovementCache, InMemoryCache, create_cache
from .feedback_hook import FeedbackHook
from .models import (
    FeedbackRecord,
    FeedbackType,
    ImprovementTrigger,
    RuleEffectiveness,
)
from .orchestrator import ImprovementOrchestrator
from .validators import (
    KIRO2ValidationResult,
    QuestionQualityMetrics,
    ZPDBounds,
    fix_turkish_encoding,
    is_turkish_text,
    turkish_lower,
    turkish_normalize,
    turkish_upper,
    validate_irt_params,
    validate_kiro2_question,
    validate_zpd_probability,
)

__all__ = [
    # Cache
    "CacheConfig",
    "ImprovementCache",
    "InMemoryCache",
    "create_cache",
    # Feedback
    "FeedbackHook",
    "FeedbackRecord",
    "FeedbackType",
    "ImprovementTrigger",
    "RuleEffectiveness",
    "ImprovementOrchestrator",
    # Validators
    "KIRO2ValidationResult",
    "QuestionQualityMetrics",
    "ZPDBounds",
    "fix_turkish_encoding",
    "is_turkish_text",
    "turkish_lower",
    "turkish_normalize",
    "turkish_upper",
    "validate_irt_params",
    "validate_kiro2_question",
    "validate_zpd_probability",
]
