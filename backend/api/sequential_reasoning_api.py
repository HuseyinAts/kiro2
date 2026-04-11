"""
Sequential Reasoning API
REST API endpoints for step-by-step problem solving

Author: KIRO AI Team
Date: 2026-01-16

Updated: 2026-01-17
- Added Mermaid visualization endpoint (REQ-6.2)
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth_dependencies import AuthorizationDependency, authenticate_optional
from core.database import get_async_session

get_current_admin_user = AuthorizationDependency(
    required_roles=["admin", "super_admin"]
)
from services.reasoning.visualization_service import get_visualization_service
from services.sequential_reasoning_service import SequentialReasoningService

router = APIRouter(prefix="/api/v1/reasoning", tags=["Sequential Reasoning"])


# ============================================================================
# Request/Response Models
# ============================================================================


class SolveRequest(BaseModel):
    """Request to solve a problem"""

    problem: str = Field(..., min_length=5, description="Problem to solve")
    provider: str | None = Field(
        None,
        description="LLM provider: gemini, openai, claude, qwen",
    )
    use_ensemble: bool = Field(
        False,
        description="Use ensemble of all providers",
    )
    max_steps: int = Field(
        10,
        ge=1,
        le=20,
        description="Maximum reasoning steps",
    )
    use_cache: bool = Field(
        True,
        description="Check and use reasoning cache",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "problem": "x^2 + 5x + 6 = 0 denklemini coz",
                "provider": "gemini",
                "use_ensemble": False,
                "max_steps": 10,
                "use_cache": True,
            }
        }
    )


class ReasoningStepResponse(BaseModel):
    """Single reasoning step"""

    step_number: int
    step_type: str
    description: str
    reasoning: str | None
    result: str | None
    confidence: float


class SolveResponse(BaseModel):
    """Response from solve endpoint"""

    session_id: str | None
    problem: str
    understanding: str | None
    steps: list[dict]
    final_answer: str
    verification: str | None
    confidence: float
    provider: str | None
    model: str | None
    latency_ms: float
    from_cache: bool = False
    ensemble_scores: dict | None


class DecomposeRequest(BaseModel):
    """Request to decompose a problem"""

    problem: str = Field(..., min_length=5, description="Complex problem to decompose")
    provider: str | None = Field(None)


class DecomposeResponse(BaseModel):
    """Response from decompose endpoint"""

    main_problem: str
    sub_problems: list[dict]
    solving_order: list[int]
    total_steps: int


class CompareRequest(BaseModel):
    """Request to compare providers"""

    problem: str = Field(..., min_length=5)


class CompareResponse(BaseModel):
    """Response from compare endpoint"""

    problem: str
    providers: dict
    best_provider: str | None
    fastest_provider: str | None


class CacheInvalidateRequest(BaseModel):
    """Request to invalidate cache"""

    problem: str | None = Field(None, description="Specific problem to invalidate")


class MermaidResponse(BaseModel):
    """Response with Mermaid diagram (REQ-6.2)"""

    mermaid: str = Field(..., description="Mermaid diagram code")
    node_count: int = Field(..., description="Number of nodes")
    edge_count: int = Field(..., description="Number of edges")
    critical_path: list[str] = Field(
        default_factory=list, description="Critical path node IDs"
    )
    has_branches: bool = Field(False, description="Whether tree has branches")
    tree_data: dict | None = Field(
        None, description="JSON tree data for interactive UI"
    )


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/solve", response_model=SolveResponse)
async def solve_problem(
    request: SolveRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(authenticate_optional),
):
    """
    Solve a problem with step-by-step reasoning

    Uses sequential thinking to solve the problem, showing each step
    of the reasoning process.

    **Providers:**
    - `gemini` - Google Gemini (best for thinking mode)
    - `openai` - OpenAI GPT-4
    - `claude` - Anthropic Claude
    - `qwen` - Alibaba Qwen

    **Ensemble Mode:**
    When `use_ensemble=true`, all available providers solve the problem
    and the best result is selected via voting.
    """
    service = SequentialReasoningService(db)

    user_id = current_user.id if current_user else None

    try:
        result = await service.solve(
            problem=request.problem,
            provider=request.provider,
            use_ensemble=request.use_ensemble,
            max_steps=request.max_steps,
            use_cache=request.use_cache,
            user_id=user_id,
        )

        return SolveResponse(
            session_id=result.get("session_id"),
            problem=request.problem,
            understanding=result.get("understanding"),
            steps=result.get("steps", []),
            final_answer=result.get("final_answer") or result.get("answer", ""),
            verification=result.get("verification"),
            confidence=result.get("confidence", 0.0),
            provider=result.get("provider"),
            model=result.get("model"),
            latency_ms=result.get("latency_ms", 0.0),
            from_cache=result.get("from_cache", False),
            ensemble_scores=result.get("ensemble_scores"),
        )

    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/session/{session_id}")
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(authenticate_optional),
):
    """
    Get a reasoning session by ID

    Returns the complete session including all steps.
    """
    service = SequentialReasoningService(db)

    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Ownership check: only session owner can view
    session_user_id = (
        session.get("user_id")
        if isinstance(session, dict)
        else getattr(session, "user_id", None)
    )
    if (
        current_user
        and session_user_id
        and str(session_user_id) != str(current_user.id)
    ):
        raise HTTPException(status_code=403, detail="Bu oturuma erisim yetkiniz yok")

    return session


@router.get("/session/{session_id}/steps")
async def get_session_steps(
    session_id: UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(authenticate_optional),
):
    """
    Get all reasoning steps for a session

    Returns steps in order with their details.
    """
    service = SequentialReasoningService(db)

    # Verify session exists and check ownership
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session_user_id = (
        session.get("user_id")
        if isinstance(session, dict)
        else getattr(session, "user_id", None)
    )
    if (
        current_user
        and session_user_id
        and str(session_user_id) != str(current_user.id)
    ):
        raise HTTPException(status_code=403, detail="Bu oturuma erisim yetkiniz yok")

    steps = await service.get_session_steps(session_id)
    return {"session_id": str(session_id), "steps": steps}


@router.get("/session/{session_id}/mermaid", response_model=MermaidResponse)
async def get_session_mermaid(
    session_id: UUID,
    orientation: str = Query(
        "TD", regex="^(TD|LR)$", description="TD=top-down, LR=left-right"
    ),
    show_confidence: bool = Query(True, description="Show confidence values"),
    include_tree_data: bool = Query(
        True, description="Include JSON tree for interactive UI"
    ),
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(authenticate_optional),
):
    """
    Get Mermaid diagram for a reasoning session (REQ-6.2)

    Generates a Mermaid flowchart visualization of the reasoning steps.
    Useful for displaying thought trees in the frontend.

    **Orientation:**
    - `TD` - Top-Down (vertical)
    - `LR` - Left-Right (horizontal)

    **Example Response:**
    ```
    {
      "mermaid": "graph TD\\n    S1[\\"📖 Problem anla\\"] --> S2[\\"💭 Cozum adimi\\"]",
      "node_count": 2,
      "critical_path": ["S1", "S2"]
    }
    ```
    """
    service = SequentialReasoningService(db)
    viz_service = get_visualization_service()

    # Get session steps
    steps = await service.get_session_steps(session_id)
    if not steps:
        raise HTTPException(status_code=404, detail="Session not found or has no steps")

    # Generate Mermaid diagram
    diagram = viz_service.generate_thought_tree(
        steps=steps,
        show_confidence=show_confidence,
        highlight_critical_path=True,
        orientation=orientation,
    )

    # Optionally include JSON tree
    tree_data = None
    if include_tree_data:
        tree_data = viz_service.steps_to_json_tree(steps)

    return MermaidResponse(
        mermaid=diagram.code,
        node_count=diagram.node_count,
        edge_count=diagram.edge_count,
        critical_path=diagram.critical_path,
        has_branches=diagram.has_branches,
        tree_data=tree_data,
    )


@router.post("/decompose", response_model=DecomposeResponse)
async def decompose_problem(
    request: DecomposeRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(authenticate_optional),
):
    """
    Decompose a complex problem into sub-problems

    Breaks down the problem into smaller, manageable sub-problems
    with dependencies and solving order (topological sort).
    """
    service = SequentialReasoningService(db)

    try:
        result = await service.decompose_problem(
            problem=request.problem,
            provider=request.provider,
        )

        return DecomposeResponse(
            main_problem=result.get("main_problem", request.problem),
            sub_problems=result.get("sub_problems", []),
            solving_order=result.get("solving_order", []),
            total_steps=result.get("total_steps", 0),
        )

    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/compare", response_model=CompareResponse)
async def compare_providers(
    request: CompareRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(authenticate_optional),
):
    """
    Compare all providers on the same problem

    Runs the problem through all available providers and
    returns comparison results including latency and quality.
    """
    service = SequentialReasoningService(db)

    try:
        result = await service.compare_providers(request.problem)

        return CompareResponse(
            problem=result.get("problem", request.problem),
            providers=result.get("providers", {}),
            best_provider=result.get("best_provider"),
            fastest_provider=result.get("fastest_provider"),
        )

    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/cache/invalidate")
async def invalidate_cache(
    request: CacheInvalidateRequest,
    db: AsyncSession = Depends(get_async_session),
    _admin=Depends(get_current_admin_user),
):
    """
    Invalidate reasoning cache (admin only)

    If `problem` is provided, invalidates cache for that specific problem.
    Otherwise, removes all expired cache entries.
    """
    service = SequentialReasoningService(db)

    count = await service.invalidate_cache(request.problem)

    return {"invalidated_count": count}


@router.get("/my-sessions")
async def get_my_sessions(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(authenticate_optional),
):
    """
    Get current user's recent reasoning sessions

    Requires authentication.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    service = SequentialReasoningService(db)

    sessions = await service.get_user_sessions(current_user.id, limit=limit)

    return {"sessions": sessions}


