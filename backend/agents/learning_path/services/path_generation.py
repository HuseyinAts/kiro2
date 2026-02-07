"""
Path Generation Service
Teknofest 2025 - Eğitim Eylemci Projesi

Extracted from God Class (agent.py) following Single Responsibility Principle.

This service handles personalized learning path generation:
- Topic determination (LLM or templates)
- Prerequisite sequencing
- Resource allocation per topic
- Duration estimation

Dependencies:
- LLM service for topic generation
- ResourceDiscoveryService for finding resources
- StudentProfiler for profile management
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..models import StudentProfile

from ..config import get_learning_path_config
from ..models import (
    KnowledgeLevel,
    LearningPath,
    LearningResource,
    PathNode,
)

logger = logging.getLogger(__name__)


@dataclass
class PathGenerationRequest:
    """Request for path generation."""

    student_profile: StudentProfile
    target_subject: str
    target_topics: list[str] | None = None
    target_level: KnowledgeLevel = KnowledgeLevel.INTERMEDIATE
    max_duration_hours: int = 20
    include_exercises: bool = True
    include_videos: bool = True


@dataclass
class PathGenerationResult:
    """Result of path generation."""

    success: bool
    path: LearningPath | None = None
    nodes: list[PathNode] | None = None
    total_duration_minutes: int = 0
    error: str | None = None

    def __post_init__(self):
        if self.nodes is None:
            self.nodes = []


class PathGenerationService:
    """Service for generating personalized learning paths.

    Extracts path generation logic from the God Class (agent.py)
    following Single Responsibility Principle.

    This service:
    - Determines topics (LLM or templates)
    - Sequences topics by prerequisites
    - Allocates resources per topic
    - Calculates total duration
    """

    def __init__(
        self,
        llm_service=None,
        resource_finder=None,
        student_profiler=None,
    ):
        """Initialize PathGenerationService.

        Args:
            llm_service: LLM service for topic generation (optional)
            resource_finder: Resource discovery service (optional)
            student_profiler: Student profiler service (optional)
        """
        self.config = get_learning_path_config()
        self.llm_service = llm_service
        self.resource_finder = resource_finder
        self.student_profiler = student_profiler

        # Default topic templates for YKS
        self.yks_topic_templates = self._load_yks_templates()

        logger.info("PathGenerationService initialized")

    async def generate_path(self, request: PathGenerationRequest) -> PathGenerationResult:
        """Generate a personalized learning path.

        Args:
            request: Path generation request with student profile and targets

        Returns:
            PathGenerationResult with success status and generated path

        Example:
            >>> service = PathGenerationService(llm_service, resource_finder)
            >>> request = PathGenerationRequest(
            ...     student_profile=profile,
            ...     target_subject="matematik",
            ...     target_level=KnowledgeLevel.INTERMEDIATE
            ... )
            >>> result = await service.generate_path(request)
        """
        try:
            logger.info(
                f"Generating path for student: {request.student_profile.student_id}"
            )

            # Step 1: Determine topics
            topics = await self._determine_topics(request)
            if not topics:
                return PathGenerationResult(
                    success=False, error="No topics could be determined"
                )

            # Step 2: Sequence topics by prerequisites
            sequenced_topics = self._sequence_topics(topics, request.target_subject)

            # Step 3: Allocate resources per topic
            nodes = await self._create_path_nodes(sequenced_topics, request)

            # Step 4: Calculate total duration
            total_duration = sum(node.estimated_time for node in nodes)

            # Step 5: Create learning path
            path = LearningPath(
                path_id=f"path-{request.student_profile.student_id}-{request.target_subject}",
                student_id=request.student_profile.student_id,
                goal=f"{request.target_subject.capitalize()} Öğrenme Yolu",
                resources=[
                    resource for node in nodes for resource in node.resources
                ],  # Flatten resources
                phases=[],  # PathNode'lar kullanıldığı için phases boş
                created_at=__import__("datetime").datetime.now(),
                reasoning=f"{request.target_level.value} seviyesi için {request.target_subject} konuları",
                metadata={
                    "nodes": [node.to_dict() for node in nodes],
                    "target_level": request.target_level.value,
                    "total_duration_minutes": total_duration,
                },
            )

            logger.info(
                f"Generated path with {len(nodes)} nodes, {total_duration} minutes total"
            )

            return PathGenerationResult(
                success=True,
                path=path,
                nodes=nodes,
                total_duration_minutes=total_duration,
            )

        except Exception as e:
            logger.error(f"Path generation failed: {e}")
            return PathGenerationResult(success=False, error=str(e))

    async def _determine_topics(self, request: PathGenerationRequest) -> list[str]:
        """Determine topics to include in the path.

        Priority:
        1. Use provided topics if available
        2. Use LLM to generate topics
        3. Fallback to templates
        """
        # If topics provided, use them
        if request.target_topics:
            return request.target_topics

        # Otherwise, use LLM or templates
        if self.llm_service:
            return await self._get_topics_from_llm(request)

        # Fallback to templates
        return self._get_topics_from_template(
            request.target_subject, request.target_level
        )

    async def _get_topics_from_llm(self, request: PathGenerationRequest) -> list[str]:
        """Use LLM to generate topic list.

        Constructs a prompt asking the LLM to generate topics
        based on student profile and target subject.
        """
        try:
            prompt = f"""
            Öğrenci profili:
            - Seviye: {request.target_level.value}
            - Ders: {request.target_subject}
            - Öğrenme stili: {request.student_profile.learning_style.value}

            Bu öğrenci için {request.target_subject} dersinde öğrenmesi gereken
            konuları sırala. Önkoşul ilişkilerini dikkate al.

            JSON formatında döndür: {{"topics": ["konu1", "konu2", ...]}}
            """

            response = await self.llm_service.generate(prompt)

            # Parse response
            import json

            data = json.loads(response)
            return data.get("topics", [])

        except Exception as e:
            logger.warning(f"LLM topic generation failed: {e}")
            return self._get_topics_from_template(
                request.target_subject, request.target_level
            )

    def _get_topics_from_template(
        self, subject: str, level: KnowledgeLevel
    ) -> list[str]:
        """Get topics from predefined templates.

        Falls back to YKS templates when LLM is unavailable.
        Filters topics by knowledge level.
        """
        subject_lower = subject.lower()

        if subject_lower in self.yks_topic_templates:
            all_topics = self.yks_topic_templates[subject_lower]

            # Filter by level
            level_index = list(KnowledgeLevel).index(level)
            topics_per_level = len(all_topics) // 5
            start = level_index * topics_per_level
            end = start + topics_per_level + 5  # Include some overlap

            return all_topics[start : min(end, len(all_topics))]

        return []

    def _sequence_topics(
        self, topics: list[str], subject: str
    ) -> list[dict[str, Any]]:
        """Sequence topics by prerequisites.

        Uses topological sort to respect prerequisite relationships.

        Args:
            topics: List of topics
            subject: Subject name

        Returns:
            List of dictionaries with topic, prerequisites, and order
        """
        # Get prerequisite graph
        prereq_graph = self._get_prerequisite_graph(subject)

        # Topological sort
        sequenced = []
        visited = set()

        def visit(topic: str):
            if topic in visited:
                return
            visited.add(topic)

            # Visit prerequisites first
            prereqs = prereq_graph.get(topic, [])
            for prereq in prereqs:
                if prereq in topics:
                    visit(prereq)

            sequenced.append(
                {"topic": topic, "prerequisites": prereqs, "order": len(sequenced)}
            )

        for topic in topics:
            visit(topic)

        return sequenced

    def _get_prerequisite_graph(self, subject: str) -> dict[str, list[str]]:
        """Get prerequisite relationships for a subject.

        This could be loaded from database or config.
        Currently using hardcoded graphs for YKS subjects.

        Args:
            subject: Subject name

        Returns:
            Dictionary mapping topics to their prerequisites
        """
        subject_lower = subject.lower()

        if subject_lower == "matematik":
            return {
                "türev": ["limit", "süreklilik"],
                "integral": ["türev"],
                "limit": ["fonksiyonlar"],
                "fonksiyonlar": ["denklemler"],
                "olasılık": ["kombinatorik"],
                "kombinatorik": ["permütasyon"],
            }
        if subject_lower == "fizik":
            return {
                "kuvvet ve newton": ["hareket"],
                "enerji": ["kuvvet ve newton"],
                "momentum": ["kuvvet ve newton"],
                "dönme hareketi": ["kuvvet ve newton"],
            }
        if subject_lower == "kimya":
            return {
                "kimyasal bağlar": ["atom modelleri", "periyodik sistem"],
                "mol kavramı": ["kimyasal bağlar"],
                "gazlar": ["mol kavramı"],
                "çözeltiler": ["mol kavramı"],
            }

        return {}

    async def _create_path_nodes(
        self, sequenced_topics: list[dict[str, Any]], request: PathGenerationRequest
    ) -> list[PathNode]:
        """Create path nodes with resources for each topic.

        Args:
            sequenced_topics: Topics with prerequisite information
            request: Path generation request

        Returns:
            List of PathNode objects with resources
        """
        nodes = []

        for topic_info in sequenced_topics:
            topic = topic_info["topic"]
            order = topic_info["order"]

            # Find resources for this topic
            resources: list[LearningResource] = []
            if self.resource_finder:
                try:
                    # ResourceFinder'ın search_resources metodunu kullan
                    resources = await self.resource_finder.search_resources(
                        topic=topic,
                        subjects=[request.target_subject],
                        difficulty=request.target_level,
                        count=5,
                    )
                except Exception as e:
                    logger.warning(f"Resource search failed for {topic}: {e}")
                    resources = []

            # Estimate time
            estimated_time = self._estimate_topic_time(
                topic, request.target_level, resources
            )

            # Create node
            node = PathNode(
                node_id=f"node-{order}-{topic.replace(' ', '-')}",
                topic=topic,
                order=order,
                resources=resources,
                estimated_time=estimated_time,
                is_completed=False,
                prerequisites=topic_info.get("prerequisites", []),
            )

            nodes.append(node)

        return nodes

    def _estimate_topic_time(
        self,
        topic: str,
        level: KnowledgeLevel,
        resources: list[LearningResource],
    ) -> int:
        """Estimate time needed for a topic in minutes.

        Args:
            topic: Topic name
            level: Knowledge level
            resources: Resources for this topic

        Returns:
            Estimated time in minutes
        """
        # Base time by level
        base_times = {
            KnowledgeLevel.BEGINNER: 30,
            KnowledgeLevel.ELEMENTARY: 45,
            KnowledgeLevel.INTERMEDIATE: 60,
            KnowledgeLevel.ADVANCED: 90,
            KnowledgeLevel.EXPERT: 120,
        }

        base = base_times.get(level, 60)

        # Add resource times
        if resources:
            resource_time = sum(r.estimated_time for r in resources)
            return max(base, resource_time)

        return base

    def _load_yks_templates(self) -> dict[str, list[str]]:
        """Load YKS topic templates.

        These templates are used when LLM is unavailable.
        Topics are ordered from beginner to advanced.

        Returns:
            Dictionary mapping subjects to topic lists
        """
        return {
            "matematik": [
                "Temel Kavramlar",
                "Sayılar",
                "Bölünebilme",
                "EBOB-EKOK",
                "Rasyonel Sayılar",
                "Ondalık Sayılar",
                "Üslü Sayılar",
                "Köklü Sayılar",
                "Çarpanlara Ayırma",
                "Denklemler",
                "Eşitsizlikler",
                "Mutlak Değer",
                "Fonksiyonlar",
                "Polinomlar",
                "Permütasyon",
                "Kombinasyon",
                "Olasılık",
                "Limit",
                "Süreklilik",
                "Türev",
                "İntegral",
            ],
            "fizik": [
                "Birimler ve Vektörler",
                "Hareket",
                "Kuvvet ve Newton",
                "Enerji",
                "Momentum",
                "Dönme Hareketi",
                "Basit Harmonik",
                "Dalgalar",
                "Elektrik",
                "Manyetizma",
                "Optik",
                "Atom Fiziği",
            ],
            "kimya": [
                "Atom Modelleri",
                "Periyodik Sistem",
                "Kimyasal Bağlar",
                "Mol Kavramı",
                "Gazlar",
                "Çözeltiler",
                "Asit-Baz",
                "Elektrokimya",
                "Organik Kimya",
                "Reaksiyon Hızları",
            ],
            "biyoloji": [
                "Hücre",
                "Canlı Sistemleri",
                "Enerji Dönüşümleri",
                "Hücre Bölünmesi",
                "Kalıtım",
                "Evrim",
                "Ekosistem",
                "Bitkiler",
                "Solunum",
                "Dolaşım",
                "Sinir Sistemi",
            ],
        }
