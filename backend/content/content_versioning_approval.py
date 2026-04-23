"""
KIRO2 Content Versioning and Approval System
Comprehensive version control and approval workflow system for educational content
Türkiye Üniversite Sınavları Hazırlık Platformu - İçerik Versiyonlama ve Onay Sistemi
"""

import asyncio
import copy
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from content.unified_content_management import (
    ContentItem,
    ContentStatus,
    ContentType,
)
from core.structured_logging import LogCategory, get_logger
from core.unified_config import get_unified_config

logger = get_logger(__name__, LogCategory.CONTENT)
config = get_unified_config()


class ApprovalStatus(Enum):
    """Approval workflow statuses"""

    PENDING_REVIEW = "pending_review"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_CHANGES = "requires_changes"
    APPROVED_WITH_CONDITIONS = "approved_with_conditions"


class ReviewerRole(Enum):
    """Roles that can review content"""

    CONTENT_REVIEWER = "content_reviewer"
    SUBJECT_EXPERT = "subject_expert"
    EDUCATIONAL_SPECIALIST = "educational_specialist"
    TECHNICAL_REVIEWER = "technical_reviewer"
    FINAL_APPROVER = "final_approver"
    QUALITY_ASSURANCE = "quality_assurance"


class ChangeType(Enum):
    """Types of changes in content versions"""

    MAJOR = "major"  # Breaking changes, requires full review
    MINOR = "minor"  # Small updates, requires limited review
    PATCH = "patch"  # Bug fixes, minimal review
    EDITORIAL = "editorial"  # Text corrections, no content review needed


class WorkflowStage(Enum):
    """Approval workflow stages"""

    CONTENT_REVIEW = "content_review"
    TECHNICAL_REVIEW = "technical_review"
    EDUCATIONAL_REVIEW = "educational_review"
    QUALITY_ASSURANCE = "quality_assurance"
    FINAL_APPROVAL = "final_approval"


@dataclass
class ContentVersion:
    """Version of content with metadata"""

    version_id: str
    content_id: str
    version_number: str

    # Version data
    content_snapshot: ContentItem
    change_summary: str
    change_type: ChangeType

    # Version metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    created_by: int = 0
    parent_version_id: str | None = None

    # Change tracking
    changes_from_parent: dict[str, Any] = field(default_factory=dict)
    affected_files: list[str] = field(default_factory=list)

    # Review and approval
    approval_status: ApprovalStatus = ApprovalStatus.PENDING_REVIEW
    review_comments: list[dict[str, Any]] = field(default_factory=list)
    approved_by: int | None = None
    approved_at: datetime | None = None

    # Publishing
    is_published: bool = False
    published_at: datetime | None = None
    published_by: int | None = None

    # Turkish localization
    change_summary_tr: str | None = None

    def __post_init__(self):
        if not self.version_id:
            self.version_id = str(uuid.uuid4())
        if not self.change_summary_tr:
            self.change_summary_tr = self.change_summary

    def add_review_comment(
        self,
        reviewer_id: int,
        reviewer_role: ReviewerRole,
        comment: str,
        comment_type: str = "general",
    ) -> None:
        """Add review comment"""
        review_comment = {
            "comment_id": str(uuid.uuid4()),
            "reviewer_id": reviewer_id,
            "reviewer_role": reviewer_role.value,
            "comment": comment,
            "comment_type": comment_type,
            "timestamp": datetime.now(UTC).isoformat(),
            "resolved": False,
        }
        self.review_comments.append(review_comment)

    def approve_version(self, approver_id: int) -> None:
        """Approve this version"""
        self.approval_status = ApprovalStatus.APPROVED
        self.approved_by = approver_id
        self.approved_at = datetime.now(UTC)

    def reject_version(self, reviewer_id: int, reason: str) -> None:
        """Reject this version"""
        self.approval_status = ApprovalStatus.REJECTED
        self.add_review_comment(
            reviewer_id, ReviewerRole.CONTENT_REVIEWER, reason, "rejection_reason"
        )

    def publish_version(self, publisher_id: int) -> None:
        """Publish this version"""
        if self.approval_status != ApprovalStatus.APPROVED:
            raise ValueError("Cannot publish non-approved version")

        self.is_published = True
        self.published_by = publisher_id
        self.published_at = datetime.now(UTC)

        # Update content item status
        self.content_snapshot.update_status(ContentStatus.PUBLISHED, publisher_id)

    def calculate_version_score(self) -> float:
        """Calculate version quality score based on reviews and metrics"""
        score = 0.0

        # Base score from approval status
        if self.approval_status == ApprovalStatus.APPROVED:
            score += 100
        elif self.approval_status == ApprovalStatus.APPROVED_WITH_CONDITIONS:
            score += 85
        elif self.approval_status == ApprovalStatus.REQUIRES_CHANGES:
            score += 60
        elif self.approval_status == ApprovalStatus.REJECTED:
            score += 20
        else:
            score += 40  # Pending or in review

        # Penalty for unresolved comments
        unresolved_comments = len(
            [c for c in self.review_comments if not c["resolved"]]
        )
        score -= unresolved_comments * 5

        # Bonus for quick approval
        if self.approved_at:
            review_duration = (self.approved_at - self.created_at).days
            if review_duration <= 1:
                score += 10
            elif review_duration <= 3:
                score += 5

        return max(0, min(100, score))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "version_id": self.version_id,
            "content_id": self.content_id,
            "version_number": self.version_number,
            "content_snapshot": self.content_snapshot.to_dict(),
            "change_summary": self.change_summary,
            "change_summary_tr": self.change_summary_tr,
            "change_type": self.change_type.value,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "parent_version_id": self.parent_version_id,
            "changes_from_parent": self.changes_from_parent,
            "affected_files": self.affected_files,
            "approval_status": self.approval_status.value,
            "review_comments": self.review_comments,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "is_published": self.is_published,
            "published_at": self.published_at.isoformat()
            if self.published_at
            else None,
            "published_by": self.published_by,
            "version_score": self.calculate_version_score(),
        }


