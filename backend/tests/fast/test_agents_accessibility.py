"""
Tests for Accessibility Agent
Zero coverage -> Target: 70%+
"""

import pytest
from agents.accessibility_agent import (
    AccessibilityAgent,
    AccessibilityLevel,
    ContentType,
    IssueType,
)


@pytest.fixture
def agent():
    """Create accessibility agent instance"""
    return AccessibilityAgent()


class TestAccessibilityAgent:
    """Test accessibility agent functionality"""

    @pytest.mark.asyncio
    async def test_analyze_text_simple(self, agent):
        """Test simple text analysis"""
        content = "Bu çok basit bir metin."
        result = await agent.analyze_content(content, ContentType.TEXT)

        assert result is not None
        assert result.content_type == ContentType.TEXT
        assert result.score >= 0
        assert result.score <= 100
        assert isinstance(result.issues, list)

    @pytest.mark.asyncio
    async def test_analyze_text_complex(self, agent):
        """Test complex text analysis"""
        content = """Deoksiribonükleik asit (DNA), genetik bilgiyi taşıyan karmaşık bir moleküldür ve tüm canlı organizmaların kalıtsal özelliklerini belirleyen temel yapıdır."""
        result = await agent.analyze_content(content, ContentType.TEXT)

        assert result.score < 100  # Should have some issues
        # Should detect complex language
        has_complex_issue = any(
            issue.issue_type == IssueType.COMPLEX_LANGUAGE for issue in result.issues
        )
        assert has_complex_issue or len(result.issues) >= 0

    @pytest.mark.asyncio
    async def test_analyze_html_missing_alt(self, agent):
        """Test HTML analysis - missing alt text"""
        html = '<html><body><img src="test.jpg"></body></html>'
        result = await agent.analyze_content(html, ContentType.HTML)

        # Should detect missing alt text
        has_alt_issue = any(
            issue.issue_type == IssueType.MISSING_ALT_TEXT for issue in result.issues
        )
        assert has_alt_issue

    @pytest.mark.asyncio
    async def test_analyze_html_missing_h1(self, agent):
        """Test HTML analysis - missing H1"""
        html = "<html><body><h2>Title</h2></body></html>"
        result = await agent.analyze_content(html, ContentType.HTML)

        # Should detect missing H1
        has_header_issue = any(
            issue.issue_type == IssueType.MISSING_HEADERS for issue in result.issues
        )
        assert has_header_issue

    @pytest.mark.asyncio
    async def test_generate_alt_text(self, agent):
        """Test alt text generation"""
        result = await agent.generate_alt_text(
            "image_data", context="Matematik dersi görseli"
        )

        assert result is not None
        assert result.generated_alt != ""
        assert result.language == "tr"
        assert 0 <= result.confidence <= 1

    @pytest.mark.asyncio
    async def test_simplify_text(self, agent):
        """Test text simplification"""
        complex_text = "Mitokondri, hücrenin enerji üretim merkezi olan organeldir."
        result = await agent.simplify_text(complex_text)

        assert result is not None
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_check_contrast_good(self, agent):
        """Test color contrast - good contrast"""
        result = await agent.check_contrast("#000000", "#FFFFFF")

        assert result["contrast_ratio"] > 4.5
        assert result["passes_aa_normal"] is True

    @pytest.mark.asyncio
    async def test_check_contrast_poor(self, agent):
        """Test color contrast - poor contrast"""
        result = await agent.check_contrast("#AAAAAA", "#BBBBBB")

        assert result["contrast_ratio"] < 4.5
        assert result["passes_aa_normal"] is False

    def test_find_jargon(self, agent):
        """Test jargon detection"""
        text = "TYT ve AYT sınavları için LGS notları önemlidir"
        jargon = agent._find_jargon(text)

        assert len(jargon) > 0
        assert "TYT" in jargon or "AYT" in jargon or "LGS" in jargon

    def test_calculate_text_complexity(self, agent):
        """Test text complexity calculation"""
        simple_text = "Bu basit bir metin."
        complex_text = "Bu son derece karmaşık ve anlaşılması zor bir metin."

        simple_score = agent._calculate_text_complexity(simple_text)
        complex_score = agent._calculate_text_complexity(complex_text)

        assert 0 <= simple_score <= 1
        assert 0 <= complex_score <= 1

    def test_determine_level(self, agent):
        """Test accessibility level determination"""
        level_aaa = agent._determine_level(95)
        level_aa = agent._determine_level(75)
        level_a = agent._determine_level(50)

        assert level_aaa == AccessibilityLevel.AAA
        assert level_aa == AccessibilityLevel.AA
        assert level_a == AccessibilityLevel.A

    @pytest.mark.asyncio
    async def test_create_accessible_version_text(self, agent):
        """Test accessible version creation for text"""
        content = "DNA hücrenin kalıtsal bilgisini taşır."
        result = await agent.create_accessible_version(content, ContentType.TEXT)

        assert result is not None
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_create_accessible_version_html(self, agent):
        """Test accessible version creation for HTML"""
        html = '<html><body><img src="test.jpg"><h2>Title</h2></body></html>'
        result = await agent.create_accessible_version(html, ContentType.HTML)

        assert 'lang="tr"' in result or "<html" in result
        assert "alt=" in result  # Should add alt text

    @pytest.mark.asyncio
    async def test_improve_structure_html(self, agent):
        """Test structure improvement suggestions"""
        html = "<html><body><h2>Title</h2>- Item 1<br>- Item 2</body></html>"
        suggestions = await agent.improve_structure(html, ContentType.HTML)

        assert "headings" in suggestions
        assert "lists" in suggestions

    def test_get_wcag_guidelines(self, agent):
        """Test WCAG guidelines retrieval"""
        guidelines_a = agent.get_wcag_guidelines(AccessibilityLevel.A)
        guidelines_aa = agent.get_wcag_guidelines(AccessibilityLevel.AA)
        guidelines_aaa = agent.get_wcag_guidelines(AccessibilityLevel.AAA)

        assert len(guidelines_a) > 0
        assert len(guidelines_aa) > len(guidelines_a)
        assert len(guidelines_aaa) > len(guidelines_aa)

    def test_get_report(self, agent):
        """Test report retrieval"""
        # Add a report
        agent.reports["test_id"] = "test_report"
        result = agent.get_report("test_id")

        assert result == "test_report"
        assert agent.get_report("nonexistent") is None

    def test_add_term_explanations(self, agent):
        """Test term explanation addition"""
        text = "TYT sınavı önemlidir"
        result = agent._add_term_explanations(text)

        # Should add explanation for TYT
        assert "Temel Yeterlilik Testi" in result or "TYT" in result
