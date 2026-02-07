"""
Konu Bazli Uzman Subagent Sistemi
REQ-1 to REQ-6: 6 Domain Expert Agent
Teknofest 2025 - KIRO2 YKS Platformu

Sid Bidasaria subagent mimarisi:
- Her agent 200K token izole context
- Blackboard pattern ile koordinasyon
- Sequential multi-domain isleme
"""

from .base_domain_agent import (
    BaseDomainAgent,
    DomainType,
    DomainResponse,
    DomainContext,
)
from .matematik_agent import MatematikAgent
from .fizik_agent import FizikAgent
from .turkce_agent import TurkceAgent
from .sosyal_agent import SosyalAgent
from .biyoloji_agent import BiyolojiAgent
from .yabanci_dil_agent import YabanciDilAgent

__all__ = [
    "BaseDomainAgent",
    "DomainType",
    "DomainResponse",
    "DomainContext",
    "MatematikAgent",
    "FizikAgent",
    "TurkceAgent",
    "SosyalAgent",
    "BiyolojiAgent",
    "YabanciDilAgent",
]
