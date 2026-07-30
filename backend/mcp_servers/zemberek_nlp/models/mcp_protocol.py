"""
MCP Protocol Models for Zemberek NLP Server

Defines MCP protocol request/response schemas.
"""

from typing import Any

from pydantic import BaseModel, Field


class MCPToolCall(BaseModel):
    """MCP tool call request."""

    name: str = Field(..., description="Tool adı (e.g., zemberek_analyze)")
    arguments: dict[str, Any] = Field(
        default_factory=dict, description="Tool argümanları"
    )


class MCPTextContent(BaseModel):
    """MCP text content block."""

    type: str = Field(default="text", description="Content tipi")
    text: str = Field(..., description="İçerik metni")


class MCPToolResponse(BaseModel):
    """MCP tool call response."""

    content: list[MCPTextContent] = Field(..., description="Response içeriği")
    isError: bool = Field(default=False, description="Hata oluştu mu")


class MCPInputSchema(BaseModel):
    """MCP tool input schema definition."""

    type: str = Field(default="object", description="Schema tipi")
    properties: dict[str, dict[str, Any]] = Field(
        default_factory=dict, description="Property tanımları"
    )
    required: list[str] = Field(default_factory=list, description="Zorunlu alanlar")


class MCPToolDefinition(BaseModel):
    """MCP tool definition for listing."""

    name: str = Field(..., description="Tool adı")
    description: str = Field(..., description="Tool açıklaması")
    inputSchema: MCPInputSchema = Field(..., description="Input schema")


class MCPToolsListResponse(BaseModel):
    """MCP tools list response."""

    tools: list[MCPToolDefinition] = Field(..., description="Kullanılabilir tool'lar")


# Pre-defined tool definitions for Zemberek
ZEMBEREK_TOOLS: list[MCPToolDefinition] = [
    MCPToolDefinition(
        name="zemberek_analyze",
        description="Türkçe morphological analysis - kök, ek, tip bilgisi",
        inputSchema=MCPInputSchema(
            type="object",
            properties={
                "text": {
                    "type": "string",
                    "description": "Analiz edilecek Türkçe metin",
                }
            },
            required=["text"],
        ),
    ),
    MCPToolDefinition(
        name="zemberek_lemmatize",
        description="Türkçe lemmatization - kelime köklerini bulma",
        inputSchema=MCPInputSchema(
            type="object",
            properties={
                "text": {"type": "string", "description": "Lemmatize edilecek metin"},
                "batch": {
                    "type": "boolean",
                    "description": "Batch processing aktif mi",
                },
            },
            required=["text"],
        ),
    ),
    MCPToolDefinition(
        name="zemberek_spell_check",
        description="Türkçe yazım denetimi ve düzeltme önerileri",
        inputSchema=MCPInputSchema(
            type="object",
            properties={
                "text": {"type": "string", "description": "Kontrol edilecek metin"}
            },
            required=["text"],
        ),
    ),
    MCPToolDefinition(
        name="zemberek_tokenize",
        description="Türkçe tokenization - sözcük ayırma",
        inputSchema=MCPInputSchema(
            type="object",
            properties={
                "text": {"type": "string", "description": "Tokenize edilecek metin"}
            },
            required=["text"],
        ),
    ),
    MCPToolDefinition(
        name="zemberek_ner",
        description="Türkçe Named Entity Recognition - özel isim tespiti",
        inputSchema=MCPInputSchema(
            type="object",
            properties={
                "text": {"type": "string", "description": "NER yapılacak metin"}
            },
            required=["text"],
        ),
    ),
    MCPToolDefinition(
        name="zemberek_segment_sentences",
        description="Türkçe cümle segmentasyonu",
        inputSchema=MCPInputSchema(
            type="object",
            properties={
                "text": {"type": "string", "description": "Segment edilecek metin"}
            },
            required=["text"],
        ),
    ),
    MCPToolDefinition(
        name="zemberek_normalize",
        description="Türkçe metin normalizasyonu - informal -> formal",
        inputSchema=MCPInputSchema(
            type="object",
            properties={
                "text": {"type": "string", "description": "Normalize edilecek metin"}
            },
            required=["text"],
        ),
    ),
    MCPToolDefinition(
        name="zemberek_health",
        description="Zemberek server health check",
        inputSchema=MCPInputSchema(type="object", properties={}),
    ),
    MCPToolDefinition(
        name="zemberek_entity_link",
        description="Türkçe entity linking - bilgi tabanına bağlama",
        inputSchema=MCPInputSchema(
            type="object",
            properties={
                "text": {
                    "type": "string",
                    "description": "Entity linking yapılacak metin",
                }
            },
            required=["text"],
        ),
    ),
]
