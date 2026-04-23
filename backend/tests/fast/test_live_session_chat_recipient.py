"""Live session private chat: recipient must be host or participant."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from api.live_session_routes import _verify_private_chat_recipient


@pytest.mark.asyncio
async def test_private_chat_recipient_host_allowed() -> None:
    sid = uuid4()
    host_id = uuid4()
    db = AsyncMock()
    r_host = MagicMock()
    r_host.first.return_value = MagicMock(host_id=host_id)
    db.execute = AsyncMock(return_value=r_host)
    await _verify_private_chat_recipient(sid, host_id, db)
    assert db.execute.await_count == 1


@pytest.mark.asyncio
async def test_private_chat_recipient_stranger_denied() -> None:
    sid = uuid4()
    host_id = uuid4()
    stranger = uuid4()
    db = AsyncMock()
    r_host = MagicMock()
    r_host.first.return_value = MagicMock(host_id=host_id)
    r_part = MagicMock()
    r_part.first.return_value = None
    db.execute = AsyncMock(side_effect=[r_host, r_part])
    with pytest.raises(HTTPException) as ei:
        await _verify_private_chat_recipient(sid, stranger, db)
    assert ei.value.status_code == 403


@pytest.mark.asyncio
async def test_viewer_is_session_host_true() -> None:
    from api.live_session_routes import _viewer_is_session_host

    sid = uuid4()
    host = uuid4()
    db = AsyncMock()
    user = MagicMock()
    user.id = host
    r = MagicMock()
    r.first.return_value = MagicMock(host_id=host)
    db.execute = AsyncMock(return_value=r)
    assert await _viewer_is_session_host(sid, user, db) is True


@pytest.mark.asyncio
async def test_viewer_is_session_host_false() -> None:
    from api.live_session_routes import _viewer_is_session_host

    sid = uuid4()
    host = uuid4()
    peer = uuid4()
    db = AsyncMock()
    user = MagicMock()
    user.id = peer
    r = MagicMock()
    r.first.return_value = MagicMock(host_id=host)
    db.execute = AsyncMock(return_value=r)
    assert await _viewer_is_session_host(sid, user, db) is False


@pytest.mark.asyncio
async def test_private_chat_recipient_participant_allowed() -> None:
    sid = uuid4()
    host_id = uuid4()
    peer = uuid4()
    db = AsyncMock()
    r_host = MagicMock()
    r_host.first.return_value = MagicMock(host_id=host_id)
    r_part = MagicMock()
    r_part.first.return_value = (1,)
    db.execute = AsyncMock(side_effect=[r_host, r_part])
    await _verify_private_chat_recipient(sid, peer, db)
    assert db.execute.await_count == 2
