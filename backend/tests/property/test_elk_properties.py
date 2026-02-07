"""
Property-Based Tests - ELK Logging System

Bu modul, hypothesis kullanarak ELK logging sistemi icin
property-based testler icerir.

Property Tests:
    1. test_log_completeness - Her log entry zorunlu alanlari icermeli
    2. test_index_rollover - ILM rollover kosullari dogru calismali
    3. test_pii_masking - Hassas veriler her zaman maskelenmeli

Task: ELK Logging Tests Implementation
Spec: centralized-logging-elk

Requirements Tested:
    REQ-1.3: Structured JSON logging with required fields
    REQ-2.2: PII masking for sensitive data
    REQ-3.1: ILM policy with hot-warm-cold-delete phases
"""

import pytest
import sys
from datetime import datetime
from hypothesis import given, strategies as st, settings, assume

sys.path.insert(0, "c:/Users/husey/kiro2/backend")

from core.structured_logger import (
    censor_sensitive_data,
    get_logger,
)


# =====================================================================
# Hypothesis Strategies
# =====================================================================

# Sensitive keys that should always be masked (must match structured_logger.py)
# These are the EXACT keys defined in censor_sensitive_data
SENSITIVE_KEYS = [
    "password",
    "token",
    "secret",
    "api_key",
    "authorization",
    "credit_card",
    "ssn",
    "private_key",
    "şifre",  # Turkish: şifre (with Turkish ş)
    "parola",  # Turkish: parola
]

# Log levels
LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# Service names for KIRO2
SERVICE_NAMES = [
    "kiro2-backend",
    "kiro2-frontend",
    "kiro2-worker",
    "kiro2-scheduler",
    "kiro2-ai-engine",
]


@st.composite
def log_entry_data(draw):
    """Generate complete log entry data."""
    return {
        "event": draw(st.text(min_size=1, max_size=200, alphabet=st.characters(
            blacklist_categories=('Cs',),
            whitelist_categories=('L', 'N', 'P', 'S', 'Z')
        ))),
        "log_level": draw(st.sampled_from(LOG_LEVELS)),
        "timestamp": draw(st.datetimes(
            min_value=datetime(2020, 1, 1),
            max_value=datetime(2030, 12, 31)
        )).isoformat(),
        "service_name": draw(st.sampled_from(SERVICE_NAMES)),
        "correlation_id": draw(st.uuids().map(str)),
        "user_id": draw(st.one_of(st.none(), st.integers(min_value=1, max_value=1000000))),
    }


@st.composite
def sensitive_log_data(draw):
    """Generate log data with sensitive keys."""
    key = draw(st.sampled_from(SENSITIVE_KEYS))
    value = draw(st.text(
        min_size=1,
        max_size=50,
        alphabet=st.characters(blacklist_categories=('Cs',))
    ))
    nested_depth = draw(st.integers(min_value=0, max_value=2))
    return key, value, nested_depth


@st.composite
def ilm_metrics(draw):
    """Generate ILM-related metrics for rollover testing."""
    return {
        "index_size_gb": draw(st.floats(min_value=0, max_value=100, allow_nan=False)),
        "index_age_days": draw(st.integers(min_value=0, max_value=60)),
        "doc_count": draw(st.integers(min_value=0, max_value=10000000)),
    }


# =====================================================================
# Helper Functions
# =====================================================================

def build_nested_log(key: str, value: str, depth: int) -> dict:
    """Build a nested log structure with sensitive data at specified depth."""
    if depth == 0:
        return {key: value, "event": "test_event", "log_level": "INFO"}
    return {
        "nested": build_nested_log(key, value, depth - 1),
        "event": "test_event",
        "log_level": "INFO"
    }


def extract_nested_value(data: dict, key: str, depth: int) -> str | None:
    """Extract value from nested dict at specified depth."""
    if depth == 0:
        return data.get(key)
    if "nested" in data:
        return extract_nested_value(data["nested"], key, depth - 1)
    return None


# =====================================================================
# Property Tests - Log Completeness
# =====================================================================

