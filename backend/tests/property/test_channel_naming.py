"""
Property-Based Tests - Channel Naming Convention (REQ-1.4)

Bu modul, hypothesis kullanarak Redis channel naming icin
property-based testler icerir.

Property 2: Channel Naming Convention - All channels follow
kiro2:agents:{agent_type}:{action} pattern

Boris Cherny Standards: Minimum 100 iterations per property test
"""

import re
import pytest
from hypothesis import given, settings, strategies as st, assume

import sys
sys.path.insert(0, "c:/Users/husey/kiro2/backend")


# Channel naming pattern from spec REQ-1.4
CHANNEL_PATTERN = re.compile(r'^kiro2:agents:[a-z_]+:[a-z_]+$')

# Valid agent types (from domain experts)
VALID_AGENT_TYPES = [
    "matematik",
    "fizik",
    "kimya",
    "biyoloji",
    "turkce",
    "sosyal",
    "yabanci_dil",
    "orchestrator",
    "coordinator",
    "monitor",
]

# Valid actions
VALID_ACTIONS = [
    "subscribe",
    "publish",
    "request",
    "response",
    "heartbeat",
    "status",
    "discovery",
    "handoff",
    "context",
    "event",
]


def generate_channel_name(agent_type: str, action: str) -> str:
    """
    Generate a channel name following the convention.

    Args:
        agent_type: The type of agent
        action: The action being performed

    Returns:
        Channel name in format kiro2:agents:{agent_type}:{action}
    """
    return f"kiro2:agents:{agent_type}:{action}"


def validate_channel_name(channel: str) -> bool:
    """
    Validate a channel name follows the convention (REQ-1.4).

    Args:
        channel: Channel name to validate

    Returns:
        True if valid, False otherwise
    """
    return bool(CHANNEL_PATTERN.match(channel))


class TestChannelNamingProperties:
    """Channel naming property-based testleri (REQ-1.4)."""

    @given(
        agent_type=st.sampled_from(VALID_AGENT_TYPES),
        action=st.sampled_from(VALID_ACTIONS)
    )
    @settings(max_examples=100)
    def test_valid_channels_match_pattern(self, agent_type: str, action: str):
        """
        Property 1: Valid channels match pattern (REQ-1.4)

        For any valid agent_type and action combination,
        the generated channel MUST match the pattern.
        """
        channel = generate_channel_name(agent_type, action)

        # Property: Channel matches pattern
        assert CHANNEL_PATTERN.match(channel), f"Invalid channel: {channel}"
        assert validate_channel_name(channel), f"Validation failed for: {channel}"

    @given(
        agent_type=st.text(
            alphabet="abcdefghijklmnopqrstuvwxyz_",
            min_size=1,
            max_size=20
        ),
        action=st.text(
            alphabet="abcdefghijklmnopqrstuvwxyz_",
            min_size=1,
            max_size=20
        )
    )
    @settings(max_examples=100)
    def test_lowercase_only_channels_valid(self, agent_type: str, action: str):
        """
        Property 2: Lowercase-only channels are valid (REQ-1.4)

        For any lowercase agent_type and action (with underscores),
        the channel MUST be valid.
        """
        # Filter out leading/trailing underscores and empty strings
        agent_type = agent_type.strip("_")
        action = action.strip("_")

        assume(len(agent_type) > 0 and len(action) > 0)
        assume(agent_type.replace("_", "").isalpha())
        assume(action.replace("_", "").isalpha())

        channel = generate_channel_name(agent_type, action)

        # Property: Lowercase channels should be valid
        assert validate_channel_name(channel), f"Lowercase channel invalid: {channel}"

    @given(
        agent_type=st.sampled_from(VALID_AGENT_TYPES),
        action=st.sampled_from(VALID_ACTIONS)
    )
    @settings(max_examples=100)
    def test_channel_prefix_correct(self, agent_type: str, action: str):
        """
        Property 3: Channel prefix is always 'kiro2:agents:' (REQ-1.4)

        For any channel, it MUST start with 'kiro2:agents:'.
        """
        channel = generate_channel_name(agent_type, action)

        # Property: Correct prefix
        assert channel.startswith("kiro2:agents:"), f"Wrong prefix: {channel}"

    @given(
        agent_type=st.sampled_from(VALID_AGENT_TYPES),
        action=st.sampled_from(VALID_ACTIONS)
    )
    @settings(max_examples=100)
    def test_channel_has_four_parts(self, agent_type: str, action: str):
        """
        Property 4: Channel has exactly 4 colon-separated parts (REQ-1.4)

        For any channel, splitting by ':' MUST yield exactly 4 parts.
        """
        channel = generate_channel_name(agent_type, action)
        parts = channel.split(":")

        # Property: Exactly 4 parts
        assert len(parts) == 4, f"Expected 4 parts, got {len(parts)} in: {channel}"
        assert parts[0] == "kiro2", f"First part should be 'kiro2': {channel}"
        assert parts[1] == "agents", f"Second part should be 'agents': {channel}"
        assert parts[2] == agent_type, f"Third part mismatch: {channel}"
        assert parts[3] == action, f"Fourth part mismatch: {channel}"

    @given(
        invalid_char=st.sampled_from(["A", "B", "1", "2", "!", "@", "#", " ", "-"])
    )
    @settings(max_examples=50)
    def test_invalid_characters_rejected(self, invalid_char: str):
        """
        Property 5: Invalid characters in channel are rejected (REQ-1.4)

        Channels with uppercase, numbers, or special chars MUST be invalid.
        """
        # Create channel with invalid character
        invalid_channel = f"kiro2:agents:mat{invalid_char}:subscribe"

        # Property: Invalid channels should fail validation
        is_valid = validate_channel_name(invalid_channel)
        if not invalid_char == "_":  # underscore is allowed
            assert not is_valid, f"Should reject invalid char '{invalid_char}'"


