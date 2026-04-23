
"""
Structured Logging System Tests - Teknofest 2025 Eğitim Eylemci Platformu
"""

import asyncio
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from core.log_config import LogAnalyzer, LogRetentionManager
    from core.logging_middleware import DatabaseLoggingMiddleware
    from core.structured_logger import (
        JSONFormatter,
        LogCategory,
        StructuredLogger,
        log_execution_time,
        setup_logging,
    )
except (ImportError, ModuleNotFoundError):
    pytest.skip("logging modules not available", allow_module_level=True)


class TestStructuredLogger:
    """StructuredLogger test sınıfı"""

    def setup_method(self):
        """Her test öncesi çalışır"""
        self.temp_dir = tempfile.mkdtemp()
        self.logger = StructuredLogger("test-logger", log_dir=self.temp_dir)

    def teardown_method(self):
        """Her test sonrası çalışır"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_logger_initialization(self):
        """Logger başlatma testi"""
        assert self.logger.name == "test-logger"
        assert self.logger.logger is not None
        assert len(self.logger.logger.handlers) == 3  # console, file, error

    def test_basic_logging(self):
        """Temel loglama testi"""
        self.logger.info("Test mesajı", test_param="test_value")
        self.logger.error("Test hatası", error_code="TEST_ERROR")
        self.logger.warning("Test uyarısı")
        self.logger.debug("Test debug")
        self.logger.critical("Test kritik")

        # Log dosyasının oluştuğunu kontrol et
        log_file = Path(self.temp_dir) / "test-logger.log"
        assert log_file.exists()

        # Log içeriğini kontrol et
        with open(log_file, encoding="utf-8") as f:
            logs = f.readlines()

        assert len(logs) >= 4  # debug hariç (console level INFO)

        # JSON formatını kontrol et
        for log_line in logs:
            log_data = json.loads(log_line)
            assert "timestamp" in log_data
            assert "level" in log_data
            assert "message" in log_data

    def test_log_categories(self):
        """Log kategorileri testi"""
        self.logger.info("Auth test", LogCategory.AUTH, user_id="123")
        self.logger.info("Exam test", LogCategory.EXAM, exam_id="456")
        self.logger.info("API test", LogCategory.API, endpoint="/test")

        log_file = Path(self.temp_dir) / "test-logger.log"
        with open(log_file, encoding="utf-8") as f:
            logs = [json.loads(line) for line in f.readlines()]

        categories = [log.get("category") for log in logs]
        assert "auth" in categories
        assert "exam" in categories
        assert "api" in categories

    def test_exception_logging(self):
        """Exception loglama testi"""
        try:
            raise ValueError("Test exception")
        except Exception as e:
            self.logger.log_exception("Test exception occurred", e, LogCategory.SYSTEM)

        log_file = Path(self.temp_dir) / "test-logger.log"
        with open(log_file, encoding="utf-8") as f:
            log_data = json.loads(f.readline())

        assert log_data["level"] == "ERROR"
        assert "exception_type" in log_data
        assert log_data["exception_type"] == "ValueError"
        assert "stack_trace" in log_data

    def test_user_action_logging(self):
        """Kullanıcı eylem loglama testi"""
        self.logger.log_user_action(
            user_id="user123",
            action="exam_started",
            details={"exam_type": "TYT", "duration": 165},
        )

        log_file = Path(self.temp_dir) / "test-logger.log"
        with open(log_file, encoding="utf-8") as f:
            log_data = json.loads(f.readline())

        assert log_data["category"] == "user_action"
        assert log_data["user_id"] == "user123"
        assert log_data["action"] == "exam_started"
        assert "details" in log_data

    def test_performance_logging(self):
        """Performans loglama testi"""
        self.logger.log_performance(
            operation="database_query",
            duration_ms=150.5,
            success=True,
            query_type="SELECT",
        )

        log_file = Path(self.temp_dir) / "test-logger.log"
        with open(log_file, encoding="utf-8") as f:
            log_data = json.loads(f.readline())

        assert log_data["category"] == "performance"
        assert log_data["operation"] == "database_query"
        assert log_data["duration_ms"] == 150.5
        assert log_data["success"] is True

    def test_api_call_logging(self):
        """API çağrı loglama testi"""
        self.logger.log_api_call(
            method="POST",
            endpoint="/api/v1/exam/start",
            status_code=200,
            duration_ms=250.0,
            user_id="user123",
        )

        log_file = Path(self.temp_dir) / "test-logger.log"
        with open(log_file, encoding="utf-8") as f:
            log_data = json.loads(f.readline())

        assert log_data["category"] == "api"
        assert log_data["method"] == "POST"
        assert log_data["endpoint"] == "/api/v1/exam/start"
        assert log_data["status_code"] == 200

    def test_agent_activity_logging(self):
        """AI Agent aktivite loglama testi"""
        self.logger.log_agent_activity(
            agent_name="LearningPathAgent",
            activity="generate_learning_path",
            student_id="student123",
            success=True,
            path_length=5,
        )

        log_file = Path(self.temp_dir) / "test-logger.log"
        with open(log_file, encoding="utf-8") as f:
            log_data = json.loads(f.readline())

        assert log_data["category"] == "agent"
        assert log_data["agent_name"] == "LearningPathAgent"
        assert log_data["activity"] == "generate_learning_path"
        assert log_data["student_id"] == "student123"


class TestJSONFormatter:
    """JSONFormatter test sınıfı"""

    def test_json_formatting(self):
        """JSON formatı testi"""
        import logging

        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)
        log_data = json.loads(formatted)

        assert log_data["level"] == "INFO"
        assert log_data["message"] == "Test message"
        assert "timestamp" in log_data
        assert "module" in log_data
        assert "function" in log_data


class TestLogExecutionTimeDecorator:
    """log_execution_time decorator test sınıfı"""

    def setup_method(self):
        """Her test öncesi çalışır"""
        self.temp_dir = tempfile.mkdtemp()
        setup_logging(log_dir=self.temp_dir)

    def teardown_method(self):
        """Her test sonrası çalışır"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @log_execution_time(LogCategory.PERFORMANCE)
    def sample_function(self, duration=0.1):
        """Test fonksiyonu"""
        import time

        time.sleep(duration)
        return "success"

    @log_execution_time(LogCategory.PERFORMANCE)
    async def sample_async_function(self, duration=0.1):
        """Test async fonksiyonu"""
        await asyncio.sleep(duration)
        return "async_success"

    def test_sync_function_logging(self):
        """Sync fonksiyon loglama testi"""
        result = self.sample_function(0.05)
        assert result == "success"

        # Log dosyasını kontrol et
        log_file = Path(self.temp_dir) / "teknofest-platform.log"
        assert log_file.exists()

        with open(log_file, encoding="utf-8") as f:
            logs = [json.loads(line) for line in f.readlines()]

        performance_logs = [log for log in logs if log.get("category") == "performance"]
        assert len(performance_logs) > 0

        perf_log = performance_logs[0]
        assert "duration_ms" in perf_log
        assert perf_log["success"] is True

    @pytest.mark.asyncio
    async def test_async_function_logging(self):
        """Async fonksiyon loglama testi"""
        result = await self.sample_async_function(0.05)
        assert result == "async_success"

        # Log dosyasını kontrol et
        log_file = Path(self.temp_dir) / "teknofest-platform.log"
        assert log_file.exists()


