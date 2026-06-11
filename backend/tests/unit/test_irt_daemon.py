import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from core.irt_daemon import IRTCalibrationDaemon, sync_calibrate_wrapper
from services.irt_calibration_service import IRTParameters

@pytest.mark.asyncio
async def test_irt_daemon_start_stop():
    daemon = IRTCalibrationDaemon()
    
    # Patch the run loop so it doesn't execute during the start/stop test
    with patch.object(daemon, "_run_loop", return_value=None):
        await daemon.start()
        assert daemon._running is True
        assert daemon._task is not None
        
        await daemon.stop()
        assert daemon._running is False

@pytest.mark.asyncio
async def test_irt_daemon_graceful_shutdown_timeout():
    daemon = IRTCalibrationDaemon()
    daemon._running = True
    daemon.cancel_event.set()
    
    # Verify stopping daemon exits immediately and does not hang for 60 seconds
    start_time = asyncio.get_event_loop().time()
    await daemon.stop()
    end_time = asyncio.get_event_loop().time()
    
    # It must stop in less than 1.0 second
    assert (end_time - start_time) < 1.0

@pytest.mark.asyncio
async def test_irt_daemon_fetch_uncalibrated_questions():
    daemon = IRTCalibrationDaemon()
    mock_session = AsyncMock()
    mock_session.bind.dialect.name = "sqlite"
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    # Mock db_manager get_session to return our mock session context manager
    with patch("core.irt_daemon.db_manager.get_session") as mock_get_session:
        async_cm = AsyncMock()
        async_cm.__aenter__ = AsyncMock(return_value=mock_session)
        async_cm.__aexit__ = AsyncMock(return_value=None)
        mock_get_session.return_value = async_cm
        
        res = await daemon._fetch_uncalibrated_questions()
        assert isinstance(res, list)
        assert len(res) == 0

def test_sync_calibrate_wrapper():
    mock_calibrator = MagicMock()
    mock_params = IRTParameters(
        difficulty=0.5,
        discrimination=1.2,
        guessing=0.25,
        morphology_complexity=0.3,
        readability_score=0.75,
        calibration_confidence=0.9
    )
    
    async def mock_async_calibrate(*args, **kwargs):
        return mock_params
        
    mock_calibrator.calibrate_question_irt = mock_async_calibrate
    
    res = sync_calibrate_wrapper(
        mock_calibrator,
        "Bu bir test sorusudur ve en az 15 karakter olmalıdır.",
        ["A", "B", "C", "D"],
        "Matematik",
        "orta"
    )
    assert res == mock_params
