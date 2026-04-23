"""
IRT (Item Response Theory) 4-Parameter Model Implementation
For OSYM question difficulty estimation and calibration

Author: KIRO AI Team
Date: 2025-10-19
"""

from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np


@dataclass
class IRTParameters:
    """IRT 4-Parameter Model Parameters"""

    a: float  # Discrimination parameter (slope)
    b: float  # Difficulty parameter (location)
    c: float  # Guessing parameter (lower asymptote)
    d: float  # Upper asymptote parameter (1 = perfect discrimination)

    def __post_init__(self):
        """Validate parameters"""
        if self.a <= 0:
            raise ValueError("Discrimination (a) must be positive")
        if not 0 <= self.c < 1:
            raise ValueError("Guessing (c) must be in [0, 1)")
        if not self.c < self.d <= 1:
            raise ValueError("Upper asymptote (d) must be in (c, 1]")


class FourParameterIRT:
    """
    4-Parameter Logistic IRT Model (4PL)

    P(theta) = c + (d - c) / (1 + exp(-a(theta - b)))

    Where:
    - theta: Student ability
    - a: Discrimination (how well item differentiates abilities)
    - b: Difficulty (ability level where P = 0.5)
    - c: Guessing (probability of correct answer by guessing)
    - d: Upper asymptote (max probability, usually 1.0)
    """

    def __init__(self, a: float, b: float, c: float = 0.0, d: float = 1.0):
        """
        Initialize 4PL IRT model

        Args:
            a: Discrimination parameter (typically 0.5-2.5)
            b: Difficulty parameter (typically -3 to +3)
            c: Guessing parameter (typically 0.0-0.25 for 4-option MCQ)
            d: Upper asymptote (typically 1.0)
        """
        self.params = IRTParameters(a=a, b=b, c=c, d=d)

    def probability(self, theta: np.ndarray) -> np.ndarray:
        """
        Calculate probability of correct response

        Args:
            theta: Student ability (can be array)

        Returns:
            Probability of correct response
        """
        theta = np.asarray(theta)
        a, b, c, d = self.params.a, self.params.b, self.params.c, self.params.d

        # 4PL formula
        exponent = -a * (theta - b)
        prob = c + (d - c) / (1 + np.exp(exponent))

        return prob

    def information(self, theta: np.ndarray) -> np.ndarray:
        """
        Calculate Fisher Information at given ability level

        Information indicates how much the item contributes to
        precise measurement at different ability levels

        Args:
            theta: Student ability

        Returns:
            Fisher Information
        """
        theta = np.asarray(theta)
        a, b, c, d = self.params.a, self.params.b, self.params.c, self.params.d

        # Calculate probability and its components
        prob = self.probability(theta)
        exponent = -a * (theta - b)
        exp_term = np.exp(exponent)

        # Fisher Information formula for 4PL
        numerator = (a**2) * ((d - c) ** 2) * exp_term
        denominator = (1 + exp_term) ** 2

        # Ensure no division by zero
        q = 1 - prob
        info = numerator / (denominator * prob * q + 1e-10)

        return info

    def likelihood(self, theta: float, response: int) -> float:
        """
        Calculate likelihood of response given ability

        Args:
            theta: Student ability
            response: Response (1=correct, 0=incorrect)

        Returns:
            Likelihood
        """
        prob = self.probability(np.array([theta]))[0]

        if response == 1:
            return prob
        return 1 - prob

    def log_likelihood(self, theta: float, response: int) -> float:
        """Calculate log-likelihood"""
        likelihood = self.likelihood(theta, response)
        return np.log(likelihood + 1e-10)  # Avoid log(0)


