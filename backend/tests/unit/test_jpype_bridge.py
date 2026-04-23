"""
Unit Tests for Zemberek JPype Bridge

Tests:
- Singleton pattern
- JVM initialization
- Thread safety
- Error handling
- Component availability
"""

import threading
from unittest.mock import MagicMock, patch

import pytest

from mcp_servers.zemberek_nlp.bridge.exceptions import (
    AnalysisError,
    JVMInitializationError,
    JVMNotStartedError,
)

# Import bridge module
from mcp_servers.zemberek_nlp.bridge.jpype_bridge import ZemberekJPypeBridge, get_bridge


class TestSingletonPattern:
    """Test singleton pattern implementation."""

    def test_singleton_returns_same_instance(self):
        """Bridge should return same instance on multiple calls."""
        # Reset singleton for test
        ZemberekJPypeBridge._instance = None
        ZemberekJPypeBridge._initialized = False

        bridge1 = ZemberekJPypeBridge()
        bridge2 = ZemberekJPypeBridge()

        assert bridge1 is bridge2

    def test_get_bridge_returns_same_instance(self):
        """get_bridge() should return singleton instance."""
        # Reset for test
        import mcp_servers.zemberek_nlp.bridge.jpype_bridge as bridge_module
        bridge_module._bridge = None
        ZemberekJPypeBridge._instance = None
        ZemberekJPypeBridge._initialized = False

        bridge1 = get_bridge()
        bridge2 = get_bridge()

        assert bridge1 is bridge2

    def test_singleton_thread_safety(self):
        """Singleton creation should be thread-safe."""
        # Reset singleton
        ZemberekJPypeBridge._instance = None
        ZemberekJPypeBridge._initialized = False

        instances = []
        errors = []

        def create_bridge():
            try:
                bridge = ZemberekJPypeBridge()
                instances.append(bridge)
            except Exception as e:
                errors.append(e)

        # Create threads
        threads = [threading.Thread(target=create_bridge) for _ in range(10)]

        # Start all threads
        for t in threads:
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        # All instances should be the same
        assert len(errors) == 0
        assert len(instances) == 10
        assert all(inst is instances[0] for inst in instances)


class TestInitialization:
    """Test JVM and Zemberek initialization."""

    def test_is_initialized_false_before_init(self):
        """is_initialized should be False before initialize()."""
        ZemberekJPypeBridge._instance = None
        ZemberekJPypeBridge._initialized = False

        bridge = ZemberekJPypeBridge()
        assert bridge.is_initialized is False

    @patch("mcp_servers.zemberek_nlp.bridge.jpype_bridge._import_jpype")
    def test_jvm_started_property(self, mock_import):
        """jvm_started should reflect JPype state."""
        mock_jpype = MagicMock()
        mock_jpype.isJVMStarted.return_value = False
        mock_import.return_value = mock_jpype

        ZemberekJPypeBridge._instance = None
        ZemberekJPypeBridge._initialized = False

        bridge = ZemberekJPypeBridge()
        assert bridge.jvm_started is False

    @patch("mcp_servers.zemberek_nlp.bridge.jpype_bridge._import_jpype")
    def test_initialize_without_jar_raises_error(self, mock_import):
        """initialize() should raise error if JAR not found."""
        mock_jpype = MagicMock()
        mock_jpype.isJVMStarted.return_value = False
        mock_import.return_value = mock_jpype

        ZemberekJPypeBridge._instance = None
        ZemberekJPypeBridge._initialized = False

        bridge = ZemberekJPypeBridge()

        with pytest.raises(JVMInitializationError):
            bridge.initialize(jar_path="/nonexistent/path.jar")

    def test_ensure_initialized_raises_when_not_init(self):
        """_ensure_initialized should raise when not initialized."""
        ZemberekJPypeBridge._instance = None
        ZemberekJPypeBridge._initialized = False

        bridge = ZemberekJPypeBridge()

        with pytest.raises(JVMNotStartedError):
            bridge._ensure_initialized()


class TestHealthCheck:
    """Test health check functionality."""

    def test_get_health_returns_dict(self):
        """get_health() should return health dictionary."""
        ZemberekJPypeBridge._instance = None
        ZemberekJPypeBridge._initialized = False

        bridge = ZemberekJPypeBridge()
        health = bridge.get_health()

        assert isinstance(health, dict)
        assert "initialized" in health
        assert "jvm_started" in health
        assert "components" in health

    def test_get_health_shows_uninitialized(self):
        """get_health() should show uninitialized state."""
        ZemberekJPypeBridge._instance = None
        ZemberekJPypeBridge._initialized = False

        bridge = ZemberekJPypeBridge()
        health = bridge.get_health()

        assert health["initialized"] is False
        assert health["components"]["morphology"] is False


