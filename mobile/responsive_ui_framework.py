"""
KIRO2 Responsive UI Framework
Cross-platform responsive user interface framework for Turkish exam preparation platform
Türkiye Üniversite Sınavları Hazırlık Platformu - Duyarlı UI Framework
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from enum import Enum
import json
import uuid
from pathlib import Path
import math

from backend.core.structured_logging import get_logger, LogCategory
from backend.core.unified_config import get_unified_config

logger = get_logger(__name__, LogCategory.MOBILE)
config = get_unified_config()


class ScreenSize(Enum):
    """Screen size categories"""
    XS = "xs"  # < 576px
    SM = "sm"  # 576px - 768px
    MD = "md"  # 768px - 992px
    LG = "lg"  # 992px - 1200px
    XL = "xl"  # > 1200px


class Orientation(Enum):
    """Screen orientation"""
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"


class UIComponent(Enum):
    """UI component types"""
    BUTTON = "button"
    INPUT = "input"
    TEXT = "text"
    IMAGE = "image"
    CARD = "card"
    LIST = "list"
    GRID = "grid"
    MODAL = "modal"
    NAVIGATION = "navigation"
    FORM = "form"
    CHART = "chart"
    PROGRESS = "progress"
    QUIZ = "quiz"
    EXAM = "exam"


class InteractionType(Enum):
    """User interaction types"""
    TOUCH = "touch"
    MOUSE = "mouse"
    KEYBOARD = "keyboard"
    VOICE = "voice"
    GESTURE = "gesture"


class ThemeVariant(Enum):
    """Theme variants"""
    LIGHT = "light"
    DARK = "dark"
    HIGH_CONTRAST = "high_contrast"
    SEPIA = "sepia"


@dataclass
class ResponsiveBreakpoint:
    """Responsive design breakpoint"""
    name: str
    min_width: int
    max_width: Optional[int] = None
    
    # Layout properties
    columns: int = 12
    gutter: int = 16
    margin: int = 16
    
    # Typography scale
    base_font_size: int = 14
    line_height: float = 1.5
    scale_factor: float = 1.0
    
    # Component sizes
    button_height: int = 44
    input_height: int = 40
    card_padding: int = 16
    
    def matches_width(self, width: int) -> bool:
        """Check if width matches this breakpoint"""
        if self.max_width:
            return self.min_width <= width < self.max_width
        else:
            return width >= self.min_width


@dataclass
class LayoutConstraints:
    """Layout constraints and rules"""
    min_width: Optional[int] = None
    max_width: Optional[int] = None
    min_height: Optional[int] = None
    max_height: Optional[int] = None
    
    # Spacing
    padding: Dict[str, int] = field(default_factory=dict)
    margin: Dict[str, int] = field(default_factory=dict)
    
    # Alignment
    horizontal_align: str = "left"  # left, center, right, stretch
    vertical_align: str = "top"  # top, center, bottom, stretch
    
    # Responsive behavior
    flex_grow: float = 0
    flex_shrink: float = 1
    flex_basis: str = "auto"
    
    # Visibility rules
    hidden_on: List[ScreenSize] = field(default_factory=list)
    visible_only_on: List[ScreenSize] = field(default_factory=list)
    
    def should_be_visible(self, screen_size: ScreenSize) -> bool:
        """Check if component should be visible at given screen size"""
        if self.hidden_on and screen_size in self.hidden_on:
            return False
        
        if self.visible_only_on and screen_size not in self.visible_only_on:
            return False
        
        return True


@dataclass
class UIStyle:
    """UI component styling"""
    # Colors
    background_color: Optional[str] = None
    text_color: Optional[str] = None
    border_color: Optional[str] = None
    accent_color: Optional[str] = None
    
    # Typography
    font_family: Optional[str] = None
    font_size: Optional[int] = None
    font_weight: str = "normal"
    text_align: str = "left"
    line_height: Optional[float] = None
    
    # Spacing
    padding: Dict[str, int] = field(default_factory=dict)
    margin: Dict[str, int] = field(default_factory=dict)
    
    # Border and radius
    border_width: int = 0
    border_radius: int = 0
    
    # Shadow and effects
    shadow_elevation: int = 0
    opacity: float = 1.0
    
    # Responsive overrides
    responsive_styles: Dict[ScreenSize, Dict[str, Any]] = field(default_factory=dict)
    
    def get_style_for_screen(self, screen_size: ScreenSize) -> Dict[str, Any]:
        """Get computed style for specific screen size"""
        base_style = {
            "background_color": self.background_color,
            "text_color": self.text_color,
            "border_color": self.border_color,
            "accent_color": self.accent_color,
            "font_family": self.font_family,
            "font_size": self.font_size,
            "font_weight": self.font_weight,
            "text_align": self.text_align,
            "line_height": self.line_height,
            "padding": self.padding.copy(),
            "margin": self.margin.copy(),
            "border_width": self.border_width,
            "border_radius": self.border_radius,
            "shadow_elevation": self.shadow_elevation,
            "opacity": self.opacity
        }
        
        # Apply responsive overrides
        if screen_size in self.responsive_styles:
            responsive_overrides = self.responsive_styles[screen_size]
            for key, value in responsive_overrides.items():
                if key in ["padding", "margin"] and isinstance(value, dict):
                    base_style[key].update(value)
                else:
                    base_style[key] = value
        
        return base_style


@dataclass
class ResponsiveUIComponent:
    """Responsive UI component definition"""
    component_id: str
    component_type: UIComponent
    
    # Content
    content: Dict[str, Any] = field(default_factory=dict)
    
    # Layout
    layout_constraints: LayoutConstraints = field(default_factory=LayoutConstraints)
    
    # Styling
    style: UIStyle = field(default_factory=UIStyle)
    
    # Behavior
    interactive: bool = True
    accessible: bool = True
    
    # Event handlers
    event_handlers: Dict[str, Callable] = field(default_factory=dict)
    
    # Responsive variants
    responsive_variants: Dict[ScreenSize, Dict[str, Any]] = field(default_factory=dict)
    
    # Turkish localization
    localized_content: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Children components
    children: List['ResponsiveUIComponent'] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.component_id:
            self.component_id = str(uuid.uuid4())
    
    def add_child(self, child: 'ResponsiveUIComponent') -> None:
        """Add child component"""
        self.children.append(child)
    
    def remove_child(self, component_id: str) -> bool:
        """Remove child component"""
        for i, child in enumerate(self.children):
            if child.component_id == component_id:
                self.children.pop(i)
                return True
        return False
    
    def get_content_for_language(self, language: str = "tr") -> Dict[str, Any]:
        """Get localized content"""
        if language in self.localized_content:
            return self.localized_content[language]
        return self.content
    
    def adapt_for_screen(self, screen_size: ScreenSize, breakpoint: ResponsiveBreakpoint) -> Dict[str, Any]:
        """Adapt component for specific screen size"""
        # Check visibility
        if not self.layout_constraints.should_be_visible(screen_size):
            return {"visible": False}
        
        # Get base configuration
        component_config = {
            "id": self.component_id,
            "type": self.component_type.value,
            "content": self.get_content_for_language("tr"),
            "visible": True,
            "interactive": self.interactive,
            "accessible": self.accessible
        }
        
        # Apply layout constraints
        layout_config = self._get_layout_config(screen_size, breakpoint)
        component_config["layout"] = layout_config
        
        # Apply styling
        style_config = self.style.get_style_for_screen(screen_size)
        component_config["style"] = style_config
        
        # Apply responsive variant overrides
        if screen_size in self.responsive_variants:
            variant_config = self.responsive_variants[screen_size]
            self._merge_config(component_config, variant_config)
        
        # Process children
        if self.children:
            component_config["children"] = [
                child.adapt_for_screen(screen_size, breakpoint)
                for child in self.children
                if child.layout_constraints.should_be_visible(screen_size)
            ]
        
        return component_config
    
    def _get_layout_config(self, screen_size: ScreenSize, breakpoint: ResponsiveBreakpoint) -> Dict[str, Any]:
        """Get layout configuration for screen size"""
        constraints = self.layout_constraints
        
        return {
            "width": self._calculate_responsive_size(constraints.min_width, constraints.max_width, breakpoint),
            "height": self._calculate_responsive_size(constraints.min_height, constraints.max_height, breakpoint),
            "padding": self._scale_spacing(constraints.padding, breakpoint),
            "margin": self._scale_spacing(constraints.margin, breakpoint),
            "alignment": {
                "horizontal": constraints.horizontal_align,
                "vertical": constraints.vertical_align
            },
            "flex": {
                "grow": constraints.flex_grow,
                "shrink": constraints.flex_shrink,
                "basis": constraints.flex_basis
            }
        }
    
    def _calculate_responsive_size(self, min_size: Optional[int], max_size: Optional[int], breakpoint: ResponsiveBreakpoint) -> Dict[str, Any]:
        """Calculate responsive size constraints"""
        return {
            "min": min_size * breakpoint.scale_factor if min_size else None,
            "max": max_size * breakpoint.scale_factor if max_size else None
        }
    
    def _scale_spacing(self, spacing: Dict[str, int], breakpoint: ResponsiveBreakpoint) -> Dict[str, int]:
        """Scale spacing values for breakpoint"""
        scaled_spacing = {}
        for key, value in spacing.items():
            scaled_spacing[key] = int(value * breakpoint.scale_factor)
        return scaled_spacing
    
    def _merge_config(self, base_config: Dict[str, Any], override_config: Dict[str, Any]) -> None:
        """Merge override configuration into base configuration"""
        for key, value in override_config.items():
            if isinstance(value, dict) and key in base_config and isinstance(base_config[key], dict):
                self._merge_config(base_config[key], value)
            else:
                base_config[key] = value


class ResponsiveLayoutManager:
    """Manager for responsive layout calculations"""
    
    def __init__(self):
        self.breakpoints: Dict[ScreenSize, ResponsiveBreakpoint] = self._initialize_breakpoints()
        self.current_breakpoint: Optional[ResponsiveBreakpoint] = None
        self.current_screen_size: Optional[ScreenSize] = None
    
    def _initialize_breakpoints(self) -> Dict[ScreenSize, ResponsiveBreakpoint]:
        """Initialize responsive breakpoints"""
        return {
            ScreenSize.XS: ResponsiveBreakpoint(
                name="Extra Small",
                min_width=0,
                max_width=576,
                columns=4,
                gutter=8,
                margin=8,
                base_font_size=12,
                scale_factor=0.8,
                button_height=40,
                input_height=36,
                card_padding=12
            ),
            ScreenSize.SM: ResponsiveBreakpoint(
                name="Small",
                min_width=576,
                max_width=768,
                columns=8,
                gutter=12,
                margin=12,
                base_font_size=14,
                scale_factor=0.9,
                button_height=42,
                input_height=38,
                card_padding=14
            ),
            ScreenSize.MD: ResponsiveBreakpoint(
                name="Medium",
                min_width=768,
                max_width=992,
                columns=12,
                gutter=16,
                margin=16,
                base_font_size=16,
                scale_factor=1.0,
                button_height=44,
                input_height=40,
                card_padding=16
            ),
            ScreenSize.LG: ResponsiveBreakpoint(
                name="Large",
                min_width=992,
                max_width=1200,
                columns=12,
                gutter=20,
                margin=20,
                base_font_size=18,
                scale_factor=1.1,
                button_height=48,
                input_height=44,
                card_padding=20
            ),
            ScreenSize.XL: ResponsiveBreakpoint(
                name="Extra Large",
                min_width=1200,
                columns=12,
                gutter=24,
                margin=24,
                base_font_size=20,
                scale_factor=1.2,
                button_height=52,
                input_height=48,
                card_padding=24
            )
        }
    
    def get_screen_size_for_width(self, width: int) -> ScreenSize:
        """Determine screen size category for given width"""
        for screen_size, breakpoint in self.breakpoints.items():
            if breakpoint.matches_width(width):
                return screen_size
        return ScreenSize.XL  # Default to extra large
    
    def get_breakpoint(self, screen_size: ScreenSize) -> ResponsiveBreakpoint:
        """Get breakpoint configuration for screen size"""
        return self.breakpoints[screen_size]
    
    def calculate_grid_layout(
        self,
        container_width: int,
        items_count: int,
        screen_size: ScreenSize,
        min_item_width: int = 200
    ) -> Dict[str, Any]:
        """Calculate responsive grid layout"""
        breakpoint = self.breakpoints[screen_size]
        
        # Calculate available width (minus margins and gutters)
        available_width = container_width - (2 * breakpoint.margin)
        
        # Calculate optimal columns
        max_columns = breakpoint.columns
        item_width_with_gutter = min_item_width + breakpoint.gutter
        ideal_columns = max(1, min(max_columns, available_width // item_width_with_gutter))
        
        # Calculate actual item width
        total_gutter_width = (ideal_columns - 1) * breakpoint.gutter
        actual_item_width = (available_width - total_gutter_width) // ideal_columns
        
        # Calculate rows needed
        rows = math.ceil(items_count / ideal_columns)
        
        return {
            "columns": ideal_columns,
            "rows": rows,
            "item_width": actual_item_width,
            "item_height": actual_item_width * 0.75,  # 4:3 aspect ratio default
            "gutter": breakpoint.gutter,
            "margin": breakpoint.margin,
            "total_width": container_width,
            "total_height": (rows * (actual_item_width * 0.75)) + ((rows - 1) * breakpoint.gutter) + (2 * breakpoint.margin)
        }
    
    def calculate_typography_scale(self, screen_size: ScreenSize) -> Dict[str, int]:
        """Calculate typography scale for screen size"""
        breakpoint = self.breakpoints[screen_size]
        base_size = breakpoint.base_font_size
        
        return {
            "h1": int(base_size * 2.5),
            "h2": int(base_size * 2.0),
            "h3": int(base_size * 1.75),
            "h4": int(base_size * 1.5),
            "h5": int(base_size * 1.25),
            "h6": int(base_size * 1.0),
            "body": base_size,
            "caption": int(base_size * 0.875),
            "small": int(base_size * 0.75)
        }


class TurkishUIComponentFactory:
    """Factory for creating Turkish exam-specific UI components"""
    
    def __init__(self, layout_manager: ResponsiveLayoutManager):
        self.layout_manager = layout_manager
        self.theme_colors = self._initialize_theme_colors()
    
    def _initialize_theme_colors(self) -> Dict[ThemeVariant, Dict[str, str]]:
        """Initialize theme color schemes"""
        return {
            ThemeVariant.LIGHT: {
                "primary": "#2196F3",
                "secondary": "#FF9800",
                "success": "#4CAF50",
                "warning": "#FF9800",
                "error": "#F44336",
                "background": "#FFFFFF",
                "surface": "#F5F5F5",
                "text_primary": "#212121",
                "text_secondary": "#757575"
            },
            ThemeVariant.DARK: {
                "primary": "#1976D2",
                "secondary": "#F57C00",
                "success": "#388E3C",
                "warning": "#F57C00",
                "error": "#D32F2F",
                "background": "#121212",
                "surface": "#1E1E1E",
                "text_primary": "#FFFFFF",
                "text_secondary": "#AAAAAA"
            },
            ThemeVariant.HIGH_CONTRAST: {
                "primary": "#0066CC",
                "secondary": "#FF6600",
                "success": "#00AA00",
                "warning": "#FFAA00",
                "error": "#CC0000",
                "background": "#FFFFFF",
                "surface": "#F0F0F0",
                "text_primary": "#000000",
                "text_secondary": "#333333"
            }
        }
    
    def create_exam_question_card(
        self,
        question_data: Dict[str, Any],
        theme: ThemeVariant = ThemeVariant.LIGHT
    ) -> ResponsiveUIComponent:
        """Create responsive exam question card"""
        colors = self.theme_colors[theme]
        
        # Question text component
        question_text = ResponsiveUIComponent(
            component_type=UIComponent.TEXT,
            content={
                "text": question_data.get("question_text", ""),
                "type": "question"
            },
            localized_content={
                "tr": {
                    "text": question_data.get("question_text", ""),
                    "type": "soru"
                }
            },
            style=UIStyle(
                font_size=16,
                font_weight="500",
                text_color=colors["text_primary"],
                margin={"bottom": 16}
            ),
            layout_constraints=LayoutConstraints(
                padding={"all": 0},
                horizontal_align="left"
            )
        )
        
        # Answer options
        answer_options = []
        for i, option in enumerate(question_data.get("options", [])):
            option_component = ResponsiveUIComponent(
                component_type=UIComponent.BUTTON,
                content={
                    "text": f"{chr(65 + i)}) {option}",
                    "value": str(i),
                    "type": "option"
                },
                style=UIStyle(
                    background_color="#FFFFFF",
                    text_color=colors["text_primary"],
                    border_color=colors["primary"],
                    border_width=1,
                    border_radius=8,
                    padding={"all": 12},
                    margin={"bottom": 8},
                    responsive_styles={
                        ScreenSize.XS: {"padding": {"all": 8}},
                        ScreenSize.SM: {"padding": {"all": 10}}
                    }
                ),
                layout_constraints=LayoutConstraints(
                    horizontal_align="stretch",
                    margin={"bottom": 8}
                ),
                interactive=True
            )
            answer_options.append(option_component)
        
        # Main question card
        question_card = ResponsiveUIComponent(
            component_type=UIComponent.CARD,
            content={
                "question_id": question_data.get("id"),
                "subject": question_data.get("subject"),
                "difficulty": question_data.get("difficulty")
            },
            style=UIStyle(
                background_color=colors["background"],
                border_color=colors["surface"],
                border_width=1,
                border_radius=12,
                shadow_elevation=2,
                padding={"all": 20},
                margin={"bottom": 16},
                responsive_styles={
                    ScreenSize.XS: {"padding": {"all": 12}},
                    ScreenSize.SM: {"padding": {"all": 16}}
                }
            ),
            layout_constraints=LayoutConstraints(
                horizontal_align="stretch",
                margin={"horizontal": 16, "vertical": 8}
            )
        )
        
        # Add children
        question_card.add_child(question_text)
        for option in answer_options:
            question_card.add_child(option)
        
        return question_card
    
    def create_exam_timer(
        self,
        total_time: int,
        remaining_time: int,
        theme: ThemeVariant = ThemeVariant.LIGHT
    ) -> ResponsiveUIComponent:
        """Create responsive exam timer component"""
        colors = self.theme_colors[theme]
        
        # Calculate timer progress
        progress_percentage = (remaining_time / total_time) * 100
        
        # Timer color based on remaining time
        if progress_percentage > 50:
            timer_color = colors["success"]
        elif progress_percentage > 25:
            timer_color = colors["warning"]
        else:
            timer_color = colors["error"]
        
        # Format time display
        minutes = remaining_time // 60
        seconds = remaining_time % 60
        time_display = f"{minutes:02d}:{seconds:02d}"
        
        timer_component = ResponsiveUIComponent(
            component_type=UIComponent.PROGRESS,
            content={
                "time_display": time_display,
                "progress": progress_percentage,
                "total_time": total_time,
                "remaining_time": remaining_time
            },
            localized_content={
                "tr": {
                    "label": "Kalan Süre",
                    "time_display": time_display
                }
            },
            style=UIStyle(
                background_color=colors["surface"],
                text_color=timer_color,
                accent_color=timer_color,
                font_size=18,
                font_weight="bold",
                text_align="center",
                border_radius=8,
                padding={"all": 12},
                responsive_styles={
                    ScreenSize.XS: {
                        "font_size": 14,
                        "padding": {"all": 8}
                    },
                    ScreenSize.SM: {
                        "font_size": 16,
                        "padding": {"all": 10}
                    }
                }
            ),
            layout_constraints=LayoutConstraints(
                horizontal_align="center",
                min_width=120,
                visible_only_on=[ScreenSize.SM, ScreenSize.MD, ScreenSize.LG, ScreenSize.XL]
            )
        )
        
        return timer_component
    
    def create_subject_navigation(
        self,
        subjects: List[Dict[str, Any]],
        current_subject: str,
        theme: ThemeVariant = ThemeVariant.LIGHT
    ) -> ResponsiveUIComponent:
        """Create responsive subject navigation"""
        colors = self.theme_colors[theme]
        
        navigation_component = ResponsiveUIComponent(
            component_type=UIComponent.NAVIGATION,
            content={
                "current_subject": current_subject,
                "subjects": subjects
            },
            style=UIStyle(
                background_color=colors["surface"],
                border_radius=8,
                padding={"all": 4}
            ),
            layout_constraints=LayoutConstraints(
                horizontal_align="stretch",
                margin={"bottom": 16}
            )
        )
        
        # Create subject tabs
        for subject_data in subjects:
            is_current = subject_data["id"] == current_subject
            
            tab_component = ResponsiveUIComponent(
                component_type=UIComponent.BUTTON,
                content={
                    "text": subject_data["name"],
                    "subject_id": subject_data["id"],
                    "question_count": subject_data.get("question_count", 0)
                },
                localized_content={
                    "tr": {
                        "text": subject_data["name_tr"],
                        "label": f"{subject_data['name_tr']} ({subject_data.get('question_count', 0)} soru)"
                    }
                },
                style=UIStyle(
                    background_color=colors["primary"] if is_current else "transparent",
                    text_color=colors["background"] if is_current else colors["text_primary"],
                    font_size=14,
                    font_weight="500" if is_current else "normal",
                    border_radius=6,
                    padding={"horizontal": 12, "vertical": 8},
                    margin={"right": 4},
                    responsive_styles={
                        ScreenSize.XS: {
                            "font_size": 12,
                            "padding": {"horizontal": 8, "vertical": 6}
                        }
                    }
                ),
                layout_constraints=LayoutConstraints(
                    flex_grow=1 if len(subjects) <= 4 else 0,
                    horizontal_align="center"
                ),
                interactive=True
            )
            
            navigation_component.add_child(tab_component)
        
        return navigation_component
    
    def create_progress_dashboard(
        self,
        user_stats: Dict[str, Any],
        theme: ThemeVariant = ThemeVariant.LIGHT
    ) -> ResponsiveUIComponent:
        """Create responsive progress dashboard"""
        colors = self.theme_colors[theme]
        
        dashboard = ResponsiveUIComponent(
            component_type=UIComponent.GRID,
            content={
                "title": "İlerleme Özeti",
                "user_stats": user_stats
            },
            style=UIStyle(
                background_color=colors["background"],
                padding={"all": 16}
            ),
            layout_constraints=LayoutConstraints(
                horizontal_align="stretch"
            ),
            responsive_variants={
                ScreenSize.XS: {"layout": {"columns": 1}},
                ScreenSize.SM: {"layout": {"columns": 2}},
                ScreenSize.MD: {"layout": {"columns": 3}},
                ScreenSize.LG: {"layout": {"columns": 4}}
            }
        )
        
        # Create stat cards
        stats = [
            {
                "key": "total_questions",
                "title": "Toplam Soru",
                "value": user_stats.get("total_questions", 0),
                "icon": "quiz",
                "color": colors["primary"]
            },
            {
                "key": "correct_answers",
                "title": "Doğru Cevap",
                "value": user_stats.get("correct_answers", 0),
                "icon": "check_circle",
                "color": colors["success"]
            },
            {
                "key": "success_rate",
                "title": "Başarı Oranı",
                "value": f"{user_stats.get('success_rate', 0):.1f}%",
                "icon": "trending_up",
                "color": colors["warning"]
            },
            {
                "key": "study_streak",
                "title": "Çalışma Serisi",
                "value": f"{user_stats.get('study_streak', 0)} gün",
                "icon": "local_fire_department",
                "color": colors["error"]
            }
        ]
        
        for stat in stats:
            stat_card = ResponsiveUIComponent(
                component_type=UIComponent.CARD,
                content=stat,
                style=UIStyle(
                    background_color=colors["surface"],
                    border_radius=12,
                    padding={"all": 16},
                    margin={"all": 8},
                    shadow_elevation=1,
                    responsive_styles={
                        ScreenSize.XS: {"margin": {"all": 4}}
                    }
                ),
                layout_constraints=LayoutConstraints(
                    min_height=100,
                    horizontal_align="stretch"
                )
            )
            
            dashboard.add_child(stat_card)
        
        return dashboard


class ResponsiveUIFramework:
    """Main responsive UI framework"""
    
    def __init__(self):
        self.layout_manager = ResponsiveLayoutManager()
        self.component_factory = TurkishUIComponentFactory(self.layout_manager)
        self.current_theme = ThemeVariant.LIGHT
        self.current_screen_size = ScreenSize.MD
        self.screen_width = 992
        self.screen_height = 768
        self.orientation = Orientation.LANDSCAPE
        
        # Component registry
        self.registered_components: Dict[str, ResponsiveUIComponent] = {}
        self.screen_layouts: Dict[str, List[ResponsiveUIComponent]] = {}
        
        # Interaction handling
        self.interaction_handlers: Dict[InteractionType, List[Callable]] = {
            InteractionType.TOUCH: [],
            InteractionType.MOUSE: [],
            InteractionType.KEYBOARD: [],
            InteractionType.VOICE: [],
            InteractionType.GESTURE: []
        }
    
    async def initialize(self, screen_width: int, screen_height: int) -> bool:
        """Initialize UI framework with screen dimensions"""
        try:
            self.screen_width = screen_width
            self.screen_height = screen_height
            self.orientation = Orientation.LANDSCAPE if screen_width > screen_height else Orientation.PORTRAIT
            self.current_screen_size = self.layout_manager.get_screen_size_for_width(screen_width)
            
            logger.info(f"UI Framework initialized: {screen_width}x{screen_height}, {self.current_screen_size.value}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize UI framework: {e}")
            return False
    
    def register_component(self, component: ResponsiveUIComponent) -> None:
        """Register a UI component"""
        self.registered_components[component.component_id] = component
    
    def create_screen_layout(self, screen_id: str, components: List[ResponsiveUIComponent]) -> None:
        """Create a screen layout with components"""
        self.screen_layouts[screen_id] = components
        
        # Register all components
        for component in components:
            self.register_component(component)
            self._register_children_recursive(component)
    
    def _register_children_recursive(self, component: ResponsiveUIComponent) -> None:
        """Recursively register child components"""
        for child in component.children:
            self.register_component(child)
            self._register_children_recursive(child)
    
    async def render_screen(self, screen_id: str) -> Dict[str, Any]:
        """Render screen layout for current screen size"""
        if screen_id not in self.screen_layouts:
            raise ValueError(f"Screen layout {screen_id} not found")
        
        components = self.screen_layouts[screen_id]
        breakpoint = self.layout_manager.get_breakpoint(self.current_screen_size)
        
        rendered_components = []
        for component in components:
            if component.layout_constraints.should_be_visible(self.current_screen_size):
                rendered_component = component.adapt_for_screen(self.current_screen_size, breakpoint)
                rendered_components.append(rendered_component)
        
        screen_config = {
            "screen_id": screen_id,
            "screen_size": self.current_screen_size.value,
            "breakpoint": {
                "name": breakpoint.name,
                "width_range": f"{breakpoint.min_width}px - {breakpoint.max_width or '∞'}px",
                "columns": breakpoint.columns,
                "gutter": breakpoint.gutter
            },
            "layout": {
                "width": self.screen_width,
                "height": self.screen_height,
                "orientation": self.orientation.value
            },
            "theme": self.current_theme.value,
            "components": rendered_components,
            "typography": self.layout_manager.calculate_typography_scale(self.current_screen_size)
        }
        
        return screen_config
    
    async def handle_screen_resize(self, new_width: int, new_height: int) -> Dict[str, Any]:
        """Handle screen resize event"""
        old_screen_size = self.current_screen_size
        
        self.screen_width = new_width
        self.screen_height = new_height
        self.orientation = Orientation.LANDSCAPE if new_width > new_height else Orientation.PORTRAIT
        self.current_screen_size = self.layout_manager.get_screen_size_for_width(new_width)
        
        resize_info = {
            "old_screen_size": old_screen_size.value,
            "new_screen_size": self.current_screen_size.value,
            "dimensions": {
                "width": new_width,
                "height": new_height
            },
            "orientation": self.orientation.value,
            "layout_changed": old_screen_size != self.current_screen_size
        }
        
        logger.info(f"Screen resized: {resize_info}")
        return resize_info
    
    def set_theme(self, theme: ThemeVariant) -> None:
        """Set UI theme"""
        self.current_theme = theme
        logger.info(f"Theme changed to: {theme.value}")
    
    def add_interaction_handler(self, interaction_type: InteractionType, handler: Callable) -> None:
        """Add interaction event handler"""
        self.interaction_handlers[interaction_type].append(handler)
    
    async def handle_interaction(self, interaction_type: InteractionType, event_data: Dict[str, Any]) -> bool:
        """Handle user interaction event"""
        handlers = self.interaction_handlers.get(interaction_type, [])
        
        for handler in handlers:
            try:
                await handler(event_data)
            except Exception as e:
                logger.error(f"Interaction handler failed: {e}")
                return False
        
        return len(handlers) > 0
    
    def calculate_grid_layout(self, container_width: int, items_count: int, min_item_width: int = 200) -> Dict[str, Any]:
        """Calculate responsive grid layout"""
        return self.layout_manager.calculate_grid_layout(
            container_width, items_count, self.current_screen_size, min_item_width
        )
    
    def get_framework_status(self) -> Dict[str, Any]:
        """Get current framework status"""
        return {
            "screen_size": self.current_screen_size.value,
            "dimensions": {
                "width": self.screen_width,
                "height": self.screen_height
            },
            "orientation": self.orientation.value,
            "theme": self.current_theme.value,
            "registered_components": len(self.registered_components),
            "screen_layouts": len(self.screen_layouts),
            "breakpoint_info": {
                "name": self.layout_manager.breakpoints[self.current_screen_size].name,
                "columns": self.layout_manager.breakpoints[self.current_screen_size].columns,
                "gutter": self.layout_manager.breakpoints[self.current_screen_size].gutter
            }
        }


if __name__ == "__main__":
    # Example usage and testing
    print("KIRO2 Responsive UI Framework")
    print("=" * 40)
    
    async def test_responsive_ui():
        """Test responsive UI framework"""
        ui_framework = ResponsiveUIFramework()
        
        # Initialize framework
        await ui_framework.initialize(1200, 800)
        
        # Create exam question
        question_data = {
            "id": "q1",
            "question_text": "Türkiye'nin başkenti neresidir?",
            "options": ["İstanbul", "Ankara", "İzmir", "Bursa"],
            "correct_answer": 1,
            "subject": "Tarih",
            "difficulty": "easy"
        }
        
        question_card = ui_framework.component_factory.create_exam_question_card(question_data)
        
        # Create exam timer
        timer = ui_framework.component_factory.create_exam_timer(3600, 2400)
        
        # Create user stats
        user_stats = {
            "total_questions": 150,
            "correct_answers": 120,
            "success_rate": 80.0,
            "study_streak": 5
        }
        
        progress_dashboard = ui_framework.component_factory.create_progress_dashboard(user_stats)
        
        # Create screen layout
        ui_framework.create_screen_layout("exam_screen", [question_card, timer, progress_dashboard])
        
        # Render screen
        screen_config = await ui_framework.render_screen("exam_screen")
        print(f"Screen rendered with {len(screen_config['components'])} components")
        
        # Test screen resize
        resize_info = await ui_framework.handle_screen_resize(768, 1024)
        print(f"Screen resized: {resize_info['layout_changed']}")
        
        # Re-render after resize
        screen_config = await ui_framework.render_screen("exam_screen")
        print(f"Screen re-rendered for {screen_config['screen_size']}")
        
        # Test grid layout calculation
        grid_layout = ui_framework.calculate_grid_layout(800, 12, 150)
        print(f"Grid layout: {grid_layout['columns']} columns, {grid_layout['rows']} rows")
        
        # Test theme change
        ui_framework.set_theme(ThemeVariant.DARK)
        
        # Get framework status
        status = ui_framework.get_framework_status()
        print(f"Framework status: {status['screen_size']}, {status['registered_components']} components")
        
        print("\nResponsive UI framework test completed!")
    
    # Run test
    asyncio.run(test_responsive_ui())