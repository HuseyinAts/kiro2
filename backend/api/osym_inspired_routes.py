"""
OSYM-Inspired Question Generation API
Generate questions using real OSYM questions as inspiration
"""

import os

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from core.dependencies import AuthenticatedUser, get_current_user

router = APIRouter(prefix="/api/v1/osym-inspired", tags=["OSYM-Inspired Generation"])


class OSYMInspiredRequest(BaseModel):
    subject: str = Field(..., description="Subject (Matematik, Turkce, etc.)")
    topic: str = Field(..., description="Specific topic")
    exam_type: str = Field(default="TYT", description="Exam type (TYT, AYT)")
    difficulty: str = Field(default="orta", description="Difficulty (kolay, orta, zor)")
    provider: str = Field(default="claude", description="AI provider (claude, openai)")


@router.post("/generate")
async def generate_osym_inspired_question(
    request: OSYMInspiredRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    """Generate a question inspired by real OSYM questions using few-shot learning."""
    try:
        from services.osym_inspired_generator import OSYMInspiredGenerator

        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")

        generator = OSYMInspiredGenerator(
            openai_api_key=openai_key, anthropic_api_key=anthropic_key
        )

        result = await generator.generate_with_few_shot(
            subject=request.subject,
            topic=request.topic,
            exam_type=request.exam_type,
            difficulty=request.difficulty,
            provider=request.provider,
        )

        return {
            "success": True,
            "data": result,
            "message": f"Generated {request.subject} question inspired by OSYM",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Generation failed: {e!s}")


@router.get("/style-guide/{subject}")
async def get_osym_style_guide(subject: str, exam_type: str = Query("TYT")) -> dict:
    """Get OSYM style guide for a subject."""
    try:
        from services.osym_inspired_generator import OSYMInspiredGenerator

        generator = OSYMInspiredGenerator()

        style_guide = await generator.analyze_osym_style(
            subject=subject, exam_type=exam_type
        )

        return {
            "success": True,
            "data": style_guide,
            "message": f"OSYM style guide for {subject}",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Analysis failed: {e!s}")


@router.get("/examples/{subject}")
async def get_osym_examples(
    subject: str, exam_type: str = Query("TYT"), count: int = Query(3, ge=1, le=10)
) -> dict:
    """Get real OSYM questions as examples for few-shot prompting."""
    try:
        from services.osym_inspired_generator import OSYMInspiredGenerator

        generator = OSYMInspiredGenerator()

        examples = await generator.get_similar_osym_questions(
            subject=subject, exam_type=exam_type, count=count
        )

        return {
            "success": True,
            "data": examples,
            "count": len(examples),
            "message": f"Retrieved {len(examples)} OSYM examples",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to get examples: {e!s}")


@router.get("/statistics")
async def get_training_statistics() -> dict:
    """Get OSYM question bank statistics."""
    try:
        from services.osym_inspired_generator import OSYMInspiredGenerator

        generator = OSYMInspiredGenerator()

        stats = await generator.get_osym_statistics()

        return {
            "success": True,
            "data": stats,
            "message": "OSYM training data statistics",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to get statistics: {e!s}")
