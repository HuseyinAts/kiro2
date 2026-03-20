"""
PDF Processing API
ÖSYM PDF Upload, OCR, Layout Analysis & Question Extraction
"""

import os
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field

from services.pdf_layout_analyzer import PDFLayoutAnalyzer
from core.celery_app import celery_app

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/pdf",
    tags=["PDF Processing"]
)


# ==================== MODELS ====================

class PDFUploadResponse(BaseModel):
    """PDF upload response"""
    job_id: str = Field(..., description="Processing job ID")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    status: str = Field(default="queued", description="Processing status")
    message: str = Field(..., description="Status message")
    estimated_time_seconds: int = Field(..., description="Estimated processing time")


class PDFProcessingStatus(BaseModel):
    """PDF processing status"""
    job_id: str
    status: str  # queued, processing, completed, failed
    progress: float  # 0.0 - 1.0
    current_page: Optional[int] = None
    total_pages: Optional[int] = None
    message: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class ExtractedQuestion(BaseModel):
    """Extracted question from PDF"""
    question_number: int
    question_text: str
    options: Dict[str, str]  # {'A': '...', 'B': '...', ...}
    correct_answer: Optional[str] = None
    subject: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    confidence_score: float  # 0.0 - 1.0
    page_number: int
    bounding_box: Optional[Dict[str, float]] = None  # {x, y, width, height}


class PDFProcessingResult(BaseModel):
    """PDF processing result"""
    job_id: str
    filename: str
    status: str
    total_pages: int
    questions_extracted: int
    questions: List[ExtractedQuestion]
    metadata: Dict[str, Any]
    processing_time_seconds: float
    warnings: List[str] = []
    errors: List[str] = []


class PDFProcessingConfig(BaseModel):
    """PDF processing configuration"""
    enable_ocr: bool = Field(default=True, description="Enable OCR for scanned PDFs")
    extract_images: bool = Field(default=True, description="Extract images and figures")
    extract_tables: bool = Field(default=True, description="Extract tables")
    auto_detect_metadata: bool = Field(default=True, description="Auto-detect exam metadata")
    min_confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Minimum confidence score")


# ==================== STORAGE ====================

# In-memory storage for processing jobs (use Redis in production)
processing_jobs: Dict[str, Dict[str, Any]] = {}

# PDF upload directory
UPLOAD_DIR = Path("backend/uploads/pdfs")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ==================== CELERY TASKS ====================

