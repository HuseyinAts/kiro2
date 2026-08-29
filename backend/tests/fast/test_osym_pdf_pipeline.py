from pathlib import Path

import pytest

from services.osym_pdf_pipeline import OSYMPDFPipeline


@pytest.mark.asyncio
async def test_real_pdf_pipeline():
    # Write a dummy pdf to test with PyMuPDF
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (50, 50),
        "ÖSYM yeni nesil deneme sorusunda Türkçe'nin eklemeli dil olmasının okuduğunu anlama üzerindeki etkisi ölçülür.",
    )
    pdf_path = "dummy_test.pdf"
    doc.save(pdf_path)
    doc.close()

    try:
        from unittest.mock import AsyncMock

        mock_db_session = AsyncMock()
        mock_db_session.add = AsyncMock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        trend = await OSYMPDFPipeline.process_exam_pdf(
            db=mock_db_session,
            file_path=pdf_path,
            year=2026,
            exam_type="TYT",
            subject="Türkçe",
        )

        assert trend is not None
        assert trend.year == 2026
        assert trend.subject == "Türkçe"
        assert trend.avg_word_length > 0
        assert trend.cognitive_load_score > 0

    finally:
        if Path(pdf_path).exists():
            Path(pdf_path).unlink()
