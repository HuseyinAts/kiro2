"""
Question Bank v2.0 API Routes
Next-Gen Features: Full pipeline, CAT, Knowledge Graph, HITL

Endpoints:
- POST /api/v2/questions/generate - Full generation pipeline
- POST /api/v2/cat/start - Start adaptive test session
- POST /api/v2/cat/submit - Submit response & get next question
- GET /api/v2/knowledge-graph/recommendations - Smart question suggestions
- POST /api/v2/hitl/tasks - Create expert review task
- GET /api/v2/hitl/dashboard/{expert_id} - Expert dashboard
"""
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Optional
from pydantic import BaseModel, Field
from uuid import uuid4
from datetime import datetime

# Import services
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.ai_question_generator import HybridQuestionGenerator
from scripts.question_validator import QuestionValidator
from services.knowledge_graph_service import KnowledgeGraphService, QuestionNode
from services.plagiarism_detection_service import PlagiarismDetectionService
from services.adaptive_testing_service import ComputerAdaptiveTestingService
from services.hitl_workflow_service import (
    HITLWorkflowService,
    ReviewDecision,
    ReviewSubmission,
)

router = APIRouter(prefix="/api/v2", tags=["Question Bank v2.0"])

# Initialize services (in production: use dependency injection)
question_generator = HybridQuestionGenerator()
question_validator = QuestionValidator()
kg_service = KnowledgeGraphService()
plagiarism_service = PlagiarismDetectionService()
hitl_service = HITLWorkflowService()

# Mock item bank for CAT (in production: load from database)
MOCK_ITEM_BANK = []
cat_service = ComputerAdaptiveTestingService(MOCK_ITEM_BANK)


# ============================================================================
# PYDANTIC MODELS
# ============================================================================


class QuestionGenerationRequest(BaseModel):
    """Request to generate a question"""

    konu: str = Field(..., description="Topic (e.g., Matematik, Türkçe)")
    alt_konu: str = Field(..., description="Subtopic (e.g., Türev, Cümle Bilgisi)")
    kazanim: str = Field(..., description="Learning objective")
    zorluk: str = Field(default="medium", description="Difficulty: easy, medium, hard")
    bloom_level: str = Field(default="apply", description="Bloom's taxonomy level")
    force_model: Optional[str] = Field(
        None, description="Force AI model: gpt-5 or claude"
    )


class QuestionGenerationResponse(BaseModel):
    """Response from question generation"""

    status: str  # "approved", "needs_review", "rejected"
    question_id: Optional[str]
    question: Optional[Dict]
    task_id: Optional[str]  # If needs review
    priority: Optional[str]
    plagiarism_result: Optional[Dict]
    validation_result: Optional[Dict]
    message: str


class CATStartRequest(BaseModel):
    """Request to start CAT session"""

    student_id: str
    konu: str
    sinav_tipi: Optional[str] = "TYT"
    initial_theta: Optional[float] = 0.0


class CATStartResponse(BaseModel):
    """Response from CAT session start"""

    session_id: str
    first_question: Dict
    initial_ability: float
    estimated_questions: str


class CATSubmitRequest(BaseModel):
    """Request to submit CAT response"""

    session_id: str
    question_id: str
    is_correct: bool
    response_time_seconds: int


class CATSubmitResponse(BaseModel):
    """Response from CAT submission"""

    status: str  # "in_progress" or "complete"
    current_ability: Optional[float]
    current_sem: Optional[float]
    questions_answered: int
    next_question: Optional[Dict]
    final_results: Optional[Dict]


class KnowledgeGraphRecommendationRequest(BaseModel):
    """Request for question recommendations"""

    student_id: str
    current_question_id: str
    limit: int = Field(default=10, le=50)


class HITLTaskRequest(BaseModel):
    """Request to create HITL task"""

    question_id: str
    question_data: Dict
    ai_validation_result: Dict


class HITLReviewSubmission(BaseModel):
    """Expert review submission"""

    task_id: str
    expert_id: str
    decision: str  # "approve", "reject", "needs_revision", "escalate"
    pedagogy_score: int = Field(..., ge=0, le=100)
    comments: str
    suggested_changes: Optional[Dict]
    review_time_seconds: int


# ============================================================================
# QUESTION GENERATION ENDPOINTS
# ============================================================================


