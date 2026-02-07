"""
Zemberek JPype Bridge Module
Thread-safe bridge to Zemberek Java library via JPype
"""

from .jpype_bridge import ZemberekJPypeBridge, get_bridge
from .exceptions import (
    ZemberekError,
    JVMInitializationError,
    JVMNotStartedError,
    AnalysisError,
    SpellCheckError,
    TokenizationError,
    NERError,
)

__all__ = [
    "ZemberekJPypeBridge",
    "get_bridge",
    "ZemberekError",
    "JVMInitializationError",
    "JVMNotStartedError",
    "AnalysisError",
    "SpellCheckError",
    "TokenizationError",
    "NERError",
]
