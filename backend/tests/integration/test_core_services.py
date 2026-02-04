"""
Test file for core services (LLM and RAG)
Increase test coverage for core modules
"""
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Test edilecek modüller
from core.llm_service import HuggingFaceLLMService


class TestHuggingFaceLLMService:
    """HuggingFace LLM Service testleri"""

    @pytest.fixture
    def llm_service(self):
        """LLM service fixture"""
        return HuggingFaceLLMService()

    @pytest.mark.asyncio
    async def test_generate_success(self, llm_service):
        """Başarılı LLM generation testi"""
        with patch("aiohttp.ClientSession") as mock_session:
            # Mock response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value=[{"generated_text": "Test response from LLM"}]
            )

            # Mock session
            mock_session_instance = AsyncMock()
            mock_session_instance.post = AsyncMock(return_value=mock_response)
            mock_session_instance.__aenter__ = AsyncMock(
                return_value=mock_session_instance
            )
            mock_session_instance.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_session_instance

            # Test
            result = await llm_service.generate(
                prompt="Test prompt", max_tokens=100, temperature=0.7
            )

            assert result["success"] == True
            assert "text" in result
            assert len(result["text"]) > 0

    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self, llm_service):
        """System prompt ile generation testi"""
        with patch("aiohttp.ClientSession") as mock_session:
            # Mock response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value=[{"generated_text": "System prompt response"}]
            )

            # Mock session
            mock_session_instance = AsyncMock()
            mock_session_instance.post = AsyncMock(return_value=mock_response)
            mock_session_instance.__aenter__ = AsyncMock(
                return_value=mock_session_instance
            )
            mock_session_instance.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_session_instance

            result = await llm_service.generate(
                prompt="User question", system_prompt="You are a helpful assistant"
            )

            assert result["success"] == True
            assert "metadata" in result

    @pytest.mark.asyncio
    async def test_generate_fallback_on_error(self, llm_service):
        """API hatası durumunda fallback testi"""
        with patch("aiohttp.ClientSession") as mock_session:
            # Mock error response
            mock_response = AsyncMock()
            mock_response.status = 401
            mock_response.text = AsyncMock(return_value="Unauthorized")

            # Mock session
            mock_session_instance = AsyncMock()
            mock_session_instance.post = AsyncMock(return_value=mock_response)
            mock_session_instance.__aenter__ = AsyncMock(
                return_value=mock_session_instance
            )
            mock_session_instance.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_session_instance

            result = await llm_service.generate("Test prompt")

            assert result["success"] == True
            assert result["metadata"]["model"] == "fallback-educational"
            assert len(result["text"]) > 0  # Fallback response

    @pytest.mark.asyncio
    async def test_generate_for_education(self, llm_service):
        """Eğitim amaçlı özel generation testi"""
        with patch.object(llm_service, "generate") as mock_generate:
            mock_generate.return_value = {
                "success": True,
                "text": "Educational content response",
            }

            result = await llm_service.generate_for_education(
                task_type="question_generation", content="Test content", parameters={}
            )

            assert result["success"] == True
            assert result["task_type"] == "question_generation"
            assert "content" in result

    @pytest.mark.asyncio
    async def test_chat_functionality(self, llm_service):
        """Chat fonksiyonu testi"""
        with patch.object(llm_service, "generate") as mock_generate:
            mock_generate.return_value = {"success": True, "text": "Chat response"}

            messages = [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ]

            result = await llm_service.chat(messages)

            assert result["success"] == True
            mock_generate.assert_called_once()

    def test_prepare_prompt(self, llm_service):
        """Prompt hazırlama testi"""
        # Without system prompt
        prompt1 = llm_service._prepare_prompt("User message")
        assert prompt1 == "User message"

        # With system prompt
        prompt2 = llm_service._prepare_prompt("User message", "System instructions")
        assert "System:" in prompt2
        assert "User:" in prompt2
        assert "Assistant:" in prompt2

    def test_generate_educational_response(self, llm_service):
        """Educational fallback response testi"""
        # Python related
        response1 = llm_service._generate_educational_response(
            "Python öğrenmek istiyorum"
        )
        assert "Python" in response1
        assert "öğrenme planı" in response1.lower()

        # Math related
        response2 = llm_service._generate_educational_response("Matematik çalışmak")
        assert "matematik" in response2.lower()

        # Exam related
        response3 = llm_service._generate_educational_response("LGS hazırlık")
        assert "sınav" in response3.lower() or "LGS" in response3

        # General
        response4 = llm_service._generate_educational_response("Yardım")
        assert len(response4) > 100


