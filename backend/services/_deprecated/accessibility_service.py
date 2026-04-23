"""
Unified Accessibility Service
FAZ 3.3: Accessibility Module Optimization
WCAG 2.1 AA/AAA Compliance for Turkish Educational Platform
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AccessibilityProfile(Enum):
    """Predefined accessibility profiles"""
    STANDARD = "standard"
    ADHD = "adhd"                    # DEHB - Dikkat Eksikliği
    DYSLEXIA = "dyslexia"            # Disleksi - Okuma Güçlüğü
    DYSCALCULIA = "dyscalculia"      # Diskalkuli - Matematik Güçlüğü
    VISUAL_IMPAIRMENT = "visual"     # Görme Engelli
    HEARING_IMPAIRMENT = "hearing"   # İşitme Engelli
    MOTOR_IMPAIRMENT = "motor"       # Motor Engelli
    COGNITIVE = "cognitive"          # Bilişsel Engel
    AUTISM = "autism"                # Otizm Spektrumu (OSB)
    LOW_VISION = "low_vision"        # Az Gören


class WCAGLevel(Enum):
    """WCAG compliance levels"""
    A = "A"
    AA = "AA"
    AAA = "AAA"


class ContentAdaptationType(Enum):
    """Types of content adaptations"""
    FONT_SIZE = "font_size"
    LINE_HEIGHT = "line_height"
    LETTER_SPACING = "letter_spacing"
    WORD_SPACING = "word_spacing"
    CONTRAST = "contrast"
    COLOR_SCHEME = "color_scheme"
    TEXT_TO_SPEECH = "text_to_speech"
    BIONIC_READING = "bionic_reading"
    SIMPLIFIED_TEXT = "simplified_text"
    MATH_VISUALIZATION = "math_visualization"
    FOCUS_MODE = "focus_mode"
    ANIMATION_CONTROL = "animation_control"
    READING_GUIDE = "reading_guide"
    TIME_EXTENSION = "time_extension"


@dataclass
class AccessibilitySettings:
    """User's accessibility settings"""
    user_id: int
    profile: AccessibilityProfile = AccessibilityProfile.STANDARD
    wcag_level: WCAGLevel = WCAGLevel.AA

    # Visual settings
    font_size_multiplier: float = 1.0
    font_family: str = "system-ui"
    line_height_multiplier: float = 1.5
    letter_spacing: float = 0.0
    word_spacing: float = 0.0
    high_contrast: bool = False
    color_scheme: str = "light"  # light, dark, sepia, high-contrast

    # Reading assistance
    text_to_speech_enabled: bool = False
    tts_rate: float = 1.0
    tts_voice: str = "tr-TR"
    bionic_reading_enabled: bool = False
    reading_guide_enabled: bool = False

    # Focus and attention
    focus_mode_enabled: bool = False
    reduce_motion: bool = False
    reduce_transparency: bool = False

    # Time and pacing
    extended_time_percentage: int = 0  # 0, 25, 50, 100
    auto_pause_enabled: bool = False
    break_reminder_interval: int = 30  # minutes

    # Math specific
    math_step_by_step: bool = False
    number_line_visualization: bool = False
    grid_paper_enabled: bool = False

    # Cognitive assistance
    simplified_language: bool = False
    predictable_layout: bool = True
    consistent_navigation: bool = True

    # Created/Updated
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class AccessibilityAuditResult:
    """WCAG audit result for content"""
    content_id: str
    wcag_level: WCAGLevel
    passed: bool
    issues: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    score: float = 0.0  # 0-100
    audit_date: datetime = field(default_factory=datetime.now)


