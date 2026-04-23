"""
KIRO2 Unified Content Management System
Comprehensive content management system for Turkish exam preparation platform
Türkiye Üniversite Sınavları Hazırlık Platformu - Birleşik İçerik Yönetim Sistemi
"""

import asyncio
import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from analytics.unified_analytics_data_model import (
    TurkishExamType,
    TurkishSubject,
)
from core.structured_logging import LogCategory, get_logger
from core.unified_config import get_unified_config

logger = get_logger(__name__, LogCategory.CONTENT)
config = get_unified_config()


class ContentType(Enum):
    """Types of content in the system"""

    QUESTION = "question"
    VIDEO = "video"
    DOCUMENT = "document"
    INTERACTIVE = "interactive"
    SIMULATION = "simulation"
    AUDIO = "audio"
    IMAGE = "image"
    QUIZ = "quiz"
    ASSIGNMENT = "assignment"
    LESSON_PLAN = "lesson_plan"


class ContentStatus(Enum):
    """Content lifecycle status"""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    REJECTED = "rejected"


class DifficultyLevel(Enum):
    """Content difficulty levels"""

    BASIC = "basic"  # Temel seviye
    INTERMEDIATE = "intermediate"  # Orta seviye
    ADVANCED = "advanced"  # İleri seviye
    EXPERT = "expert"  # Uzman seviye


class LearningObjective(Enum):
    """Learning objectives for Turkish education"""

    KNOWLEDGE = "knowledge"  # Bilgi
    COMPREHENSION = "comprehension"  # Kavrama
    APPLICATION = "application"  # Uygulama
    ANALYSIS = "analysis"  # Analiz
    SYNTHESIS = "synthesis"  # Sentez
    EVALUATION = "evaluation"  # Değerlendirme


@dataclass
class ContentMetadata:
    """Metadata for content items"""

    # Basic info
    title: str
    description: str
    keywords: list[str] = field(default_factory=list)
    language: str = "tr"

    # Educational context
    subject: TurkishSubject
    exam_types: list[TurkishExamType] = field(default_factory=list)
    grade_levels: list[int] = field(default_factory=list)  # 9-12
    topics: list[str] = field(default_factory=list)
    subtopics: list[str] = field(default_factory=list)

    # Learning classification
    difficulty_level: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    learning_objectives: list[LearningObjective] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)

    # Content properties
    estimated_duration_minutes: int = 0
    interaction_required: bool = False
    accessibility_features: list[str] = field(default_factory=list)

    # Turkish curriculum alignment
    curriculum_code: str | None = None
    curriculum_outcome: str | None = None
    bloom_taxonomy_level: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "title": self.title,
            "description": self.description,
            "keywords": self.keywords,
            "language": self.language,
            "subject": self.subject.value,
            "exam_types": [et.value for et in self.exam_types],
            "grade_levels": self.grade_levels,
            "topics": self.topics,
            "subtopics": self.subtopics,
            "difficulty_level": self.difficulty_level.value,
            "learning_objectives": [lo.value for lo in self.learning_objectives],
            "prerequisites": self.prerequisites,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "interaction_required": self.interaction_required,
            "accessibility_features": self.accessibility_features,
            "curriculum_code": self.curriculum_code,
            "curriculum_outcome": self.curriculum_outcome,
            "bloom_taxonomy_level": self.bloom_taxonomy_level,
        }


@dataclass
class ContentFile:
    """File associated with content"""

    file_id: str
    filename: str
    file_path: str
    file_size: int
    mime_type: str

    # File properties
    checksum: str
    upload_date: datetime
    uploaded_by: int

    # Processing status
    processed: bool = False
    processing_status: str = "pending"
    processing_errors: list[str] = field(default_factory=list)

    # Media-specific properties (for videos, images, etc.)
    width: int | None = None
    height: int | None = None
    duration_seconds: float | None = None
    bitrate: int | None = None
    format_info: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.file_id:
            self.file_id = str(uuid.uuid4())
        if not self.checksum:
            self.checksum = self._calculate_checksum()

    def _calculate_checksum(self) -> str:
        """Calculate file checksum"""
        if Path(self.file_path).exists():
            with open(self.file_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        return ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "file_id": self.file_id,
            "filename": self.filename,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "checksum": self.checksum,
            "upload_date": self.upload_date.isoformat(),
            "uploaded_by": self.uploaded_by,
            "processed": self.processed,
            "processing_status": self.processing_status,
            "width": self.width,
            "height": self.height,
            "duration_seconds": self.duration_seconds,
            "format_info": self.format_info,
        }


