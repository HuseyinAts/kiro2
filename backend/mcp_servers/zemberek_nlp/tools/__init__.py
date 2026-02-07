"""
Zemberek NLP Tools Package
9 NLP tool handlers for MCP server (8 core + 1 advanced)
"""

from .base import BaseToolHandler
from .morphology import MorphologyHandler
from .lemmatization import LemmatizationHandler
from .spell_check import SpellCheckHandler
from .tokenization import TokenizationHandler
from .ner import NERHandler
from .segmentation import SegmentationHandler
from .normalization import NormalizationHandler
from .health import HealthHandler
from .entity_linker import EntityLinkerHandler

__all__ = [
    "BaseToolHandler",
    "MorphologyHandler",
    "LemmatizationHandler",
    "SpellCheckHandler",
    "TokenizationHandler",
    "NERHandler",
    "SegmentationHandler",
    "NormalizationHandler",
    "HealthHandler",
    "EntityLinkerHandler",
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