class TestDatabaseLoggingMiddleware:
    """DatabaseLoggingMiddleware test sınıfı"""

    def setup_method(self):
        """Her test öncesi çalışır"""
        self.temp_dir = tempfile.mkdtemp()
        setup_logging(log_dir=self.temp_dir)
        self.db_middleware = DatabaseLoggingMiddleware()

    def teardown_method(self):
        """Her test sonrası çalışır"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_query_logging(self):
        """Veritabanı sorgu loglama testi"""
        await self.db_middleware.log_query(
            query="SELECT * FROM users WHERE id = %s",
            params={"id": 123, "password": "secret123"},
            duration_ms=45.2,
            rows_affected=1,
            operation_type="SELECT",
        )

        log_file = Path(self.temp_dir) / "teknofest-platform.log"
        with open(log_file, encoding="utf-8") as f:
            log_data = json.loads(f.readline())

        assert log_data["category"] == "database"
        assert "SELECT * FROM users" in log_data["query"]
        assert log_data["duration_ms"] == 45.2
        assert log_data["params"]["password"] == "***HIDDEN***"  # Sanitized

    @pytest.mark.asyncio
    async def test_slow_query_warning(self):
        """Yavaş sorgu uyarı testi"""
        await self.db_middleware.log_query(
            query="SELECT * FROM large_table",
            duration_ms=1500.0,  # 1.5 saniye
            operation_type="SELECT",
        )

        log_file = Path(self.temp_dir) / "teknofest-platform.log"
        with open(log_file, encoding="utf-8") as f:
            log_data = json.loads(f.readline())

        assert log_data["level"] == "WARNING"
        assert "Yavaş veritabanı sorgusu" in log_data["message"]


class TestLogRetentionManager:
    """LogRetentionManager test sınıfı"""

    def setup_method(self):
        """Her test öncesi çalışır"""
        self.temp_dir = tempfile.mkdtemp()
        self.retention_manager = LogRetentionManager(self.temp_dir)

    def teardown_method(self):
        """Her test sonrası çalışır"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_log_file_sizes(self):
        """Log dosya boyutları testi"""
        # Test dosyaları oluştur
        test_file1 = Path(self.temp_dir) / "test1.log"
        test_file2 = Path(self.temp_dir) / "test2.log"

        test_file1.write_text("Test log content 1")
        test_file2.write_text("Test log content 2 - longer")

        sizes = self.retention_manager.get_log_file_sizes()

        assert len(sizes) == 2
        assert sizes[str(test_file1)] > 0
        assert sizes[str(test_file2)] > sizes[str(test_file1)]

    def test_cleanup_old_logs(self):
        """Eski log temizleme testi"""
        # Test dosyası oluştur
        old_log = Path(self.temp_dir) / "old.log"
        old_log.write_text("Old log content")

        # Dosya zamanını değiştir (çok eski yap)
        import time

        old_time = time.time() - (40 * 24 * 60 * 60)  # 40 gün önce
        os.utime(old_log, (old_time, old_time))

        # Temizlik yap
        deleted_files = self.retention_manager.cleanup_old_logs(retention_days=30)

        assert len(deleted_files) == 1
        assert not old_log.exists()


