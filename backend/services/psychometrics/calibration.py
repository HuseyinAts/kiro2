"""
IRT Calibration Service
Adaptive and batch calibration for OSYM questions

Author: KIRO AI Team
Date: 2025-10-19
"""

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.optimize import differential_evolution, minimize

from services.psychometrics.irt_model import FourParameterIRT, IRTParameters


@dataclass
class CalibrationResult:
    """Result of IRT calibration"""

    parameters: IRTParameters
    log_likelihood: float
    converged: bool
    iterations: int
    method: str


class IRTCalibrator:
    """
    IRT Parameter Calibration using Maximum Likelihood Estimation
    """

    def __init__(self, method: str = "L-BFGS-B"):
        """
        Initialize calibrator

        Args:
            method: Optimization method ('L-BFGS-B', 'Nelder-Mead', 'differential_evolution')
        """
        self.method = method

    def calibrate(
        self,
        responses: np.ndarray,
        abilities: np.ndarray,
        initial_params: IRTParameters | None = None,
        max_iterations: int = 1000,
    ) -> CalibrationResult:
        """
        Calibrate IRT parameters from response data

        Args:
            responses: Array of responses (1=correct, 0=incorrect)
            abilities: Array of student abilities (theta)
            initial_params: Initial parameter guess (optional)
            max_iterations: Maximum optimization iterations

        Returns:
            Calibration result
        """
        # Validate inputs
        if len(responses) != len(abilities):
            raise ValueError("Responses and abilities must have same length")

        # Set initial parameters
        if initial_params is None:
            initial_params = self._estimate_initial_params(responses, abilities)

        # Initial parameter vector [a, b, c, d]
        x0 = np.array(
            [initial_params.a, initial_params.b, initial_params.c, initial_params.d]
        )

        # Parameter bounds
        bounds = [
            (0.1, 5.0),  # a: discrimination (must be positive)
            (-4.0, 4.0),  # b: difficulty
            (0.0, 0.3),  # c: guessing (max 0.3 for 5-option MCQ)
            (0.7, 1.0),  # d: upper asymptote
        ]

        # Optimize using chosen method
        if self.method == "differential_evolution":
            result = differential_evolution(
                lambda x: self._negative_log_likelihood(x, responses, abilities),
                bounds=bounds,
                maxiter=max_iterations,
                seed=42,
            )
        else:
            result = minimize(
                lambda x: self._negative_log_likelihood(x, responses, abilities),
                x0=x0,
                method=self.method,
                bounds=bounds,
                options={"maxiter": max_iterations},
            )

        # Extract optimized parameters
        a_opt, b_opt, c_opt, d_opt = result.x

        return CalibrationResult(
            parameters=IRTParameters(a=a_opt, b=b_opt, c=c_opt, d=d_opt),
            log_likelihood=-result.fun,  # Convert back from negative
            converged=result.success,
            iterations=result.nit if hasattr(result, "nit") else max_iterations,
            method=self.method,
        )

    def _negative_log_likelihood(
        self, params: np.ndarray, responses: np.ndarray, abilities: np.ndarray
    ) -> float:
        """
        Calculate negative log-likelihood (for minimization)

        Args:
            params: [a, b, c, d]
            responses: Response data
            abilities: Student abilities

        Returns:
            Negative log-likelihood
        """
        a, b, c, d = params

        # Create temporary IRT model
        try:
            model = FourParameterIRT(a=a, b=b, c=c, d=d)
        except ValueError:
            # Invalid parameters, return large penalty
            return 1e10

        # Calculate probabilities
        probs = model.probability(abilities)

        # Avoid log(0) and log(1)
        probs = np.clip(probs, 1e-10, 1 - 1e-10)

        # Log-likelihood
        log_lik = np.sum(
            responses * np.log(probs) + (1 - responses) * np.log(1 - probs)
        )

        return -log_lik  # Return negative for minimization

    def _estimate_initial_params(
        self, responses: np.ndarray, abilities: np.ndarray
    ) -> IRTParameters:
        """
        Estimate initial parameters using simple statistics

        Args:
            responses: Response data
            abilities: Student abilities

        Returns:
            Initial parameter estimates
        """
        # Proportion correct
        p_correct = np.mean(responses)

        # Estimate difficulty (b) using logit transform
        if 0.01 < p_correct < 0.99:
            b_est = -np.log(p_correct / (1 - p_correct))
        elif p_correct <= 0.01:
            b_est = 3.0
        else:
            b_est = -3.0

        # Estimate discrimination from variance
        variance = np.var(responses)
        a_est = 1.0 + variance

        # Guessing parameter (5-option MCQ)
        c_est = 0.2

        # Upper asymptote
        d_est = 1.0

        return IRTParameters(a=a_est, b=b_est, c=c_est, d=d_est)