@dataclass
class ApprovalWorkflow:
    """Approval workflow definition"""

    workflow_id: str
    name: str
    description: str

    # Workflow stages
    stages: list[WorkflowStage] = field(default_factory=list)
    stage_requirements: dict[WorkflowStage, dict[str, Any]] = field(
        default_factory=dict
    )

    # Reviewer assignments
    stage_reviewers: dict[WorkflowStage, list[ReviewerRole]] = field(
        default_factory=dict
    )
    required_approvals_per_stage: dict[WorkflowStage, int] = field(default_factory=dict)

    # Workflow settings
    auto_progression: bool = True
    parallel_review: bool = False
    deadline_days: int = 7

    # Content type applicability
    applicable_content_types: list[ContentType] = field(
        default_factory=lambda: list(ContentType)
    )
    applicable_change_types: list[ChangeType] = field(
        default_factory=lambda: list(ChangeType)
    )

    def __post_init__(self):
        if not self.workflow_id:
            self.workflow_id = str(uuid.uuid4())

        # Set default stages if none provided
        if not self.stages:
            self.stages = [
                WorkflowStage.CONTENT_REVIEW,
                WorkflowStage.TECHNICAL_REVIEW,
                WorkflowStage.EDUCATIONAL_REVIEW,
                WorkflowStage.QUALITY_ASSURANCE,
                WorkflowStage.FINAL_APPROVAL,
            ]

        # Set default requirements
        if not self.stage_requirements:
            self.stage_requirements = {
                WorkflowStage.CONTENT_REVIEW: {
                    "min_reviewers": 1,
                    "expertise_required": True,
                },
                WorkflowStage.TECHNICAL_REVIEW: {
                    "min_reviewers": 1,
                    "technical_expertise": True,
                },
                WorkflowStage.EDUCATIONAL_REVIEW: {
                    "min_reviewers": 1,
                    "educational_background": True,
                },
                WorkflowStage.QUALITY_ASSURANCE: {
                    "min_reviewers": 1,
                    "qa_certification": True,
                },
                WorkflowStage.FINAL_APPROVAL: {
                    "min_reviewers": 1,
                    "senior_approval": True,
                },
            }

    def get_next_stage(
        self, current_stage: WorkflowStage | None
    ) -> WorkflowStage | None:
        """Get next stage in workflow"""
        if not current_stage:
            return self.stages[0] if self.stages else None

        try:
            current_index = self.stages.index(current_stage)
            if current_index + 1 < len(self.stages):
                return self.stages[current_index + 1]
        except ValueError:
            pass

        return None

    def is_applicable_to_content(
        self, content_type: ContentType, change_type: ChangeType
    ) -> bool:
        """Check if workflow applies to content"""
        type_applicable = (
            not self.applicable_content_types
            or content_type in self.applicable_content_types
        )

        change_applicable = (
            not self.applicable_change_types
            or change_type in self.applicable_change_types
        )

        return type_applicable and change_applicable

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "stages": [stage.value for stage in self.stages],
            "stage_requirements": {
                stage.value: requirements
                for stage, requirements in self.stage_requirements.items()
            },
            "stage_reviewers": {
                stage.value: [role.value for role in roles]
                for stage, roles in self.stage_reviewers.items()
            },
            "required_approvals_per_stage": {
                stage.value: count
                for stage, count in self.required_approvals_per_stage.items()
            },
            "auto_progression": self.auto_progression,
            "parallel_review": self.parallel_review,
            "deadline_days": self.deadline_days,
            "applicable_content_types": [
                ct.value for ct in self.applicable_content_types
            ],
            "applicable_change_types": [
                ct.value for ct in self.applicable_change_types
            ],
        }