@dataclass
class ContentItem:
    """Main content item in the system"""

    # Core identification
    content_id: str
    content_type: ContentType
    metadata: ContentMetadata

    # Content data
    content_data: dict[str, Any] = field(default_factory=dict)
    files: list[ContentFile] = field(default_factory=list)

    # Lifecycle management
    status: ContentStatus = ContentStatus.DRAFT
    version: str = "1.0"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Authorship and ownership
    created_by: int = 0
    last_modified_by: int = 0
    owner_id: int = 0
    collaborators: list[int] = field(default_factory=list)

    # Publishing and access
    published_at: datetime | None = None
    published_by: int | None = None
    access_level: str = "public"  # public, private, school, premium

    # Analytics
    view_count: int = 0
    engagement_score: float = 0.0
    rating: float = 0.0
    rating_count: int = 0

    # Relationships
    parent_content_id: str | None = None  # For content hierarchies
    child_content_ids: list[str] = field(default_factory=list)
    related_content_ids: list[str] = field(default_factory=list)

    # Turkish localization
    title_tr: str | None = None
    description_tr: str | None = None

    def __post_init__(self):
        if not self.content_id:
            self.content_id = str(uuid.uuid4())
        if not self.title_tr:
            self.title_tr = self.metadata.title
        if not self.description_tr:
            self.description_tr = self.metadata.description

    def update_status(self, new_status: ContentStatus, user_id: int) -> None:
        """Update content status"""
        self.status = new_status
        self.last_modified_by = user_id
        self.updated_at = datetime.now(UTC)

        if new_status == ContentStatus.PUBLISHED:
            self.published_at = datetime.now(UTC)
            self.published_by = user_id

        logger.info(
            f"Content {self.content_id} status updated to {new_status.value} by user {user_id}"
        )

    def add_file(self, content_file: ContentFile) -> None:
        """Add file to content"""
        self.files.append(content_file)
        self.updated_at = datetime.now(UTC)
        logger.info(f"File {content_file.file_id} added to content {self.content_id}")

    def remove_file(self, file_id: str) -> bool:
        """Remove file from content"""
        for i, file in enumerate(self.files):
            if file.file_id == file_id:
                removed_file = self.files.pop(i)
                self.updated_at = datetime.now(UTC)
                logger.info(f"File {file_id} removed from content {self.content_id}")
                return True
        return False

    def get_primary_file(self) -> ContentFile | None:
        """Get primary file for content"""
        if not self.files:
            return None

        # For most content types, first file is primary
        primary_file = self.files[0]

        # For specific content types, look for specific file types
        if self.content_type == ContentType.VIDEO:
            video_files = [f for f in self.files if f.mime_type.startswith("video/")]
            if video_files:
                primary_file = video_files[0]
        elif self.content_type == ContentType.DOCUMENT:
            doc_files = [
                f for f in self.files if f.mime_type.startswith("application/")
            ]
            if doc_files:
                primary_file = doc_files[0]

        return primary_file

    def calculate_engagement_score(self) -> float:
        """Calculate engagement score based on various metrics"""
        # Base score from view count (normalized)
        view_score = min(self.view_count / 1000, 1.0) * 30

        # Rating contribution
        rating_score = self.rating / 5.0 * 40 if self.rating_count > 0 else 0

        # Recency bonus (newer content gets slight boost)
        days_since_creation = (datetime.now(UTC) - self.created_at).days
        recency_score = max(0, 30 - days_since_creation) / 30 * 20

        # Duration appropriateness (content with appropriate duration gets bonus)
        duration_score = 10
        if self.metadata.estimated_duration_minutes > 0:
            if 5 <= self.metadata.estimated_duration_minutes <= 30:
                duration_score = 20
            elif self.metadata.estimated_duration_minutes > 60:
                duration_score = 5

        total_score = view_score + rating_score + recency_score + duration_score
        self.engagement_score = min(100, total_score)
        return self.engagement_score

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "content_id": self.content_id,
            "content_type": self.content_type.value,
            "metadata": self.metadata.to_dict(),
            "content_data": self.content_data,
            "files": [f.to_dict() for f in self.files],
            "status": self.status.value,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "last_modified_by": self.last_modified_by,
            "owner_id": self.owner_id,
            "collaborators": self.collaborators,
            "published_at": self.published_at.isoformat()
            if self.published_at
            else None,
            "published_by": self.published_by,
            "access_level": self.access_level,
            "view_count": self.view_count,
            "engagement_score": self.engagement_score,
            "rating": self.rating,
            "rating_count": self.rating_count,
            "parent_content_id": self.parent_content_id,
            "child_content_ids": self.child_content_ids,
            "related_content_ids": self.related_content_ids,
            "title_tr": self.title_tr,
            "description_tr": self.description_tr,
        }


