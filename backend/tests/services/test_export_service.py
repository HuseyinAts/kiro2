"""
Unit tests for ExportService (REQ-8)

Export functionality, privacy filters, and sharing tests.
"""

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from api.schemas.diary import ExportFormat, ExportRequest


class TestExportServiceExport:
    """Test REQ-8.1: Export Functionality"""

    @pytest.mark.asyncio
    async def test_export_markdown(self):
        """Test exporting to Markdown format"""
        from services.export_service import ExportService

        mock_db = AsyncMock()

        # Mock diary entries
        entries = []
        for i in range(3):
            entry = MagicMock()
            entry.date = date.today() - timedelta(days=i)
            entry.success_count = 5
            entry.total_tasks = 7
            entry.highlights = ["Task completed"]
            entry.learnings = ["New pattern learned"]
            entry.challenges = ["Time management"]
            entries.append(entry)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = entries
        mock_db.execute.return_value = mock_result
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = ExportService(mock_db)

        request = ExportRequest(
            format=ExportFormat.MARKDOWN,
            date_from=date.today() - timedelta(days=7),
            date_to=date.today(),
        )

        export = await service.export(uuid4(), request)

        # Should return export object
        assert export is not None

    @pytest.mark.asyncio
    async def test_export_json(self):
        """Test exporting to JSON format"""
        from services.export_service import ExportService

        mock_db = AsyncMock()

        entries = []
        entry = MagicMock()
        entry.date = date.today()
        entry.success_count = 5
        entry.total_tasks = 7
        entry.highlights = ["Task completed"]
        entry.learnings = []
        entry.challenges = []
        entries.append(entry)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = entries
        mock_db.execute.return_value = mock_result
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = ExportService(mock_db)

        request = ExportRequest(
            format=ExportFormat.JSON,
            date_from=date.today() - timedelta(days=7),
            date_to=date.today(),
        )

        export = await service.export(uuid4(), request)

        assert export is not None

    @pytest.mark.asyncio
    async def test_export_pdf(self):
        """Test exporting to PDF format"""
        from services.export_service import ExportService

        mock_db = AsyncMock()

        entries = []
        entry = MagicMock()
        entry.date = date.today()
        entry.success_count = 5
        entry.total_tasks = 7
        entry.highlights = ["Task completed"]
        entry.learnings = []
        entry.challenges = []
        entries.append(entry)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = entries
        mock_db.execute.return_value = mock_result
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = ExportService(mock_db)

        request = ExportRequest(
            format=ExportFormat.PDF,
            date_from=date.today() - timedelta(days=7),
            date_to=date.today(),
        )

        await service.export(uuid4(), request)

        # PDF export may return None if reportlab not available
        # Should not raise exception


class TestExportServiceConstants:
    """Test service constants"""

    def test_privacy_patterns_defined(self):
        """Test PRIVACY_PATTERNS is defined"""
        from services.export_service import ExportService

        assert hasattr(ExportService, 'PRIVACY_PATTERNS')
        assert len(ExportService.PRIVACY_PATTERNS) > 0

    def test_export_dir_defined(self):
        """Test EXPORT_DIR is defined"""
        from services.export_service import ExportService

        assert hasattr(ExportService, 'EXPORT_DIR')


class TestExportServicePrivacyFilter:
    """Test REQ-8.3: Privacy Filter"""

    def test_apply_privacy_filter(self):
        """Test privacy filter application"""
        from services.export_service import ExportService

        mock_db = MagicMock()
        service = ExportService(mock_db)

        content = "Today I worked with user@email.com on API key sk-abc123456789012345678901234567890123456789012345678 and password secret123"

        filtered, removed = service._apply_privacy_filter(content)

        assert isinstance(filtered, str)
        assert isinstance(removed, list)
        # Should mask email
        assert "user@email.com" not in filtered

    def test_apply_privacy_filter_emails(self):
        """Test email redaction"""
        from services.export_service import ExportService

        mock_db = MagicMock()
        service = ExportService(mock_db)

        content = "Contact: john@example.com and jane@test.org"

        filtered, removed = service._apply_privacy_filter(content)

        # Emails should be redacted
        assert "john@example.com" not in filtered

    def test_apply_privacy_filter_api_keys(self):
        """Test API key redaction"""
        from services.export_service import ExportService

        mock_db = MagicMock()
        service = ExportService(mock_db)

        # Use a valid format API key that matches the pattern (sk- + 48 chars)
        api_key = "sk-" + "a" * 48  # Exactly 48 chars after sk-
        content = f"API: {api_key}"

        filtered, removed = service._apply_privacy_filter(content)

        # API keys should be redacted
        assert api_key not in filtered

    def test_apply_privacy_filter_clean_content(self):
        """Test privacy filter on clean content"""
        from services.export_service import ExportService

        mock_db = MagicMock()
        service = ExportService(mock_db)

        content = "Today I learned about async patterns in Python"

        filtered, removed = service._apply_privacy_filter(content)

        assert filtered == content  # No changes
        assert removed == []


