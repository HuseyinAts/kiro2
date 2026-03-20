"""
Tests for IRT 3PL service (FAZ-1.2)
API behavior verified empirically:
  - eap_theta returns (theta, se) tuple
  - select_next_question returns question ID string (not dict)
"""


class TestIRTService3PL:
    """Test IRT 3PL item characteristic curve and CAT selection."""

    def test_icc_output_range(self):
        from services.irt_service_3pl import IRTService3PL

        for theta in [-3.0, -1.0, 0.0, 1.0, 3.0]:
            p = IRTService3PL.icc(theta=theta, a=1.0, b=0.0, c=0.2)
            assert 0.0 <= p <= 1.0, f"ICC out of range: p={p}, theta={theta}"

    def test_icc_c_is_lower_asymptote(self):
        from services.irt_service_3pl import IRTService3PL

        # At very low theta, probability should approach c (guessing)
        p = IRTService3PL.icc(theta=-10.0, a=1.0, b=0.0, c=0.25)
        assert abs(p - 0.25) < 0.01, f"Expected ~0.25 at theta=-10, got {p}"

    def test_icc_at_b_is_midpoint(self):
        from services.irt_service_3pl import IRTService3PL

        c = 0.2
        # At theta=b, probability should be (1+c)/2
        p = IRTService3PL.icc(theta=1.0, a=1.0, b=1.0, c=c)
        expected = (1 + c) / 2
        assert abs(p - expected) < 0.01, f"Expected {expected} at theta=b, got {p}"

    def test_information_positive(self):
        from services.irt_service_3pl import IRTService3PL

        info = IRTService3PL.information(theta=0.0, a=1.5, b=0.0, c=0.2)
        assert info >= 0.0

    def test_eap_theta_returns_tuple(self):
        from services.irt_service_3pl import IRTService3PL

        # eap_theta returns (theta_est, se) tuple
        items = [{"a": 1.0, "b": 0.0, "c": 0.2}] * 3
        responses = [True, True, True]
        result = IRTService3PL.eap_theta(items, responses)
        assert isinstance(result, tuple)
        assert len(result) == 2
        theta, se = result
        assert isinstance(theta, float)
        assert isinstance(se, float)
        assert -4.0 <= theta <= 4.0

    def test_eap_theta_correct_vs_wrong(self):
        from services.irt_service_3pl import IRTService3PL

        items = [{"a": 1.0, "b": 0.0, "c": 0.2}] * 5
        theta_correct, _ = IRTService3PL.eap_theta(items, [True] * 5)
        theta_wrong, _ = IRTService3PL.eap_theta(items, [False] * 5)
        assert theta_correct > theta_wrong

    def test_validate_params_accepts_valid(self):
        from services.irt_service_3pl import IRTService3PL

        assert IRTService3PL.validate_params(a=1.0, b=0.0, c=0.2) is True

    def test_validate_params_rejects_invalid_a_too_low(self):
        from services.irt_service_3pl import IRTService3PL

        assert IRTService3PL.validate_params(a=0.0, b=0.0, c=0.2) is False

    def test_validate_params_rejects_invalid_a_too_high(self):
        from services.irt_service_3pl import IRTService3PL

        assert IRTService3PL.validate_params(a=3.0, b=0.0, c=0.2) is False

    def test_validate_params_rejects_c_too_high(self):
        from services.irt_service_3pl import IRTService3PL

        assert IRTService3PL.validate_params(a=1.0, b=0.0, c=0.5) is False

    def test_select_next_returns_string_id(self):
        """select_next_question returns a string ID, not a dict."""
        from services.irt_service_3pl import IRTService3PL

        item_bank = [
            {"id": "q1", "irt_a": 2.0, "irt_b": 0.0, "irt_c": 0.1},
            {"id": "q2", "irt_a": 0.5, "irt_b": -2.0, "irt_c": 0.25},
        ]
        selected = IRTService3PL.select_next_question(
            theta=0.0, answered_ids=[], item_bank=item_bank
        )
        assert selected is not None
        assert isinstance(selected, str)

    def test_select_next_skips_answered(self):
        from services.irt_service_3pl import IRTService3PL

        item_bank = [
            {"id": "q1", "irt_a": 2.0, "irt_b": 0.0, "irt_c": 0.1},
            {"id": "q2", "irt_a": 1.5, "irt_b": 0.0, "irt_c": 0.2},
        ]
        # Find which is selected first
        first = IRTService3PL.select_next_question(
            theta=0.0, answered_ids=[], item_bank=item_bank
        )
        # Now skip it — should get the other
        second = IRTService3PL.select_next_question(
            theta=0.0, answered_ids=[first], item_bank=item_bank
        )
        assert second is not None
        assert second != first

    def test_select_next_returns_none_when_exhausted(self):
        from services.irt_service_3pl import IRTService3PL

        item_bank = [{"id": "q1", "irt_a": 1.0, "irt_b": 0.0, "irt_c": 0.2}]
        selected = IRTService3PL.select_next_question(
            theta=0.0, answered_ids=["q1"], item_bank=item_bank
        )
        assert selected is None