@celery_app.task(name='tasks.process_pdf')
def process_pdf_task(
    job_id: str,
    file_path: str,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Celery task for PDF processing

    Args:
        job_id: Processing job ID
        file_path: Path to PDF file
        config: Processing configuration

    Returns:
        Processing results
    """
    try:
        # Update status
        processing_jobs[job_id]['status'] = 'processing'
        processing_jobs[job_id]['started_at'] = datetime.now()

        # Initialize analyzer
        analyzer = PDFLayoutAnalyzer(enable_ocr=config.get('enable_ocr', True))

        # Process PDF
        logger.info(f"Processing PDF: {file_path}")
        layout_result = analyzer.analyze_pdf_layout(file_path)

        # Extract metadata
        metadata = {}
        if config.get('auto_detect_metadata', True):
            metadata = analyzer.extract_metadata(file_path)

        # Extract questions
        questions = layout_result.get('questions', [])

        # Filter by confidence
        min_confidence = config.get('min_confidence', 0.5)
        filtered_questions = []

        for idx, q in enumerate(questions):
            confidence = analyzer.calculate_confidence_score(q)

            if confidence >= min_confidence:
                filtered_questions.append({
                    'question_number': idx + 1,
                    'question_text': q.get('text', ''),
                    'options': q.get('options', {}),
                    'correct_answer': q.get('correct_answer'),
                    'subject': metadata.get('subject'),
                    'topic': q.get('topic'),
                    'difficulty': q.get('difficulty'),
                    'confidence_score': confidence,
                    'page_number': q.get('page_number', 1),
                    'bounding_box': q.get('bounding_box')
                })

        # Calculate processing time
        processing_time = (datetime.now() - processing_jobs[job_id]['started_at']).total_seconds()

        # Prepare result
        result = {
            'job_id': job_id,
            'filename': processing_jobs[job_id]['filename'],
            'status': 'completed',
            'total_pages': layout_result.get('total_pages', 0),
            'questions_extracted': len(filtered_questions),
            'questions': filtered_questions,
            'metadata': metadata,
            'processing_time_seconds': processing_time,
            'warnings': layout_result.get('warnings', []),
            'errors': layout_result.get('errors', [])
        }

        # Update job status
        processing_jobs[job_id].update({
            'status': 'completed',
            'completed_at': datetime.now(),
            'result': result,
            'progress': 1.0
        })

        logger.info(f"PDF processing completed: {job_id} - {len(filtered_questions)} questions extracted")

        return result

    except Exception as e:
        logger.error(f"PDF processing failed: {job_id} - {str(e)}")

        processing_jobs[job_id].update({
            'status': 'failed',
            'completed_at': datetime.now(),
            'error': str(e),
            'progress': 0.0
        })

        raise


# ==================== ENDPOINTS ====================

@router.post("/upload", response_model=PDFUploadResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    enable_ocr: bool = Query(default=True, description="Enable OCR"),
    extract_images: bool = Query(default=True, description="Extract images"),
    extract_tables: bool = Query(default=True, description="Extract tables"),
    auto_detect_metadata: bool = Query(default=True, description="Auto-detect metadata"),
    min_confidence: float = Query(default=0.5, ge=0.0, le=1.0, description="Min confidence")
) -> PDFUploadResponse:
    """
    Upload PDF for processing

    Endpoint: POST /api/pdf/upload

    Args:
        file: PDF file (max 50MB)
        enable_ocr: Enable OCR for scanned PDFs
        extract_images: Extract images and figures
        extract_tables: Extract tables
        auto_detect_metadata: Auto-detect exam metadata
        min_confidence: Minimum confidence score

    Returns:
        Upload response with job_id

    Example:
        curl -X POST http://localhost:8000/api/pdf/upload \
          -F "file=@osym_2024_tyt.pdf" \
          -F "enable_ocr=true"
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Validate file size (max 50MB)
    file_content = await file.read()
    file_size = len(file_content)

    if file_size > 50 * 1024 * 1024:  # 50MB
        raise HTTPException(status_code=400, detail="File size exceeds 50MB limit")

    # Generate job ID
    job_id = str(uuid.uuid4())

    # Save file
    file_path = UPLOAD_DIR / f"{job_id}_{file.filename}"

    try:
        with open(file_path, 'wb') as f:
            f.write(file_content)

        # Create processing config
        config = {
            'enable_ocr': enable_ocr,
            'extract_images': extract_images,
            'extract_tables': extract_tables,
            'auto_detect_metadata': auto_detect_metadata,
            'min_confidence': min_confidence
        }

        # Initialize job
        processing_jobs[job_id] = {
            'job_id': job_id,
            'filename': file.filename,
            'file_path': str(file_path),
            'file_size': file_size,
            'status': 'queued',
            'progress': 0.0,
            'config': config,
            'created_at': datetime.now(),
            'started_at': None,
            'completed_at': None,
            'result': None,
            'error': None
        }

        # Queue processing task
        background_tasks.add_task(
            process_pdf_task.delay,
            job_id=job_id,
            file_path=str(file_path),
            config=config
        )

        # Estimate processing time (1-2 seconds per page)
        estimated_pages = file_size / (100 * 1024)  # rough estimate
        estimated_time = int(estimated_pages * 2)

        logger.info(f"PDF uploaded: {job_id} - {file.filename} ({file_size} bytes)")

        return PDFUploadResponse(
            job_id=job_id,
            filename=file.filename,
            file_size=file_size,
            status="queued",
            message="PDF queued for processing",
            estimated_time_seconds=estimated_time
        )

    except Exception as e:
        logger.error(f"PDF upload failed: {str(e)}")

        # Clean up file
        if file_path.exists():
            file_path.unlink()

        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/status/{job_id}", response_model=PDFProcessingStatus)
async def get_processing_status(job_id: str) -> PDFProcessingStatus:
    """
    Get PDF processing status

    Endpoint: GET /api/pdf/status/{job_id}

    Args:
        job_id: Processing job ID

    Returns:
        Processing status

    Example:
        curl http://localhost:8000/api/pdf/status/abc123
    """
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = processing_jobs[job_id]

    return PDFProcessingStatus(
        job_id=job_id,
        status=job['status'],
        progress=job['progress'],
        current_page=job.get('current_page'),
        total_pages=job.get('total_pages'),
        message=job.get('message', f"Status: {job['status']}"),
        started_at=job.get('started_at'),
        completed_at=job.get('completed_at'),
        error=job.get('error')
    )


@router.get("/results/{job_id}", response_model=PDFProcessingResult)
async def get_processing_results(job_id: str) -> PDFProcessingResult:
    """
    Get PDF processing results

    Endpoint: GET /api/pdf/results/{job_id}

    Args:
        job_id: Processing job ID

    Returns:
        Processing results with extracted questions

    Example:
        curl http://localhost:8000/api/pdf/results/abc123
    """
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = processing_jobs[job_id]

    if job['status'] != 'completed':
        raise HTTPException(
            status_code=400,
            detail=f"Processing not completed. Current status: {job['status']}"
        )

    if not job.get('result'):
        raise HTTPException(status_code=500, detail="Results not available")

    return PDFProcessingResult(**job['result'])


@router.delete("/cancel/{job_id}")
async def cancel_processing(job_id: str) -> Dict[str, Any]:
    """
    Cancel PDF processing job

    Endpoint: DELETE /api/pdf/cancel/{job_id}

    Args:
        job_id: Processing job ID

    Returns:
        Cancellation confirmation

    Example:
        curl -X DELETE http://localhost:8000/api/pdf/cancel/abc123
    """
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = processing_jobs[job_id]

    if job['status'] in ['completed', 'failed']:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel {job['status']} job"
        )

    # Cancel Celery task
    try:
        celery_app.control.revoke(job_id, terminate=True)
    except Exception as e:
        logger.warning(f"Failed to revoke Celery task: {e}")

    # Update status
    job['status'] = 'cancelled'
    job['completed_at'] = datetime.now()
    job['error'] = 'Cancelled by user'

    # Clean up file
    file_path = Path(job['file_path'])
    if file_path.exists():
        file_path.unlink()

    logger.info(f"PDF processing cancelled: {job_id}")

    return {
        "success": True,
        "message": f"Processing cancelled: {job_id}",
        "job_id": job_id,
        "status": "cancelled"
    }


