"""
EBA TV Integration Service
Türkiye Eğitim Bakanlığı EBA TV servisleri entegrasyonu
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class EBAContentCategory(Enum):
    MATEMATIK = "matematik"
    TURKCE = "turkce"
    FEN = "fen"
    SOSYAL = "sosyal"
    INGILIZCE = "ingilizce"


class EBAGradeLevel(Enum):
    GRADE_5 = "5"
    GRADE_6 = "6"
    GRADE_7 = "7"
    GRADE_8 = "8"


@dataclass
class EBAVideoMetadata:
    """EBA Video metadata structure"""
    title: str
    category: EBAContentCategory
    grade_level: EBAGradeLevel
    duration: int
    description: str = ""
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class EBAContentCollection:
    """EBA Content collection structure"""
    videos: List[EBAVideoMetadata]
    total_count: int
    categories: Dict[EBAContentCategory, int]
    grade_levels: Dict[EBAGradeLevel, int]
    quality_distribution: Dict[str, int]
    last_updated: Any
    
    def __post_init__(self):
        if self.total_count is None:
            self.total_count = len(self.videos)


class EBAContentQualityAnalyzer:
    """EBA Content quality analyzer"""
    
    def __init__(self):
        """Initialize quality analyzer with criteria"""
        self.quality_criteria = {
            "video_duration": 1.0,
            "title_clarity": 1.0,
            "curriculum_keywords": 1.0,
            "description_quality": 1.0,
            "accessibility_features": 0.8
        }
    
    async def analyze_video_quality(self, video: EBAVideoMetadata) -> float:
        """Analyze video quality metrics"""
        score = 0.0
        score += self._evaluate_duration(video.duration)
        score += self._evaluate_title_clarity(video.title)
        score += self._evaluate_description(video.description)
        score += self._evaluate_curriculum_alignment(video)
        score += self._evaluate_accessibility(getattr(video, 'accessibility_features', []))
        return min(score * 2, 10.0)  # Scale to 0-10
    
    def _evaluate_duration(self, duration: int) -> float:
        """Evaluate video duration"""
        if 10 <= duration <= 20:
            return 1.0  # Optimal
        elif 5 <= duration <= 30:
            return 0.8  # Good
        elif duration < 5:
            return 0.3  # Too short
        else:
            return 0.5  # Too long
    
    def _evaluate_title_clarity(self, title: str) -> float:
        """Evaluate title clarity"""
        if len(title) >= 20:
            return 1.0  # Clear and descriptive
        elif len(title) >= 10:
            return 0.7  # Adequate
        else:
            return 0.4  # Too short
    
    def _evaluate_description(self, description: str) -> float:
        """Evaluate description quality"""
        if len(description) >= 50:
            return 1.0  # Detailed
        elif len(description) >= 20:
            return 0.6  # Basic
        elif len(description) > 0:
            return 0.3  # Minimal
        else:
            return 0.0  # Empty
    
    def _evaluate_curriculum_alignment(self, video: EBAVideoMetadata) -> float:
        """Evaluate curriculum alignment"""
        keywords = ["kazanım", "öğrenme", "hedef", "amaç", "ders"]
        description_lower = video.description.lower()
        matches = sum(1 for keyword in keywords if keyword in description_lower)
        return min(matches * 0.2, 1.0)
    
    def _evaluate_accessibility(self, features: List[str]) -> float:
        """Evaluate accessibility features"""
        if not features:
            return 0.2  # Basic accessibility
        
        feature_scores = {
            "altyazi": 0.3,
            "transkript": 0.3,
            "sesli_betimleme": 0.2
        }
        
        total_score = 0.2  # Base score
        for feature in features:
            total_score += feature_scores.get(feature, 0)
        
        return min(total_score, 1.0)
    
    def evaluate_curriculum_alignment(self, video: EBAVideoMetadata) -> float:
        """Evaluate curriculum alignment score"""
        return self._evaluate_curriculum_alignment(video)


class EBACurriculumMatcher:
    """EBA Curriculum matcher"""
    
    def __init__(self):
        """Initialize curriculum matcher"""
        self.curriculum_topics = {
            EBAGradeLevel.GRADE_8: {
                EBAContentCategory.MATEMATIK: [
                    "Çarpanlar ve Katlar",
                    "Üslü İfadeler",
                    "Kareköklü İfadeler",
                    "Veri Analizi"
                ]
            }
        }
    
    async def match_content_to_curriculum(self, video: EBAVideoMetadata) -> Dict[str, Any]:
        """Match content to curriculum"""
        grade_topics = self.curriculum_topics.get(video.grade_level, {})
        category_topics = grade_topics.get(video.category, [])
        
        if not category_topics:
            return {
                "alignment_score": 0.0,
                "matched_topics": [],
                "suggestions": []
            }
        
        # Simple text matching for topics
        title_lower = video.title.lower()
        desc_lower = video.description.lower()
        
        matched_topics = []
        for topic in category_topics:
            topic_words = topic.lower().split()
            if any(word in title_lower or word in desc_lower for word in topic_words):
                matched_topics.append(topic)
        
        alignment_score = len(matched_topics) / len(category_topics) if category_topics else 0.0
        
        return {
            "alignment_score": alignment_score,
            "matched_topics": matched_topics,
            "suggestions": ["Improve topic matching"] if alignment_score < 0.5 else []
        }


class EBAContentCollector:
    """EBA Content collector"""
    
    def __init__(self):
        """Initialize content collector"""
        self.session = None
        self.quality_analyzer = EBAContentQualityAnalyzer()
        self.curriculum_matcher = EBACurriculumMatcher()
        self.manual_video_links = []
    
    async def __aenter__(self):
        """Async context manager entry"""
        # Create a mock session for testing
        if not self.session:
            from unittest.mock import MagicMock
            self.session = MagicMock()
            self.session.close = lambda: None
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session and hasattr(self.session, 'close'):
            if asyncio.iscoroutinefunction(self.session.close):
                await self.session.close()
            else:
                self.session.close()
    
    async def collect_content_by_category(self, grade: EBAGradeLevel, category: EBAContentCategory) -> List[EBAVideoMetadata]:
        """Collect content by category"""
        # Mock implementation - return sample videos
        videos = []
        sample_video = EBAVideoMetadata(
            title=f"{category.value.title()} Sample Video",
            category=category,
            grade_level=grade,
            duration=15,
            description=f"Sample {category.value} video for grade {grade.value}",
            tags=[category.value, f"grade_{grade.value}"]
        )
        
        # Add quality score and curriculum alignment
        sample_video.quality_score = await self.quality_analyzer.analyze_video_quality(sample_video)
        curriculum_result = await self.curriculum_matcher.match_content_to_curriculum(sample_video)
        sample_video.curriculum_alignment = curriculum_result["alignment_score"]
        
        videos.append(sample_video)
        return videos
    
    async def collect_all_content(self) -> EBAContentCollection:
        """Collect all content"""
        all_videos = []
        categories = {}
        grade_levels = {}
        
        for grade in EBAGradeLevel:
            for category in EBAContentCategory:
                videos = await self.collect_content_by_category(grade, category)
                all_videos.extend(videos)
                
                # Count by category and grade
                categories[category] = categories.get(category, 0) + len(videos)
                grade_levels[grade] = grade_levels.get(grade, 0) + len(videos)
        
        # Quality distribution
        quality_distribution = {"high": 0, "medium": 0, "low": 0}
        for video in all_videos:
            score = getattr(video, 'quality_score', 7.5)
            if score >= 8.0:
                quality_distribution["high"] += 1
            elif score >= 6.0:
                quality_distribution["medium"] += 1
            else:
                quality_distribution["low"] += 1
        
        return EBAContentCollection(
            videos=all_videos,
            total_count=len(all_videos),
            categories=categories,
            grade_levels=grade_levels,
            quality_distribution=quality_distribution,
            last_updated=datetime.now()
        )
    
    def _estimate_difficulty(self, grade: EBAGradeLevel, duration: int):
        """Estimate content difficulty"""
        from backend.models.enums import ZorlukSeviyesi
        
        base_difficulty = {
            EBAGradeLevel.GRADE_5: ZorlukSeviyesi.KOLAY,
            EBAGradeLevel.GRADE_6: ZorlukSeviyesi.KOLAY,
            EBAGradeLevel.GRADE_7: ZorlukSeviyesi.ORTA,
            EBAGradeLevel.GRADE_8: ZorlukSeviyesi.ZOR
        }
        
        difficulty = base_difficulty.get(grade, ZorlukSeviyesi.ORTA)
        
        # Long videos are typically more complex
        if duration > 30:
            if difficulty == ZorlukSeviyesi.KOLAY:
                difficulty = ZorlukSeviyesi.ORTA
            elif difficulty == ZorlukSeviyesi.ORTA:
                difficulty = ZorlukSeviyesi.ZOR
        
        return difficulty
    
    async def _create_video_metadata(self, video_data: Dict, grade: EBAGradeLevel, category: EBAContentCategory) -> EBAVideoMetadata:
        """Create video metadata from data"""
        metadata = EBAVideoMetadata(
            title=video_data["title"],
            category=category,
            grade_level=grade,
            duration=video_data["duration"],
            description=video_data["description"]
        )
        
        # Add subject topics and accessibility features
        if "topics" in video_data:
            metadata.subject_topics = video_data["topics"]
        metadata.accessibility_features = ["altyazi"]  # Basic subtitle support
        
        return metadata


class EBAtvService:
    """Main EBA TV service"""
    
    def __init__(self):
        """Initialize service"""
        self.content_collector = EBAContentCollector()
        self.quality_analyzer = EBAContentQualityAnalyzer()
        self.curriculum_matcher = EBACurriculumMatcher()
        self._content_cache = None
        self._cache_expiry = None
    
    async def get_all_content(self, force_refresh: bool = False) -> EBAContentCollection:
        """Get all content with caching"""
        if not force_refresh and self._content_cache and self._cache_expiry and datetime.now() < self._cache_expiry:
            return self._content_cache
        
        async with self.content_collector:
            collection = await self.content_collector.collect_all_content()
            self._content_cache = collection
            from datetime import timedelta
            self._cache_expiry = datetime.now() + timedelta(hours=1)  # 1 hour cache
            return collection
    
    async def search_content(self, query: str, grade_level: Optional[EBAGradeLevel] = None, 
                           category: Optional[EBAContentCategory] = None, min_quality: float = 0.0) -> List[EBAVideoMetadata]:
        """Search content with filters"""
        collection = await self.get_all_content()
        results = []
        
        for video in collection.videos:
            # Text search
            if query.lower() not in video.title.lower() and query.lower() not in video.description.lower():
                continue
            
            # Grade filter
            if grade_level and video.grade_level != grade_level:
                continue
                
            # Category filter
            if category and video.category != category:
                continue
                
            # Quality filter
            if hasattr(video, 'quality_score') and video.quality_score < min_quality:
                continue
            
            results.append(video)
        
        return results
    
    async def get_content_by_curriculum_topic(self, grade: EBAGradeLevel, category: EBAContentCategory, topic: str) -> List[EBAVideoMetadata]:
        """Get content by curriculum topic"""
        collection = await self.get_all_content()
        results = []
        
        for video in collection.videos:
            if video.grade_level != grade or video.category != category:
                continue
                
            # Check if topic matches
            if hasattr(video, 'subject_topics') and topic in video.subject_topics:
                results.append(video)
        
        return results
    
    async def get_recommended_content(self, student_grade: EBAGradeLevel, weak_subjects: List[EBAContentCategory], 
                                    learning_style: str) -> List[EBAVideoMetadata]:
        """Get recommended content based on student profile"""
        collection = await self.get_all_content()
        results = []
        
        for video in collection.videos:
            if video.grade_level != student_grade:
                continue
                
            if video.category not in weak_subjects:
                continue
                
            # Simple learning style matching
            if learning_style == "visual" or learning_style == "auditory":
                results.append(video)
        
        return results
    
    async def get_content_statistics(self) -> Dict[str, Any]:
        """Get content statistics"""
        collection = await self.get_all_content()
        
        return {
            "total_videos": collection.total_count,
            "categories": dict(collection.categories),
            "grade_levels": dict(collection.grade_levels),
            "quality_distribution": dict(collection.quality_distribution),
            "last_updated": collection.last_updated.isoformat() if collection.last_updated else None,
            "cache_status": "cached" if self._content_cache else "not_cached"
        }


# Global service instance
ebatv_service = EBAtvService()


async def get_ebatv_service() -> EBAtvService:
    """Get EBA TV service instance"""
    return ebatv_service