@dataclass
class ContentCollection:
    """Collection of related content items"""

    collection_id: str
    name: str
    description: str

    # Collection properties
    content_ids: list[str] = field(default_factory=list)
    collection_type: str = "manual"  # manual, auto_generated, curated

    # Educational context
    subject: TurkishSubject | None = None
    exam_types: list[TurkishExamType] = field(default_factory=list)
    difficulty_progression: bool = True  # Whether content is ordered by difficulty

    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    created_by: int = 0
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Access control
    access_level: str = "public"
    owner_id: int = 0

    # Turkish localization
    name_tr: str | None = None
    description_tr: str | None = None

    def __post_init__(self):
        if not self.collection_id:
            self.collection_id = str(uuid.uuid4())
        if not self.name_tr:
            self.name_tr = self.name
        if not self.description_tr:
            self.description_tr = self.description

    def add_content(self, content_id: str) -> None:
        """Add content to collection"""
        if content_id not in self.content_ids:
            self.content_ids.append(content_id)
            self.updated_at = datetime.now(UTC)

    def remove_content(self, content_id: str) -> bool:
        """Remove content from collection"""
        if content_id in self.content_ids:
            self.content_ids.remove(content_id)
            self.updated_at = datetime.now(UTC)
            return True
        return False

    def reorder_content(self, new_order: list[str]) -> bool:
        """Reorder content in collection"""
        if set(new_order) == set(self.content_ids):
            self.content_ids = new_order
            self.updated_at = datetime.now(UTC)
            return True
        return False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "collection_id": self.collection_id,
            "name": self.name,
            "description": self.description,
            "name_tr": self.name_tr,
            "description_tr": self.description_tr,
            "content_ids": self.content_ids,
            "collection_type": self.collection_type,
            "subject": self.subject.value if self.subject else None,
            "exam_types": [et.value for et in self.exam_types],
            "difficulty_progression": self.difficulty_progression,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "updated_at": self.updated_at.isoformat(),
            "access_level": self.access_level,
            "owner_id": self.owner_id,
        }


