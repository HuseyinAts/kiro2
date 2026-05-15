"""Judge API clients — Opus + Gemini Pro wrappers.

DESIGN:
  - Each call returns a uniform dict: {ok, raw, parsed, tokens, latency_ms, error}
  - parse_response handled here, caller gets validated dict or error
  - Retry policy from spec §8.1 (network=2 retry, 429=sleep+retry, safety=no retry)
  - Gemini safety_settings configurable (Session 161+ BLOCK_NONE for Geometri)

USAGE (after API keys set):
  from backend.scripts.judge import client, prompt_v1

  user = prompt_v1.build_user_prompt(...)
  opus_result = client.call_opus(
      system=prompt_v1.build_opus_system(),
      user=user,
      api_key=os.getenv("ANTHROPIC_API_KEY"),
  )
  pro_result = client.call_pro(
      full_prompt=prompt_v1.build_pro_full_prompt(user_prompt=user),
      api_key=os.getenv("GEMINI_API_KEY"),
  )
"""

from __future__ import annotations

import os
import time
from typing import Any

from .prompt_v1 import JudgeParseError, parse_response

# Lazy SDK imports — only loaded when first call happens
_anthropic_client = None
_genai_configured = False


# ============================================================================
# OPUS CLIENT (Anthropic)
# ============================================================================


def _get_anthropic():
    """Lazy import + singleton anthropic.Anthropic client."""
    global _anthropic_client
    if _anthropic_client is None:
        import anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY env var required")
        _anthropic_client = anthropic.Anthropic(api_key=api_key)
    return _anthropic_client


def call_opus(
    *,
    system: str,
    user: str,
    model: str = "claude-opus-4-7",
    max_tokens: int = 256,
    temperature: float = 0.0,
    max_retries: int = 2,
) -> dict[str, Any]:
    """
    Call Anthropic Opus 4.7 with judge prompt.

    Returns:
        {
          "ok": bool,
          "raw": str,                    # raw model output (None on error)
          "parsed": dict | None,         # parsed verdict dict (None on parse fail)
          "tokens": {"in": int, "out": int},
          "latency_ms": int,
          "error": str | None,           # error category if ok=False
          "retry_count": int,
        }
    """
    client = _get_anthropic()
    attempt = 0
    last_error = None

    while attempt <= max_retries:
        t0 = time.time()
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            latency_ms = int((time.time() - t0) * 1000)
            raw = resp.content[0].text if resp.content else ""
            tokens = {
                "in": resp.usage.input_tokens,
                "out": resp.usage.output_tokens,
            }

            try:
                parsed = parse_response(raw)
                return {
                    "ok": True,
                    "raw": raw,
                    "parsed": parsed,
                    "tokens": tokens,
                    "latency_ms": latency_ms,
                    "error": None,
                    "retry_count": attempt,
                }
            except JudgeParseError as e:
                last_error = f"parse_error: {e}"
                if attempt < max_retries:
                    attempt += 1
                    continue
                return {
                    "ok": False,
                    "raw": raw,
                    "parsed": None,
                    "tokens": tokens,
                    "latency_ms": latency_ms,
                    "error": last_error,
                    "retry_count": attempt,
                }

        except Exception as e:
            err_str = str(e)
            latency_ms = int((time.time() - t0) * 1000)

            # Rate limit → backoff
            if "429" in err_str or "rate_limit" in err_str.lower():
                if attempt < max_retries:
                    time.sleep(30)
                    attempt += 1
                    last_error = f"rate_limit (retry {attempt})"
                    continue
                last_error = "rate_limit_exhausted"
            # Network / 5xx → exponential backoff
            elif "timeout" in err_str.lower() or "5" in err_str[:3]:
                if attempt < max_retries:
                    time.sleep(2**attempt)
                    attempt += 1
                    last_error = f"network (retry {attempt})"
                    continue
                last_error = f"network_exhausted: {err_str[:80]}"
            else:
                last_error = f"opus_api_error: {err_str[:100]}"

            return {
                "ok": False,
                "raw": None,
                "parsed": None,
                "tokens": {"in": 0, "out": 0},
                "latency_ms": latency_ms,
                "error": last_error,
                "retry_count": attempt,
            }

    return {
        "ok": False,
        "raw": None,
        "parsed": None,
        "tokens": {"in": 0, "out": 0},
        "latency_ms": 0,
        "error": last_error or "unknown",
        "retry_count": attempt,
    }


# ============================================================================
# PRO CLIENT (Gemini 2.5 Pro)
# ============================================================================


def _ensure_genai_configured(api_key: str | None = None):
    """Lazy import + global configure for google.generativeai."""
    global _genai_configured
    if not _genai_configured:
        import google.generativeai as genai

        key = api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("GEMINI_API_KEY env var required")
        genai.configure(api_key=key)
        _genai_configured = True