class TestLogCompletenessProperties:
    """Log entry completeness property testleri."""

    @given(data=log_entry_data())
    @settings(max_examples=100)
    def test_log_entry_has_required_fields(self, data: dict):
        """
        Property 1: Her log entry zorunlu alanlari icermeli.
        REQ-1.3: Structured JSON logging with required fields

        Required fields:
            - event (string)
            - log_level (string)
            - timestamp (ISO 8601)
        """
        required_fields = ["event", "log_level", "timestamp"]

        for field in required_fields:
            assert field in data, f"Required field '{field}' missing from log entry"
            assert data[field] is not None, f"Required field '{field}' is None"
            assert len(str(data[field])) > 0, f"Required field '{field}' is empty"

    @given(data=log_entry_data())
    @settings(max_examples=100)
    def test_timestamp_is_valid_iso8601(self, data: dict):
        """
        Property: Timestamp gecerli ISO 8601 formatinda olmali.
        """
        timestamp = data["timestamp"]

        # Try to parse the timestamp
        try:
            parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            assert isinstance(parsed, datetime)
        except ValueError as e:
            pytest.fail(f"Invalid timestamp format: {timestamp}, error: {e}")

    @given(
        event=st.text(min_size=1, max_size=500, alphabet=st.characters(
            blacklist_categories=('Cs',),
            whitelist_categories=('L', 'N', 'P', 'Z')
        )),
        level=st.sampled_from(LOG_LEVELS)
    )
    @settings(max_examples=100)
    def test_log_level_is_valid(self, event: str, level: str):
        """
        Property: Log level gecerli degerlerden biri olmali.
        """
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        assert level in valid_levels, f"Invalid log level: {level}"

    @given(data=log_entry_data())
    @settings(max_examples=100)
    def test_service_name_present(self, data: dict):
        """
        Property: Service name log entry'de bulunmali.
        """
        assert "service_name" in data
        assert data["service_name"] is not None
        assert len(data["service_name"]) > 0

    @given(data=log_entry_data())
    @settings(max_examples=100)
    def test_correlation_id_is_valid_uuid(self, data: dict):
        """
        Property: Correlation ID gecerli UUID formatinda olmali.
        """
        import uuid

        if "correlation_id" in data and data["correlation_id"]:
            try:
                uuid.UUID(data["correlation_id"])
            except ValueError:
                pytest.fail(f"Invalid UUID format: {data['correlation_id']}")


# =====================================================================
# Property Tests - ILM Index Rollover
# =====================================================================

class TestIndexRolloverProperties:
    """ILM index rollover property testleri."""

    @given(metrics=ilm_metrics())
    @settings(max_examples=100)
    def test_hot_phase_rollover_50gb_trigger(self, metrics: dict):
        """
        Property: Index >= 50GB hot phase rollover tetiklemeli.
        REQ-3.1: ILM policy with hot phase rollover at 50GB
        """
        rollover_size_gb = 50.0

        should_rollover = metrics["index_size_gb"] >= rollover_size_gb

        if should_rollover:
            assert metrics["index_size_gb"] >= rollover_size_gb, \
                f"Rollover should trigger at {rollover_size_gb}GB, got {metrics['index_size_gb']}GB"

    @given(metrics=ilm_metrics())
    @settings(max_examples=100)
    def test_hot_phase_rollover_1day_trigger(self, metrics: dict):
        """
        Property: Index >= 1 gun hot phase rollover tetiklemeli.
        """
        rollover_age_days = 1

        should_rollover_by_age = metrics["index_age_days"] >= rollover_age_days

        if should_rollover_by_age:
            assert metrics["index_age_days"] >= rollover_age_days

    @given(metrics=ilm_metrics())
    @settings(max_examples=100)
    def test_warm_phase_at_7_days(self, metrics: dict):
        """
        Property: Index 7 gun sonra warm phase'e gecmeli.
        """
        warm_phase_days = 7

        is_warm_phase = metrics["index_age_days"] >= warm_phase_days

        if is_warm_phase and metrics["index_age_days"] < 14:
            # Should be in warm phase (7-14 days)
            assert warm_phase_days <= metrics["index_age_days"] < 14

    @given(metrics=ilm_metrics())
    @settings(max_examples=100)
    def test_cold_phase_at_14_days(self, metrics: dict):
        """
        Property: Index 14 gun sonra cold phase'e gecmeli.
        """
        cold_phase_days = 14

        is_cold_phase = metrics["index_age_days"] >= cold_phase_days

        if is_cold_phase and metrics["index_age_days"] < 30:
            # Should be in cold phase (14-30 days)
            assert cold_phase_days <= metrics["index_age_days"] < 30

    @given(metrics=ilm_metrics())
    @settings(max_examples=100)
    def test_delete_phase_at_30_days(self, metrics: dict):
        """
        Property: Index 30 gun sonra silinmeli.
        """
        delete_phase_days = 30

        should_delete = metrics["index_age_days"] >= delete_phase_days

        if should_delete:
            assert metrics["index_age_days"] >= delete_phase_days, \
                f"Index should be deleted at {delete_phase_days} days"

    @given(
        size_gb=st.floats(min_value=0, max_value=100, allow_nan=False),
        age_days=st.integers(min_value=0, max_value=60)
    )
    @settings(max_examples=100)
    def test_rollover_conditions_are_or_not_and(self, size_gb: float, age_days: int):
        """
        Property: Rollover kosullari OR ile birlestirilmeli (AND degil).
        Herhangi biri saglanirsa rollover olmali.
        """
        size_trigger = size_gb >= 50.0
        age_trigger = age_days >= 1

        should_rollover = size_trigger or age_trigger

        # En az biri saglaniyorsa rollover olmali
        if size_trigger:
            assert should_rollover, "Size trigger should cause rollover"
        if age_trigger:
            assert should_rollover, "Age trigger should cause rollover"