class ContentRepository:
    """Repository for content storage and retrieval"""

    def __init__(self):
        self.content_items: dict[str, ContentItem] = {}
        self.collections: dict[str, ContentCollection] = {}
        self.content_index: dict[str, set[str]] = {
            "subject": {},
            "exam_type": {},
            "difficulty": {},
            "content_type": {},
            "status": {},
        }

        # Caching
        self.search_cache: dict[str, list[str]] = {}
        self.cache_ttl = config.get_setting("content.cache_ttl", 3600)

    async def store_content(self, content: ContentItem) -> str:
        """Store content item"""
        self.content_items[content.content_id] = content
        self._update_content_index(content)

        # Invalidate relevant search cache
        self._invalidate_search_cache()

        logger.info(f"Stored content {content.content_id}: {content.metadata.title}")
        return content.content_id

    async def get_content(self, content_id: str) -> ContentItem | None:
        """Retrieve content by ID"""
        content = self.content_items.get(content_id)
        if content:
            # Increment view count
            content.view_count += 1
            content.updated_at = datetime.now(UTC)
        return content

    async def search_content(
        self,
        query: str | None = None,
        subject: TurkishSubject | None = None,
        exam_types: list[TurkishExamType] | None = None,
        difficulty_level: DifficultyLevel | None = None,
        content_type: ContentType | None = None,
        status: ContentStatus | None = None,
        grade_levels: list[int] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ContentItem]:
        """Search content with various filters"""

        # Create cache key
        cache_key = hashlib.md5(
            json.dumps(
                {
                    "query": query,
                    "subject": subject.value if subject else None,
                    "exam_types": [et.value for et in exam_types]
                    if exam_types
                    else None,
                    "difficulty_level": difficulty_level.value
                    if difficulty_level
                    else None,
                    "content_type": content_type.value if content_type else None,
                    "status": status.value if status else None,
                    "grade_levels": grade_levels,
                    "limit": limit,
                    "offset": offset,
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()

        # Check cache
        if cache_key in self.search_cache:
            content_ids = self.search_cache[cache_key]
            return [
                self.content_items[cid]
                for cid in content_ids
                if cid in self.content_items
            ]

        # Filter content
        filtered_content = list(self.content_items.values())

        # Apply filters
        if subject:
            filtered_content = [
                c for c in filtered_content if c.metadata.subject == subject
            ]

        if exam_types:
            filtered_content = [
                c
                for c in filtered_content
                if any(et in c.metadata.exam_types for et in exam_types)
            ]

        if difficulty_level:
            filtered_content = [
                c
                for c in filtered_content
                if c.metadata.difficulty_level == difficulty_level
            ]

        if content_type:
            filtered_content = [
                c for c in filtered_content if c.content_type == content_type
            ]

        if status:
            filtered_content = [c for c in filtered_content if c.status == status]

        if grade_levels:
            filtered_content = [
                c
                for c in filtered_content
                if any(gl in c.metadata.grade_levels for gl in grade_levels)
            ]

        # Text search in title and description
        if query:
            query_lower = query.lower()
            filtered_content = [
                c
                for c in filtered_content
                if query_lower in c.metadata.title.lower()
                or query_lower in c.metadata.description.lower()
                or any(
                    keyword.lower().startswith(query_lower)
                    for keyword in c.metadata.keywords
                )
            ]

        # Sort by engagement score and recency
        filtered_content.sort(
            key=lambda c: (c.calculate_engagement_score(), c.updated_at), reverse=True
        )

        # Apply pagination
        paginated_content = filtered_content[offset : offset + limit]

        # Cache results
        content_ids = [c.content_id for c in paginated_content]
        self.search_cache[cache_key] = content_ids

        return paginated_content

    async def get_related_content(
        self, content_id: str, limit: int = 5
    ) -> list[ContentItem]:
        """Get content related to the given content"""
        content = await self.get_content(content_id)
        if not content:
            return []

        # Find content with similar attributes
        related_content = await self.search_content(
            subject=content.metadata.subject,
            exam_types=content.metadata.exam_types,
            difficulty_level=content.metadata.difficulty_level,
            limit=limit * 2,  # Get more to filter out the original
        )

        # Remove the original content and limit results
        related_content = [c for c in related_content if c.content_id != content_id]
        return related_content[:limit]

    async def get_content_by_collection(self, collection_id: str) -> list[ContentItem]:
        """Get all content in a collection"""
        collection = self.collections.get(collection_id)
        if not collection:
            return []

        content_list = []
        for content_id in collection.content_ids:
            if content_id in self.content_items:
                content_list.append(self.content_items[content_id])

        return content_list

    async def create_collection(self, collection: ContentCollection) -> str:
        """Create a new content collection"""
        self.collections[collection.collection_id] = collection
        logger.info(f"Created collection {collection.collection_id}: {collection.name}")
        return collection.collection_id

    async def update_content_rating(self, content_id: str, rating: float) -> bool:
        """Update content rating"""
        content = self.content_items.get(content_id)
        if not content:
            return False

        # Simple running average (in production, would use more sophisticated method)
        total_rating = content.rating * content.rating_count + rating
        content.rating_count += 1
        content.rating = total_rating / content.rating_count
        content.updated_at = datetime.now(UTC)

        return True

    def _update_content_index(self, content: ContentItem) -> None:
        """Update search index for content"""
        content_id = content.content_id

        # Index by subject
        subject_key = content.metadata.subject.value
        if subject_key not in self.content_index["subject"]:
            self.content_index["subject"][subject_key] = set()
        self.content_index["subject"][subject_key].add(content_id)

        # Index by exam types
        for exam_type in content.metadata.exam_types:
            exam_key = exam_type.value
            if exam_key not in self.content_index["exam_type"]:
                self.content_index["exam_type"][exam_key] = set()
            self.content_index["exam_type"][exam_key].add(content_id)

        # Index by difficulty
        difficulty_key = content.metadata.difficulty_level.value
        if difficulty_key not in self.content_index["difficulty"]:
            self.content_index["difficulty"][difficulty_key] = set()
        self.content_index["difficulty"][difficulty_key].add(content_id)

        # Index by content type
        type_key = content.content_type.value
        if type_key not in self.content_index["content_type"]:
            self.content_index["content_type"][type_key] = set()
        self.content_index["content_type"][type_key].add(content_id)

        # Index by status
        status_key = content.status.value
        if status_key not in self.content_index["status"]:
            self.content_index["status"][status_key] = set()
        self.content_index["status"][status_key].add(content_id)

    def _invalidate_search_cache(self) -> None:
        """Invalidate search cache"""
        self.search_cache.clear()

    def get_content_statistics(self) -> dict[str, Any]:
        """Get repository statistics"""
        total_content = len(self.content_items)
        status_counts = {}
        type_counts = {}
        subject_counts = {}

        for content in self.content_items.values():
            # Count by status
            status = content.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

            # Count by type
            content_type = content.content_type.value
            type_counts[content_type] = type_counts.get(content_type, 0) + 1

            # Count by subject
            subject = content.metadata.subject.value
            subject_counts[subject] = subject_counts.get(subject, 0) + 1

        return {
            "total_content": total_content,
            "total_collections": len(self.collections),
            "status_distribution": status_counts,
            "type_distribution": type_counts,
            "subject_distribution": subject_counts,
            "cache_size": len(self.search_cache),
        }


class ContentManager:
    """High-level content management operations"""

    def __init__(self, repository: ContentRepository):
        self.repository = repository
        self.content_validators = self._initialize_validators()

    def _initialize_validators(self) -> dict[ContentType, Callable]:
        """Initialize content type validators"""
        return {
            ContentType.QUESTION: self._validate_question_content,
            ContentType.VIDEO: self._validate_video_content,
            ContentType.DOCUMENT: self._validate_document_content,
            ContentType.QUIZ: self._validate_quiz_content,
            ContentType.INTERACTIVE: self._validate_interactive_content,
        }

    async def create_content(
        self,
        content_type: ContentType,
        metadata: ContentMetadata,
        content_data: dict[str, Any],
        files: list[ContentFile] = None,
        created_by: int = 0,
    ) -> ContentItem:
        """Create new content item"""

        # Validate content data
        validation_errors = await self._validate_content(
            content_type, content_data, files or []
        )
        if validation_errors:
            raise ValueError(
                f"Content validation failed: {', '.join(validation_errors)}"
            )

        # Create content item
        content = ContentItem(
            content_id=str(uuid.uuid4()),
            content_type=content_type,
            metadata=metadata,
            content_data=content_data,
            files=files or [],
            created_by=created_by,
            owner_id=created_by,
            last_modified_by=created_by,
        )

        # Store in repository
        await self.repository.store_content(content)

        logger.info(f"Created {content_type.value} content: {metadata.title}")
        return content

    async def _validate_content(
        self,
        content_type: ContentType,
        content_data: dict[str, Any],
        files: list[ContentFile],
    ) -> list[str]:
        """Validate content data based on type"""
        errors = []

        # Get type-specific validator
        validator = self.content_validators.get(content_type)
        if validator:
            type_errors = await validator(content_data, files)
            errors.extend(type_errors)

        return errors

    async def _validate_question_content(
        self, content_data: dict[str, Any], files: list[ContentFile]
    ) -> list[str]:
        """Validate question content"""
        errors = []

        # Required fields for questions
        required_fields = ["question_text", "options", "correct_answer"]
        for field in required_fields:
            if field not in content_data:
                errors.append(f"Missing required field: {field}")

        # Validate options structure
        if "options" in content_data:
            options = content_data["options"]
            if not isinstance(options, list) or len(options) < 2:
                errors.append("Question must have at least 2 options")

            # For Turkish exams, typically 5 options
            if len(options) != 5:
                errors.append("Turkish exam questions should have exactly 5 options")

        # Validate correct answer
        if "correct_answer" in content_data and "options" in content_data:
            correct_answer = content_data["correct_answer"]
            options = content_data["options"]
            if correct_answer not in ["A", "B", "C", "D", "E"]:
                errors.append("Correct answer must be A, B, C, D, or E")

            option_index = ord(correct_answer) - ord("A")
            if option_index >= len(options):
                errors.append("Correct answer index exceeds available options")

        return errors

    async def _validate_video_content(
        self, content_data: dict[str, Any], files: list[ContentFile]
    ) -> list[str]:
        """Validate video content"""
        errors = []

        # Must have at least one video file
        video_files = [f for f in files if f.mime_type.startswith("video/")]
        if not video_files:
            errors.append("Video content must have at least one video file")

        # Check for required metadata
        required_fields = ["title", "description"]
        for field in required_fields:
            if field not in content_data or not content_data[field]:
                errors.append(f"Missing required field: {field}")

        return errors

    async def _validate_document_content(
        self, content_data: dict[str, Any], files: list[ContentFile]
    ) -> list[str]:
        """Validate document content"""
        errors = []

        # Must have at least one document file
        doc_files = [f for f in files if f.mime_type.startswith("application/")]
        if not doc_files:
            errors.append("Document content must have at least one document file")

        return errors

    async def _validate_quiz_content(
        self, content_data: dict[str, Any], files: list[ContentFile]
    ) -> list[str]:
        """Validate quiz content"""
        errors = []

        # Must have questions
        if "questions" not in content_data or not content_data["questions"]:
            errors.append("Quiz must have at least one question")

        # Validate each question
        questions = content_data.get("questions", [])
        for i, question in enumerate(questions):
            question_errors = await self._validate_question_content(question, [])
            for error in question_errors:
                errors.append(f"Question {i+1}: {error}")

        return errors

    async def _validate_interactive_content(
        self, content_data: dict[str, Any], files: list[ContentFile]
    ) -> list[str]:
        """Validate interactive content"""
        errors = []

        # Interactive content should have interaction definition
        if "interaction_type" not in content_data:
            errors.append("Interactive content must specify interaction_type")

        if "parameters" not in content_data:
            errors.append("Interactive content must have parameters")

        return errors

    async def update_content(
        self, content_id: str, updates: dict[str, Any], updated_by: int
    ) -> ContentItem | None:
        """Update existing content"""
        content = await self.repository.get_content(content_id)
        if not content:
            return None

        # Apply updates
        for key, value in updates.items():
            if hasattr(content, key):
                setattr(content, key, value)
            elif key in ["title", "description", "keywords"] and hasattr(
                content.metadata, key
            ):
                setattr(content.metadata, key, value)
            else:
                content.content_data[key] = value

        content.last_modified_by = updated_by
        content.updated_at = datetime.now(UTC)

        # Re-validate if content_data changed
        if any(k in content.content_data for k in updates):
            validation_errors = await self._validate_content(
                content.content_type, content.content_data, content.files
            )
            if validation_errors:
                raise ValueError(
                    f"Update validation failed: {', '.join(validation_errors)}"
                )

        # Update in repository
        await self.repository.store_content(content)

        logger.info(f"Updated content {content_id} by user {updated_by}")
        return content

    async def publish_content(self, content_id: str, published_by: int) -> bool:
        """Publish content (make it available to students)"""
        content = await self.repository.get_content(content_id)
        if not content:
            return False

        # Validate content is ready for publishing
        if content.status not in [ContentStatus.APPROVED, ContentStatus.DRAFT]:
            logger.warning(
                f"Cannot publish content {content_id} with status {content.status.value}"
            )
            return False

        # Update status to published
        content.update_status(ContentStatus.PUBLISHED, published_by)
        await self.repository.store_content(content)

        logger.info(f"Published content {content_id}: {content.metadata.title}")
        return True

    async def archive_content(self, content_id: str, archived_by: int) -> bool:
        """Archive content (remove from active use)"""
        content = await self.repository.get_content(content_id)
        if not content:
            return False

        content.update_status(ContentStatus.ARCHIVED, archived_by)
        await self.repository.store_content(content)

        logger.info(f"Archived content {content_id}: {content.metadata.title}")
        return True

    async def get_content_analytics(self, content_id: str) -> dict[str, Any]:
        """Get analytics for specific content"""
        content = await self.repository.get_content(content_id)
        if not content:
            return {}

        return {
            "content_id": content_id,
            "view_count": content.view_count,
            "engagement_score": content.calculate_engagement_score(),
            "rating": content.rating,
            "rating_count": content.rating_count,
            "days_since_creation": (
                datetime.now(UTC) - content.created_at
            ).days,
            "days_since_published": (
                (datetime.now(UTC) - content.published_at).days
                if content.published_at
                else None
            ),
            "status": content.status.value,
            "content_type": content.content_type.value,
            "subject": content.metadata.subject.value,
            "difficulty_level": content.metadata.difficulty_level.value,
        }


if __name__ == "__main__":
    # Example usage and testing
    print("KIRO2 Unified Content Management System")
    print("=" * 45)

    async def test_content_system():
        """Test content management system"""
        repository = ContentRepository()
        manager = ContentManager(repository)

        # Create sample metadata
        metadata = ContentMetadata(
            title="Türev Alma Kuralları",
            description="Temel türev alma kurallarını öğrenin",
            keywords=["türev", "matematik", "kalkülüs"],
            subject=TurkishSubject.MATEMATIK,
            exam_types=[TurkishExamType.TYT, TurkishExamType.AYT],
            grade_levels=[11, 12],
            topics=["Kalkülüs", "Türev"],
            subtopics=["Türev Alma Kuralları"],
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            learning_objectives=[
                LearningObjective.COMPREHENSION,
                LearningObjective.APPLICATION,
            ],
            estimated_duration_minutes=25,
        )

        # Create sample question content
        question_data = {
            "question_text": "f(x) = x² + 3x - 2 fonksiyonunun türevi nedir?",
            "options": ["2x + 3", "x² + 3", "2x - 2", "x + 3", "3x - 2"],
            "correct_answer": "A",
            "solution": "f'(x) = 2x + 3 (kuvvet kuralı ve toplam kuralı)",
            "explanation": "Polinom fonksiyonların türevi alınırken kuvvet kuralı uygulanır.",
        }

        # Create content
        content = await manager.create_content(
            content_type=ContentType.QUESTION,
            metadata=metadata,
            content_data=question_data,
            created_by=1001,
        )

        print(f"Created content: {content.content_id}")
        print(f"Title: {content.metadata.title}")
        print(f"Status: {content.status.value}")

        # Publish content
        await manager.publish_content(content.content_id, 1001)
        print("Content published")

        # Search content
        math_content = await repository.search_content(
            subject=TurkishSubject.MATEMATIK, exam_types=[TurkishExamType.TYT], limit=10
        )
        print(f"Found {len(math_content)} math content items")

        # Get statistics
        stats = repository.get_content_statistics()
        print(f"Repository statistics: {stats}")

        # Create content collection
        collection = ContentCollection(
            collection_id=str(uuid.uuid4()),
            name="Türev Konuları",
            description="Türev konusuyla ilgili tüm materyaller",
            subject=TurkishSubject.MATEMATIK,
            exam_types=[TurkishExamType.AYT],
            content_ids=[content.content_id],
        )

        await repository.create_collection(collection)
        print(f"Created collection: {collection.name}")

        # Get content analytics
        analytics = await manager.get_content_analytics(content.content_id)
        print(f"Content analytics: {analytics}")

    # Run test
    asyncio.run(test_content_system())
