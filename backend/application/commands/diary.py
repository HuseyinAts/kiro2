import logging
from typing import Any
from uuid import UUID
from datetime import date, datetime
from pydantic import ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from sqlalchemy import select

from core.cqrs.base import Command, CommandHandler
from api.schemas.diary import (
    DiaryEntryCreate, DiaryEntryResponse, DiaryEntryUpdate,
    GoalCreate, GoalProgressUpdate, GoalResponse, GoalUpdate, GoalRiskResponse,
    InsightResponse,
    ReflectionCreate, ReflectionResponse,
    LearningEntryCreate, LearningEntryResponse, LearningReviewResponse,
    EmotionalStateCreate, EmotionalStateResponse,
    ExportRequest, ExportResponse, ShareLinkCreate, ShareLinkResponse,
    SuccessResponse, MilestoneResponse
)
from models.diary import DiaryEntry, Goal, Insight, Reflection, LearningEntry, DiaryExport
from services.diary_service import DiaryService
from services.goal_service import GoalService
from services.insight_service import InsightService
from services.reflection_service import ReflectionService
from services.learning_journal_service import LearningJournalService
from services.emotional_service import EmotionalService
from services.export_service import ExportService

logger = logging.getLogger(__name__)

async def _verify_ownership(db: AsyncSession, model_class, entity_id: UUID, user_id: UUID, label: str = "Kayit"):
    query = select(model_class.user_id).where(model_class.id == entity_id)
    result = await db.execute(query)
    owner_id = result.scalar_one_or_none()
    if owner_id is None:
        raise HTTPException(status_code=404, detail=f"{label} bulunamadi")
    if str(owner_id) != str(user_id):
        raise HTTPException(status_code=403, detail="Bu veriye erisim yetkiniz yok")

def _diary_entry_to_response(entry) -> DiaryEntryResponse:
    return DiaryEntryResponse(
        id=entry.id,
        user_id=entry.user_id,
        date=entry.date,
        success_count=entry.success_count,
        failure_count=entry.failure_count,
        total_tasks=entry.total_tasks,
        total_duration_minutes=entry.total_duration_minutes,
        highlights=entry.highlights or [],
        learnings=entry.learnings or [],
        challenges=entry.challenges or [],
        markdown_content=entry.markdown_content,
        file_path=entry.file_path,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        success_rate=entry.success_rate,
    )

def _goal_to_response(goal) -> GoalResponse:
    milestones = []
    for m in goal.milestones or []:
        milestones.append(
            MilestoneResponse(
                percentage=m.get("percentage", 0),
                title=m.get("title", ""),
                achieved=m.get("achieved", False),
                achieved_at=m.get("achieved_at"),
            )
        )
    return GoalResponse(
        id=goal.id, user_id=goal.user_id, title=goal.title, description=goal.description,
        progress=goal.progress, current_value=goal.current_value, target_value=goal.target_value,
        unit=goal.unit, status=goal.status, milestones=milestones, is_at_risk=goal.is_at_risk,
        risk_factors=goal.risk_factors or [], velocity=goal.velocity, predicted_completion=goal.predicted_completion,
        start_date=goal.start_date, target_date=goal.target_date, completed_at=goal.completed_at,
        category=goal.category, priority=goal.priority, days_remaining=getattr(goal, "days_remaining", 0),
        created_at=goal.created_at, updated_at=goal.updated_at,
    )

def _insight_to_response(insight) -> InsightResponse:
    return InsightResponse(
        id=insight.id, diary_entry_id=insight.diary_entry_id, user_id=insight.user_id,
        category=insight.category, pattern=insight.pattern, confidence=insight.confidence,
        evidence_count=insight.evidence_count, recommendation=insight.recommendation, priority=insight.priority,
        root_cause=insight.root_cause, correlation=insight.correlation, created_at=insight.created_at,
    )

def _reflection_to_response(reflection) -> ReflectionResponse:
    return ReflectionResponse(
        id=reflection.id, diary_entry_id=reflection.diary_entry_id, user_id=reflection.user_id,
        what_went_well=reflection.what_went_well, what_could_improve=reflection.what_could_improve,
        what_did_i_learn=reflection.what_did_i_learn, what_will_i_do_differently=reflection.what_will_i_do_differently,
        additional_notes=reflection.additional_notes, depth=reflection.depth, depth_score=reflection.depth_score,
        extracted_learnings=reflection.extracted_learnings or [], action_items=reflection.action_items or [],
        created_at=reflection.created_at, updated_at=reflection.updated_at,
    )