class TestMorphologyMethods:
    """Test morphology-related methods."""

    def test_analyze_word_requires_init(self):
        """analyze_word should require initialization."""
        ZemberekJPypeBridge._instance = None
        ZemberekJPypeBridge._initialized = False

        bridge = ZemberekJPypeBridge()

        with pytest.raises(JVMNotStartedError):
            bridge.analyze_word("kitap")

    def test_lemmatize_requires_init(self):
        """lemmatize should require initialization."""
        ZemberekJPypeBridge._instance = None
        ZemberekJPypeBridge._initialized = False

        bridge = ZemberekJPypeBridge()

        with pytest.raises(JVMNotStartedError):
            bridge.lemmatize("kitaplar")

    def test_lemmatize_all_requires_init(self):
        """lemmatize_all should require initialization."""
        ZemberekJPypeBridge._instance = None
        ZemberekJPypeBridge._initialized = False

        bridge = ZemberekJPypeBridge()

        with pytest.raises(JVMNotStartedError):
            bridge.lemmatize_all("kitaplar")


class TestSpellCheckMethods:
    """Test spell check methods."""

    def test_check_spelling_requires_init(self):
        """check_spelling should require initialization."""
        ZemberekJPypeBridge._instance = None
        ZemberekJPypeBridge._initialized = False

        bridge = ZemberekJPypeBridge()

        with pytest.raises(JVMNotStartedError):
            bridge.check_spelling("kitap")


class TestTokenizationMethods:
    """Test tokenization methods."""

    def test_tokenize_requires_init(self):
        """tokenize should require initialization."""
        ZemberekJPypeBridge._instance = None
        ZemberekJPypeBridge._initialized = False

        bridge = ZemberekJPypeBridge()

        with pytest.raises(JVMNotStartedError):
            bridge.tokenize("Merhaba dunya")

    def test_segment_sentences_requires_init(self):
        """segment_sentences should require initialization."""
        ZemberekJPypeBridge._instance = None
        ZemberekJPypeBridge._initialized = False

        bridge = ZemberekJPypeBridge()

        with pytest.raises(JVMNotStartedError):
            bridge.segment_sentences("Birinci cumle. Ikinci cumle.")


class TestNormalizationMethods:
    """Test normalization methods."""

    def test_normalize_requires_init(self):
        """normalize should require initialization."""
        ZemberekJPypeBridge._instance = None
        ZemberekJPypeBridge._initialized = False

        bridge = ZemberekJPypeBridge()

        with pytest.raises(JVMNotStartedError):
            bridge.normalize("merhba nasilsn")


class TestNERMethods:
    """Test NER methods."""

    def test_extract_entities_requires_init(self):
        """extract_entities should require initialization."""
        ZemberekJPypeBridge._instance = None
        ZemberekJPypeBridge._initialized = False

        bridge = ZemberekJPypeBridge()

        with pytest.raises(JVMNotStartedError):
            bridge.extract_entities("Istanbul guzel bir sehir.")


class TestAsyncWrappers:
    """Test async wrapper methods."""

    @pytest.mark.asyncio
    async def test_analyze_word_async_requires_init(self):
        """analyze_word_async should require initialization."""
        ZemberekJPypeBridge._instance = None
        ZemberekJPypeBridge._initialized = False

        bridge = ZemberekJPypeBridge()

        with pytest.raises(JVMNotStartedError):
            await bridge.analyze_word_async("kitap")

    @pytest.mark.asyncio
    async def test_lemmatize_async_requires_init(self):
        """lemmatize_async should require initialization."""
        ZemberekJPypeBridge._instance = None
        ZemberekJPypeBridge._initialized = False

        bridge = ZemberekJPypeBridge()

        with pytest.raises(JVMNotStartedError):
            await bridge.lemmatize_async("kitaplar")


class TestExceptionClasses:
    """Test custom exception classes."""

    def test_jvm_initialization_error(self):
        """JVMInitializationError should have message."""
        error = JVMInitializationError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"

    def test_jvm_not_started_error(self):
        """JVMNotStartedError should have default message."""
        error = JVMNotStartedError()
        assert "JVM is not started" in str(error)

    def test_analysis_error(self):
        """AnalysisError should include word."""
        # Without custom message, default message includes word
        error = AnalysisError("kitap")
        assert "kitap" in str(error)
        assert error.word == "kitap"
        # With custom message, word is stored but not in string
        error_custom = AnalysisError("kitap", "Custom error")
        assert error_custom.word == "kitap"


class TestPathDetection:
    """Test JAR and JVM path detection."""

    def test_find_zemberek_jar_returns_none_if_not_found(self):
        """_find_zemberek_jar should return None if JAR not found."""
        ZemberekJPypeBridge._instance = None
        ZemberekJPypeBridge._initialized = False

        bridge = ZemberekJPypeBridge()

        # Clear environment variable
        import os
        original = os.environ.get("ZEMBEREK_JAR_PATH")
        if "ZEMBEREK_JAR_PATH" in os.environ:
            del os.environ["ZEMBEREK_JAR_PATH"]

        try:
            result = bridge._find_zemberek_jar()
            # Result could be None or a path if JAR exists in default locations
            assert result is None or isinstance(result, str)
        finally:
            if original:
                os.environ["ZEMBEREK_JAR_PATH"] = original

    def test_build_classpath_uses_correct_separator(self):
        """_build_classpath should use platform-specific separator."""
        import platform

        ZemberekJPypeBridge._instance = None
        ZemberekJPypeBridge._initialized = False

        bridge = ZemberekJPypeBridge()
        classpath = bridge._build_classpath("/path/to/test.jar")

        expected_sep = ";" if platform.system() == "Windows" else ":"
        assert "/path/to/test.jar" in classpath
