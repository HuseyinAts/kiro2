"""Property-based tests for hooks system.

Uses hypothesis for property-based testing with 100 iterations.
Tests the correctness properties defined in design.md.
"""

from hypothesis import given, strategies as st, settings

from backend.hooks.models import (
    QualityCheckResult,
    AggregatedResult,
    ExitCode,
    ErrorCategory,
    LintError,
)


# Property 1: Exit Code Consistency
# For any quality check with errors, exit code must be 2.

@settings(max_examples=100)
@given(
    has_errors=st.booleans(),
    error_count=st.integers(min_value=0, max_value=10)
)
def test_exit_code_consistency(has_errors: bool, error_count: int):
    """
    Property 1: Exit Code Consistency

    WHEN a quality check has errors (passed=False)
    THEN exit_code MUST be 2 (BLOCKING_ERROR)

    WHEN a quality check has no errors (passed=True)
    THEN exit_code MUST be 0 (SUCCESS)

    Validates: Requirements 1.5, 2.5, 3.5
    """
    errors = [f"Error {i}" for i in range(error_count)] if has_errors else []

    result = QualityCheckResult(
        tool="test",
        passed=not has_errors,
        exit_code=ExitCode.BLOCKING_ERROR if has_errors else ExitCode.SUCCESS,
        errors=errors,
        warnings=[],
        execution_time=1.0,
        files_checked=1
    )

    if result.passed:
        assert result.exit_code == ExitCode.SUCCESS, \
            "Passed result must have exit code 0"
    else:
        assert result.exit_code == ExitCode.BLOCKING_ERROR, \
            "Failed result must have exit code 2"


@settings(max_examples=100)
@given(
    passed_count=st.integers(min_value=0, max_value=10),
    failed_count=st.integers(min_value=0, max_value=10)
)
def test_aggregated_exit_code_consistency(passed_count: int, failed_count: int):
    """
    Property: Aggregated exit code consistency.

    WHEN any check fails
    THEN aggregated exit code MUST be 2

    WHEN all checks pass
    THEN aggregated exit code MUST be 0
    """
    aggregated = AggregatedResult()

    # Add passed results
    for i in range(passed_count):
        aggregated.add_result(QualityCheckResult(
            tool=f"pass_{i}",
            passed=True,
            exit_code=ExitCode.SUCCESS,
            execution_time=0.1,
            files_checked=1
        ))

    # Add failed results
    for i in range(failed_count):
        aggregated.add_result(QualityCheckResult(
            tool=f"fail_{i}",
            passed=False,
            exit_code=ExitCode.BLOCKING_ERROR,
            errors=["Error"],
            execution_time=0.1,
            files_checked=1
        ))

    if failed_count > 0:
        assert aggregated.exit_code == ExitCode.BLOCKING_ERROR, \
            "Any failure must result in exit code 2"
        assert aggregated.all_passed is False
    else:
        assert aggregated.exit_code == ExitCode.SUCCESS, \
            "All passed must result in exit code 0"
        assert aggregated.all_passed is True


# Property 2: Lint Error Criticality
# E and F codes are critical, W codes are not.

@settings(max_examples=100)
@given(
    code=st.sampled_from(["E501", "E101", "F401", "F811", "W291", "W293"])
)
def test_lint_error_criticality(code: str):
    """
    Property: Lint error criticality based on code prefix.

    WHEN code starts with E or F
    THEN error is_critical MUST be True

    WHEN code starts with W
    THEN error is_critical MUST be False

    Validates: Requirements 1.2, 1.5, 1.6
    """
    category = ErrorCategory.ERROR if code.startswith("E") else \
               ErrorCategory.FATAL if code.startswith("F") else \
               ErrorCategory.WARNING

    error = LintError(
        file="test.py",
        line=1,
        column=1,
        code=code,
        message="Test error",
        category=category
    )

    if code.startswith("E") or code.startswith("F"):
        assert error.is_critical is True, \
            f"Code {code} should be critical"
    else:
        assert error.is_critical is False, \
            f"Code {code} should not be critical"


# Property 3: Execution Time Aggregation

@settings(max_examples=100)
@given(
    times=st.lists(
        st.floats(min_value=0.1, max_value=10.0),
        min_size=1,
        max_size=10
    )
)
def test_execution_time_aggregation(times: list[float]):
    """
    Property: Total execution time is sum of individual times.

    Note: For parallel execution, actual wall-clock time would be
    max(times), but we track sum for total CPU time.

    Validates: Requirements 8.4
    """
    aggregated = AggregatedResult()

    for i, t in enumerate(times):
        aggregated.add_result(QualityCheckResult(
            tool=f"tool_{i}",
            passed=True,
            exit_code=ExitCode.SUCCESS,
            execution_time=t,
            files_checked=1
        ))

    expected_sum = sum(times)
    assert abs(aggregated.total_execution_time - expected_sum) < 0.001, \
        f"Total execution time {aggregated.total_execution_time} != sum {expected_sum}"


# Property 4: Error and Warning Counts

@settings(max_examples=100)
@given(
    error_counts=st.lists(
        st.integers(min_value=0, max_value=5),
        min_size=1,
        max_size=5
    ),
    warning_counts=st.lists(
        st.integers(min_value=0, max_value=5),
        min_size=1,
        max_size=5
    )
)
def test_error_warning_count_aggregation(error_counts: list[int], warning_counts: list[int]):
    """
    Property: Error and warning counts are correctly aggregated.
    """
    aggregated = AggregatedResult()

    # Ensure same length
    min_len = min(len(error_counts), len(warning_counts))
    error_counts = error_counts[:min_len]
    warning_counts = warning_counts[:min_len]

    for i, (e_count, w_count) in enumerate(zip(error_counts, warning_counts)):
        aggregated.add_result(QualityCheckResult(
            tool=f"tool_{i}",
            passed=e_count == 0,
            exit_code=ExitCode.BLOCKING_ERROR if e_count > 0 else ExitCode.SUCCESS,
            errors=[f"Error {j}" for j in range(e_count)],
            warnings=[f"Warning {j}" for j in range(w_count)],
            execution_time=0.1,
            files_checked=1
        ))

    assert aggregated.total_errors == sum(error_counts), \
        "Total errors mismatch"
    assert aggregated.total_warnings == sum(warning_counts), \
        "Total warnings mismatch"


# Property 5: Files Checked Count

@settings(max_examples=100)
@given(
    file_counts=st.lists(
        st.integers(min_value=1, max_value=20),
        min_size=1,
        max_size=5
    )
)
def test_files_checked_independence(file_counts: list[int]):
    """
    Property: Each hook can check different number of files.

    The aggregated result tracks individual hook file counts,
    not a global total (since hooks may check same files).
    """
    aggregated = AggregatedResult()

    for i, f_count in enumerate(file_counts):
        result = QualityCheckResult(
            tool=f"tool_{i}",
            passed=True,
            exit_code=ExitCode.SUCCESS,
            execution_time=0.1,
            files_checked=f_count
        )
        aggregated.add_result(result)

        # Each result maintains its own files_checked
        assert aggregated.results[i].files_checked == f_count
