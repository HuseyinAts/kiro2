"""
Claude Diary Plugin - Export Service

Diary export ve sharing servisi (REQ-8).
Multi-format export, privacy redaction ve encrypted backup.
"""

import io
import json
import os
import re
import secrets
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

try:
    import base64

    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from api.schemas.diary import (
    ExportRequest,
    ShareLinkCreate,
    ShareLinkResponse,
)
from models.diary import (
    DiaryEntry,
    DiaryExport,
    ExportFormat,
    Goal,
    Insight,
    LearningEntry,
    Reflection,
)


class ExportService:
    """
    Export servisi (REQ-8)

    Diary export ve sharing:
    - Multi-format support: markdown, PDF, JSON (REQ-8.1)
    - Date range filtering (REQ-8.2)
    - Privacy redaction (REQ-8.3)
    - Sharing links (REQ-8.4)
    - Customizable templates (REQ-8.5)
    - Encrypted backup (REQ-8.6)
    """

    # Privacy patterns to redact
    PRIVACY_PATTERNS = [
        (r'\b[\w.-]+@[\w.-]+\.\w+\b', '[EMAIL]'),  # Email
        (r'\b\d{10,11}\b', '[PHONE]'),  # Phone
        (r'\b(?:password|sifre|parola)[\s:=]+\S+', '[PASSWORD]'),  # Password
        (r'\bsk-[a-zA-Z0-9]{48}\b', '[API_KEY]'),  # OpenAI API key
        (r'\b[A-Za-z0-9]{32,}\b(?=.*[A-Z])(?=.*[a-z])(?=.*\d)', '[TOKEN]'),  # Generic token
        (r'\b(?:AKIA|ABIA|ACCA|ASIA)[A-Z0-9]{16}\b', '[AWS_KEY]'),  # AWS key
    ]

    # Export directory
    EXPORT_DIR = Path(".kiro/exports")

    def __init__(self, db: AsyncSession):
        """
        Initialize ExportService.

        Args:
            db: AsyncSession - SQLAlchemy async session
        """
        self.db = db

    # =========================================================================
    # REQ-8.1: Multi-Format Export
    # =========================================================================

    async def export(
        self,
        user_id: UUID,
        request: ExportRequest,
    ) -> DiaryExport:
        """
        Diary export olustur (REQ-8.1).

        Args:
            user_id: UUID - Kullanici ID
            request: ExportRequest - Export istegi

        Returns:
            DiaryExport - Export kaydi
        """
        # Verileri topla
        data = await self._collect_data(user_id, request)

        # Format'a gore export
        if request.format == ExportFormat.MARKDOWN:
            content, file_path = await self._export_markdown(data, request)
        elif request.format == ExportFormat.PDF:
            content, file_path = await self._export_pdf(data, request)
        else:  # JSON
            content, file_path = await self._export_json(data, request)

        # Dosya boyutu
        file_size = len(content) if isinstance(content, bytes) else len(content.encode('utf-8'))

        # Redacted fields
        redacted_fields: list[str] = []
        if request.apply_privacy_filter:
            redacted_fields = data.get("redacted_fields", [])

        # Export kaydi olustur
        export_record = DiaryExport(
            user_id=user_id,
            format=request.format,
            date_from=request.date_from,
            date_to=request.date_to,
            file_path=str(file_path) if file_path else None,
            file_size=file_size,
            privacy_filter_applied=request.apply_privacy_filter,
            redacted_fields=redacted_fields,
        )

        self.db.add(export_record)
        await self.db.commit()
        await self.db.refresh(export_record)

        return export_record

    async def _collect_data(
        self,
        user_id: UUID,
        request: ExportRequest,
    ) -> dict[str, Any]:
        """
        Export icin verileri topla.

        Args:
            user_id: UUID - Kullanici ID
            request: ExportRequest - Export istegi

        Returns:
            Dict - Toplanan veriler
        """
        data: dict[str, Any] = {
            "user_id": str(user_id),
            "export_date": datetime.now().isoformat(),
            "date_range": {
                "from": request.date_from.isoformat(),
                "to": request.date_to.isoformat(),
            },
            "entries": [],
            "insights": [],
            "reflections": [],
            "learning_entries": [],
            "goals": [],
            "redacted_fields": [],
        }

        # Diary entries
        entry_query = (
            select(DiaryEntry)
            .where(
                and_(
                    DiaryEntry.user_id == user_id,
                    DiaryEntry.date >= request.date_from,
                    DiaryEntry.date <= request.date_to,
                )
            )
            .order_by(DiaryEntry.date)
        )
        result = await self.db.execute(entry_query)
        entries = list(result.scalars().all())

        for entry in entries:
            entry_data = {
                "id": str(entry.id),
                "date": entry.date.isoformat(),
                "success_count": entry.success_count,
                "failure_count": entry.failure_count,
                "total_tasks": entry.total_tasks,
                "highlights": entry.highlights or [],
                "learnings": entry.learnings or [],
                "challenges": entry.challenges or [],
            }

            # Privacy filter
            if request.apply_privacy_filter:
                entry_data, redacted = self._apply_privacy_filter_to_dict(entry_data)
                data["redacted_fields"].extend(redacted)

            data["entries"].append(entry_data)

        # Insights
        if request.include_insights:
            insight_query = select(Insight).where(
                and_(
                    Insight.user_id == user_id,
                    Insight.diary_entry_id.in_([e.id for e in entries]) if entries else False
                )
            )
            result = await self.db.execute(insight_query)
            insights = list(result.scalars().all())

            for insight in insights:
                insight_data = {
                    "id": str(insight.id),
                    "category": insight.category.value if insight.category else None,
                    "pattern": insight.pattern,
                    "confidence": insight.confidence,
                    "recommendation": insight.recommendation,
                }

                if request.apply_privacy_filter:
                    insight_data, redacted = self._apply_privacy_filter_to_dict(insight_data)
                    data["redacted_fields"].extend(redacted)

                data["insights"].append(insight_data)

        # Reflections
        if request.include_reflections:
            reflection_query = select(Reflection).where(
                and_(
                    Reflection.user_id == user_id,
                    Reflection.diary_entry_id.in_([e.id for e in entries]) if entries else False
                )
            )
            result = await self.db.execute(reflection_query)
            reflections = list(result.scalars().all())

            for reflection in reflections:
                reflection_data = {
                    "id": str(reflection.id),
                    "what_went_well": reflection.what_went_well,
                    "what_could_improve": reflection.what_could_improve,
                    "what_did_i_learn": reflection.what_did_i_learn,
                    "depth": reflection.depth.value if reflection.depth else None,
                    "depth_score": reflection.depth_score,
                }

                if request.apply_privacy_filter:
                    reflection_data, redacted = self._apply_privacy_filter_to_dict(reflection_data)
                    data["redacted_fields"].extend(redacted)

                data["reflections"].append(reflection_data)

        # Learning entries
        if request.include_learning:
            learning_query = (
                select(LearningEntry)
                .where(
                    and_(
                        LearningEntry.user_id == user_id,
                        LearningEntry.created_at >= datetime.combine(request.date_from, datetime.min.time()),
                        LearningEntry.created_at <= datetime.combine(request.date_to, datetime.max.time()),
                    )
                )
            )
            result = await self.db.execute(learning_query)
            learning_entries = list(result.scalars().all())

            for learning in learning_entries:
                learning_data = {
                    "id": str(learning.id),
                    "title": learning.title,
                    "content": learning.content[:200] + "..." if len(learning.content) > 200 else learning.content,
                    "tags": learning.tags or [],
                    "domain": learning.domain,
                    "retention_score": learning.retention_score,
                }

                if request.apply_privacy_filter:
                    learning_data, redacted = self._apply_privacy_filter_to_dict(learning_data)
                    data["redacted_fields"].extend(redacted)

                data["learning_entries"].append(learning_data)

        # Goals
        if request.include_goals:
            goal_query = (
                select(Goal)
                .where(
                    and_(
                        Goal.user_id == user_id,
                        Goal.created_at >= datetime.combine(request.date_from, datetime.min.time()),
                        Goal.created_at <= datetime.combine(request.date_to, datetime.max.time()),
                    )
                )
            )
            result = await self.db.execute(goal_query)
            goals = list(result.scalars().all())

            for goal in goals:
                goal_data = {
                    "id": str(goal.id),
                    "title": goal.title,
                    "progress": goal.progress,
                    "status": goal.status.value if goal.status else None,
                    "target_date": goal.target_date.isoformat() if goal.target_date else None,
                }

                if request.apply_privacy_filter:
                    goal_data, redacted = self._apply_privacy_filter_to_dict(goal_data)
                    data["redacted_fields"].extend(redacted)

                data["goals"].append(goal_data)

        # Remove duplicates from redacted fields
        data["redacted_fields"] = list(set(data["redacted_fields"]))

        return data

    async def _export_markdown(
        self,
        data: dict[str, Any],
        request: ExportRequest,
    ) -> tuple[str, Path | None]:
        """
        Markdown export olustur.

        Args:
            data: Dict - Export verileri
            request: ExportRequest - Export istegi

        Returns:
            Tuple[str, Path] - Icerik ve dosya yolu
        """
        md = f"""# Claude Diary Export

**Tarih Aralığı:** {request.date_from} - {request.date_to}
**Oluşturulma:** {data['export_date']}

---

## 📊 Özet

- **Toplam Gün:** {len(data['entries'])}
- **Toplam Insight:** {len(data['insights'])}
- **Toplam Yansıtma:** {len(data['reflections'])}
- **Toplam Öğrenme:** {len(data['learning_entries'])}
- **Toplam Hedef:** {len(data['goals'])}

"""

        # Entries
        if data['entries']:
            md += "\n## 📔 Günlük Kayıtları\n\n"
            for entry in data['entries']:
                md += f"### {entry['date']}\n\n"
                md += f"- **Başarılı:** {entry['success_count']} | **Başarısız:** {entry['failure_count']}\n"
                if entry['highlights']:
                    md += f"- **Öne Çıkanlar:** {', '.join(entry['highlights'][:3])}\n"
                if entry['learnings']:
                    md += f"- **Öğrenimler:** {', '.join(entry['learnings'][:3])}\n"
                md += "\n"

        # Insights
        if data['insights']:
            md += "\n## 💡 İçgörüler\n\n"
            for insight in data['insights']:
                md += f"- **[{insight.get('category', 'N/A')}]** {insight['pattern']}\n"
                md += f"  - *Öneri:* {insight['recommendation']}\n"
                md += f"  - *Güven:* %{int(insight['confidence'] * 100)}\n\n"

        # Reflections
        if data['reflections']:
            md += "\n## 🪞 Yansıtmalar\n\n"
            for reflection in data['reflections']:
                md += f"- **Derinlik:** {reflection.get('depth', 'N/A')} (skor: {reflection.get('depth_score', 0)})\n"
                if reflection.get('what_went_well'):
                    md += f"  - *İyi giden:* {reflection['what_went_well'][:100]}...\n"
                if reflection.get('what_did_i_learn'):
                    md += f"  - *Öğrenilen:* {reflection['what_did_i_learn'][:100]}...\n"
                md += "\n"

        # Learning entries
        if data['learning_entries']:
            md += "\n## 📚 Öğrenme Günlüğü\n\n"
            for learning in data['learning_entries']:
                md += f"- **{learning['title']}**\n"
                if learning.get('tags'):
                    md += f"  - *Etiketler:* {', '.join(learning['tags'])}\n"
                md += f"  - *Retention:* %{int(learning.get('retention_score', 0) * 100)}\n\n"

        # Goals
        if data['goals']:
            md += "\n## 🎯 Hedefler\n\n"
            for goal in data['goals']:
                status_emoji = {"active": "🟡", "completed": "✅", "at_risk": "🔴", "cancelled": "⚫"}.get(
                    goal.get('status'), "❓"
                )
                md += f"- {status_emoji} **{goal['title']}** - %{goal.get('progress', 0)}\n"

        # Privacy notice
        if request.apply_privacy_filter and data['redacted_fields']:
            md += f"\n---\n\n*{len(data['redacted_fields'])} hassas alan gizlendi.*\n"

        md += "\n---\n\n*Claude Diary Plugin ile oluşturuldu*\n"

        # Dosyaya kaydet
        file_path = self._get_export_path(request.format, request.date_from, request.date_to)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(md)

        return md, file_path

    async def _export_pdf(
        self,
        data: dict[str, Any],
        request: ExportRequest,
    ) -> tuple[bytes, Path | None]:
        """
        PDF export olustur.

        Args:
            data: Dict - Export verileri
            request: ExportRequest - Export istegi

        Returns:
            Tuple[bytes, Path] - PDF bytes ve dosya yolu
        """
        if not REPORTLAB_AVAILABLE:
            # Fallback to markdown if reportlab not available
            md_content, _ = await self._export_markdown(data, request)
            return md_content.encode('utf-8'), None

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)

        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
        )
        story.append(Paragraph("Claude Diary Export", title_style))

        # Date range
        story.append(Paragraph(
            f"<b>Tarih Aralığı:</b> {request.date_from} - {request.date_to}",
            styles['Normal']
        ))
        story.append(Spacer(1, 20))

        # Summary table
        summary_data = [
            ["Metrik", "Değer"],
            ["Toplam Gün", str(len(data['entries']))],
            ["Toplam Insight", str(len(data['insights']))],
            ["Toplam Yansıtma", str(len(data['reflections']))],
            ["Toplam Öğrenme", str(len(data['learning_entries']))],
            ["Toplam Hedef", str(len(data['goals']))],
        ]

        summary_table = Table(summary_data, colWidths=[200, 100])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 30))

        # Entries
        if data['entries']:
            story.append(Paragraph("Günlük Kayıtları", styles['Heading2']))
            for entry in data['entries'][:10]:  # Limit to 10 for PDF
                story.append(Paragraph(
                    f"<b>{entry['date']}</b> - Başarılı: {entry['success_count']}, Başarısız: {entry['failure_count']}",
                    styles['Normal']
                ))
            story.append(Spacer(1, 20))

        # Insights
        if data['insights']:
            story.append(Paragraph("İçgörüler", styles['Heading2']))
            for insight in data['insights'][:5]:  # Limit
                story.append(Paragraph(
                    f"• [{insight.get('category', 'N/A')}] {insight['pattern'][:100]}...",
                    styles['Normal']
                ))
            story.append(Spacer(1, 20))

        # Goals
        if data['goals']:
            story.append(Paragraph("Hedefler", styles['Heading2']))
            for goal in data['goals'][:5]:
                story.append(Paragraph(
                    f"• {goal['title']} - %{goal.get('progress', 0)} ({goal.get('status', 'N/A')})",
                    styles['Normal']
                ))

        # Build PDF
        doc.build(story)
        pdf_bytes = buffer.getvalue()

        # Dosyaya kaydet
        file_path = self._get_export_path(request.format, request.date_from, request.date_to)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'wb') as f:
            f.write(pdf_bytes)

        return pdf_bytes, file_path

    async def _export_json(
        self,
        data: dict[str, Any],
        request: ExportRequest,
    ) -> tuple[str, Path | None]:
        """
        JSON export olustur.

        Args:
            data: Dict - Export verileri
            request: ExportRequest - Export istegi

        Returns:
            Tuple[str, Path] - JSON string ve dosya yolu
        """
        json_str = json.dumps(data, indent=2, ensure_ascii=False, default=str)

        # Dosyaya kaydet
        file_path = self._get_export_path(request.format, request.date_from, request.date_to)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(json_str)

        return json_str, file_path

    def _get_export_path(
        self,
        format: ExportFormat,
        date_from: date,
        date_to: date,
    ) -> Path:
        """Export dosya yolunu olustur."""
        extension = {
            ExportFormat.MARKDOWN: "md",
            ExportFormat.PDF: "pdf",
            ExportFormat.JSON: "json",
        }[format]

        filename = f"diary_export_{date_from}_{date_to}.{extension}"
        return self.EXPORT_DIR / filename

    # =========================================================================
    # REQ-8.3: Privacy Redaction
    # =========================================================================

    def _apply_privacy_filter(
        self,
        content: str,
    ) -> tuple[str, list[str]]:
        """
        Privacy filter uygula (REQ-8.3).

        Args:
            content: str - Icerik

        Returns:
            Tuple[str, List[str]] - Filtrelenmis icerik ve redact edilen alanlar
        """
        redacted_fields: list[str] = []

        for pattern, replacement in self.PRIVACY_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                redacted_fields.append(replacement)

        return content, redacted_fields

    def _apply_privacy_filter_to_dict(
        self,
        data: dict[str, Any],
    ) -> tuple[dict[str, Any], list[str]]:
        """Dict'e privacy filter uygula."""
        all_redacted: list[str] = []

        for key, value in data.items():
            if isinstance(value, str):
                filtered, redacted = self._apply_privacy_filter(value)
                data[key] = filtered
                all_redacted.extend(redacted)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, str):
                        filtered, redacted = self._apply_privacy_filter(item)
                        value[i] = filtered
                        all_redacted.extend(redacted)

        return data, all_redacted

    # =========================================================================
    # REQ-8.4: Sharing Links
    # =========================================================================

    async def create_share_link(
        self,
        user_id: UUID,
        data: ShareLinkCreate,
    ) -> ShareLinkResponse | None:
        """
        Paylasim linki olustur (REQ-8.4).

        Args:
            user_id: UUID - Kullanici ID
            data: ShareLinkCreate - Paylasim verileri

        Returns:
            Optional[ShareLinkResponse] - Paylasim linki veya None
        """
        # Export'u bul
        query = select(DiaryExport).where(
            and_(
                DiaryExport.id == data.export_id,
                DiaryExport.user_id == user_id
            )
        )
        result = await self.db.execute(query)
        export_record = result.scalar_one_or_none()

        if not export_record:
            return None

        # Token olustur
        share_token = secrets.token_urlsafe(32)

        # Expiration
        expires_at = datetime.now() + timedelta(days=data.expires_in_days)

        # Share URL (placeholder - gercek URL host'a gore ayarlanmali)
        share_url = f"/api/v1/diary/export/share/{share_token}"

        # Export kaydini guncelle
        export_record.share_token = share_token
        export_record.share_url = share_url
        export_record.share_expires_at = expires_at
        export_record.is_public = True

        await self.db.commit()
        await self.db.refresh(export_record)

        return ShareLinkResponse(
            export_id=export_record.id,
            share_token=share_token,
            share_url=share_url,
            expires_at=expires_at,
        )

    async def get_shared_export(
        self,
        share_token: str,
    ) -> DiaryExport | None:
        """
        Paylasilan export'u getir.

        Args:
            share_token: str - Paylasim token'i

        Returns:
            Optional[DiaryExport] - Export veya None
        """
        query = select(DiaryExport).where(
            and_(
                DiaryExport.share_token == share_token,
                DiaryExport.is_public == True,
                DiaryExport.share_expires_at > datetime.now()
            )
        )

        result = await self.db.execute(query)
        export_record = result.scalar_one_or_none()

        if export_record:
            # Access count artir
            export_record.share_access_count = (export_record.share_access_count or 0) + 1
            await self.db.commit()

        return export_record

    # =========================================================================
    # REQ-8.6: Encrypted Backup
    # =========================================================================

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Sifre'den anahtar turet."""
        if not CRYPTOGRAPHY_AVAILABLE:
            raise RuntimeError("cryptography paketi gerekli")

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    async def create_encrypted_backup(
        self,
        user_id: UUID,
        password: str,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> tuple[bytes, bytes]:
        """
        Sifrelenmis backup olustur (REQ-8.6).

        AES-256 encryption.

        Args:
            user_id: UUID - Kullanici ID
            password: str - Sifreleme sifresi
            date_from: Optional[date] - Baslangic
            date_to: Optional[date] - Bitis

        Returns:
            Tuple[bytes, bytes] - Encrypted data ve salt
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            raise RuntimeError("cryptography paketi gerekli")

        # Default tarihler
        if not date_to:
            date_to = date.today()
        if not date_from:
            date_from = date_to - timedelta(days=365)

        # Verileri topla
        request = ExportRequest(
            format=ExportFormat.JSON,
            date_from=date_from,
            date_to=date_to,
            include_insights=True,
            include_reflections=True,
            include_learning=True,
            include_goals=True,
            apply_privacy_filter=False,
        )
        data = await self._collect_data(user_id, request)

        # JSON serialize
        json_data = json.dumps(data, ensure_ascii=False, default=str)

        # Salt olustur
        salt = os.urandom(16)

        # Key turet
        key = self._derive_key(password, salt)

        # Sifrele
        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(json_data.encode('utf-8'))

        # Backup kaydi olustur
        backup_export = DiaryExport(
            user_id=user_id,
            format=ExportFormat.JSON,
            date_from=date_from,
            date_to=date_to,
            is_backup=True,
            is_encrypted=True,
            encryption_algorithm="AES-256-Fernet",
            file_size=len(encrypted_data),
        )

        self.db.add(backup_export)
        await self.db.commit()

        return encrypted_data, salt

    def decrypt_backup(
        self,
        encrypted_data: bytes,
        salt: bytes,
        password: str,
    ) -> dict[str, Any]:
        """
        Backup'i coz.

        Args:
            encrypted_data: bytes - Sifrelenmis veri
            salt: bytes - Salt
            password: str - Sifre

        Returns:
            Dict - Cozulmus veri
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            raise RuntimeError("cryptography paketi gerekli")

        key = self._derive_key(password, salt)
        fernet = Fernet(key)

        decrypted_data = fernet.decrypt(encrypted_data)
        return json.loads(decrypted_data.decode('utf-8'))

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    async def get_exports(
        self,
        user_id: UUID,
        limit: int = 20,
    ) -> list[DiaryExport]:
        """
        Export gecmisini getir.

        Args:
            user_id: UUID - Kullanici ID
            limit: int - Maksimum kayit sayisi

        Returns:
            List[DiaryExport] - Export listesi
        """
        query = (
            select(DiaryExport)
            .where(DiaryExport.user_id == user_id)
            .order_by(desc(DiaryExport.created_at))
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_export_by_id(
        self,
        export_id: UUID,
        user_id: UUID,
    ) -> DiaryExport | None:
        """
        ID ile export getir.

        Args:
            export_id: UUID - Export ID
            user_id: UUID - Kullanici ID

        Returns:
            Optional[DiaryExport] - Export veya None
        """
        query = select(DiaryExport).where(
            and_(
                DiaryExport.id == export_id,
                DiaryExport.user_id == user_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def delete_export(
        self,
        export_id: UUID,
        user_id: UUID,
    ) -> bool:
        """
        Export sil.

        Args:
            export_id: UUID - Export ID
            user_id: UUID - Kullanici ID

        Returns:
            bool - Basari durumu
        """
        export_record = await self.get_export_by_id(export_id, user_id)
        if not export_record:
            return False

        # Dosyayi da sil
        if export_record.file_path:
            try:
                Path(export_record.file_path).unlink(missing_ok=True)
            except Exception:
                pass

        await self.db.delete(export_record)
        await self.db.commit()
        return True