class AdaptiveCalibrator:
    """
    Adaptive IRT Calibration
    Updates parameters incrementally as new response data arrives
    """

    def __init__(self, initial_params: IRTParameters | None = None):
        """
        Initialize adaptive calibrator

        Args:
            initial_params: Initial parameter estimates
        """
        if initial_params:
            self.params = initial_params
        else:
            # Default parameters for medium difficulty
            self.params = IRTParameters(a=1.5, b=0.0, c=0.2, d=1.0)

        self.response_history: list[tuple[float, int]] = []  # (ability, response)
        self.update_count = 0

    def add_response(self, ability: float, response: int, update_now: bool = True):
        """
        Add new response and optionally update parameters

        Args:
            ability: Student ability
            response: Response (1=correct, 0=incorrect)
            update_now: Whether to update parameters immediately
        """
        self.response_history.append((ability, response))

        if update_now and len(self.response_history) >= 10:
            # Update parameters every 10 responses
            if len(self.response_history) % 10 == 0:
                self.update_parameters()

    def update_parameters(self, method: str = "L-BFGS-B"):
        """
        Update IRT parameters based on accumulated responses

        Args:
            method: Optimization method
        """
        if len(self.response_history) < 5:
            return  # Need minimum data

        # Extract data
        abilities = np.array([ability for ability, _ in self.response_history])
        responses = np.array([response for _, response in self.response_history])

        # Calibrate
        calibrator = IRTCalibrator(method=method)
        result = calibrator.calibrate(
            responses=responses, abilities=abilities, initial_params=self.params
        )

        if result.converged:
            self.params = result.parameters
            self.update_count += 1

    def get_current_model(self) -> FourParameterIRT:
        """Get current IRT model"""
        return FourParameterIRT(
            a=self.params.a, b=self.params.b, c=self.params.c, d=self.params.d
        )

    def get_calibration_stats(self) -> dict[str, Any]:
        """Get calibration statistics"""
        return {
            "total_responses": len(self.response_history),
            "update_count": self.update_count,
            "current_parameters": {
                "a": self.params.a,
                "b": self.params.b,
                "c": self.params.c,
                "d": self.params.d,
            },
            "proportion_correct": (
                np.mean([r for _, r in self.response_history])
                if self.response_history
                else 0.0
            ),
        }


class BatchCalibrator:
    """
    Batch calibration for multiple questions simultaneously
    """

    def __init__(self, num_questions: int):
        """
        Initialize batch calibrator

        Args:
            num_questions: Number of questions to calibrate
        """
        self.num_questions = num_questions
        self.calibrators = [AdaptiveCalibrator() for _ in range(num_questions)]

    def add_student_responses(self, ability: float, responses: list[int]):
        """
        Add responses from one student to all questions

        Args:
            ability: Student ability
            responses: List of responses (one per question)
        """
        if len(responses) != self.num_questions:
            raise ValueError(
                f"Expected {self.num_questions} responses, got {len(responses)}"
            )

        for i, response in enumerate(responses):
            self.calibrators[i].add_response(ability, response, update_now=False)

    def calibrate_all(self, method: str = "L-BFGS-B"):
        """
        Calibrate all questions

        Args:
            method: Optimization method
        """
        for calibrator in self.calibrators:
            calibrator.update_parameters(method=method)

    def get_all_parameters(self) -> list[IRTParameters]:
        """Get parameters for all questions"""
        return [cal.params for cal in self.calibrators]

    def get_summary(self) -> dict[str, Any]:
        """Get calibration summary"""
        all_params = self.get_all_parameters()

        return {
            "num_questions": self.num_questions,
            "avg_discrimination": np.mean([p.a for p in all_params]),
            "avg_difficulty": np.mean([p.b for p in all_params]),
            "difficulty_range": (
                min([p.b for p in all_params]),
                max([p.b for p in all_params]),
            ),
            "total_responses": sum(
                len(cal.response_history) for cal in self.calibrators
            ),
        }
