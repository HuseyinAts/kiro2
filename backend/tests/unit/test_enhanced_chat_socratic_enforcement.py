"""U04 — enforce_socratic_output() birim testleri.

Kaynak: docs/superpowers/specs/2026-08-12-u04-socratic-guardrail-design.md
"""

from unittest.mock import AsyncMock

import pytest

from api.enhanced_chat import SOCRATIC_FALLBACK_MESSAGE, enforce_socratic_output


@pytest.mark.asyncio
async def test_direct_mode_passthrough_even_if_looks_like_leak():
    """teaching_mode != 'socratic' ise direkt cevap bir ihlal DEĞİL — dokunma."""
    regenerate = AsyncMock(return_value="asla cagirilmamali")
    result = await enforce_socratic_output("C) 4", "direct", regenerate)
    assert result == "C) 4"
    regenerate.assert_not_called()


@pytest.mark.asyncio
async def test_clean_socratic_response_passthrough_no_regenerate():
    regenerate = AsyncMock(return_value="asla cagirilmamali")
    clean = "Once dusunelim: esitligin iki tarafinda ayni islemi yapabilir miyiz?"
    result = await enforce_socratic_output(clean, "socratic", regenerate)
    assert result == clean
    regenerate.assert_not_called()


@pytest.mark.asyncio
async def test_leak_triggers_regenerate_and_clean_retry_wins():
    regenerate = AsyncMock(return_value="Guzel soru! Ilk adim ne olmali sence?")
    result = await enforce_socratic_output("C) 4", "socratic", regenerate)
    assert result == "Guzel soru! Ilk adim ne olmali sence?"
    regenerate.assert_awaited_once()


@pytest.mark.asyncio
async def test_leak_persists_after_retry_falls_back_to_template():
    regenerate = AsyncMock(return_value="C")  # retry de siziyor
    result = await enforce_socratic_output("C) 4", "socratic", regenerate)
    assert result == SOCRATIC_FALLBACK_MESSAGE
    regenerate.assert_awaited_once()


@pytest.mark.asyncio
async def test_empty_regenerate_result_falls_back_to_template():
    regenerate = AsyncMock(return_value="")  # backend hata verdi, bos dondu
    result = await enforce_socratic_output("C) 4", "socratic", regenerate)
    assert result == SOCRATIC_FALLBACK_MESSAGE
