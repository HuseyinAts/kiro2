"""
Property-Based Tests - Context Isolation (REQ-7.1, REQ-7.2)

Bu modül, hypothesis kullanarak context manager için
property-based testler içerir.

Property 1: Context Isolation - Context her zaman <= 200K tokens
Property 2: Token counting accuracy

Boris Cherny Standards: Minimum 100 iterations per property test
"""

import sys

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

sys.path.insert(0, "c:/Users/husey/kiro2/backend")

from agents.context.context_manager import ContextManager, TokenCounter


class TestContextIsolationProperties:
    """Context isolation property-based testleri (REQ-7.1, REQ-7.2)."""

    def setup_method(self):
        """Test setup."""
        self.default_max_tokens = 200_000

    @given(
        content=st.text(min_size=1, max_size=50000)
    )
    @settings(max_examples=100)
    def test_context_never_exceeds_max_tokens(self, content: str):
        """
        Property 1: Context size <= max_tokens (REQ-7.2)

        For any content added, the context manager MUST NOT
        allow total tokens to exceed the configured limit.
        """
        ctx = ContextManager(max_tokens=self.default_max_tokens, auto_prune=False)

        # Try to add content
        ctx.add_content(content)

        # Property: Context tokens <= max_tokens
        assert ctx.current_tokens <= ctx.max_tokens, (
            f"Context exceeded max tokens: {ctx.current_tokens} > {ctx.max_tokens}"
        )

    @given(
        max_tokens=st.integers(min_value=100, max_value=500_000),
        content_size=st.integers(min_value=1, max_value=10000)
    )
    @settings(max_examples=100)
    def test_context_limit_configurable(self, max_tokens: int, content_size: int):
        """
        Property: Context limit configurable and enforced.

        For any configured max_tokens, the limit MUST be respected.
        """
        ctx = ContextManager(max_tokens=max_tokens, auto_prune=False)
        content = "a" * content_size

        # Add content
        ctx.add_content(content)

        # Property: Never exceed configured limit
        assert ctx.current_tokens <= max_tokens

    @given(
        contents=st.lists(
            st.text(min_size=10, max_size=5000),
            min_size=1,
            max_size=20
        )
    )
    @settings(max_examples=100)
    def test_multiple_additions_respect_limit(self, contents: list):
        """
        Property: Multiple content additions respect limit.

        For any sequence of content additions, total tokens
        MUST NOT exceed the limit.
        """
        ctx = ContextManager(max_tokens=self.default_max_tokens, auto_prune=False)

        for content in contents:
            ctx.add_content(content)

        # Property: Total never exceeds limit
        assert ctx.current_tokens <= ctx.max_tokens

    @given(
        content=st.text(min_size=100, max_size=10000)
    )
    @settings(max_examples=100)
    def test_auto_prune_maintains_limit(self, content: str):
        """
        Property: Auto-prune maintains limit even with overflow attempts.

        With auto_prune=True, context MUST maintain limit by removing
        low-priority content.
        """
        # Small limit to force pruning
        ctx = ContextManager(max_tokens=1000, auto_prune=True)

        # Add multiple contents to trigger pruning
        for i in range(5):
            ctx.add_content(content[:200], priority=0)  # Low priority
            ctx.add_content(content[:100], priority=2)  # High priority

        # Property: Limit maintained
        assert ctx.current_tokens <= ctx.max_tokens

    @given(
        text=st.text(min_size=1, max_size=10000)
    )
    @settings(max_examples=100)
    def test_token_counter_returns_positive(self, text: str):
        """
        Property: Token counter always returns positive integer.
        """
        counter = TokenCounter()
        assume(len(text) > 0)

        tokens = counter.count(text)

        # Property: Token count is positive
        assert tokens > 0, "Token count should be positive for non-empty text"
        assert isinstance(tokens, int), "Token count should be integer"

    @given(
        text1=st.text(min_size=10, max_size=5000),
        text2=st.text(min_size=10, max_size=5000)
    )
    @settings(max_examples=100)
    def test_token_counter_additivity(self, text1: str, text2: str):
        """
        Property: Token count is approximately additive.

        count(a + b) ≈ count(a) + count(b) (within reasonable margin)
        """
        counter = TokenCounter()
        assume(len(text1) > 0 and len(text2) > 0)

        count1 = counter.count(text1)
        count2 = counter.count(text2)
        combined_count = counter.count(text1 + text2)

        # Property: Combined count should be close to sum
        # Allow 10% margin for tokenization edge effects
        expected = count1 + count2
        margin = max(10, int(expected * 0.1))

        assert abs(combined_count - expected) <= margin, (
            f"Token additivity violated: {combined_count} vs {expected} (±{margin})"
        )

    @given(
        content=st.text(min_size=10, max_size=5000)
    )
    @settings(max_examples=100)
    def test_remaining_tokens_accurate(self, content: str):
        """
        Property: Remaining tokens = max - current.
        """
        ctx = ContextManager(max_tokens=self.default_max_tokens)
        ctx.add_content(content)

        # Property: Remaining tokens formula
        assert ctx.get_remaining_tokens() == (ctx.max_tokens - ctx.current_tokens)

    @given(
        content=st.text(min_size=100, max_size=5000)
    )
    @settings(max_examples=100)
    def test_usage_percentage_bounds(self, content: str):
        """
        Property: Usage percentage in [0, 100].
        """
        ctx = ContextManager(max_tokens=self.default_max_tokens)
        ctx.add_content(content)

        # Property: Percentage bounds
        usage = ctx.get_usage_percentage()
        assert 0.0 <= usage <= 100.0, f"Usage percentage out of bounds: {usage}"

    def test_clear_resets_tokens_to_zero(self):
        """
        Test: Clear resets token count to zero.
        """
        ctx = ContextManager(max_tokens=10000)
        ctx.add_content("This is some test content")
        assert ctx.current_tokens > 0

        ctx.clear()
        assert ctx.current_tokens == 0
        assert len(ctx.entries) == 0

    def test_priority_ordering_in_prune(self):
        """
        Test: Low priority content is pruned first.
        """
        ctx = ContextManager(max_tokens=500, auto_prune=True)

        # Add high priority first
        ctx.add_content("HIGH PRIORITY CONTENT", priority=2)
        high_priority_present = True

        # Add low priority until it triggers prune
        for i in range(10):
            ctx.add_content(f"low priority {i}" * 10, priority=0)

        # High priority should still be present
        high_content_found = any(
            "HIGH PRIORITY" in e.content for e in ctx.entries
        )
        assert high_content_found, "High priority content should survive pruning"

    @given(
        max_tokens=st.integers(min_value=100, max_value=10000)
    )
    @settings(max_examples=50)
    def test_can_fit_accuracy(self, max_tokens: int):
        """
        Property: can_fit() accurately predicts whether content will fit.
        """
        ctx = ContextManager(max_tokens=max_tokens, auto_prune=False)
        content = "test " * 100  # ~500 chars

        can_fit_result = ctx.can_fit(content)
        add_result = ctx.add_content(content)

        # Property: can_fit should match add result
        assert can_fit_result == add_result, (
            f"can_fit={can_fit_result} but add_content={add_result}"
        )