@dataclass
class ReviewTask:
    """Individual review task for a reviewer"""

    task_id: str
    version_id: str
    reviewer_id: int
    reviewer_role: ReviewerRole
    workflow_stage: WorkflowStage

    # Task properties
    assigned_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    due_date: datetime | None = None
    priority: str = "normal"  # low, normal, high, urgent

    # Task status
    status: str = "assigned"  # assigned, in_progress, completed, skipped
    completed_at: datetime | None = None

    # Review criteria
    review_checklist: list[dict[str, Any]] = field(default_factory=list)
    required_checks: list[str] = field(default_factory=list)

    # Turkish localization
    task_description_tr: str = ""

    def __post_init__(self):
        if not self.task_id:
            self.task_id = str(uuid.uuid4())

        # Set default due date (7 days from assignment)
        if not self.due_date:
            self.due_date = self.assigned_at + timedelta(days=7)

        # Set Turkish description
        if not self.task_description_tr:
            self.task_description_tr = (
                f"{self.workflow_stage.value} aşaması için içerik incelemesi"
            )

    def complete_task(self, review_data: dict[str, Any]) -> None:
        """Complete the review task"""
        self.status = "completed"
        self.completed_at = datetime.now(UTC)

        # Update checklist with review results
        for item in self.review_checklist:
            check_id = item.get("check_id")
            if check_id in review_data:
                item["completed"] = True
                item["result"] = review_data[check_id]
                item["notes"] = review_data.get(f"{check_id}_notes", "")

    def is_overdue(self) -> bool:
        """Check if task is overdue"""
        if not self.due_date or self.status == "completed":
            return False

        return datetime.now(UTC) > self.due_date

    def get_completion_percentage(self) -> float:
        """Get task completion percentage"""
        if self.status == "completed":
            return 100.0

        if not self.review_checklist:
            return 0.0

        completed_checks = len(
            [item for item in self.review_checklist if item.get("completed", False)]
        )
        return (completed_checks / len(self.review_checklist)) * 100

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "task_id": self.task_id,
            "version_id": self.version_id,
            "reviewer_id": self.reviewer_id,
            "reviewer_role": self.reviewer_role.value,
            "workflow_stage": self.workflow_stage.value,
            "assigned_at": self.assigned_at.isoformat(),
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "priority": self.priority,
            "status": self.status,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "review_checklist": self.review_checklist,
            "required_checks": self.required_checks,
            "task_description_tr": self.task_description_tr,
            "is_overdue": self.is_overdue(),
            "completion_percentage": self.get_completion_percentage(),
        }


