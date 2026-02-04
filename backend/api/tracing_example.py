"""
Example Traced Endpoints - Sprint 11
Demonstrates distributed tracing with OpenTelemetry + Jaeger

Examples show:
- Automatic request tracing
- Custom business spans
- Performance profiling
- Error tracking
- Trace context propagation
"""
import asyncio
import time
import random
from typing import Dict

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from core.tracing_middleware import (
    get_business_span_manager,
    profile_function_performance,
)
from core.opentelemetry_config import trace_function

router = APIRouter(prefix="/api/tracing-demo", tags=["Distributed Tracing Demo"])


class ExamSessionRequest(BaseModel):
    """Example exam session request"""

    exam_id: str
    user_id: str
    exam_type: str = "TYT"


class QuestionAnswerRequest(BaseModel):
    """Example question answer request"""

    question_id: str
    user_id: str
    answer: str
    correct_answer: str


# ==================== AUTOMATIC TRACING EXAMPLES ====================


@router.get("/simple")
async def simple_traced_request() -> Dict:
    """
    Simple traced request - automatically traced by middleware

    Visit Jaeger UI: http://localhost:16686
    Search for service: kiro2-backend
    Find trace with span: GET /api/tracing-demo/simple
    """
    # Simulate some work
    await asyncio_sleep(0.1)

    return {
        "message": "This request is automatically traced!",
        "trace_info": "Check X-Trace-ID in response headers",
        "jaeger_ui": "http://localhost:16686",
    }


@router.get("/slow-request")
async def slow_request_example() -> Dict:
    """
    Slow request example - will be marked as 'slow' in traces

    Middleware automatically classifies request performance:
    - < 100ms: fast
    - 100-500ms: normal
    - 500-2000ms: slow
    - > 2000ms: very_slow

    This request takes ~1.5s, so it will be classified as 'slow'
    and trigger a 'slow_request' event in the span.
    """
    # Simulate slow processing
    await asyncio_sleep(1.5)

    return {
        "message": "This was a slow request!",
        "performance": "Check 'performance.classification' attribute in trace",
        "event": "Look for 'slow_request' event in span",
    }


# ==================== BUSINESS LOGIC TRACING ====================


@router.post("/exam-session")
async def start_exam_session(request: ExamSessionRequest) -> Dict:
    """
    Example: Tracing an exam session (business operation)

    Creates a custom business span with exam context:
    - exam.id
    - user.id
    - business.operation: exam_taking

    Check Jaeger for nested spans:
    1. HTTP Request span (middleware)
    2. exam.session span (business logic)
    """
    span_manager = get_business_span_manager()

    with span_manager.trace_exam_session(request.exam_id, request.user_id):
        # Simulate exam initialization
        await asyncio_sleep(0.2)

        # Add custom event
        from opentelemetry import trace

        current_span = trace.get_current_span()
        current_span.add_event(
            "exam_initialized",
            {"exam_type": request.exam_type, "questions_count": 40},
        )

        # Simulate more work
        await asyncio_sleep(0.1)

        return {
            "exam_id": request.exam_id,
            "user_id": request.user_id,
            "status": "started",
            "trace_info": "Check nested 'exam.session' span in trace",
        }


@router.post("/question-answer")
async def answer_question(request: QuestionAnswerRequest) -> Dict:
    """
    Example: Tracing question answering

    Creates a custom span for question solving with:
    - question.id
    - user.id
    - answer.correct (true/false)
    """
    span_manager = get_business_span_manager()
    correct = request.answer == request.correct_answer

    with span_manager.trace_question_answer(
        request.question_id, request.user_id, correct
    ):
        # Simulate question processing
        await asyncio_sleep(0.05)

        # Add attributes to span
        from opentelemetry import trace

        current_span = trace.get_current_span()
        current_span.set_attribute("question.difficulty", "medium")
        current_span.set_attribute("answer.time_spent_ms", 15000)

        return {
            "question_id": request.question_id,
            "correct": correct,
            "trace_info": "Check 'question.answer' span with attributes",
        }


