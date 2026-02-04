"""
Elasticsearch Client Test Dosyası
Türkçe text analyzer ve indeksleme sistemi testleri
"""

from unittest.mock import AsyncMock, patch

import pytest
from core.elasticsearch_client import (
    ElasticsearchClient,
    ElasticsearchConfig,
    SearchResponse,
    SearchResult,
    elasticsearch_client,
    get_elasticsearch_client,
)


class TestElasticsearchConfig:
    """ElasticsearchConfig model testleri"""

    def test_default_config(self):
        """Varsayılan konfigürasyon testi"""
        config = ElasticsearchConfig()

        assert config.host == "localhost"
        assert config.port == 9200
        assert config.username is None
        assert config.password is None
        assert config.use_ssl is False
        assert config.verify_certs is False
        assert config.ca_certs is None
        assert config.timeout == 30
        assert config.max_retries == 3

    def test_custom_config(self):
        """Özel konfigürasyon testi"""
        config = ElasticsearchConfig(
            host="elasticsearch.example.com",
            port=9201,
            username="test_user",
            password="test_pass",
            use_ssl=True,
            verify_certs=True,
            timeout=60,
        )

        assert config.host == "elasticsearch.example.com"
        assert config.port == 9201
        assert config.username == "test_user"
        assert config.password == "test_pass"
        assert config.use_ssl is True
        assert config.verify_certs is True
        assert config.timeout == 60


class TestSearchModels:
    """Search model testleri"""

    def test_search_result_model(self):
        """SearchResult model testi"""
        result = SearchResult(
            id="test_id",
            score=0.95,
            source={"title": "Test Document", "content": "Test content"},
            highlight={"title": ["<mark>Test</mark> Document"]},
        )

        assert result.id == "test_id"
        assert result.score == 0.95
        assert result.source["title"] == "Test Document"
        assert result.highlight["title"][0] == "<mark>Test</mark> Document"

    def test_search_response_model(self):
        """SearchResponse model testi"""
        results = [
            SearchResult(id="1", score=0.95, source={"title": "Doc 1"}),
            SearchResult(id="2", score=0.85, source={"title": "Doc 2"}),
        ]

        response = SearchResponse(
            total=2, max_score=0.95, results=results, took=15, timed_out=False
        )

        assert response.total == 2
        assert response.max_score == 0.95
        assert len(response.results) == 2
        assert response.took == 15
        assert response.timed_out is False