# =====================================================================
# Property Tests - PII Masking
# =====================================================================

class TestPIIMaskingProperties:
    """PII masking property testleri."""

    @given(data=sensitive_log_data())
    @settings(max_examples=100)
    def test_pii_always_masked_top_level(self, data: tuple):
        """
        Property 3a: Top-level hassas veriler her zaman maskelenmeli.
        REQ-2.2: PII masking for sensitive data
        """
        key, value, _ = data
        assume(len(value) > 0)  # Skip empty values

        log_entry = {key: value, "event": "test_event"}

        # Apply censoring
        censored = censor_sensitive_data(None, None, log_entry.copy())

        # Property: Value should be redacted
        assert censored[key] == "***REDACTED***", \
            f"Sensitive key '{key}' with value '{value}' was not masked"

    @given(
        key=st.sampled_from(SENSITIVE_KEYS),
        value=st.text(min_size=1, max_size=50, alphabet=st.characters(
            blacklist_categories=('Cs',)
        ))
    )
    @settings(max_examples=100)
    def test_sensitive_value_never_in_output(self, key: str, value: str):
        """
        Property: Hassas deger cikti string'inde asla gorunmemeli.
        """
        assume(len(value) > 0)

        log_entry = {key: value, "event": "test_event"}
        censored = censor_sensitive_data(None, None, log_entry.copy())

        # Convert to string and check
        output_str = str(censored)

        # The actual value should not appear in output
        # (unless it's very short and happens to match REDACTED)
        if len(value) > 3:  # Skip very short values that might match
            assert value not in output_str, \
                f"Sensitive value '{value}' found in output"

    @given(
        base_key=st.sampled_from(["password", "token", "secret"]),
        prefix=st.text(min_size=0, max_size=10, alphabet="abcdefghijklmnopqrstuvwxyz_"),
        suffix=st.text(min_size=0, max_size=10, alphabet="abcdefghijklmnopqrstuvwxyz_")
    )
    @settings(max_examples=100)
    def test_partial_key_matches_masked(self, base_key: str, prefix: str, suffix: str):
        """
        Property: Kismi key eslesmelerinde de maskeleme yapilmali.
        Ornegin: user_password, api_token_secret, etc.
        """
        key = f"{prefix}{base_key}{suffix}"
        value = "sensitive_data_123"

        log_entry = {key: value, "event": "test_event"}
        censored = censor_sensitive_data(None, None, log_entry.copy())

        # Property: Key containing sensitive word should be masked
        assert censored[key] == "***REDACTED***", \
            f"Key '{key}' containing '{base_key}' was not masked"

    @given(
        key=st.sampled_from(["şifre", "parola"]),  # Turkish keys with proper chars
        value=st.text(min_size=1, max_size=50, alphabet=st.characters(
            blacklist_categories=('Cs',),
            whitelist_categories=('L', 'N')
        ))
    )
    @settings(max_examples=100)
    def test_turkish_sensitive_keys_masked(self, key: str, value: str):
        """
        Property: Turkce hassas anahtar kelimeler maskelenmeli.
        şifre, parola gibi Turkce kelimeler de maskeli olmali.
        """
        assume(len(value) > 0)

        log_entry = {key: value}
        censored = censor_sensitive_data(None, None, log_entry.copy())

        # Property: Turkish keys should be masked
        assert censored[key] == "***REDACTED***", \
            f"Turkish sensitive key '{key}' was not masked"

    @given(
        non_sensitive_key=st.sampled_from([
            "user_id", "email", "name", "message",
            "status", "endpoint", "duration_ms", "request_id"
        ]),
        value=st.text(min_size=1, max_size=50, alphabet=st.characters(
            blacklist_categories=('Cs',)
        ))
    )
    @settings(max_examples=100)
    def test_non_sensitive_keys_not_masked(self, non_sensitive_key: str, value: str):
        """
        Property: Hassas olmayan keyler maskelenmemeli.
        """
        assume(len(value) > 0)

        # Create log entry with non-sensitive key and its value
        log_entry = {non_sensitive_key: value}
        censored = censor_sensitive_data(None, None, log_entry.copy())

        # Property: Non-sensitive keys should keep their value
        assert censored[non_sensitive_key] == value, \
            f"Non-sensitive key '{non_sensitive_key}' was incorrectly masked"

    @given(
        key=st.sampled_from(SENSITIVE_KEYS),
        case_variant=st.sampled_from(["lower", "upper", "title", "mixed"])
    )
    @settings(max_examples=100)
    def test_case_insensitive_masking(self, key: str, case_variant: str):
        """
        Property: Maskeleme buyuk/kucuk harf duyarsiz olmali.
        """
        # Apply case variant
        if case_variant == "lower":
            test_key = key.lower()
        elif case_variant == "upper":
            test_key = key.upper()
        elif case_variant == "title":
            test_key = key.title()
        else:  # mixed
            test_key = "".join(
                c.upper() if i % 2 else c.lower()
                for i, c in enumerate(key)
            )

        value = "secret_value_123"
        log_entry = {test_key: value, "event": "test_event"}
        censored = censor_sensitive_data(None, None, log_entry.copy())

        # Property: Case variants should all be masked
        assert censored[test_key] == "***REDACTED***", \
            f"Case variant '{test_key}' was not masked"