def _learning_to_response(entry) -> LearningEntryResponse:
    return LearningEntryResponse(
        id=entry.id, user_id=entry.user_id, title=entry.title, content=entry.content, summary=entry.summary,
        tags=entry.tags or [], domain=entry.domain, skill_type=entry.skill_type, related_concepts=entry.related_concepts or [],
        next_review=entry.next_review, review_count=entry.review_count, retention_score=entry.retention_score,
        mastery_level=entry.mastery_level, importance=entry.importance, created_at=entry.created_at, updated_at=entry.updated_at,
    )

def _emotional_to_response(state) -> EmotionalStateResponse:
    return EmotionalStateResponse(
        id=state.id, user_id=state.user_id, timestamp=state.timestamp, confidence_level=state.confidence_level,
        frustration_score=state.frustration_score, retry_count=state.retry_count, error_count=state.error_count,
        flow_state=state.flow_state, productivity_score=state.productivity_score, tasks_completed=state.tasks_completed,
        task_type=state.task_type, trigger_factors=state.trigger_factors or {}, self_awareness_score=state.self_awareness_score,
    )

# SUMMARY COMMANDS
class CreateSummaryCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    request: DiaryEntryCreate
    persist_file: bool
    user_id: UUID
    db: Any

class CreateSummaryCommandHandler(CommandHandler[CreateSummaryCommand, DiaryEntryResponse]):
    async def handle(self, command: CreateSummaryCommand) -> DiaryEntryResponse:
        service = DiaryService(command.db)
        existing = await service.get_summary(command.user_id, command.request.date)
        if existing:
            raise HTTPException(status_code=400, detail=f"{command.request.date} tarihi icin kayit zaten mevcut")
        entry = await service.generate_summary(user_id=command.user_id, entry_date=command.request.date, tasks=command.request.tasks, persist_file=command.persist_file)
        return _diary_entry_to_response(entry)

class UpdateSummaryCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    entry_id: UUID
    request: DiaryEntryUpdate
    user_id: UUID
    db: Any

class UpdateSummaryCommandHandler(CommandHandler[UpdateSummaryCommand, DiaryEntryResponse]):
    async def handle(self, command: UpdateSummaryCommand) -> DiaryEntryResponse:
        await _verify_ownership(command.db, DiaryEntry, command.entry_id, command.user_id, "Ozet")
        service = DiaryService(command.db)
        entry = await service.update_summary(command.entry_id, highlights=command.request.highlights, learnings=command.request.learnings, challenges=command.request.challenges)
        if not entry: raise HTTPException(status_code=404, detail="Kayit bulunamadi")
        return _diary_entry_to_response(entry)

class DeleteSummaryCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    entry_id: UUID
    user_id: UUID
    db: Any

class DeleteSummaryCommandHandler(CommandHandler[DeleteSummaryCommand, SuccessResponse]):
    async def handle(self, command: DeleteSummaryCommand) -> SuccessResponse:
        await _verify_ownership(command.db, DiaryEntry, command.entry_id, command.user_id, "Ozet")
        service = DiaryService(command.db)
        deleted = await service.delete_summary(command.entry_id)
        if not deleted: raise HTTPException(status_code=404, detail="Kayit bulunamadi")
        return SuccessResponse(success=True, message="Kayit silindi")

# GOAL COMMANDS
class CreateGoalCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    request: GoalCreate
    user_id: UUID
    db: Any

class CreateGoalCommandHandler(CommandHandler[CreateGoalCommand, GoalResponse]):
    async def handle(self, command: CreateGoalCommand) -> GoalResponse:
        service = GoalService(command.db)
        smart_result = service.validate_smart(command.request)
        if not smart_result["is_valid"]:
            raise HTTPException(status_code=400, detail={"message": "SMART kriterleri karsilanmiyor", "missing": smart_result["missing"], "warnings": smart_result["warnings"]})
        goal = await service.create_goal(command.user_id, command.request)
        return _goal_to_response(goal)

class UpdateGoalCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    goal_id: UUID
    request: GoalUpdate
    user_id: UUID
    db: Any

class UpdateGoalCommandHandler(CommandHandler[UpdateGoalCommand, GoalResponse]):
    async def handle(self, command: UpdateGoalCommand) -> GoalResponse:
        await _verify_ownership(command.db, Goal, command.goal_id, command.user_id, "Hedef")
        service = GoalService(command.db)
        goal = await service.update_goal(command.goal_id, command.request)
        if not goal: raise HTTPException(status_code=404, detail="Hedef bulunamadi")
        return _goal_to_response(goal)

class UpdateGoalProgressCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    goal_id: UUID
    request: GoalProgressUpdate
    user_id: UUID
    db: Any