class TestElasticsearchClient:
    """ElasticsearchClient testleri"""

    @pytest.fixture
    def client(self):
        """Test client fixture"""
        config = ElasticsearchConfig(host="localhost", port=9200)
        return ElasticsearchClient(config)

    @pytest.fixture
    def mock_es_client(self):
        """Mock Elasticsearch client"""
        mock_client = AsyncMock()
        mock_client.cluster.health.return_value = {"cluster_name": "test_cluster"}
        mock_client.indices.exists.return_value = False
        mock_client.indices.create.return_value = {"acknowledged": True}
        mock_client.indices.delete.return_value = {"acknowledged": True}
        mock_client.indices.stats.return_value = {
            "indices": {"test_index": {"total": {"docs": {"count": 100}}}}
        }
        return mock_client

    def test_client_initialization(self, client):
        """Client başlatma testi"""
        assert client.config.host == "localhost"
        assert client.config.port == 9200
        assert client.client is None
        assert client._is_connected is False
        assert (
            "turkish_analyzer"
            in client.turkish_analyzer_settings["analysis"]["analyzer"]
        )

    def test_turkish_analyzer_settings(self, client):
        """Türkçe analyzer ayarları testi"""
        settings = client.turkish_analyzer_settings

        # Analyzer varlığı
        assert "turkish_analyzer" in settings["analysis"]["analyzer"]
        assert "turkish_search_analyzer" in settings["analysis"]["analyzer"]

        # Filter varlığı
        assert "turkish_stop" in settings["analysis"]["filter"]
        assert "turkish_stemmer" in settings["analysis"]["filter"]

        # Türkçe stop words
        stop_words = settings["analysis"]["filter"]["turkish_stop"]["stopwords"]
        assert "bir" in stop_words
        assert "bu" in stop_words
        assert "ve" in stop_words
        assert "için" in stop_words

    @pytest.mark.asyncio
    async def test_connect_success(self, client, mock_es_client):
        """Başarılı bağlantı testi"""
        with patch(
            "backend.core.elasticsearch_client.AsyncElasticsearch",
            return_value=mock_es_client,
        ):
            result = await client.connect()

            assert result is True
            assert client._is_connected is True
            assert client.client is not None
            mock_es_client.cluster.health.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_failure(self, client):
        """Başarısız bağlantı testi"""
        with patch("backend.core.elasticsearch_client.AsyncElasticsearch") as mock_es:
            mock_es.side_effect = Exception("Connection failed")

            result = await client.connect()

            assert result is False
            assert client._is_connected is False

    @pytest.mark.asyncio
    async def test_disconnect(self, client, mock_es_client):
        """Bağlantı kapatma testi"""
        client.client = mock_es_client
        client._is_connected = True

        await client.disconnect()

        assert client._is_connected is False
        mock_es_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_index_success(self, client, mock_es_client):
        """İndeks oluşturma başarı testi"""
        client.client = mock_es_client

        mapping = {
            "properties": {
                "title": {"type": "text", "analyzer": "turkish_analyzer"},
                "content": {"type": "text", "analyzer": "turkish_analyzer"},
            }
        }

        result = await client.create_index("test_index", mapping)

        assert result is True
        mock_es_client.indices.create.assert_called_once()

        # Call arguments kontrolü
        call_args = mock_es_client.indices.create.call_args
        assert call_args[1]["index"] == "test_index"
        assert "settings" in call_args[1]["body"]
        assert "mappings" in call_args[1]["body"]

    @pytest.mark.asyncio
    async def test_create_index_existing(self, client, mock_es_client):
        """Mevcut indeks üzerine yazma testi"""
        client.client = mock_es_client
        mock_es_client.indices.exists.return_value = True

        mapping = {"properties": {"title": {"type": "text"}}}

        result = await client.create_index("existing_index", mapping)

        assert result is True
        mock_es_client.indices.delete.assert_called_once_with(index="existing_index")
        mock_es_client.indices.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_index_failure(self, client, mock_es_client):
        """İndeks oluşturma hata testi"""
        client.client = mock_es_client
        mock_es_client.indices.create.side_effect = Exception("Index creation failed")

        mapping = {"properties": {"title": {"type": "text"}}}

        result = await client.create_index("test_index", mapping)

        assert result is False

    @pytest.mark.asyncio
    async def test_index_document_success(self, client, mock_es_client):
        """Doküman indeksleme başarı testi"""
        client.client = mock_es_client
        mock_es_client.index.return_value = {"_id": "test_doc_id"}

        document = {
            "title": "Test Başlık",
            "content": "Test içerik",
            "category": "test",
        }

        result = await client.index_document("test_index", document, "custom_id")

        assert result is True
        mock_es_client.index.assert_called_once()

        # Call arguments kontrolü
        call_args = mock_es_client.index.call_args
        assert call_args[1]["index"] == "test_index"
        assert call_args[1]["id"] == "custom_id"
        assert "indexed_at" in call_args[1]["body"]

    @pytest.mark.asyncio
    async def test_index_document_failure(self, client, mock_es_client):
        """Doküman indeksleme hata testi"""
        client.client = mock_es_client
        mock_es_client.index.side_effect = Exception("Indexing failed")

        document = {"title": "Test"}

        result = await client.index_document("test_index", document)

        assert result is False

    @pytest.mark.asyncio
    async def test_bulk_index_success(self, client, mock_es_client):
        """Toplu indeksleme başarı testi"""
        client.client = mock_es_client
        mock_es_client.bulk.return_value = {
            "items": [
                {"index": {"status": 201}},
                {"index": {"status": 200}},
                {"index": {"status": 400}},
            ]
        }

        documents = [
            {"title": "Doc 1", "id": "1"},
            {"title": "Doc 2", "id": "2"},
            {"title": "Doc 3", "id": "3"},
        ]

        result = await client.bulk_index("test_index", documents, "id")

        assert result["success"] == 2
        assert result["errors"] == 1
        assert result["total"] == 3
        mock_es_client.bulk.assert_called_once()

    @pytest.mark.asyncio
    async def test_bulk_index_failure(self, client, mock_es_client):
        """Toplu indeksleme hata testi"""
        client.client = mock_es_client
        mock_es_client.bulk.side_effect = Exception("Bulk indexing failed")

        documents = [{"title": "Doc 1"}]

        result = await client.bulk_index("test_index", documents)

        assert result["success"] == 0
        assert result["errors"] == 1
        assert result["total"] == 1

    @pytest.mark.asyncio
    async def test_search_success(self, client, mock_es_client):
        """Arama başarı testi"""
        client.client = mock_es_client
        mock_es_client.search.return_value = {
            "took": 15,
            "timed_out": False,
            "hits": {
                "total": {"value": 2},
                "max_score": 0.95,
                "hits": [
                    {
                        "_id": "1",
                        "_score": 0.95,
                        "_source": {"title": "Test Doc 1"},
                        "highlight": {"title": ["<mark>Test</mark> Doc 1"]},
                    },
                    {"_id": "2", "_score": 0.85, "_source": {"title": "Test Doc 2"}},
                ],
            },
        }

        query = {"match": {"title": "test"}}

        result = await client.search("test_index", query, size=10)

        assert isinstance(result, SearchResponse)
        assert result.total == 2
        assert result.max_score == 0.95
        assert len(result.results) == 2
        assert result.took == 15
        assert result.timed_out is False

        # İlk sonuç kontrolü
        first_result = result.results[0]
        assert first_result.id == "1"
        assert first_result.score == 0.95
        assert first_result.source["title"] == "Test Doc 1"
        assert first_result.highlight["title"][0] == "<mark>Test</mark> Doc 1"

    @pytest.mark.asyncio
    async def test_search_failure(self, client, mock_es_client):
        """Arama hata testi"""
        client.client = mock_es_client
        mock_es_client.search.side_effect = Exception("Search failed")

        query = {"match": {"title": "test"}}

        result = await client.search("test_index", query)

        assert isinstance(result, SearchResponse)
        assert result.total == 0
        assert result.max_score is None
        assert len(result.results) == 0

    @pytest.mark.asyncio
    async def test_turkish_full_text_search(self, client, mock_es_client):
        """Türkçe full-text arama testi"""
        client.client = mock_es_client
        mock_es_client.search.return_value = {
            "took": 20,
            "timed_out": False,
            "hits": {
                "total": {"value": 1},
                "max_score": 0.9,
                "hits": [
                    {
                        "_id": "1",
                        "_score": 0.9,
                        "_source": {"title": "Türkçe Test", "content": "İçerik"},
                        "highlight": {"title": ["<mark>Türkçe</mark> Test"]},
                    }
                ],
            },
        }

        result = await client.turkish_full_text_search(
            "test_index",
            "Türkçe",
            ["title", "content"],
            size=5,
            filters={"category": "education"},
        )

        assert isinstance(result, SearchResponse)
        assert result.total == 1

        # Search call kontrolü
        call_args = mock_es_client.search.call_args
        query = call_args[1]["body"]["query"]

        # Bool query kontrolü
        assert "bool" in query
        assert "must" in query["bool"]
        assert "filter" in query["bool"]

        # Multi-match query kontrolü
        multi_match = query["bool"]["must"][0]["multi_match"]
        assert multi_match["query"] == "Türkçe"
        assert multi_match["analyzer"] == "turkish_analyzer"
        assert "title" in multi_match["fields"]
        assert "content" in multi_match["fields"]

        # Filter kontrolü
        filter_term = query["bool"]["filter"][0]["term"]
        assert filter_term["category"] == "education"

    @pytest.mark.asyncio
    async def test_get_document_success(self, client, mock_es_client):
        """Doküman getirme başarı testi"""
        client.client = mock_es_client
        mock_es_client.get.return_value = {
            "_source": {"title": "Test Doc", "content": "Test content"}
        }

        result = await client.get_document("test_index", "test_id")

        assert result is not None
        assert result["title"] == "Test Doc"
        assert result["content"] == "Test content"
        mock_es_client.get.assert_called_once_with(index="test_index", id="test_id")

    @pytest.mark.asyncio
    async def test_get_document_not_found(self, client, mock_es_client):
        """Doküman bulunamama testi"""
        from elasticsearch.exceptions import NotFoundError

        client.client = mock_es_client
        mock_es_client.get.side_effect = NotFoundError("Document not found")

        result = await client.get_document("test_index", "nonexistent_id")

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_document_success(self, client, mock_es_client):
        """Doküman silme başarı testi"""
        client.client = mock_es_client
        mock_es_client.delete.return_value = {"result": "deleted"}

        result = await client.delete_document("test_index", "test_id")

        assert result is True
        mock_es_client.delete.assert_called_once_with(
            index="test_index", id="test_id", refresh=True
        )

    @pytest.mark.asyncio
    async def test_delete_document_not_found(self, client, mock_es_client):
        """Doküman silme - bulunamama testi"""
        from elasticsearch.exceptions import NotFoundError

        client.client = mock_es_client
        mock_es_client.delete.side_effect = NotFoundError("Document not found")

        result = await client.delete_document("test_index", "nonexistent_id")

        assert result is False

    @pytest.mark.asyncio
    async def test_update_document_success(self, client, mock_es_client):
        """Doküman güncelleme başarı testi"""
        client.client = mock_es_client
        mock_es_client.update.return_value = {"result": "updated"}

        updates = {"title": "Updated Title", "status": "active"}

        result = await client.update_document("test_index", "test_id", updates)

        assert result is True
        mock_es_client.update.assert_called_once()

        # Call arguments kontrolü
        call_args = mock_es_client.update.call_args
        assert call_args[1]["index"] == "test_index"
        assert call_args[1]["id"] == "test_id"
        assert "updated_at" in call_args[1]["body"]["doc"]
        assert call_args[1]["body"]["doc"]["title"] == "Updated Title"

    @pytest.mark.asyncio
    async def test_update_document_failure(self, client, mock_es_client):
        """Doküman güncelleme hata testi"""
        client.client = mock_es_client
        mock_es_client.update.side_effect = Exception("Update failed")

        updates = {"title": "Updated Title"}

        result = await client.update_document("test_index", "test_id", updates)

        assert result is False

    @pytest.mark.asyncio
    async def test_get_index_stats_success(self, client, mock_es_client):
        """İndeks istatistik başarı testi"""
        client.client = mock_es_client

        result = await client.get_index_stats("test_index")

        assert result is not None
        assert "total" in result
        mock_es_client.indices.stats.assert_called_once_with(index="test_index")

    @pytest.mark.asyncio
    async def test_get_index_stats_failure(self, client, mock_es_client):
        """İndeks istatistik hata testi"""
        client.client = mock_es_client
        mock_es_client.indices.stats.side_effect = Exception("Stats failed")

        result = await client.get_index_stats("test_index")

        assert result is None

    def test_is_connected_property(self, client):
        """Bağlantı durumu property testi"""
        assert client.is_connected is False

        client._is_connected = True
        assert client.is_connected is True

    @pytest.mark.asyncio
    async def test_client_not_connected_error(self, client):
        """Client bağlı değilken hata testi"""
        # Client bağlı değil
        client.client = None

        # Çeşitli operasyonlar hata vermeli
        result = await client.index_document("test", {})
        assert result is False

        result = await client.search("test", {})
        assert result.total == 0

        result = await client.get_document("test", "1")
        assert result is None