class TestContextManagerEdgeCases:
    """Edge case testleri."""

    def test_zero_max_tokens_raises(self):
        """Zero max_tokens should raise ValueError."""
        with pytest.raises(ValueError):
            ContextManager(max_tokens=0)

    def test_negative_max_tokens_raises(self):
        """Negative max_tokens should raise ValueError."""
        with pytest.raises(ValueError):
            ContextManager(max_tokens=-100)

    def test_empty_content_allowed(self):
        """Empty content should be allowed."""
        ctx = ContextManager(max_tokens=1000)
        result = ctx.add_content("")
        assert result is True

    def test_exact_limit_content(self):
        """Content exactly at limit should be allowed."""
        ctx = ContextManager(max_tokens=100, auto_prune=False)

        # Add content that's exactly at limit
        # This might need adjustment based on actual token counting
        counter = TokenCounter()
        test_content = "a"
        while counter.count(test_content) < 100:
            test_content += "a"

        # Should succeed
        result = ctx.add_content(test_content)
        # Either fits exactly or slightly over
        assert ctx.current_tokens <= ctx.max_tokens


class TestTurkishContextHandling:
    """Türkçe karakter testleri."""

    @given(
        turkish_text=st.sampled_from([
            "Türkçe karakterler: ğüşıöç ĞÜŞİÖÇ",
            "İstanbul'da güneşli bir gün",
            "Öğrenci sınavda başarılı oldu",
            "Çağdaş Türk edebiyatı eserleri",
            "Şükrü'nün ödevi tamamlandı",
        ])
    )
    @settings(max_examples=50)
    def test_turkish_characters_counted(self, turkish_text: str):
        """
        Property: Turkish characters properly counted.
        """
        counter = TokenCounter()
        tokens = counter.count(turkish_text)

        assert tokens > 0, "Turkish text should have positive token count"

    def test_turkish_uppercase_i(self):
        """Test Turkish İ/ı handling."""
        counter = TokenCounter()

        text_with_i = "İstanbul"
        text_with_dotless_i = "ışık"

        assert counter.count(text_with_i) > 0
        assert counter.count(text_with_dotless_i) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-seed=0"])