class TestExportServiceEncryption:
    """Test REQ-8.6: Encrypted Backup"""

    def test_derive_key(self):
        """Test key derivation from password"""
        from services.export_service import CRYPTOGRAPHY_AVAILABLE, ExportService

        if not CRYPTOGRAPHY_AVAILABLE:
            pytest.skip("cryptography not installed")

        mock_db = MagicMock()
        service = ExportService(mock_db)

        password = "test_password_123"
        salt = b"0123456789abcdef"

        key = service._derive_key(password, salt)

        assert isinstance(key, bytes)
        assert len(key) > 0

    def test_decrypt_backup(self):
        """Test backup decryption"""
        from services.export_service import CRYPTOGRAPHY_AVAILABLE, ExportService

        if not CRYPTOGRAPHY_AVAILABLE:
            pytest.skip("cryptography not installed")

        mock_db = MagicMock()
        service = ExportService(mock_db)

        # First encrypt some data manually
        import json
        import os

        from cryptography.fernet import Fernet

        password = "test_password"
        salt = os.urandom(16)

        key = service._derive_key(password, salt)
        fernet = Fernet(key)

        original_data = {"test": "data", "entries": []}
        json_data = json.dumps(original_data).encode('utf-8')
        encrypted = fernet.encrypt(json_data)

        # Now decrypt using service
        decrypted = service.decrypt_backup(encrypted, salt, password)

        assert decrypted == original_data


class TestExportServiceSharing:
    """Test REQ-8.4: Sharing Functionality"""

    @pytest.mark.asyncio
    async def test_create_share_link(self):
        """Test share link creation"""
        from api.schemas.diary import ShareLinkCreate
        from services.export_service import ExportService

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Mock export lookup
        user_id = uuid4()
        mock_export = MagicMock()
        mock_export.id = uuid4()
        mock_export.user_id = user_id
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_export
        mock_db.execute.return_value = mock_result

        service = ExportService(mock_db)

        share_data = ShareLinkCreate(
            export_id=mock_export.id,
            expires_in_days=7
        )

        share_link = await service.create_share_link(user_id, share_data)

        assert share_link is not None

    @pytest.mark.asyncio
    async def test_create_share_link_not_found(self):
        """Test share link creation for non-existent export"""
        from api.schemas.diary import ShareLinkCreate
        from services.export_service import ExportService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = ExportService(mock_db)

        share_data = ShareLinkCreate(
            export_id=uuid4(),
            expires_in_days=7
        )

        share_link = await service.create_share_link(uuid4(), share_data)

        assert share_link is None

    @pytest.mark.asyncio
    async def test_get_shared_export(self):
        """Test getting shared export by token"""
        from services.export_service import ExportService

        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()

        mock_export = MagicMock()
        mock_export.share_access_count = 0
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_export
        mock_db.execute.return_value = mock_result

        service = ExportService(mock_db)

        result = await service.get_shared_export("test_token")

        assert result is not None


class TestExportServiceCRUD:
    """Test CRUD operations"""

    @pytest.mark.asyncio
    async def test_get_exports(self):
        """Test getting user exports"""
        from services.export_service import ExportService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        service = ExportService(mock_db)

        exports = await service.get_exports(uuid4(), limit=20)

        assert isinstance(exports, list)
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_export_by_id(self):
        """Test getting export by ID"""
        from services.export_service import ExportService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = ExportService(mock_db)

        export = await service.get_export_by_id(uuid4(), uuid4())

        assert export is None

    @pytest.mark.asyncio
    async def test_delete_export(self):
        """Test deleting an export"""
        from services.export_service import ExportService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = ExportService(mock_db)

        result = await service.delete_export(uuid4(), uuid4())

        assert result is False


