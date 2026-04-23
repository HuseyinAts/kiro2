"""
MapDiagramGenerator Service - Phase 4: Maps & Diagrams

BACKWARD COMPATIBILITY WRAPPER

This module has been refactored into the diagrams package.
This file is kept for backward compatibility with existing imports.

New location: backend/services/diagrams/

Usage (recommended):
    from backend.services.diagrams import MapDiagramGenerator

Usage (legacy, still works):
    from backend.services.map_diagram_generator import MapDiagramGenerator
"""

# Re-export everything from the new package for backward compatibility
from .diagrams import (
    COLORS,
    CONTINENTS,
    DEFAULT_FIG_SIZE,
    OSYM_DIAGRAM_STYLE,
    TURKEY_MAJOR_CITIES,
    TURKEY_REGIONS,
    BaseDiagramGenerator,
    ClassificationMixin,
    GeographicMapMixin,
    MapDiagramGenerator,
    ProcessDiagramMixin,
    TimelineMixin,
    close_figure,
    fig_to_svg,
    setup_axes,
)

# Legacy name aliases
OSYM_DIAGRAM_STYLE = OSYM_DIAGRAM_STYLE

__all__ = [
    "COLORS",
    "CONTINENTS",
    "DEFAULT_FIG_SIZE",
    "OSYM_DIAGRAM_STYLE",
    "TURKEY_MAJOR_CITIES",
    "TURKEY_REGIONS",
    "BaseDiagramGenerator",
    "ClassificationMixin",
    "GeographicMapMixin",
    "MapDiagramGenerator",
    "ProcessDiagramMixin",
    "TimelineMixin",
    "close_figure",
    "fig_to_svg",
    "setup_axes",
]


# ==================== TESTING ====================

if __name__ == "__main__":
    print("=" * 70)
    print("MapDiagramGenerator Test Suite")
    print("=" * 70)
    print()

    generator = MapDiagramGenerator()

    # Test 1: Turkey Regions Map
    print("[TEST 1] Turkey Regions Map")
    content1 = {
        "title": "Turkiye Cografi Bolgeleri",
        "highlight_regions": ["Marmara", "Ege"],
    }
    result1 = generator.generate_diagram(
        diagram_type="geographic_map",
        diagram_subtype="turkey_regions",
        content=content1,
        show_legend=True,
    )
    print(f"  - Generated: {result1['metadata']['diagram_subtype']}")
    print(f"  - Description: {result1['metadata']['description']}")
    print(f"  - SVG Size: {len(result1['content'])} chars")
    print()

    # Test 2: Flowchart
    print("[TEST 2] Flowchart")
    content2 = {
        "title": "Su Dongusu",
        "nodes": [
            {"id": "start", "type": "oval", "text": "Baslangic", "x": 5, "y": 10},
            {"id": "evap", "type": "rectangle", "text": "Buharlasma", "x": 5, "y": 8},
            {"id": "cond", "type": "rectangle", "text": "Yogunlasma", "x": 5, "y": 6},
            {"id": "precip", "type": "rectangle", "text": "Yagis", "x": 5, "y": 4},
            {"id": "end", "type": "oval", "text": "Dongu Devam Eder", "x": 5, "y": 2},
        ],
        "edges": [
            {"from": "start", "to": "evap"},
            {"from": "evap", "to": "cond"},
            {"from": "cond", "to": "precip"},
            {"from": "precip", "to": "end"},
        ],
    }
    result2 = generator.generate_diagram(
        diagram_type="process_diagram", diagram_subtype="flowchart", content=content2
    )
    print(f"  - Generated: {result2['metadata']['diagram_subtype']}")
    print(f"  - Nodes: {result2['metadata']['nodes_count']}")
    print(f"  - SVG Size: {len(result2['content'])} chars")
    print()

    # Test 3: Venn Diagram
    print("[TEST 3] Venn Diagram")
    content3 = {
        "title": "Kume Diyagrami",
        "sets": [
            {"label": "A", "only": ["2", "4"]},
            {"label": "B", "only": ["3", "5"]},
        ],
        "intersection": ["6", "8"],
    }
    result3 = generator.generate_diagram(
        diagram_type="classification_diagram",
        diagram_subtype="venn_diagram",
        content=content3,
    )
    print(f"  - Generated: {result3['metadata']['diagram_subtype']}")
    print(f"  - Sets: {result3['metadata']['sets_count']}")
    print(f"  - SVG Size: {len(result3['content'])} chars")
    print()

    # Test 4: Horizontal Timeline
    print("[TEST 4] Horizontal Timeline")
    content4 = {
        "title": "Turkiye Cumhuriyeti Tarihi",
        "events": [
            {"year": 1920, "event": "TBMM Acildi"},
            {"year": 1923, "event": "Cumhuriyet Ilan Edildi"},
            {"year": 1928, "event": "Harf Devrimi"},
            {"year": 1934, "event": "Soyadi Kanunu"},
            {"year": 1945, "event": "BM Uyeligi"},
        ],
    }
    result4 = generator.generate_diagram(
        diagram_type="timeline", diagram_subtype="horizontal_timeline", content=content4
    )
    print(f"  - Generated: {result4['metadata']['diagram_subtype']}")
    print(f"  - Events: {result4['metadata']['events_count']}")
    print(f"  - Time Span: {result4['metadata']['time_span']}")
    print(f"  - SVG Size: {len(result4['content'])} chars")
    print()

    # Test 5: Tree Diagram
    print("[TEST 5] Tree Diagram")
    content5 = {
        "title": "Canli Siniflandirmasi",
        "tree": {
            "root": "Canlilar",
            "levels": [
                {"nodes": ["Hayvanlar", "Bitkiler"]},
                {"nodes": ["Omurgalilar", "Omurgasizlar", "Tohumlu", "Tohumsuz"]},
            ],
        },
    }
    result5 = generator.generate_diagram(
        diagram_type="classification_diagram",
        diagram_subtype="tree_diagram",
        content=content5,
    )
    print(f"  - Generated: {result5['metadata']['diagram_subtype']}")
    print(f"  - Total Nodes: {result5['metadata']['total_nodes']}")
    print(f"  - SVG Size: {len(result5['content'])} chars")
    print()

    print("=" * 70)
    print("All Tests PASSED!")
    print("=" * 70)
