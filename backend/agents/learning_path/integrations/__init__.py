"""External Service Integrations.

This package contains integrations with external services:
- YouTubeIntegration: YouTube API integration
- KhanIntegration: Khan Academy API integration
- OERIntegration: Open Educational Resources integration
- ChatIntegrationService: Chat-based learning path interaction
- ChatIntegration: Legacy chat interface wrapper
- FormIntegration: Form interface integration
"""

from .chat_integration import (
    ChatIntegration,
    ChatIntegrationService,
    ChatIntent,
    ChatMessage,
    ChatResponse,
)
from .form_integration import (
    FormDefinition,
    FormField,
    FormFieldType,
    FormIntegration,
    FormIntegrationService,
    FormSubmission,
    FormSubmissionResult,
    FormValidationResult,
)
from .khan_integration import KhanIntegration
from .oer_integration import OERIntegration
from .youtube_integration import YouTubeIntegration

__all__ = [
    # Legacy classes
    "YouTubeIntegration",
    "KhanIntegration",
    "OERIntegration",
    "ChatIntegration",
    "FormIntegration",
    # Service classes
    "ChatIntegrationService",
    "FormIntegrationService",
    # Chat types
    "ChatMessage",
    "ChatResponse",
    "ChatIntent",
    # Form types
    "FormDefinition",
    "FormField",
    "FormFieldType",
    "FormSubmission",
    "FormValidationResult",
    "FormSubmissionResult",
]