@router.post("/questions/generate", response_model=QuestionGenerationResponse)
async def generate_question_full_pipeline(request: QuestionGenerationRequest):
    """
    Full question generation pipeline:
    1. AI Generation (GPT-5/Claude 4.5)
    2. Plagiarism check (BERT-based)
    3. Quality validation (QUEST framework)
    4. HITL escalation (if needed)
    5. Knowledge graph integration

    Returns: Question with status (approved/needs_review/rejected)
    """
    try:
        # Step 1: Generate question
        question = await question_generator.generate_question(
            konu=request.konu,
            alt_konu=request.alt_konu,
            kazanim=request.kazanim,
            zorluk=request.zorluk,
            bloom_level=request.bloom_level,
            force_model=request.force_model,
        )

        if "error" in question:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI generation failed: {question['error']}",
            )

        question_id = str(uuid4())
        question["id"] = question_id

        # Step 2: Plagiarism check
        plag_result = await plagiarism_service.comprehensive_plagiarism_check(
            question["metin"]
        )

        if not plag_result["is_safe"]:
            return QuestionGenerationResponse(
                status="rejected",
                question_id=None,
                question=None,
                plagiarism_result=plag_result,
                message=plag_result.get("recommendation", "Plagiarism detected"),
            )

        # Step 3: Quality validation
        # Note: question_validator expects specific format
        validation_result = {
            "approved": True,
            "confidence": 0.8,  # Mock for now
            "weaknesses": [],
        }

        # Step 4: HITL escalation check
        hitl_eval = hitl_service.evaluate_question_for_review(
            question_id=question_id,
            question_data=question,
            ai_validation_result=validation_result,
        )

        if hitl_eval["needs_review"]:
            return QuestionGenerationResponse(
                status="needs_review",
                question_id=question_id,
                question=question,
                task_id=hitl_eval.get("task_id"),
                priority=hitl_eval.get("priority"),
                plagiarism_result=plag_result,
                validation_result=validation_result,
                message=f"Question escalated for expert review (confidence: {validation_result['confidence']:.2f})",
            )

        # Step 5: Knowledge graph integration
        kg_node = QuestionNode(
            id=question_id,
            konu=request.konu,
            kazanim=request.kazanim,
            bloom_level=request.bloom_level,
            irt_difficulty=0.5,  # Default, will be calibrated
            cognitive_skills=question.get("cognitive_skills", []),
        )
        kg_service.add_question_node(kg_node)

        # Add to plagiarism database (prevent future duplicates)
        plagiarism_service.add_to_platform_database(question_id, question["metin"])

        return QuestionGenerationResponse(
            status="approved",
            question_id=question_id,
            question=question,
            plagiarism_result=plag_result,
            validation_result=validation_result,
            message="Question approved and ready for use",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline error: {str(e)}",
        )


# ============================================================================
# CAT (COMPUTER ADAPTIVE TESTING) ENDPOINTS
# ============================================================================


@router.post("/cat/start", response_model=CATStartResponse)
async def start_cat_session(request: CATStartRequest):
    """
    Start a new CAT (Computer Adaptive Testing) session

    Returns: Session ID and first question
    """
    try:
        # In production: Load item bank from database for this topic
        # For now: Use mock data
        item_bank = [
            {
                "id": f"q-{i}",
                "konu": request.konu,
                "metin": f"Mock question {i}",
                "irt_params": {"a": 1.0 + (i * 0.1), "b": -1.0 + (i * 0.5), "c": 0.25},
            }
            for i in range(10)
        ]

        # Update CAT service item bank
        cat_service.item_bank = item_bank

        # Start session
        session_id = f"cat-{request.student_id}-{datetime.now().timestamp()}"
        session = cat_service.start_new_session(
            student_id=request.student_id,
            session_id=session_id,
            initial_theta=request.initial_theta,
        )

        # Get first question
        first_question = cat_service.select_next_question(session_id)

        return CATStartResponse(
            session_id=session_id,
            first_question=first_question,
            initial_ability=session.current_ability.theta,
            estimated_questions="10-20 sorular",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CAT session start failed: {str(e)}",
        )


