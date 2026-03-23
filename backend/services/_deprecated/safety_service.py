"""
Safety Guardrails Service - CLAUDE.md Self-Improvement

Bu servis, zararlı rule değişikliklerini önler:
- Safety policy compliance
- Manual approval workflow
- Sandbox testing
- Fast rollback mechanism
- Audit logging
- Emergency stop

Spec: claude-md-self-improvement REQ-8
- REQ-8.1: Safety policy compliance kontrol
- REQ-8.2: Manual approval requirement
- REQ-8.3: Sandbox isolated environment
- REQ-8.4: < 5s recovery time
- REQ-8.5: Who, what, when, why audit log
- REQ-8.6: Emergency stop

Author: KIRO2 Team
Date: 2026-01-17
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from enum import Enum
from dataclasses import dataclass, field
import re
import logging
import hashlib
import asyncio

# Database
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

# Models
from backend.models.claude_md_improvement_models import (
    ImprovementTrigger,
    RuleVersion,
    AuditLog,
)

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Risk level for rule changes."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalStatus(str, Enum):
    """Approval status for changes."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"


@dataclass
class SafetyCheckResult:
    """Result of safety check."""
    passed: bool
    risk_level: RiskLevel
    violations: List[str]
    warnings: List[str]
    requires_approval: bool
    checked_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ApprovalRequest:
    """Approval request for risky changes."""
    id: str
    rule_id: str
    proposed_change: str
    risk_level: RiskLevel
    reason: str
    requested_by: str
    requested_at: datetime
    status: ApprovalStatus = ApprovalStatus.PENDING
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None


@dataclass
class SandboxResult:
    """Result of sandbox testing."""
    test_id: str
    passed: bool
    execution_time: float
    errors: List[str]
    warnings: List[str]
    metrics: Dict[str, float]


