"""
Context Manager - 200K Token Izolasyonu
REQ-7.1, REQ-7.2
Teknofest 2025 - KIRO2 YKS Platformu

Sid Bidasaria subagent mimarisi:
- Her agent icin 200K token HARD LIMIT
- Prioritized context management
- Automatic history pruning
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Default max tokens per agent (REQ-7.2)
DEFAULT_MAX_TOKENS = 200_000


class TokenCounter:
    """
    Token sayaci - tiktoken veya fallback

    Production'da tiktoken kullanilmali (daha dogru)
    Fallback: 4 karakter ~ 1 token (Turkce icin ~3.5)
    """

    def __init__(self, encoding_name: str = "cl100k_base"):
        """
        TokenCounter olustur

        Args:
            encoding_name: tiktoken encoding adi (Claude/GPT-4 icin cl100k_base)
        """
        self.encoding_name = encoding_name
        self._encoder = None
        self._use_fallback = False

        try:
            import tiktoken

            self._encoder = tiktoken.get_encoding(encoding_name)
            logger.info(f"TokenCounter initialized with tiktoken ({encoding_name})")
        except ImportError:
            self._use_fallback = True
            logger.warning(
                "tiktoken not available, using fallback token estimation"
            )

    def count(self, text: str) -> int:
        """
        Metindeki token sayisini hesapla

        Args:
            text: Token sayilacak metin

        Returns:
            Token sayisi
        """
        if not text:
            return 0

        if self._use_fallback:
            # Turkce icin ~3.5 karakter/token, genel ~4
            # Guvenli tarafta kalmak icin 3.5 kullan
            return max(1, int(len(text) / 3.5))

        try:
            return len(self._encoder.encode(text))
        except Exception as e:
            logger.warning(f"Token counting error, using fallback: {e}")
            return max(1, int(len(text) / 3.5))

    def count_messages(self, messages: List[Dict[str, str]]) -> int:
        """
        Mesaj listesindeki toplam token sayisi

        Args:
            messages: [{"role": "user", "content": "..."}] formatinda mesajlar

        Returns:
            Toplam token sayisi
        """
        total = 0
        for msg in messages:
            # Role + content + message overhead (~4 tokens per message)
            content = msg.get("content", "")
            total += self.count(content) + 4
        return total


@dataclass
class ContextEntry:
    """Tek bir context girisi"""

    content: str
    tokens: int
    priority: int = 0  # 0=low, 1=medium, 2=high
    entry_type: str = "general"  # "domain_knowledge", "history", "shared", "general"
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContextManager:
    """
    Agent Context Manager (REQ-7.1, REQ-7.2)

    Her agent icin 200K token HARD LIMIT enforces eder.
    Context asildigi zaman otomatik olarak dusuk oncelikli
    icerik cikarilir.

    Priority order (en dusukten en yuksege):
    0 - Eski conversation history
    1 - Shared context
    2 - Domain knowledge

    Attributes:
        max_tokens: Maximum token limiti (default 200K)
        current_tokens: Suanki token sayisi
        entries: Context girisleri
    """

    def __init__(
        self,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        auto_prune: bool = True,
    ):
        """
        ContextManager olustur

        Args:
            max_tokens: Maximum token limiti
            auto_prune: Limit asildiginda otomatik prune
        """
        if max_tokens <= 0:
            raise ValueError(f"max_tokens must be positive, got {max_tokens}")

        self.max_tokens = max_tokens
        self.auto_prune = auto_prune
        self.current_tokens = 0
        self.entries: List[ContextEntry] = []

        self._token_counter = TokenCounter()
        self._created_at = datetime.now()
        self._last_updated = datetime.now()

        logger.info(
            f"ContextManager initialized with max_tokens={max_tokens}, "
            f"auto_prune={auto_prune}"
        )

    def add_content(
        self,
        content: str,
        priority: int = 0,
        entry_type: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Context'e icerik ekle

        Args:
            content: Eklenecek metin
            priority: Oncelik (0=low, 1=medium, 2=high)
            entry_type: Giris tipi
            metadata: Ek bilgiler

        Returns:
            True eklendi, False eklenemedi (limit asildı ve prune yapilamadi)
        """
        if not content:
            return True  # Empty content is always OK

        tokens = self._token_counter.count(content)

        # Check if we can fit
        if self.current_tokens + tokens > self.max_tokens:
            if self.auto_prune:
                # Try to make space
                needed = (self.current_tokens + tokens) - self.max_tokens
                freed = self._prune(needed)
                if freed < needed:
                    logger.warning(
                        f"Could not free enough tokens. "
                        f"Needed: {needed}, freed: {freed}"
                    )
                    return False
            else:
                logger.warning(
                    f"Token limit exceeded: {self.current_tokens} + {tokens} > {self.max_tokens}"
                )
                return False

        # Add entry
        entry = ContextEntry(
            content=content,
            tokens=tokens,
            priority=priority,
            entry_type=entry_type,
            metadata=metadata or {},
        )
        self.entries.append(entry)
        self.current_tokens += tokens
        self._last_updated = datetime.now()

        logger.debug(
            f"Added {tokens} tokens ({entry_type}), "
            f"total: {self.current_tokens}/{self.max_tokens}"
        )
        return True

    def add_domain_knowledge(self, content: str, topic: str = "") -> bool:
        """Domain bilgisi ekle (yuksek oncelik)"""
        return self.add_content(
            content=content,
            priority=2,
            entry_type="domain_knowledge",
            metadata={"topic": topic},
        )

    def add_conversation(self, role: str, content: str) -> bool:
        """Conversation history ekle (dusuk oncelik)"""
        return self.add_content(
            content=f"{role}: {content}",
            priority=0,
            entry_type="history",
            metadata={"role": role},
        )

    def add_shared_context(self, source_agent: str, content: str) -> bool:
        """Shared context ekle (orta oncelik)"""
        return self.add_content(
            content=content,
            priority=1,
            entry_type="shared",
            metadata={"source_agent": source_agent},
        )

    def _prune(self, tokens_needed: int) -> int:
        """
        Dusuk oncelikli icerik cikararak yer ac

        Args:
            tokens_needed: Acihlmasi gereken token sayisi

        Returns:
            Acilan token sayisi
        """
        if not self.entries:
            return 0

        freed = 0

        # Sort by priority (lowest first), then by age (oldest first)
        sorted_entries = sorted(
            self.entries,
            key=lambda e: (e.priority, e.created_at),
        )

        entries_to_remove = []
        for entry in sorted_entries:
            if freed >= tokens_needed:
                break

            entries_to_remove.append(entry)
            freed += entry.tokens

        # Remove entries
        for entry in entries_to_remove:
            self.entries.remove(entry)
            self.current_tokens -= entry.tokens

        logger.info(
            f"Pruned {len(entries_to_remove)} entries, freed {freed} tokens"
        )
        return freed

    def clear(self):
        """Tum context'i temizle"""
        self.entries.clear()
        self.current_tokens = 0
        self._last_updated = datetime.now()
        logger.info("Context cleared")

    def clear_history(self):
        """Sadece conversation history'yi temizle"""
        history_entries = [e for e in self.entries if e.entry_type == "history"]
        for entry in history_entries:
            self.entries.remove(entry)
            self.current_tokens -= entry.tokens

        self._last_updated = datetime.now()
        logger.info(f"Cleared {len(history_entries)} history entries")

    def get_remaining_tokens(self) -> int:
        """Kalan token sayisi"""
        return self.max_tokens - self.current_tokens

    def get_usage_percentage(self) -> float:
        """Kullanim yuzdesi"""
        if self.max_tokens == 0:
            return 100.0
        return (self.current_tokens / self.max_tokens) * 100

    def can_fit(self, content: str) -> bool:
        """Icerigin sigip sigmayacagini kontrol et"""
        tokens = self._token_counter.count(content)
        return (self.current_tokens + tokens) <= self.max_tokens

    def get_context_string(
        self,
        include_types: Optional[List[str]] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Context'i string olarak al

        Args:
            include_types: Dahil edilecek entry tipleri (None = hepsi)
            max_tokens: Maximum token sayisi (None = limit yok)

        Returns:
            Birlestirilmis context string
        """
        filtered = self.entries
        if include_types:
            filtered = [e for e in filtered if e.entry_type in include_types]

        # Sort by priority (highest first)
        sorted_entries = sorted(filtered, key=lambda e: -e.priority)

        parts = []
        token_count = 0
        for entry in sorted_entries:
            if max_tokens and token_count + entry.tokens > max_tokens:
                break
            parts.append(entry.content)
            token_count += entry.tokens

        return "\n\n".join(parts)

    def get_status(self) -> Dict[str, Any]:
        """Context durumunu al"""
        return {
            "current_tokens": self.current_tokens,
            "max_tokens": self.max_tokens,
            "remaining_tokens": self.get_remaining_tokens(),
            "usage_percentage": self.get_usage_percentage(),
            "entry_count": len(self.entries),
            "entries_by_type": {
                entry_type: len([e for e in self.entries if e.entry_type == entry_type])
                for entry_type in set(e.entry_type for e in self.entries)
            },
            "created_at": self._created_at.isoformat(),
            "last_updated": self._last_updated.isoformat(),
        }

    def __repr__(self) -> str:
        return (
            f"ContextManager(tokens={self.current_tokens}/{self.max_tokens}, "
            f"entries={len(self.entries)})"
        )