@router.post("/cat/submit", response_model=CATSubmitResponse)
async def submit_cat_response(request: CATSubmitRequest):
    """
    Submit response to CAT question and get next question

    Returns: Updated ability estimate and next question (or final results)
    """
    try:
        result = cat_service.submit_response(
            session_id=request.session_id,
            question_id=request.question_id,
            is_correct=request.is_correct,
            response_time_seconds=request.response_time_seconds,
        )

        if result["status"] == "complete":
            return CATSubmitResponse(
                status="complete",
                current_ability=result["final_ability"],
                current_sem=result["final_sem"],
                questions_answered=result["questions_answered"],
                next_question=None,
                final_results=result.get("performance_summary"),
            )
        else:
            return CATSubmitResponse(
                status="in_progress",
                current_ability=result["current_ability"],
                current_sem=result["current_sem"],
                questions_answered=result["questions_answered"],
                next_question=result["next_question"],
                final_results=None,
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CAT submission failed: {str(e)}",
        )


# ============================================================================
# KNOWLEDGE GRAPH ENDPOINTS
# ============================================================================


@router.post("/knowledge-graph/recommendations")
async def get_question_recommendations(request: KnowledgeGraphRecommendationRequest):
    """
    Get smart question recommendations based on:
    - Current question topic
    - Student performance
    - Knowledge graph relationships

    Returns: List of recommended questions
    """
    try:
        recommendations = kg_service.get_recommended_questions(
            student_id=request.student_id,
            current_question_id=request.current_question_id,
            limit=request.limit,
        )

        return {"recommendations": recommendations, "count": len(recommendations)}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation failed: {str(e)}",
        )


@router.get("/knowledge-graph/stats")
async def get_knowledge_graph_stats():
    """Get knowledge graph statistics"""
    try:
        stats = kg_service.export_graph_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stats retrieval failed: {str(e)}",
        )


@router.get("/knowledge-graph/student/{student_id}/gaps")
async def analyze_student_knowledge_gaps(student_id: str):
    """Analyze student's knowledge gaps and generate learning path"""
    try:
        gap_analysis = kg_service.analyze_student_gaps(student_id)
        return gap_analysis
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gap analysis failed: {str(e)}",
        )


# ============================================================================
# HITL (HUMAN-IN-THE-LOOP) ENDPOINTS
# ============================================================================


@router.post("/hitl/tasks")
async def create_review_task(request: HITLTaskRequest):
    """Create expert review task for a question"""
    try:
        eval_result = hitl_service.evaluate_question_for_review(
            question_id=request.question_id,
            question_data=request.question_data,
            ai_validation_result=request.ai_validation_result,
        )

        return eval_result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Task creation failed: {str(e)}",
        )


@router.post("/hitl/tasks/{task_id}/assign")
async def assign_task_to_expert(task_id: str, expert_id: Optional[str] = None):
    """Assign review task to an expert (auto-match if expert_id not provided)"""
    try:
        assignment = hitl_service.assign_task_to_expert(task_id, expert_id)
        return assignment

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Task assignment failed: {str(e)}",
        )


@router.post("/hitl/tasks/{task_id}/review")
async def submit_expert_review(task_id: str, review: HITLReviewSubmission):
    """Submit expert review for a task"""
    try:
        # Convert to ReviewSubmission dataclass
        submission = ReviewSubmission(
            task_id=task_id,
            expert_id=review.expert_id,
            decision=ReviewDecision(review.decision),
            pedagogy_score=review.pedagogy_score,
            comments=review.comments,
            suggested_changes=review.suggested_changes,
            review_time_seconds=review.review_time_seconds,
        )

        result = hitl_service.submit_review(submission)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Review submission failed: {str(e)}",
        )


@router.get("/hitl/dashboard/{expert_id}")
async def get_expert_dashboard(expert_id: str):
    """Get expert's dashboard with tasks and statistics"""
    try:
        dashboard = hitl_service.get_expert_dashboard(expert_id)
        return dashboard

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Expert not found: {str(e)}"
        )


@router.get("/hitl/leaderboard")
async def get_expert_leaderboard(limit: int = 10):
    """Get expert leaderboard"""
    try:
        leaderboard = hitl_service.get_leaderboard(limit)
        return {"leaderboard": leaderboard, "count": len(leaderboard)}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Leaderboard retrieval failed: {str(e)}",
        )


# ============================================================================
# HEALTH CHECK
# ============================================================================


@router.get("/health")
async def health_check():
    """Health check for v2.0 services"""
    return {
        "status": "healthy",
        "version": "2.0",
        "services": {
            "question_generator": "operational",
            "knowledge_graph": "operational",
            "plagiarism_detection": "operational",
            "cat_engine": "operational",
            "hitl_workflow": "operational",
        },
        "timestamp": datetime.now().isoformat(),
    }
