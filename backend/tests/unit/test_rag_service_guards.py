"""
RAGService başlatılmamış-durum bekçileri.

`RAGService._initialize()` TESTING=true iken erken döner ve `_initialize()`
içindeki `except` dalları da `vector_store`'u None bırakabilir. Yani
`embeddings` / `vector_store` / `text_splitter` None hâli GERÇEKTEN
ulaşılabilir bir durumdur, teorik değil.

Bu dosya iki şeyi çivilemek için var:
  1. Başlatılmamış serviste hata sebebi LOG'DA NET olmalı — bugünkü
     kriptik `'NoneType' object has no attribute ...` yerine.
  2. `add_documents`'ın `vector_store is None` → lazy-init yolu
     KIRILMAMALI (oraya blanket guard koymak onu bozar).

Dış sözleşme (search → [], add_documents → {"success": False}) bilinçli
olarak DEĞİŞMİYOR; geniş `except Exception` dalları guard'ı yutar.
"""

from unittest.mock import MagicMock, patch

import pytest

from core.rag_service import RAGService


@pytest.fixture
def uninitialized_service(monkeypatch):
    """TESTING=true → _initialize() erken döner, üç bileşen de None kalır."""
    monkeypatch.setenv("TESTING", "true")
    service = RAGService(persist_directory="./test_vector_db_guards")
    # Fixture'ın gerçekten başlatılmamış bir servis ürettiğini doğrula,
    # yoksa aşağıdaki testler yanlış şeyi ölçer.
    assert service.vector_store is None
    assert service.embeddings is None
    assert service.text_splitter is None
    return service


class TestRequireReady:
    def test_require_ready_raises_when_uninitialized(self, uninitialized_service):
        """Başlatılmamış serviste guard net bir RuntimeError üretmeli."""
        with pytest.raises(RuntimeError) as exc_info:
            uninitialized_service._require_ready()

        mesaj = str(exc_info.value)
        assert "RAGService" in mesaj
        assert "başlatılmadı" in mesaj

    def test_require_ready_passes_when_initialized(self, uninitialized_service):
        """Bileşenler doluyken guard geçmeli (yanlış-pozitif olmamalı) ve
        daraltılmış (vector_store, embeddings) ikilisini döndürmeli."""
        sahte_store = MagicMock()
        sahte_embeddings = MagicMock()
        uninitialized_service.vector_store = sahte_store
        uninitialized_service.embeddings = sahte_embeddings

        store, embeddings = uninitialized_service._require_ready()

        assert store is sahte_store
        assert embeddings is sahte_embeddings


class TestSearchDiagnostics:
    @pytest.mark.asyncio
    async def test_search_logs_clear_reason_not_nonetype(
        self, uninitialized_service, caplog
    ):
        """
        Bugün log'da `'NoneType' object has no attribute 'similarity_search'`
        yazıyor — sebebi göstermiyor. Guard sonrası sebep net olmalı.
        """
        with caplog.at_level("ERROR"):
            await uninitialized_service.search("fotosentez nedir")

        assert "başlatılmadı" in caplog.text
        assert "NoneType" not in caplog.text

    @pytest.mark.asyncio
    async def test_search_still_returns_empty_list(self, uninitialized_service):
        """Dış sözleşme korunmalı: guard eklenince de [] dönmeli, patlamamalı."""
        sonuc = await uninitialized_service.search("fotosentez nedir")

        assert sonuc == []

    @pytest.mark.asyncio
    async def test_hybrid_search_logs_clear_reason(self, uninitialized_service, caplog):
        with caplog.at_level("ERROR"):
            sonuc = await uninitialized_service.hybrid_search("mitokondri")

        assert sonuc == []
        assert "başlatılmadı" in caplog.text


class TestLazyInitNotBroken:
    """
    TUZAK REGRESYON BEKÇİSİ.

    `add_documents` satır ~378'de `vector_store is None` durumunu KASITLI
    olarak lazy-init için kullanıyor. Metot başına `_require_ready()`
    koymak bu yolu kırar. Bu test o hatayı yakalar.
    """

    @pytest.mark.asyncio
    async def test_add_documents_lazily_creates_vector_store(
        self, uninitialized_service
    ):
        # text_splitter yolunu atlamak için kısa içerik (<1000 karakter)
        uninitialized_service.embeddings = MagicMock()
        sahte_store = MagicMock()
        sahte_store.add_documents.return_value = ["doc-1"]

        with patch(
            "core.vector_store_factory.VectorStoreFactory.create_optimized_store",
            return_value=sahte_store,
        ) as sahte_factory:
            sonuc = await uninitialized_service.add_documents(
                documents=[{"content": "Mitokondri enerji üretir.", "metadata": {}}]
            )

        assert sahte_factory.called, "lazy-init yolu kırıldı: factory hiç çağrılmadı"
        assert sonuc["success"] is True
        assert sonuc["document_ids"] == ["doc-1"]

    @pytest.mark.asyncio
    async def test_add_documents_long_text_reports_clear_reason(
        self, uninitialized_service, caplog
    ):
        """
        >1000 karakter içerik `text_splitter`'a gider. text_splitter None
        iken sebep net olmalı.
        """
        uninitialized_service.embeddings = MagicMock()
        uzun_metin = "Mitokondri hücrenin enerji üretim merkezidir. " * 40

        with caplog.at_level("ERROR"):
            sonuc = await uninitialized_service.add_documents(
                documents=[{"content": uzun_metin, "metadata": {}}]
            )

        assert sonuc["success"] is False
        assert "başlatılmadı" in sonuc["error"]