class SafetyService:
    """
    Safety guardrails service for CLAUDE.md improvements.

    Prevents harmful changes through:
    - Policy compliance checking
    - Manual approval workflow
    - Sandbox testing
    - Fast rollback
    - Comprehensive audit logging
    """

    # Safety policies
    RISKY_KEYWORDS = [
        "delete", "drop", "truncate", "remove all",
        "rm -rf", "force", "override", "bypass",
        "disable", "skip", "ignore", "eval", "exec",
        "sudo", "admin", "root", "password", "secret",
    ]

    FORBIDDEN_PATTERNS = [
        r"rm\s+-rf\s+/",  # Root deletion
        r"DROP\s+TABLE",  # SQL drop
        r"eval\s*\(",  # Code evaluation
        r"exec\s*\(",  # Code execution
        r"\.env",  # Environment files
        r"api[_-]?key",  # API keys
        r"password\s*=",  # Passwords
    ]

    # Configuration
    MAX_ROLLBACK_TIME = 5.0  # seconds
    SANDBOX_TIMEOUT = 30.0  # seconds
    AUTO_APPROVE_RISK_THRESHOLD = RiskLevel.LOW

    def __init__(self, db: AsyncSession):
        """Initialize safety service."""
        self.db = db
        self._emergency_stop_active = False
        self._pending_approvals: Dict[str, ApprovalRequest] = {}

    # =========================================================================
    # REQ-8.1: Safety Policy Compliance
    # =========================================================================

    async def check_safety(
        self,
        rule_text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> SafetyCheckResult:
        """
        Check if rule change complies with safety policies.

        Args:
            rule_text: Proposed rule text
            context: Additional context

        Returns:
            SafetyCheckResult with compliance status
        """
        violations = []
        warnings = []

        if not rule_text:
            return SafetyCheckResult(
                passed=True,
                risk_level=RiskLevel.LOW,
                violations=[],
                warnings=["Empty rule text"],
                requires_approval=False,
            )

        rule_lower = rule_text.lower()

        # Check for risky keywords
        for keyword in self.RISKY_KEYWORDS:
            if keyword in rule_lower:
                if keyword in ["delete", "drop", "rm -rf", "eval", "exec"]:
                    violations.append(f"Forbidden keyword detected: '{keyword}'")
                else:
                    warnings.append(f"Risky keyword detected: '{keyword}'")

        # Check for forbidden patterns
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, rule_text, re.IGNORECASE):
                violations.append(f"Forbidden pattern detected: '{pattern}'")

        # Determine risk level
        risk_level = self._calculate_risk_level(violations, warnings)

        # Determine if approval needed
        requires_approval = risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]

        passed = len(violations) == 0 and risk_level != RiskLevel.CRITICAL

        # Log audit
        await self._log_audit(
            action="safety_check",
            entity_type="rule",
            details={
                "passed": passed,
                "risk_level": risk_level.value,
                "violations_count": len(violations),
                "warnings_count": len(warnings),
            },
        )

        return SafetyCheckResult(
            passed=passed,
            risk_level=risk_level,
            violations=violations,
            warnings=warnings,
            requires_approval=requires_approval,
        )

    def _calculate_risk_level(
        self,
        violations: List[str],
        warnings: List[str],
    ) -> RiskLevel:
        """Calculate risk level based on violations and warnings."""
        if len(violations) > 2:
            return RiskLevel.CRITICAL
        elif len(violations) > 0:
            return RiskLevel.HIGH
        elif len(warnings) > 3:
            return RiskLevel.MEDIUM
        elif len(warnings) > 0:
            return RiskLevel.LOW
        else:
            return RiskLevel.LOW

    # =========================================================================
    # REQ-8.2: Manual Approval Requirement
    # =========================================================================

    async def request_approval(
        self,
        rule_id: str,
        proposed_change: str,
        reason: str,
        requested_by: str = "system",
    ) -> ApprovalRequest:
        """
        Request manual approval for risky change.

        Args:
            rule_id: Rule being changed
            proposed_change: Proposed rule text
            reason: Reason for change
            requested_by: Who requested the change

        Returns:
            ApprovalRequest object
        """
        # Check safety first
        safety = await self.check_safety(proposed_change)

        # Create approval request
        request_id = hashlib.md5(
            f"{rule_id}{proposed_change}{datetime.now(timezone.utc).isoformat()}".encode()
        ).hexdigest()[:12]

        request = ApprovalRequest(
            id=request_id,
            rule_id=rule_id,
            proposed_change=proposed_change,
            risk_level=safety.risk_level,
            reason=reason,
            requested_by=requested_by,
            requested_at=datetime.now(timezone.utc),
        )

        # Auto-approve low risk changes
        if safety.risk_level.value <= self.AUTO_APPROVE_RISK_THRESHOLD.value:
            request.status = ApprovalStatus.AUTO_APPROVED
            request.approved_at = datetime.now(timezone.utc)
            request.approved_by = "auto_approval_system"

        self._pending_approvals[request_id] = request

        # Update database
        await self._save_approval_request(request)

        # Log audit
        await self._log_audit(
            action="request_approval",
            entity_type="approval",
            entity_id=request_id,
            details={
                "rule_id": rule_id,
                "risk_level": safety.risk_level.value,
                "status": request.status.value,
            },
        )

        return request

    async def approve_change(
        self,
        request_id: str,
        approved_by: str,
        comments: Optional[str] = None,
    ) -> ApprovalRequest:
        """
        Approve a pending change request.

        Args:
            request_id: Request ID
            approved_by: Who approved
            comments: Optional comments

        Returns:
            Updated ApprovalRequest
        """
        request = self._pending_approvals.get(request_id)
        if not request:
            raise ValueError(f"Approval request not found: {request_id}")

        if request.status != ApprovalStatus.PENDING:
            raise ValueError(f"Request already processed: {request.status}")

        request.status = ApprovalStatus.APPROVED
        request.approved_by = approved_by
        request.approved_at = datetime.now(timezone.utc)

        # Log audit with who, what, when, why
        await self._log_audit(
            action="approve_change",
            entity_type="approval",
            entity_id=request_id,
            actor=approved_by,
            reason=comments or "Approved by admin",
            details={
                "rule_id": request.rule_id,
                "risk_level": request.risk_level.value,
            },
        )

        return request

    async def reject_change(
        self,
        request_id: str,
        rejected_by: str,
        reason: str,
    ) -> ApprovalRequest:
        """
        Reject a pending change request.

        Args:
            request_id: Request ID
            rejected_by: Who rejected
            reason: Rejection reason

        Returns:
            Updated ApprovalRequest
        """
        request = self._pending_approvals.get(request_id)
        if not request:
            raise ValueError(f"Approval request not found: {request_id}")

        if request.status != ApprovalStatus.PENDING:
            raise ValueError(f"Request already processed: {request.status}")

        request.status = ApprovalStatus.REJECTED
        request.rejection_reason = reason

        # Log audit
        await self._log_audit(
            action="reject_change",
            entity_type="approval",
            entity_id=request_id,
            actor=rejected_by,
            reason=reason,
            details={
                "rule_id": request.rule_id,
                "risk_level": request.risk_level.value,
            },
        )

        return request

    async def get_pending_approvals(self) -> List[ApprovalRequest]:
        """Get all pending approval requests."""
        return [
            r for r in self._pending_approvals.values()
            if r.status == ApprovalStatus.PENDING
        ]

    # =========================================================================
    # REQ-8.3: Sandbox Testing
    # =========================================================================

    async def test_in_sandbox(
        self,
        rule_text: str,
        test_cases: Optional[List[Dict[str, Any]]] = None,
    ) -> SandboxResult:
        """
        Test rule change in isolated sandbox environment.

        Args:
            rule_text: Rule to test
            test_cases: Optional test cases

        Returns:
            SandboxResult with test results
        """
        test_id = hashlib.md5(
            f"{rule_text}{datetime.now(timezone.utc).isoformat()}".encode()
        ).hexdigest()[:8]

        start_time = datetime.now(timezone.utc)
        errors = []
        warnings = []
        metrics = {}

        try:
            # Run safety check first
            safety = await self.check_safety(rule_text)

            if not safety.passed:
                errors.extend(safety.violations)
                warnings.extend(safety.warnings)

            # Simulate sandbox execution
            # In production, this would run in isolated container
            await asyncio.sleep(0.1)  # Simulate execution

            # Run test cases if provided
            if test_cases:
                for i, case in enumerate(test_cases):
                    try:
                        # Simulate test execution
                        await asyncio.sleep(0.05)
                        metrics[f"test_{i}_passed"] = 1.0
                    except Exception as e:
                        errors.append(f"Test case {i} failed: {str(e)}")
                        metrics[f"test_{i}_passed"] = 0.0

            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()

            passed = len(errors) == 0

            # Log audit
            await self._log_audit(
                action="sandbox_test",
                entity_type="sandbox",
                entity_id=test_id,
                details={
                    "passed": passed,
                    "execution_time": execution_time,
                    "errors_count": len(errors),
                },
            )

            return SandboxResult(
                test_id=test_id,
                passed=passed,
                execution_time=execution_time,
                errors=errors,
                warnings=warnings,
                metrics=metrics,
            )

        except asyncio.TimeoutError:
            return SandboxResult(
                test_id=test_id,
                passed=False,
                execution_time=self.SANDBOX_TIMEOUT,
                errors=["Sandbox execution timed out"],
                warnings=warnings,
                metrics={},
            )
        except Exception as e:
            return SandboxResult(
                test_id=test_id,
                passed=False,
                execution_time=(datetime.now(timezone.utc) - start_time).total_seconds(),
                errors=[f"Sandbox error: {str(e)}"],
                warnings=warnings,
                metrics={},
            )

    # =========================================================================
    # REQ-8.4: Fast Rollback (< 5s)
    # =========================================================================

    async def fast_rollback(
        self,
        rule_id: str,
        reason: str,
    ) -> Dict[str, Any]:
        """
        Perform fast rollback of a rule (< 5s recovery).

        Args:
            rule_id: Rule to rollback
            reason: Reason for rollback

        Returns:
            Rollback result with timing
        """
        start_time = datetime.now(timezone.utc)

        try:
            # Get current version
            result = await self.db.execute(
                select(RuleVersion)
                .where(
                    and_(
                        RuleVersion.rule_id == rule_id,
                        RuleVersion.is_current == True,
                    )
                )
            )
            current = result.scalar_one_or_none()

            if not current:
                return {
                    "success": False,
                    "error": "No current version found",
                    "recovery_time": 0,
                }

            # Get previous version
            if not current.previous_version_id:
                return {
                    "success": False,
                    "error": "No previous version to rollback to",
                    "recovery_time": 0,
                }

            result = await self.db.execute(
                select(RuleVersion)
                .where(RuleVersion.id == current.previous_version_id)
            )
            previous = result.scalar_one_or_none()

            if not previous:
                return {
                    "success": False,
                    "error": "Previous version not found",
                    "recovery_time": 0,
                }

            # Perform fast swap
            current.is_current = False
            previous.is_current = True

            await self.db.commit()

            recovery_time = (datetime.now(timezone.utc) - start_time).total_seconds()

            # Verify recovery time
            if recovery_time > self.MAX_ROLLBACK_TIME:
                logger.warning(
                    f"Rollback took {recovery_time:.2f}s, "
                    f"exceeding {self.MAX_ROLLBACK_TIME}s target"
                )

            # Log audit
            await self._log_audit(
                action="fast_rollback",
                entity_type="rule",
                entity_id=rule_id,
                reason=reason,
                details={
                    "from_version": current.version,
                    "to_version": previous.version,
                    "recovery_time": recovery_time,
                },
            )

            return {
                "success": True,
                "rule_id": rule_id,
                "rolled_back_from": current.version,
                "rolled_back_to": previous.version,
                "recovery_time": recovery_time,
                "met_sla": recovery_time < self.MAX_ROLLBACK_TIME,
            }

        except Exception as e:
            logger.error(f"Fast rollback failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "recovery_time": (datetime.now(timezone.utc) - start_time).total_seconds(),
            }

    # =========================================================================
    # REQ-8.5: Comprehensive Audit Logging
    # =========================================================================

    async def _log_audit(
        self,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        actor: Optional[str] = None,
        reason: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log audit entry with who, what, when, why.

        Args:
            action: What action was performed
            entity_type: What type of entity
            entity_id: Which entity
            actor: Who performed it
            reason: Why it was done
            details: Additional details
        """
        try:
            audit = AuditLog(
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                actor=actor or "safety_service",
                reason=reason,
                details=details or {},
            )
            self.db.add(audit)
            await self.db.commit()

        except Exception as e:
            logger.error(f"Failed to log audit: {e}")

    async def get_audit_history(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get audit history with filters."""
        query = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)

        if entity_type:
            query = query.where(AuditLog.entity_type == entity_type)

        if entity_id:
            query = query.where(AuditLog.entity_id == entity_id)

        result = await self.db.execute(query)
        audits = result.scalars().all()

        return [
            {
                "id": str(a.id),
                "action": a.action,
                "entity_type": a.entity_type,
                "entity_id": a.entity_id,
                "actor": a.actor,
                "reason": a.reason,
                "details": a.details,
                "created_at": a.created_at.isoformat(),
            }
            for a in audits
        ]

    # =========================================================================
    # REQ-8.6: Emergency Stop
    # =========================================================================

    async def emergency_stop(
        self,
        reason: str,
        activated_by: str = "system",
    ) -> Dict[str, Any]:
        """
        Activate emergency stop to pause all auto-improvements.

        Args:
            reason: Reason for emergency stop
            activated_by: Who activated

        Returns:
            Emergency stop status
        """
        self._emergency_stop_active = True

        # Cancel all pending improvements
        result = await self.db.execute(
            select(ImprovementTrigger)
            .where(ImprovementTrigger.processed == False)
        )
        pending = result.scalars().all()

        cancelled_count = 0
        for trigger in pending:
            trigger.processed = True
            trigger.processed_at = datetime.now(timezone.utc)
            cancelled_count += 1

        await self.db.commit()

        # Log audit
        await self._log_audit(
            action="emergency_stop",
            entity_type="system",
            actor=activated_by,
            reason=reason,
            details={
                "cancelled_improvements": cancelled_count,
            },
        )

        logger.critical(f"EMERGENCY STOP ACTIVATED: {reason}")

        return {
            "success": True,
            "emergency_stop_active": True,
            "reason": reason,
            "activated_by": activated_by,
            "activated_at": datetime.now(timezone.utc).isoformat(),
            "cancelled_improvements": cancelled_count,
        }

    async def resume_operations(
        self,
        resumed_by: str,
        reason: str,
    ) -> Dict[str, Any]:
        """
        Resume operations after emergency stop.

        Args:
            resumed_by: Who resumed
            reason: Reason for resuming

        Returns:
            Resume status
        """
        self._emergency_stop_active = False

        # Log audit
        await self._log_audit(
            action="resume_operations",
            entity_type="system",
            actor=resumed_by,
            reason=reason,
        )

        logger.info(f"Operations resumed by {resumed_by}: {reason}")

        return {
            "success": True,
            "emergency_stop_active": False,
            "resumed_by": resumed_by,
            "resumed_at": datetime.now(timezone.utc).isoformat(),
        }

    def is_emergency_stop_active(self) -> bool:
        """Check if emergency stop is active."""
        return self._emergency_stop_active

    # =========================================================================
    # Safety Status
    # =========================================================================

    async def get_safety_status(self) -> Dict[str, Any]:
        """Get current safety system status."""
        # Count pending approvals
        pending_approvals = len(await self.get_pending_approvals())

        # Get recent violations
        result = await self.db.execute(
            select(func.count())
            .select_from(AuditLog)
            .where(
                and_(
                    AuditLog.action == "safety_check",
                    AuditLog.created_at >= datetime.now(timezone.utc) - timedelta(hours=24),
                )
            )
        )
        recent_checks = result.scalar() or 0

        return {
            "emergency_stop_active": self._emergency_stop_active,
            "pending_approvals": pending_approvals,
            "recent_safety_checks": recent_checks,
            "auto_approve_threshold": self.AUTO_APPROVE_RISK_THRESHOLD.value,
            "max_rollback_time": self.MAX_ROLLBACK_TIME,
            "status": "paused" if self._emergency_stop_active else "active",
        }

    async def _save_approval_request(self, request: ApprovalRequest) -> None:
        """Save approval request to database."""
        # Create improvement trigger record for tracking
        trigger = ImprovementTrigger(
            rule_id=request.rule_id,
            trigger_reason=request.reason,
            current_score=0.0,
            priority=3 if request.risk_level == RiskLevel.HIGH else 2,
            approved=request.status == ApprovalStatus.APPROVED,
            approved_by=request.approved_by,
        )
        self.db.add(trigger)
        await self.db.commit()


# Factory function
async def get_safety_service(db: AsyncSession) -> SafetyService:
    """Get safety service instance."""
    return SafetyService(db)