class UpdateGoalProgressCommandHandler(CommandHandler[UpdateGoalProgressCommand, dict[str, Any]]):
    async def handle(self, command: UpdateGoalProgressCommand) -> dict[str, Any]:
        await _verify_ownership(command.db, Goal, command.goal_id, command.user_id, "Hedef")
        service = GoalService(command.db)
        result = await service.update_progress(command.goal_id, command.request)
        if not result: raise HTTPException(status_code=404, detail="Hedef bulunamadi")
        return {
            "success": True,
            "goal": _goal_to_response(result["goal"]),
            "old_progress": result["old_progress"],
            "new_progress": result["new_progress"],
            "celebrations": result["celebrations"],
            "risk": {
                "is_at_risk": result["risk"].is_at_risk,
                "risk_level": result["risk"].risk_level,
                "risk_factors": result["risk"].risk_factors,
                "recommendations": result["risk"].recommendations,
            }
        }

class AdjustGoalCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    goal_id: UUID
    reason: str
    new_target_value: float | None
    new_target_date: datetime | None
    user_id: UUID
    db: Any

class AdjustGoalCommandHandler(CommandHandler[AdjustGoalCommand, GoalResponse]):
    async def handle(self, command: AdjustGoalCommand) -> GoalResponse:
        await _verify_ownership(command.db, Goal, command.goal_id, command.user_id, "Hedef")
        service = GoalService(command.db)
        goal = await service.adjust_goal(command.goal_id, command.reason, command.new_target_value, command.new_target_date)
        if not goal: raise HTTPException(status_code=404, detail="Hedef bulunamadi")
        return _goal_to_response(goal)

class CreateGoalRetrospectiveCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    goal_id: UUID
    lessons_learned: list[str]
    success_factors: list[str]
    challenges_faced: list[str]
    user_id: UUID
    db: Any

class CreateGoalRetrospectiveCommandHandler(CommandHandler[CreateGoalRetrospectiveCommand, GoalResponse]):
    async def handle(self, command: CreateGoalRetrospectiveCommand) -> GoalResponse:
        await _verify_ownership(command.db, Goal, command.goal_id, command.user_id, "Hedef")
        service = GoalService(command.db)
        goal = await service.create_retrospective(command.goal_id, command.lessons_learned, command.success_factors, command.challenges_faced)
        if not goal: raise HTTPException(status_code=404, detail="Hedef bulunamadi")
        return _goal_to_response(goal)

class DeleteGoalCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    goal_id: UUID
    user_id: UUID
    db: Any

class DeleteGoalCommandHandler(CommandHandler[DeleteGoalCommand, SuccessResponse]):
    async def handle(self, command: DeleteGoalCommand) -> SuccessResponse:
        await _verify_ownership(command.db, Goal, command.goal_id, command.user_id, "Hedef")
        service = GoalService(command.db)
        deleted = await service.delete_goal(command.goal_id)
        if not deleted: raise HTTPException(status_code=404, detail="Hedef bulunamadi")
        return SuccessResponse(success=True, message="Hedef silindi")

# INSIGHT COMMANDS
class AnalyzeEntriesForInsightsCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    start_date: date | None
    end_date: date | None
    user_id: UUID
    db: Any

class AnalyzeEntriesForInsightsCommandHandler(CommandHandler[AnalyzeEntriesForInsightsCommand, list[InsightResponse]]):
    async def handle(self, command: AnalyzeEntriesForInsightsCommand) -> list[InsightResponse]:
        service = InsightService(command.db)
        insights = await service.analyze_and_generate_insights(command.user_id, command.start_date, command.end_date)
        return [_insight_to_response(i) for i in insights]

class DeleteInsightCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    insight_id: UUID
    user_id: UUID
    db: Any

class DeleteInsightCommandHandler(CommandHandler[DeleteInsightCommand, SuccessResponse]):
    async def handle(self, command: DeleteInsightCommand) -> SuccessResponse:
        await _verify_ownership(command.db, Insight, command.insight_id, command.user_id, "Insight")
        service = InsightService(command.db)
        deleted = await service.delete_insight(command.insight_id)
        if not deleted: raise HTTPException(status_code=404, detail="Insight bulunamadi")
        return SuccessResponse(success=True, message="Insight silindi")

# REFLECTION COMMANDS
class CreateReflectionCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    request: ReflectionCreate
    user_id: UUID
    db: Any

class CreateReflectionCommandHandler(CommandHandler[CreateReflectionCommand, ReflectionResponse]):
    async def handle(self, command: CreateReflectionCommand) -> ReflectionResponse:
        service = ReflectionService(command.db)
        reflection = await service.create_reflection(command.user_id, command.request)
        return _reflection_to_response(reflection)

