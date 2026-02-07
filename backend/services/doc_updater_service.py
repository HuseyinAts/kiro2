"""
Automated Documentation Update Service - CLAUDE.md Self-Improvement

Bu servis, CLAUDE.md dosyasının otomatik güncellenmesini yönetir:
- Rule değişikliklerinde otomatik update
- Best practice example seçimi
- Migration guide oluşturma
- Semantic versioning
- Before/after diff
- Human-in-the-loop approval workflow

Spec: claude-md-self-improvement REQ-6
- REQ-6.1: CLAUDE.md otomatik update
- REQ-6.2: Best practice example seçimi
- REQ-6.3: Migration guide oluşturma
- REQ-6.4: Semantic versioning
- REQ-6.5: Before/after diff
- REQ-6.6: Human-in-the-loop approval workflow

Author: KIRO2 Team
Date: 2026-01-17
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import re
import logging
import difflib
import hashlib

# Git integration
try:
    import git
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    git = None  # type: ignore

# Database
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

# Models
from backend.models.claude_md_improvement_models import (
    RuleEffectiveness,
    RuleVersion,
    ImprovementTrigger,
    AuditLog,
)

logger = logging.getLogger(__name__)


class ChangeType(str, Enum):
    """Type of change for semantic versioning."""
    MAJOR = "major"  # Breaking changes
    MINOR = "minor"  # New features
    PATCH = "patch"  # Bug fixes


class ApprovalStatus(str, Enum):
    """Approval status for changes."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"


@dataclass
class Example:
    """Best practice example."""
    rule_id: str
    title: str
    good_example: str
    bad_example: Optional[str] = None
    explanation: str = ""
    effectiveness_score: float = 0.0


@dataclass
class DiffResult:
    """Result of diff generation."""
    rule_id: str
    old_text: str
    new_text: str
    unified_diff: str
    lines_added: int
    lines_removed: int
    change_type: ChangeType
    generated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Change:
    """A single change to CLAUDE.md."""
    section: str
    rule_id: str
    old_content: str
    new_content: str
    change_type: ChangeType
    reason: str


@dataclass
class ApprovalRequest:
    """Request for human approval."""
    id: str
    changes: List[Change]
    version_before: str
    version_after: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    requested_at: datetime = field(default_factory=datetime.utcnow)
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None


@dataclass
class UpdateResult:
    """Result of CLAUDE.md update."""
    success: bool
    version_before: str
    version_after: str
    changes_applied: int
    diff: Optional[DiffResult] = None
    error: Optional[str] = None
    updated_at: datetime = field(default_factory=datetime.utcnow)


