"""
Base Diagram Generator - KIRO2

Abstract base class for diagram generators.
"""

from abc import ABC, abstractmethod
from typing import Any

import matplotlib.pyplot as plt

from .styles import DEFAULT_FIG_SIZE, OSYM_DIAGRAM_STYLE


class BaseDiagramGenerator(ABC):
    """Abstract base class for diagram generators."""

    def __init__(self, fig_size: tuple[int, int] = DEFAULT_FIG_SIZE) -> None:
        """
        Initialize generator with OSYM styling.

        Args:
            fig_size: Figure size tuple (width, height)
        """
        self.fig_size = fig_size
        plt.style.use("default")
        plt.rcParams.update(OSYM_DIAGRAM_STYLE)

    @abstractmethod
    def generate(
        self,
        subtype: str,
        content: dict[str, Any],
        labels: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> tuple[str, dict[str, Any]]:
        """
        Generate diagram SVG and metadata.

        Args:
            subtype: Specific subtype of diagram
            content: Content data for the diagram
            labels: Optional custom labels
            **kwargs: Additional arguments

        Returns:
            Tuple of (svg_content, metadata)
        """

    def create_figure(
        self, figsize: tuple[int, int] | None = None
    ) -> tuple[Any, Any]:
        """
        Create a new matplotlib figure and axes.

        Args:
            figsize: Optional custom figure size

        Returns:
            Tuple of (figure, axes)
        """
        return plt.subplots(figsize=figsize or self.fig_size)
