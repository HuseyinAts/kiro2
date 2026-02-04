"""
MapDiagramGenerator Service - Phase 4: Maps & Diagrams

Generates ÖSYM-style maps and diagrams in SVG format for educational questions.

Diagram Types:
1. Geographic Maps: Turkey regions, cities, continents
2. Process Diagrams: Flowcharts, cycles, system diagrams
3. Classification Diagrams: Tree diagrams, Venn diagrams, matrices, org charts
4. Timeline Diagrams: Horizontal/vertical historical timelines

Features:
- ÖSYM styling (black & white, minimal, professional)
- Turkish text support with proper encoding
- SVG format (scalable, print-friendly)
- Context-aware content generation

Author: Phase 4 Implementation Team
Date: 2025-11-07
"""

import sys
import io
import math
import random
from typing import Dict, List, Literal, Optional, Any, Tuple
from datetime import datetime

# UTF-8 encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import matplotlib

matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Circle, Polygon, Wedge, FancyArrowPatch
from matplotlib.lines import Line2D
import numpy as np


# ÖSYM Diagram Styling
OSYM_DIAGRAM_STYLE = {
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "black",
    "axes.linewidth": 1.5,
    "grid.color": "#cccccc",
    "grid.linestyle": "--",
    "grid.linewidth": 0.5,
    "text.color": "black",
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.titlesize": 12,
    "lines.linewidth": 1.5,
    "lines.color": "black",
    "patch.edgecolor": "black",
    "patch.linewidth": 1.5,
}


# Turkey Geographic Data
TURKEY_REGIONS = {
    "Marmara": {
        "bbox": [(26, 40), (32, 42)],  # Simplified bounding box
        "cities": ["İstanbul", "Bursa", "Kocaeli", "Edirne", "Tekirdağ"],
    },
    "Ege": {
        "bbox": [(26, 37), (30, 40)],
        "cities": ["İzmir", "Aydın", "Muğla", "Manisa", "Denizli"],
    },
    "Akdeniz": {
        "bbox": [(29, 36), (37, 38)],
        "cities": ["Antalya", "Adana", "Mersin", "Hatay", "Kahramanmaraş"],
    },
    "İç Anadolu": {
        "bbox": [(31, 38), (36, 41)],
        "cities": ["Ankara", "Konya", "Kayseri", "Sivas", "Eskişehir"],
    },
    "Karadeniz": {
        "bbox": [(31, 40), (42, 42)],
        "cities": ["Samsun", "Trabzon", "Ordu", "Zonguldak", "Rize"],
    },
    "Doğu Anadolu": {
        "bbox": [(38, 38), (45, 41)],
        "cities": ["Erzurum", "Van", "Elazığ", "Malatya", "Ağrı"],
    },
    "Güneydoğu Anadolu": {
        "bbox": [(37, 36), (43, 39)],
        "cities": ["Gaziantep", "Şanlıurfa", "Diyarbakır", "Mardin", "Batman"],
    },
}

TURKEY_MAJOR_CITIES = {
    "İstanbul": {"coords": (29.0, 41.0), "population": 15840000},
    "Ankara": {"coords": (32.85, 39.93), "population": 5747325},
    "İzmir": {"coords": (27.14, 38.42), "population": 4425789},
    "Bursa": {"coords": (29.06, 40.18), "population": 3194720},
    "Antalya": {"coords": (30.71, 36.89), "population": 2619832},
}


