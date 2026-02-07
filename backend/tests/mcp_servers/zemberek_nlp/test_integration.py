"""
Integration Tests for Zemberek NLP MCP Server
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


class TestMCPServerIntegration:
    """Integration tests for MCP server"""

    @pytest.mark.asyncio
    async def test_tool_list(self):
        """Test tool list contains all 8 tools"""
        from backend.mcp_servers.zemberek_nlp.models.mcp_protocol import get_tool_list

        tool_list = get_tool_list()

        assert len(tool_list.tools) == 8

        tool_names = [t.name for t in tool_list.tools]
        assert "zemberek_analyze" in tool_names
        assert "zemberek_lemmatize" in tool_names
        assert "zemberek_spell_check" in tool_names
        assert "zemberek_tokenize" in tool_names
        assert "zemberek_ner" in tool_names
        assert "zemberek_segment_sentences" in tool_names
        assert "zemberek_normalize" in tool_names
        assert "zemberek_health" in tool_names

    @pytest.mark.asyncio
    async def test_tool_handlers_mapping(self):
        """Test tool handlers are correctly mapped"""
        from backend.mcp_servers.zemberek_nlp.tools import TOOL_HANDLERS

        assert len(TOOL_HANDLERS) == 8

        # Verify all handlers are classes
        for name, handler_class in TOOL_HANDLERS.items():
            assert hasattr(handler_class, "execute")
            assert hasattr(handler_class, "tool_name")


class TestConfigIntegration:
    """Integration tests for configuration"""

    def test_config_url_generation(self):
        """Test URL generation from config"""
        from backend.mcp_servers.zemberek_nlp.config import ZemberekConfig

        config = ZemberekConfig(
            zemberek_host="localhost",
            zemberek_port=8081,
            redis_host="localhost",
            redis_port=6379,
        )

        assert config.zemberek_url == "http://localhost:8081"
        assert "redis://localhost:6379" in config.redis_url

    def test_config_with_password(self):
        """Test Redis URL with password"""
        from backend.mcp_servers.zemberek_nlp.config import ZemberekConfig

        config = ZemberekConfig(
            redis_host="localhost",
            redis_port=6379,
            redis_password="secret",
        )

        assert ":secret@" in config.redis_url


class TestModelSchemas:
    """Tests for Pydantic model schemas"""

    def test_morphology_result_schema(self):
        """Test MorphologyResult schema"""
        from backend.mcp_servers.zemberek_nlp.models.tool_schemas import MorphologyResult

        result = MorphologyResult(
            text="test",
            word_analyses=[],
            total_words=0,
        )

        assert result.text == "test"
        assert result.cached is False

    def test_ner_result_schema(self):
        """Test NERResult schema"""
        from backend.mcp_servers.zemberek_nlp.models.tool_schemas import NERResult, NamedEntity, EntityType

        entity = NamedEntity(
            text="Istanbul",
            type=EntityType.LOCATION,
            start=0,
            end=8,
        )

        result = NERResult(
            text="Istanbul",
            entities=[entity],
            entity_count=1,
        )

        assert result.entity_count == 1
        assert result.entities[0].type == EntityType.LOCATION

    def test_health_result_schema(self):
        """Test HealthResult schema"""
        from backend.mcp_servers.zemberek_nlp.models.tool_schemas import HealthResult

        result = HealthResult(
            status="healthy",
            zemberek_available=True,
            redis_available=True,
            http_backend_available=True,
            version="1.0.0",
        )

        assert result.status == "healthy"


class TestMCPProtocol:
    """Tests for MCP protocol models"""

    def test_tool_response_success(self):
        """Test successful tool response"""
        from backend.mcp_servers.zemberek_nlp.models.mcp_protocol import MCPToolResponse

        response = MCPToolResponse.success({"result": "data"})

        assert response.isError is False
        assert len(response.content) == 1

    def test_tool_response_error(self):
        """Test error tool response"""
        from backend.mcp_servers.zemberek_nlp.models.mcp_protocol import MCPToolResponse

        response = MCPToolResponse.error("Something went wrong")

        assert response.isError is True
        assert "Error:" in response.content[0].text

    def test_tool_info_schema(self):
        """Test tool info schema"""
        from backend.mcp_servers.zemberek_nlp.models.mcp_protocol import ZEMBEREK_TOOLS

        for tool in ZEMBEREK_TOOLS:
            assert tool.name.startswith("zemberek_")
            assert tool.description
            assert tool.inputSchema is not None


class TestEndToEnd:
    """End-to-end integration tests"""

    @pytest.mark.asyncio
    async def test_full_morphology_pipeline(self):
        """Test full morphology analysis pipeline"""
        from backend.mcp_servers.zemberek_nlp.tools.morphology import MorphologyHandler

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=MagicMock(
            json=lambda: {
                "word": "kitap",
                "analyses": [{"lemma": "kitap", "pos": "Noun", "morphemes": ["kitap"]}],
                "count": 1
            },
            raise_for_status=lambda: None
        ))

        handler = MorphologyHandler(mock_client, None)
        result = await handler.execute(text="kitap okumak")

        # Verify complete pipeline
        assert "text" in result
        assert "word_analyses" in result
        assert "total_words" in result
        assert "cached" in result
        assert "latency_ms" in result

    @pytest.mark.asyncio
    async def test_full_ner_pipeline(self):
        """Test full NER pipeline"""
        from backend.mcp_servers.zemberek_nlp.tools.ner import NERHandler

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=MagicMock(
            json=lambda: {
                "word": "Ahmet",
                "analyses": [{"lemma": "Ahmet", "pos": "Noun,Prop"}],
                "count": 1
            },
            raise_for_status=lambda: None
        ))

        handler = NERHandler(mock_client, None)
        result = await handler.execute(text="Ahmet Istanbul'da")

        # Verify NER output structure
        assert "entities" in result
        assert "entity_count" in result
        assert "person_count" in result
        assert "location_count" in result
        assert "organization_count" in result