class ItemCharacteristicCurve:
    """
    Item Characteristic Curve (ICC) visualization and analysis
    """

    def __init__(self, irt_model: FourParameterIRT):
        """
        Initialize ICC

        Args:
            irt_model: 4PL IRT model
        """
        self.model = irt_model

    def plot(
        self,
        theta_range: tuple[float, float] = (-4, 4),
        num_points: int = 200,
        title: str | None = None,
        save_path: str | None = None,
    ) -> plt.Figure:
        """
        Plot Item Characteristic Curve

        Args:
            theta_range: Range of ability to plot
            num_points: Number of points to plot
            title: Plot title
            save_path: Path to save plot (optional)

        Returns:
            Matplotlib figure
        """
        theta = np.linspace(theta_range[0], theta_range[1], num_points)
        prob = self.model.probability(theta)

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(theta, prob, "b-", linewidth=2, label="ICC")

        # Mark difficulty point (b parameter)
        b = self.model.params.b
        prob_at_b = self.model.probability(np.array([b]))[0]
        ax.plot(b, prob_at_b, "ro", markersize=8, label=f"Difficulty (b={b:.2f})")

        # Mark guessing and upper asymptote
        ax.axhline(
            y=self.model.params.c,
            color="g",
            linestyle="--",
            alpha=0.5,
            label=f"Guessing (c={self.model.params.c:.2f})",
        )
        ax.axhline(
            y=self.model.params.d,
            color="r",
            linestyle="--",
            alpha=0.5,
            label=f"Upper Asymptote (d={self.model.params.d:.2f})",
        )

        ax.set_xlabel("Ability (theta)", fontsize=12)
        ax.set_ylabel("Probability of Correct Response", fontsize=12)
        ax.set_title(title or "Item Characteristic Curve", fontsize=14)
        ax.grid(True, alpha=0.3)
        ax.legend()
        ax.set_ylim(0, 1.05)

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")

        return fig

    def get_discrimination_quality(self) -> str:
        """
        Assess discrimination quality based on 'a' parameter

        Returns:
            Quality rating
        """
        a = self.model.params.a

        if a < 0.5:
            return "Very Low"
        if a < 1.0:
            return "Low"
        if a < 1.5:
            return "Moderate"
        if a < 2.0:
            return "High"
        return "Very High"


class TestInformationFunction:
    """
    Test Information Function (TIF)
    Aggregates information from multiple items
    """

    def __init__(self, irt_models: list[FourParameterIRT]):
        """
        Initialize TIF

        Args:
            irt_models: List of IRT models for test items
        """
        self.models = irt_models

    def total_information(self, theta: np.ndarray) -> np.ndarray:
        """
        Calculate total test information

        Args:
            theta: Ability levels

        Returns:
            Total information across all items
        """
        theta = np.asarray(theta)
        total_info = np.zeros_like(theta, dtype=float)

        for model in self.models:
            total_info += model.information(theta)

        return total_info

    def standard_error(self, theta: np.ndarray) -> np.ndarray:
        """
        Calculate standard error of measurement

        SE(theta) = 1 / sqrt(I(theta))

        Args:
            theta: Ability levels

        Returns:
            Standard error
        """
        info = self.total_information(theta)
        return 1.0 / np.sqrt(info + 1e-10)

    def reliability(self, theta: np.ndarray) -> np.ndarray:
        """
        Calculate test reliability at different ability levels

        Reliability = 1 - SE^2 / Var(theta)

        Args:
            theta: Ability levels

        Returns:
            Reliability coefficients
        """
        se = self.standard_error(theta)
        # Assume variance of theta = 1 (standardized)
        reliability = 1 - se**2
        return reliability

    def plot(
        self,
        theta_range: tuple[float, float] = (-4, 4),
        num_points: int = 200,
        title: str | None = None,
        save_path: str | None = None,
    ) -> plt.Figure:
        """
        Plot Test Information Function

        Args:
            theta_range: Range of ability
            num_points: Number of points
            title: Plot title
            save_path: Save path

        Returns:
            Figure
        """
        theta = np.linspace(theta_range[0], theta_range[1], num_points)
        info = self.total_information(theta)
        se = self.standard_error(theta)

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

        # Plot Information
        ax1.plot(theta, info, "b-", linewidth=2)
        ax1.fill_between(theta, 0, info, alpha=0.3)
        ax1.set_xlabel("Ability (theta)", fontsize=12)
        ax1.set_ylabel("Test Information", fontsize=12)
        ax1.set_title("Test Information Function", fontsize=14)
        ax1.grid(True, alpha=0.3)

        # Plot Standard Error
        ax2.plot(theta, se, "r-", linewidth=2)
        ax2.fill_between(theta, 0, se, alpha=0.3, color="red")
        ax2.set_xlabel("Ability (theta)", fontsize=12)
        ax2.set_ylabel("Standard Error", fontsize=12)
        ax2.set_title("Standard Error of Measurement", fontsize=14)
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")

        return fig

    def get_optimal_measurement_range(
        self, min_reliability: float = 0.7
    ) -> tuple[float, float]:
        """
        Find ability range where test is most reliable

        Args:
            min_reliability: Minimum acceptable reliability

        Returns:
            (min_theta, max_theta) for optimal measurement
        """
        theta = np.linspace(-4, 4, 1000)
        reliability = self.reliability(theta)

        reliable_indices = np.where(reliability >= min_reliability)[0]

        if len(reliable_indices) == 0:
            return (0.0, 0.0)  # No reliable range

        min_theta = theta[reliable_indices[0]]
        max_theta = theta[reliable_indices[-1]]

        return (min_theta, max_theta)


