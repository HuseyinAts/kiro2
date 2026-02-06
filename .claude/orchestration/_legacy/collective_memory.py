"""
Collective Memory - Agent'lar Arasi Bilgi Paylasimi

Tum agent'larin paylaştigi bilgi havuzu.
Ogrenilen bilgiler, basarili stratejiler ve deneyimler burada saklanir.
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from enum import Enum
import hashlib


class InsightType(Enum):
    """Bilgi tipi"""
    STRATEGY = "strategy"           # Basarili strateji
    PATTERN = "pattern"             # Tespit edilen pattern
    SOLUTION = "solution"           # Problem cozumu
    ANTI_PATTERN = "anti_pattern"   # Kacinilmasi gereken
    OPTIMIZATION = "optimization"   # Performans iyilestirme
    TOOL_USAGE = "tool_usage"       # Arac kullanimi bilgisi
    DOMAIN_KNOWLEDGE = "domain"     # Alan bilgisi


class InsightQuality(Enum):
    """Bilgi kalitesi"""
    VERIFIED = "verified"       # Dogrulanmis
    EXPERIMENTAL = "experimental"  # Deneysel
    DEPRECATED = "deprecated"   # Gecersiz


@dataclass
class Insight:
    """Bilgi kaydi"""
    insight_id: str
    insight_type: InsightType
    title: str
    content: str
    source_agent_id: str
    context: dict = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    quality: InsightQuality = InsightQuality.EXPERIMENTAL
    relevance_score: float = 0.5  # 0.0 - 1.0
    usage_count: int = 0
    success_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

    @property
    def success_rate(self) -> float:
        if self.usage_count == 0:
            return 0.0
        return self.success_count / self.usage_count

    def to_dict(self) -> dict:
        return {
            "insight_id": self.insight_id,
            "insight_type": self.insight_type.value,
            "title": self.title,
            "content": self.content,
            "source_agent_id": self.source_agent_id,
            "context": self.context,
            "tags": self.tags,
            "quality": self.quality.value,
            "relevance_score": self.relevance_score,
            "usage_count": self.usage_count,
            "success_count": self.success_count,
            "success_rate": self.success_rate,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Insight":
        insight = cls(
            insight_id=data["insight_id"],
            insight_type=InsightType(data["insight_type"]),
            title=data["title"],
            content=data["content"],
            source_agent_id=data["source_agent_id"],
            context=data.get("context", {}),
            tags=data.get("tags", []),
            quality=InsightQuality(data.get("quality", "experimental")),
            relevance_score=data.get("relevance_score", 0.5),
            usage_count=data.get("usage_count", 0),
            success_count=data.get("success_count", 0),
        )

        if "created_at" in data:
            insight.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            insight.updated_at = datetime.fromisoformat(data["updated_at"])
        if data.get("expires_at"):
            insight.expires_at = datetime.fromisoformat(data["expires_at"])

        return insight


class CollectiveMemory:
    """
    Collective Memory - Merkezi Bilgi Havuzu

    Ozellikler:
    - Insight saklama ve sorgulama
    - Relevance skorlama
    - Bilgi konsolidasyonu
    - Gecersiz bilgi temizleme
    - Tag-bazli arama
    """

    def __init__(self, base_path: str = ".claude"):
        self.base_path = Path(base_path)
        self.memory_file = self.base_path / "orchestration" / "collective_memory.json"

        self._insights: dict[str, Insight] = {}
        self._tag_index: dict[str, list[str]] = {}  # tag -> insight_ids
        self._type_index: dict[str, list[str]] = {}  # type -> insight_ids
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Memory'yi baslat"""
        await self._load_memory()
        self._build_indexes()

    async def _load_memory(self) -> None:
        """Bilgileri yukle"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for insight_data in data.get("insights", []):
                        insight = Insight.from_dict(insight_data)
                        self._insights[insight.insight_id] = insight
            except Exception as e:
                print(f"Warning: Could not load collective memory: {e}")

    async def _save_memory(self) -> None:
        """Bilgileri kaydet"""
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "insights": [i.to_dict() for i in self._insights.values()],
            "total_count": len(self._insights),
            "updated_at": datetime.now().isoformat(),
        }

        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _build_indexes(self) -> None:
        """Indexleri olustur"""
        self._tag_index.clear()
        self._type_index.clear()

        for insight_id, insight in self._insights.items():
            # Tag index
            for tag in insight.tags:
                if tag not in self._tag_index:
                    self._tag_index[tag] = []
                self._tag_index[tag].append(insight_id)

            # Type index
            type_key = insight.insight_type.value
            if type_key not in self._type_index:
                self._type_index[type_key] = []
            self._type_index[type_key].append(insight_id)

    def _generate_insight_id(self, title: str, content: str) -> str:
        """Benzersiz insight ID olustur"""
        hash_content = f"{title}-{content[:100]}-{datetime.now().isoformat()}"
        return hashlib.sha256(hash_content.encode()).hexdigest()[:12]

    async def store_insight(
        self,
        agent_id: str,
        insight_type: InsightType,
        title: str,
        content: str,
        tags: Optional[list[str]] = None,
        context: Optional[dict] = None,
        expires_days: Optional[int] = None
    ) -> Insight:
        """
        Yeni bilgi kaydet

        Args:
            agent_id: Kaynak agent
            insight_type: Bilgi tipi
            title: Baslik
            content: Icerik
            tags: Etiketler
            context: Ek bagiam
            expires_days: Gecerlilik suresi (gun)

        Returns:
            Kaydedilen Insight
        """
        async with self._lock:
            insight_id = self._generate_insight_id(title, content)

            # Check for duplicate
            existing = self._find_similar(title, content)
            if existing:
                # Update existing
                existing.usage_count += 1
                existing.updated_at = datetime.now()
                if context:
                    existing.context.update(context)
                await self._save_memory()
                return existing

            # Create new
            expires_at = None
            if expires_days:
                from datetime import timedelta
                expires_at = datetime.now() + timedelta(days=expires_days)

            insight = Insight(
                insight_id=insight_id,
                insight_type=insight_type,
                title=title,
                content=content,
                source_agent_id=agent_id,
                tags=tags or [],
                context=context or {},
                expires_at=expires_at,
            )

            self._insights[insight_id] = insight
            self._build_indexes()
            await self._save_memory()

            return insight

    def _find_similar(self, title: str, content: str) -> Optional[Insight]:
        """Benzer bilgi bul"""
        title_lower = title.lower()
        content_preview = content[:200].lower()

        for insight in self._insights.values():
            # Title similarity
            if insight.title.lower() == title_lower:
                return insight

            # Content similarity (simple check)
            if insight.content[:200].lower() == content_preview:
                return insight

        return None

    async def query_knowledge(
        self,
        query: str,
        insight_type: Optional[InsightType] = None,
        tags: Optional[list[str]] = None,
        min_relevance: float = 0.3,
        limit: int = 10
    ) -> list[Insight]:
        """
        Bilgi sorgula

        Args:
            query: Arama sorgusu
            insight_type: Filtre: bilgi tipi
            tags: Filtre: etiketler
            min_relevance: Minimum relevance skoru
            limit: Maksimum sonuc sayisi

        Returns:
            Eslesen bilgiler
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())
        results = []

        for insight in self._insights.values():
            # Check expiry
            if insight.expires_at and insight.expires_at < datetime.now():
                continue

            # Check quality
            if insight.quality == InsightQuality.DEPRECATED:
                continue

            # Type filter
            if insight_type and insight.insight_type != insight_type:
                continue

            # Tag filter
            if tags:
                if not any(tag in insight.tags for tag in tags):
                    continue

            # Calculate relevance
            relevance = self._calculate_relevance(query_words, insight)

            if relevance >= min_relevance:
                insight.relevance_score = relevance
                results.append(insight)

        # Sort by relevance
        results.sort(key=lambda i: i.relevance_score, reverse=True)

        return results[:limit]

    def _calculate_relevance(self, query_words: set, insight: Insight) -> float:
        """Relevance skoru hesapla"""
        title_words = set(insight.title.lower().split())
        content_words = set(insight.content.lower().split()[:100])  # First 100 words
        tag_words = set(t.lower() for t in insight.tags)

        # Word overlap
        title_match = len(query_words & title_words) / max(1, len(query_words))
        content_match = len(query_words & content_words) / max(1, len(query_words))
        tag_match = len(query_words & tag_words) / max(1, len(query_words))

        # Weighted score
        base_score = (title_match * 0.4) + (content_match * 0.3) + (tag_match * 0.3)

        # Boost factors
        if insight.quality == InsightQuality.VERIFIED:
            base_score *= 1.2

        if insight.success_rate > 0.8:
            base_score *= 1.1

        # Recent insights slightly preferred
        age_days = (datetime.now() - insight.created_at).days
        if age_days < 7:
            base_score *= 1.05

        return min(1.0, base_score)

    async def record_usage(
        self,
        insight_id: str,
        success: bool
    ) -> None:
        """
        Bilgi kullanimini kaydet

        Args:
            insight_id: Kullanilan bilgi ID
            success: Basarili mi
        """
        if insight_id in self._insights:
            insight = self._insights[insight_id]
            insight.usage_count += 1
            if success:
                insight.success_count += 1
            insight.updated_at = datetime.now()

            # Auto-verify if consistently successful
            if insight.usage_count >= 10 and insight.success_rate >= 0.8:
                insight.quality = InsightQuality.VERIFIED

            # Auto-deprecate if consistently failing
            if insight.usage_count >= 5 and insight.success_rate < 0.3:
                insight.quality = InsightQuality.DEPRECATED

            await self._save_memory()

    async def consolidate_memories(self) -> int:
        """
        Benzer bilgileri birlestir

        Returns:
            Birlestirilen bilgi sayisi
        """
        consolidated = 0
        to_remove = []

        insights_list = list(self._insights.values())

        for i, insight1 in enumerate(insights_list):
            for insight2 in insights_list[i+1:]:
                if insight2.insight_id in to_remove:
                    continue

                # Check similarity
                similarity = self._compute_similarity(insight1, insight2)

                if similarity > 0.8:
                    # Merge into the better one
                    if insight1.success_rate >= insight2.success_rate:
                        self._merge_insights(insight1, insight2)
                        to_remove.append(insight2.insight_id)
                    else:
                        self._merge_insights(insight2, insight1)
                        to_remove.append(insight1.insight_id)

                    consolidated += 1

        # Remove merged insights
        for insight_id in to_remove:
            if insight_id in self._insights:
                del self._insights[insight_id]

        self._build_indexes()
        await self._save_memory()

        return consolidated

    def _compute_similarity(self, i1: Insight, i2: Insight) -> float:
        """Iki insight arasindaki benzerlik"""
        # Same type
        if i1.insight_type != i2.insight_type:
            return 0.0

        # Title similarity
        t1_words = set(i1.title.lower().split())
        t2_words = set(i2.title.lower().split())
        title_sim = len(t1_words & t2_words) / max(1, len(t1_words | t2_words))

        # Content similarity (first 200 chars)
        c1 = i1.content[:200].lower()
        c2 = i2.content[:200].lower()
        content_sim = 1.0 if c1 == c2 else 0.0

        # Tag similarity
        tag_sim = len(set(i1.tags) & set(i2.tags)) / max(1, len(set(i1.tags) | set(i2.tags)))

        return (title_sim * 0.4) + (content_sim * 0.4) + (tag_sim * 0.2)

    def _merge_insights(self, target: Insight, source: Insight) -> None:
        """Source'u target'a birlestir"""
        target.usage_count += source.usage_count
        target.success_count += source.success_count
        target.tags = list(set(target.tags + source.tags))
        target.context.update(source.context)
        target.updated_at = datetime.now()

        # Keep better content if source has higher success rate
        if source.success_rate > target.success_rate:
            target.content = source.content

    async def cleanup_expired(self) -> int:
        """
        Gecersiz bilgileri temizle

        Returns:
            Temizlenen bilgi sayisi
        """
        now = datetime.now()
        to_remove = []

        for insight_id, insight in self._insights.items():
            # Expired
            if insight.expires_at and insight.expires_at < now:
                to_remove.append(insight_id)
                continue

            # Deprecated and old
            if insight.quality == InsightQuality.DEPRECATED:
                age_days = (now - insight.updated_at).days
                if age_days > 30:
                    to_remove.append(insight_id)

        for insight_id in to_remove:
            del self._insights[insight_id]

        self._build_indexes()
        await self._save_memory()

        return len(to_remove)

    async def get_top_insights(
        self,
        insight_type: Optional[InsightType] = None,
        limit: int = 10
    ) -> list[Insight]:
        """En iyi bilgileri getir"""
        insights = list(self._insights.values())

        if insight_type:
            insights = [i for i in insights if i.insight_type == insight_type]

        # Sort by success rate and usage
        insights.sort(
            key=lambda i: (i.success_rate, i.usage_count),
            reverse=True
        )

        return insights[:limit]

    async def get_insights_by_agent(self, agent_id: str) -> list[Insight]:
        """Agent'in paylastigi bilgileri getir"""
        return [
            i for i in self._insights.values()
            if i.source_agent_id == agent_id
        ]

    def get_statistics(self) -> dict:
        """Memory istatistikleri"""
        total = len(self._insights)

        type_dist = {}
        for t in InsightType:
            type_dist[t.value] = len(self._type_index.get(t.value, []))

        quality_dist = {q.value: 0 for q in InsightQuality}
        for insight in self._insights.values():
            quality_dist[insight.quality.value] += 1

        return {
            "total_insights": total,
            "type_distribution": type_dist,
            "quality_distribution": quality_dist,
            "total_tags": len(self._tag_index),
            "top_tags": sorted(
                self._tag_index.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )[:10],
        }
