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
    DomainContext,
    DomainResponse,
    DomainType,
)
from .biyoloji_agent import BiyolojiAgent
from .fizik_agent import FizikAgent
from .matematik_agent import MatematikAgent
from .sosyal_agent import SosyalAgent
from .turkce_agent import TurkceAgent
from .yabanci_dil_agent import YabanciDilAgent

__all__ = [
    "BaseDomainAgent",
    "BiyolojiAgent",
    "DomainContext",
    "DomainResponse",
    "DomainType",
    "FizikAgent",
    "MatematikAgent",
    "SosyalAgent",
    "TurkceAgent",
    "YabanciDilAgent",
]