class DocUpdaterService:
    """
    Documentation update service for CLAUDE.md.

    Manages automatic updates with:
    - Git-based version control
    - Semantic versioning
    - Approval workflow
    - Diff generation
    """

    # Configuration
    CLAUDE_MD_FILENAME = "CLAUDE.md"
    VERSION_PATTERN = r"v?(\d+)\.(\d+)\.(\d+)"
    AUTO_APPROVE_THRESHOLD = 0.8  # High confidence changes auto-approved

    def __init__(
        self,
        db: AsyncSession,
        claude_md_path: Optional[Path] = None,
    ):
        """
        Initialize doc updater service.

        Args:
            db: Database session
            claude_md_path: Path to CLAUDE.md file
        """
        self.db = db
        self.claude_md_path = claude_md_path or Path(self.CLAUDE_MD_FILENAME)
        self._pending_approvals: Dict[str, ApprovalRequest] = {}

        # Git repo
        self._repo: Optional[git.Repo] = None
        if GIT_AVAILABLE:
            try:
                self._repo = git.Repo(search_parent_directories=True)
            except Exception:
                logger.warning("Git repository not found")

    # =========================================================================
    # REQ-6.1: Auto-update CLAUDE.md
    # =========================================================================

    async def update_claude_md(
        self,
        rule_id: str,
        new_text: str,
        reason: str = "",
        auto_approve: bool = False,
    ) -> UpdateResult:
        """
        Update CLAUDE.md with new rule text.

        Args:
            rule_id: Rule identifier
            new_text: New rule text
            reason: Reason for update
            auto_approve: Whether to auto-approve

        Returns:
            UpdateResult with status
        """
        try:
            # Read current content
            if not self.claude_md_path.exists():
                return UpdateResult(
                    success=False,
                    version_before="0.0.0",
                    version_after="0.0.0",
                    changes_applied=0,
                    error=f"CLAUDE.md not found at {self.claude_md_path}",
                )

            current_content = self.claude_md_path.read_text(encoding="utf-8")
            current_version = self._extract_version(current_content)

            # Find and replace rule section
            old_text = self._find_rule_section(current_content, rule_id)
            if old_text is None:
                # Rule doesn't exist, append to appropriate section
                updated_content = self._append_rule(current_content, rule_id, new_text)
                change_type = ChangeType.MINOR
            else:
                # Update existing rule
                updated_content = self._replace_rule(current_content, rule_id, new_text)
                change_type = self._determine_change_type(old_text, new_text)

            # Generate diff
            diff = await self.generate_diff(rule_id, old_text or "", new_text)
            diff.change_type = change_type

            # Increment version
            new_version = self.increment_version(current_version, change_type.value)

            # Update version in content
            updated_content = self._update_version_in_content(updated_content, new_version)

            # Create change record
            change = Change(
                section=self._find_rule_section_name(current_content, rule_id) or "unknown",
                rule_id=rule_id,
                old_content=old_text or "",
                new_content=new_text,
                change_type=change_type,
                reason=reason,
            )

            # Check if approval needed
            if auto_approve or change_type == ChangeType.PATCH:
                # Auto-approve patches and explicit auto-approve
                await self._apply_changes(updated_content)
                await self._create_version_record(rule_id, new_text, new_version, reason)

                await self._log_audit(
                    action="auto_update_claude_md",
                    entity_type="documentation",
                    entity_id=rule_id,
                    details={
                        "version_before": current_version,
                        "version_after": new_version,
                        "change_type": change_type.value,
                    },
                )

                return UpdateResult(
                    success=True,
                    version_before=current_version,
                    version_after=new_version,
                    changes_applied=1,
                    diff=diff,
                )
            else:
                # Request approval
                approval = await self.request_approval([change])

                return UpdateResult(
                    success=False,
                    version_before=current_version,
                    version_after=new_version,
                    changes_applied=0,
                    diff=diff,
                    error=f"Approval required. Request ID: {approval.id}",
                )

        except Exception as e:
            logger.error(f"Failed to update CLAUDE.md: {e}")
            return UpdateResult(
                success=False,
                version_before="0.0.0",
                version_after="0.0.0",
                changes_applied=0,
                error=str(e),
            )

    # =========================================================================
    # REQ-6.2: Best Practice Example Selection
    # =========================================================================

    async def select_best_examples(
        self,
        rule_id: str,
        limit: int = 3,
    ) -> List[Example]:
        """
        Select best practice examples for a rule.

        Args:
            rule_id: Rule identifier
            limit: Maximum examples to return

        Returns:
            List of best practice examples
        """
        # Get high-performing feedback for this rule
        result = await self.db.execute(
            select(RuleEffectiveness)
            .where(
                and_(
                    RuleEffectiveness.rule_id == rule_id,
                    RuleEffectiveness.effectiveness_score >= 0.8,
                )
            )
            .order_by(desc(RuleEffectiveness.effectiveness_score))
            .limit(limit)
        )
        rules = result.scalars().all()

        examples = []
        for rule in rules:
            # Extract examples from rule text
            good_example, bad_example = self._extract_examples(rule.rule_text or "")

            examples.append(Example(
                rule_id=rule.rule_id,
                title=f"Best practice for {rule.rule_id}",
                good_example=good_example or rule.rule_text or "",
                bad_example=bad_example,
                explanation=f"This pattern has {rule.effectiveness_score:.0%} effectiveness",
                effectiveness_score=rule.effectiveness_score,
            ))

        # If no examples found, generate generic ones
        if not examples:
            examples.append(Example(
                rule_id=rule_id,
                title=f"Example for {rule_id}",
                good_example="# Good: Follow the rule consistently",
                bad_example="# Bad: Ignore the rule",
                explanation="Follow established patterns for best results",
                effectiveness_score=0.5,
            ))

        return examples

    def _extract_examples(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract good/bad examples from text."""
        good_match = re.search(r"(?:Good|GOOD|✓|✅)[:\s]*(.+?)(?=Bad|BAD|✗|❌|$)", text, re.DOTALL | re.IGNORECASE)
        bad_match = re.search(r"(?:Bad|BAD|✗|❌)[:\s]*(.+?)(?=$)", text, re.DOTALL | re.IGNORECASE)

        good = good_match.group(1).strip() if good_match else None
        bad = bad_match.group(1).strip() if bad_match else None

        return good, bad

    # =========================================================================
    # REQ-6.3: Migration Guide Generation
    # =========================================================================

    async def generate_migration_guide(
        self,
        old_version: str,
        new_version: str,
    ) -> str:
        """
        Generate migration guide between versions.

        Args:
            old_version: Previous version
            new_version: New version

        Returns:
            Migration guide markdown
        """
        # Get version history
        result = await self.db.execute(
            select(RuleVersion)
            .where(
                and_(
                    RuleVersion.version >= old_version,
                    RuleVersion.version <= new_version,
                )
            )
            .order_by(RuleVersion.created_at)
        )
        versions = result.scalars().all()

        if not versions:
            return f"# Migration Guide: {old_version} → {new_version}\n\nNo changes found."

        # Build migration guide
        guide_parts = [
            f"# Migration Guide: {old_version} → {new_version}",
            f"\n**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            "\n## Changes\n",
        ]

        for version in versions:
            guide_parts.append(f"### Version {version.version}")
            guide_parts.append(f"- **Rule:** {version.rule_id}")
            guide_parts.append(f"- **Reason:** {version.change_reason or 'Not specified'}")

            if version.effectiveness_before and version.effectiveness_after:
                change = version.effectiveness_after - version.effectiveness_before
                guide_parts.append(
                    f"- **Impact:** {'+' if change >= 0 else ''}{change:.1%} effectiveness"
                )

            guide_parts.append("")

        # Add migration steps
        guide_parts.extend([
            "## Migration Steps\n",
            "1. Review the changes above",
            "2. Update any custom rules that depend on changed rules",
            "3. Test in a sandbox environment",
            "4. Apply changes in production",
            "",
            "## Rollback\n",
            f"If issues occur, rollback to version {old_version}:",
            "```bash",
            f"git checkout {old_version} -- CLAUDE.md",
            "```",
        ])

        return "\n".join(guide_parts)

    # =========================================================================
    # REQ-6.4: Semantic Versioning
    # =========================================================================

    def increment_version(
        self,
        current: str,
        change_type: str,
    ) -> str:
        """
        Increment version using semantic versioning.

        Args:
            current: Current version string (e.g., "1.2.3")
            change_type: Type of change ("major", "minor", "patch")

        Returns:
            New version string
        """
        # Parse current version
        match = re.match(self.VERSION_PATTERN, current)
        if match:
            major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))
        else:
            major, minor, patch = 1, 0, 0

        # Increment based on change type
        if change_type == "major" or change_type == ChangeType.MAJOR:
            major += 1
            minor = 0
            patch = 0
        elif change_type == "minor" or change_type == ChangeType.MINOR:
            minor += 1
            patch = 0
        else:  # patch
            patch += 1

        return f"{major}.{minor}.{patch}"

    def _extract_version(self, content: str) -> str:
        """Extract version from CLAUDE.md content."""
        # Look for version in content
        match = re.search(r"Version:\s*" + self.VERSION_PATTERN, content, re.IGNORECASE)
        if match:
            return f"{match.group(1)}.{match.group(2)}.{match.group(3)}"

        # Default version
        return "1.0.0"

    def _update_version_in_content(self, content: str, new_version: str) -> str:
        """Update version in CLAUDE.md content."""
        # Try to replace existing version
        pattern = r"(Version:\s*)" + self.VERSION_PATTERN
        replacement = f"\\g<1>{new_version}"

        updated = re.sub(pattern, replacement, content, count=1, flags=re.IGNORECASE)

        # If no version found, add it
        if updated == content:
            # Add version after first heading
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("#"):
                    lines.insert(i + 1, f"\nVersion: {new_version}\n")
                    break
            updated = "\n".join(lines)

        return updated

    # =========================================================================
    # REQ-6.5: Before/After Diff Generation
    # =========================================================================

    async def generate_diff(
        self,
        rule_id: str,
        old_text: Optional[str] = None,
        new_text: Optional[str] = None,
    ) -> DiffResult:
        """
        Generate diff between old and new text.

        Args:
            rule_id: Rule identifier
            old_text: Old text (if None, fetch from DB)
            new_text: New text (if None, fetch current)

        Returns:
            DiffResult with unified diff
        """
        # Get texts if not provided
        if old_text is None:
            result = await self.db.execute(
                select(RuleVersion)
                .where(
                    and_(
                        RuleVersion.rule_id == rule_id,
                        RuleVersion.is_current == True,
                    )
                )
            )
            version = result.scalar_one_or_none()
            old_text = version.rule_text if version else ""

        if new_text is None:
            new_text = old_text  # No change

        # Generate unified diff
        old_lines = (old_text or "").splitlines(keepends=True)
        new_lines = (new_text or "").splitlines(keepends=True)

        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{rule_id}",
            tofile=f"b/{rule_id}",
            lineterm="",
        )
        unified_diff = "".join(diff)

        # Count changes
        lines_added = sum(1 for line in new_lines if line not in old_lines)
        lines_removed = sum(1 for line in old_lines if line not in new_lines)

        # Determine change type
        change_type = self._determine_change_type(old_text or "", new_text or "")

        return DiffResult(
            rule_id=rule_id,
            old_text=old_text or "",
            new_text=new_text or "",
            unified_diff=unified_diff,
            lines_added=lines_added,
            lines_removed=lines_removed,
            change_type=change_type,
        )

    def _determine_change_type(self, old_text: str, new_text: str) -> ChangeType:
        """Determine change type based on diff."""
        if not old_text:
            return ChangeType.MINOR  # New addition

        # Calculate similarity
        similarity = difflib.SequenceMatcher(None, old_text, new_text).ratio()

        if similarity < 0.5:
            return ChangeType.MAJOR  # Significant change
        elif similarity < 0.9:
            return ChangeType.MINOR  # Moderate change
        else:
            return ChangeType.PATCH  # Small fix

    # =========================================================================
    # REQ-6.6: Human-in-the-Loop Approval Workflow
    # =========================================================================

    async def request_approval(
        self,
        changes: List[Change],
    ) -> ApprovalRequest:
        """
        Request human approval for changes.

        Args:
            changes: List of proposed changes

        Returns:
            ApprovalRequest object
        """
        # Read current version
        current_content = ""
        if self.claude_md_path.exists():
            current_content = self.claude_md_path.read_text(encoding="utf-8")

        current_version = self._extract_version(current_content)

        # Determine new version based on largest change type
        change_types = [c.change_type for c in changes]
        if ChangeType.MAJOR in change_types:
            max_change = ChangeType.MAJOR
        elif ChangeType.MINOR in change_types:
            max_change = ChangeType.MINOR
        else:
            max_change = ChangeType.PATCH

        new_version = self.increment_version(current_version, max_change.value)

        # Create approval request
        request_id = hashlib.md5(
            f"{current_version}{new_version}{datetime.now(timezone.utc).isoformat()}".encode()
        ).hexdigest()[:12]

        request = ApprovalRequest(
            id=request_id,
            changes=changes,
            version_before=current_version,
            version_after=new_version,
        )

        self._pending_approvals[request_id] = request

        # Save to database
        trigger = ImprovementTrigger(
            rule_id=changes[0].rule_id if changes else "unknown",
            trigger_reason=f"Documentation update: {len(changes)} change(s)",
            current_score=0.0,
            priority=2,
            approved=None,
        )
        self.db.add(trigger)
        await self.db.commit()

        # Log audit
        await self._log_audit(
            action="request_approval",
            entity_type="documentation",
            entity_id=request_id,
            details={
                "changes_count": len(changes),
                "version_before": current_version,
                "version_after": new_version,
            },
        )

        logger.info(f"Approval request created: {request_id}")
        return request

    async def approve_changes(
        self,
        request_id: str,
        approved_by: str,
    ) -> UpdateResult:
        """
        Approve pending changes.

        Args:
            request_id: Request ID
            approved_by: Who approved

        Returns:
            UpdateResult after applying changes
        """
        request = self._pending_approvals.get(request_id)
        if not request:
            return UpdateResult(
                success=False,
                version_before="",
                version_after="",
                changes_applied=0,
                error=f"Request not found: {request_id}",
            )

        if request.status != ApprovalStatus.PENDING:
            return UpdateResult(
                success=False,
                version_before=request.version_before,
                version_after=request.version_after,
                changes_applied=0,
                error=f"Request already processed: {request.status}",
            )

        # Mark as approved
        request.status = ApprovalStatus.APPROVED
        request.approved_by = approved_by
        request.approved_at = datetime.now(timezone.utc)

        # Apply changes
        try:
            current_content = self.claude_md_path.read_text(encoding="utf-8")

            for change in request.changes:
                current_content = self._replace_rule(
                    current_content, change.rule_id, change.new_content
                )
                await self._create_version_record(
                    change.rule_id,
                    change.new_content,
                    request.version_after,
                    change.reason,
                )

            # Update version
            current_content = self._update_version_in_content(
                current_content, request.version_after
            )

            # Apply
            await self._apply_changes(current_content)

            # Log audit
            await self._log_audit(
                action="approve_changes",
                entity_type="documentation",
                entity_id=request_id,
                actor=approved_by,
                details={
                    "changes_count": len(request.changes),
                    "version": request.version_after,
                },
            )

            return UpdateResult(
                success=True,
                version_before=request.version_before,
                version_after=request.version_after,
                changes_applied=len(request.changes),
            )

        except Exception as e:
            logger.error(f"Failed to apply approved changes: {e}")
            return UpdateResult(
                success=False,
                version_before=request.version_before,
                version_after=request.version_after,
                changes_applied=0,
                error=str(e),
            )

    async def reject_changes(
        self,
        request_id: str,
        rejected_by: str,
        reason: str,
    ) -> bool:
        """
        Reject pending changes.

        Args:
            request_id: Request ID
            rejected_by: Who rejected
            reason: Rejection reason

        Returns:
            Success status
        """
        request = self._pending_approvals.get(request_id)
        if not request:
            return False

        request.status = ApprovalStatus.REJECTED
        request.rejection_reason = reason

        # Log audit
        await self._log_audit(
            action="reject_changes",
            entity_type="documentation",
            entity_id=request_id,
            actor=rejected_by,
            reason=reason,
        )

        return True

    async def get_pending_approvals(self) -> List[ApprovalRequest]:
        """Get all pending approval requests."""
        return [
            r for r in self._pending_approvals.values()
            if r.status == ApprovalStatus.PENDING
        ]

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _find_rule_section(
        self,
        content: str,
        rule_id: str,
    ) -> Optional[str]:
        """Find rule section in CLAUDE.md content."""
        # Pattern to find rule by ID
        pattern = rf"(?:^|\n)(##?\s*{re.escape(rule_id)}.*?)(?=\n##|\Z)"
        match = re.search(pattern, content, re.DOTALL | re.MULTILINE)

        if match:
            return match.group(1).strip()

        # Try finding by rule ID in content
        pattern = rf"(?:^|\n)(.*?{re.escape(rule_id)}.*?)(?=\n##|\Z)"
        match = re.search(pattern, content, re.DOTALL | re.MULTILINE)

        if match:
            return match.group(1).strip()

        return None

    def _find_rule_section_name(
        self,
        content: str,
        rule_id: str,
    ) -> Optional[str]:
        """Find section name containing rule."""
        lines = content.split("\n")
        current_section = "root"

        for line in lines:
            if line.startswith("## "):
                current_section = line[3:].strip()
            elif rule_id in line:
                return current_section

        return None

    def _replace_rule(
        self,
        content: str,
        rule_id: str,
        new_text: str,
    ) -> str:
        """Replace rule in content."""
        old_text = self._find_rule_section(content, rule_id)

        if old_text:
            return content.replace(old_text, new_text)

        # Rule not found, append
        return self._append_rule(content, rule_id, new_text)

    def _append_rule(
        self,
        content: str,
        rule_id: str,
        new_text: str,
    ) -> str:
        """Append new rule to content."""
        # Add before the last section or at end
        return f"{content.rstrip()}\n\n## {rule_id}\n\n{new_text}\n"

    async def _apply_changes(self, content: str) -> None:
        """Apply changes to CLAUDE.md file."""
        # Write content
        self.claude_md_path.write_text(content, encoding="utf-8")

        # Git commit if available
        if self._repo and GIT_AVAILABLE:
            try:
                self._repo.index.add([str(self.claude_md_path)])
                self._repo.index.commit(
                    f"CLAUDE.md auto-update: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"
                )
            except Exception as e:
                logger.warning(f"Git commit failed: {e}")

    async def _create_version_record(
        self,
        rule_id: str,
        rule_text: str,
        version: str,
        reason: str,
    ) -> None:
        """Create version record in database."""
        # Get previous version
        result = await self.db.execute(
            select(RuleVersion)
            .where(
                and_(
                    RuleVersion.rule_id == rule_id,
                    RuleVersion.is_current == True,
                )
            )
        )
        previous = result.scalar_one_or_none()

        if previous:
            previous.is_current = False

        # Create new version
        new_version = RuleVersion(
            rule_id=rule_id,
            version=version,
            rule_text=rule_text,
            change_reason=reason,
            previous_version_id=previous.id if previous else None,
            created_by="doc_updater_service",
            is_current=True,
        )
        self.db.add(new_version)
        await self.db.commit()

    async def _log_audit(
        self,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        actor: Optional[str] = None,
        reason: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log audit entry."""
        try:
            audit = AuditLog(
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                actor=actor or "doc_updater_service",
                reason=reason,
                details=details or {},
            )
            self.db.add(audit)
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log audit: {e}")


# Factory function
async def get_doc_updater_service(
    db: AsyncSession,
    claude_md_path: Optional[Path] = None,
) -> DocUpdaterService:
    """Get doc updater service instance."""
    return DocUpdaterService(db, claude_md_path)
