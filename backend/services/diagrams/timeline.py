"""
Timeline Diagrams Mixin - KIRO2

Generates horizontal and vertical timeline diagrams.
"""

from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
from matplotlib.patches import Circle

from .utils import close_figure, fig_to_svg


class TimelineMixin:
    """Mixin for timeline diagram generation."""

    fig_size: Tuple[int, int]

    def _generate_timeline(
        self,
        subtype: str,
        content: Dict[str, Any],
        labels: Optional[Dict[str, str]],
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate timeline diagram (horizontal or vertical).

        Args:
            subtype: Type of timeline
            content: Content data
            labels: Optional custom labels

        Returns:
            Tuple of (svg_content, metadata)
        """
        if subtype == "horizontal_timeline":
            return self._generate_horizontal_timeline(content)
        elif subtype == "vertical_timeline":
            return self._generate_vertical_timeline(content)
        else:
            raise ValueError(f"Unknown timeline subtype: {subtype}")

    def _generate_horizontal_timeline(
        self, content: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate horizontal timeline."""
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.set_aspect("auto")
        ax.axis("off")

        title = content.get("title", "Zaman Cizelgesi")
        ax.set_title(title, fontsize=14, fontweight="bold", pad=20)

        events: List[Dict[str, Any]] = content.get("events", [])
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

        svg_content = fig_to_svg(fig)
        close_figure(fig)

        time_span = "N/A"
        if events:
            time_span = f"{events[0]['year']} - {events[-1]['year']}"

        metadata = {
            "description": title,
            "events_count": num_events,
            "time_span": time_span,
        }

        return svg_content, metadata

    def _generate_vertical_timeline(
        self, content: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate vertical timeline."""
        fig, ax = plt.subplots(figsize=(8, 11))
        ax.set_aspect("auto")
        ax.axis("off")

        title = content.get("title", "Zaman Cizelgesi")
        ax.set_title(title, fontsize=14, fontweight="bold", pad=20)

        events: List[Dict[str, Any]] = content.get("events", [])
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
                x + 0.5,
                y,
                event_text,
                ha="left",
                va="center",
                fontsize=9,
                wrap=True,
            )

        # Set limits
        ax.set_xlim(0, 8)
        ax.set_ylim(0, 11)

        svg_content = fig_to_svg(fig)
        close_figure(fig)

        time_span = "N/A"
        if events:
            time_span = f"{events[0]['year']} - {events[-1]['year']}"

        metadata = {
            "description": title,
            "events_count": num_events,
            "time_span": time_span,
        }

        return svg_content, metadata
