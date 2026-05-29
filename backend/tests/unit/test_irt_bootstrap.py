"""IRT cold-start bootstrap prior testleri (TDD)."""

import pytest

from services.irt_bootstrap import difficulty_to_irt


class TestDifficultyToIrt:
    def test_difficulty_levels_monotonic_b(self):
        """b zorluk arttıkça monoton artmalı (VERY_EASY < ... < VERY_HARD)."""
        order = ["VERY_EASY", "EASY", "MEDIUM", "HARD", "VERY_HARD"]
        bs = [difficulty_to_irt(level)["b"] for level in order]
        assert bs == sorted(bs), f"b monoton değil: {bs}"
        assert len(set(bs)) == 5, "her seviye farklı b vermeli"

    def test_medium_base_is_zero(self):
        assert difficulty_to_irt("MEDIUM")["b"] == 0.0

    def test_symmetric_extremes(self):
        assert (
            difficulty_to_irt("VERY_EASY")["b"] == -difficulty_to_irt("VERY_HARD")["b"]
        )

    def test_case_insensitive(self):
        assert difficulty_to_irt("hard")["b"] == difficulty_to_irt("HARD")["b"]

    def test_unknown_and_none_default_to_medium(self):
        assert difficulty_to_irt(None)["b"] == 0.0
        assert difficulty_to_irt("BOGUS")["b"] == 0.0

    def test_guessing_is_one_fifth(self):
        """5 şıklı YKS -> c = 0.20."""
        assert difficulty_to_irt("MEDIUM")["c"] == 0.20

    def test_default_discrimination(self):
        assert difficulty_to_irt("MEDIUM")["a"] == 0.9

    def test_bloom_breaks_medium_bunching(self):
        """Bloom ekseni, aynı MEDIUM kovasındaki soruları farklı b'ye yayar."""
        low = difficulty_to_irt("MEDIUM", bloom_level=1)["b"]
        mid = difficulty_to_irt("MEDIUM", bloom_level=3)["b"]
        high = difficulty_to_irt("MEDIUM", bloom_level=6)["b"]
        assert low < mid < high, f"bloom yayılımı yok: {low}, {mid}, {high}"
        assert mid == 0.0  # bloom=3 nötr

    def test_bloom_step_value(self):
        # (1-3)*0.15 = -0.30
        assert difficulty_to_irt("MEDIUM", bloom_level=1)["b"] == -0.30
        # (6-3)*0.15 = +0.45
        assert difficulty_to_irt("MEDIUM", bloom_level=6)["b"] == 0.45

    def test_b_clamped(self):
        # VERY_HARD (1.8) + bloom çok yüksek teorik taşma -> clamp 3.5 içinde
        b = difficulty_to_irt("VERY_HARD", bloom_level=6)["b"]
        assert -3.5 <= b <= 3.5

    @pytest.mark.parametrize(
        "level", ["VERY_EASY", "EASY", "MEDIUM", "HARD", "VERY_HARD"]
    )
    def test_not_default_irt_params(self, level):
        """Üretilen prior, motorun 'kalibre değil' saydığı (1.0, 0.0, 0.25) default'una eşit olmamalı."""
        p = difficulty_to_irt(level, bloom_level=2)
        assert not (p["a"] == 1.0 and p["b"] == 0.0 and p["c"] == 0.25)