class VersionManager:
    """Manages content versions and version control"""

    def __init__(self):
        self.versions: dict[str, ContentVersion] = {}
        self.content_versions: dict[str, list[str]] = {}  # content_id -> version_ids
        self.published_versions: dict[
            str, str
        ] = {}  # content_id -> published_version_id

    async def create_version(
        self,
        content_item: ContentItem,
        change_summary: str,
        change_type: ChangeType,
        created_by: int,
        parent_version_id: str | None = None,
    ) -> ContentVersion:
        """Create new version of content"""

        # Generate version number
        existing_versions = self.content_versions.get(content_item.content_id, [])
        version_number = self._generate_version_number(existing_versions, change_type)

        # Create content snapshot
        content_snapshot = copy.deepcopy(content_item)
        content_snapshot.version = version_number

        # Calculate changes from parent
        changes_from_parent = {}
        if parent_version_id:
            parent_version = self.versions.get(parent_version_id)
            if parent_version:
                changes_from_parent = self._calculate_changes(
                    parent_version.content_snapshot, content_snapshot
                )

        # Create version
        version = ContentVersion(
            version_id=str(uuid.uuid4()),
            content_id=content_item.content_id,
            version_number=version_number,
            content_snapshot=content_snapshot,
            change_summary=change_summary,
            change_type=change_type,
            created_by=created_by,
            parent_version_id=parent_version_id,
            changes_from_parent=changes_from_parent,
        )

        # Store version
        self.versions[version.version_id] = version

        # Update content versions list
        if content_item.content_id not in self.content_versions:
            self.content_versions[content_item.content_id] = []
        self.content_versions[content_item.content_id].append(version.version_id)

        logger.info(
            f"Created version {version_number} for content {content_item.content_id}"
        )
        return version

    def _generate_version_number(
        self, existing_versions: list[str], change_type: ChangeType
    ) -> str:
        """Generate new version number based on change type"""
        if not existing_versions:
            return "1.0.0"

        # Get latest version
        latest_version_id = existing_versions[-1]
        latest_version = self.versions.get(latest_version_id)

        if not latest_version:
            return "1.0.0"

        # Parse current version number
        try:
            parts = latest_version.version_number.split(".")
            major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        except (ValueError, IndexError):
            return "1.0.0"

        # Increment based on change type
        if change_type == ChangeType.MAJOR:
            major += 1
            minor = 0
            patch = 0
        elif change_type == ChangeType.MINOR:
            minor += 1
            patch = 0
        else:  # PATCH or EDITORIAL
            patch += 1

        return f"{major}.{minor}.{patch}"

    def _calculate_changes(
        self, old_content: ContentItem, new_content: ContentItem
    ) -> dict[str, Any]:
        """Calculate changes between two content versions"""
        changes = {}

        # Compare metadata
        old_meta = old_content.metadata.to_dict()
        new_meta = new_content.metadata.to_dict()

        for key, new_value in new_meta.items():
            old_value = old_meta.get(key)
            if old_value != new_value:
                changes[f"metadata.{key}"] = {
                    "old_value": old_value,
                    "new_value": new_value,
                }

        # Compare content data
        for key, new_value in new_content.content_data.items():
            old_value = old_content.content_data.get(key)
            if old_value != new_value:
                changes[f"content_data.{key}"] = {
                    "old_value": old_value,
                    "new_value": new_value,
                }

        # Compare files
        old_file_ids = {f.file_id for f in old_content.files}
        new_file_ids = {f.file_id for f in new_content.files}

        if old_file_ids != new_file_ids:
            changes["files"] = {
                "added": list(new_file_ids - old_file_ids),
                "removed": list(old_file_ids - new_file_ids),
            }

        return changes

    async def get_version(self, version_id: str) -> ContentVersion | None:
        """Get specific version"""
        return self.versions.get(version_id)

    async def get_content_versions(self, content_id: str) -> list[ContentVersion]:
        """Get all versions of content"""
        version_ids = self.content_versions.get(content_id, [])
        return [self.versions[vid] for vid in version_ids if vid in self.versions]

    async def get_latest_version(self, content_id: str) -> ContentVersion | None:
        """Get latest version of content"""
        versions = await self.get_content_versions(content_id)
        if not versions:
            return None

        # Sort by creation date
        versions.sort(key=lambda v: v.created_at, reverse=True)
        return versions[0]

    async def get_published_version(self, content_id: str) -> ContentVersion | None:
        """Get published version of content"""
        published_version_id = self.published_versions.get(content_id)
        if published_version_id:
            return self.versions.get(published_version_id)
        return None

    async def publish_version(self, version_id: str, publisher_id: int) -> bool:
        """Publish a version"""
        version = self.versions.get(version_id)
        if not version:
            return False

        try:
            version.publish_version(publisher_id)
            self.published_versions[version.content_id] = version_id
            logger.info(f"Published version {version_id}")
            return True
        except ValueError as e:
            logger.error(f"Failed to publish version {version_id}: {e}")
            return False

    async def compare_versions(
        self, version_id1: str, version_id2: str
    ) -> dict[str, Any]:
        """Compare two versions and return differences"""
        version1 = self.versions.get(version_id1)
        version2 = self.versions.get(version_id2)

        if not version1 or not version2:
            return {"error": "One or both versions not found"}

        changes = self._calculate_changes(
            version1.content_snapshot, version2.content_snapshot
        )

        return {
            "version1": {
                "version_id": version1.version_id,
                "version_number": version1.version_number,
                "created_at": version1.created_at.isoformat(),
                "created_by": version1.created_by,
            },
            "version2": {
                "version_id": version2.version_id,
                "version_number": version2.version_number,
                "created_at": version2.created_at.isoformat(),
                "created_by": version2.created_by,
            },
            "changes": changes,
            "summary": self._generate_change_summary(changes),
        }

    def _generate_change_summary(self, changes: dict[str, Any]) -> dict[str, Any]:
        """Generate human-readable change summary"""
        summary = {
            "total_changes": len(changes),
            "categories": {"metadata": 0, "content": 0, "files": 0},
            "major_changes": [],
            "minor_changes": [],
        }

        for key, change in changes.items():
            if key.startswith("metadata."):
                summary["categories"]["metadata"] += 1
            elif key.startswith("content_data."):
                summary["categories"]["content"] += 1
            elif key == "files":
                summary["categories"]["files"] += 1

            # Categorize change importance
            if key in ["metadata.title", "content_data.question_text", "files"]:
                summary["major_changes"].append(key)
            else:
                summary["minor_changes"].append(key)

        return summary


