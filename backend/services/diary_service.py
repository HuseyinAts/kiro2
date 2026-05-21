"""
Claude Diary Plugin - Diary Service

Gunluk ozet olusturma servisi (REQ-1).
Task agregasyonu, key learnings, highlights, challenges ve markdown formatting.
"""

from datetime import date, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

# B-P0-21: wrong-direction import (service→api). Plan: move to
# services/schemas/diary.py in a separate sprint to break the cycle.
from api.schemas.diary import (  # noqa: TID  # B-P0-21
    TaskSummary,
)
from models.diary import DiaryEntry


class DiaryService:
    """
    Gunluk ozet servisi (REQ-1)

    Gunluk aktivite ozetleri:
    - Task agregasyonu (success/failure count)
    - Key learnings (top 3)
    - Highlights (one cikan tasklar)
    - Challenges (karsilasilan zorluklar)
    - Markdown formatting
    - File persistence (.kiro/diary/YYYY-MM-DD.md)
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize DiaryService.

        Args:
            db: AsyncSession - SQLAlchemy async session
        """
        self.db = db
        self.diary_base_path = Path(".kiro/diary")

    # =========================================================================
    # REQ-1.1: Task Aggregation
    # =========================================================================

    def aggregate_tasks(self, tasks: list[TaskSummary]) -> dict[str, Any]:
        """
        Task istatistiklerini hesapla (REQ-1.1).

        Args:
            tasks: List[TaskSummary] - Task listesi

        Returns:
            Dict containing:
            - success_count: Basarili task sayisi
            - failure_count: Basarisiz task sayisi
            - total_tasks: Toplam task sayisi
            - total_duration_minutes: Toplam sure (dakika)
            - success_rate: Basari orani (%)
        """
        success_count = sum(1 for t in tasks if t.status == "success")
        failure_count = sum(1 for t in tasks if t.status == "failure")
        partial_count = sum(1 for t in tasks if t.status == "partial")
        total_duration = sum(t.duration_minutes for t in tasks)

        total_tasks = len(tasks)
        success_rate = (success_count / total_tasks * 100) if total_tasks > 0 else 0.0

        return {
            "success_count": success_count,
            "failure_count": failure_count,
            "partial_count": partial_count,
            "total_tasks": total_tasks,
            "total_duration_minutes": total_duration,
            "success_rate": round(success_rate, 2),
        }

    # =========================================================================
    # REQ-1.2: Key Learnings Extraction
    # =========================================================================

    def extract_learnings(
        self,
        tasks: list[TaskSummary],
        max_learnings: int = 3
    ) -> list[str]:
        """
        Task notlarindan key learnings cikar (REQ-1.2).

        Args:
            tasks: List[TaskSummary] - Task listesi
            max_learnings: int - Maksimum ogrenim sayisi (default: 3)

        Returns:
            List[str] - Key learnings listesi (top 3)
        """
        learnings: list[str] = []

        # Basarili tasklerden ogrenimler
        successful_tasks = [t for t in tasks if t.status == "success"]
        for task in successful_tasks:
            if task.notes and len(task.notes) > 20:
                # Notlardan ogrenim cikar
                learning = f"[{task.task_type or 'Task'}] {task.title}: {task.notes[:100]}"
                learnings.append(learning)

        # Basarisiz tasklerden dersler
        failed_tasks = [t for t in tasks if t.status == "failure"]
        for task in failed_tasks:
            if task.notes:
                learning = f"[Ders] {task.title}: {task.notes[:100]}"
                learnings.append(learning)

        # Uzun suren tasklerden cikarimlar
        long_tasks = sorted(tasks, key=lambda t: t.duration_minutes, reverse=True)[:2]
        for task in long_tasks:
            if task.duration_minutes > 30:
                learning = f"[Zaman] {task.title}: {task.duration_minutes} dakika suruyor"
                if learning not in learnings:
                    learnings.append(learning)

        return learnings[:max_learnings]

    # =========================================================================
    # REQ-1.3: Highlight Selection
    # =========================================================================

    def select_highlights(
        self,
        tasks: list[TaskSummary],
        max_highlights: int = 3
    ) -> list[str]:
        """
        En etkili tasklari sec (REQ-1.3).

        Secim kriterleri:
        - Basarili tasklar oncelikli
        - Uzun suren tasklar daha onemli
        - Notlu tasklar tercih edilir

        Args:
            tasks: List[TaskSummary] - Task listesi
            max_highlights: int - Maksimum highlight sayisi

        Returns:
            List[str] - Highlight listesi
        """
        # Skor hesapla
        scored_tasks: list[tuple] = []
        for task in tasks:
            score = 0
            # Basari durumu
            if task.status == "success":
                score += 50
            elif task.status == "partial":
                score += 25
            # Sure (normalize edilmis)
            score += min(task.duration_minutes, 60) * 0.5
            # Not varsa bonus
            if task.notes:
                score += 20

            scored_tasks.append((score, task))

        # Skorla sirala
        scored_tasks.sort(key=lambda x: x[0], reverse=True)

        # Highlight formatla
        highlights: list[str] = []
        for score, task in scored_tasks[:max_highlights]:
            status_emoji = "✅" if task.status == "success" else "⚠️"
            highlight = f"{status_emoji} {task.title}"
            if task.duration_minutes > 0:
                highlight += f" ({task.duration_minutes} dk)"
            highlights.append(highlight)

        return highlights

    # =========================================================================
    # REQ-1.4: Challenge Logging
    # =========================================================================

    def extract_challenges(self, tasks: list[TaskSummary]) -> list[str]:
        """
        Karsilasilan zorluklari listele (REQ-1.4).

        Args:
            tasks: List[TaskSummary] - Task listesi

        Returns:
            List[str] - Zorluklar listesi
        """
        challenges: list[str] = []

        # Basarisiz taskler
        failed_tasks = [t for t in tasks if t.status == "failure"]
        for task in failed_tasks:
            challenge = f"❌ {task.title}"
            if task.notes:
                challenge += f": {task.notes[:80]}"
            challenges.append(challenge)

        # Kismi basarili taskler
        partial_tasks = [t for t in tasks if t.status == "partial"]
        for task in partial_tasks:
            challenge = f"⚠️ {task.title} (kismi)"
            if task.notes:
                challenge += f": {task.notes[:80]}"
            challenges.append(challenge)

        # Cok uzun suren taskler (potansiyel zorluk)
        long_tasks = [t for t in tasks if t.duration_minutes > 60]
        for task in long_tasks:
            if task.status == "success":
                challenge = f"⏱️ {task.title}: Beklenenin ustunde sure ({task.duration_minutes} dk)"
                challenges.append(challenge)

        return challenges

    # =========================================================================
    # REQ-1.5: Markdown Formatting
    # =========================================================================

    def format_markdown(
        self,
        entry_date: date,
        stats: dict[str, Any],
        highlights: list[str],
        learnings: list[str],
        challenges: list[str],
        tasks: list[TaskSummary],
    ) -> str:
        """
        Markdown ozet olustur (REQ-1.5).

        Args:
            entry_date: date - Kayit tarihi
            stats: Dict - Task istatistikleri
            highlights: List[str] - One cikan tasklar
            learnings: List[str] - Key learnings
            challenges: List[str] - Zorluklar
            tasks: List[TaskSummary] - Tum tasklar

        Returns:
            str - Markdown formatli ozet
        """
        date_str = entry_date.strftime("%Y-%m-%d")
        day_name_tr = self._get_turkish_day_name(entry_date)

        md = f"""# 📔 Gunluk Ozet - {date_str} ({day_name_tr})

## 📊 Istatistikler

| Metrik | Deger |
|--------|-------|
| Toplam Task | {stats['total_tasks']} |
| Basarili | {stats['success_count']} ✅ |
| Basarisiz | {stats['failure_count']} ❌ |
| Basari Orani | %{stats['success_rate']:.1f} |
| Toplam Sure | {stats['total_duration_minutes']} dakika |

## ⭐ One Cikanlar

"""
        for highlight in highlights:
            md += f"- {highlight}\n"

        if not highlights:
            md += "- _Bu gun one cikan task yok_\n"

        md += "\n## 📚 Ogrenimler\n\n"
        for learning in learnings:
            md += f"- {learning}\n"

        if not learnings:
            md += "- _Bu gun kaydedilen ogrenim yok_\n"

        md += "\n## 🚧 Zorluklar\n\n"
        for challenge in challenges:
            md += f"- {challenge}\n"

        if not challenges:
            md += "- _Bu gun karsilasilan zorluk yok_ 🎉\n"

        # Task detaylari
        md += "\n## 📋 Task Detaylari\n\n"
        md += "| Task | Durum | Sure |\n"
        md += "|------|-------|------|\n"

        for task in tasks:
            status_icon = {"success": "✅", "failure": "❌", "partial": "⚠️"}.get(
                task.status, "❓"
            )
            md += f"| {task.title[:40]} | {status_icon} | {task.duration_minutes} dk |\n"

        # Footer
        md += f"""
---
_Olusturulma: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_
_Claude Diary Plugin v1.0_
"""
        return md

    def _get_turkish_day_name(self, d: date) -> str:
        """Turkce gun adi getir"""
        days = ["Pazartesi", "Sali", "Carsamba", "Persembe", "Cuma", "Cumartesi", "Pazar"]
        return days[d.weekday()]

    # =========================================================================
    # REQ-1.6: File Persistence
    # =========================================================================

    def get_file_path(self, entry_date: date) -> str:
        """
        Dosya yolunu olustur (REQ-1.6).

        Format: .kiro/diary/YYYY-MM-DD.md

        Args:
            entry_date: date - Kayit tarihi

        Returns:
            str - Dosya yolu
        """
        return str(self.diary_base_path / f"{entry_date.strftime('%Y-%m-%d')}.md")

    async def persist_to_file(
        self,
        markdown_content: str,
        file_path: str
    ) -> bool:
        """
        Markdown icerigi dosyaya kaydet (REQ-1.6).

        Args:
            markdown_content: str - Markdown icerik
            file_path: str - Dosya yolu

        Returns:
            bool - Basari durumu
        """
        try:
            # Dizin olustur
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            # Dosyaya yaz
            with open(path, "w", encoding="utf-8") as f:
                f.write(markdown_content)

            return True
        except Exception:
            return False

    # =========================================================================
    # Main Methods: Generate Summary
    # =========================================================================

    async def generate_summary(
        self,
        user_id: UUID,
        entry_date: date,
        tasks: list[TaskSummary],
        persist_file: bool = True,
    ) -> DiaryEntry:
        """
        Gunluk ozet olustur ve kaydet.

        Args:
            user_id: UUID - Kullanici ID
            entry_date: date - Kayit tarihi
            tasks: List[TaskSummary] - Task listesi
            persist_file: bool - Dosyaya kaydet (default: True)

        Returns:
            DiaryEntry - Olusturulan kayit
        """
        # Istatistikleri hesapla
        stats = self.aggregate_tasks(tasks)

        # Icerikleri cikar
        highlights = self.select_highlights(tasks)
        learnings = self.extract_learnings(tasks)
        challenges = self.extract_challenges(tasks)

        # Markdown olustur
        markdown_content = self.format_markdown(
            entry_date=entry_date,
            stats=stats,
            highlights=highlights,
            learnings=learnings,
            challenges=challenges,
            tasks=tasks,
        )

        # Dosya yolu
        file_path = self.get_file_path(entry_date)

        # Veritabanina kaydet
        entry = DiaryEntry(
            user_id=user_id,
            date=entry_date,
            success_count=stats["success_count"],
            failure_count=stats["failure_count"],
            total_tasks=stats["total_tasks"],
            total_duration_minutes=stats["total_duration_minutes"],
            highlights=highlights,
            learnings=learnings,
            challenges=challenges,
            tasks_data=[t.model_dump() for t in tasks],
            markdown_content=markdown_content,
            file_path=file_path if persist_file else None,
        )

        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)

        # Dosyaya kaydet
        if persist_file:
            await self.persist_to_file(markdown_content, file_path)

        return entry

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    async def get_summary(
        self,
        user_id: UUID,
        entry_date: date
    ) -> DiaryEntry | None:
        """
        Belirli bir tarihin ozetini getir.

        Args:
            user_id: UUID - Kullanici ID
            entry_date: date - Kayit tarihi

        Returns:
            Optional[DiaryEntry] - Kayit veya None
        """
        query = select(DiaryEntry).where(
            and_(
                DiaryEntry.user_id == user_id,
                DiaryEntry.date == entry_date
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_today_summary(self, user_id: UUID) -> DiaryEntry | None:
        """
        Bugunun ozetini getir.

        Args:
            user_id: UUID - Kullanici ID

        Returns:
            Optional[DiaryEntry] - Kayit veya None
        """
        return await self.get_summary(user_id, date.today())

    async def get_summaries(
        self,
        user_id: UUID,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 30,
    ) -> list[DiaryEntry]:
        """
        Ozet listesi getir.

        Args:
            user_id: UUID - Kullanici ID
            start_date: Optional[date] - Baslangic tarihi
            end_date: Optional[date] - Bitis tarihi
            limit: int - Maksimum kayit sayisi

        Returns:
            List[DiaryEntry] - Kayit listesi
        """
        conditions = [DiaryEntry.user_id == user_id]

        if start_date:
            conditions.append(DiaryEntry.date >= start_date)
        if end_date:
            conditions.append(DiaryEntry.date <= end_date)

        query = (
            select(DiaryEntry)
            .where(and_(*conditions))
            .order_by(desc(DiaryEntry.date))
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_summary(
        self,
        entry_id: UUID,
        highlights: list[str] | None = None,
        learnings: list[str] | None = None,
        challenges: list[str] | None = None,
    ) -> DiaryEntry | None:
        """
        Ozeti guncelle.

        Args:
            entry_id: UUID - Kayit ID
            highlights: Optional[List[str]] - Yeni highlights
            learnings: Optional[List[str]] - Yeni learnings
            challenges: Optional[List[str]] - Yeni challenges

        Returns:
            Optional[DiaryEntry] - Guncellenmis kayit veya None
        """
        query = select(DiaryEntry).where(DiaryEntry.id == entry_id)
        result = await self.db.execute(query)
        entry = result.scalar_one_or_none()

        if not entry:
            return None

        if highlights is not None:
            entry.highlights = highlights
        if learnings is not None:
            entry.learnings = learnings
        if challenges is not None:
            entry.challenges = challenges

        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def delete_summary(self, entry_id: UUID) -> bool:
        """
        Ozeti sil.

        Args:
            entry_id: UUID - Kayit ID

        Returns:
            bool - Basari durumu
        """
        query = select(DiaryEntry).where(DiaryEntry.id == entry_id)
        result = await self.db.execute(query)
        entry = result.scalar_one_or_none()

        if not entry:
            return False

        await self.db.delete(entry)
        await self.db.commit()
        return True

    # =========================================================================
    # Statistics
    # =========================================================================

    async def get_weekly_stats(
        self,
        user_id: UUID,
        week_start: date
    ) -> dict[str, Any]:
        """
        Haftalik istatistikleri getir.

        Args:
            user_id: UUID - Kullanici ID
            week_start: date - Hafta baslangici

        Returns:
            Dict - Haftalik istatistikler
        """
        from datetime import timedelta

        week_end = week_start + timedelta(days=6)
        entries = await self.get_summaries(
            user_id=user_id,
            start_date=week_start,
            end_date=week_end,
        )

        total_success = sum(e.success_count for e in entries)
        total_failure = sum(e.failure_count for e in entries)
        total_tasks = sum(e.total_tasks for e in entries)
        total_duration = sum(e.total_duration_minutes for e in entries)

        return {
            "week_start": week_start,
            "week_end": week_end,
            "days_logged": len(entries),
            "total_tasks": total_tasks,
            "total_success": total_success,
            "total_failure": total_failure,
            "success_rate": (total_success / total_tasks * 100) if total_tasks > 0 else 0,
            "total_duration_minutes": total_duration,
            "avg_tasks_per_day": total_tasks / 7,
            "all_highlights": [h for e in entries for h in e.highlights],
            "all_learnings": [l for e in entries for l in e.learnings],
        }