@router.get("/irt-calculation/{user_id}")
async def calculate_irt(user_id: str, algorithm: str = Query("IRT")) -> Dict:
    """
    Example: Tracing IRT calculation

    Creates algorithm-specific span:
    - algorithm.name (IRT, FSRS, ZPD)
    - algorithm.type: adaptive_learning
    - business.operation: ability_estimation
    """
    span_manager = get_business_span_manager()

    with span_manager.trace_irt_calculation(user_id, algorithm):
        # Simulate IRT calculation
        await asyncio_sleep(0.3)

        # Calculate fake theta
        theta = random.uniform(-3.0, 3.0)

        from opentelemetry import trace

        current_span = trace.get_current_span()
        current_span.set_attribute("algorithm.result.theta", theta)
        current_span.set_attribute("algorithm.iterations", 5)

        return {
            "user_id": user_id,
            "algorithm": algorithm,
            "theta": round(theta, 3),
            "trace_info": f"Check 'algorithm.{algorithm.lower()}' span",
        }


# ==================== AI MODEL TRACING ====================


@router.get("/ai-chat/{user_id}")
async def ai_chat_example(user_id: str, model: str = Query("GPT-4")) -> Dict:
    """
    Example: Tracing AI model requests

    Creates AI model span with:
    - ai.model (GPT-4, BERTurk, etc.)
    - ai.operation (chat, embedding, classification)
    - business.operation: ai_inference
    """
    span_manager = get_business_span_manager()

    with span_manager.trace_ai_model_request(model, "chat"):
        # Simulate AI processing
        await asyncio_sleep(0.8)

        from opentelemetry import trace

        current_span = trace.get_current_span()
        current_span.set_attribute("ai.tokens.prompt", 150)
        current_span.set_attribute("ai.tokens.completion", 300)
        current_span.set_attribute("ai.cost_usd", 0.0045)

        return {
            "user_id": user_id,
            "model": model,
            "response": "Bu bir örnek AI yanıtıdır.",
            "trace_info": f"Check 'ai.{model.lower()}.chat' span",
        }


# ==================== DECORATOR-BASED TRACING ====================


@trace_function(name="process_recommendation", attributes={"algorithm": "collaborative"})
async def process_recommendation(user_id: str) -> Dict:
    """
    Internal function with decorator-based tracing

    @trace_function automatically creates a span for this function
    """
    # Simulate recommendation processing
    await asyncio_sleep(0.2)

    return {
        "user_id": user_id,
        "recommendations": ["video1", "video2", "video3"],
        "algorithm": "collaborative_filtering",
    }


@router.get("/recommendation/{user_id}")
async def get_recommendations(user_id: str) -> Dict:
    """
    Example: Using @trace_function decorator

    The process_recommendation function is automatically traced
    with custom name and attributes.

    You'll see nested spans:
    1. HTTP Request (middleware)
    2. process_recommendation (decorator)
    """
    result = await process_recommendation(user_id)

    return {
        **result,
        "trace_info": "Check 'process_recommendation' span created by decorator",
    }


# ==================== PERFORMANCE PROFILING ====================


@profile_function_performance("calculate_exam_statistics")
async def calculate_statistics(exam_id: str) -> Dict:
    """
    Function with performance profiling

    @profile_function_performance tracks execution time
    and adds performance.{func_name} span
    """
    # Simulate heavy computation
    await asyncio_sleep(0.5)

    return {
        "exam_id": exam_id,
        "average_score": 75.5,
        "completion_rate": 0.89,
        "total_students": 1250,
    }


@router.get("/exam-statistics/{exam_id}")
async def exam_statistics(exam_id: str) -> Dict:
    """
    Example: Performance profiling

    The calculate_statistics function is profiled,
    and its execution time is recorded in the span.
    """
    stats = await calculate_statistics(exam_id)

    return {
        **stats,
        "trace_info": "Check 'performance.calculate_exam_statistics' span with duration",
    }