class ApprovalWorkflowManager:
    """Manages approval workflows and review processes"""

    def __init__(self, version_manager: VersionManager):
        self.version_manager = version_manager
        self.workflows: dict[str, ApprovalWorkflow] = {}
        self.active_reviews: dict[
            str, dict[str, Any]
        ] = {}  # version_id -> review_state
        self.review_tasks: dict[str, ReviewTask] = {}
        self.reviewer_assignments: dict[int, list[ReviewerRole]] = {}

        # Initialize default workflows
        self._initialize_default_workflows()

    def _initialize_default_workflows(self) -> None:
        """Initialize default approval workflows"""
        # Standard content workflow
        standard_workflow = ApprovalWorkflow(
            workflow_id="standard_content",
            name="Standard Content Review",
            description="Standard approval workflow for educational content",
            stages=[
                WorkflowStage.CONTENT_REVIEW,
                WorkflowStage.EDUCATIONAL_REVIEW,
                WorkflowStage.FINAL_APPROVAL,
            ],
            applicable_content_types=[
                ContentType.QUESTION,
                ContentType.DOCUMENT,
                ContentType.QUIZ,
            ],
            applicable_change_types=[ChangeType.MINOR, ChangeType.PATCH],
        )

        # Major change workflow
        major_workflow = ApprovalWorkflow(
            workflow_id="major_content",
            name="Major Content Review",
            description="Comprehensive review for major content changes",
            stages=[
                WorkflowStage.CONTENT_REVIEW,
                WorkflowStage.TECHNICAL_REVIEW,
                WorkflowStage.EDUCATIONAL_REVIEW,
                WorkflowStage.QUALITY_ASSURANCE,
                WorkflowStage.FINAL_APPROVAL,
            ],
            applicable_change_types=[ChangeType.MAJOR],
            deadline_days=14,
        )

        # Multimedia content workflow
        multimedia_workflow = ApprovalWorkflow(
            workflow_id="multimedia_content",
            name="Multimedia Content Review",
            description="Specialized workflow for multimedia content",
            stages=[
                WorkflowStage.CONTENT_REVIEW,
                WorkflowStage.TECHNICAL_REVIEW,
                WorkflowStage.EDUCATIONAL_REVIEW,
                WorkflowStage.FINAL_APPROVAL,
            ],
            applicable_content_types=[
                ContentType.VIDEO,
                ContentType.AUDIO,
                ContentType.INTERACTIVE,
            ],
            deadline_days=10,
        )

        # Quick approval workflow
        quick_workflow = ApprovalWorkflow(
            workflow_id="quick_approval",
            name="Quick Approval",
            description="Fast-track approval for editorial changes",
            stages=[WorkflowStage.CONTENT_REVIEW, WorkflowStage.FINAL_APPROVAL],
            applicable_change_types=[ChangeType.EDITORIAL],
            deadline_days=3,
        )

        # Store workflows
        for workflow in [
            standard_workflow,
            major_workflow,
            multimedia_workflow,
            quick_workflow,
        ]:
            self.workflows[workflow.workflow_id] = workflow

    async def start_approval_workflow(
        self, version_id: str, workflow_id: str | None = None
    ) -> bool:
        """Start approval workflow for a version"""
        version = await self.version_manager.get_version(version_id)
        if not version:
            logger.error(f"Version {version_id} not found")
            return False

        # Select appropriate workflow
        if not workflow_id:
            workflow = self._select_workflow_for_version(version)
        else:
            workflow = self.workflows.get(workflow_id)

        if not workflow:
            logger.error(f"No suitable workflow found for version {version_id}")
            return False

        # Initialize review state
        review_state = {
            "version_id": version_id,
            "workflow_id": workflow.workflow_id,
            "current_stage": workflow.stages[0] if workflow.stages else None,
            "stage_progress": {},
            "started_at": datetime.now(UTC),
            "deadline": datetime.now(UTC)
            + timedelta(days=workflow.deadline_days),
            "review_tasks": [],
        }

        self.active_reviews[version_id] = review_state

        # Create initial review tasks
        await self._create_stage_review_tasks(version_id, workflow.stages[0])

        # Update version status
        version.approval_status = ApprovalStatus.IN_REVIEW

        logger.info(f"Started {workflow.name} workflow for version {version_id}")
        return True

    def _select_workflow_for_version(
        self, version: ContentVersion
    ) -> ApprovalWorkflow | None:
        """Select appropriate workflow for version"""
        content_type = version.content_snapshot.content_type
        change_type = version.change_type

        # Find matching workflows
        suitable_workflows = []
        for workflow in self.workflows.values():
            if workflow.is_applicable_to_content(content_type, change_type):
                suitable_workflows.append(workflow)

        if not suitable_workflows:
            return None

        # Select most specific workflow (fewest applicable types)
        return min(
            suitable_workflows,
            key=lambda w: len(w.applicable_content_types)
            + len(w.applicable_change_types),
        )

    async def _create_stage_review_tasks(
        self, version_id: str, stage: WorkflowStage
    ) -> None:
        """Create review tasks for a workflow stage"""
        review_state = self.active_reviews.get(version_id)
        if not review_state:
            return

        workflow = self.workflows.get(review_state["workflow_id"])
        if not workflow:
            return

        # Get required reviewers for stage
        required_roles = workflow.stage_reviewers.get(
            stage, [ReviewerRole.CONTENT_REVIEWER]
        )

        # Find available reviewers
        for role in required_roles:
            reviewers = self._find_reviewers_by_role(role)

            for reviewer_id in reviewers[:2]:  # Limit to 2 reviewers per role
                task = ReviewTask(
                    task_id=str(uuid.uuid4()),
                    version_id=version_id,
                    reviewer_id=reviewer_id,
                    reviewer_role=role,
                    workflow_stage=stage,
                    review_checklist=self._get_stage_checklist(stage),
                    due_date=review_state["deadline"],
                )

                self.review_tasks[task.task_id] = task
                review_state["review_tasks"].append(task.task_id)

        logger.info(
            f"Created {len(review_state['review_tasks'])} review tasks for stage {stage.value}"
        )

    def _find_reviewers_by_role(self, role: ReviewerRole) -> list[int]:
        """Find available reviewers by role"""
        # In a real implementation, this would query user database
        # For now, return mock reviewer IDs
        role_reviewers = {
            ReviewerRole.CONTENT_REVIEWER: [2001, 2002, 2003],
            ReviewerRole.SUBJECT_EXPERT: [2010, 2011],
            ReviewerRole.EDUCATIONAL_SPECIALIST: [2020, 2021],
            ReviewerRole.TECHNICAL_REVIEWER: [2030, 2031],
            ReviewerRole.FINAL_APPROVER: [2040],
            ReviewerRole.QUALITY_ASSURANCE: [2050, 2051],
        }

        return role_reviewers.get(role, [])

    def _get_stage_checklist(self, stage: WorkflowStage) -> list[dict[str, Any]]:
        """Get review checklist for workflow stage"""
        checklists = {
            WorkflowStage.CONTENT_REVIEW: [
                {
                    "check_id": "content_accuracy",
                    "description": "İçerik doğruluğu ve güncelliği",
                    "description_tr": "İçerik doğruluğu ve güncelliği",
                    "required": True,
                    "type": "boolean",
                },
                {
                    "check_id": "language_quality",
                    "description": "Dil kalitesi ve anlaşılırlık",
                    "description_tr": "Dil kalitesi ve anlaşılırlık",
                    "required": True,
                    "type": "rating",
                },
                {
                    "check_id": "curriculum_alignment",
                    "description": "Müfredat uyumu",
                    "description_tr": "Müfredat uyumu",
                    "required": True,
                    "type": "boolean",
                },
            ],
            WorkflowStage.TECHNICAL_REVIEW: [
                {
                    "check_id": "technical_quality",
                    "description": "Teknik kalite ve format",
                    "description_tr": "Teknik kalite ve format",
                    "required": True,
                    "type": "rating",
                },
                {
                    "check_id": "accessibility",
                    "description": "Erişilebilirlik standartları",
                    "description_tr": "Erişilebilirlik standartları",
                    "required": True,
                    "type": "boolean",
                },
                {
                    "check_id": "performance",
                    "description": "Performans optimizasyonu",
                    "description_tr": "Performans optimizasyonu",
                    "required": False,
                    "type": "rating",
                },
            ],
            WorkflowStage.EDUCATIONAL_REVIEW: [
                {
                    "check_id": "learning_objectives",
                    "description": "Öğrenme hedefleri uyumu",
                    "description_tr": "Öğrenme hedefleri uyumu",
                    "required": True,
                    "type": "boolean",
                },
                {
                    "check_id": "pedagogical_approach",
                    "description": "Pedagojik yaklaşım uygunluğu",
                    "description_tr": "Pedagojik yaklaşım uygunluğu",
                    "required": True,
                    "type": "rating",
                },
                {
                    "check_id": "age_appropriateness",
                    "description": "Yaş grubu uygunluğu",
                    "description_tr": "Yaş grubu uygunluğu",
                    "required": True,
                    "type": "boolean",
                },
            ],
            WorkflowStage.QUALITY_ASSURANCE: [
                {
                    "check_id": "final_quality_check",
                    "description": "Final kalite kontrolü",
                    "description_tr": "Final kalite kontrolü",
                    "required": True,
                    "type": "boolean",
                },
                {
                    "check_id": "metadata_completeness",
                    "description": "Metadata tamlığı",
                    "description_tr": "Metadata tamlığı",
                    "required": True,
                    "type": "boolean",
                },
            ],
            WorkflowStage.FINAL_APPROVAL: [
                {
                    "check_id": "overall_approval",
                    "description": "Genel onay",
                    "description_tr": "Genel onay",
                    "required": True,
                    "type": "boolean",
                }
            ],
        }

        return checklists.get(stage, [])

    async def submit_review(
        self,
        task_id: str,
        reviewer_id: int,
        review_data: dict[str, Any],
        comments: str = "",
    ) -> bool:
        """Submit review for a task"""
        task = self.review_tasks.get(task_id)
        if not task or task.reviewer_id != reviewer_id:
            return False

        # Complete the task
        task.complete_task(review_data)

        # Add review comment to version
        version = await self.version_manager.get_version(task.version_id)
        if version:
            if comments:
                version.add_review_comment(
                    reviewer_id, task.reviewer_role, comments, "review_submission"
                )

            # Add checklist results as structured comments
            checklist_summary = []
            for item in task.review_checklist:
                if item.get("completed"):
                    result = item.get("result")
                    check_desc = item.get("description_tr", item.get("description", ""))
                    checklist_summary.append(f"{check_desc}: {result}")

            if checklist_summary:
                version.add_review_comment(
                    reviewer_id,
                    task.reviewer_role,
                    "; ".join(checklist_summary),
                    "checklist_results",
                )

        # Check if stage is complete
        await self._check_stage_completion(task.version_id, task.workflow_stage)

        logger.info(f"Review submitted for task {task_id} by reviewer {reviewer_id}")
        return True

    async def _check_stage_completion(
        self, version_id: str, stage: WorkflowStage
    ) -> None:
        """Check if workflow stage is complete and advance if necessary"""
        review_state = self.active_reviews.get(version_id)
        if not review_state or review_state["current_stage"] != stage:
            return

        workflow = self.workflows.get(review_state["workflow_id"])
        if not workflow:
            return

        # Get tasks for current stage
        stage_tasks = [
            self.review_tasks[task_id]
            for task_id in review_state["review_tasks"]
            if task_id in self.review_tasks
            and self.review_tasks[task_id].workflow_stage == stage
        ]

        # Check completion
        completed_tasks = [task for task in stage_tasks if task.status == "completed"]
        required_approvals = workflow.required_approvals_per_stage.get(stage, 1)

        if len(completed_tasks) >= required_approvals:
            # Stage completed, advance to next
            next_stage = workflow.get_next_stage(stage)

            if next_stage:
                review_state["current_stage"] = next_stage
                await self._create_stage_review_tasks(version_id, next_stage)
                logger.info(
                    f"Advanced version {version_id} to stage {next_stage.value}"
                )
            else:
                # Workflow completed
                await self._complete_approval_workflow(version_id)

    async def _complete_approval_workflow(self, version_id: str) -> None:
        """Complete approval workflow"""
        review_state = self.active_reviews.get(version_id)
        if not review_state:
            return

        version = await self.version_manager.get_version(version_id)
        if not version:
            return

        # Calculate overall approval decision
        all_tasks = [
            self.review_tasks[task_id]
            for task_id in review_state["review_tasks"]
            if task_id in self.review_tasks
        ]

        # Simple majority decision (in real implementation, would be more sophisticated)
        positive_reviews = 0
        negative_reviews = 0

        for task in all_tasks:
            if task.status == "completed":
                overall_check = next(
                    (
                        item
                        for item in task.review_checklist
                        if item.get("check_id") == "overall_approval"
                    ),
                    None,
                )

                if overall_check and overall_check.get("result") is True:
                    positive_reviews += 1
                elif overall_check and overall_check.get("result") is False:
                    negative_reviews += 1

        # Make final decision
        if positive_reviews > negative_reviews and positive_reviews > 0:
            version.approval_status = ApprovalStatus.APPROVED
            logger.info(f"Approved version {version_id}")
        else:
            version.approval_status = ApprovalStatus.REJECTED
            logger.info(f"Rejected version {version_id}")

        # Mark workflow as completed
        review_state["completed_at"] = datetime.now(UTC)
        review_state["current_stage"] = None

    async def get_pending_reviews(self, reviewer_id: int) -> list[dict[str, Any]]:
        """Get pending review tasks for a reviewer"""
        pending_tasks = []

        for task in self.review_tasks.values():
            if task.reviewer_id == reviewer_id and task.status in [
                "assigned",
                "in_progress",
            ]:
                version = await self.version_manager.get_version(task.version_id)
                task_data = task.to_dict()

                if version:
                    task_data["content_title"] = version.content_snapshot.metadata.title
                    task_data[
                        "content_type"
                    ] = version.content_snapshot.content_type.value
                    task_data["version_number"] = version.version_number

                pending_tasks.append(task_data)

        return sorted(pending_tasks, key=lambda t: t.get("due_date", ""))

    async def get_workflow_status(self, version_id: str) -> dict[str, Any] | None:
        """Get current workflow status for a version"""
        review_state = self.active_reviews.get(version_id)
        if not review_state:
            return None

        workflow = self.workflows.get(review_state["workflow_id"])
        if not workflow:
            return None

        # Get task statistics
        all_tasks = [
            self.review_tasks[task_id]
            for task_id in review_state["review_tasks"]
            if task_id in self.review_tasks
        ]

        completed_tasks = [task for task in all_tasks if task.status == "completed"]
        overdue_tasks = [task for task in all_tasks if task.is_overdue()]

        # Calculate progress
        total_stages = len(workflow.stages)
        current_stage_index = (
            workflow.stages.index(review_state["current_stage"])
            if review_state.get("current_stage")
            else total_stages
        )
        progress_percentage = (
            (current_stage_index / total_stages) * 100
            if review_state.get("current_stage")
            else 100
        )

        return {
            "version_id": version_id,
            "workflow_name": workflow.name,
            "current_stage": review_state.get("current_stage").value
            if review_state.get("current_stage")
            else "completed",
            "progress_percentage": progress_percentage,
            "total_tasks": len(all_tasks),
            "completed_tasks": len(completed_tasks),
            "overdue_tasks": len(overdue_tasks),
            "started_at": review_state["started_at"].isoformat(),
            "deadline": review_state["deadline"].isoformat(),
            "is_overdue": datetime.now(UTC) > review_state["deadline"],
            "completed_at": review_state.get("completed_at").isoformat()
            if review_state.get("completed_at")
            else None,
        }

    def get_workflow_statistics(self) -> dict[str, Any]:
        """Get overall workflow statistics"""
        total_reviews = len(self.active_reviews)
        completed_reviews = len(
            [r for r in self.active_reviews.values() if r.get("completed_at")]
        )
        overdue_reviews = len(
            [
                r
                for r in self.active_reviews.values()
                if not r.get("completed_at")
                and datetime.now(UTC) > r["deadline"]
            ]
        )

        # Task statistics
        total_tasks = len(self.review_tasks)
        completed_tasks = len(
            [t for t in self.review_tasks.values() if t.status == "completed"]
        )
        overdue_tasks = len([t for t in self.review_tasks.values() if t.is_overdue()])

        return {
            "active_reviews": total_reviews - completed_reviews,
            "completed_reviews": completed_reviews,
            "overdue_reviews": overdue_reviews,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "overdue_tasks": overdue_tasks,
            "completion_rate": (completed_tasks / total_tasks * 100)
            if total_tasks > 0
            else 0,
            "average_review_duration_days": 5.2,  # Would calculate from actual data
        }


