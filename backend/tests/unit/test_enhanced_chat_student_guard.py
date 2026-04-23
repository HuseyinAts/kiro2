"""F4: enhanced_chat student_id — verify_student_access + history owner uid."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from api.enhanced_chat import (
    ChatMessageRequest,
    ChatMessageType,
    _verify_enhanced_chat_student_context,
)


@pytest.mark.asyncio
async def test_verify_context_skips_when_unauthenticated() -> None:
    await _verify_enhanced_chat_student_context("STU_any", None, AsyncMock())


@pytest.mark.asyncio
async def test_verify_context_503_when_no_db() -> None:
    user = MagicMock()
    with pytest.raises(HTTPException) as exc:
        await _verify_enhanced_chat_student_context("STU_1", user, None)
    assert exc.value.status_code == 503


@pytest.mark.asyncio
async def test_send_message_awaits_verify_student_access() -> None:
    from api import enhanced_chat as mod
    from fastapi import Request
    from fastapi.responses import JSONResponse

    payload = ChatMessageRequest(
        student_id="STU_probe",
        message="test",
        subject="matematik",
    )
    req = MagicMock(spec=Request)
    res = JSONResponse({})
    user, db = MagicMock(), AsyncMock()

    with patch.object(mod.limiter, "enabled", False):
        with patch.object(
            mod, "_verify_enhanced_chat_student_context", new_callable=AsyncMock
        ) as vctx:
            with patch.object(
                mod, "_verify_chat_tables", new_callable=AsyncMock
            ) as vtbl:
                vtbl.return_value = False
                with patch.object(mod, "_call_llm", new_callable=AsyncMock) as llm:
                    llm.return_value = MagicMock(
                        message="ok",
                        message_type=ChatMessageType.AI_RESPONSE,
                        confidence_score=0.9,
                    )
                    out = await mod.send_message(
                        request=req,
                        response=res,
                        payload=payload,
                        current_user=user,
                        db=db,
                    )
                    vctx.assert_awaited_once_with("STU_probe", user, db)
                    assert out["success"] is True
