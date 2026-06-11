import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# NLP ThreadPool - isolated for Turkish NLP & morphology calculations
NLP_POOL = ThreadPoolExecutor(max_workers=8, thread_name_prefix="nlp_worker_pool")

# PDF ThreadPool - isolated for PDF generation and heavy document tasks
PDF_POOL = ThreadPoolExecutor(max_workers=4, thread_name_prefix="pdf_worker_pool")

def shutdown_pools():
    """
    Gracefully shut down all custom ThreadPoolExecutors.
    This prevents zombie threads from hanging Pytest or live application shutdown.
    """
    logger.info("[SRE] Shutting down bulkheaded thread pools...")
    NLP_POOL.shutdown(wait=True)
    PDF_POOL.shutdown(wait=True)
    logger.info("[SRE] Thread pools shut down successfully.")