class ADHDSupport:
    """ADHD (DEHB) specific accessibility features"""

    # Pomodoro defaults optimized for ADHD
    DEFAULT_WORK_DURATION = 25  # minutes
    DEFAULT_SHORT_BREAK = 5
    DEFAULT_LONG_BREAK = 15
    SESSIONS_UNTIL_LONG_BREAK = 4

    @staticmethod
    def get_focus_mode_settings() -> dict[str, Any]:
        """Get optimal focus mode settings for ADHD"""
        return {
            "hide_distractions": True,
            "simplified_ui": True,
            "progress_indicators": True,
            "chunked_content": True,
            "max_items_per_view": 3,
            "visual_timer": True,
            "sound_notifications": True,
            "haptic_feedback": True,
            "color_coding": True,
            "immediate_feedback": True,
        }

    @staticmethod
    def get_task_breakdown_rules() -> dict[str, Any]:
        """Rules for breaking down tasks for ADHD students"""
        return {
            "max_task_duration_minutes": 15,
            "max_steps_per_task": 5,
            "include_micro_rewards": True,
            "visual_progress_tracking": True,
            "estimated_time_display": True,
            "difficulty_indicator": True,
            "allow_task_reordering": True,
        }

    @staticmethod
    def get_exam_adaptations(base_time_minutes: int) -> dict[str, Any]:
        """Get ADHD-specific exam adaptations"""
        return {
            "extended_time_minutes": int(base_time_minutes * 1.5),
            "break_allowed": True,
            "break_interval_minutes": 20,
            "break_duration_minutes": 5,
            "question_chunking": True,
            "questions_per_page": 3,
            "progress_bar": True,
            "remaining_time_alerts": [15, 10, 5, 2],  # minutes
            "distraction_blocker": True,
        }


