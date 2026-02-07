"""
Geographic Maps Mixin - KIRO2

Generates Turkey and world geographic maps.
"""

from typing import Any, Dict, Optional, Tuple

import matplotlib.patches as patches
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

from .styles import COLORS, CONTINENTS, TURKEY_MAJOR_CITIES, TURKEY_REGIONS
from .utils import close_figure, fig_to_svg, setup_axes


class GeographicMapMixin:
    """Mixin for geographic map generation."""

    fig_size: Tuple[int, int]

    def _generate_geographic_map(
        self,
        subtype: str,
        content: Dict[str, Any],
        labels: Optional[Dict[str, str]],
        show_legend: bool,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate geographic map (Turkey regions, cities, continents).

        Args:
            subtype: Type of geographic map
            content: Content data
            labels: Optional custom labels
            show_legend: Whether to show legend

        Returns:
            Tuple of (svg_content, metadata)
        """
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
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate Turkey regions map with 7 geographical regions."""
        fig, ax = plt.subplots(figsize=self.fig_size)
        setup_axes(ax, content.get("title", "Turkiye Cografi Bolgeleri"))

        highlight_regions = content.get("highlight_regions", [])

        # Draw regions as simplified rectangles
        for region_name, region_data in TURKEY_REGIONS.items():
            bbox = region_data["bbox"]
            (x1, y1), (x2, y2) = bbox

            # Color: highlighted regions in gray, others in light gray
            if region_name in highlight_regions:
                facecolor = COLORS["highlighted"]
                linewidth = 2.5
                text_color = "white"
            else:
                facecolor = COLORS["default"]
                linewidth = 1.5
                text_color = "black"

            # Draw region rectangle
            rect = patches.Rectangle(
                (x1, y1),
                x2 - x1,
                y2 - y1,
                linewidth=linewidth,
                edgecolor="black",
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
                color=text_color,
            )

        # Set limits
        ax.set_xlim(25, 46)
        ax.set_ylim(35.5, 42.5)

        # Legend
        if show_legend and highlight_regions:
            legend_elements = [
                patches.Patch(
                    facecolor=COLORS["highlighted"],
                    edgecolor="black",
                    label="Vurgulanan Bolge",
                ),
                patches.Patch(
                    facecolor=COLORS["default"],
                    edgecolor="black",
                    label="Diger Bolgeler",
                ),
            ]
            ax.legend(
                handles=legend_elements,
                loc="upper left",
                frameon=True,
                fancybox=False,
                edgecolor="black",
            )

        svg_content = fig_to_svg(fig)
        close_figure(fig)

        title = content.get("title", "Turkiye Cografi Bolgeleri")
        metadata = {
            "description": f"{title} - {len(highlight_regions)} bolge vurgulanmis"
            if highlight_regions
            else title,
            "regions_count": 7,
            "highlighted_regions": highlight_regions,
        }

        return svg_content, metadata

    def _generate_turkey_cities_map(
        self, content: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate Turkey cities map with major city markers."""
        fig, ax = plt.subplots(figsize=self.fig_size)
        title = content.get("title", "Turkiye Buyuk Sehirleri")
        setup_axes(ax, title)

        # Draw Turkey outline (simplified)
        turkey_outline = patches.Rectangle(
            (26, 36), 19, 6, linewidth=2, edgecolor="black", facecolor=COLORS["light_gray"]
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

        svg_content = fig_to_svg(fig)
        close_figure(fig)

        metadata = {
            "description": f"{title} - {len(cities_to_show)} sehir gosterilmis",
            "cities_count": len(cities_to_show),
            "cities": cities_to_show,
        }

        return svg_content, metadata

    def _generate_continents_map(
        self, content: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate world map with continents (simplified)."""
        fig, ax = plt.subplots(figsize=self.fig_size)
        title = content.get("title", "Dunya Kitalari")
        setup_axes(ax, title)

        highlight_continents = content.get("highlight_continents", [])

        for continent_name, continent_data in CONTINENTS.items():
            x, y, width, height = continent_data["bbox"]
            label_x, label_y = continent_data["label_pos"]

            # Color
            if continent_name in highlight_continents:
                facecolor = COLORS["highlighted"]
                linewidth = 2.5
                text_color = "white"
            else:
                facecolor = COLORS["default"]
                linewidth = 1.5
                text_color = "black"

            # Draw continent
            rect = patches.Rectangle(
                (x, y),
                width,
                height,
                linewidth=linewidth,
                edgecolor="black",
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

        svg_content = fig_to_svg(fig)
        close_figure(fig)

        metadata = {
            "description": title,
            "continents_count": 6,
            "highlighted_continents": highlight_continents,
        }

        return svg_content, metadata