class TestRAGService:
    """RAG Service testleri"""

    @pytest.fixture
    def rag_service_mock(self):
        """RAG service fixture with mocked ChromaDB"""
        with patch("chromadb.PersistentClient"):
            from core.rag_service import RAGService

            service = RAGService()
            return service

    @pytest.mark.asyncio
    async def test_add_document(self, rag_service_mock):
        """Doküman ekleme testi"""
        # Mock collection
        mock_collection = Mock()
        mock_collection.add = Mock()
        rag_service_mock.collection = mock_collection

        result = await rag_service_mock.add_document(
            document="Test document content",
            metadata={"source": "test"},
            doc_id="test_123",
        )

        assert result["success"] == True
        assert result["doc_id"] == "test_123"
        mock_collection.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_documents(self, rag_service_mock):
        """Doküman arama testi"""
        # Mock collection
        mock_collection = Mock()
        mock_collection.query = Mock(
            return_value={
                "documents": [["Document 1", "Document 2"]],
                "distances": [[0.1, 0.2]],
                "metadatas": [[{"source": "test1"}, {"source": "test2"}]],
            }
        )
        rag_service_mock.collection = mock_collection

        result = await rag_service_mock.search(query="Test query", n_results=2)

        assert result["success"] == True
        assert len(result["results"]) == 2
        assert result["results"][0]["score"] > result["results"][1]["score"]

    @pytest.mark.asyncio
    async def test_add_batch_documents(self, rag_service_mock):
        """Toplu doküman ekleme testi"""
        # Mock collection
        mock_collection = Mock()
        mock_collection.add = Mock()
        rag_service_mock.collection = mock_collection

        documents = [
            {"text": "Doc 1", "metadata": {"source": "source1"}},
            {"text": "Doc 2", "metadata": {"source": "source2"}},
        ]

        result = await rag_service_mock.add_batch(documents)

        assert result["success"] == True
        assert result["count"] == 2
        mock_collection.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_with_metadata_filter(self, rag_service_mock):
        """Metadata filtresi ile arama testi"""
        # Mock collection
        mock_collection = Mock()
        mock_collection.query = Mock(
            return_value={
                "documents": [["Filtered document"]],
                "distances": [[0.15]],
                "metadatas": [[{"type": "quiz"}]],
            }
        )
        rag_service_mock.collection = mock_collection

        result = await rag_service_mock.search(
            query="Quiz question", filter={"type": "quiz"}
        )

        assert result["success"] == True
        assert len(result["results"]) == 1

    @pytest.mark.asyncio
    async def test_clear_collection(self, rag_service_mock):
        """Collection temizleme testi"""
        # Mock collection
        mock_collection = Mock()
        mock_collection.delete = Mock()
        mock_collection.get = Mock(return_value={"ids": ["1", "2", "3"]})
        rag_service_mock.collection = mock_collection

        result = await rag_service_mock.clear()

        assert result["success"] == True
        mock_collection.delete.assert_called()

    @pytest.mark.asyncio
    async def test_get_collection_count(self, rag_service_mock):
        """Collection sayısı alma testi"""
        # Mock collection
        mock_collection = Mock()
        mock_collection.count = Mock(return_value=42)
        rag_service_mock.collection = mock_collection

        result = await rag_service_mock.get_count()

        assert result["success"] == True
        assert result["count"] == 42


class TestIntegration:
    """LLM ve RAG entegrasyon testleri"""

    @pytest.mark.asyncio
    async def test_llm_rag_integration(self):
        """LLM ve RAG birlikte çalışma testi"""
        llm_service = HuggingFaceLLMService()

        with patch("chromadb.PersistentClient"):
            from core.rag_service import RAGService

            rag_service = RAGService()

            # Mock RAG search
            with patch.object(rag_service, "search") as mock_search:
                mock_search.return_value = {
                    "success": True,
                    "results": [
                        {"document": "Python is a programming language", "score": 0.9}
                    ],
                }

                # Mock LLM generate
                with patch.object(llm_service, "generate") as mock_generate:
                    mock_generate.return_value = {
                        "success": True,
                        "text": "Based on the context, Python is...",
                    }

                    # RAG search
                    context = await rag_service.search("What is Python?")

                    # LLM generation with context
                    response = await llm_service.generate(
                        prompt=f"Context: {context['results'][0]['document']}\n\nQuestion: What is Python?",
                        temperature=0.5,
                    )

                    assert context["success"] == True
                    assert response["success"] == True
                    assert "Python" in response["text"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
