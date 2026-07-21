import pytest
from pydantic import ValidationError

from api.question_crud_api import QuestionCreateRequest


def test_content_shield_html_repair():
    # Test valid HTML is unchanged
    req = QuestionCreateRequest(
        soru_metni="Bu bir test sorusudur ve en az 15 karakter olmalidir.",
        soru_html="<p>Test HTML</p>",
        secenekler=["A", "B", "C", "D"],
        dogru_cevap="A",
        konu="Matematik"
    )
    assert req.soru_html == "<p>Test HTML</p>"

    # Test unclosed tags are repaired
    req2 = QuestionCreateRequest(
        soru_metni="Bu bir test sorusudur ve en az 15 karakter olmalidir.",
        soru_html="<div><p>Test HTML",
        secenekler=["A", "B", "C", "D"],
        dogru_cevap="A",
        konu="Matematik"
    )
    assert req2.soru_html == "<div><p>Test HTML</p></div>"

def test_content_shield_latex_repair():
    # Test unclosed dollar signs are repaired
    req = QuestionCreateRequest(
        soru_metni="Bu bir test sorusudur ve en az 15 karakter olmalidir.",
        soru_latex="$x^2 + y^2 = z^2",
        secenekler=["A", "B", "C", "D"],
        dogru_cevap="A",
        konu="Matematik"
    )
    assert req.soru_latex == "$x^2 + y^2 = z^2$"

    # Test mismatched braces are repaired
    req2 = QuestionCreateRequest(
        soru_metni="Bu bir test sorusudur ve en az 15 karakter olmalidir.",
        soru_latex="\\frac{1}{2",
        secenekler=["A", "B", "C", "D"],
        dogru_cevap="A",
        konu="Matematik"
    )
    assert req2.soru_latex == "\\frac{1}{2}"

def test_content_shield_trash_text_rejection():
    # Test text shorter than 15 chars is rejected
    with pytest.raises(ValidationError) as exc_info:
        QuestionCreateRequest(
            soru_metni="Kısa.",
            secenekler=["A", "B", "C", "D"],
            dogru_cevap="A",
            konu="Matematik"
        )
    assert "Question text must be at least 15 characters long" in str(exc_info.value)

    # Test short math formulas bypass the 15 char check
    req = QuestionCreateRequest(
        soru_metni="12x²y³",
        secenekler=["A", "B", "C", "D"],
        dogru_cevap="A",
        konu="Matematik"
    )
    assert req.soru_metni == "12x²y³"
