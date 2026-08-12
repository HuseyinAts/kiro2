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
    from fastapi import Request
    from fastapi.responses import JSONResponse

    from api import enhanced_chat as mod

    payload = ChatMessageRequest(
        student_id="STU_probe",
        message="test",
        subject="matematik",
    )
    req = MagicMock(spec=Request)
    res = JSONResponse({})
    user, db = MagicMock(), AsyncMock()

    with (
        patch.object(mod.limiter, "enabled", False),
        patch.object(
            mod, "_verify_enhanced_chat_student_context", new_callable=AsyncMock
        ) as vctx,
        patch.object(mod, "_verify_chat_tables", new_callable=AsyncMock) as vtbl,
    ):
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


@pytest.mark.asyncio
async def test_call_llm_ollama_leak_triggers_regenerate_and_uses_clean_retry():
    from api import enhanced_chat as mod

    leak_resp = MagicMock(status_code=200)
    leak_resp.json.return_value = {"message": {"content": "C) 4"}}
    clean_resp = MagicMock(status_code=200)
    clean_resp.json.return_value = {
        "message": {"content": "Once dusunelim: esitligin iki tarafinda ne yapmaliyiz?"}
    }

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=[leak_resp, clean_resp])
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = False

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await mod._call_llm(
            "2x+5=13 ise x kactir? A)2 B)3 C)4 D)5 E)6", "matematik", "socratic"
        )

    assert result.message == "Once dusunelim: esitligin iki tarafinda ne yapmaliyiz?"
    assert mock_client.post.call_count == 2


@pytest.mark.asyncio
async def test_call_llm_clean_response_never_regenerates():
    from api import enhanced_chat as mod

    clean_resp = MagicMock(status_code=200)
    clean_resp.json.return_value = {
        "message": {"content": "Guzel soru! Once neyi bildigimizi listeleyelim mi?"}
    }

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=clean_resp)
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = False

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await mod._call_llm("2x+5=13 nasil cozulur?", "matematik", "socratic")

    assert result.message == "Guzel soru! Once neyi bildigimizi listeleyelim mi?"
    assert mock_client.post.call_count == 1
