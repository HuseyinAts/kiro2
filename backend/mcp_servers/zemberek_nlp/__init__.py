"""
Zemberek NLP MCP Server Package
Turkish NLP tools exposed via Model Context Protocol

8 Tools:
- zemberek_analyze: Morphological analysis
- zemberek_lemmatize: Lemmatization
- zemberek_spell_check: Spell checking
- zemberek_tokenize: Tokenization
- zemberek_ner: Named Entity Recognition
- zemberek_segment_sentences: Sentence segmentation
- zemberek_normalize: Text normalization
- zemberek_health: Health check
"""

from .config import ZemberekConfig, get_config

__version__ = "1.0.0"
__all__ = ["ZemberekConfig", "get_config"]
