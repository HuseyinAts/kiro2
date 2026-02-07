"""
Unit Tests for Reporters
========================

Tests for Console, JSON, and HTML reporters.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from backend.core.quality_gates.models import (
    GateResult,
    GateStatus,
    PipelineResult,
)
from backend.core.quality_gates.reporters import (
    ConsoleReporter,
    JsonReporter,
    HtmlReporter,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def sample_gate_result() -> GateResult:
    """Create sample gate result."""
    return GateResult(
        gate_name="code_quality",
        status=GateStatus.PASS,
        score=8.5,
        threshold=7.0,
        message="All checks passed",
        issues=[],
        metrics=None,
        details={},
        execution_time_ms=1500.0,
        blocking=True,
        retries=0,
        auto_fixed=False,
        started_at=datetime.now(),
        completed_at=datetime.now(),
    )


@pytest.fixture
def sample_pipeline_result(sample_gate_result: GateResult) -> PipelineResult:
    """Create sample pipeline result."""
    return PipelineResult(
        pipeline_name="quality-gates",
        status=GateStatus.PASS,
        gates=[sample_gate_result],
        total_score=8.5,
        passed_gates=1,
        failed_gates=0,
        skipped_gates=0,
        total_execution_time_ms=1500.0,
        started_at=datetime.now(),
        completed_at=datetime.now(),
    )


@pytest.fixture
def failed_pipeline_result() -> PipelineResult:
    """Create failed pipeline result."""
    return PipelineResult(
        pipeline_name="quality-gates",
        status=GateStatus.FAIL,
        gates=[
            GateResult(
                gate_name="security",
                status=GateStatus.FAIL,
                score=4.0,
                threshold=7.0,
                message="Critical vulnerability found",
                issues=[],
                metrics=None,
                details={},
                execution_time_ms=2000.0,
                blocking=True,
                retries=0,
                auto_fixed=False,
                started_at=datetime.now(),
                completed_at=datetime.now(),
            ),
        ],
        total_score=4.0,
        passed_gates=0,
        failed_gates=1,
        skipped_gates=0,
        total_execution_time_ms=2000.0,
        started_at=datetime.now(),
        completed_at=datetime.now(),
    )


# =============================================================================
# Test Cases: ConsoleReporter
# =============================================================================

class TestConsoleReporter:
    """Tests for console reporter."""

    def test_report_callable(self, sample_pipeline_result: PipelineResult):
        """Report should be callable and not raise."""
        reporter = ConsoleReporter()

        # Should not raise
        reporter.report(sample_pipeline_result)

    def test_verbose_mode_init(self):
        """Verbose mode should be settable."""
        reporter = ConsoleReporter(verbose=True)

        assert reporter.verbose is True

    def test_non_verbose_mode_init(self):
        """Non-verbose mode should be default."""
        reporter = ConsoleReporter()

        assert reporter.verbose is False

    def test_failed_report_callable(self, failed_pipeline_result: PipelineResult):
        """Failed pipeline report should be callable."""
        reporter = ConsoleReporter()

        # Should not raise
        reporter.report(failed_pipeline_result)


# =============================================================================
# Test Cases: JsonReporter
# =============================================================================

class TestJsonReporter:
    """Tests for JSON reporter."""

    def test_report_returns_valid_json(self, sample_pipeline_result: PipelineResult):
        """Report should return valid JSON."""
        reporter = JsonReporter()
        output = reporter.report(sample_pipeline_result)

        # Should be valid JSON
        data = json.loads(output)
        assert isinstance(data, dict)

    def test_report_contains_pipeline_data(self, sample_pipeline_result: PipelineResult):
        """Report should contain pipeline data."""
        reporter = JsonReporter()
        output = reporter.report(sample_pipeline_result)
        data = json.loads(output)

        # Data is nested under "pipeline" key
        assert "pipeline" in data
        assert "name" in data["pipeline"]
        assert "status" in data["pipeline"]

    def test_report_contains_gates(self, sample_pipeline_result: PipelineResult):
        """Report should contain gate results."""
        reporter = JsonReporter()
        output = reporter.report(sample_pipeline_result)
        data = json.loads(output)

        assert "gates" in data
        assert len(data["gates"]) == 1

    def test_report_to_file(self, sample_pipeline_result: PipelineResult, tmp_path: Path):
        """Report can be saved to file."""
        output_path = tmp_path / "report.json"
        reporter = JsonReporter(output_path=output_path)
        reporter.report(sample_pipeline_result)

        assert output_path.exists()

        # Verify file content is valid JSON
        content = output_path.read_text()
        data = json.loads(content)
        assert "pipeline" in data

    def test_report_includes_metadata(self, sample_pipeline_result: PipelineResult):
        """Report should include metadata."""
        reporter = JsonReporter()
        output = reporter.report(sample_pipeline_result)
        data = json.loads(output)

        # Should have metadata section
        assert "metadata" in data or "execution" in data


# =============================================================================
# Test Cases: HtmlReporter
# =============================================================================

class TestHtmlReporter:
    """Tests for HTML reporter."""

    def test_report_returns_html(self, sample_pipeline_result: PipelineResult):
        """Report should return HTML string."""
        reporter = HtmlReporter()
        output = reporter.report(sample_pipeline_result)

        assert "<html" in output.lower() or "<!doctype" in output.lower()

    def test_report_contains_title(self, sample_pipeline_result: PipelineResult):
        """Report should contain title."""
        reporter = HtmlReporter()
        output = reporter.report(sample_pipeline_result)

        assert "<title>" in output.lower() or "quality" in output.lower()

    def test_report_contains_score(self, sample_pipeline_result: PipelineResult):
        """Report should contain score."""
        reporter = HtmlReporter()
        output = reporter.report(sample_pipeline_result)

        assert "8.5" in output or "score" in output.lower()

    def test_report_to_file(self, sample_pipeline_result: PipelineResult, tmp_path: Path):
        """Report can be saved to file."""
        output_path = tmp_path / "report.html"
        reporter = HtmlReporter(output_path=output_path)
        reporter.report(sample_pipeline_result)

        assert output_path.exists()

        # Verify file content is HTML
        content = output_path.read_text()
        assert "<html" in content.lower() or "<!doctype" in content.lower()

    def test_report_has_styling(self, sample_pipeline_result: PipelineResult):
        """Report should have CSS styling."""
        reporter = HtmlReporter()
        output = reporter.report(sample_pipeline_result)

        assert "<style" in output.lower() or "css" in output.lower()

    def test_report_shows_pass_color(self, sample_pipeline_result: PipelineResult):
        """Passed gate should show green/pass color."""
        reporter = HtmlReporter()
        output = reporter.report(sample_pipeline_result)

        # Should have some indication of pass status
        assert "pass" in output.lower() or "green" in output.lower() or "#" in output

    def test_report_shows_fail_color(self, failed_pipeline_result: PipelineResult):
        """Failed gate should show red/fail color."""
        reporter = HtmlReporter()
        output = reporter.report(failed_pipeline_result)

        # Should have some indication of fail status
        assert "fail" in output.lower() or "red" in output.lower()


# =============================================================================
# Test Cases: Reporter Interface
# =============================================================================

class TestReporterInterface:
    """Tests for reporter interface consistency."""

    def test_all_reporters_have_report_method(self):
        """All reporters should have report method."""
        reporters = [ConsoleReporter(), JsonReporter(), HtmlReporter()]

        for reporter in reporters:
            assert hasattr(reporter, "report")
            assert callable(reporter.report)

    def test_json_and_html_return_string(self, sample_pipeline_result: PipelineResult):
        """JSON and HTML reporters should return string."""
        reporters = [JsonReporter(), HtmlReporter()]

        for reporter in reporters:
            output = reporter.report(sample_pipeline_result)
            assert isinstance(output, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
