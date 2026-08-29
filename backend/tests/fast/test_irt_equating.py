from services.irt_equating_service import MeanMeanEquator


def test_calculate_constants():
    # Base scale (Form X) parameters for 3 anchor items
    base_b = [-1.0, 0.0, 1.0]

    # New scale (Form Y) parameters for the same 3 anchor items
    # Let's say New scale is shifted by +0.5 and spread by 2.0
    # b_y = (b_x - B) / A
    # If A=2.0 and B=0.5
    # For b_x = -1.0 -> b_y = (-1.0 - 0.5) / 2 = -0.75
    # For b_x = 0.0 -> b_y = (0.0 - 0.5) / 2 = -0.25
    # For b_x = 1.0 -> b_y = (1.0 - 0.5) / 2 = 0.25
    new_b = [-0.75, -0.25, 0.25]

    A, B = MeanMeanEquator.calculate_constants(base_b, new_b)

    # A should be SD(base_b)/SD(new_b) = 1.0 / 0.5 = 2.0
    # B should be Mean(base_b) - A * Mean(new_b)
    # Mean(base_b) = 0.0
    # Mean(new_b) = -0.25
    # B = 0.0 - (2.0 * -0.25) = 0.5
    assert A == 2.0
    assert B == 0.5


def test_calculate_constants_single_item():
    base_b = [1.5]
    new_b = [0.5]

    A, B = MeanMeanEquator.calculate_constants(base_b, new_b)

    # Fallback to A=1.0, B = 1.5 - 0.5 = 1.0
    assert A == 1.0
    assert B == 1.0


def test_equate_parameters():
    A = 2.0
    B = 0.5

    # Form Y parameter
    a_y = 1.5
    b_y = -0.25
    c_y = 0.20

    equated = MeanMeanEquator.equate_parameters(A, B, a=a_y, b=b_y, c=c_y)

    # a_x = 1.5 / 2.0 = 0.75
    # b_x = 2.0 * (-0.25) + 0.5 = 0.0
    # c_x = 0.20
    assert equated["a"] == 0.75
    assert equated["b"] == 0.0
    assert equated["c"] == 0.20


def test_equate_theta():
    A = 2.0
    B = 0.5

    theta_y = 1.0
    theta_x = MeanMeanEquator.equate_theta(A, B, theta_y)

    # theta_x = 2.0 * 1.0 + 0.5 = 2.5
    assert theta_x == 2.5
