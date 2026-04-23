"""
Pattern definitions for Reward Hacking Detection.

Daisy Stanton Standards - Banned Patterns List
"""

from __future__ import annotations

# =============================================================================
# REWARD HACKING PATTERNS
# =============================================================================
# Each pattern type maps to a list of regex patterns that detect that type.
# Patterns are designed to minimize false positives while catching all real cases.

REWARD_HACKING_PATTERNS: dict[str, list[str]] = {
    # =========================================================================
    # 1. Assert True Detection (REQ-1)
    # =========================================================================
    "assert_true": [
        r"\bassert\s+True\s*$",           # Python: assert True
        r"\bassert\s+True\s*#",           # Python: assert True # comment
        r"\bassert\s+true\s*$",           # Python: assert true (lowercase)
        r"ASSERT_TRUE\s*\(\s*true\s*\)",  # C++/GTest: ASSERT_TRUE(true)
        r"ASSERT_TRUE\s*\(\s*True\s*\)",  # C++: ASSERT_TRUE(True)
        r"self\.assertTrue\s*\(\s*True\s*\)",  # unittest: self.assertTrue(True)
        r"assert\s+1\s*==\s*1",           # Tautology: assert 1 == 1
        r"assert\s+\".*\"\s*==\s*\".*\"", # String tautology
    ],

    # =========================================================================
    # 2. Echo Success Detection (REQ-2)
    # =========================================================================
    "echo_success": [
        r'echo\s+"?Success"?\s*$',             # Bash: echo Success
        r'echo\s+"?SUCCESS"?\s*$',             # Bash: echo SUCCESS
        r'print\s*\(\s*["\']Success["\']\s*\)',   # Python: print("Success")
        r'print\s*\(\s*["\']SUCCESS["\']\s*\)',   # Python: print("SUCCESS")
        r'console\.log\s*\(\s*["\']Success["\']\s*\)',  # JS: console.log("Success")
        r'System\.out\.println\s*\(\s*["\']Success["\']\s*\)',  # Java
        r'puts\s+["\']Success["\']',           # Ruby: puts "Success"
    ],

    # =========================================================================
    # 3. Placeholder Code Detection (REQ-3)
    # =========================================================================
    "placeholder": [
        r"pass\s*#\s*placeholder",        # pass # placeholder
        r"pass\s*#\s*TODO",               # pass # TODO
        r"pass\s*#\s*FIXME",              # pass # FIXME
        r"#\s*TODO:\s*implement",         # # TODO: implement
        r"#\s*FIXME:\s*implement",        # # FIXME: implement
        r"raise\s+NotImplementedError\s*\(\s*\)",  # raise NotImplementedError()
        r"raise\s+NotImplementedError\s*$",        # raise NotImplementedError
        r"^\s*\.\.\.\s*$",                # Ellipsis as placeholder
        r"return\s+None\s*#\s*stub",      # return None # stub
        r"return\s+None\s*#\s*TODO",      # return None # TODO
    ],

    # =========================================================================
    # 4. Coverage Manipulation Detection (REQ-4)
    # =========================================================================
    "coverage_manipulation": [
        r"#\s*pragma:\s*no\s*cover(?!\s*#\s*\w)",  # pragma: no cover without reason
        r"#\s*pragma:\s*nocover",          # pragma: nocover (variant)
        r"#\s*type:\s*ignore\s*$",         # type: ignore without code
        r"#\s*type:\s*ignore\s*#",         # type: ignore with comment but no code
        r"#\s*noqa\s*$",
        r"#\s*nosec\s*$",                  # nosec without reason
        r"@pytest\.mark\.skip\s*$",        # skip without reason
        r"@unittest\.skip\s*$",            # unittest skip without reason
    ],

    # =========================================================================
    # 5. Mock Abuse Detection (REQ-5)
    # =========================================================================
    "mock_abuse": [
        r"@patch\s*\([^)]*\)\s*\n\s*@patch",  # Multiple consecutive patches
        r"mock\.return_value\s*=\s*True",     # Mock returning True
        r"mock\.return_value\s*=\s*\[\]",     # Mock returning empty list
        r"mock\.return_value\s*=\s*\{\}",     # Mock returning empty dict
        r"MagicMock\s*\(\s*\)",               # Empty MagicMock
        r"Mock\s*\(\s*return_value\s*=\s*None\s*\)",  # Mock returning None
    ],

    # =========================================================================
    # 6. Empty Exception Handler Detection (REQ-6)
    # =========================================================================
    "empty_exception": [
        r"except\s*:\s*\n\s*pass",            # except: pass
        r"except\s+Exception\s*:\s*\n\s*pass", # except Exception: pass
        r"except\s+BaseException\s*:\s*\n\s*pass",  # except BaseException: pass
        r"except\s+\w+Error\s*:\s*\n\s*pass",  # except SomeError: pass
        r"except\s*:\s*\n\s*\.\.\.",          # except: ...
        r"except\s+Exception\s*:\s*\n\s*\.\.\.",  # except Exception: ...
    ],

    # =========================================================================
    # 7. Hardcoded Test Data Detection (REQ-7)
    # =========================================================================
    "hardcoded_test_data": [
        r"user_id\s*=\s*1\s*$",              # user_id = 1
        r"id\s*=\s*1\s*$",                   # id = 1
        r'email\s*=\s*["\']test@',           # email = "test@..."
        r'password\s*=\s*["\']password',     # password = "password..."
        r'password\s*=\s*["\']123',          # password = "123..."
        r'password\s*=\s*["\']test',         # password = "test..."
        r'api_key\s*=\s*["\']test',          # api_key = "test..."
        r'secret\s*=\s*["\']test',           # secret = "test..."
    ],

    # =========================================================================
    # 8. CI/CD Bypass Detection (REQ-8)
    # =========================================================================
    "cicd_bypass": [
        r"\[skip\s*ci\]",                   # [skip ci]
        r"\[ci\s*skip\]",                   # [ci skip]
        r"\[no\s*ci\]",                     # [no ci]
        r"--no-verify",                     # git commit --no-verify
        r"--skip-ci",                       # --skip-ci flag
        r"@pytest\.mark\.skip\s*\(\s*\)",   # @pytest.mark.skip() without reason
        r"@unittest\.skip\s*\(\s*\)",       # @unittest.skip() without reason
        r"pytest\.skip\s*\(\s*\)",          # pytest.skip() without reason
    ],
}


