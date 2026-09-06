from pathlib import Path

import pytest

from services.osym_pdf_pipeline import OSYMPDFPipeline


@pytest.mark.asyncio
async def test_real_pdf_pipeline():
    # Write a dummy pdf to test with PyMuPDF
    #
    # ON KOSUL, KUSUR DEGIL: `fitz` (PyMuPDF) bu deponun HICBIR requirements
    # dosyasinda YOK (olculdu: requirements.txt / requirements-test.txt /
    # requirements.qa.txt -> 0 eslesme). CI'da kurulu olmadigi icin test
    # `ModuleNotFoundError: No module named 'fitz'` ile DUSUYORDU -- yani
    # eksik bir ORTAM on kosulu, urun kusuru gibi raporlaniyordu.
    # `importorskip` bunu skip'e cevirir: PyMuPDF kurulu oldugu her yerde
    # test GERCEKTEN kosar, kurulu olmadigi yerde kapiyi kirmizi tutmaz.
    # PyMuPDF'in bagimlilik listesine EKLENMESI ayri bir urun karari.
    fitz = pytest.importorskip(
        "fitz",
        reason="PyMuPDF (fitz) kurulu degil ve depo bagimliliklarinda tanimli degil",
    )

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