class MapDiagramGenerator:
    """
    Generates ÖSYM-style maps and diagrams in SVG format.

    Supported diagram types:
    - Geographic Maps: Turkey regions, cities, continents
    - Process Diagrams: Flowcharts, cycles, system diagrams
    - Classification Diagrams: Trees, Venn diagrams, matrices, org charts
    - Timeline Diagrams: Horizontal/vertical historical timelines
    """

    def __init__(self):
        """Initialize generator with ÖSYM styling."""
        self.fig_size = (10, 7)  # ÖSYM standard size
        plt.style.use("default")
        plt.rcParams.update(OSYM_DIAGRAM_STYLE)

    def generate_diagram(
        self,
        diagram_type: Literal[
            "geographic_map", "process_diagram", "classification_diagram", "timeline"
        ],
        diagram_subtype: str,
        content: Dict[str, Any],
        labels: Optional[Dict[str, str]] = None,
        show_legend: bool = True,
    ) -> Dict:
        """
        Generate map or diagram in SVG format.

        Args:
            diagram_type: Type of diagram (geographic_map, process_diagram, classification_diagram, timeline)
            diagram_subtype: Specific subtype (e.g., "turkey_regions", "flowchart", "venn_diagram")
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
                "generated_at": datetime.utcnow().isoformat(),
                **metadata,
            },
        }

    # ==================== GEOGRAPHIC MAPS ====================

    def _generate_geographic_map(
        self,
        subtype: str,
        content: Dict[str, Any],
        labels: Optional[Dict[str, str]],
        show_legend: bool,
    ) -> Tuple[str, Dict]:
        """Generate geographic map (Turkey regions, cities, continents)."""

        if subtype == "turkey_regions":
            return self._generate_turkey_regions_map(content, show_legend)
        elif subtype == "turkey_cities":
            return self._generate_turkey_cities_map(content)
        elif subtype == "continents":
            return self._generate_continents_map(content)
        else:
            raise ValueError(f"Unknown geographic map subtype: {subtype}")

    def _generate_turkey_regions_map(
        self, content: Dict[str, Any], show_legend: bool
    ) -> Tuple[str, Dict]:
        """Generate Turkey regions map with 7 geographical regions."""

        fig, ax = plt.subplots(figsize=self.fig_size)
        ax.set_aspect("equal")
        ax.axis("off")

        # Title
        title = content.get("title", "Türkiye Coğrafi Bölgeleri")
        ax.set_title(title, fontsize=14, fontweight="bold", pad=20)

        # Highlight regions (if specified)
        highlight_regions = content.get("highlight_regions", [])

        # Draw regions as simplified rectangles
        region_colors = {}
        for i, (region_name, region_data) in enumerate(TURKEY_REGIONS.items()):
            bbox = region_data["bbox"]
            (x1, y1), (x2, y2) = bbox

            # Color: highlighted regions in gray, others in light gray
            if region_name in highlight_regions:
                facecolor = "#666666"
                edgecolor = "black"
                linewidth = 2.5
            else:
                facecolor = "#e0e0e0"
                edgecolor = "black"
                linewidth = 1.5

            region_colors[region_name] = facecolor

            # Draw region rectangle
            rect = patches.Rectangle(
                (x1, y1),
                x2 - x1,
                y2 - y1,
                linewidth=linewidth,
                edgecolor=edgecolor,
                facecolor=facecolor,
            )
            ax.add_patch(rect)

            # Region label
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            ax.text(
                center_x,
                center_y,
                region_name,
                ha="center",
                va="center",
                fontsize=10,
                fontweight="bold",
                color="white" if region_name in highlight_regions else "black",
            )

        # Set limits
        ax.set_xlim(25, 46)
        ax.set_ylim(35.5, 42.5)

        # Legend
        if show_legend and highlight_regions:
            legend_elements = [
                patches.Patch(
                    facecolor="#666666", edgecolor="black", label="Vurgulanan Bölge"
                ),
                patches.Patch(
                    facecolor="#e0e0e0", edgecolor="black", label="Diğer Bölgeler"
                ),
            ]
            ax.legend(
                handles=legend_elements,
                loc="upper left",
                frameon=True,
                fancybox=False,
                edgecolor="black",
            )

        # Convert to SVG
        svg_content = self._fig_to_svg(fig)
        plt.close(fig)

        metadata = {
            "description": f"{title} - {len(highlight_regions)} bölge vurgulanmış"
            if highlight_regions
            else title,
            "regions_count": 7,
            "highlighted_regions": highlight_regions,
        }

        return svg_content, metadata

    def _generate_turkey_cities_map(self, content: Dict[str, Any]) -> Tuple[str, Dict]:
        """Generate Turkey cities map with major city markers."""

        fig, ax = plt.subplots(figsize=self.fig_size)
        ax.set_aspect("equal")
        ax.axis("off")

        # Title
        title = content.get("title", "Türkiye Büyük Şehirleri")
        ax.set_title(title, fontsize=14, fontweight="bold", pad=20)

        # Draw Turkey outline (simplified)
        turkey_outline = patches.Rectangle(
            (26, 36), 19, 6, linewidth=2, edgecolor="black", facecolor="#f5f5f5"
        )
        ax.add_patch(turkey_outline)

        # Cities to display
        cities_to_show = content.get("cities", list(TURKEY_MAJOR_CITIES.keys())[:5])

        # Plot cities
        for city_name in cities_to_show:
            if city_name in TURKEY_MAJOR_CITIES:
                city_data = TURKEY_MAJOR_CITIES[city_name]
                lon, lat = city_data["coords"]

                # City marker (circle)
                circle = Circle(
                    (lon, lat),
                    0.3,
                    facecolor="black",
                    edgecolor="black",
                    linewidth=1.5,
                    zorder=3,
                )
                ax.add_patch(circle)

                # City label
                ax.text(
                    lon,
                    lat + 0.5,
                    city_name,
                    ha="center",
                    va="bottom",
                    fontsize=10,
                    fontweight="bold",
                    zorder=4,
                )

        # Set limits
        ax.set_xlim(25, 46)
        ax.set_ylim(35.5, 42.5)

        # Convert to SVG
        svg_content = self._fig_to_svg(fig)
        plt.close(fig)

        metadata = {
            "description": f"{title} - {len(cities_to_show)} şehir gösterilmiş",
            "cities_count": len(cities_to_show),
            "cities": cities_to_show,
        }

        return svg_content, metadata

    def _generate_continents_map(self, content: Dict[str, Any]) -> Tuple[str, Dict]:
        """Generate world map with continents (simplified)."""

        fig, ax = plt.subplots(figsize=self.fig_size)
        ax.set_aspect("equal")
        ax.axis("off")

        # Title
        title = content.get("title", "Dünya Kıtaları")
        ax.set_title(title, fontsize=14, fontweight="bold", pad=20)

        # Simplified continents (very simplified shapes)
        continents = {
            "Asya": {"bbox": (70, 10, 70, 50), "label_pos": (105, 30)},
            "Avrupa": {"bbox": (10, 35, 40, 35), "label_pos": (30, 52.5)},
            "Afrika": {"bbox": (15, -35, 40, 50), "label_pos": (35, 7.5)},
            "Kuzey Amerika": {"bbox": (-130, 15, 60, 55), "label_pos": (-100, 42.5)},
            "Güney Amerika": {"bbox": (-80, -55, 35, 55), "label_pos": (-62.5, -27.5)},
            "Avustralya": {"bbox": (113, -39, 40, 22), "label_pos": (133, -28)},
        }

        highlight_continents = content.get("highlight_continents", [])

        for continent_name, continent_data in continents.items():
            x, y, width, height = continent_data["bbox"]
            label_x, label_y = continent_data["label_pos"]

            # Color
            if continent_name in highlight_continents:
                facecolor = "#666666"
                edgecolor = "black"
                linewidth = 2.5
                text_color = "white"
            else:
                facecolor = "#e0e0e0"
                edgecolor = "black"
                linewidth = 1.5
                text_color = "black"

            # Draw continent
            rect = patches.Rectangle(
                (x, y),
                width,
                height,
                linewidth=linewidth,
                edgecolor=edgecolor,
                facecolor=facecolor,
            )
            ax.add_patch(rect)

            # Continent label
            ax.text(
                label_x,
                label_y,
                continent_name,
                ha="center",
                va="center",
                fontsize=9,
                fontweight="bold",
                color=text_color,
            )

        # Set limits
        ax.set_xlim(-170, 170)
        ax.set_ylim(-60, 80)

        # Convert to SVG
        svg_content = self._fig_to_svg(fig)
        plt.close(fig)

        metadata = {
            "description": title,
            "continents_count": 6,
            "highlighted_continents": highlight_continents,
        }

        return svg_content, metadata

    # ==================== PROCESS DIAGRAMS ====================

    def _generate_process_diagram(
        self, subtype: str, content: Dict[str, Any], labels: Optional[Dict[str, str]]
    ) -> Tuple[str, Dict]:
        """Generate process diagram (flowchart, cycle, system)."""

        if subtype == "flowchart":
            return self._generate_flowchart(content)
        elif subtype == "cycle_diagram":
            return self._generate_cycle_diagram(content)
        elif subtype == "system_diagram":
            return self._generate_system_diagram(content)
        else:
            raise ValueError(f"Unknown process diagram subtype: {subtype}")

    def _generate_flowchart(self, content: Dict[str, Any]) -> Tuple[str, Dict]:
        """Generate flowchart with nodes and edges."""

        fig, ax = plt.subplots(figsize=(9, 11))
        ax.set_aspect("equal")
        ax.axis("off")

        # Title
        title = content.get("title", "Akış Diyagramı")
        ax.set_title(title, fontsize=14, fontweight="bold", pad=20)

        # Nodes
        nodes = content.get("nodes", [])

        # Draw nodes
        node_positions = {}
        for i, node in enumerate(nodes):
            node_id = node.get("id", f"node_{i}")
            node_type = node.get("type", "rectangle")  # oval, rectangle, diamond
            node_text = node.get("text", "")
            x = node.get("x", 5)
            y = node.get("y", 10 - i * 2)
            width = node.get("width", 3)
            height = node.get("height", 1.2)

            node_positions[node_id] = (x, y)

            if node_type == "oval":
                # Start/End node
                ellipse = patches.Ellipse(
                    (x, y),
                    width,
                    height,
                    facecolor="white",
                    edgecolor="black",
                    linewidth=2,
                )
                ax.add_patch(ellipse)
            elif node_type == "diamond":
                # Decision node
                diamond_points = [
                    (x, y + height / 2),
                    (x + width / 2, y),
                    (x, y - height / 2),
                    (x - width / 2, y),
                ]
                diamond = patches.Polygon(
                    diamond_points, facecolor="white", edgecolor="black", linewidth=2
                )
                ax.add_patch(diamond)
            else:
                # Process node (rectangle)
                rect = patches.Rectangle(
                    (x - width / 2, y - height / 2),
                    width,
                    height,
                    facecolor="white",
                    edgecolor="black",
                    linewidth=2,
                )
                ax.add_patch(rect)

            # Node text
            ax.text(
                x,
                y,
                node_text,
                ha="center",
                va="center",
                fontsize=9,
                fontweight="bold",
                wrap=True,
            )

        # Edges
        edges = content.get("edges", [])
        for edge in edges:
            from_id = edge.get("from")
            to_id = edge.get("to")
            edge_label = edge.get("label", "")

            if from_id in node_positions and to_id in node_positions:
                x1, y1 = node_positions[from_id]
                x2, y2 = node_positions[to_id]

                # Arrow
                arrow = FancyArrowPatch(
                    (x1, y1 - 0.7),
                    (x2, y2 + 0.7),
                    arrowstyle="->,head_width=0.4,head_length=0.8",
                    color="black",
                    linewidth=2,
                    zorder=1,
                )
                ax.add_patch(arrow)

                # Edge label
                if edge_label:
                    mid_x = (x1 + x2) / 2
                    mid_y = (y1 + y2) / 2
                    ax.text(
                        mid_x + 0.5,
                        mid_y,
                        edge_label,
                        ha="left",
                        va="center",
                        fontsize=8,
                        style="italic",
                    )

        # Set limits
        ax.set_xlim(0, 10)
        ax.set_ylim(-1, 11)

        # Convert to SVG
        svg_content = self._fig_to_svg(fig)
        plt.close(fig)

        metadata = {
            "description": title,
            "nodes_count": len(nodes),
            "edges_count": len(edges),
        }

        return svg_content, metadata

    def _generate_cycle_diagram(self, content: Dict[str, Any]) -> Tuple[str, Dict]:
        """Generate cycle diagram (circular process)."""

        fig, ax = plt.subplots(figsize=(9, 9))
        ax.set_aspect("equal")
        ax.axis("off")

        # Title
        title = content.get("title", "Döngü Diyagramı")
        ax.set_title(title, fontsize=14, fontweight="bold", pad=20)

        # Steps
        steps = content.get("steps", [])
        num_steps = len(steps)

        # Circle parameters
        center_x, center_y = 5, 5
        radius = 3

        # Draw steps in circle
        for i, step in enumerate(steps):
            angle = 2 * np.pi * i / num_steps - np.pi / 2  # Start at top

            # Step position
            x = center_x + radius * np.cos(angle)
            y = center_y + radius * np.sin(angle)

            # Step box
            box = FancyBboxPatch(
                (x - 1, y - 0.4),
                2,
                0.8,
                boxstyle="round,pad=0.1",
                facecolor="white",
                edgecolor="black",
                linewidth=2,
            )
            ax.add_patch(box)

            # Step text
            step_text = step.get("text", f"Adım {i+1}")
            ax.text(
                x, y, step_text, ha="center", va="center", fontsize=9, fontweight="bold"
            )

            # Arrow to next step
            next_angle = 2 * np.pi * ((i + 1) % num_steps) / num_steps - np.pi / 2
            next_x = center_x + radius * np.cos(next_angle)
            next_y = center_y + radius * np.sin(next_angle)

            # Draw curved arrow
            arrow_start_x = x + 0.9 * np.cos(angle)
            arrow_start_y = y + 0.9 * np.cos(angle)
            arrow_end_x = next_x - 0.9 * np.cos(next_angle)
            arrow_end_y = next_y - 0.9 * np.cos(next_angle)

            ax.annotate(
                "",
                xy=(next_x - 1 * np.cos(next_angle), next_y - 0.5 * np.sin(next_angle)),
                xytext=(x + 1 * np.cos(angle), y + 0.5 * np.sin(angle)),
                arrowprops=dict(
                    arrowstyle="->,head_width=0.4,head_length=0.6",
                    color="black",
                    linewidth=2,
                    connectionstyle="arc3,rad=.3",
                ),
            )

        # Set limits
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)

        # Convert to SVG
        svg_content = self._fig_to_svg(fig)
        plt.close(fig)

        metadata = {"description": title, "steps_count": num_steps}

        return svg_content, metadata

    def _generate_system_diagram(self, content: Dict[str, Any]) -> Tuple[str, Dict]:
        """Generate system diagram (components and interactions)."""

        fig, ax = plt.subplots(figsize=self.fig_size)
        ax.set_aspect("equal")
        ax.axis("off")

        # Title
        title = content.get("title", "Sistem Diyagramı")
        ax.set_title(title, fontsize=14, fontweight="bold", pad=20)

        # Components
        components = content.get("components", [])

        # Draw components
        component_positions = {}
        for comp in components:
            comp_id = comp.get("id")
            comp_text = comp.get("text", "")
            x = comp.get("x", 5)
            y = comp.get("y", 5)
            width = comp.get("width", 2.5)
            height = comp.get("height", 1.5)

            component_positions[comp_id] = (x, y)

            # Component box
            rect = patches.Rectangle(
                (x - width / 2, y - height / 2),
                width,
                height,
                facecolor="#f0f0f0",
                edgecolor="black",
                linewidth=2,
            )
            ax.add_patch(rect)

            # Component text
            ax.text(
                x,
                y,
                comp_text,
                ha="center",
                va="center",
                fontsize=10,
                fontweight="bold",
            )

        # Connections
        connections = content.get("connections", [])
        for conn in connections:
            from_id = conn.get("from")
            to_id = conn.get("to")
            conn_label = conn.get("label", "")

            if from_id in component_positions and to_id in component_positions:
                x1, y1 = component_positions[from_id]
                x2, y2 = component_positions[to_id]

                # Double-headed arrow (bidirectional)
                arrow = FancyArrowPatch(
                    (x1, y1),
                    (x2, y2),
                    arrowstyle="<->,head_width=0.4,head_length=0.6",
                    color="black",
                    linewidth=1.5,
                    zorder=1,
                )
                ax.add_patch(arrow)

                # Connection label
                if conn_label:
                    mid_x = (x1 + x2) / 2
                    mid_y = (y1 + y2) / 2
                    ax.text(
                        mid_x,
                        mid_y + 0.3,
                        conn_label,
                        ha="center",
                        va="bottom",
                        fontsize=8,
                        style="italic",
                        bbox=dict(
                            boxstyle="round,pad=0.3",
                            facecolor="white",
                            edgecolor="none",
                        ),
                    )

        # Set limits
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 7)

        # Convert to SVG
        svg_content = self._fig_to_svg(fig)
        plt.close(fig)

        metadata = {
            "description": title,
            "components_count": len(components),
            "connections_count": len(connections),
        }

        return svg_content, metadata

    # ==================== CLASSIFICATION DIAGRAMS ====================

    def _generate_classification_diagram(
        self, subtype: str, content: Dict[str, Any], labels: Optional[Dict[str, str]]
    ) -> Tuple[str, Dict]:
        """Generate classification diagram (tree, Venn, matrix, org chart)."""

        if subtype == "tree_diagram":
            return self._generate_tree_diagram(content)
        elif subtype == "venn_diagram":
            return self._generate_venn_diagram(content)
        elif subtype == "matrix_diagram":
            return self._generate_matrix_diagram(content)
        elif subtype == "organizational_chart":
            return self._generate_organizational_chart(content)
        else:
            raise ValueError(f"Unknown classification diagram subtype: {subtype}")

    def _generate_tree_diagram(self, content: Dict[str, Any]) -> Tuple[str, Dict]:
        """Generate tree diagram (hierarchical classification)."""

        fig, ax = plt.subplots(figsize=(10, 8))
        ax.set_aspect("equal")
        ax.axis("off")

        # Title
        title = content.get("title", "Sınıflandırma Ağacı")
        ax.set_title(title, fontsize=14, fontweight="bold", pad=20)

        # Tree structure
        tree_data = content.get("tree", {})
        root = tree_data.get("root", "Kök")
        levels = tree_data.get("levels", [])

        # Draw root
        root_x, root_y = 5, 7
        root_box = FancyBboxPatch(
            (root_x - 1.5, root_y - 0.4),
            3,
            0.8,
            boxstyle="round,pad=0.1",
            facecolor="#d0d0d0",
            edgecolor="black",
            linewidth=2,
        )
        ax.add_patch(root_box)
        ax.text(
            root_x,
            root_y,
            root,
            ha="center",
            va="center",
            fontsize=11,
            fontweight="bold",
        )

        # Draw levels
        current_y = root_y - 2
        for level_idx, level in enumerate(levels):
            level_nodes = level.get("nodes", [])
            num_nodes = len(level_nodes)
            spacing = 8 / (num_nodes + 1)

            for i, node_text in enumerate(level_nodes):
                node_x = 1 + (i + 1) * spacing
                node_y = current_y

                # Node box
                node_box = FancyBboxPatch(
                    (node_x - 0.8, node_y - 0.35),
                    1.6,
                    0.7,
                    boxstyle="round,pad=0.08",
                    facecolor="white",
                    edgecolor="black",
                    linewidth=1.5,
                )
                ax.add_patch(node_box)
                ax.text(node_x, node_y, node_text, ha="center", va="center", fontsize=9)

                # Line from parent to child
                parent_x = root_x if level_idx == 0 else 5  # Simplified
                parent_y = (
                    root_y - 0.4
                    if level_idx == 0
                    else root_y - 2 - (level_idx - 1) * 2 - 0.35
                )

                line = Line2D(
                    [parent_x, node_x],
                    [parent_y, node_y + 0.35],
                    color="black",
                    linewidth=1.5,
                )
                ax.add_line(line)

            current_y -= 2

        # Set limits
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 8)

        # Convert to SVG
        svg_content = self._fig_to_svg(fig)
        plt.close(fig)

        metadata = {
            "description": title,
            "levels_count": len(levels) + 1,  # +1 for root
            "total_nodes": 1 + sum(len(level.get("nodes", [])) for level in levels),
        }

        return svg_content, metadata

    def _generate_venn_diagram(self, content: Dict[str, Any]) -> Tuple[str, Dict]:
        """Generate Venn diagram (2 or 3 sets)."""

        fig, ax = plt.subplots(figsize=(9, 8))
        ax.set_aspect("equal")
        ax.axis("off")

        # Title
        title = content.get("title", "Venn Diyagramı")
        ax.set_title(title, fontsize=14, fontweight="bold", pad=20)

        # Sets
        sets = content.get("sets", [])
        num_sets = len(sets)

        if num_sets == 2:
            # 2-set Venn diagram
            set1, set2 = sets[0], sets[1]

            # Circles
            circle1 = Circle(
                (4, 4), 2, facecolor="none", edgecolor="black", linewidth=2.5
            )
            circle2 = Circle(
                (6, 4), 2, facecolor="none", edgecolor="black", linewidth=2.5
            )
            ax.add_patch(circle1)
            ax.add_patch(circle2)

            # Labels
            ax.text(
                3,
                6.5,
                set1.get("label", "A"),
                ha="center",
                va="center",
                fontsize=12,
                fontweight="bold",
            )
            ax.text(
                7,
                6.5,
                set2.get("label", "B"),
                ha="center",
                va="center",
                fontsize=12,
                fontweight="bold",
            )

            # Elements
            ax.text(
                2.5,
                4,
                "\n".join(set1.get("only", [])),
                ha="center",
                va="center",
                fontsize=9,
            )
            ax.text(
                7.5,
                4,
                "\n".join(set2.get("only", [])),
                ha="center",
                va="center",
                fontsize=9,
            )
            ax.text(
                5,
                4,
                "\n".join(content.get("intersection", [])),
                ha="center",
                va="center",
                fontsize=9,
                fontweight="bold",
            )

            ax.set_xlim(0, 10)
            ax.set_ylim(1, 8)

        elif num_sets == 3:
            # 3-set Venn diagram
            set1, set2, set3 = sets[0], sets[1], sets[2]

            # Circles
            circle1 = Circle(
                (4, 5), 1.8, facecolor="none", edgecolor="black", linewidth=2.5
            )
            circle2 = Circle(
                (6, 5), 1.8, facecolor="none", edgecolor="black", linewidth=2.5
            )
            circle3 = Circle(
                (5, 3.5), 1.8, facecolor="none", edgecolor="black", linewidth=2.5
            )
            ax.add_patch(circle1)
            ax.add_patch(circle2)
            ax.add_patch(circle3)

            # Labels
            ax.text(
                3,
                6.9,
                set1.get("label", "A"),
                ha="center",
                va="center",
                fontsize=12,
                fontweight="bold",
            )
            ax.text(
                7,
                6.9,
                set2.get("label", "B"),
                ha="center",
                va="center",
                fontsize=12,
                fontweight="bold",
            )
            ax.text(
                5,
                1.5,
                set3.get("label", "C"),
                ha="center",
                va="center",
                fontsize=12,
                fontweight="bold",
            )

            ax.set_xlim(1, 9)
            ax.set_ylim(0.5, 7.5)

        # Convert to SVG
        svg_content = self._fig_to_svg(fig)
        plt.close(fig)

        metadata = {"description": title, "sets_count": num_sets}

        return svg_content, metadata

    def _generate_matrix_diagram(self, content: Dict[str, Any]) -> Tuple[str, Dict]:
        """Generate matrix diagram (2x2 or 3x3)."""

        fig, ax = plt.subplots(figsize=(9, 9))
        ax.set_aspect("equal")
        ax.axis("off")

        # Title
        title = content.get("title", "Matris Diyagramı")
        ax.set_title(title, fontsize=14, fontweight="bold", pad=20)

        # Matrix data
        rows = content.get("rows", 2)
        cols = content.get("cols", 2)
        cells = content.get("cells", {})

        # Draw matrix
        cell_width = 3
        cell_height = 3
        start_x = 2
        start_y = 1

        for i in range(rows):
            for j in range(cols):
                x = start_x + j * cell_width
                y = start_y + (rows - 1 - i) * cell_height

                # Cell rectangle
                rect = patches.Rectangle(
                    (x, y),
                    cell_width,
                    cell_height,
                    facecolor="white",
                    edgecolor="black",
                    linewidth=2,
                )
                ax.add_patch(rect)

                # Cell content
                cell_key = f"{i},{j}"
                cell_text = cells.get(cell_key, "")
                ax.text(
                    x + cell_width / 2,
                    y + cell_height / 2,
                    cell_text,
                    ha="center",
                    va="center",
                    fontsize=10,
                    wrap=True,
                )

        # Axis labels
        x_label = content.get("x_label", "X Ekseni")
        y_label = content.get("y_label", "Y Ekseni")

        ax.text(
            start_x + cols * cell_width / 2,
            start_y - 0.5,
            x_label,
            ha="center",
            va="top",
            fontsize=11,
            fontweight="bold",
        )
        ax.text(
            start_x - 0.5,
            start_y + rows * cell_height / 2,
            y_label,
            ha="right",
            va="center",
            fontsize=11,
            fontweight="bold",
            rotation=90,
        )

        # Set limits
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)

        # Convert to SVG
        svg_content = self._fig_to_svg(fig)
        plt.close(fig)

        metadata = {"description": title, "dimensions": f"{rows}x{cols}"}

        return svg_content, metadata

    def _generate_organizational_chart(
        self, content: Dict[str, Any]
    ) -> Tuple[str, Dict]:
        """Generate organizational chart (hierarchy)."""

        # Similar to tree diagram but with specific org chart styling
        # For brevity, reusing tree diagram logic with different styling
        return self._generate_tree_diagram(content)

    # ==================== TIMELINE DIAGRAMS ====================

    def _generate_timeline(
        self, subtype: str, content: Dict[str, Any], labels: Optional[Dict[str, str]]
    ) -> Tuple[str, Dict]:
        """Generate timeline diagram (horizontal or vertical)."""

        if subtype == "horizontal_timeline":
            return self._generate_horizontal_timeline(content)
        elif subtype == "vertical_timeline":
            return self._generate_vertical_timeline(content)
        else:
            raise ValueError(f"Unknown timeline subtype: {subtype}")

    def _generate_horizontal_timeline(
        self, content: Dict[str, Any]
    ) -> Tuple[str, Dict]:
        """Generate horizontal timeline."""

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.set_aspect("auto")
        ax.axis("off")

        # Title
        title = content.get("title", "Zaman Çizelgesi")
        ax.set_title(title, fontsize=14, fontweight="bold", pad=20)

        # Events
        events = content.get("events", [])
        num_events = len(events)

        # Timeline line
        ax.plot([1, 11], [3, 3], "k-", linewidth=3)

        # Events
        spacing = 10 / (num_events + 1)
        for i, event in enumerate(events):
            x = 1 + (i + 1) * spacing
            y = 3

            year = event.get("year", "")
            event_text = event.get("event", "")

            # Event marker
            circle = Circle(
                (x, y), 0.15, facecolor="black", edgecolor="black", zorder=3
            )
            ax.add_patch(circle)

            # Year (below line)
            ax.text(
                x,
                y - 0.5,
                str(year),
                ha="center",
                va="top",
                fontsize=11,
                fontweight="bold",
            )

            # Event text (above line)
            ax.text(
                x,
                y + 0.5,
                event_text,
                ha="center",
                va="bottom",
                fontsize=9,
                wrap=True,
                rotation=0,
            )

        # Set limits
        ax.set_xlim(0, 12)
        ax.set_ylim(0, 6)

        # Convert to SVG
        svg_content = self._fig_to_svg(fig)
        plt.close(fig)

        metadata = {
            "description": title,
            "events_count": num_events,
            "time_span": f"{events[0]['year']} - {events[-1]['year']}"
            if events
            else "N/A",
        }

        return svg_content, metadata

    def _generate_vertical_timeline(self, content: Dict[str, Any]) -> Tuple[str, Dict]:
        """Generate vertical timeline."""

        fig, ax = plt.subplots(figsize=(8, 11))
        ax.set_aspect("auto")
        ax.axis("off")

        # Title
        title = content.get("title", "Zaman Çizelgesi")
        ax.set_title(title, fontsize=14, fontweight="bold", pad=20)

        # Events
        events = content.get("events", [])
        num_events = len(events)

        # Timeline line
        ax.plot([4, 4], [1, 10], "k-", linewidth=3)

        # Events
        spacing = 9 / (num_events + 1)
        for i, event in enumerate(events):
            x = 4
            y = 10 - (i + 1) * spacing

            year = event.get("year", "")
            event_text = event.get("event", "")

            # Event marker
            circle = Circle(
                (x, y), 0.15, facecolor="black", edgecolor="black", zorder=3
            )
            ax.add_patch(circle)

            # Year (left of line)
            ax.text(
                x - 0.5,
                y,
                str(year),
                ha="right",
                va="center",
                fontsize=11,
                fontweight="bold",
            )

            # Event text (right of line)
            ax.text(
                x + 0.5, y, event_text, ha="left", va="center", fontsize=9, wrap=True
            )

        # Set limits
        ax.set_xlim(0, 8)
        ax.set_ylim(0, 11)

        # Convert to SVG
        svg_content = self._fig_to_svg(fig)
        plt.close(fig)

        metadata = {
            "description": title,
            "events_count": num_events,
            "time_span": f"{events[0]['year']} - {events[-1]['year']}"
            if events
            else "N/A",
        }

        return svg_content, metadata

    # ==================== UTILITY METHODS ====================

    def _fig_to_svg(self, fig) -> str:
        """Convert matplotlib figure to SVG string."""
        svg_io = io.BytesIO()
        fig.savefig(svg_io, format="svg", bbox_inches="tight", pad_inches=0.2)
        svg_io.seek(0)
        svg_content = svg_io.getvalue().decode("utf-8")
        return svg_content


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
        "title": "Türkiye Coğrafi Bölgeleri",
        "highlight_regions": ["Marmara", "Ege"],
    }
    result1 = generator.generate_diagram(
        diagram_type="geographic_map",
        diagram_subtype="turkey_regions",
        content=content1,
        show_legend=True,
    )
    print(f"  ✓ Generated: {result1['metadata']['diagram_subtype']}")
    print(f"  ✓ Description: {result1['metadata']['description']}")
    print(f"  ✓ SVG Size: {len(result1['content'])} chars")
    print()

    # Test 2: Flowchart
    print("[TEST 2] Flowchart")
    content2 = {
        "title": "Su Döngüsü",
        "nodes": [
            {"id": "start", "type": "oval", "text": "Başlangıç", "x": 5, "y": 10},
            {"id": "evap", "type": "rectangle", "text": "Buharlaşma", "x": 5, "y": 8},
            {"id": "cond", "type": "rectangle", "text": "Yoğunlaşma", "x": 5, "y": 6},
            {"id": "precip", "type": "rectangle", "text": "Yağış", "x": 5, "y": 4},
            {"id": "end", "type": "oval", "text": "Döngü Devam Eder", "x": 5, "y": 2},
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
    print(f"  ✓ Generated: {result2['metadata']['diagram_subtype']}")
    print(f"  ✓ Nodes: {result2['metadata']['nodes_count']}")
    print(f"  ✓ SVG Size: {len(result2['content'])} chars")
    print()

    # Test 3: Venn Diagram
    print("[TEST 3] Venn Diagram")
    content3 = {
        "title": "Küme Diyagramı",
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
    print(f"  ✓ Generated: {result3['metadata']['diagram_subtype']}")
    print(f"  ✓ Sets: {result3['metadata']['sets_count']}")
    print(f"  ✓ SVG Size: {len(result3['content'])} chars")
    print()

    # Test 4: Horizontal Timeline
    print("[TEST 4] Horizontal Timeline")
    content4 = {
        "title": "Türkiye Cumhuriyeti Tarihi",
        "events": [
            {"year": 1920, "event": "TBMM Açıldı"},
            {"year": 1923, "event": "Cumhuriyet İlan Edildi"},
            {"year": 1928, "event": "Harf Devrimi"},
            {"year": 1934, "event": "Soyadı Kanunu"},
            {"year": 1945, "event": "BM Üyeliği"},
        ],
    }
    result4 = generator.generate_diagram(
        diagram_type="timeline", diagram_subtype="horizontal_timeline", content=content4
    )
    print(f"  ✓ Generated: {result4['metadata']['diagram_subtype']}")
    print(f"  ✓ Events: {result4['metadata']['events_count']}")
    print(f"  ✓ Time Span: {result4['metadata']['time_span']}")
    print(f"  ✓ SVG Size: {len(result4['content'])} chars")
    print()

    # Test 5: Tree Diagram
    print("[TEST 5] Tree Diagram")
    content5 = {
        "title": "Canlı Sınıflandırması",
        "tree": {
            "root": "Canlılar",
            "levels": [
                {"nodes": ["Hayvanlar", "Bitkiler"]},
                {"nodes": ["Omurgalılar", "Omurgasızlar", "Tohumlu", "Tohumsuz"]},
            ],
        },
    }
    result5 = generator.generate_diagram(
        diagram_type="classification_diagram",
        diagram_subtype="tree_diagram",
        content=content5,
    )
    print(f"  ✓ Generated: {result5['metadata']['diagram_subtype']}")
    print(f"  ✓ Total Nodes: {result5['metadata']['total_nodes']}")
    print(f"  ✓ SVG Size: {len(result5['content'])} chars")
    print()

    print("=" * 70)
    print("All Tests PASSED!")
    print("=" * 70)
