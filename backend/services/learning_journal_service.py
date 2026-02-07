"""
Claude Diary Plugin - Learning Journal Service

Ogrenme gunlugu ve knowledge graph servisi (REQ-4).
Spaced repetition, concept linking ve gap detection.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

import networkx as nx
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from models.diary import LearningEntry
from api.schemas.diary import (
    LearningEntryCreate,
    LearningReviewRequest,
    LearningReviewResponse,
)


class LearningJournalService:
    """
    Learning Journal servisi (REQ-4)

    Knowledge tracking:
    - Knowledge entry creation (REQ-4.1)
    - Categorization with tags (REQ-4.2)
    - Concept linking / knowledge graph (REQ-4.3)
    - Spaced repetition scheduling (REQ-4.4)
    - Gap detection (REQ-4.5)
    - Interactive visualization (REQ-4.6)
    """

    # Spaced repetition intervals (FSRS-inspired)
    INTERVALS = [1, 3, 7, 14, 30, 60, 120]  # Gun

    # Default ease factor
    DEFAULT_EASE = 2.5

    # Domain categories
    DOMAINS = ["backend", "frontend", "devops", "database", "security", "ai_ml", "testing"]

    def __init__(self, db: AsyncSession):
        """
        Initialize LearningJournalService.

        Args:
            db: AsyncSession - SQLAlchemy async session
        """
        self.db = db
        self._knowledge_graph: Optional[nx.Graph] = None

    # =========================================================================
    # REQ-4.1: Knowledge Entry Creation
    # =========================================================================

    async def create_entry(
        self,
        user_id: UUID,
        data: LearningEntryCreate,
    ) -> LearningEntry:
        """
        Yeni ogrenme kaydi olustur (REQ-4.1).

        Args:
            user_id: UUID - Kullanici ID
            data: LearningEntryCreate - Ogrenme verileri

        Returns:
            LearningEntry - Olusturulan kayit
        """
        # Ilk review zamani (yarin)
        next_review = datetime.now() + timedelta(days=1)

        # Auto-generate summary if not provided
        summary = data.summary
        if not summary and len(data.content) > 100:
            summary = data.content[:100] + "..."

        entry = LearningEntry(
            user_id=user_id,
            title=data.title,
            content=data.content,
            summary=summary,
            tags=data.tags or [],
            domain=data.domain,
            skill_type=data.skill_type,
            related_concepts=data.related_concepts or [],
            importance=data.importance,
            source_type=data.source_type,
            source_reference=data.source_reference,
            next_review=next_review,
            interval_days=1,
            ease_factor=self.DEFAULT_EASE,
        )

        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)

        # Knowledge graph'i invalidate et
        self._knowledge_graph = None

        return entry

    # =========================================================================
    # REQ-4.2: Categorization with Tags
    # =========================================================================

    def auto_tag(self, content: str, title: str) -> List[str]:
        """
        Icerigi otomatik etiketle (REQ-4.2).

        Args:
            content: str - Icerik
            title: str - Baslik

        Returns:
            List[str] - Otomatik etiketler
        """
        tags: Set[str] = set()
        text = f"{title} {content}".lower()

        # Domain detection
        domain_keywords = {
            "backend": ["api", "server", "database", "sql", "rest", "graphql", "fastapi", "django"],
            "frontend": ["react", "vue", "angular", "css", "html", "javascript", "typescript", "ui"],
            "devops": ["docker", "kubernetes", "ci/cd", "deploy", "jenkins", "github actions"],
            "database": ["postgresql", "mysql", "mongodb", "redis", "query", "index"],
            "security": ["auth", "jwt", "oauth", "xss", "sql injection", "encryption"],
            "ai_ml": ["machine learning", "neural", "model", "training", "prediction", "nlp"],
            "testing": ["test", "pytest", "unittest", "mock", "coverage", "assertion"],
        }

        for domain, keywords in domain_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    tags.add(domain)
                    break

        # Skill type detection
        skill_keywords = {
            "python": ["python", "pip", "virtualenv", "django", "fastapi"],
            "javascript": ["javascript", "js", "node", "npm", "react", "vue"],
            "sql": ["sql", "query", "join", "index", "postgresql", "mysql"],
            "git": ["git", "commit", "branch", "merge", "rebase"],
        }

        for skill, keywords in skill_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    tags.add(skill)
                    break

        return list(tags)[:10]  # Max 10 tags

    async def update_tags(
        self,
        entry_id: UUID,
        user_id: UUID,
        tags: List[str],
    ) -> Optional[LearningEntry]:
        """
        Etiketleri guncelle.

        Args:
            entry_id: UUID - Kayit ID
            user_id: UUID - Kullanici ID
            tags: List[str] - Yeni etiketler

        Returns:
            Optional[LearningEntry] - Guncellenmis kayit
        """
        entry = await self.get_entry_by_id(entry_id, user_id)
        if not entry:
            return None

        entry.tags = tags
        await self.db.commit()
        await self.db.refresh(entry)

        return entry

    # =========================================================================
    # REQ-4.3: Concept Linking (Knowledge Graph)
    # =========================================================================

    async def link_concepts(
        self,
        entry_id: UUID,
        user_id: UUID,
        concepts: List[str],
    ) -> Optional[LearningEntry]:
        """
        Kavramlari bagla (REQ-4.3).

        Args:
            entry_id: UUID - Kayit ID
            user_id: UUID - Kullanici ID
            concepts: List[str] - Baglanacak kavramlar

        Returns:
            Optional[LearningEntry] - Guncellenmis kayit
        """
        entry = await self.get_entry_by_id(entry_id, user_id)
        if not entry:
            return None

        # Mevcut kavramlari koru ve yenilerini ekle
        existing = set(entry.related_concepts or [])
        new_concepts = existing.union(set(concepts))
        entry.related_concepts = list(new_concepts)

        # Concept links guncelle
        concept_links = entry.concept_links or []
        for concept in concepts:
            if not any(cl.get("concept") == concept for cl in concept_links):
                concept_links.append({
                    "concept": concept,
                    "relationship_type": "related",
                    "added_at": datetime.now().isoformat(),
                })
        entry.concept_links = concept_links

        await self.db.commit()
        await self.db.refresh(entry)

        # Graph'i invalidate et
        self._knowledge_graph = None

        return entry

    async def get_knowledge_graph(
        self,
        user_id: UUID,
        max_nodes: int = 100,
    ) -> nx.Graph:
        """
        Knowledge graph olustur (REQ-4.3, REQ-4.6).

        Args:
            user_id: UUID - Kullanici ID
            max_nodes: int - Maksimum node sayisi

        Returns:
            nx.Graph - Knowledge graph
        """
        # Cache kullan
        if self._knowledge_graph is not None:
            return self._knowledge_graph

        G = nx.Graph()

        # Tum entry'leri getir
        entries = await self.get_entries(user_id, limit=max_nodes)

        # Node'lari ekle
        for entry in entries:
            G.add_node(
                str(entry.id),
                label=entry.title,
                domain=entry.domain,
                importance=entry.importance,
                mastery=entry.mastery_level,
                type="entry",
            )

            # Related concepts node olarak ekle
            for concept in (entry.related_concepts or []):
                concept_id = f"concept:{concept}"
                if not G.has_node(concept_id):
                    G.add_node(
                        concept_id,
                        label=concept,
                        type="concept",
                    )
                # Edge ekle
                G.add_edge(str(entry.id), concept_id, relationship="related_to")

            # Tag'leri node olarak ekle
            for tag in (entry.tags or []):
                tag_id = f"tag:{tag}"
                if not G.has_node(tag_id):
                    G.add_node(
                        tag_id,
                        label=tag,
                        type="tag",
                    )
                G.add_edge(str(entry.id), tag_id, relationship="tagged_with")

        self._knowledge_graph = G
        return G

    def get_graph_statistics(self, G: nx.Graph) -> Dict[str, Any]:
        """
        Graph istatistiklerini getir.

        Args:
            G: nx.Graph - Knowledge graph

        Returns:
            Dict - Graph istatistikleri
        """
        if G.number_of_nodes() == 0:
            return {
                "node_count": 0,
                "edge_count": 0,
                "density": 0,
                "components": 0,
                "central_nodes": [],
            }

        # Centrality hesapla
        try:
            centrality = nx.degree_centrality(G)
            central_nodes = sorted(
                centrality.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        except Exception:
            central_nodes = []

        return {
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges(),
            "density": round(nx.density(G), 4),
            "components": nx.number_connected_components(G),
            "central_nodes": [
                {"id": n, "label": G.nodes[n].get("label", n), "centrality": round(c, 3)}
                for n, c in central_nodes
            ],
        }

    # =========================================================================
    # REQ-4.4: Spaced Repetition Scheduling
    # =========================================================================

    async def get_due_reviews(
        self,
        user_id: UUID,
        limit: int = 10,
    ) -> List[LearningEntry]:
        """
        Review gereken kayitlari getir (REQ-4.4).

        Args:
            user_id: UUID - Kullanici ID
            limit: int - Maksimum kayit sayisi

        Returns:
            List[LearningEntry] - Review gereken kayitlar
        """
        now = datetime.now()

        query = (
            select(LearningEntry)
            .where(
                and_(
                    LearningEntry.user_id == user_id,
                    LearningEntry.next_review <= now
                )
            )
            .order_by(LearningEntry.next_review)
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def record_review(
        self,
        user_id: UUID,
        data: LearningReviewRequest,
    ) -> Optional[LearningReviewResponse]:
        """
        Review sonucunu kaydet ve schedule guncelle (REQ-4.4).

        FSRS-inspired algorithm:
        - Quality 1-2: Zorluk, kisa interval
        - Quality 3: Normal, orta interval
        - Quality 4-5: Kolay, uzun interval

        Args:
            user_id: UUID - Kullanici ID
            data: LearningReviewRequest - Review verisi

        Returns:
            Optional[LearningReviewResponse] - Sonuc veya None
        """
        entry = await self.get_entry_by_id(data.entry_id, user_id)
        if not entry:
            return None

        quality = data.quality  # 1-5
        remembered = data.remembered

        # Ease factor guncelle
        ease = entry.ease_factor
        if quality < 3:
            ease = max(1.3, ease - 0.15)
        elif quality > 3:
            ease = min(3.0, ease + 0.1)

        # Interval hesapla
        current_interval = entry.interval_days
        if remembered and quality >= 3:
            # Basarili review - interval'i uzat
            new_interval = int(current_interval * ease)
            new_interval = min(new_interval, 365)  # Max 1 yil
        else:
            # Basarisiz - interval'i kisalt
            new_interval = max(1, current_interval // 2)

        # Retention score guncelle
        review_count = entry.review_count + 1
        if remembered:
            retention = min(1.0, entry.retention_score + 0.1)
        else:
            retention = max(0.0, entry.retention_score - 0.2)

        # Mastery level guncelle
        mastery = (retention * 0.6) + (min(review_count, 10) / 10 * 0.4)

        # Next review zamani
        next_review = datetime.now() + timedelta(days=new_interval)

        # Entry'yi guncelle
        entry.ease_factor = ease
        entry.interval_days = new_interval
        entry.next_review = next_review
        entry.review_count = review_count
        entry.last_review = datetime.now()
        entry.retention_score = retention
        entry.mastery_level = mastery

        await self.db.commit()
        await self.db.refresh(entry)

        return LearningReviewResponse(
            entry_id=entry.id,
            next_review=next_review,
            new_interval_days=new_interval,
            retention_score=retention,
            mastery_level=mastery,
        )

    # =========================================================================
    # REQ-4.5: Gap Detection
    # =========================================================================

    async def detect_gaps(
        self,
        user_id: UUID,
    ) -> List[Dict[str, Any]]:
        """
        Knowledge gap'leri tespit et (REQ-4.5).

        Args:
            user_id: UUID - Kullanici ID

        Returns:
            List[Dict] - Tespit edilen gap'ler
        """
        gaps: List[Dict[str, Any]] = []

        # Tum entry'leri getir
        entries = await self.get_entries(user_id, limit=500)

        if not entries:
            return [{
                "type": "no_entries",
                "message": "Henüz öğrenme kaydı yok",
                "recommendation": "Öğrendiklerinizi kaydetmeye başlayın",
            }]

        # Domain coverage analizi
        covered_domains = set()
        domain_entries: Dict[str, int] = {}

        for entry in entries:
            if entry.domain:
                covered_domains.add(entry.domain)
                domain_entries[entry.domain] = domain_entries.get(entry.domain, 0) + 1

        # Eksik domain'ler
        missing_domains = set(self.DOMAINS) - covered_domains
        for domain in missing_domains:
            gaps.append({
                "type": "missing_domain",
                "domain": domain,
                "message": f"'{domain}' alanında hiç kayıt yok",
                "recommendation": f"'{domain}' alanında öğrenmeye başlayın",
                "priority": 1,
            })

        # Az kapsama olan domain'ler
        for domain, count in domain_entries.items():
            if count < 3:
                gaps.append({
                    "type": "low_coverage",
                    "domain": domain,
                    "entry_count": count,
                    "message": f"'{domain}' alanında sadece {count} kayıt var",
                    "recommendation": f"'{domain}' alanında daha fazla kayıt ekleyin",
                    "priority": 2,
                })

        # Dusuk retention'li konular
        low_retention = [e for e in entries if e.retention_score < 0.5 and e.review_count > 2]
        for entry in low_retention[:5]:
            gaps.append({
                "type": "low_retention",
                "entry_id": str(entry.id),
                "title": entry.title,
                "retention_score": entry.retention_score,
                "message": f"'{entry.title}' konusunda düşük retention",
                "recommendation": "Bu konuyu daha sık tekrar edin",
                "priority": 1,
            })

        # Uzun suredir review edilmemis
        stale_date = datetime.now() - timedelta(days=60)
        stale_entries = [e for e in entries if e.last_review and e.last_review < stale_date]
        if len(stale_entries) > 5:
            gaps.append({
                "type": "stale_knowledge",
                "count": len(stale_entries),
                "message": f"{len(stale_entries)} konu 60+ gündür tekrar edilmedi",
                "recommendation": "Eski konuları tekrar gözden geçirin",
                "priority": 2,
            })

        # Oncelik sirasina gore sirala
        gaps.sort(key=lambda x: x.get("priority", 99))

        return gaps

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    async def get_entries(
        self,
        user_id: UUID,
        domain: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 50,
    ) -> List[LearningEntry]:
        """
        Ogrenme kayitlarini getir.

        Args:
            user_id: UUID - Kullanici ID
            domain: Optional[str] - Domain filtresi
            tag: Optional[str] - Tag filtresi
            limit: int - Maksimum kayit sayisi

        Returns:
            List[LearningEntry] - Kayit listesi
        """
        conditions = [LearningEntry.user_id == user_id]

        if domain:
            conditions.append(LearningEntry.domain == domain)

        query = (
            select(LearningEntry)
            .where(and_(*conditions))
            .order_by(desc(LearningEntry.created_at))
            .limit(limit)
        )

        result = await self.db.execute(query)
        entries = list(result.scalars().all())

        # Tag filtresi (post-query)
        if tag:
            entries = [e for e in entries if tag in (e.tags or [])]

        return entries

    async def get_entry_by_id(
        self,
        entry_id: UUID,
        user_id: UUID,
    ) -> Optional[LearningEntry]:
        """
        ID ile kayit getir.

        Args:
            entry_id: UUID - Kayit ID
            user_id: UUID - Kullanici ID

        Returns:
            Optional[LearningEntry] - Kayit veya None
        """
        query = select(LearningEntry).where(
            and_(
                LearningEntry.id == entry_id,
                LearningEntry.user_id == user_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_entry(
        self,
        entry_id: UUID,
        user_id: UUID,
        data: LearningEntryCreate,
    ) -> Optional[LearningEntry]:
        """
        Kaydi guncelle.

        Args:
            entry_id: UUID - Kayit ID
            user_id: UUID - Kullanici ID
            data: LearningEntryCreate - Yeni veriler

        Returns:
            Optional[LearningEntry] - Guncellenmis kayit
        """
        entry = await self.get_entry_by_id(entry_id, user_id)
        if not entry:
            return None

        entry.title = data.title
        entry.content = data.content
        entry.summary = data.summary
        entry.tags = data.tags or []
        entry.domain = data.domain
        entry.skill_type = data.skill_type
        entry.related_concepts = data.related_concepts or []
        entry.importance = data.importance
        entry.source_type = data.source_type
        entry.source_reference = data.source_reference

        await self.db.commit()
        await self.db.refresh(entry)

        # Graph invalidate
        self._knowledge_graph = None

        return entry

    async def delete_entry(
        self,
        entry_id: UUID,
        user_id: UUID,
    ) -> bool:
        """
        Kaydi sil.

        Args:
            entry_id: UUID - Kayit ID
            user_id: UUID - Kullanici ID

        Returns:
            bool - Basari durumu
        """
        entry = await self.get_entry_by_id(entry_id, user_id)
        if not entry:
            return False

        await self.db.delete(entry)
        await self.db.commit()

        # Graph invalidate
        self._knowledge_graph = None

        return True

    # =========================================================================
    # Search and Discovery
    # =========================================================================

    async def search_entries(
        self,
        user_id: UUID,
        query: str,
        limit: int = 20,
    ) -> List[LearningEntry]:
        """
        Kayitlarda arama yap.

        Args:
            user_id: UUID - Kullanici ID
            query: str - Arama sorgusu
            limit: int - Maksimum sonuc sayisi

        Returns:
            List[LearningEntry] - Bulunan kayitlar
        """
        query_lower = query.lower()

        # Tum entry'leri getir ve filtrele (basit arama)
        all_entries = await self.get_entries(user_id, limit=500)

        matches = []
        for entry in all_entries:
            score = 0
            # Title match
            if query_lower in entry.title.lower():
                score += 10
            # Content match
            if query_lower in entry.content.lower():
                score += 5
            # Tag match
            for tag in (entry.tags or []):
                if query_lower in tag.lower():
                    score += 3
            # Concept match
            for concept in (entry.related_concepts or []):
                if query_lower in concept.lower():
                    score += 3

            if score > 0:
                matches.append((score, entry))

        # Skora gore sirala
        matches.sort(key=lambda x: x[0], reverse=True)

        return [entry for _, entry in matches[:limit]]

    async def get_related_entries(
        self,
        entry_id: UUID,
        user_id: UUID,
        limit: int = 5,
    ) -> List[LearningEntry]:
        """
        Ilgili kayitlari getir.

        Args:
            entry_id: UUID - Kayit ID
            user_id: UUID - Kullanici ID
            limit: int - Maksimum sonuc sayisi

        Returns:
            List[LearningEntry] - Ilgili kayitlar
        """
        entry = await self.get_entry_by_id(entry_id, user_id)
        if not entry:
            return []

        # Tum entry'leri getir
        all_entries = await self.get_entries(user_id, limit=500)

        related = []
        for other in all_entries:
            if other.id == entry.id:
                continue

            score = 0

            # Ayni domain
            if entry.domain and entry.domain == other.domain:
                score += 5

            # Ortak tag'ler
            entry_tags = set(entry.tags or [])
            other_tags = set(other.tags or [])
            score += len(entry_tags & other_tags) * 3

            # Ortak kavramlar
            entry_concepts = set(entry.related_concepts or [])
            other_concepts = set(other.related_concepts or [])
            score += len(entry_concepts & other_concepts) * 4

            if score > 0:
                related.append((score, other))

        related.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in related[:limit]]