class TestGlobalFunctions:
    """Global fonksiyon testleri"""

    @pytest.mark.asyncio
    async def test_get_elasticsearch_client_connected(self):
        """Bağlı client alma testi"""
        with patch.object(elasticsearch_client, "is_connected", True):
            client = await get_elasticsearch_client()
            assert client is elasticsearch_client

    @pytest.mark.asyncio
    async def test_get_elasticsearch_client_not_connected(self):
        """Bağlı olmayan client alma testi"""
        with patch.object(elasticsearch_client, "is_connected", False), patch.object(
            elasticsearch_client, "connect", return_value=True
        ) as mock_connect:
            client = await get_elasticsearch_client()

            assert client is elasticsearch_client
            mock_connect.assert_called_once()


class TestTurkishLanguageSupport:
    """Türkçe dil desteği testleri"""

    @pytest.fixture
    def client(self):
        return ElasticsearchClient()

    def test_turkish_stop_words(self, client):
        """Türkçe stop words testi"""
        stop_words = client.turkish_analyzer_settings["analysis"]["filter"][
            "turkish_stop"
        ]["stopwords"]

        # Temel Türkçe stop words kontrolü
        expected_stop_words = [
            "bir",
            "bu",
            "da",
            "de",
            "den",
            "dır",
            "dir",
            "için",
            "ile",
            "ise",
            "ki",
            "mi",
            "mu",
            "mü",
            "ne",
            "olan",
            "olarak",
            "şu",
            "ve",
            "veya",
            "ya",
        ]

        for word in expected_stop_words:
            assert word in stop_words

    def test_turkish_analyzer_configuration(self, client):
        """Türkçe analyzer konfigürasyon testi"""
        analyzer = client.turkish_analyzer_settings["analysis"]["analyzer"][
            "turkish_analyzer"
        ]

        assert analyzer["type"] == "custom"
        assert analyzer["tokenizer"] == "standard"

        expected_filters = [
            "lowercase",
            "turkish_stop",
            "turkish_stemmer",
            "asciifolding",
        ]
        for filter_name in expected_filters:
            assert filter_name in analyzer["filter"]

    def test_turkish_search_analyzer_configuration(self, client):
        """Türkçe search analyzer konfigürasyon testi"""
        analyzer = client.turkish_analyzer_settings["analysis"]["analyzer"][
            "turkish_search_analyzer"
        ]

        assert analyzer["type"] == "custom"
        assert analyzer["tokenizer"] == "standard"

        expected_filters = ["lowercase", "turkish_stop", "asciifolding"]
        for filter_name in expected_filters:
            assert filter_name in analyzer["filter"]

        # Search analyzer'da stemmer olmamalı
        assert "turkish_stemmer" not in analyzer["filter"]

    def test_turkish_stemmer_configuration(self, client):
        """Türkçe stemmer konfigürasyon testi"""
        stemmer = client.turkish_analyzer_settings["analysis"]["filter"][
            "turkish_stemmer"
        ]

        assert stemmer["type"] == "stemmer"
        assert stemmer["language"] == "turkish"


