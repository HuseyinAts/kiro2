"""
GraphGenerator Service - Phase 2: Graphs

Generates SVG graphs for OSYM-style visual questions.

Supported graph types:
1. Line graphs (Cizgi grafigi) - Trends over time
2. Bar charts (Sutun grafigi) - Comparisons
3. Pie charts (Pasta grafigi) - Proportions
4. Scatter plots (Nokta grafigi) - Correlations
5. Histograms (Histogram) - Distributions

Usage:
    generator = GraphGenerator()
    graph_data = generator.generate_graph(
        graph_type="line",
        data={"x": [1, 2, 3], "y": [10, 20, 15]},
        title="Grafik 1: Hareket-Zaman"
    )
"""

import io
from typing import Any, Literal

import matplotlib

matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

# OSYM Style Configuration
OSYM_STYLE = {
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "black",
    "axes.linewidth": 1.5,
    "axes.grid": True,
    "grid.color": "#e0e0e0",
    "grid.linestyle": "--",
    "grid.linewidth": 0.8,
    "font.family": "DejaVu Sans",
    "font.size": 12,
    "axes.labelsize": 12,
    "axes.titlesize": 14,
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
    "legend.fontsize": 11,
    "text.color": "black",
    "axes.labelcolor": "black",
    "xtick.color": "black",
    "ytick.color": "black",
}


