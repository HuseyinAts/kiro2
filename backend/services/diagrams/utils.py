"""
Diagram Utilities - KIRO2

Helper functions for diagram generation.
"""

import io
import os
import sys
from typing import Any

import matplotlib
import matplotlib.pyplot as plt

# UTF-8 encoding for Windows console (skip during testing to preserve pytest capture)
if hasattr(sys.stdout, "buffer") and os.environ.get("TESTING") != "true":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer") and os.environ.get("TESTING") != "true":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Non-interactive backend
matplotlib.use("Agg")


def fig_to_svg(fig: Any) -> str:
    """
    Convert matplotlib figure to SVG string.

    Args:
        fig: Matplotlib figure object

    Returns:
        SVG content as string
    """
    svg_io = io.BytesIO()
    fig.savefig(svg_io, format="svg", bbox_inches="tight", pad_inches=0.2)
    svg_io.seek(0)
    svg_content = svg_io.getvalue().decode("utf-8")
    return svg_content


def setup_axes(ax: Any, title: str, fontsize: int = 14) -> None:
    """
    Setup axes with common configuration.

    Args:
        ax: Matplotlib axes object
        title: Title for the diagram
        fontsize: Font size for title
    """
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, fontsize=fontsize, fontweight="bold", pad=20)


def close_figure(fig: Any) -> None:
    """
    Properly close matplotlib figure to free memory.

    Args:
        fig: Matplotlib figure object
    """
    plt.close(fig)
