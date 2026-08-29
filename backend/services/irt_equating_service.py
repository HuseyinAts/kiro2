import numpy as np


class MeanMeanEquator:
    """
    Implements the Mean-Mean Equating method for IRT.
    This method links a new test form (Form Y) to a base test form (Form X)
    using a set of common anchor items.

    Equations:
    A = SD(b_x) / SD(b_y)   -> The scale factor (slope)
    B = Mean(b_x) - A * Mean(b_y)  -> The location shift (intercept)

    Transformed parameters on Base Scale (X):
    a_x' = a_y / A
    b_x' = A * b_y + B
    c_x' = c_y
    theta_x = A * theta_y + B
    """

    @classmethod
    def calculate_constants(
        cls, base_b_values: list[float], new_b_values: list[float]
    ) -> tuple[float, float]:
        """
        Calculates the A and B equating constants based on the difficulty (b) parameters
        of the common anchor items.

        Args:
            base_b_values: List of b parameters of anchor items on the Base scale (Form X)
            new_b_values: List of b parameters of anchor items on the New scale (Form Y)

        Returns:
            Tuple[float, float]: (A, B) constants.
        """
        if len(base_b_values) != len(new_b_values):
            raise ValueError("Base and New lists must have the same length.")
        if len(base_b_values) < 2:
            # If there's only 0 or 1 anchor item, standard deviation is undefined or 0.
            # We fallback to simple location shift (A=1.0) and difference of means (B) if 1 item.
            # If 0 items, A=1.0, B=0.0
            if len(base_b_values) == 1:
                return 1.0, float(base_b_values[0] - new_b_values[0])
            return 1.0, 0.0

        sd_x = np.std(base_b_values, ddof=1)
        sd_y = np.std(new_b_values, ddof=1)

        # Avoid division by zero if all items have the same difficulty
        if sd_y == 0 or sd_x == 0:
            A = 1.0
        else:
            A = float(sd_x / sd_y)

        mean_x = np.mean(base_b_values)
        mean_y = np.mean(new_b_values)

        B = float(mean_x - (A * mean_y))

        return round(A, 4), round(B, 4)

    @classmethod
    def equate_parameters(
        cls, A: float, B: float, a: float = 1.0, b: float = 0.0, c: float = 0.25
    ) -> dict[str, float]:
        """
        Transforms item parameters from the New scale to the Base scale.
        """
        # Protect against A <= 0. In valid IRT, slope should be positive.
        safe_a_constant = A if A > 0 else 1.0

        a_equated = a / safe_a_constant
        b_equated = safe_a_constant * b + B
        c_equated = c  # c (guessing) is scale invariant

        return {
            "a": round(a_equated, 4),
            "b": round(b_equated, 4),
            "c": round(c_equated, 4),
        }

    @classmethod
    def equate_theta(cls, A: float, B: float, theta: float) -> float:
        """
        Transforms student ability (theta) from New scale to Base scale.
        """
        safe_a_constant = A if A > 0 else 1.0
        theta_equated = safe_a_constant * theta + B
        return round(theta_equated, 4)
