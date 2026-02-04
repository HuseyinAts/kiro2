"""
Streaming Chat API
Server-Sent Events (SSE) for real-time chat responses
Target: Reduce perceived latency and improve user experience
"""
import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from core.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/streaming", tags=["Streaming Chat"])


class ChatMessage(BaseModel):
    """Chat message"""

    role: str = Field(..., description="Message role (user/assistant/system)")
    content: str = Field(..., description="Message content")


class StreamingChatRequest(BaseModel):
    """Streaming chat request"""

    messages: List[ChatMessage] = Field(..., description="Chat history")
    model: str = Field("gpt-3.5-turbo", description="Model name")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, description="Max tokens to generate")
    stream: bool = Field(True, description="Enable streaming")


class RAGStreamingRequest(BaseModel):
    """RAG streaming request"""

    query: str = Field(..., description="User query")
    k: int = Field(5, ge=1, le=20, description="Number of documents")
    expand_queries: bool = Field(True, description="Enable query expansion")
    use_reranking: bool = Field(True, description="Enable reranking")


@router.post("/chat")
async def stream_chat(
    request: StreamingChatRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Stream chat completion responses

    Uses Server-Sent Events (SSE) for real-time streaming.
    Client receives tokens as they're generated.
    """
    try:

        async def generate_stream():
            """Generate SSE stream"""
            try:
                from core.llm_pool import OpenAIPool
                import os

                # Get LLM client
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    yield _format_sse_error("OpenAI API key not configured")
                    return

                llm_client = OpenAIPool(api_key)

                # Convert messages to OpenAI format
                messages = [
                    {"role": msg.role, "content": msg.content}
                    for msg in request.messages
                ]

                # Stream completion
                start_time = time.time()
                token_count = 0

                async for chunk in llm_client.chat_completion(
                    messages=messages,
                    model=request.model,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    stream=True,
                ):
                    # Parse SSE chunk
                    chunk_str = chunk.decode("utf-8")

                    # Skip empty lines
                    if not chunk_str.strip():
                        continue

                    # Parse JSON
                    if chunk_str.startswith("data: "):
                        data_str = chunk_str[6:]  # Remove "data: " prefix

                        if data_str.strip() == "[DONE]":
                            # Stream completed
                            latency = (time.time() - start_time) * 1000
                            yield _format_sse_event(
                                event="done",
                                data={"tokens": token_count, "latency_ms": latency},
                            )
                            break

                        try:
                            chunk_data = json.loads(data_str)
                            delta = chunk_data.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")

                            if content:
                                token_count += 1
                                yield _format_sse_event(
                                    event="token", data={"content": content}
                                )
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse chunk: {data_str}")

                await llm_client.close()

            except Exception as e:
                logger.error(f"Streaming error: {e}")
                yield _format_sse_error(str(e))

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            },
        )

    except Exception as e:
        logger.error(f"Stream chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag")
async def stream_rag_query(
    request: RAGStreamingRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Stream RAG query results

    Streams intermediate results:
    1. Query expansion
    2. Document retrieval
    3. Reranking
    4. LLM generation (token by token)
    """
    try:

        async def generate_rag_stream():
            """Generate RAG SSE stream"""
            try:
                from core.parallel_rag import ParallelRAGPipeline
                from core.vector_optimizations import get_vector_store
                from core.llm_pool import OpenAIPool
                import os

                # Initialize components
                vector_store = await get_vector_store()
                api_key = os.getenv("OPENAI_API_KEY")
                llm_client = OpenAIPool(api_key) if api_key else None

                if not llm_client:
                    yield _format_sse_error("OpenAI API key not configured")
                    return

                # Initialize embedding model for RAG
                try:
                    from services.nlp_training.berturk_embedding import (
                        BERTurkEmbeddingService,
                    )

                    embedding_model = BERTurkEmbeddingService()
                    logger.info("BERTurk embedding model loaded for RAG")
                except Exception as e:
                    logger.warning(
                        f"Failed to load BERTurk embedding model: {e}, using default"
                    )
                    embedding_model = None

                # Create pipeline
                pipeline = ParallelRAGPipeline(
                    vector_store=vector_store,
                    llm_client=llm_client,
                    embedding_model=embedding_model,
                )

                # Stream query results
                async for event in pipeline.stream_query(
                    query_text=request.query, k=request.k
                ):
                    yield _format_sse_event(
                        event=event.get("type", "update"), data=event
                    )

                await llm_client.close()

            except Exception as e:
                logger.error(f"RAG streaming error: {e}")
                yield _format_sse_error(str(e))

        return StreamingResponse(
            generate_rag_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    except Exception as e:
        logger.error(f"Stream RAG error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/exam-explanation")
async def stream_exam_explanation(
    question_id: str,
    student_answer: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Stream exam question explanation

    Provides real-time explanation generation for exam questions.
    """
    try:

        async def generate_explanation_stream():
            """Generate explanation SSE stream"""
            try:
                from services.soru_bankasi_service import soru_bankasi_servisi
                from core.llm_pool import OpenAIPool
                import os

                # Get question
                question = await soru_bankasi_servisi.soru_getir(question_id)

                if not question:
                    yield _format_sse_error("Soru bulunamadı")
                    return

                # Send question details
                yield _format_sse_event(
                    event="question",
                    data={
                        "id": question.id,
                        "text": question.question_text,
                        "correct_answer": question.correct_answer,
                        "student_answer": student_answer,
                    },
                )

                # Generate explanation
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    # Use stored explanation
                    yield _format_sse_event(
                        event="explanation",
                        data={
                            "content": question.explanation or "Açıklama mevcut değil"
                        },
                    )
                    yield _format_sse_event(event="done", data={})
                    return

                llm_client = OpenAIPool(api_key)

                # Build prompt
                prompt = f"""Aşağıdaki sınav sorusunu Türkçe olarak detaylı bir şekilde açıkla.

Soru: {question.question_text}

Seçenekler:
A) {question.option_a}
B) {question.option_b}
C) {question.option_c}
D) {question.option_d}
{f'E) {question.option_e}' if question.option_e else ''}