class IRTModel:
    """
    High-level IRT Model Manager
    Combines 4PL model with estimation and calibration utilities
    """

    @staticmethod
    def estimate_initial_parameters(
        responses: list[int], thetas: list[float] | None = None
    ) -> IRTParameters:
        """
        Estimate initial IRT parameters from response data

        Args:
            responses: List of responses (1=correct, 0=incorrect)
            thetas: Student abilities (optional, assumed normal if not provided)

        Returns:
            Estimated parameters
        """
        responses = np.array(responses)
        n = len(responses)

        # Calculate proportion correct
        p_correct = np.mean(responses)

        # Estimate difficulty (b) from proportion correct
        # Assume median ability is 0
        if p_correct > 0.99:
            b = -3.0  # Very easy
        elif p_correct < 0.01:
            b = 3.0  # Very hard
        else:
            # Inverse logit approximation
            b = -np.log(p_correct / (1 - p_correct))

        # Estimate discrimination (a)
        # Higher variance in responses -> higher discrimination
        variance = np.var(responses)
        a = min(2.5, max(0.5, 1.0 + variance))

        # Estimate guessing (c)
        # For 5-option MCQ, theoretical minimum is 0.2
        c = max(0.0, min(0.25, p_correct - 0.7))

        # Upper asymptote usually 1.0
        d = 1.0

        return IRTParameters(a=a, b=b, c=c, d=d)

    @staticmethod
    def create_from_difficulty(difficulty: float) -> FourParameterIRT:
        """
        Create IRT model from difficulty level (0.0-1.0)

        Args:
            difficulty: Difficulty level (0=easy, 1=hard)

        Returns:
            IRT model
        """
        # Map difficulty to b parameter
        # 0.0 -> -2 (very easy)
        # 0.5 -> 0 (medium)
        # 1.0 -> +2 (very hard)
        b = (difficulty - 0.5) * 4

        # Default discrimination
        a = 1.5

        # Guessing for 5-option MCQ
        c = 0.2

        # Upper asymptote
        d = 1.0

        return FourParameterIRT(a=a, b=b, c=c, d=d)

    @staticmethod
    def categorize_difficulty(b: float) -> str:
        """
        Categorize difficulty based on b parameter

        Args:
            b: Difficulty parameter

        Returns:
            Difficulty category
        """
        if b < -1.5:
            return "Very Easy"
        if b < -0.5:
            return "Easy"
        if b < 0.5:
            return "Medium"
        if b < 1.5:
            return "Hard"
        return "Very Hard"
