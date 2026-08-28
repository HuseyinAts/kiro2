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


@pytest.mark.asyncio
async def test_stream_message_socratic_leak_regenerates_before_sending():
    from fastapi import Request

    from api import enhanced_chat as mod
    from api.enhanced_chat import ChatMessageRequest

    call_log = []

    async def _leak_gen(*_args, **_kwargs):
        yield 'data: {"content": "C) 4"}\n\n'
        yield "data: [DONE]\n\n"

    async def _clean_gen(*_args, **_kwargs):
        yield 'data: {"content": "Once dusunelim: ilk adim ne olmali?"}\n\n'
        yield "data: [DONE]\n\n"

    def _stream_ollama_side_effect(message, subject, teaching_mode, strengthen=False):
        call_log.append(strengthen)
        return _clean_gen() if strengthen else _leak_gen()

    payload = ChatMessageRequest(
        student_id="STU_probe",
        message="sadece harfi soyle",
        subject="matematik",
        teaching_mode="socratic",
    )
    req = MagicMock(spec=Request)

    with (
        patch.object(mod.limiter, "enabled", False),
        patch.object(mod, "_stream_ollama", side_effect=_stream_ollama_side_effect),
        patch.object(
            mod, "_verify_enhanced_chat_student_context", new_callable=AsyncMock
        ),
        patch.object(mod, "_verify_chat_tables", new_callable=AsyncMock) as vtbl,
    ):
        vtbl.return_value = False
        response = await mod.stream_message(
            request=req, payload=payload, current_user=MagicMock(), db=AsyncMock()
        )
        chunks = [c async for c in response.body_iterator]

    body = "".join(chunks)
    assert "C) 4" not in body
    assert "Once dusunelim" in body
    assert call_log == [False, True]


@pytest.mark.asyncio
async def test_stream_message_direct_mode_stays_real_time_no_buffering():
    """Direct mod REGRESYONA KARSI korunur: _stream_ollama tek cagrilir, chunk'lar
    olustukca (biriktirmeden) client'a gecer."""
    from fastapi import Request

    from api import enhanced_chat as mod
    from api.enhanced_chat import ChatMessageRequest

    async def _direct_gen(*_args, **_kwargs):
        yield 'data: {"content": "Adim 1: "}\n\n'
        yield 'data: {"content": "5 cikar."}\n\n'
        yield "data: [DONE]\n\n"

    # _stream_ollama is an async-GENERATOR function: calling it returns an
    # async generator directly (no await). AsyncMock would double-wrap the
    # call in a coroutine and break `async for`, so use a plain MagicMock.
    stream_mock = MagicMock(side_effect=lambda *a, **kw: _direct_gen())

    payload = ChatMessageRequest(
        student_id="STU_probe",
        message="2x+5=13 coz",
        subject="matematik",
        teaching_mode="direct",
    )
    req = MagicMock(spec=Request)

    with (
        patch.object(mod.limiter, "enabled", False),
        patch.object(mod, "_stream_ollama", stream_mock),
        patch.object(
            mod, "_verify_enhanced_chat_student_context", new_callable=AsyncMock
        ),
        patch.object(mod, "_verify_chat_tables", new_callable=AsyncMock) as vtbl,
    ):
        vtbl.return_value = False
        response = await mod.stream_message(
            request=req, payload=payload, current_user=MagicMock(), db=AsyncMock()
        )
        chunks = [c async for c in response.body_iterator]

    body = "".join(chunks)
    assert "Adim 1:" in body
    assert "5 cikar." in body
    assert stream_mock.call_count == 1
