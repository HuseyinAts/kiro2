"""
Test: Accessibility Agent
"""

import os
import sys
from unittest.mock import patch

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.accessibility_agent import (
    AccessibilityAgent,
    AccessibilityIssue,
    AccessibilityLevel,
    AccessibilityReport,
    ContentType,
    IssueType,
)


@pytest.fixture
def agent():
    """Accessibility agent fixture"""
    return AccessibilityAgent()


@pytest.fixture
def sample_html():
    """Sample HTML content"""
    return """
    <html>
    <head><title>Test Page</title></head>
    <body>
        <img src="test.jpg">
        <h2>Alt Başlık</h2>
        <p>Bu çok karmaşık ve anlaşılması zor bir cümledir ki okuyucuların anlayabilmesi için basitleştirilmesi gerekmektedir.</p>
        <input type="text" id="name">
    </body>
    </html>
    """


@pytest.fixture
def sample_text():
    """Sample text content"""
    return """
    ATP (Adenozin Trifosfat) hücrelerin enerji molekülüdür.
    Bu molekül, hücresel metabolizmada kritik bir rol oynar.
    Mitokondri, ATP üretiminin gerçekleştiği organeldir.
    """


@pytest.mark.asyncio
async def test_analyze_text_content(agent, sample_text):
    """Test text content analysis"""
    report = await agent.analyze_content(
        sample_text, ContentType.TEXT, context="Biyoloji ders materyali"
    )

    assert report is not None
    assert report.content_type == ContentType.TEXT
    assert report.score >= 0 and report.score <= 100
    assert report.level in [
        AccessibilityLevel.A,
        AccessibilityLevel.AA,
        AccessibilityLevel.AAA,
    ]
    assert isinstance(report.issues, list)
    assert isinstance(report.recommendations, list)


@pytest.mark.asyncio
async def test_analyze_html_content(agent, sample_html):
    """Test HTML content analysis"""
    report = await agent.analyze_content(
        sample_html, ContentType.HTML, context="Web sayfası"
    )

    assert report is not None
    assert report.content_type == ContentType.HTML

    # Check for missing alt text issue
    alt_text_issues = [
        i for i in report.issues if i.issue_type == IssueType.MISSING_ALT_TEXT
    ]
    assert len(alt_text_issues) > 0

    # Check for missing headers issue
    header_issues = [
        i for i in report.issues if i.issue_type == IssueType.MISSING_HEADERS
    ]
    assert len(header_issues) > 0  # No H1 in sample


def test_calculate_text_complexity(agent):
    """Test text complexity calculation"""
    simple_text = "Bu basit bir cümle."
    complex_text = "Bu cümle içerisinde münasebetiyle, ehemmiyetli, mütemadiyen gibi karmaşık kelimeler barındırmakta olup okuyucuların anlayabilmesi için ciddi bir çaba gerektirmektedir."

    simple_score = agent._calculate_text_complexity(simple_text)
    complex_score = agent._calculate_text_complexity(complex_text)

    assert simple_score < complex_score
    assert 0 <= simple_score <= 1
    assert 0 <= complex_score <= 1


def test_find_jargon(agent, sample_text):
    """Test jargon detection"""
    jargon_terms = agent._find_jargon(sample_text)

    assert "ATP" in jargon_terms  # Unexplained abbreviation
    # Note: ATP is in terminology_db but its explanation is not in the text


def test_calculate_accessibility_score(agent):
    """Test accessibility score calculation"""
    # No issues
    score1 = agent._calculate_accessibility_score([])
    assert score1 == 100

    # High severity issues
    issues = [
        AccessibilityIssue(
            issue_type=IssueType.MISSING_ALT_TEXT,
            severity="high",
            description="Test",
            location="Test",
            suggestion="Test",
        ),
        AccessibilityIssue(
            issue_type=IssueType.COMPLEX_LANGUAGE,
            severity="medium",
            description="Test",
            location="Test",
            suggestion="Test",
        ),
    ]

    score2 = agent._calculate_accessibility_score(issues)
    assert score2 < 100
    assert score2 >= 0


def test_determine_level(agent):
    """Test accessibility level determination"""
    level_aaa = agent._determine_level(95)
    assert level_aaa == AccessibilityLevel.AAA

    level_aa = agent._determine_level(75)
    assert level_aa == AccessibilityLevel.AA

    level_a = agent._determine_level(50)
    assert level_a == AccessibilityLevel.A


@pytest.mark.asyncio
async def test_generate_alt_text(agent):
    """Test alt text generation"""
    with patch("agents.accessibility_agent.llm_service.generate") as mock_llm:
        mock_llm.return_value = {
            "success": True,
            "text": "Öğrenciler laboratuvarda deney yapıyor",
        }

        alt_text = await agent.generate_alt_text(
            image_data="base64_image_data", context="Fen dersi görseli", language="tr"
        )

        assert alt_text is not None
        assert alt_text.generated_alt != ""
        assert alt_text.confidence > 0
        assert alt_text.language == "tr"