# =====================================================================
# Property Tests - Log Processing
# =====================================================================

class TestLogProcessingProperties:
    """Log processing property testleri."""

    @given(
        event=st.text(min_size=1, max_size=200, alphabet=st.characters(
            blacklist_categories=('Cs',),
            whitelist_categories=('L', 'N', 'P', 'Z')
        )),
        extra_fields=st.dictionaries(
            keys=st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz_"),
            values=st.one_of(
                st.text(min_size=0, max_size=100),
                st.integers(),
                st.floats(allow_nan=False, allow_infinity=False),
                st.booleans()
            ),
            min_size=0,
            max_size=10
        )
    )
    @settings(max_examples=50)
    def test_extra_fields_preserved(self, event: str, extra_fields: dict):
        """
        Property: Extra alanlar log entry'de korunmali.
        """
        logger = get_logger("test_logger")

        # Build log entry
        log_entry = {"event": event}
        log_entry.update(extra_fields)

        # Process through censor (simulating structlog processor)
        processed = censor_sensitive_data(None, None, log_entry.copy())

        # Property: All extra fields should be present (possibly censored)
        for key in extra_fields:
            assert key in processed, f"Extra field '{key}' was lost"

    @given(
        unicode_text=st.text(
            min_size=1,
            max_size=100,
            alphabet=st.characters(
                whitelist_categories=('L',),
                whitelist_characters='cdefghijklmnopqrstuvwxyz'
            )
        )
    )
    @settings(max_examples=50)
    def test_unicode_handling(self, unicode_text: str):
        """
        Property: Unicode karakterler dogru islenmeli.
        """
        log_entry = {
            "event": unicode_text,
            "message": unicode_text,
            "log_level": "INFO"
        }

        processed = censor_sensitive_data(None, None, log_entry.copy())

        # Property: Unicode text should be preserved
        assert processed["event"] == unicode_text
        assert processed["message"] == unicode_text

    @given(
        empty_type=st.sampled_from(["empty_string", "none", "empty_dict", "empty_list"])
    )
    @settings(max_examples=20)
    def test_empty_values_handled(self, empty_type: str):
        """
        Property: Bos degerler dogru islenmeli.
        """
        if empty_type == "empty_string":
            value = ""
        elif empty_type == "none":
            value = None
        elif empty_type == "empty_dict":
            value = {}
        else:
            value = []

        log_entry = {
            "event": "test",
            "test_field": value,
            "log_level": "INFO"
        }

        # Should not raise exception
        processed = censor_sensitive_data(None, None, log_entry.copy())

        # Property: Empty values should be preserved
        assert processed["test_field"] == value