class TestErrorHandling:
    """Hata yönetimi testleri"""

    @pytest.fixture
    def client(self):
        return ElasticsearchClient()

    @pytest.mark.asyncio
    async def test_connection_error_handling(self, client):
        """Bağlantı hatası yönetimi testi"""
        from elasticsearch.exceptions import ConnectionError

        with patch("backend.core.elasticsearch_client.AsyncElasticsearch") as mock_es:
            mock_es.side_effect = ConnectionError("Connection failed")

            result = await client.connect()

            assert result is False
            assert client._is_connected is False

    @pytest.mark.asyncio
    async def test_request_error_handling(self, client):
        """İstek hatası yönetimi testi"""
        from elasticsearch.exceptions import RequestError

        mock_es_client = AsyncMock()
        mock_es_client.indices.create.side_effect = RequestError("Invalid request")
        client.client = mock_es_client

        result = await client.create_index("test", {})

        assert result is False

    @pytest.mark.asyncio
    async def test_timeout_handling(self, client):
        """Timeout hatası yönetimi testi"""
        import asyncio

        mock_es_client = AsyncMock()
        mock_es_client.search.side_effect = asyncio.TimeoutError("Request timeout")
        client.client = mock_es_client

        result = await client.search("test", {})

        assert isinstance(result, SearchResponse)
        assert result.total == 0