@pytest.mark.asyncio
async def test_simplify_text(agent, sample_text):
    """Test text simplification"""
    with patch(
        "agents.accessibility_agent.llm_service.generate_for_education"
    ) as mock_llm:
        mock_llm.return_value = {
            "success": True,
            "content": "ATP hücrelerin enerji kaynağıdır. Hücrelerde önemli işler yapar.",
        }

        simplified = await agent.simplify_text(sample_text, target_level="beginner")

        assert simplified is not None
        assert len(simplified) > 0


def test_add_term_explanations(agent):
    """Test adding term explanations"""
    text = "LGS sınavına hazırlanıyorum. YKS için de çalışmam gerekiyor."

    result = agent._add_term_explanations(text)

    # Check if explanations are added
    assert "Liselere Giriş Sınavı" in result
    assert "Yükseköğretim Kurumları Sınavı" in result


@pytest.mark.asyncio
async def test_improve_structure_html(agent, sample_html):
    """Test HTML structure improvement suggestions"""
    suggestions = await agent.improve_structure(sample_html, ContentType.HTML)

    assert "headings" in suggestions
    assert len(suggestions["headings"]) > 0  # Should suggest adding H1

    assert "semantic" in suggestions
    assert len(suggestions["semantic"]) > 0


@pytest.mark.asyncio
async def test_improve_structure_text(agent):
    """Test text structure improvement suggestions"""
    long_text = "\n\n".join(["Paragraf " + str(i) for i in range(15)])

    suggestions = await agent.improve_structure(long_text, ContentType.TEXT)

    assert "headings" in suggestions
    assert len(suggestions["headings"]) > 0  # Should suggest sections for long text


@pytest.mark.asyncio
async def test_check_contrast(agent):
    """Test color contrast checking"""
    # Good contrast (black on white)
    result1 = await agent.check_contrast("#000000", "#FFFFFF")
    assert result1["contrast_ratio"] > 7
    assert result1["passes_aa_normal"] == True
    assert result1["passes_aaa_normal"] == True

    # Poor contrast (light gray on white)
    result2 = await agent.check_contrast("#CCCCCC", "#FFFFFF")
    assert result2["contrast_ratio"] < 3
    assert result2["passes_aa_normal"] == False


@pytest.mark.asyncio
async def test_create_accessible_version_text(agent, sample_text):
    """Test creating accessible version of text"""
    with patch.object(agent, "analyze_content") as mock_analyze:
        mock_analyze.return_value = AccessibilityReport(
            report_id="test",
            content_type=ContentType.TEXT,
            issues=[],
            score=80,
            level=AccessibilityLevel.AA,
            recommendations=[],
            improved_content=None,
            metadata={},
        )

        with patch.object(agent, "simplify_text") as mock_simplify:
            mock_simplify.return_value = "Simplified text"

            accessible = await agent.create_accessible_version(
                sample_text, ContentType.TEXT, AccessibilityLevel.AA
            )

            assert accessible is not None
            assert len(accessible) > 0


@pytest.mark.asyncio
async def test_create_accessible_version_html(agent, sample_html):
    """Test creating accessible version of HTML"""
    with patch.object(agent, "analyze_content") as mock_analyze:
        mock_analyze.return_value = AccessibilityReport(
            report_id="test",
            content_type=ContentType.HTML,
            issues=[],
            score=70,
            level=AccessibilityLevel.A,
            recommendations=[],
            improved_content=None,
            metadata={},
        )

        accessible = await agent.create_accessible_version(
            sample_html, ContentType.HTML, AccessibilityLevel.AA
        )

        assert accessible is not None
        # Check if alt text is added
        assert "alt=" in accessible
        # Check if language attribute is added
        if "<html" in accessible:
            assert "lang=" in accessible


def test_get_wcag_guidelines(agent):
    """Test getting WCAG guidelines"""
    guidelines_a = agent.get_wcag_guidelines(AccessibilityLevel.A)
    assert len(guidelines_a) > 0
    assert "1.1.1" in guidelines_a[0]

    guidelines_aa = agent.get_wcag_guidelines(AccessibilityLevel.AA)
    assert len(guidelines_aa) > len(guidelines_a)  # AA includes A guidelines

    guidelines_aaa = agent.get_wcag_guidelines(AccessibilityLevel.AAA)
    assert len(guidelines_aaa) > len(guidelines_aa)  # AAA includes AA and A


def test_get_report(agent):
    """Test getting accessibility report"""
    # Report doesn't exist
    report = agent.get_report("non_existent")
    assert report is None

    # Add a report
    test_report = AccessibilityReport(
        report_id="test_report",
        content_type=ContentType.TEXT,
        issues=[],
        score=85,
        level=AccessibilityLevel.AA,
        recommendations=["Test recommendation"],
        improved_content="Improved content",
        metadata={},
    )
    agent.reports["test_report"] = test_report

    # Get the report
    retrieved = agent.get_report("test_report")
    assert retrieved == test_report
    assert retrieved.score == 85


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