class DyslexiaSupport:
    """Dyslexia (Disleksi) specific accessibility features"""

    # Recommended fonts for dyslexia
    RECOMMENDED_FONTS = [
        "OpenDyslexic",
        "Lexie Readable",
        "Comic Sans MS",
        "Arial",
        "Verdana",
    ]

    # Default Turkish voice settings
    DEFAULT_TTS_SETTINGS = {
        "voice": "tr-TR-Wavenet-A",
        "rate": 0.9,
        "pitch": 0.0,
        "volume": 1.0,
    }

    @staticmethod
    def get_text_display_settings() -> dict[str, Any]:
        """Get optimal text display settings for dyslexia"""
        return {
            "font_family": "OpenDyslexic, Arial, sans-serif",
            "font_size_min": 16,
            "font_size_recommended": 18,
            "line_height": 1.8,
            "letter_spacing": "0.12em",
            "word_spacing": "0.16em",
            "max_characters_per_line": 60,
            "paragraph_spacing": "1.5em",
            "text_align": "left",  # Never justify
            "avoid_italics": True,
            "avoid_all_caps": True,
        }

    @staticmethod
    def get_color_settings() -> dict[str, Any]:
        """Get optimal color settings for dyslexia"""
        return {
            "background_color": "#FFFEF0",  # Cream/off-white
            "text_color": "#2D2D2D",  # Dark gray (not pure black)
            "link_color": "#0066CC",
            "highlight_color": "#FFE066",
            "alternative_backgrounds": [
                "#F5F5DC",  # Beige
                "#E6F3FF",  # Light blue
                "#E8F5E9",  # Light green
                "#FFF3E0",  # Light orange
            ],
            "avoid_pure_white": True,
            "avoid_pure_black": True,
        }

    @staticmethod
    def get_bionic_reading_settings() -> dict[str, Any]:
        """Get bionic reading settings (bold first letters)"""
        return {
            "enabled": True,
            "bold_percentage": 40,  # % of word to bold
            "min_word_length": 3,
            "bold_weight": 700,
            "apply_to_turkish_chars": True,
        }

    @staticmethod
    def apply_bionic_reading(text: str) -> str:
        """Apply bionic reading formatting to Turkish text"""
        words = text.split()
        result = []

        for word in words:
            if len(word) < 3:
                result.append(word)
                continue

            # Calculate bold portion
            bold_length = max(1, len(word) * 40 // 100)
            bold_part = word[:bold_length]
            rest = word[bold_length:]

            # Use markdown-style bold
            result.append(f"**{bold_part}**{rest}")

        return " ".join(result)


class DyscalculiaSupport:
    """Dyscalculia (Diskalkuli) specific accessibility features"""

    @staticmethod
    def get_math_display_settings() -> dict[str, Any]:
        """Get optimal math display settings for dyscalculia"""
        return {
            "large_numbers": True,
            "number_spacing": "0.2em",
            "grid_paper_background": True,
            "color_coded_operations": True,
            "step_by_step_solutions": True,
            "visual_number_line": True,
            "manipulatives_enabled": True,
            "audio_numbers": True,
            "avoid_cluttered_equations": True,
        }

    @staticmethod
    def get_operation_colors() -> dict[str, str]:
        """Color coding for mathematical operations"""
        return {
            "addition": "#4CAF50",      # Green
            "subtraction": "#F44336",   # Red
            "multiplication": "#2196F3", # Blue
            "division": "#FF9800",      # Orange
            "equals": "#9C27B0",        # Purple
            "parentheses": "#795548",   # Brown
        }

    @staticmethod
    def get_number_visualization(number: int) -> dict[str, Any]:
        """Get visual representation for a number"""
        return {
            "number": number,
            "blocks": number,
            "number_line_position": number,
            "spoken_form_tr": DyscalculiaSupport._number_to_turkish(number),
            "decomposition": DyscalculiaSupport._decompose_number(number),
        }

    @staticmethod
    def _number_to_turkish(n: int) -> str:
        """Convert number to Turkish words"""
        ones = ["", "bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz"]
        tens = ["", "on", "yirmi", "otuz", "kırk", "elli", "altmış", "yetmiş", "seksen", "doksan"]

        if n == 0:
            return "sıfır"
        if n < 10:
            return ones[n]
        if n < 100:
            return f"{tens[n // 10]} {ones[n % 10]}".strip()
        if n < 1000:
            hundreds = "yüz" if n // 100 == 1 else f"{ones[n // 100]} yüz"
            remainder = DyscalculiaSupport._number_to_turkish(n % 100)
            return f"{hundreds} {remainder}".strip()
        return str(n)  # For larger numbers, return as string

    @staticmethod
    def _decompose_number(n: int) -> list[dict[str, Any]]:
        """Decompose number into place values"""
        if n == 0:
            return [{"place": "ones", "value": 0}]

        result = []
        places = [
            ("thousands", 1000),
            ("hundreds", 100),
            ("tens", 10),
            ("ones", 1),
        ]

        for place_name, place_value in places:
            if n >= place_value:
                digit = n // place_value
                result.append({
                    "place": place_name,
                    "value": digit,
                    "contribution": digit * place_value,
                })
                n %= place_value

        return result


class VisualImpairmentSupport:
    """Visual impairment accessibility features"""

    @staticmethod
    def get_screen_reader_settings() -> dict[str, Any]:
        """Get optimal screen reader settings"""
        return {
            "aria_labels": True,
            "semantic_html": True,
            "skip_links": True,
            "focus_indicators": True,
            "keyboard_navigation": True,
            "alt_text_required": True,
            "table_summaries": True,
            "form_labels": True,
            "error_announcements": True,
            "live_regions": True,
        }

    @staticmethod
    def get_high_contrast_colors() -> dict[str, str]:
        """High contrast color scheme"""
        return {
            "background": "#000000",
            "text": "#FFFFFF",
            "link": "#FFFF00",
            "visited_link": "#FF00FF",
            "focus_outline": "#00FFFF",
            "error": "#FF6B6B",
            "success": "#00FF00",
            "warning": "#FFA500",
        }

    @staticmethod
    def calculate_contrast_ratio(
        foreground: str,
        background: str,
    ) -> float:
        """Calculate WCAG contrast ratio between two colors"""
        def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        def relative_luminance(rgb: tuple[int, int, int]) -> float:
            def adjust(c: int) -> float:
                c = c / 255
                return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
            r, g, b = rgb
            return 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b)

        l1 = relative_luminance(hex_to_rgb(foreground))
        l2 = relative_luminance(hex_to_rgb(background))

        lighter = max(l1, l2)
        darker = min(l1, l2)

        return (lighter + 0.05) / (darker + 0.05)

    @classmethod
    def check_wcag_contrast(
        cls,
        foreground: str,
        background: str,
        level: WCAGLevel = WCAGLevel.AA,
        is_large_text: bool = False,
    ) -> tuple[bool, float]:
        """Check if colors meet WCAG contrast requirements"""
        ratio = cls.calculate_contrast_ratio(foreground, background)

        # WCAG requirements
        if level == WCAGLevel.AAA:
            required = 4.5 if is_large_text else 7.0
        else:  # AA
            required = 3.0 if is_large_text else 4.5

        return ratio >= required, ratio


