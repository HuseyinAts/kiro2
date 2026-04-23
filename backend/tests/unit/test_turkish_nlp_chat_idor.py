"""F4: turkish_nlp_chat student_id gövdesi — verify_student_access."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import api.turkish_nlp_chat as chat_mod
from api.turkish_nlp_chat import (
    ChatMessageRequest,
    ContextManagementRequest,
    generate_step_by_step_solution,
    manage_conversation_context,
    send_chat_message,
)
from fastapi import BackgroundTasks


@pytest.mark.asyncio
async def test_send_chat_message_verifies_student_id() -> None:
    req = ChatMessageRequest(student_id="stu-chat-1", message="merhaba")
    user, db = MagicMock(), AsyncMock()
    bt = BackgroundTasks()
    resp = MagicMock(
        response_text="ok",
        explanation_type="t",
        difficulty_level="orta",
        related_concepts=[],
        follow_up_questions=[],
        motivational_elements=[],
        confidence_score=0.9,
        bionic_reading_text=None,
    )
    mock_sys = MagicMock()
    mock_sys.process_message = AsyncMock(return_value=resp)
    with patch.object(chat_mod, "verify_student_access", new_callable=AsyncMock) as v:
        v.return_value = True
        with patch.object(chat_mod, "_ensure_initialized", new_callable=AsyncMock):
            with patch.object(chat_mod, "turkish_nlp_chat_system", mock_sys):
                out = await send_chat_message(req, bt, user, db)
                v.assert_awaited_once_with("stu-chat-1", user, db)
                assert out.success is True


@pytest.mark.asyncio
async def test_step_by_step_verifies_student_id() -> None:
    req = ChatMessageRequest(student_id="stu-chat-3", message="coz")
    user, db = MagicMock(), AsyncMock()
    resp = MagicMock(
        response_text="adim",
        explanation_type="t",
        difficulty_level="orta",
        related_concepts=[],
        follow_up_questions=[],
        motivational_elements=[],
        confidence_score=0.9,
        bionic_reading_text=None,
    )
    mock_sys = MagicMock()
    mock_sys.process_message = AsyncMock(return_value=resp)
    with patch.object(chat_mod, "verify_student_access", new_callable=AsyncMock) as v:
        v.return_value = True
        with patch.object(chat_mod, "_ensure_initialized", new_callable=AsyncMock):
            with patch.object(chat_mod, "turkish_nlp_chat_system", mock_sys):
                out = await generate_step_by_step_solution(req, user, db)
                v.assert_awaited_once_with("stu-chat-3", user, db)
                assert out["success"] is True


@pytest.mark.asyncio
async def test_manage_context_clear_verifies_student_id() -> None:
    req = ContextManagementRequest(student_id="stu-chat-2", action="clear")
    user, db = MagicMock(), AsyncMock()
    mock_sys = MagicMock()
    mock_sys.clear_conversation_context = AsyncMock(return_value=True)
    with patch.object(chat_mod, "verify_student_access", new_callable=AsyncMock) as v:
        v.return_value = True
        with patch.object(chat_mod, "turkish_nlp_chat_system", mock_sys):
            out = await manage_conversation_context(req, user, db)
            v.assert_awaited_once_with("stu-chat-2", user, db)
            assert out["success"] is True
