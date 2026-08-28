#!/usr/bin/env python
"""
PreToolUse Hook — Reward Hacking Prevention (Write|Edit blocker)

Matcher: Write|Edit (set in settings.json)
EXIT CODE 2: BLOCKS the write — file is NOT saved to disk
EXIT CODE 0: ALLOW

This hook checks file CONTENT before it's written. Unlike PostToolUse
(which is non-blocking), PreToolUse exit 2 actually prevents the operation.

Bash security is handled by permissions.deny in settings.json (declarative).
Regex blacklisting shell commands is a losing game — permissions.deny is
Claude Code's built-in mechanism and more reliable.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from functools import lru_cache
from pathlib import Path

# Windows cp1254 crash fix
if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and sys.stderr.encoding and sys.stderr.encoding.lower().startswith("cp"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# Patterns that indicate fake/placeholder code (reward hacking)
REWARD_HACKING_PATTERNS: list[tuple[str, str]] = [
    # Fake assertions
    (r"^\s*assert\s+True\s*$", "assert True"),
    (r"^\s*assert\s+true\s*$", "assert true"),
    (r"ASSERT_TRUE\s*\(\s*[Tt]rue\s*\)", "ASSERT_TRUE(true)"),
    (r"expect\s*\(\s*true\s*\)\s*\.\s*toBe\s*\(\s*true\s*\)", "expect(true).toBe(true)"),
    # Trivial numeric assertions (no legitimate use)
    (r"^\s*assert\s+1\s*==\s*1\s*$", "assert 1 == 1"),
    (r"expect\s*\(\s*1\s*\)\s*\.\s*toBe\s*\(\s*1\s*\)", "expect(1).toBe(1)"),
    # Fake success signals
    (r"""print\s*\(\s*['"]Success['"]\s*\)""", "print('Success')"),
    # Stub markers
    (r"pass\s*#\s*placeholder", "pass # placeholder"),
    (r"return\s+None\s*#\s*stub", "return None # stub"),
    (r"#\s*FIXME:\s*fake", "# FIXME: fake"),
]

# Files to skip (hook infrastructure, config)
SKIP_PATH_PARTS = {".claude", "node_modules", ".git", "__pycache__"}


@lru_cache(maxsize=1)
def _bastirici():
    """String literal / yorum bastiricisini yukle; yoksa None (#452).

    Backend bekcisiyle AYNI mantik kullanilir — kopyalanmaz. `literal_spans.py`
    yalnizca stdlib'e (io, tokenize, functools) baglidir ve goreli import
    icermez, bu yuzden paket baglami olmadan dosya yolundan yuklenebilir.

    HATA DURUMUNDA None -> hicbir bastirma yapilmaz, yani hook BUGUNKU gibi
    bloklamaya devam eder. Belirsizlikte bekci kor degil ACIK kalir; bu,
    literal_spans.py'nin kendi FAIL-OPEN politikasiyla ayni yon.
    """
    try:
        yol = (
            Path(__file__).resolve().parents[2]
            / "backend"
            / "hooks"
            / "reward_hacking"
            / "literal_spans.py"
        )
        spec = importlib.util.spec_from_file_location("_kiro2_literal_spans", yol)
        if spec is None or spec.loader is None:
            return None
        modul = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modul)
        return modul.bulgu_bastirilmali
    except Exception:
        return None


def _kod_disi(file_path: str, content: str, offset: int, desen: str) -> bool:
    """Eslesme string literali / yorum icinde mi (yani TEST VERISI mi)?"""
    bastir = _bastirici()
    if bastir is None:
        return False
    try:
        return bool(bastir(file_path, content, offset, desen))
    except Exception:
        return False


def extract_content(hook_input: dict) -> tuple[str, str]:
    """Extract writable content and file_path from hook input.

    Write tool: tool_input.content
    Edit tool: tool_input.new_string
    """
    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if tool_name == "Write":
        return tool_input.get("content", ""), file_path
    elif tool_name == "Edit":
        return tool_input.get("new_string", ""), file_path
    return "", file_path