class AutismSupport:
    """Autism Spectrum (OSB) accessibility features"""

    @staticmethod
    def get_predictable_layout_settings() -> dict[str, Any]:
        """Get predictable layout settings for autism"""
        return {
            "consistent_navigation": True,
            "clear_visual_hierarchy": True,
            "explicit_instructions": True,
            "avoid_ambiguity": True,
            "literal_language": True,
            "visual_schedules": True,
            "transition_warnings": True,
            "sensory_controls": True,
            "quiet_mode_available": True,
            "structured_content": True,
        }

    @staticmethod
    def get_sensory_settings() -> dict[str, Any]:
        """Get sensory-friendly settings"""
        return {
            "reduce_animations": True,
            "reduce_auto_play": True,
            "mute_sounds": False,  # User preference
            "volume_control": True,
            "brightness_control": True,
            "color_temperature": "warm",
            "reduce_flashing": True,
            "simple_backgrounds": True,
            "avoid_busy_patterns": True,
        }

    @staticmethod
    def get_social_story_template(
        activity: str,
        steps: list[str],
    ) -> dict[str, Any]:
        """Generate social story template for an activity"""
        return {
            "title": f"{activity} Yaparken",
            "introduction": f"Bugün {activity} yapacağız.",
            "steps": [
                {"step_number": i + 1, "description": step, "completed": False}
                for i, step in enumerate(steps)
            ],
            "conclusion": f"{activity} tamamlandı! Harika iş çıkardın!",
            "visual_supports": True,
            "timer_available": True,
        }