class TestLogAnalyzer:
    """LogAnalyzer test sınıfı"""

    def setup_method(self):
        """Her test öncesi çalışır"""
        self.temp_dir = tempfile.mkdtemp()
        self.analyzer = LogAnalyzer(self.temp_dir)

    def teardown_method(self):
        """Her test sonrası çalışır"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_error_pattern_analysis(self):
        """Hata kalıp analizi testi"""
        # Test error log dosyası oluştur
        error_log = Path(self.temp_dir) / "teknofest-platform-errors.log"

        error_entries = [
            {
                "timestamp": datetime.now().isoformat(),
                "level": "ERROR",
                "message": "Test error 1",
                "exception": {"type": "ValueError"},
                "endpoint": "/api/v1/test",
            },
            {
                "timestamp": datetime.now().isoformat(),
                "level": "ERROR",
                "message": "Test error 2",
                "exception": {"type": "ValueError"},
                "endpoint": "/api/v1/test",
            },
            {
                "timestamp": datetime.now().isoformat(),
                "level": "ERROR",
                "message": "Test error 3",
                "exception": {"type": "KeyError"},
                "endpoint": "/api/v1/other",
            },
        ]

        with open(error_log, "w", encoding="utf-8") as f:
            for entry in error_entries:
                f.write(json.dumps(entry) + "\n")

        # Analiz yap
        patterns = self.analyzer.analyze_error_patterns(hours=24)

        assert patterns["total_errors"] == 3
        assert patterns["error_types"]["ValueError"] == 2
        assert patterns["error_types"]["KeyError"] == 1
        assert patterns["error_endpoints"]["/api/v1/test"] == 2


if __name__ == "__main__":
    pytest.main([__file__])
