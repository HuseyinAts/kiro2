"""
Classification Diagrams Mixin - KIRO2

Generates tree diagrams, Venn diagrams, matrix diagrams, and org charts.
"""

from typing import Any

import matplotlib.pyplot as plt
from matplotlib import patches
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyBboxPatch

from .styles import COLORS
from .utils import close_figure, fig_to_svg, setup_axes


class ClassificationMixin:
    """Mixin for classification diagram generation."""

    fig_size: tuple[int, int]

    def _generate_classification_diagram(
        self,
        subtype: str,
        content: dict[str, Any],
        labels: dict[str, str] | None,
    ) -> tuple[str, dict[str, Any]]:
        """
        Generate classification diagram (tree, Venn, matrix, org chart).

        Args:
            subtype: Type of classification diagram
            content: Content data
            labels: Optional custom labels

        Returns:
            Tuple of (svg_content, metadata)
        """
        if subtype == "tree_diagram":
            return self._generate_tree_diagram(content)
        if subtype == "venn_diagram":
            return self._generate_venn_diagram(content)
        if subtype == "matrix_diagram":
            return self._generate_matrix_diagram(content)
        if subtype == "organizational_chart":
            return self._generate_organizational_chart(content)
        raise ValueError(f"Unknown classification diagram subtype: {subtype}")

    def _generate_tree_diagram(
        self, content: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        """Generate tree diagram (hierarchical classification)."""
        fig, ax = plt.subplots(figsize=(10, 8))
        title = content.get("title", "Siniflandirma Agaci")
        setup_axes(ax, title)

        # Tree structure
        tree_data = content.get("tree", {})
        root = tree_data.get("root", "Kok")
        levels = tree_data.get("levels", [])

        # Draw root
        root_x, root_y = 5, 7
        root_box = FancyBboxPatch(
            (root_x - 1.5, root_y - 0.4),
            3,
            0.8,
            boxstyle="round,pad=0.1",
            facecolor=COLORS["root_bg"],
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
                ax.text(
                    node_x,
                    node_y,
                    node_text,
                    ha="center",
                    va="center",
                    fontsize=9,
                )

                # Line from parent to child
                parent_x = root_x if level_idx == 0 else 5
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

        svg_content = fig_to_svg(fig)
        close_figure(fig)

        metadata = {
            "description": title,
            "levels_count": len(levels) + 1,
            "total_nodes": 1 + sum(len(level.get("nodes", [])) for level in levels),
        }

        return svg_content, metadata

    def _generate_venn_diagram(
        self, content: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        """Generate Venn diagram (2 or 3 sets)."""
        fig, ax = plt.subplots(figsize=(9, 8))
        title = content.get("title", "Venn Diyagrami")
        setup_axes(ax, title)

        sets = content.get("sets", [])
        num_sets = len(sets)

        if num_sets == 2:
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

        svg_content = fig_to_svg(fig)
        close_figure(fig)

        metadata = {"description": title, "sets_count": num_sets}

        return svg_content, metadata

    def _generate_matrix_diagram(
        self, content: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        """Generate matrix diagram (2x2 or 3x3)."""
        fig, ax = plt.subplots(figsize=(9, 9))
        title = content.get("title", "Matris Diyagrami")
        setup_axes(ax, title)

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

        svg_content = fig_to_svg(fig)
        close_figure(fig)

        metadata = {"description": title, "dimensions": f"{rows}x{cols}"}

        return svg_content, metadata

    def _generate_organizational_chart(
        self, content: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        """Generate organizational chart (hierarchy)."""
        # Reuse tree diagram logic with org chart styling
        return self._generate_tree_diagram(content)