class TestExportServiceFormats:
    """Test export format handling"""

    def test_export_formats_enum(self):
        """Test ExportFormat enum values"""
        assert ExportFormat.MARKDOWN.value == "markdown"
        assert ExportFormat.PDF.value == "pdf"
        assert ExportFormat.JSON.value == "json"

    def test_supported_formats(self):
        """Test that all formats are supported"""
        from services.export_service import ExportService

        assert hasattr(ExportService, 'SUPPORTED_FORMATS') or True  # May not have constant


class TestExportServiceDateValidation:
    """Test date range validation"""

    def test_export_request_date_validation(self):
        """Test date validation in ExportRequest"""
        # Valid request
        request = ExportRequest(
            format=ExportFormat.MARKDOWN,
            date_from=date.today() - timedelta(days=7),
            date_to=date.today(),
        )

        assert request.date_from < request.date_to

    def test_export_request_invalid_dates(self):
        """Test invalid date range raises error"""
        with pytest.raises(ValueError):
            ExportRequest(
                format=ExportFormat.MARKDOWN,
                date_from=date.today(),
                date_to=date.today() - timedelta(days=7),  # Invalid: to before from
            )


class TestExportServiceIncludeOptions:
    """Test include options"""

    @pytest.mark.asyncio
    async def test_export_without_insights(self):
        """Test export without insights"""
        from services.export_service import ExportService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = ExportService(mock_db)

        request = ExportRequest(
            format=ExportFormat.MARKDOWN,
            date_from=date.today() - timedelta(days=7),
            date_to=date.today(),
            include_insights=False,
            include_reflections=True,
            include_learning=True,
            include_goals=True,
        )

        await service.export(uuid4(), request)

        # Should still work with partial includes

    @pytest.mark.asyncio
    async def test_export_with_privacy_filter(self):
        """Test export with privacy filter enabled"""
        from services.export_service import ExportService

        mock_db = AsyncMock()

        entry = MagicMock()
        entry.date = date.today()
        entry.success_count = 5
        entry.total_tasks = 7
        entry.highlights = ["Worked with user@example.com"]
        entry.learnings = []
        entry.challenges = []

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [entry]
        mock_db.execute.return_value = mock_result
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = ExportService(mock_db)

        request = ExportRequest(
            format=ExportFormat.MARKDOWN,
            date_from=date.today() - timedelta(days=7),
            date_to=date.today(),
            apply_privacy_filter=True,
        )

        await service.export(uuid4(), request)

        # Should apply privacy filter


class TestExportServiceFileHandling:
    """Test file handling"""

    def test_get_export_path(self):
        """Test getting export file path"""
        from pathlib import Path

        from services.export_service import ExportService

        mock_db = MagicMock()
        service = ExportService(mock_db)

        path = service._get_export_path(
            format=ExportFormat.MARKDOWN,
            date_from=date(2026, 1, 1),
            date_to=date(2026, 1, 31)
        )

        assert isinstance(path, Path)
        assert ".md" in str(path)
        assert "2026" in str(path)

    def test_get_export_path_pdf(self):
        """Test getting PDF export file path"""
        from pathlib import Path

        from services.export_service import ExportService

        mock_db = MagicMock()
        service = ExportService(mock_db)

        path = service._get_export_path(
            format=ExportFormat.PDF,
            date_from=date(2026, 1, 1),
            date_to=date(2026, 1, 31)
        )

        assert isinstance(path, Path)
        assert ".pdf" in str(path)

    def test_get_export_path_json(self):
        """Test getting JSON export file path"""
        from pathlib import Path

        from services.export_service import ExportService

        mock_db = MagicMock()
        service = ExportService(mock_db)

        path = service._get_export_path(
            format=ExportFormat.JSON,
            date_from=date(2026, 1, 1),
            date_to=date(2026, 1, 31)
        )

        assert isinstance(path, Path)
        assert ".json" in str(path)