def call_pro(
    *,
    full_prompt: str,
    model_name: str = "gemini-2.5-pro",
    max_output_tokens: int = 256,
    temperature: float = 0.0,
    safety_block_dangerous: bool = False,
    max_retries: int = 2,
) -> dict[str, Any]:
    """
    Call Gemini 2.5 Pro with full judge prompt (system + few-shot + user merged).

    Args:
        safety_block_dangerous: If False (default), passes through standard safety.
            Set True only for math/geometry retry pile (Session 160 finding —
            geometric figures trigger HARM_CATEGORY_DANGEROUS_CONTENT false positive).
            spec §8.2 stratejisi.

    Returns same dict shape as call_opus.
    """
    _ensure_genai_configured()
    import google.generativeai as genai

    safety_settings = None
    if safety_block_dangerous:
        # Session 161+ Geometri retry policy
        safety_settings = {
            "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
        }

    model = genai.GenerativeModel(
        model_name,
        generation_config={
            "temperature": temperature,
            "max_output_tokens": max_output_tokens,
        },
        safety_settings=safety_settings,
    )

    attempt = 0
    last_error = None

    while attempt <= max_retries:
        t0 = time.time()
        try:
            resp = model.generate_content(full_prompt)
            latency_ms = int((time.time() - t0) * 1000)

            # Gemini quirk: response.text raises if finish_reason != STOP
            # (Session 160 Geometri pattern). Treat as safety_block.
            try:
                raw = resp.text
            except Exception as e:
                # Don't retry safety blocks — Faz 5.8 retry pile
                err_str = str(e)
                if "response.text" in err_str or "finish_reason" in err_str:
                    return {
                        "ok": False,
                        "raw": None,
                        "parsed": None,
                        "tokens": {"in": 0, "out": 0},
                        "latency_ms": latency_ms,
                        "error": "gemini_safety_blocked",
                        "retry_count": attempt,
                    }
                raise

            # Token usage from usage_metadata
            tokens = {
                "in": getattr(resp.usage_metadata, "prompt_token_count", 0)
                if hasattr(resp, "usage_metadata")
                else 0,
                "out": getattr(resp.usage_metadata, "candidates_token_count", 0)
                if hasattr(resp, "usage_metadata")
                else 0,
            }

            try:
                parsed = parse_response(raw)
                return {
                    "ok": True,
                    "raw": raw,
                    "parsed": parsed,
                    "tokens": tokens,
                    "latency_ms": latency_ms,
                    "error": None,
                    "retry_count": attempt,
                }
            except JudgeParseError as e:
                last_error = f"parse_error: {e}"
                if attempt < max_retries:
                    attempt += 1
                    continue
                return {
                    "ok": False,
                    "raw": raw,
                    "parsed": None,
                    "tokens": tokens,
                    "latency_ms": latency_ms,
                    "error": last_error,
                    "retry_count": attempt,
                }

        except Exception as e:
            err_str = str(e)
            latency_ms = int((time.time() - t0) * 1000)

            if "429" in err_str or "quota" in err_str.lower():
                if attempt < max_retries:
                    time.sleep(30)
                    attempt += 1
                    last_error = f"rate_limit (retry {attempt})"
                    continue
                last_error = "rate_limit_exhausted"
            elif "timeout" in err_str.lower():
                if attempt < max_retries:
                    time.sleep(2**attempt)
                    attempt += 1
                    last_error = f"network (retry {attempt})"
                    continue
                last_error = f"network_exhausted: {err_str[:80]}"
            else:
                last_error = f"pro_api_error: {err_str[:100]}"

            return {
                "ok": False,
                "raw": None,
                "parsed": None,
                "tokens": {"in": 0, "out": 0},
                "latency_ms": latency_ms,
                "error": last_error,
                "retry_count": attempt,
            }

    return {
        "ok": False,
        "raw": None,
        "parsed": None,
        "tokens": {"in": 0, "out": 0},
        "latency_ms": 0,
        "error": last_error or "unknown",
        "retry_count": attempt,
    }


# ============================================================================
# DUMMY MODE (for runner.py dry-run, no API calls)
# ============================================================================


def call_dummy(
    *,
    verdict: str = "PASS",
    answer: str = "B",
    issue: str | None = None,
) -> dict[str, Any]:
    """Synthetic response for runner --dry-run testing."""
    return {
        "ok": True,
        "raw": '{"verdict": "%s", "agreed_answer": "%s", ...}' % (verdict, answer),
        "parsed": {
            "verdict": verdict,
            "agreed_answer": answer,
            "issue": issue,
            "confidence": 0.85,
            "reasoning": "dummy",
        },
        "tokens": {"in": 757, "out": 100},
        "latency_ms": 1,
        "error": None,
        "retry_count": 0,
    }
