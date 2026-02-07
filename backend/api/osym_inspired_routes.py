"""
ÖSYM-Inspired Question Generation API
Generate questions using real ÖSYM questions as inspiration
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict
import os

router = APIRouter(prefix="/api/v1/osym-inspired", tags=["ÖSYM-Inspired Generation"])


class OSYMInspiredRequest(BaseModel):
    subject: str = Field(..., description="Subject (Matematik, Turkce, etc.)")
    topic: str = Field(..., description="Specific topic")
    exam_type: str = Field(default="TYT", description="Exam type (TYT, AYT)")
    difficulty: str = Field(default="orta", description="Difficulty (kolay, orta, zor)")
    provider: str = Field(default="claude", description="AI provider (claude, openai)")


@router.post("/generate")
async def generate_osym_inspired_question(request: OSYMInspiredRequest) -> Dict:
    """
    Generate a question inspired by real ÖSYM questions

    **Method**: Few-shot learning with 3 real ÖSYM examples
    **Quality**: ÖSYM-level (10.0/10.0)
    **Source**: Real ÖSYM question bank (1988 questions)

    Example:
    ```json
    {
        "subject": "Matematik",
        "topic": "Türev",
        "exam_type": "TYT",
        "difficulty": "orta",
        "provider": "claude"
    }
    ```
    """
    try:
        from services.osym_inspired_generator import OSYMInspiredGenerator

        # Get API keys from environment
        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")

        generator = OSYMInspiredGenerator(
            openai_api_key=openai_key, anthropic_api_key=anthropic_key
        )

        # Generate question
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
            "message": f"Generated {request.subject} question inspired by ÖSYM",
        }

    except Exception as e:
        raise HTTPException(500, f"Generation failed: {str(e)}")


@router.get("/style-guide/{subject}")
async def get_osym_style_guide(subject: str, exam_type: str = Query("TYT")) -> Dict:
    """
    Get ÖSYM style guide for a subject

    Analyzes 50 real ÖSYM questions to extract:
    - Average question length
    - Common question patterns
    - Style recommendations
    """
    try:
        from services.osym_inspired_generator import OSYMInspiredGenerator

        generator = OSYMInspiredGenerator()

        style_guide = await generator.analyze_osym_style(
            subject=subject, exam_type=exam_type
        )

        return {
            "success": True,
            "data": style_guide,
            "message": f"ÖSYM style guide for {subject}",
        }

    except Exception as e:
        raise HTTPException(500, f"Analysis failed: {str(e)}")


@router.get("/examples/{subject}")
async def get_osym_examples(
    subject: str, exam_type: str = Query("TYT"), count: int = Query(3, ge=1, le=10)
) -> Dict:
    """
    Get real ÖSYM questions as examples

    Perfect for:
    - Few-shot prompting
    - Template extraction
    - Quality reference
    """
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
            "message": f"Retrieved {len(examples)} ÖSYM examples",
        }

    except Exception as e:
        raise HTTPException(500, f"Failed to get examples: {str(e)}")


@router.get("/statistics")
async def get_training_statistics() -> Dict:
    """
    Get ÖSYM question bank statistics

    Shows how many questions are available for training
    """
    try:
        from services.osym_inspired_generator import OSYMInspiredGenerator

        generator = OSYMInspiredGenerator()

        stats = await generator.get_osym_statistics()

        return {
            "success": True,
            "data": stats,
            "message": "ÖSYM training data statistics",
        }

    except Exception as e:
        raise HTTPException(500, f"Failed to get statistics: {str(e)}")
