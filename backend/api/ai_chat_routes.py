"""
Task 106: AI Chat Assistant API Routes

REST API for enhanced chat with image upload and OCR
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.ai_chat_service import AIChatService
from services.ocr_service import OCRService
from models.ai_chat import MessageRole, SessionStatus, SubjectType


router = APIRouter(prefix="/api/chat", tags=["AI Chat"])


# ============================================================
# Request/Response Models
# ============================================================


class SessionCreateRequest(BaseModel):
    """Request model for creating session"""

    title: Optional[str] = None
    subject_type: SubjectType = SubjectType.GENERAL


class MessageRequest(BaseModel):
    """Request model for sending message"""

    content: str
    image_id: Optional[UUID] = None


class MessageRatingRequest(BaseModel):
    """Request model for rating message"""

    rating: int
    is_helpful: bool
    feedback_comment: Optional[str] = None


# ============================================================
# Session Endpoints
# ============================================================


@router.post("/sessions")
async def create_session(
    request: SessionCreateRequest, user_id: UUID, db: AsyncSession = Depends(get_db)
):
    """Create a new chat session"""
    service = AIChatService(db)
    session = await service.create_session(
        user_id=user_id, title=request.title, subject_type=request.subject_type
    )
    return {"session_id": session.id, "title": session.title}


@router.get("/sessions")
async def get_user_sessions(
    user_id: UUID,
    status: Optional[SessionStatus] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get user's chat sessions"""
    service = AIChatService(db)
    sessions = await service.get_user_sessions(user_id, status)
    return [
        {
            "id": s.id,
            "title": s.title,
            "subject_type": s.subject_type.value,
            "message_count": s.message_count,
            "updated_at": s.updated_at,
        }
        for s in sessions
    ]


@router.get("/sessions/{session_id}")
async def get_session(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get session details"""
    service = AIChatService(db)
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "id": session.id,
        "title": session.title,
        "subject_type": session.subject_type.value,
        "message_count": session.message_count,
        "total_tokens": session.total_tokens,
    }


# ============================================================
# Message Endpoints
# ============================================================


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: UUID, request: MessageRequest, db: AsyncSession = Depends(get_db)
):
    """Send a message and get AI response"""
    service = AIChatService(db)

    # Add user message
    user_msg = await service.add_message(
        session_id=session_id,
        role=MessageRole.USER,
        content=request.content,
        image_id=request.image_id,
    )

    # Get image text if image_id provided
    image_text = None
    if request.image_id:
        image = await service.get_image_upload(request.image_id)
        if image:
            image_text = image.ocr_text

    # Generate AI response
    ai_response = await service.generate_ai_response(
        session_id, request.content, image_text
    )

    # Add assistant message
    assistant_msg = await service.add_message(
        session_id=session_id,
        role=MessageRole.ASSISTANT,
        content=ai_response["content"],
        model=ai_response["model"],
        tokens_used=ai_response["tokens_used"],
        cost=ai_response["cost"],
        response_time_ms=ai_response["response_time_ms"],
        confidence_score=ai_response["confidence_score"],
    )

    return {
        "message_id": assistant_msg.id,
        "content": ai_response["content"],
        "tokens_used": ai_response["tokens_used"],
    }


@router.get("/sessions/{session_id}/messages")
async def get_messages(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get messages for a session"""
    service = AIChatService(db)
    messages = await service.get_messages(session_id)
    return [
        {
            "id": m.id,
            "role": m.role.value,
            "content": m.content,
            "created_at": m.created_at,
            "user_rating": m.user_rating,
        }
        for m in messages
    ]


# ============================================================
# Image Upload Endpoints
# ============================================================


@router.post("/sessions/{session_id}/upload")
async def upload_image(
    session_id: UUID,
    user_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload image for OCR processing"""
    import os
    from pathlib import Path

    # Save file
    upload_dir = Path("uploads/chat_images")
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / f"{session_id}_{file.filename}"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Create image record
    chat_service = AIChatService(db)
    image = await chat_service.create_image_upload(
        session_id=session_id,
        user_id=user_id,
        filename=file.filename,
        file_path=str(file_path),
        file_size=len(content),
        mime_type=file.content_type,
    )

    # Process with OCR
    ocr_service = OCRService()
    result = await ocr_service.process_image_complete(str(file_path))

    if result["success"]:
        await chat_service.update_ocr_results(
            image.id,
            ocr_text=result["ocr_text"],
            ocr_confidence=result["ocr_confidence"],
            contains_math=result["contains_math"],
            math_latex=result["math_latex"],
            is_handwritten=result["is_handwritten"],
            handwriting_quality=result["handwriting_quality"],
            image_description=result["image_description"],
            suggested_subjects=result["suggested_subjects"],
            processing_time_ms=result["processing_time_ms"],
        )

    return {
        "image_id": image.id,
        "ocr_text": result.get("ocr_text"),
        "contains_math": result.get("contains_math"),
    }


# ============================================================
# Statistics Endpoint
# ============================================================


@router.get("/statistics")
async def get_statistics(user_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get chat statistics"""
    service = AIChatService(db)
    stats = await service.get_chat_statistics(user_id)
    return stats