Doğru Cevap: {question.correct_answer}
"""

                if student_answer and student_answer != question.correct_answer:
                    prompt += f"\nÖğrencinin Cevabı: {student_answer}\n\nÖğrencinin neden yanlış yaptığını da açıkla."

                prompt += "\n\nAçıklama:"

                messages = [{"role": "user", "content": prompt}]

                # Stream explanation
                async for chunk in llm_client.chat_completion(
                    messages=messages,
                    model="gpt-3.5-turbo",
                    temperature=0.7,
                    stream=True,
                ):
                    chunk_str = chunk.decode("utf-8")
                    if chunk_str.startswith("data: "):
                        data_str = chunk_str[6:]
                        if data_str.strip() == "[DONE]":
                            yield _format_sse_event(event="done", data={})
                            break

                        try:
                            chunk_data = json.loads(data_str)
                            delta = chunk_data.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")

                            if content:
                                yield _format_sse_event(
                                    event="explanation", data={"content": content}
                                )
                        except json.JSONDecodeError:
                            pass

                await llm_client.close()

            except Exception as e:
                logger.error(f"Explanation streaming error: {e}")
                yield _format_sse_error(str(e))

        return StreamingResponse(
            generate_explanation_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    except Exception as e:
        logger.error(f"Stream explanation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _format_sse_event(event: str, data: Any) -> str:
    """Format Server-Sent Event"""
    data_str = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {data_str}\n\n"


def _format_sse_error(error_message: str) -> str:
    """Format SSE error event"""
    return _format_sse_event(event="error", data={"error": error_message})


@router.get("/health")
async def health_check():
    """Health check for streaming API"""
    return {
        "success": True,
        "data": {
            "service": "Streaming Chat API",
            "status": "healthy",
            "features": [
                "Server-Sent Events (SSE)",
                "Real-time token streaming",
                "RAG query streaming",
                "Exam explanation streaming",
            ],
        },
        "message": "Streaming API çalışıyor",
    }