# LEARNING COMMANDS
class CreateLearningEntryCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    request: LearningEntryCreate
    user_id: UUID
    db: Any

class CreateLearningEntryCommandHandler(CommandHandler[CreateLearningEntryCommand, LearningEntryResponse]):
    async def handle(self, command: CreateLearningEntryCommand) -> LearningEntryResponse:
        service = LearningJournalService(command.db)
        entry = await service.create_entry(command.user_id, command.request)
        return _learning_to_response(entry)

class RecordReviewCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    entry_id: UUID
    remembered: bool
    quality: int
    user_id: UUID
    db: Any

class RecordReviewCommandHandler(CommandHandler[RecordReviewCommand, LearningReviewResponse]):
    async def handle(self, command: RecordReviewCommand) -> LearningReviewResponse:
        await _verify_ownership(command.db, LearningEntry, command.entry_id, command.user_id, "Ogrenme kaydi")
        service = LearningJournalService(command.db)
        result = await service.record_review(command.entry_id, command.remembered, command.quality)
        if not result: raise HTTPException(status_code=404, detail="Ogrenme kaydi bulunamadi")
        return LearningReviewResponse(
            entry_id=result["entry_id"], next_review=result["next_review"],
            new_interval_days=result["new_interval_days"], retention_score=result["retention_score"],
            mastery_level=result["mastery_level"]
        )

class LinkConceptsCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    entry_id: UUID
    concepts: list[str]
    user_id: UUID
    db: Any

class LinkConceptsCommandHandler(CommandHandler[LinkConceptsCommand, SuccessResponse]):
    async def handle(self, command: LinkConceptsCommand) -> SuccessResponse:
        await _verify_ownership(command.db, LearningEntry, command.entry_id, command.user_id, "Ogrenme kaydi")
        service = LearningJournalService(command.db)
        result = await service.link_concepts(command.entry_id, command.concepts)
        if not result: raise HTTPException(status_code=404, detail="Ogrenme kaydi bulunamadi")
        return SuccessResponse(success=True, message=f"{len(command.concepts)} kavram baglandi")

# EMOTIONAL COMMANDS
class TrackEmotionalStateCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    request: EmotionalStateCreate
    user_id: UUID
    db: Any

class TrackEmotionalStateCommandHandler(CommandHandler[TrackEmotionalStateCommand, EmotionalStateResponse]):
    async def handle(self, command: TrackEmotionalStateCommand) -> EmotionalStateResponse:
        service = EmotionalService(command.db)
        state = await service.track_state(command.user_id, command.request)
        return _emotional_to_response(state)

# EXPORT COMMANDS
class CreateExportCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    request: ExportRequest
    user_id: UUID
    db: Any

class CreateExportCommandHandler(CommandHandler[CreateExportCommand, ExportResponse]):
    async def handle(self, command: CreateExportCommand) -> ExportResponse:
        service = ExportService(command.db)
        export = await service.export(command.user_id, command.request)
        return ExportResponse(
            id=export.id, user_id=export.user_id, format=export.format, date_from=export.date_from,
            date_to=export.date_to, file_path=export.file_path, file_size=export.file_size,
            privacy_filter_applied=export.privacy_filter_applied, created_at=export.created_at
        )

class CreateShareLinkCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    request: ShareLinkCreate
    user_id: UUID
    db: Any

class CreateShareLinkCommandHandler(CommandHandler[CreateShareLinkCommand, ShareLinkResponse]):
    async def handle(self, command: CreateShareLinkCommand) -> ShareLinkResponse:
        service = ExportService(command.db)
        share = await service.create_share_link(command.user_id, command.request.export_id, command.request.expires_in_days)
        if not share: raise HTTPException(status_code=404, detail="Export bulunamadi")
        return ShareLinkResponse(
            export_id=share["export_id"], share_token=share["share_token"],
            share_url=share["share_url"], expires_at=share["expires_at"]
        )

class CreateEncryptedBackupCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    password: str
    user_id: UUID
    db: Any

class CreateEncryptedBackupCommandHandler(CommandHandler[CreateEncryptedBackupCommand, dict[str, Any]]):
    async def handle(self, command: CreateEncryptedBackupCommand) -> dict[str, Any]:
        service = ExportService(command.db)
        backup = await service.create_encrypted_backup(command.user_id, command.password)
        return {
            "success": True, "backup_id": str(backup["backup_id"]), "file_size": backup["file_size"],
            "created_at": backup["created_at"].isoformat(), "encryption": "AES-256-GCM",
            "warning": "Sifreyi kaybederseniz yedege erisemezsiniz!"
        }