@router.get("/providers")
async def list_providers():
    """
    List available LLM providers

    Returns all supported providers and their capabilities.
    """
    return {
        "providers": [
            {
                "name": "gemini",
                "display_name": "Google Gemini",
                "model": "gemini-2.0-flash-thinking-exp",
                "capabilities": [
                    "sequential_thinking",
                    "math_reasoning",
                    "step_by_step",
                ],
                "recommended_for": "Complex reasoning and math problems",
            },
            {
                "name": "openai",
                "display_name": "OpenAI GPT-4",
                "model": "gpt-4o",
                "capabilities": [
                    "question_generation",
                    "content_analysis",
                    "fine_tuning",
                ],
                "recommended_for": "General purpose and question generation",
            },
            {
                "name": "claude",
                "display_name": "Anthropic Claude",
                "model": "claude-sonnet-4-5",
                "capabilities": [
                    "question_generation",
                    "quality_scoring",
                    "content_analysis",
                ],
                "recommended_for": "Fast responses and quality scoring",
            },
            {
                "name": "qwen",
                "display_name": "Alibaba Qwen",
                "model": "Qwen2.5-72B-Instruct",
                "capabilities": [
                    "sequential_thinking",
                    "step_by_step",
                    "fine_tuning",
                ],
                "recommended_for": "Local deployment and cost-effective",
            },
        ],
        "default_provider": "gemini",
        "ensemble_enabled": True,
    }


# Health check
@router.get("/health")
async def health_check():
    """Check reasoning service health"""
    return {
        "status": "healthy",
        "service": "sequential_reasoning",
        "version": "1.0.0",
    }