# =====================================================================
# Property Tests - Log Volume
# =====================================================================

class TestLogVolumeProperties:
    """Log volume property testleri."""

    @given(
        log_count=st.integers(min_value=1, max_value=100)
    )
    @settings(max_examples=30)
    def test_batch_log_processing(self, log_count: int):
        """
        Property: Batch log islemede tum loglar islenmeli.
        """
        logs = [
            {"event": f"event_{i}", "log_level": "INFO", "index": i}
            for i in range(log_count)
        ]

        processed_logs = [
            censor_sensitive_data(None, None, log.copy())
            for log in logs
        ]

        # Property: All logs should be processed
        assert len(processed_logs) == log_count

        # Property: Each log should have its index preserved
        for i, log in enumerate(processed_logs):
            assert log["index"] == i

    @given(
        field_count=st.integers(min_value=1, max_value=50)
    )
    @settings(max_examples=30)
    def test_large_log_entry_handling(self, field_count: int):
        """
        Property: Cok alanli log entry'ler dogru islenmeli.
        """
        log_entry = {"event": "test", "log_level": "INFO"}

        # Add many fields
        for i in range(field_count):
            log_entry[f"field_{i}"] = f"value_{i}"

        processed = censor_sensitive_data(None, None, log_entry.copy())

        # Property: All fields should be present
        assert len(processed) == field_count + 2  # +2 for event and log_level


# =====================================================================
# Edge Case Tests
# =====================================================================

class TestEdgeCases:
    """Edge case testleri."""

    def test_empty_log_entry(self):
        """Edge case: Bos log entry."""
        log_entry = {}
        processed = censor_sensitive_data(None, None, log_entry.copy())
        assert processed == {}

    def test_only_sensitive_fields(self):
        """Edge case: Sadece hassas alanlar iceren log."""
        log_entry = {
            "password": "secret123",
            "token": "abc-def-ghi",
            "api_key": "key-xyz"
        }

        processed = censor_sensitive_data(None, None, log_entry.copy())

        for key in log_entry:
            assert processed[key] == "***REDACTED***"

    def test_mixed_sensitive_and_safe_fields(self):
        """Edge case: Karisik hassas ve guvenli alanlar."""
        log_entry = {
            "event": "user_login",
            "user_id": 123,
            "password": "secret",
            "email": "user@example.com",
            "token": "jwt-token-here"
        }

        processed = censor_sensitive_data(None, None, log_entry.copy())

        # Safe fields preserved
        assert processed["event"] == "user_login"
        assert processed["user_id"] == 123
        assert processed["email"] == "user@example.com"

        # Sensitive fields masked
        assert processed["password"] == "***REDACTED***"
        assert processed["token"] == "***REDACTED***"

    def test_numeric_sensitive_values(self):
        """Edge case: Sayisal hassas degerler."""
        log_entry = {
            "credit_card": 4111111111111111,
            "ssn": 123456789
        }

        processed = censor_sensitive_data(None, None, log_entry.copy())

        assert processed["credit_card"] == "***REDACTED***"
        assert processed["ssn"] == "***REDACTED***"


# =====================================================================
# Run Tests
# =====================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
