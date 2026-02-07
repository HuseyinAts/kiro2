"""
Process Diagrams Mixin - KIRO2

Generates flowcharts, cycle diagrams, and system diagrams.
"""

from typing import Any, Dict, Optional, Tuple

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from .styles import COLORS
from .utils import close_figure, fig_to_svg, setup_axes


class ProcessDiagramMixin:
    """Mixin for process diagram generation."""

    fig_size: Tuple[int, int]

    def _generate_process_diagram(
        self,
        subtype: str,
        content: Dict[str, Any],
        labels: Optional[Dict[str, str]],
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate process diagram (flowchart, cycle, system).

        Args:
            subtype: Type of process diagram
            content: Content data
            labels: Optional custom labels

        Returns:
            Tuple of (svg_content, metadata)
        """
        if subtype == "flowchart":
            return self._generate_flowchart(content)
        elif subtype == "cycle_diagram":
            return self._generate_cycle_diagram(content)
        elif subtype == "system_diagram":
            return self._generate_system_diagram(content)
        else:
            raise ValueError(f"Unknown process diagram subtype: {subtype}")

    def _generate_flowchart(
        self, content: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate flowchart with nodes and edges."""
        fig, ax = plt.subplots(figsize=(9, 11))
        title = content.get("title", "Akis Diyagrami")
        setup_axes(ax, title)

        nodes = content.get("nodes", [])
        node_positions: Dict[str, Tuple[float, float]] = {}

        # Draw nodes
        for i, node in enumerate(nodes):
            node_id = node.get("id", f"node_{i}")
            node_type = node.get("type", "rectangle")
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
                    diamond_points,
                    facecolor="white",
                    edgecolor="black",
                    linewidth=2,
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

        # Draw edges
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

        svg_content = fig_to_svg(fig)
        close_figure(fig)

        metadata = {
            "description": title,
            "nodes_count": len(nodes),
            "edges_count": len(edges),
        }

        return svg_content, metadata

    def _generate_cycle_diagram(
        self, content: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate cycle diagram (circular process)."""
        fig, ax = plt.subplots(figsize=(9, 9))
        title = content.get("title", "Dongu Diyagrami")
        setup_axes(ax, title)

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
            step_text = step.get("text", f"Adim {i+1}")
            ax.text(
                x,
                y,
                step_text,
                ha="center",
                va="center",
                fontsize=9,
                fontweight="bold",
            )

            # Arrow to next step
            next_angle = 2 * np.pi * ((i + 1) % num_steps) / num_steps - np.pi / 2
            next_x = center_x + radius * np.cos(next_angle)
            next_y = center_y + radius * np.sin(next_angle)

            ax.annotate(
                "",
                xy=(
                    next_x - 1 * np.cos(next_angle),
                    next_y - 0.5 * np.sin(next_angle),
                ),
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

        svg_content = fig_to_svg(fig)
        close_figure(fig)

        metadata = {"description": title, "steps_count": num_steps}

        return svg_content, metadata

    def _generate_system_diagram(
        self, content: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate system diagram (components and interactions)."""
        fig, ax = plt.subplots(figsize=self.fig_size)
        title = content.get("title", "Sistem Diyagrami")
        setup_axes(ax, title)

        components = content.get("components", [])
        component_positions: Dict[str, Tuple[float, float]] = {}

        # Draw components
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
                facecolor=COLORS["component_bg"],
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

        # Draw connections
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

        svg_content = fig_to_svg(fig)
        close_figure(fig)

        metadata = {
            "description": title,
            "components_count": len(components),
            "connections_count": len(connections),
        }

        return svg_content, metadata