# =============================================================================
# REMEDIATION SUGGESTIONS
# =============================================================================
# Human-readable suggestions for fixing each pattern type.

REMEDIATION_SUGGESTIONS: dict[str, str] = {
    "assert_true": (
        "Replace with a meaningful assertion that tests actual behavior. "
        "Example: assert user.email == expected_email"
    ),
    "echo_success": (
        "Add actual validation before declaring success. "
        "Example: if [ $exit_code -eq 0 ]; then echo 'Tests passed'; fi"
    ),
    "placeholder": (
        "Implement the actual functionality instead of using placeholders. "
        "If the feature is not ready, create a tracking issue and skip the test with reason."
    ),
    "coverage_manipulation": (
        "Add a documented reason for excluding from coverage. "
        "Example: # pragma: no cover  # defensive code for race condition"
    ),
    "mock_abuse": (
        "Consider writing integration tests instead of excessive mocking. "
        "Use assert_called_once() or assert_called_with() to verify mock usage."
    ),
    "empty_exception": (
        "Handle the exception properly: log it, re-raise it, or document why it's ignored. "
        "Example: except ValueError as e: logger.warning(f'Ignored: {e}')"
    ),
    "hardcoded_test_data": (
        "Use fixtures, factories, or parametrized tests instead of hardcoded values. "
        "Consider using Hypothesis for property-based testing."
    ),
    "cicd_bypass": (
        "Provide a documented reason for skipping CI. "
        "Example: @pytest.mark.skip(reason='Requires external service')"
    ),
}


# =============================================================================
# LEGITIMATE EXCEPTIONS
# =============================================================================
# Patterns that look like reward hacking but are legitimate uses.

LEGITIMATE_EXCEPTIONS: dict[str, list[str]] = {
    "assert_true": [
        r'""".*assert\s+True.*"""',         # In docstring
        r"#.*assert\s+True",                # In comment
        r"assert\s+True\s*,\s*['\"]",       # With message: assert True, "reason"
    ],
    "echo_success": [
        r"#.*echo.*Success",                # In comment
        r'""".*Success.*"""',               # In docstring
        r"if\s+.*;\s*then\s+echo\s+Success", # Conditional success
    ],
    "placeholder": [
        r'""".*TODO.*"""',                  # In docstring
        r"#\s*TODO:\s*\w+\s*-",             # Tracked TODO with ticket
    ],
    "coverage_manipulation": [
        r"pragma:\s*no\s*cover\s*#\s*\w{3,}", # With documented reason
        r"type:\s*ignore\s*\[\w+\]",          # Specific ignore: type: ignore[arg-type]
    ],
    "empty_exception": [
        r"except\s*:\s*\n\s*#\s*\w{10,}",   # With comment explanation
        r"except\s*:\s*\n\s*logger\.",      # With logging
    ],
}


# =============================================================================
# FILE TYPE PATTERNS
# =============================================================================
# Patterns applicable to specific file types only.

FILE_TYPE_PATTERNS: dict[str, list[str]] = {
    "python": ["assert_true", "placeholder", "coverage_manipulation",
               "mock_abuse", "empty_exception", "hardcoded_test_data"],
    "shell": ["echo_success", "cicd_bypass"],
    "yaml": ["cicd_bypass"],
    "javascript": ["echo_success"],
    "typescript": ["echo_success"],
}