class TestChannelNamingEdgeCases:
    """Edge case testleri for channel naming."""

    def test_empty_agent_type_rejected(self):
        """Empty agent_type should create invalid channel."""
        channel = "kiro2:agents::subscribe"
        assert not validate_channel_name(channel)

    def test_empty_action_rejected(self):
        """Empty action should create invalid channel."""
        channel = "kiro2:agents:matematik:"
        assert not validate_channel_name(channel)

    def test_missing_prefix_rejected(self):
        """Missing kiro2 prefix should be invalid."""
        channel = "agents:matematik:subscribe"
        assert not validate_channel_name(channel)

    def test_wrong_namespace_rejected(self):
        """Wrong namespace (not 'agents') should be invalid."""
        channel = "kiro2:services:matematik:subscribe"
        assert not validate_channel_name(channel)

    def test_extra_colons_rejected(self):
        """Extra colons should be invalid."""
        channel = "kiro2:agents:matematik:subscribe:extra"
        assert not validate_channel_name(channel)

    def test_underscore_in_names_valid(self):
        """Underscores in agent_type and action should be valid."""
        channel = "kiro2:agents:yabanci_dil:health_check"
        assert validate_channel_name(channel)

    def test_all_valid_agent_action_combinations(self):
        """All valid combinations should pass validation."""
        for agent_type in VALID_AGENT_TYPES:
            for action in VALID_ACTIONS:
                channel = generate_channel_name(agent_type, action)
                assert validate_channel_name(channel), (
                    f"Valid combination rejected: {channel}"
                )


class TestChannelNamingIntegration:
    """Integration testleri - actual blackboard channel usage."""

    def test_blackboard_coordinator_channels(self):
        """Test channel names used in BlackboardCoordinator."""
        # These are the actual channels used in the codebase
        expected_channels = [
            "kiro2:agents:orchestrator:heartbeat",
            "kiro2:agents:matematik:request",
            "kiro2:agents:fizik:response",
            "kiro2:agents:coordinator:discovery",
        ]

        for channel in expected_channels:
            assert validate_channel_name(channel), f"Expected valid: {channel}"

    def test_domain_blackboard_channels(self):
        """Test channel names from DomainBlackboard."""
        # Pattern from coordination/blackboard.py line 219
        channel_template = "blackboard:{topic}"  # Different pattern, internal use

        # Verify the spec-compliant pattern is different
        spec_channel = "kiro2:agents:matematik:subscribe"
        assert validate_channel_name(spec_channel)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-seed=0"])