def check_reward_hacking(content: str, file_path: str = "") -> list[tuple[str, str]]:
    """Check content for reward hacking patterns. Returns (pattern, label) matches.

    String literali icindeki eslesme TEST VERISIDIR, kod degil (#452). Bu hook
    BLOKLAYICI oldugu icin yanlis-pozitif pahalidir: gelistirici mesru bir
    dosyayi kaydedemez. Olculdu — uclu tirnakli bir fixture icindeki fake
    assertion yazmayi engelliyordu (bu dosyanin kendi testinin ilk surumu de
    bu yuzden bloklandi).
    """
    matches = []
    for pattern, label in REWARD_HACKING_PATTERNS:
        for m in re.finditer(pattern, content, re.MULTILINE):
            if _kod_disi(file_path, content, m.start(), pattern):
                continue
            matches.append((pattern, label))
            break
    return matches


def is_test_file(path: str) -> bool:
    """Check if file is a test file.

    Matches: test_foo.py, tests/bar.py, foo.test.ts, foo.spec.jsx
    Avoids:  contest_service.py, attestation.py (false positives)
    """
    normalized = path.replace("\\", "/")
    filename = normalized.rsplit("/", 1)[-1] if "/" in normalized else normalized
    return bool(
        filename.startswith("test_")
        or filename.startswith("tests_")
        or "/tests/" in normalized
        or re.search(r"\.test\.(ts|tsx|js|jsx)$", filename)
        or re.search(r"\.spec\.(ts|tsx|js|jsx)$", filename)
    )


def check_empty_test(content: str, file_path: str = "") -> bool:
    """Check for empty test bodies (CRLF-safe, Python + TS/JS).

    `check_reward_hacking` ile ayni literal kurali gecerli (#452): fixture
    string'i icindeki bos test govdesi test VERISIDIR, kod degil.
    """
    desenler = (
        # Python: def test_xxx(): \n    pass
        r"def\s+test_\w+\([^)]*\):\s*\r?\n\s*(pass|\.\.\.)\s*\r?\n",
        # Python async def
        r"async\s+def\s+test_\w+\([^)]*\):\s*\r?\n\s*(pass|\.\.\.)\s*\r?\n",
        # TS/JS: it('...', () => {}) or test('...', () => {})
        r"(it|test)\s*\([^)]*,\s*\(\)\s*=>\s*\{\s*\}\s*\)",
    )
    for desen in desenler:
        for m in re.finditer(desen, content):
            if _kod_disi(file_path, content, m.start(), desen):
                continue
            return True
    return False


def main() -> int:
    """Main entry point."""
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, OSError):
        return 0

    content, file_path = extract_content(hook_input)

    # Nothing to check
    if not content or not file_path:
        return 0

    # Skip infrastructure files
    if any(part in file_path.replace("\\", "/").split("/") for part in SKIP_PATH_PARTS):
        return 0

    errors: list[str] = []

    # 1. Reward hacking detection
    matches = check_reward_hacking(content, file_path)
    for _pattern, label in matches:
        errors.append(f"Reward hacking: '{label}'")

    # 2. Empty test body detection
    if is_test_file(file_path) and check_empty_test(content, file_path):
        errors.append("Empty test body (pass/...) — tests must have real assertions")

    # Verdict
    if errors:
        # Structured JSON output — Claude Code parses this on exit 2
        result = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": "; ".join(errors),
            }
        }
        json.dump(result, sys.stdout)
        print(f"\nBLOCKED: {'; '.join(errors)}", file=sys.stderr)
        return 2

    # --- TDD Bug Fix Gate reminder (non-blocking) ---
    # Source files only (not tests, not config, not hooks)
    normalized_path = file_path.replace("\\", "/")
    is_src_file = (
        ("backend/" in normalized_path or "frontend/src/" in normalized_path)
        and not is_test_file(file_path)
        and "/alembic/" not in normalized_path
    )
    if is_src_file:
        print(
            "[TDD Gate] Bug fix ise SIRASYLA: "
            "1) Root Cause Analysis tablosu goster (debugging-first.md) "
            "2) Fail eden test bul/yaz 3) Test FAIL dogrula "
            "4) Fix yaz 5) Test PASS dogrula. "
            "Bu adimlar ATLANAMAZ.",
            file=sys.stderr,
        )

    # --- Deprecation Guard reminder (non-blocking) ---
    # Warn when moving files to _deprecated/ — check imports first
    if "_deprecated" in normalized_path:
        print(
            "[Deprecation Guard] _deprecated/ hedefli islem tespit edildi. "
            "Tasimadan ONCE: grep -r 'from.*<dosya_adi>' ile TUM import "
            "referanslarini tara. Import chain kirilmasi 3+ Docker rebuild'e mal olur.",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"[WARN] pre-tool-use hook exception: {e}", file=sys.stderr)
        sys.exit(0)
