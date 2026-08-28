"""
Zemberek-NLP Models Package

Pydantic schemas for tool inputs/outputs and MCP protocol.
"""

from .mcp_protocol import (
    ZEMBEREK_TOOLS,
    MCPInputSchema,
    MCPTextContent,
    MCPToolCall,
    MCPToolDefinition,
    MCPToolResponse,
    MCPToolsListResponse,
)
from .tool_schemas import (
    ComponentStatus,
    EntityLinkResult,
    HealthCheckResult,
    LemmaResult,
    LemmatizationResult,
    LinkedEntity,
    MorphologyAnalysis,
    MorphologyResult,
    NamedEntity,
    NERResult,
    NormalizationChange,
    NormalizationResult,
    Sentence,
    SentenceSegmentationResult,
    SpellCheckResult,
    SpellCheckWord,
    TokenizationResult,
    WordAnalysis,
)

__all__ = [
    # Tool Schemas
    "MorphologyAnalysis",
    "WordAnalysis",
    "MorphologyResult",
    "LemmaResult",
    "LemmatizationResult",
    "SpellCheckWord",
    "SpellCheckResult",
    "TokenizationResult",
    "NamedEntity",
    "NERResult",
    "Sentence",
    "SentenceSegmentationResult",
    "NormalizationChange",
    "NormalizationResult",
    "ComponentStatus",
    "HealthCheckResult",
    "LinkedEntity",
    "EntityLinkResult",
    # MCP Protocol
    "MCPToolCall",
    "MCPTextContent",
    "MCPToolResponse",
    "MCPInputSchema",
    "MCPToolDefinition",
    "MCPToolsListResponse",
    "ZEMBEREK_TOOLS",
]