class UnifiedAccessibilityService:
    """
    Unified service combining all accessibility features

    WCAG 2.1 Level AA/AAA compliance for Turkish educational platform
    """

    def __init__(self):
        self.adhd = ADHDSupport()
        self.dyslexia = DyslexiaSupport()
        self.dyscalculia = DyscalculiaSupport()
        self.visual = VisualImpairmentSupport()
        self.autism = AutismSupport()
        self._user_settings: dict[int, AccessibilitySettings] = {}

    def get_user_settings(self, user_id: int) -> AccessibilitySettings:
        """Get user's accessibility settings"""
        if user_id not in self._user_settings:
            self._user_settings[user_id] = AccessibilitySettings(user_id=user_id)
        return self._user_settings[user_id]

    def update_user_settings(
        self,
        user_id: int,
        settings: dict[str, Any],
    ) -> AccessibilitySettings:
        """Update user's accessibility settings"""
        current = self.get_user_settings(user_id)

        for key, value in settings.items():
            if hasattr(current, key):
                setattr(current, key, value)

        current.updated_at = datetime.now()
        return current

    def apply_profile(
        self,
        user_id: int,
        profile: AccessibilityProfile,
    ) -> AccessibilitySettings:
        """Apply a predefined accessibility profile"""
        settings = self.get_user_settings(user_id)
        settings.profile = profile

        # Apply profile-specific defaults
        if profile == AccessibilityProfile.ADHD:
            settings.focus_mode_enabled = True
            settings.break_reminder_interval = 25
            settings.reduce_motion = True
            settings.extended_time_percentage = 50

        elif profile == AccessibilityProfile.DYSLEXIA:
            settings.font_family = "OpenDyslexic, Arial, sans-serif"
            settings.font_size_multiplier = 1.2
            settings.line_height_multiplier = 1.8
            settings.letter_spacing = 0.12
            settings.bionic_reading_enabled = True
            settings.text_to_speech_enabled = True

        elif profile == AccessibilityProfile.DYSCALCULIA:
            settings.math_step_by_step = True
            settings.number_line_visualization = True
            settings.grid_paper_enabled = True
            settings.extended_time_percentage = 50

        elif profile == AccessibilityProfile.VISUAL_IMPAIRMENT:
            settings.font_size_multiplier = 1.5
            settings.high_contrast = True
            settings.text_to_speech_enabled = True

        elif profile == AccessibilityProfile.LOW_VISION:
            settings.font_size_multiplier = 1.8
            settings.high_contrast = True
            settings.line_height_multiplier = 2.0

        elif profile == AccessibilityProfile.AUTISM:
            settings.reduce_motion = True
            settings.reduce_transparency = True
            settings.predictable_layout = True
            settings.simplified_language = True

        elif profile == AccessibilityProfile.COGNITIVE:
            settings.simplified_language = True
            settings.extended_time_percentage = 100
            settings.break_reminder_interval = 20

        settings.updated_at = datetime.now()
        return settings

    def get_adapted_content(
        self,
        content: str,
        user_id: int,
        content_type: str = "text",
    ) -> dict[str, Any]:
        """Adapt content based on user's accessibility settings"""
        settings = self.get_user_settings(user_id)

        result = {
            "original_content": content,
            "adapted_content": content,
            "adaptations_applied": [],
        }

        # Apply bionic reading
        if settings.bionic_reading_enabled:
            result["adapted_content"] = DyslexiaSupport.apply_bionic_reading(content)
            result["adaptations_applied"].append("bionic_reading")

        # Add TTS data
        if settings.text_to_speech_enabled:
            result["tts_available"] = True
            result["tts_settings"] = DyslexiaSupport.DEFAULT_TTS_SETTINGS
            result["adaptations_applied"].append("tts")

        # Add styling
        result["styles"] = self._get_content_styles(settings)

        return result

    def _get_content_styles(
        self,
        settings: AccessibilitySettings,
    ) -> dict[str, Any]:
        """Generate CSS styles based on settings"""
        styles = {
            "font-family": settings.font_family,
            "font-size": f"{settings.font_size_multiplier}rem",
            "line-height": str(settings.line_height_multiplier),
        }

        if settings.letter_spacing > 0:
            styles["letter-spacing"] = f"{settings.letter_spacing}em"

        if settings.word_spacing > 0:
            styles["word-spacing"] = f"{settings.word_spacing}em"

        if settings.high_contrast:
            contrast_colors = VisualImpairmentSupport.get_high_contrast_colors()
            styles["background-color"] = contrast_colors["background"]
            styles["color"] = contrast_colors["text"]

        return styles

    def get_exam_adaptations(
        self,
        user_id: int,
        base_time_minutes: int,
    ) -> dict[str, Any]:
        """Get exam adaptations for user"""
        settings = self.get_user_settings(user_id)

        adaptations = {
            "time_extension_percentage": settings.extended_time_percentage,
            "extended_time_minutes": int(
                base_time_minutes * (1 + settings.extended_time_percentage / 100)
            ),
            "breaks_allowed": settings.auto_pause_enabled,
            "text_to_speech": settings.text_to_speech_enabled,
            "high_contrast": settings.high_contrast,
            "large_text": settings.font_size_multiplier > 1.2,
        }

        # Profile-specific adaptations
        if settings.profile == AccessibilityProfile.ADHD:
            adaptations.update(ADHDSupport.get_exam_adaptations(base_time_minutes))
        elif settings.profile == AccessibilityProfile.DYSCALCULIA:
            adaptations["math_tools"] = DyscalculiaSupport.get_math_display_settings()

        return adaptations

    def audit_content(
        self,
        content_id: str,
        content: dict[str, Any],
        target_level: WCAGLevel = WCAGLevel.AA,
    ) -> AccessibilityAuditResult:
        """Audit content for WCAG compliance"""
        issues = []
        recommendations = []
        score = 100.0

        # Check for alt text
        if "images" in content:
            for img in content["images"]:
                if not img.get("alt"):
                    issues.append({
                        "criterion": "1.1.1",
                        "severity": "error",
                        "message": "Görsel için alternatif metin eksik",
                        "element": img.get("src", "unknown"),
                    })
                    score -= 10

        # Check color contrast
        if "colors" in content:
            fg = content["colors"].get("foreground", "#000000")
            bg = content["colors"].get("background", "#FFFFFF")
            passes, ratio = VisualImpairmentSupport.check_wcag_contrast(
                fg, bg, target_level
            )
            if not passes:
                issues.append({
                    "criterion": "1.4.3",
                    "severity": "error",
                    "message": f"Yetersiz renk kontrastı: {ratio:.2f}:1",
                    "required": "4.5:1 (AA) veya 7:1 (AAA)",
                })
                score -= 15

        # Check for headings structure
        if "headings" in content:
            levels = [h.get("level", 1) for h in content["headings"]]
            if levels and levels[0] != 1:
                issues.append({
                    "criterion": "1.3.1",
                    "severity": "warning",
                    "message": "Başlık hiyerarşisi h1 ile başlamalı",
                })
                score -= 5

        # Generate recommendations
        if content.get("has_video") and not content.get("has_captions"):
            recommendations.append("Videolara Türkçe altyazı ekleyin")

        if not content.get("keyboard_accessible", True):
            recommendations.append("Klavye erişilebilirliğini kontrol edin")
            issues.append({
                "criterion": "2.1.1",
                "severity": "error",
                "message": "Klavye ile erişilemiyor",
            })
            score -= 20

        return AccessibilityAuditResult(
            content_id=content_id,
            wcag_level=target_level,
            passed=len([i for i in issues if i["severity"] == "error"]) == 0,
            issues=issues,
            recommendations=recommendations,
            score=max(0, score),
        )

    def get_turkish_accessibility_guidelines(self) -> dict[str, Any]:
        """Get Turkish-specific accessibility guidelines"""
        return {
            "language_code": "tr-TR",
            "reading_direction": "ltr",
            "special_characters": ["ı", "ş", "ğ", "ü", "ö", "ç", "İ", "Ş", "Ğ", "Ü", "Ö", "Ç"],
            "font_recommendations": [
                "Noto Sans Turkish",
                "Open Sans",
                "Roboto",
                "Source Sans Pro",
            ],
            "tts_voices": [
                "tr-TR-Wavenet-A",
                "tr-TR-Wavenet-B",
                "tr-TR-Wavenet-C",
                "tr-TR-Wavenet-D",
                "tr-TR-Wavenet-E",
            ],
            "number_format": {
                "decimal_separator": ",",
                "thousands_separator": ".",
                "currency": "TL",
            },
            "date_format": "DD.MM.YYYY",
            "educational_terms": {
                "TYT": "Temel Yeterlilik Testi",
                "AYT": "Alan Yeterlilik Testi",
                "YKS": "Yükseköğretim Kurumları Sınavı",
                "ÖSYM": "Ölçme, Seçme ve Yerleştirme Merkezi",
            },
        }


# Global service instance
_accessibility_service: UnifiedAccessibilityService | None = None


def get_accessibility_service() -> UnifiedAccessibilityService:
    """Get global accessibility service"""
    global _accessibility_service
    if _accessibility_service is None:
        _accessibility_service = UnifiedAccessibilityService()
    return _accessibility_service