if __name__ == "__main__":
    # Example usage and testing
    print("KIRO2 Content Versioning and Approval System")
    print("=" * 50)

    async def test_versioning_system():
        """Test versioning and approval system"""

        # Create managers
        version_manager = VersionManager()
        workflow_manager = ApprovalWorkflowManager(version_manager)

        # Create sample content
        from analytics.unified_analytics_data_model import (
            TurkishExamType,
            TurkishSubject,
        )
        from content.unified_content_management import (
            ContentItem,
            ContentMetadata,
        )

        sample_metadata = ContentMetadata(
            title="Türev Alma Kuralları",
            description="Temel türev alma kuralları",
            subject=TurkishSubject.MATEMATIK,
            exam_types=[TurkishExamType.TYT],
            topics=["Kalkülüs", "Türev"],
        )

        content_item = ContentItem(
            content_id=str(uuid.uuid4()),
            content_type=ContentType.QUESTION,
            metadata=sample_metadata,
            created_by=1001,
        )

        print(f"Created content: {content_item.metadata.title}")

        # Create first version
        version1 = await version_manager.create_version(
            content_item=content_item,
            change_summary="İlk versiyon - temel içerik oluşturuldu",
            change_type=ChangeType.MAJOR,
            created_by=1001,
        )

        print(f"Created version: {version1.version_number}")

        # Start approval workflow
        success = await workflow_manager.start_approval_workflow(version1.version_id)
        print(f"Started approval workflow: {success}")

        # Get workflow status
        status = await workflow_manager.get_workflow_status(version1.version_id)
        if status:
            print(
                f"Workflow status: {status['current_stage']} ({status['progress_percentage']:.1f}%)"
            )
            print(
                f"Tasks: {status['completed_tasks']}/{status['total_tasks']} completed"
            )

        # Simulate review submission
        pending_reviews = await workflow_manager.get_pending_reviews(2001)
        if pending_reviews:
            first_task = pending_reviews[0]
            print(f"Submitting review for task: {first_task['task_id']}")

            review_data = {
                "content_accuracy": True,
                "language_quality": 4,
                "curriculum_alignment": True,
                "overall_approval": True,
            }

            review_success = await workflow_manager.submit_review(
                first_task["task_id"],
                2001,
                review_data,
                "İçerik kaliteli ve müfredata uygun",
            )
            print(f"Review submitted: {review_success}")

        # Create updated version
        updated_content = copy.deepcopy(content_item)
        updated_content.metadata.description = (
            "Geliştirilmiş türev alma kuralları ve örnekler"
        )

        version2 = await version_manager.create_version(
            content_item=updated_content,
            change_summary="Açıklamalar iyileştirildi ve örnekler eklendi",
            change_type=ChangeType.MINOR,
            created_by=1001,
            parent_version_id=version1.version_id,
        )

        print(f"Created updated version: {version2.version_number}")

        # Compare versions
        comparison = await version_manager.compare_versions(
            version1.version_id, version2.version_id
        )

        print("Version comparison:")
        print(f"  Total changes: {comparison['summary']['total_changes']}")
        print(f"  Categories: {comparison['summary']['categories']}")

        # Get statistics
        stats = workflow_manager.get_workflow_statistics()
        print(f"Workflow statistics: {stats}")

    # Run test
    asyncio.run(test_versioning_system())
