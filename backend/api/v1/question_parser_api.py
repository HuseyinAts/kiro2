from fastapi import APIRouter, File, UploadFile, BackgroundTasks, HTTPException
from typing import List
import shutil
from pathlib import Path
import uuid
import sys
import os
import logging

# Services dizinini path'e ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from services.question_parser.pipeline import YKSQuestionPipeline
    PARSER_AVAILABLE = True
except ImportError as e:
    PARSER_AVAILABLE = False
    YKSQuestionPipeline = None
    logger = logging.getLogger(__name__)
    logger.warning(f"YKSQuestionPipeline not available: {e}")

router = APIRouter(prefix="/question-parser", tags=["question-parser"])

# Global pipeline instance
pipeline = None

def get_pipeline():
    if not PARSER_AVAILABLE:
        raise HTTPException(503, "Question parser not available")
    global pipeline
    if pipeline is None:
        pipeline = YKSQuestionPipeline()
    return pipeline

@router.post("/parse-test")
async def parse_test_page(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    Tek bir test sayfasını parse et
    """
    # Geçici dosya kaydet
    temp_dir = Path("backend/temp_uploads")
    temp_dir.mkdir(exist_ok=True, parents=True)

    file_id = str(uuid.uuid4())
    temp_file = temp_dir / f"{file_id}_{file.filename}"

    try:
        # Dosyayı kaydet
        with open(temp_file, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Pipeline'ı çalıştır
        pipeline_instance = get_pipeline()
        result = await pipeline_instance.process_test_page(str(temp_file))

        # Temizlik (arka planda)
        if background_tasks:
            background_tasks.add_task(lambda: temp_file.unlink(missing_ok=True))

        return {
            "success": True,
            "data": result
        }

    except Exception as e:
        # Hata durumunda temizlik
        temp_file.unlink(missing_ok=True)
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/parse-batch")
async def parse_test_batch(
    files: List[UploadFile] = File(...)
):
    """
    Birden fazla test sayfasını parse et
    """
    temp_dir = Path("backend/temp_uploads")
    temp_dir.mkdir(exist_ok=True, parents=True)

    temp_files = []

    try:
        # Tüm dosyaları kaydet
        for file in files:
            file_id = str(uuid.uuid4())
            temp_file = temp_dir / f"{file_id}_{file.filename}"

            with open(temp_file, 'wb') as buffer:
                shutil.copyfileobj(file.file, buffer)

            temp_files.append(str(temp_file))

        # Pipeline'ı çalıştır
        pipeline_instance = get_pipeline()
        results = await pipeline_instance.process_batch(temp_files)

        # Temizlik
        for temp_file in temp_files:
            Path(temp_file).unlink(missing_ok=True)

        return {
            "success": True,
            "data": results
        }

    except Exception as e:
        # Hata durumunda temizlik
        for temp_file in temp_files:
            Path(temp_file).unlink(missing_ok=True)

        return {
            "success": False,
            "error": str(e)
        }
