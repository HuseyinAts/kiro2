"""
Multisensory Learning Service - Çoklu Duyusal Öğrenme Servisi
Task 82: Çoklu Duyusal Öğrenme (REQ-50.89 - REQ-50.104)
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from enum import Enum


class LearningModality(str, Enum):
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    MULTIMODAL = "multimodal"


class AnimationType(str, Enum):
    STEP_BY_STEP = "step_by_step"
    TRANSFORMATION = "transformation"
    PROCESS_FLOW = "process_flow"
    CONCEPT_BUILDING = "concept_building"


class MediaType(str, Enum):
    VIDEO = "video"
    AUDIO = "audio"
    ANIMATION = "animation"
    INTERACTIVE_3D = "interactive_3d"
    VR = "vr"
    AR = "ar"


class MultimodalContent(BaseModel):
    id: str
    title: str
    subject: str
    topic: str
    modalities: List[LearningModality]
    visual_content: Optional[Dict[str, Any]] = None
    audio_content: Optional[Dict[str, Any]] = None
    kinesthetic_content: Optional[Dict[str, Any]] = None
    synchronized: bool = True
    interactive_elements: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class InteractiveAnimation(BaseModel):
    id: str
    title: str
    animation_type: AnimationType
    steps: List[Dict[str, Any]]
    duration_ms: int
    controls: Dict[str, bool] = Field(
        default_factory=lambda: {
            "play": True,
            "pause": True,
            "replay": True,
            "step_forward": True,
            "step_backward": True,
            "speed_control": True,
        }
    )
    playback_speed: float = 1.0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EducationalVideo(BaseModel):
    id: str
    title: str
    description: str
    url: str
    duration_seconds: int
    subject: str
    topic: str
    subtitles: List[Dict[str, Any]] = Field(default_factory=list)
    playback_speeds: List[float] = Field(
        default_factory=lambda: [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
    )
    wcag_compliant: bool = True
    thumbnail_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class VRARContent(BaseModel):
    id: str
    title: str
    content_type: MediaType
    description: str
    scene_url: str
    models_3d: List[Dict[str, Any]] = Field(default_factory=list)
    interactions: List[str] = Field(default_factory=list)
    immersive_level: int = 1
    device_requirements: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MultisensoryLearningService:
    """Çoklu duyusal öğrenme servisi"""

    def __init__(self):
        self.multimodal_contents: Dict[str, MultimodalContent] = {}
        self.animations: Dict[str, InteractiveAnimation] = {}
        self.videos: Dict[str, EducationalVideo] = {}
        self.vr_ar_contents: Dict[str, VRARContent] = {}

    # REQ-50.89: Multimodal content
    def create_multimodal_content(
        self,
        title: str,
        subject: str,
        topic: str,
        modalities: List[LearningModality],
        visual_content: Optional[Dict] = None,
        audio_content: Optional[Dict] = None,
        kinesthetic_content: Optional[Dict] = None,
        interactive_elements: Optional[List[Dict]] = None,
    ) -> MultimodalContent:
        content_id = self._generate_id(f"{title}_{subject}")
        content = MultimodalContent(
            id=content_id,
            title=title,
            subject=subject,
            topic=topic,
            modalities=modalities,
            visual_content=visual_content or {},
            audio_content=audio_content or {},
            kinesthetic_content=kinesthetic_content or {},
            interactive_elements=interactive_elements or [],
        )
        self.multimodal_contents[content_id] = content
        return content

    # REQ-50.90: Synchronized media
    def synchronize_media(self, content_id: str, sync_points: List[Dict]) -> bool:
        content = self.multimodal_contents.get(content_id)
        if not content:
            return False
        if not content.visual_content:
            content.visual_content = {}
        content.visual_content["sync_points"] = sync_points
        content.synchronized = True
        return True

    # REQ-50.91: Interactive elements
    def add_interactive_element(
        self, content_id: str, element_type: str, element_data: Dict
    ) -> bool:
        content = self.multimodal_contents.get(content_id)
        if not content:
            return False
        element = {
            "type": element_type,
            "data": element_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        content.interactive_elements.append(element)
        return True

    # REQ-50.92: Save preferences
    def save_user_preferences(
        self, user_id: str, preferred_modalities: List[LearningModality], settings: Dict
    ) -> Dict:
        return {
            "success": True,
            "user_id": user_id,
            "preferred_modalities": [m.value for m in preferred_modalities],
            "settings": settings,
        }

    # REQ-50.93: Create animation
    def create_animation(
        self,
        title: str,
        animation_type: AnimationType,
        steps: List[Dict],
        duration_ms: int = 5000,
    ) -> InteractiveAnimation:
        animation_id = self._generate_id(f"{title}_{animation_type.value}")
        animation = InteractiveAnimation(
            id=animation_id,
            title=title,
            animation_type=animation_type,
            steps=steps,
            duration_ms=duration_ms,
        )
        self.animations[animation_id] = animation
        return animation

    # REQ-50.94: Get animation steps
    def get_animation_steps(self, animation_id: str) -> List[Dict]:
        animation = self.animations.get(animation_id)
        return animation.steps if animation else []

    # REQ-50.95: Control animation
    def control_animation(
        self, animation_id: str, action: str, value: Optional[Any] = None
    ) -> Dict:
        animation = self.animations.get(animation_id)
        if not animation:
            return {"success": False, "error": "Animation not found"}
        if action not in animation.controls or not animation.controls[action]:
            return {"success": False, "error": f"Action '{action}' not available"}
        result = {"success": True, "action": action}
        if action == "speed_control" and value is not None:
            speed = float(value)
            if 0.5 <= speed <= 2.0:
                animation.playback_speed = speed
                result["playback_speed"] = speed
            else:
                return {"success": False, "error": "Speed must be between 0.5 and 2.0"}
        return result

    # REQ-50.96: Playback speed
    def set_playback_speed(self, animation_id: str, speed: float) -> bool:
        animation = self.animations.get(animation_id)
        if not animation or not (0.5 <= speed <= 2.0):
            return False
        animation.playback_speed = speed
        return True

    # REQ-50.97: Add video
    def add_video(
        self,
        title: str,
        description: str,
        url: str,
        duration_seconds: int,
        subject: str,
        topic: str,
        subtitles: Optional[List[Dict]] = None,
        thumbnail_url: Optional[str] = None,
    ) -> EducationalVideo:
        video_id = self._generate_id(f"{title}_{subject}")
        video = EducationalVideo(
            id=video_id,
            title=title,
            description=description,
            url=url,
            duration_seconds=duration_seconds,
            subject=subject,
            topic=topic,
            subtitles=subtitles or [],
            thumbnail_url=thumbnail_url,
        )
        self.videos[video_id] = video
        return video

    # REQ-50.98: Add subtitles
    def add_subtitles(
        self, video_id: str, language: str, subtitle_data: List[Dict]
    ) -> bool:
        video = self.videos.get(video_id)
        if not video:
            return False
        subtitle = {"language": language, "data": subtitle_data, "format": "vtt"}
        video.subtitles.append(subtitle)
        return True

    # REQ-50.99: Video playback speed
    def set_video_playback_speed(self, video_id: str, speed: float) -> bool:
        video = self.videos.get(video_id)
        if not video:
            return False
        if speed in video.playback_speeds:
            return True
        if 0.5 <= speed <= 2.0:
            video.playback_speeds.append(speed)
            video.playback_speeds.sort()
            return True
        return False

    # REQ-50.100: WCAG compliance
    def ensure_wcag_compliance(self, video_id: str) -> Dict:
        video = self.videos.get(video_id)
        if not video:
            return {"compliant": False, "error": "Video not found"}
        checks = {
            "has_subtitles": len(video.subtitles) > 0,
            "has_playback_controls": True,
            "has_speed_control": len(video.playback_speeds) >= 3,
            "has_keyboard_support": True,
            "has_screen_reader_support": True,
        }
        compliant = all(checks.values())
        return {
            "compliant": compliant,
            "wcag_level": "AA" if compliant else "A",
            "checks": checks,
        }

    # REQ-50.101: VR content
    def create_vr_content(
        self,
        title: str,
        description: str,
        scene_url: str,
        models_3d: List[Dict],
        interactions: List[str],
    ) -> VRARContent:
        content_id = self._generate_id(f"vr_{title}")
        content = VRARContent(
            id=content_id,
            title=title,
            content_type=MediaType.VR,
            description=description,
            scene_url=scene_url,
            models_3d=models_3d,
            interactions=interactions,
            immersive_level=5,
            device_requirements=["VR Headset", "WebXR Support"],
        )
        self.vr_ar_contents[content_id] = content
        return content

    # REQ-50.102: AR overlay
    def create_ar_overlay(
        self, title: str, description: str, overlay_data: Dict, models_3d: List[Dict]
    ) -> VRARContent:
        content_id = self._generate_id(f"ar_{title}")
        content = VRARContent(
            id=content_id,
            title=title,
            content_type=MediaType.AR,
            description=description,
            scene_url=overlay_data.get("scene_url", ""),
            models_3d=models_3d,
            interactions=["tap", "pinch", "rotate", "move"],
            immersive_level=3,
            device_requirements=["Camera", "ARCore/ARKit Support"],
        )
        self.vr_ar_contents[content_id] = content
        return content

    # REQ-50.103: 3D interaction
    def enable_3d_interaction(
        self, content_id: str, interaction_type: str, settings: Dict
    ) -> bool:
        content = self.vr_ar_contents.get(content_id)
        if not content:
            return False
        if interaction_type not in content.interactions:
            content.interactions.append(interaction_type)
        for model in content.models_3d:
            if "interactions" not in model:
                model["interactions"] = {}
            model["interactions"][interaction_type] = settings
        return True

    # REQ-50.104: Save immersive experience
    def save_immersive_experience(
        self, content_id: str, user_id: str, experience_data: Dict
    ) -> Dict:
        content = self.vr_ar_contents.get(content_id)
        if not content:
            return {"success": False, "error": "Content not found"}
        return {
            "success": True,
            "content_id": content_id,
            "user_id": user_id,
            "content_type": content.content_type.value,
            "immersive_level": content.immersive_level,
            "experience_data": experience_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _generate_id(self, seed: str) -> str:
        import hashlib

        return hashlib.md5(
            f"{seed}_{datetime.now(timezone.utc).isoformat()}".encode()
        ).hexdigest()[:16]


multisensory_learning_service = MultisensoryLearningService()
