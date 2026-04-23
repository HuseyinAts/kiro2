"""
MapDiagramGenerator - KIRO2

Main generator class using mixin composition.

Generates OSYM-style maps and diagrams in SVG format for educational questions.

Diagram Types:
1. Geographic Maps: Turkey regions, cities, continents
2. Process Diagrams: Flowcharts, cycles, system diagrams
3. Classification Diagrams: Tree diagrams, Venn diagrams, matrices, org charts
4. Timeline Diagrams: Horizontal/vertical historical timelines

Features:
- OSYM styling (black & white, minimal, professional)
- Turkish text support with proper encoding
- SVG format (scalable, print-friendly)
- Context-aware content generation
"""

from datetime import UTC, datetime
from typing import Any, Literal

from .base import BaseDiagramGenerator
from .classification import ClassificationMixin
from .geographic_maps import GeographicMapMixin
from .process_diagrams import ProcessDiagramMixin
from .timeline import TimelineMixin


class MapDiagramGenerator(
    GeographicMapMixin,
    ProcessDiagramMixin,
    ClassificationMixin,
    TimelineMixin,
    BaseDiagramGenerator,
):
    """
    Generates OSYM-style maps and diagrams in SVG format.

    Supported diagram types:
    - Geographic Maps: Turkey regions, cities, continents
    - Process Diagrams: Flowcharts, cycles, system diagrams
    - Classification Diagrams: Trees, Venn diagrams, matrices, org charts
    - Timeline Diagrams: Horizontal/vertical historical timelines
    """

    def __init__(self) -> None:
        """Initialize generator with OSYM styling."""
        super().__init__()

    def generate_diagram(
        self,
        diagram_type: Literal[
            "geographic_map", "process_diagram", "classification_diagram", "timeline"
        ],
        diagram_subtype: str,
        content: dict[str, Any],
        labels: dict[str, str] | None = None,
        show_legend: bool = True,
    ) -> dict[str, Any]:
        """
        Generate map or diagram in SVG format.

        Args:
            diagram_type: Type of diagram (geographic_map, process_diagram,
                         classification_diagram, timeline)
            diagram_subtype: Specific subtype (e.g., "turkey_regions", "flowchart")
            content: Content data specific to diagram type
            labels: Optional custom labels (Turkish by default)
            show_legend: Whether to show legend

        Returns:
            Dict with visual_content structure:
            {
                'type': 'map_diagram',
                'format': 'svg',
                'content': '<svg>...</svg>',
                'metadata': {...}
            }
        """
        # Select appropriate generator
        if diagram_type == "geographic_map":
            svg_content, metadata = self._generate_geographic_map(
                diagram_subtype, content, labels, show_legend
            )
        elif diagram_type == "process_diagram":
            svg_content, metadata = self._generate_process_diagram(
                diagram_subtype, content, labels
            )
        elif diagram_type == "classification_diagram":
            svg_content, metadata = self._generate_classification_diagram(
                diagram_subtype, content, labels
            )
        elif diagram_type == "timeline":
            svg_content, metadata = self._generate_timeline(
                diagram_subtype, content, labels
            )
        else:
            raise ValueError(f"Unknown diagram type: {diagram_type}")

        # Return visual_content structure
        return {
            "type": "map_diagram",
            "format": "svg",
            "content": svg_content,
            "metadata": {
                "diagram_type": diagram_type,
                "diagram_subtype": diagram_subtype,
                "description": metadata.get("description", ""),
                "generated_at": datetime.now(UTC).isoformat(),
                **metadata,
            },
        }

    def generate(
        self,
        subtype: str,
        content: dict[str, Any],
        labels: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> tuple[str, dict[str, Any]]:
        """
        Abstract method implementation for BaseDiagramGenerator.

        This method routes to the appropriate diagram generator based on subtype.
        For full control, use generate_diagram() instead.

        Args:
            subtype: Full subtype identifier (e.g., "geographic_map:turkey_regions")
            content: Content data for the diagram
            labels: Optional custom labels
            **kwargs: Additional arguments (show_legend, etc.)

        Returns:
            Tuple of (svg_content, metadata)
        """
        # Parse subtype to get diagram_type and diagram_subtype
        if ":" in subtype:
            diagram_type, diagram_subtype = subtype.split(":", 1)
        else:
            # Default to geographic_map for simple subtypes
            diagram_subtype = subtype
            if subtype in ["turkey_regions", "turkey_cities", "continents"]:
                diagram_type = "geographic_map"
            elif subtype in ["flowchart", "cycle_diagram", "system_diagram"]:
                diagram_type = "process_diagram"
            elif subtype in ["tree_diagram", "venn_diagram", "matrix_diagram", "organizational_chart"]:
                diagram_type = "classification_diagram"
            elif subtype in ["horizontal_timeline", "vertical_timeline"]:
                diagram_type = "timeline"
            else:
                raise ValueError(f"Unknown subtype: {subtype}")

        show_legend = kwargs.get("show_legend", True)

        result = self.generate_diagram(
            diagram_type=diagram_type,  # type: ignore
            diagram_subtype=diagram_subtype,
            content=content,
            labels=labels,
            show_legend=show_legend,
        )

        return result["content"], result["metadata"]