@router.get("/jobs", response_model=List[PDFProcessingStatus])
async def list_processing_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(default=50, le=100, description="Max results")
) -> List[PDFProcessingStatus]:
    """
    List all PDF processing jobs

    Endpoint: GET /api/pdf/jobs

    Args:
        status: Filter by status (queued/processing/completed/failed)
        limit: Maximum number of results

    Returns:
        List of processing jobs

    Example:
        curl http://localhost:8000/api/pdf/jobs?status=completed&limit=10
    """
    jobs = list(processing_jobs.values())

    # Filter by status
    if status:
        jobs = [j for j in jobs if j['status'] == status]

    # Sort by creation time (newest first)
    jobs.sort(key=lambda x: x['created_at'], reverse=True)

    # Limit results
    jobs = jobs[:limit]

    # Convert to status objects
    results = []
    for job in jobs:
        results.append(PDFProcessingStatus(
            job_id=job['job_id'],
            status=job['status'],
            progress=job['progress'],
            current_page=job.get('current_page'),
            total_pages=job.get('total_pages'),
            message=f"Status: {job['status']}",
            started_at=job.get('started_at'),
            completed_at=job.get('completed_at'),
            error=job.get('error')
        ))

    return results


@router.get("/health")
async def pdf_api_health() -> Dict[str, Any]:
    """
    PDF API health check

    Endpoint: GET /api/pdf/health

    Returns:
        Health status and statistics
    """
    total_jobs = len(processing_jobs)
    queued = sum(1 for j in processing_jobs.values() if j['status'] == 'queued')
    processing = sum(1 for j in processing_jobs.values() if j['status'] == 'processing')
    completed = sum(1 for j in processing_jobs.values() if j['status'] == 'completed')
    failed = sum(1 for j in processing_jobs.values() if j['status'] == 'failed')

    # Check PDF analyzer
    try:
        analyzer = PDFLayoutAnalyzer()
        analyzer_healthy = True
    except Exception as e:
        analyzer_healthy = False
        logger.error(f"PDF analyzer health check failed: {e}")

    # Check upload directory
    upload_dir_exists = UPLOAD_DIR.exists()
    upload_dir_writable = os.access(UPLOAD_DIR, os.W_OK) if upload_dir_exists else False

    # Check Celery
    try:
        celery_healthy = celery_app.control.ping(timeout=1.0) is not None
    except (ConnectionError, TimeoutError, AttributeError) as e:
        logger.debug(f"Celery health check failed: {e}")
        celery_healthy = False

    return {
        "status": "healthy" if (analyzer_healthy and upload_dir_writable and celery_healthy) else "degraded",
        "analyzer_healthy": analyzer_healthy,
        "upload_dir_exists": upload_dir_exists,
        "upload_dir_writable": upload_dir_writable,
        "celery_healthy": celery_healthy,
        "total_jobs": total_jobs,
        "jobs_by_status": {
            "queued": queued,
            "processing": processing,
            "completed": completed,
            "failed": failed
        },
        "timestamp": datetime.now().isoformat()
    }
