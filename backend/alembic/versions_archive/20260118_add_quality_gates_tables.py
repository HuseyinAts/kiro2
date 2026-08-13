"""add_quality_gates_tables

Revision ID: 20260118_quality_gates
Revises: 20260117_claude_md
Create Date: 2026-01-18 10:00:00.000000
Note: Fixed down_revision from e73a8e0797c1 to 20260117_claude_md for linear chain

Quality Gates Pipeline Tables:
- quality_gates_runs: Pipeline execution records
- quality_gate_results: Individual gate results
- quality_gates_override_audit: Override request audit log

Spec: quality-gates-pipeline Phase 3 (Database Persistence)
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260118_quality_gates"
down_revision: Union[str, None] = "20260117_claude_md"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ======================================================================
    # 1. quality_gates_runs - Pipeline execution records
    # ======================================================================
    op.create_table(
        "quality_gates_runs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # Pipeline info
        sa.Column(
            "pipeline_name",
            sa.String(100),
            nullable=False,
            comment="Pipeline identifier",
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            comment="Overall status: pass, warning, fail, error",
        ),
        # Scores
        sa.Column(
            "total_score",
            sa.Float(),
            nullable=False,
            comment="Weighted average score 0-10",
        ),
        sa.Column(
            "passed_gates",
            sa.Integer(),
            server_default="0",
            comment="Number of passed gates",
        ),
        sa.Column(
            "failed_gates",
            sa.Integer(),
            server_default="0",
            comment="Number of failed gates",
        ),
        sa.Column(
            "skipped_gates",
            sa.Integer(),
            server_default="0",
            comment="Number of skipped gates",
        ),
        # Execution
        sa.Column(
            "total_execution_time_ms",
            sa.Float(),
            nullable=False,
            comment="Total execution time in milliseconds",
        ),
        sa.Column(
            "parallel_execution_used",
            sa.Boolean(),
            server_default="false",
            comment="Whether parallel execution was used",
        ),
        sa.Column(
            "fail_fast_mode",
            sa.Boolean(),
            server_default="false",
            comment="Whether fail-fast mode was enabled",
        ),
        # Git context
        sa.Column(
            "commit_hash", sa.String(40), nullable=True, comment="Git commit hash"
        ),
        sa.Column("branch", sa.String(200), nullable=True, comment="Git branch name"),
        sa.Column(
            "repository", sa.String(500), nullable=True, comment="Repository identifier"
        ),
        # Trigger info
        sa.Column(
            "triggered_by",
            sa.String(255),
            nullable=True,
            comment="User/system that triggered the run",
        ),
        sa.Column(
            "trigger_type",
            sa.String(50),
            nullable=True,
            comment="Trigger type: manual, push, pr, schedule",
        ),
        # Override info
        sa.Column(
            "overridden",
            sa.Boolean(),
            server_default="false",
            comment="Whether result was overridden",
        ),
        sa.Column(
            "override_reason",
            sa.Text(),
            nullable=True,
            comment="Override justification",
        ),
        sa.Column(
            "override_approver",
            sa.String(255),
            nullable=True,
            comment="Who approved the override",
        ),
        # Configuration snapshot
        sa.Column(
            "config_snapshot",
            postgresql.JSONB(),
            nullable=True,
            comment="Pipeline configuration at time of run",
        ),
        # Timestamps
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Pipeline start time",
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Pipeline completion time",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            comment="Record creation time",
        ),
    )

    # Indexes for quality_gates_runs
    op.create_index("idx_qg_run_status", "quality_gates_runs", ["status"])
    op.create_index("idx_qg_run_commit", "quality_gates_runs", ["commit_hash"])
    op.create_index("idx_qg_run_branch", "quality_gates_runs", ["branch"])
    op.create_index("idx_qg_run_started", "quality_gates_runs", ["started_at"])
    op.create_index("idx_qg_run_triggered_by", "quality_gates_runs", ["triggered_by"])
    op.create_index(
        "idx_qg_run_status_started", "quality_gates_runs", ["status", "started_at"]
    )

    # ======================================================================
    # 2. quality_gate_results - Individual gate results
    # ======================================================================
    op.create_table(
        "quality_gate_results",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # Foreign key to run
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Parent pipeline run ID",
        ),
        # Gate info
        sa.Column(
            "gate_name", sa.String(100), nullable=False, comment="Gate identifier"
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            comment="Gate status: pass, warning, fail, skipped, timeout, error",
        ),
        # Scores
        sa.Column("score", sa.Float(), nullable=False, comment="Gate score 0-10"),
        sa.Column("threshold", sa.Float(), nullable=False, comment="Pass threshold"),
        sa.Column(
            "blocking",
            sa.Boolean(),
            server_default="true",
            comment="Whether this is a blocking gate",
        ),
        # Result details
        sa.Column(
            "message", sa.Text(), nullable=False, comment="Result summary message"
        ),
        sa.Column(
            "issues_count",
            sa.Integer(),
            server_default="0",
            comment="Number of issues found",
        ),
        sa.Column(
            "auto_fixed",
            sa.Boolean(),
            server_default="false",
            comment="Whether issues were auto-fixed",
        ),
        # Detailed data (JSON)
        sa.Column(
            "issues",
            postgresql.JSONB(),
            nullable=True,
            comment="List of issues with file, line, severity",
        ),
        sa.Column(
            "metrics",
            postgresql.JSONB(),
            nullable=True,
            comment="Gate-specific metrics",
        ),
        sa.Column(
            "details", postgresql.JSONB(), nullable=True, comment="Additional details"
        ),
        # Execution
        sa.Column(
            "execution_time_ms",
            sa.Float(),
            nullable=False,
            comment="Gate execution time in milliseconds",
        ),
        sa.Column(
            "retries",
            sa.Integer(),
            server_default="0",
            comment="Number of retry attempts",
        ),
        # Timestamps
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Gate start time",
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Gate completion time",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            comment="Record creation time",
        ),
        # Foreign key constraint
        sa.ForeignKeyConstraint(
            ["run_id"], ["quality_gates_runs.id"], ondelete="CASCADE"
        ),
    )

    # Indexes for quality_gate_results
    op.create_index("idx_qg_result_run", "quality_gate_results", ["run_id"])
    op.create_index("idx_qg_result_gate", "quality_gate_results", ["gate_name"])
    op.create_index("idx_qg_result_status", "quality_gate_results", ["status"])
    op.create_index(
        "idx_qg_result_run_gate", "quality_gate_results", ["run_id", "gate_name"]
    )

    # ======================================================================
    # 3. quality_gates_override_audit - Override audit log
    # ======================================================================
    op.create_table(
        "quality_gates_override_audit",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # Request info
        sa.Column(
            "gate_name", sa.String(100), nullable=False, comment="Gate being overridden"
        ),
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="Related pipeline run ID",
        ),
        # Requestor
        sa.Column(
            "requestor",
            sa.String(255),
            nullable=False,
            comment="Who requested the override",
        ),
        sa.Column(
            "reason", sa.Text(), nullable=False, comment="Justification for override"
        ),
        sa.Column(
            "ticket_id",
            sa.String(100),
            nullable=True,
            comment="Related ticket/issue ID",
        ),
        # Status
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
            comment="Override status: pending, approved, denied, expired",
        ),
        # Approval
        sa.Column(
            "approver", sa.String(255), nullable=True, comment="Who approved/denied"
        ),
        sa.Column(
            "approver_comments", sa.Text(), nullable=True, comment="Approver comments"
        ),
        sa.Column(
            "approved_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Approval timestamp",
        ),
        # Expiration
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Override expiration time",
        ),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            comment="Record creation time",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            comment="Last update time",
        ),
        # Foreign key constraint (optional - run may be deleted)
        sa.ForeignKeyConstraint(
            ["run_id"], ["quality_gates_runs.id"], ondelete="SET NULL"
        ),
    )

    # Indexes for quality_gates_override_audit
    op.create_index(
        "idx_qg_override_gate", "quality_gates_override_audit", ["gate_name"]
    )
    op.create_index(
        "idx_qg_override_requestor", "quality_gates_override_audit", ["requestor"]
    )
    op.create_index(
        "idx_qg_override_status", "quality_gates_override_audit", ["status"]
    )
    op.create_index(
        "idx_qg_override_created", "quality_gates_override_audit", ["created_at"]
    )
    op.create_index(
        "idx_qg_override_pending",
        "quality_gates_override_audit",
        ["status", "expires_at"],
        postgresql_where=sa.text("status = 'pending'"),
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("quality_gates_override_audit")
    op.drop_table("quality_gate_results")
    op.drop_table("quality_gates_runs")
