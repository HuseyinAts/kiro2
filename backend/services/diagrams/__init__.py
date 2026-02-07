"""
Diagrams Package - KIRO2

OSYM-style map and diagram generation for educational questions.

Usage:
    from backend.services.diagrams import MapDiagramGenerator

    generator = MapDiagramGenerator()
    result = generator.generate_diagram(
        diagram_type="geographic_map",
        diagram_subtype="turkey_regions",
        content={"title": "Turkiye Bolgeleri", "highlight_regions": ["Marmara"]},
    )
"""

from .base import BaseDiagramGenerator
from .classification import ClassificationMixin
from .generator import MapDiagramGenerator
from .geographic_maps import GeographicMapMixin
from .process_diagrams import ProcessDiagramMixin
from .styles import (
    COLORS,
    CONTINENTS,
    DEFAULT_FIG_SIZE,
    OSYM_DIAGRAM_STYLE,
    TURKEY_MAJOR_CITIES,
    TURKEY_REGIONS,
)
from .timeline import TimelineMixin
from .utils import close_figure, fig_to_svg, setup_axes

__all__ = [
    # Main generator
    "MapDiagramGenerator",
    # Base class
    "BaseDiagramGenerator",
    # Mixins
    "GeographicMapMixin",
    "ProcessDiagramMixin",
    "ClassificationMixin",
    "TimelineMixin",
    # Styles and data
    "OSYM_DIAGRAM_STYLE",
    "COLORS",
    "TURKEY_REGIONS",
    "TURKEY_MAJOR_CITIES",
    "CONTINENTS",
    "DEFAULT_FIG_SIZE",
    # Utilities
    "fig_to_svg",
    "setup_axes",
    "close_figure",
]