class GraphGenerator:
    """
    Generate OSYM-style graphs in SVG format
    """

    def __init__(self):
        """Initialize GraphGenerator with OSYM styling"""
        plt.style.use("default")
        plt.rcParams.update(OSYM_STYLE)

    def generate_graph(
        self,
        graph_type: Literal["line", "bar", "pie", "scatter", "histogram"],
        data: dict[str, Any],
        title: str,
        x_label: str = "",
        y_label: str = "",
        style: str = "osym",
        width: int = 8,
        height: int = 6,
    ) -> dict:
        """
        Generate graph and return visual_content structure

        Args:
            graph_type: Type of graph ("line", "bar", "pie", "scatter", "histogram")
            data: Graph data (format depends on graph_type)
            title: Graph title (e.g., "Grafik 1: Hareket-Zaman")
            x_label: X-axis label
            y_label: Y-axis label
            style: Style preset ("osym" for OSYM style)
            width: Figure width in inches
            height: Figure height in inches

        Returns:
            Dict with visual_content structure:
            {
                "type": "graph",
                "format": "svg",
                "content": "<svg>...</svg>",
                "data": {...},
                "metadata": {...}
            }
        """
        # Validate graph_type
        valid_types = ["line", "bar", "pie", "scatter", "histogram"]
        if graph_type not in valid_types:
            raise ValueError(f"Invalid graph_type. Must be one of: {valid_types}")

        # Generate graph based on type
        if graph_type == "line":
            svg_content = self._generate_line_graph(
                data, title, x_label, y_label, width, height
            )
        elif graph_type == "bar":
            svg_content = self._generate_bar_chart(
                data, title, x_label, y_label, width, height
            )
        elif graph_type == "pie":
            svg_content = self._generate_pie_chart(data, title, width, height)
        elif graph_type == "scatter":
            svg_content = self._generate_scatter_plot(
                data, title, x_label, y_label, width, height
            )
        elif graph_type == "histogram":
            svg_content = self._generate_histogram(
                data, title, x_label, y_label, width, height
            )
        else:
            raise ValueError(f"Graph type '{graph_type}' not implemented")

        # Prepare metadata
        metadata = {
            "graph_type": graph_type,
            "title": title,
            "x_label": x_label,
            "y_label": y_label,
            "description": self._generate_description(graph_type, data, title),
        }

        # Return visual_content structure
        return {
            "type": "graph",
            "format": "svg",
            "content": svg_content,
            "data": data,
            "metadata": metadata,
        }

    def _generate_line_graph(
        self,
        data: dict,
        title: str,
        x_label: str,
        y_label: str,
        width: int,
        height: int,
    ) -> str:
        """
        Generate line graph (Cizgi Grafigi)

        data format:
        {
            "x": [1, 2, 3, 4, 5],
            "y": [10, 20, 15, 25, 30],
            "lines": [  # Optional: multiple lines
                {"x": [...], "y": [...], "label": "Seri 1"},
                {"x": [...], "y": [...], "label": "Seri 2"}
            ]
        }
        """
        fig, ax = plt.subplots(figsize=(width, height))

        # Single line or multiple lines
        if data.get("lines"):
            # Multiple lines
            for line_data in data["lines"]:
                ax.plot(
                    line_data["x"],
                    line_data["y"],
                    marker="o",
                    linewidth=2,
                    markersize=6,
                    label=line_data.get("label", ""),
                    color="black" if len(data["lines"]) == 1 else None,
                )
            if any(line.get("label") for line in data["lines"]):
                ax.legend(loc="best", frameon=True, fancybox=False, edgecolor="black")
        else:
            # Single line
            ax.plot(
                data["x"],
                data["y"],
                marker="o",
                linewidth=2,
                markersize=6,
                color="black",
            )

        ax.set_title(title, fontweight="bold", pad=15)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.grid(True, linestyle="--", alpha=0.7)

        # Convert to SVG
        return self._fig_to_svg(fig)

    def _generate_bar_chart(
        self,
        data: dict,
        title: str,
        x_label: str,
        y_label: str,
        width: int,
        height: int,
    ) -> str:
        """
        Generate bar chart (Sutun Grafigi)

        data format:
        {
            "categories": ["A", "B", "C", "D"],
            "values": [10, 20, 15, 25],
            "orientation": "vertical"  # or "horizontal"
        }
        """
        fig, ax = plt.subplots(figsize=(width, height))

        categories = data["categories"]
        values = data["values"]
        orientation = data.get("orientation", "vertical")

        if orientation == "horizontal":
            bars = ax.barh(
                categories, values, color="white", edgecolor="black", linewidth=1.5
            )
            ax.set_xlabel(y_label)
            ax.set_ylabel(x_label)
        else:
            bars = ax.bar(
                categories, values, color="white", edgecolor="black", linewidth=1.5
            )
            ax.set_xlabel(x_label)
            ax.set_ylabel(y_label)

        ax.set_title(title, fontweight="bold", pad=15)
        ax.grid(
            True,
            linestyle="--",
            alpha=0.7,
            axis="y" if orientation == "vertical" else "x",
        )

        # Add value labels on bars
        for bar in bars:
            if orientation == "horizontal":
                width_val = bar.get_width()
                ax.text(
                    width_val,
                    bar.get_y() + bar.get_height() / 2,
                    f"{width_val:.1f}",
                    ha="left",
                    va="center",
                    fontsize=10,
                    color="black",
                )
            else:
                height_val = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    height_val,
                    f"{height_val:.1f}",
                    ha="center",
                    va="bottom",
                    fontsize=10,
                    color="black",
                )

        return self._fig_to_svg(fig)

    def _generate_pie_chart(
        self, data: dict, title: str, width: int, height: int
    ) -> str:
        """
        Generate pie chart (Pasta Grafigi)

        data format:
        {
            "labels": ["A", "B", "C"],
            "values": [30, 50, 20],
            "show_percentages": true
        }
        """
        fig, ax = plt.subplots(figsize=(width, height))

        labels = data["labels"]
        values = data["values"]
        show_percentages = data.get("show_percentages", True)

        # Create pie chart with OSYM style (black and white)
        colors = ["white", "#e0e0e0", "#c0c0c0", "#a0a0a0", "#808080", "#606060"]
        explode = [0.05] * len(values)  # Slight separation

        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            autopct="%1.1f%%" if show_percentages else "",
            startangle=90,
            colors=colors[: len(values)],
            wedgeprops={"edgecolor": "black", "linewidth": 1.5},
            textprops={"fontsize": 11, "color": "black"},
            explode=explode,
        )

        # Bold percentage text
        for autotext in autotexts:
            autotext.set_color("black")
            autotext.set_fontweight("bold")
            autotext.set_fontsize(11)

        ax.set_title(title, fontweight="bold", pad=15)
        ax.axis("equal")

        return self._fig_to_svg(fig)

    def _generate_scatter_plot(
        self,
        data: dict,
        title: str,
        x_label: str,
        y_label: str,
        width: int,
        height: int,
    ) -> str:
        """
        Generate scatter plot (Nokta Grafigi)

        data format:
        {
            "x": [1, 2, 3, 4, 5],
            "y": [2.1, 3.9, 6.2, 7.8, 10.1],
            "show_trendline": true  # Optional
        }
        """
        fig, ax = plt.subplots(figsize=(width, height))

        x = np.array(data["x"])
        y = np.array(data["y"])

        # Scatter plot
        ax.scatter(x, y, s=80, c="black", marker="o", edgecolors="black", linewidth=1.5)

        # Optional trendline
        if data.get("show_trendline", False):
            z = np.polyfit(x, y, 1)
            p = np.poly1d(z)
            ax.plot(
                x, p(x), linestyle="--", color="black", linewidth=1.5, label="Trend"
            )
            ax.legend(loc="best", frameon=True, fancybox=False, edgecolor="black")

        ax.set_title(title, fontweight="bold", pad=15)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.grid(True, linestyle="--", alpha=0.7)

        return self._fig_to_svg(fig)

    def _generate_histogram(
        self,
        data: dict,
        title: str,
        x_label: str,
        y_label: str,
        width: int,
        height: int,
    ) -> str:
        """
        Generate histogram (Histogram)

        data format:
        {
            "values": [1, 2, 2, 3, 3, 3, 4, 4, 5],
            "bins": 5,  # Optional, default auto
            "show_curve": false  # Optional: show normal curve
        }
        """
        fig, ax = plt.subplots(figsize=(width, height))

        values = data["values"]
        bins = data.get("bins", "auto")

        # Histogram
        n, bins_edges, patches = ax.hist(
            values,
            bins=bins,
            color="white",
            edgecolor="black",
            linewidth=1.5,
            alpha=1.0,
        )

        ax.set_title(title, fontweight="bold", pad=15)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.grid(True, linestyle="--", alpha=0.7, axis="y")

        return self._fig_to_svg(fig)

    def _fig_to_svg(self, fig) -> str:
        """Convert matplotlib figure to SVG string"""
        svg_buffer = io.StringIO()
        fig.savefig(svg_buffer, format="svg", bbox_inches="tight", dpi=100)
        plt.close(fig)
        svg_content = svg_buffer.getvalue()
        svg_buffer.close()
        return svg_content

    def _generate_description(self, graph_type: str, data: dict, title: str) -> str:
        """Generate accessible description of the graph"""
        descriptions = {
            "line": f"Cizgi grafigi: {title}. Zamanla degisen bir trendi gosterir.",
            "bar": f"Sutun grafigi: {title}. Kategorileri karsilastirir.",
            "pie": f"Pasta grafigi: {title}. Oranlari yuzde dagilimiyla gosterir.",
            "scatter": f"Nokta grafigi: {title}. Iki degisken arasindaki iliskiyi gosterir.",
            "histogram": f"Histogram: {title}. Frekans dagilimini gosterir.",
        }
        return descriptions.get(graph_type, f"Grafik: {title}")


