import asyncio
import logging
from typing import Any
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import db_manager
from models.question_bank import QuestionBankItem, QuestionDifficultyLevel
from services.irt_calibration_service import IRTCalibrationService
from core.worker_pools import NLP_POOL

logger = logging.getLogger("irt_daemon")

def sync_calibrate_wrapper(
    calibrator: IRTCalibrationService,
    question_text: str,
    options: list[str],
    subject: str,
    initial_difficulty: str
) -> Any:
    """
    Runs the asynchronous calibrate_question_irt method inside a separate 
    thread pool using a dedicated event loop. This prevents CPU-bound 
    Turkish NLP/morphology logic from blocking FastAPI's main event loop.
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(
            calibrator.calibrate_question_irt(
                question_text=question_text,
                options=options,
                subject=subject,
                initial_difficulty=initial_difficulty
            )
        )
    finally:
        loop.close()

class IRTCalibrationDaemon:
    """
    State-Machine background daemon worker for continuous IRT calibration.
    Prevents Idle-in-Transaction issues by detaching objects and shutting down 
    sessions during heavy CPU calculations.
    """
    def __init__(self):
        self._running = False
        self._task = None
        self.cancel_event = asyncio.Event()
        self.calibrator = IRTCalibrationService()

    async def start(self):
        if self._running:
            return
        self._running = True
        self.cancel_event.clear()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("[IRT Daemon] Daemon started successfully.")

    async def stop(self):
        if not self._running:
            return
        self._running = False
        logger.info("[IRT Daemon] Stopping background worker...")
        self.cancel_event.set()
        if self._task:
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("[IRT Daemon] Daemon stopped successfully.")

    async def _run_loop(self):
        while self._running:
            try:
                # Phase 1: Retrieve batch of 100 questions (SKIP LOCKED for PG, standard for SQLite)
                questions_data = await self._fetch_uncalibrated_questions()
                if not questions_data:
                    # Idle sleep if no questions need calibration (SIGKILL-proof interruptible wait)
                    try:
                        await asyncio.wait_for(self.cancel_event.wait(), timeout=60.0)
                    except asyncio.TimeoutError:
                        pass
                    continue

                # Phase 2: Compute parameters in NLP_POOL (Event Loop is not blocked)
                calibrated_results = []
                for q in questions_data:
                    if not self._running:
                        break
                    
                    try:
                        # Map difficulty levels to standard string values (kolay/orta/zor)
                        dif_lvl = q["difficulty_level"]
                        if isinstance(dif_lvl, QuestionDifficultyLevel):
                            dif_str = dif_lvl.value
                        elif hasattr(dif_lvl, "name"):
                            dif_str = dif_lvl.name.lower()
                        else:
                            dif_str = str(dif_lvl).lower()
                        
                        if "easy" in dif_str or "kolay" in dif_str:
                            dif_param = "kolay"
                        elif "hard" in dif_str or "zor" in dif_str:
                            dif_param = "zor"
                        else:
                            dif_param = "orta"

                        # Run CPU-bound morphology + readability logic in bulkheaded NLP_POOL
                        loop = asyncio.get_running_loop()
                        params = await loop.run_in_executor(
                            NLP_POOL,
                            sync_calibrate_wrapper,
                            self.calibrator,
                            q["question_text"],
                            q["options"],
                            q["subject_area"] or "Matematik",
                            dif_param
                        )
                        
                        calibrated_results.append({
                            "id": q["id"],
                            "difficulty": params.difficulty,
                            "discrimination": params.discrimination,
                            "guessing": params.guessing,
                            "morphology_complexity": params.morphology_complexity,
                            "readability_score": params.readability_score
                        })
                    except Exception as e:
                        # Silent Death Protection: log error and continue with next questions in batch
                        logger.error(f"[IRT Daemon] Failed calibration for question {q['id']}: {e!s}")

                # Phase 3: Update database in a new short-lived transaction
                if calibrated_results and self._running:
                    await self._update_questions_db(calibrated_results)

                # Batch pause to throttle backpressure (Interruptible sleep)
                try:
                    await asyncio.wait_for(self.cancel_event.wait(), timeout=2.0)
                except asyncio.TimeoutError:
                    pass

            except Exception as e:
                # Global silent loop crash protection
                logger.error(f"[IRT Daemon] Unexpected error in daemon iteration: {e!s}", exc_info=True)
                await asyncio.sleep(5)

    async def _fetch_uncalibrated_questions(self) -> list[dict]:
        """
        Fetches up to 100 uncalibrated questions in a short-lived transaction.
        Uses SKIP LOCKED on PostgreSQL to support multi-worker scaling,
        and standard select on SQLite.
        """
        async with db_manager.get_session() as session:
            try:
                stmt = select(QuestionBankItem).where(
                    (QuestionBankItem.is_active == True) &
                    ((QuestionBankItem.is_calibrated == False) | (QuestionBankItem.irt_difficulty == 0.0))
                )
                
                # Check dialect to avoid syntax error in SQLite
                if session.bind.dialect.name == 'postgresql':
                    stmt = stmt.with_for_update(skip_locked=True)
                
                stmt = stmt.limit(100)
                
                res = await session.execute(stmt)
                questions = res.scalars().all()
                
                # Detach items from session by mapping to basic dict DTOs
                data = []
                for q in questions:
                    options = [q.option_a, q.option_b, q.option_c, q.option_d]
                    if q.option_e:
                        options.append(q.option_e)
                        
                    data.append({
                        "id": q.id,
                        "question_text": q.question_text,
                        "options": options,
                        "subject_area": q.subject_area,
                        "difficulty_level": q.difficulty_level
                    })
                return data
            except Exception as e:
                logger.error(f"[IRT Daemon] Error fetching questions: {e!s}")
                return []

    async def _update_questions_db(self, results: list[dict]):
        """
        Updates questions in a fresh, isolated short-lived transaction.
        """
        async with db_manager.get_session() as session:
            try:
                for r in results:
                    stmt = update(QuestionBankItem).where(QuestionBankItem.id == r["id"]).values(
                        irt_difficulty=r["difficulty"],
                        irt_discrimination=r["discrimination"],
                        irt_guessing=r["guessing"],
                        morphology_complexity=r["morphology_complexity"],
                        readability_score=r["readability_score"],
                        is_calibrated=True
                    )
                    await session.execute(stmt)
                # Session is automatically committed on exiting get_session context manager
                logger.info(f"[IRT Daemon] Successfully updated {len(results)} questions in DB.")
            except Exception as e:
                logger.error(f"[IRT Daemon] Error updating database: {e!s}")

# Singleton instance
irt_daemon = IRTCalibrationDaemon()