# ==================== ERROR TRACKING ====================


@router.get("/error-example")
async def error_example() -> Dict:
    """
    Example: Error tracking in traces

    When an exception occurs, it's automatically:
    1. Recorded in the span
    2. Span status set to ERROR
    3. Exception details added to span attributes

    Check Jaeger for error traces (red in UI)
    """
    # Simulate some work before error
    await asyncio_sleep(0.1)

    # Trigger error
    raise HTTPException(status_code=500, detail="Simulated error for tracing demo")


# ==================== TRACE CONTEXT PROPAGATION ====================


async def internal_service_call(trace_id: str) -> Dict:
    """Simulate calling another service with trace context"""
    # In a real scenario, you would pass trace context to external services
    # via HTTP headers (W3C Trace Context format)
    await asyncio_sleep(0.1)

    return {"called_service": "internal-api", "trace_id": trace_id}


@router.get("/distributed-trace")
async def distributed_trace_example() -> Dict:
    """
    Example: Distributed trace across services

    In a real microservices setup:
    1. This service creates a span
    2. Trace context is propagated to other services via headers
    3. All services contribute spans to the same trace

    Headers used for propagation:
    - traceparent (W3C Trace Context)
    - tracestate (vendor-specific data)
    """
    from opentelemetry import trace

    # Get current trace ID
    current_span = trace.get_current_span()
    trace_id = format(current_span.get_span_context().trace_id, "032x")

    # Simulate calling another service
    result = await internal_service_call(trace_id)

    return {
        "trace_id": trace_id,
        "service_call": result,
        "info": "In production, trace context would propagate to all services",
        "headers": ["traceparent", "tracestate"],
    }


# ==================== HELPER FUNCTIONS ====================


async def asyncio_sleep(seconds: float):
    """Helper to simulate async work"""
    import asyncio

    await asyncio.sleep(seconds)


# ==================== INFO ENDPOINT ====================


@router.get("/")
async def tracing_info() -> Dict:
    """
    Distributed Tracing Demo Information

    All endpoints in this router demonstrate different tracing features.
    Visit each endpoint and then check Jaeger UI to see the traces.
    """
    return {
        "title": "Sprint 11: Distributed Tracing Demo",
        "jaeger_ui": "http://localhost:16686",
        "service_name": "kiro2-backend",
        "examples": {
            "automatic_tracing": [
                "GET /api/tracing-demo/simple",
                "GET /api/tracing-demo/slow-request",
            ],
            "business_logic": [
                "POST /api/tracing-demo/exam-session",
                "POST /api/tracing-demo/question-answer",
                "GET /api/tracing-demo/irt-calculation/{user_id}",
            ],
            "ai_models": ["GET /api/tracing-demo/ai-chat/{user_id}"],
            "decorators": [
                "GET /api/tracing-demo/recommendation/{user_id}",
                "GET /api/tracing-demo/exam-statistics/{exam_id}",
            ],
            "error_tracking": ["GET /api/tracing-demo/error-example"],
            "distributed": ["GET /api/tracing-demo/distributed-trace"],
        },
        "how_to_use": {
            "step1": "Start Jaeger: cd monitoring/jaeger && docker-compose -f docker-compose.jaeger.yml up",
            "step2": "Start backend: uvicorn main:app --reload",
            "step3": "Call endpoints: curl http://localhost:8000/api/tracing-demo/simple",
            "step4": "View traces: Open http://localhost:16686 in browser",
            "step5": "Search for traces: Select 'kiro2-backend' service and click 'Find Traces'",
        },
        "features": {
            "automatic": "All HTTP requests automatically traced",
            "business_spans": "Custom spans for business operations",
            "performance": "Request duration and classification",
            "errors": "Automatic exception recording",
            "metadata": "Request/response attributes",
            "user_context": "User ID and role tracking",
            "trace_id": "X-Trace-ID header in responses",
        },
    }