# Example usage and testing
if __name__ == "__main__":
    generator = GraphGenerator()

    # Test 1: Line graph
    print("[TEST 1] Line Graph...")
    line_data = {"x": [0, 1, 2, 3, 4], "y": [0, 10, 20, 15, 25]}
    line_graph = generator.generate_graph(
        graph_type="line",
        data=line_data,
        title="Grafik 1: Hareket-Zaman",
        x_label="Zaman (s)",
        y_label="Hiz (m/s)",
    )
    print(
        f"  [OK] Line graph generated, SVG length: {len(line_graph['content'])} chars"
    )

    # Test 2: Bar chart
    print("[TEST 2] Bar Chart...")
    bar_data = {
        "categories": ["A", "B", "C", "D"],
        "values": [12, 19, 8, 15],
        "orientation": "vertical",
    }
    bar_graph = generator.generate_graph(
        graph_type="bar",
        data=bar_data,
        title="Grafik 2: Sinif Karsilastirmasi",
        x_label="Siniflar",
        y_label="Ogrenci Sayisi",
    )
    print(f"  [OK] Bar chart generated, SVG length: {len(bar_graph['content'])} chars")

    # Test 3: Pie chart
    print("[TEST 3] Pie Chart...")
    pie_data = {
        "labels": ["Kita A", "Kita B", "Kita C"],
        "values": [30, 45, 25],
        "show_percentages": True,
    }
    pie_graph = generator.generate_graph(
        graph_type="pie", data=pie_data, title="Grafik 3: Nufus Dagilimi"
    )
    print(f"  [OK] Pie chart generated, SVG length: {len(pie_graph['content'])} chars")

    # Test 4: Scatter plot
    print("[TEST 4] Scatter Plot...")
    scatter_data = {
        "x": [1, 2, 3, 4, 5],
        "y": [2.1, 3.9, 6.2, 7.8, 10.1],
        "show_trendline": True,
    }
    scatter_graph = generator.generate_graph(
        graph_type="scatter",
        data=scatter_data,
        title="Grafik 4: Korelasyon",
        x_label="Degisken X",
        y_label="Degisken Y",
    )
    print(
        f"  [OK] Scatter plot generated, SVG length: {len(scatter_graph['content'])} chars"
    )

    # Test 5: Histogram
    print("[TEST 5] Histogram...")
    histogram_data = {"values": [1, 2, 2, 3, 3, 3, 4, 4, 4, 4, 5, 5, 6], "bins": 6}
    histogram_graph = generator.generate_graph(
        graph_type="histogram",
        data=histogram_data,
        title="Grafik 5: Frekans Dagilimi",
        x_label="Deger",
        y_label="Frekans",
    )
    print(
        f"  [OK] Histogram generated, SVG length: {len(histogram_graph['content'])} chars"
    )

    print("\n[SUCCESS] All 5 graph types generated successfully!")
