"""
Zemberek NLP Tools Package
9 NLP tool handlers for MCP server (8 core + 1 advanced)
"""

from .base import BaseToolHandler
from .entity_linker import EntityLinkerHandler
from .health import HealthHandler
from .lemmatization import LemmatizationHandler
from .morphology import MorphologyHandler
from .ner import NERHandler
from .normalization import NormalizationHandler
from .segmentation import SegmentationHandler
from .spell_check import SpellCheckHandler
from .tokenization import TokenizationHandler

__all__ = [
    "BaseToolHandler",
    "EntityLinkerHandler",
    "HealthHandler",
    "LemmatizationHandler",
    "MorphologyHandler",
    "NERHandler",
    "NormalizationHandler",
    "SegmentationHandler",
    "SpellCheckHandler",
    "TokenizationHandler",
]


# Tool name to handler mapping
TOOL_HANDLERS = {
    "zemberek_analyze": MorphologyHandler,
    "zemberek_lemmatize": LemmatizationHandler,
    "zemberek_spell_check": SpellCheckHandler,
    "zemberek_tokenize": TokenizationHandler,
    "zemberek_ner": NERHandler,
    "zemberek_segment_sentences": SegmentationHandler,
    "zemberek_normalize": NormalizationHandler,
    "zemberek_health": HealthHandler,
    "zemberek_entity_link": EntityLinkerHandler,
}
