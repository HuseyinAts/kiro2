"""
Sequential Reasoning Service
Main service for step-by-step problem solving with Multi-LLM support

Author: KIRO AI Team
Date: 2026-01-16

Updated: 2026-01-17
- Added SymPy math verification (REQ-4)
- Added topological sort for sub-problems (REQ-1.3)
"""

import hashlib
import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# Topological sort for dependencies (REQ-1.3)
from core.quality_gates.dependency_graph import DependencyGraph
from models.reasoning_models import (
    LLMProviderEnum,
    ReasoningCache,
    ReasoningSession,
    ReasoningSessionStatus,
    ReasoningStep,
    ReasoningStepTypeEnum,
)
from services.llm.ensemble_manager import MultiLLMEnsembleManager
from services.llm.multi_llm_config import LLMCapability, LLMProvider

# Logic validation (REQ-5)
from services.reasoning.logic_validation_service import (
    LogicValidationService,
    get_logic_validation_service,
)

# Math verification (REQ-4)
from services.reasoning.math_verification_service import (
    MathProblemType,
    MathVerificationService,
    get_math_verification_service,
)

logger = logging.getLogger(__name__)


class SequentialReasoningService:
    """
    Sequential Reasoning Service

    Provides step-by-step problem solving using multiple LLM providers.
    Supports ensemble voting, caching, and verification.
    """

    # Cache TTL (7 days as per spec REQ-7.5)
    CACHE_TTL_DAYS = 7

    def __init__(
        self,
        db: AsyncSession,
        enable_cache: bool = True,
        enable_ensemble: bool = True,
        enable_math_verification: bool = True,
        enable_logic_validation: bool = True,
    ):
        """
        Initialize service

        Args:
            db: Database session
            enable_cache: Enable reasoning cache
            enable_ensemble: Enable multi-LLM ensemble
            enable_math_verification: Enable SymPy math verification (REQ-4)
            enable_logic_validation: Enable formal logic validation (REQ-5)
        """
        self.db = db
        self.enable_cache = enable_cache
        self.enable_ensemble = enable_ensemble
        self.enable_math_verification = enable_math_verification
        self.enable_logic_validation = enable_logic_validation

        # Initialize ensemble manager (lazy)
        self._ensemble_manager: MultiLLMEnsembleManager | None = None

        # Initialize math verification service (REQ-4)
        self._math_verifier: MathVerificationService | None = None
        if enable_math_verification:
            self._math_verifier = get_math_verification_service()
            logger.info(f"Math verification enabled: SymPy available={self._math_verifier.sympy_available}")

        # Initialize logic validation service (REQ-5)
        self._logic_validator: LogicValidationService | None = None
        if enable_logic_validation:
            self._logic_validator = get_logic_validation_service()
            logger.info("Logic validation enabled")

    @property
    def ensemble_manager(self) -> MultiLLMEnsembleManager:
        """Get or create ensemble manager"""
        if self._ensemble_manager is None:
            self._ensemble_manager = MultiLLMEnsembleManager(
                enable_gemini=True,
                enable_openai=True,
                enable_claude=True,
                enable_qwen=True,
                gemini_thinking_mode=True,
            )
        return self._ensemble_manager

    async def solve(
        self,
        problem: str,
        provider: str | None = None,
        use_ensemble: bool = False,
        max_steps: int = 10,
        use_cache: bool = True,
        user_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """
        Solve a problem with sequential thinking

        Args:
            problem: Problem to solve
            provider: Preferred provider (gemini, openai, claude, qwen)
            use_ensemble: Use ensemble of all providers
            max_steps: Maximum reasoning steps
            use_cache: Check and use cache
            user_id: User ID for tracking

        Returns:
            Complete reasoning result
        """
        # Check cache first
        if use_cache and self.enable_cache:
            cached = await self._get_cached_reasoning(problem)
            if cached:
                return cached

        # Create session
        session = await self._create_session(
            problem=problem,
            provider=provider,
            use_ensemble=use_ensemble,
            user_id=user_id,
        )

        try:
            # Perform reasoning
            if use_ensemble and self.enable_ensemble:
                result = await self._solve_with_ensemble(
                    problem, max_steps, session
                )
            else:
                result = await self._solve_with_provider(
                    problem, provider, max_steps, session
                )

            # Update session with results
            await self._update_session_with_result(session, result)

            # Cache result
            if use_cache and self.enable_cache:
                await self._cache_reasoning(problem, result)

            return result

        except Exception:
            # Mark session as failed
            session.status = ReasoningSessionStatus.FAILED
            await self.db.commit()
            raise

    async def _create_session(
        self,
        problem: str,
        provider: str | None,
        use_ensemble: bool,
        user_id: uuid.UUID | None,
    ) -> ReasoningSession:
        """Create a new reasoning session"""
        provider_enum = None
        if provider:
            try:
                provider_enum = LLMProviderEnum(provider.lower())
            except ValueError:
                provider_enum = LLMProviderEnum.GEMINI

        session = ReasoningSession(
            problem=problem,
            provider=provider_enum or LLMProviderEnum.GEMINI,
            use_ensemble=use_ensemble,
            status=ReasoningSessionStatus.IN_PROGRESS,
            user_id=user_id,
        )

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        return session

    async def _solve_with_ensemble(
        self, problem: str, max_steps: int, session: ReasoningSession
    ) -> dict[str, Any]:
        """Solve using ensemble of all providers"""
        result = await self.ensemble_manager.sequential_thinking_ensemble(
            problem=problem,
            max_steps=max_steps,
            use_voting=True,
        )

        # Store steps in database
        await self._store_steps(session, result.get("steps", []))

        return result

    async def _solve_with_provider(
        self,
        problem: str,
        provider: str | None,
        max_steps: int,
        session: ReasoningSession,
    ) -> dict[str, Any]:
        """Solve using specific provider"""
        # Map string to enum
        provider_enum = None
        if provider:
            try:
                provider_enum = LLMProvider(provider.lower())
            except ValueError:
                pass

        result = await self.ensemble_manager.solve_with_best_provider(
            problem=problem,
            capability=LLMCapability.SEQUENTIAL_THINKING,
        )

        # Store steps
        await self._store_steps(session, result.get("steps", []))

        return result

    async def _store_steps(
        self, session: ReasoningSession, steps: list[dict[str, Any]]
    ) -> None:
        """
        Store reasoning steps in database with optional math verification.

        REQ-4: If problem contains math, verify each calculation step with SymPy.
        """
        # Detect problem type for verification
        problem_type = None
        if self._math_verifier and self.enable_math_verification:
            problem_type = self._math_verifier.detect_problem_type(session.problem)

        for i, step_data in enumerate(steps):
            step_type = step_data.get("step_type", "inference")
            try:
                step_type_enum = ReasoningStepTypeEnum(step_type)
            except ValueError:
                step_type_enum = ReasoningStepTypeEnum.INFERENCE

            # Initialize verification fields
            is_verified = False
            verification_details = None

            # REQ-4: Verify math steps with SymPy
            if (
                self._math_verifier
                and self.enable_math_verification
                and problem_type in [MathProblemType.ALGEBRA, MathProblemType.CALCULUS, MathProblemType.GEOMETRY]
                and step_type_enum in [ReasoningStepTypeEnum.CALCULATION, ReasoningStepTypeEnum.INFERENCE]
            ):
                try:
                    step_result = step_data.get("result", "")
                    step_reasoning = step_data.get("reasoning", "")

                    # Try to verify the step
                    verification = await self._math_verifier.verify(
                        problem=step_reasoning,
                        solution=str(step_result),
                        problem_type=problem_type,
                    )
                    is_verified = verification.is_correct
                    verification_details = {
                        "sympy_verified": is_verified,
                        "confidence": verification.confidence,
                        "message": verification.message,
                        "details": verification.details,
                    }
                    logger.debug(f"Step {i+1} verification: {is_verified} ({verification.message})")
                except Exception as e:
                    logger.warning(f"Math verification failed for step {i+1}: {e}")
                    verification_details = {"error": str(e)}

            step = ReasoningStep(
                session_id=session.id,
                step_number=step_data.get("step_number", i + 1),
                step_type=step_type_enum,
                description=step_data.get("description", ""),
                reasoning=step_data.get("reasoning", ""),
                result=step_data.get("result"),
                confidence=step_data.get("confidence", 1.0),
                is_verified=is_verified,
            )

            # Store verification details in metadata if available
            if verification_details:
                step_data["_verification"] = verification_details

            self.db.add(step)

        session.total_steps = len(steps)
        await self.db.commit()

        # REQ-5: Run logic validation on the stored steps
        if self._logic_validator and self.enable_logic_validation:
            await self._validate_logic(session, steps)

    async def _validate_logic(
        self, session: ReasoningSession, steps: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Validate logical consistency of reasoning steps (REQ-5)

        Args:
            session: The reasoning session
            steps: List of step data

        Returns:
            Logic validation result
        """
        if not self._logic_validator:
            return {"enabled": False}

        validation_result = {
            "enabled": True,
            "is_consistent": True,
            "has_circular_reasoning": False,
            "consistency": None,
            "circular_check": None,
            "warnings": [],
        }

        try:
            # Check consistency
            consistency = await self._logic_validator.check_consistency(steps)
            validation_result["consistency"] = {
                "is_consistent": consistency.is_consistent,
                "conflicts": consistency.conflicts,
                "warnings": consistency.warnings,
                "details": consistency.details,
            }
            validation_result["is_consistent"] = consistency.is_consistent

            if consistency.warnings:
                validation_result["warnings"].extend(consistency.warnings)

            # Check for circular reasoning
            circular = await self._logic_validator.detect_circular_reasoning(steps)
            validation_result["circular_check"] = {
                "has_circular_reasoning": circular.has_circular_reasoning,
                "cycles": circular.cycles,
                "explanation": circular.explanation,
            }
            validation_result["has_circular_reasoning"] = circular.has_circular_reasoning

            if circular.has_circular_reasoning:
                validation_result["warnings"].append(circular.explanation)

            # Track assumptions
            assumptions = await self._logic_validator.track_assumptions(steps)
            validation_result["assumptions"] = [
                {
                    "content": a.proposition.content,
                    "step_number": a.step_number,
                    "is_explicit": a.is_explicit,
                    "justification": a.justification,
                }
                for a in assumptions
            ]

            # Log validation results
            if not consistency.is_consistent or circular.has_circular_reasoning:
                logger.warning(
                    f"Logic validation issues for session {session.id}: "
                    f"consistent={consistency.is_consistent}, circular={circular.has_circular_reasoning}"
                )

        except Exception as e:
            logger.error(f"Logic validation failed for session {session.id}: {e}", exc_info=True)
            validation_result["error"] = str(e)

        # Store validation result in session metadata
        # Note: This would require adding a metadata field to ReasoningSession model
        # For now, we just return the result
        return validation_result

    async def _update_session_with_result(
        self, session: ReasoningSession, result: dict[str, Any]
    ) -> None:
        """Update session with final result"""
        session.status = ReasoningSessionStatus.COMPLETED
        session.completed_at = datetime.now(UTC)
        session.understanding = result.get("understanding")
        session.final_answer = result.get("final_answer") or result.get("answer")
        session.verification = result.get("verification")
        session.confidence = result.get("confidence", 0.0)
        session.latency_ms = result.get("latency_ms", 0.0)
        session.model_name = result.get("model")
        session.ensemble_scores = result.get("ensemble_scores")
        session.winning_provider = result.get("provider")

        await self.db.commit()

    async def _get_cached_reasoning(
        self, problem: str
    ) -> dict[str, Any] | None:
        """Get cached reasoning if available"""
        problem_hash = self._hash_problem(problem)

        result = await self.db.execute(
            select(ReasoningCache)
            .where(ReasoningCache.problem_hash == problem_hash)
            .where(ReasoningCache.expires_at > datetime.now(UTC))
        )
        cached = result.scalar_one_or_none()

        if cached:
            # Update hit count
            cached.hit_count += 1
            cached.last_hit = datetime.now(UTC)
            await self.db.commit()

            return {
                **cached.reasoning_data,
                "from_cache": True,
                "cache_hit_count": cached.hit_count,
            }

        return None

    async def _cache_reasoning(
        self, problem: str, result: dict[str, Any]
    ) -> None:
        """Cache reasoning result"""
        problem_hash = self._hash_problem(problem)

        # Check if exists
        existing = await self.db.execute(
            select(ReasoningCache).where(ReasoningCache.problem_hash == problem_hash)
        )
        cache_entry = existing.scalar_one_or_none()

        if cache_entry:
            # Update existing
            cache_entry.reasoning_data = result
            cache_entry.expires_at = datetime.now(UTC) + timedelta(days=self.CACHE_TTL_DAYS)
            cache_entry.confidence = result.get("confidence", 0.0)
            cache_entry.was_verified = bool(result.get("verification"))
        else:
            # Create new
            cache_entry = ReasoningCache(
                problem_hash=problem_hash,
                problem_text=problem,
                reasoning_data=result,
                provider=result.get("provider"),
                confidence=result.get("confidence", 0.0),
                was_verified=bool(result.get("verification")),
                expires_at=datetime.now(UTC) + timedelta(days=self.CACHE_TTL_DAYS),
            )
            self.db.add(cache_entry)

        await self.db.commit()

    def _hash_problem(self, problem: str) -> str:
        """Generate hash for problem (cache key)"""
        normalized = problem.strip().lower()
        return hashlib.sha256(normalized.encode()).hexdigest()

    async def get_session(
        self, session_id: uuid.UUID
    ) -> dict[str, Any] | None:
        """Get reasoning session by ID"""
        result = await self.db.execute(
            select(ReasoningSession)
            .options(selectinload(ReasoningSession.steps))
            .options(selectinload(ReasoningSession.sub_problems))
            .where(ReasoningSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if session:
            return session.to_dict()
        return None

    async def get_session_steps(
        self, session_id: uuid.UUID
    ) -> list[dict[str, Any]]:
        """Get all steps for a session"""
        result = await self.db.execute(
            select(ReasoningStep)
            .where(ReasoningStep.session_id == session_id)
            .order_by(ReasoningStep.step_number)
        )
        steps = result.scalars().all()

        return [step.to_dict() for step in steps]

    async def decompose_problem(
        self, problem: str, provider: str | None = None
    ) -> dict[str, Any]:
        """
        Decompose complex problem into sub-problems with topological ordering.

        REQ-1.3: Uses topological sort to order sub-problems by dependencies.

        Args:
            problem: Complex problem
            provider: Preferred provider

        Returns:
            Decomposition result with topologically sorted sub-problems
        """
        # Use Gemini for decomposition (best for this)
        decomposition_result = None

        if LLMProvider.GEMINI in self.ensemble_manager.providers:
            gemini = self.ensemble_manager.providers[LLMProvider.GEMINI]
            if hasattr(gemini, "decompose_problem"):
                decomposition_result = await gemini.decompose_problem(problem)

        # Fallback to ensemble
        if not decomposition_result:
            decomposition_result = await self.ensemble_manager.solve_with_best_provider(
                problem=f"Decompose into sub-problems: {problem}",
                capability=LLMCapability.SEQUENTIAL_THINKING,
            )

        # REQ-1.3: Apply topological sort to sub-problems
        sub_problems = decomposition_result.get("sub_problems", [])
        if sub_problems and len(sub_problems) > 1:
            decomposition_result["sub_problems"] = self._topological_sort_subproblems(sub_problems)
            decomposition_result["topologically_sorted"] = True
            logger.info(f"Sub-problems sorted topologically: {len(sub_problems)} items")

        return decomposition_result

    def _topological_sort_subproblems(
        self, sub_problems: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Sort sub-problems by dependencies using topological sort.

        REQ-1.3: Implements dependency resolution for sub-problems.

        Args:
            sub_problems: List of sub-problem dicts with 'id' and 'dependencies'

        Returns:
            Topologically sorted list of sub-problems
        """
        if not sub_problems:
            return sub_problems

        # Build dependency graph
        graph = DependencyGraph()

        # Create ID mapping (some sub-problems may have string IDs)
        id_to_subproblem = {}
        for sp in sub_problems:
            sp_id = str(sp.get("id", sp.get("order_index", id(sp))))
            id_to_subproblem[sp_id] = sp
            graph.add_node(sp_id, sp)

        # Add dependencies
        for sp in sub_problems:
            sp_id = str(sp.get("id", sp.get("order_index", id(sp))))
            dependencies = sp.get("dependencies", [])

            for dep_id in dependencies:
                dep_id_str = str(dep_id)
                if dep_id_str in id_to_subproblem:
                    try:
                        graph.add_dependency(sp_id, dep_id_str)
                    except ValueError as e:
                        # Circular dependency detected
                        logger.warning(f"Circular dependency detected: {e}")

        # Get topological order
        try:
            sorted_ids = graph.topological_sort()
        except Exception as e:
            logger.error(f"Topological sort failed: {e}", exc_info=True)
            # Return original order if sort fails
            return sub_problems

        # Build sorted list
        sorted_subproblems = []
        for i, sp_id in enumerate(sorted_ids):
            sp = id_to_subproblem.get(sp_id)
            if sp:
                sp["order_index"] = i + 1  # Update order index
                sorted_subproblems.append(sp)

        return sorted_subproblems

    async def compare_providers(
        self, problem: str
    ) -> dict[str, Any]:
        """
        Compare all providers on the same problem

        Args:
            problem: Problem to solve

        Returns:
            Comparison results from all providers
        """
        return await self.ensemble_manager.compare_providers(problem)

    async def invalidate_cache(
        self, problem: str | None = None
    ) -> int:
        """
        Invalidate cache entries

        Args:
            problem: Specific problem to invalidate, or None for all expired

        Returns:
            Number of entries invalidated
        """
        if problem:
            problem_hash = self._hash_problem(problem)
            result = await self.db.execute(
                delete(ReasoningCache).where(
                    ReasoningCache.problem_hash == problem_hash
                )
            )
        else:
            # Delete expired entries
            result = await self.db.execute(
                delete(ReasoningCache).where(
                    ReasoningCache.expires_at < datetime.now(UTC)
                )
            )

        await self.db.commit()
        return result.rowcount

    async def get_user_sessions(
        self, user_id: uuid.UUID, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Get recent sessions for a user"""
        result = await self.db.execute(
            select(ReasoningSession)
            .where(ReasoningSession.user_id == user_id)
            .order_by(ReasoningSession.created_at.desc())
            .limit(limit)
        )
        sessions = result.scalars().all()

        return [s.to_dict() for s in sessions]