class TestIntegrationScenarios:
    """Entegrasyon senaryoları testleri"""

    @pytest.fixture
    def client(self):
        return ElasticsearchClient()

    @pytest.mark.asyncio
    async def test_educational_content_indexing_scenario(self, client):
        """Eğitim içeriği indeksleme senaryosu"""
        mock_es_client = AsyncMock()
        mock_es_client.cluster.health.return_value = {"cluster_name": "test"}
        mock_es_client.indices.exists.return_value = False
        mock_es_client.indices.create.return_value = {"acknowledged": True}
        mock_es_client.bulk.return_value = {
            "items": [{"index": {"status": 201}}, {"index": {"status": 201}}]
        }

        client.client = mock_es_client
        client._is_connected = True

        # Eğitim içeriği mapping
        mapping = {
            "properties": {
                "title": {"type": "text", "analyzer": "turkish_analyzer"},
                "content": {"type": "text", "analyzer": "turkish_analyzer"},
                "subject": {"type": "keyword"},
                "grade_level": {"type": "integer"},
                "difficulty": {"type": "keyword"},
                "tags": {"type": "keyword"},
            }
        }

        # İndeks oluştur
        index_result = await client.create_index("educational_content", mapping)
        assert index_result is True

        # Eğitim içerikleri
        documents = [
            {
                "title": "Matematik - Türev Konusu",
                "content": "Türev, bir fonksiyonun değişim hızını gösteren matematiksel kavramdır.",
                "subject": "matematik",
                "grade_level": 12,
                "difficulty": "orta",
                "tags": ["türev", "matematik", "analiz"],
            },
            {
                "title": "Türkçe - Cümle Çözümlemesi",
                "content": "Cümle çözümlemesi, cümlenin öğelerini belirleme işlemidir.",
                "subject": "turkce",
                "grade_level": 10,
                "difficulty": "kolay",
                "tags": ["cümle", "türkçe", "gramer"],
            },
        ]

        # Toplu indeksleme
        bulk_result = await client.bulk_index("educational_content", documents)
        assert bulk_result["success"] == 2
        assert bulk_result["errors"] == 0

    @pytest.mark.asyncio
    async def test_turkish_search_scenario(self, client):
        """Türkçe arama senaryosu"""
        mock_es_client = AsyncMock()
        mock_es_client.search.return_value = {
            "took": 25,
            "timed_out": False,
            "hits": {
                "total": {"value": 3},
                "max_score": 0.95,
                "hits": [
                    {
                        "_id": "1",
                        "_score": 0.95,
                        "_source": {
                            "title": "Matematik Türev Konusu",
                            "content": "Türev hesaplama yöntemleri",
                            "subject": "matematik",
                        },
                        "highlight": {
                            "title": ["<mark>Matematik</mark> Türev Konusu"],
                            "content": ["<mark>Türev</mark> hesaplama yöntemleri"],
                        },
                    },
                    {
                        "_id": "2",
                        "_score": 0.85,
                        "_source": {
                            "title": "Geometri Temel Kavramlar",
                            "content": "Matematik geometri konuları",
                            "subject": "matematik",
                        },
                        "highlight": {
                            "content": ["<mark>Matematik</mark> geometri konuları"]
                        },
                    },
                    {
                        "_id": "3",
                        "_score": 0.75,
                        "_source": {
                            "title": "Fizik Matematik İlişkisi",
                            "content": "Fizik problemlerinde matematik kullanımı",
                            "subject": "fizik",
                        },
                    },
                ],
            },
        }

        client.client = mock_es_client
        client._is_connected = True

        # Türkçe arama
        result = await client.turkish_full_text_search(
            index_name="educational_content",
            query_text="matematik türev",
            fields=["title^2", "content"],
            size=10,
            filters={"subject": ["matematik", "fizik"]},
        )

        assert isinstance(result, SearchResponse)
        assert result.total == 3
        assert result.max_score == 0.95
        assert len(result.results) == 3

        # İlk sonuç kontrolü
        first_result = result.results[0]
        assert first_result.id == "1"
        assert first_result.score == 0.95
        assert "Matematik" in first_result.source["title"]
        assert first_result.highlight is not None
        assert "title" in first_result.highlight
        assert "content" in first_result.highlight


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
