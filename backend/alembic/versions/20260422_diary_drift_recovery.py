"""Idempotent diary / learning journal schema for fresh DB installs.

Revision ID: diary_drift_recovery_20260422
Revises: offline_sync_pkg_20260420

Drift: diary tablolari gelistirme DB'de vardi; Alembic grafiginde yoktu
(_archive/20260119_add_diary_tables.py.disabled — ayrica eski UUID user_id).

Bu revision canli VARCHAR + PostgreSQL enum semasini models/diary.py ile hizalar.
Mevcut kurulumlarda CREATE IF NOT EXISTS ile no-op; taze DB'de tablolar olusur.

Downgrade: tablolari ve enum tiplerini kaldirir (veri kaybi).
"""

from alembic import op

revision = "diary_drift_recovery_20260422"
down_revision = "offline_sync_pkg_20260420"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- PostgreSQL enum types (SQLAlchemy SQLEnum native) ---
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE insightcategory AS ENUM (
                'TECHNICAL', 'PROCESS', 'COMMUNICATION'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE goalstatus AS ENUM (
                'ACTIVE', 'COMPLETED', 'AT_RISK', 'CANCELLED'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE reflectiondepth AS ENUM (
                'SURFACE', 'MODERATE', 'DEEP'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE exportformat AS ENUM (
                'MARKDOWN', 'PDF', 'JSON'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS diary_entries (
            id VARCHAR NOT NULL PRIMARY KEY,
            user_id VARCHAR NOT NULL
                REFERENCES users(id) ON DELETE CASCADE,
            date DATE NOT NULL,
            success_count INTEGER,
            failure_count INTEGER,
            total_tasks INTEGER,
            total_duration_minutes INTEGER,
            highlights JSONB,
            learnings JSONB,
            challenges JSONB,
            tasks_data JSONB,
            markdown_content TEXT,
            file_path VARCHAR(512),
            meta_data JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_diary_entries_user "
        "ON diary_entries (user_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_diary_entries_date "
        "ON diary_entries (date);"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_diary_entries_user_date "
        "ON diary_entries (user_id, date);"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS insights (
            id VARCHAR NOT NULL PRIMARY KEY,
            diary_entry_id VARCHAR NOT NULL
                REFERENCES diary_entries(id) ON DELETE CASCADE,
            user_id VARCHAR NOT NULL
                REFERENCES users(id) ON DELETE CASCADE,
            category insightcategory NOT NULL,
            pattern TEXT NOT NULL,
            root_cause TEXT,
            correlation TEXT,
            confidence DOUBLE PRECISION NOT NULL,
            evidence_count INTEGER,
            recommendation TEXT NOT NULL,
            priority INTEGER,
            evidence_data JSONB,
            meta_data JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_insights_diary_entry "
        "ON insights (diary_entry_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_insights_user ON insights (user_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_insights_category "
        "ON insights (category);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_insights_confidence "
        "ON insights (confidence);"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS reflections (
            id VARCHAR NOT NULL PRIMARY KEY,
            diary_entry_id VARCHAR NOT NULL
                REFERENCES diary_entries(id) ON DELETE CASCADE,
            user_id VARCHAR NOT NULL
                REFERENCES users(id) ON DELETE CASCADE,
            what_went_well TEXT,
            what_could_improve TEXT,
            what_did_i_learn TEXT,
            what_will_i_do_differently TEXT,
            additional_notes TEXT,
            depth reflectiondepth,
            depth_score DOUBLE PRECISION,
            extracted_learnings JSONB,
            action_items JSONB,
            meta_data JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_reflections_diary_entry "
        "ON reflections (diary_entry_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_reflections_user "
        "ON reflections (user_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_reflections_depth "
        "ON reflections (depth);"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS learning_entries (
            id VARCHAR NOT NULL PRIMARY KEY,
            user_id VARCHAR NOT NULL
                REFERENCES users(id) ON DELETE CASCADE,
            title VARCHAR(255) NOT NULL,
            content TEXT NOT NULL,
            summary TEXT,
            tags VARCHAR[],
            domain VARCHAR(100),
            skill_type VARCHAR(100),
            related_concepts VARCHAR[],
            concept_links JSONB,
            next_review TIMESTAMPTZ,
            review_count INTEGER,
            last_review TIMESTAMPTZ,
            retention_score DOUBLE PRECISION,
            ease_factor DOUBLE PRECISION,
            interval_days INTEGER,
            importance INTEGER,
            mastery_level DOUBLE PRECISION,
            source_type VARCHAR(50),
            source_reference VARCHAR(512),
            meta_data JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_learning_entries_user "
        "ON learning_entries (user_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_learning_entries_next_review "
        "ON learning_entries (next_review);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_learning_entries_domain "
        "ON learning_entries (domain);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_learning_entries_tags "
        "ON learning_entries USING gin (tags);"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS emotional_states (
            id VARCHAR NOT NULL PRIMARY KEY,
            user_id VARCHAR NOT NULL
                REFERENCES users(id) ON DELETE CASCADE,
            "timestamp" TIMESTAMPTZ DEFAULT NOW(),
            confidence_level INTEGER NOT NULL,
            frustration_score DOUBLE PRECISION,
            retry_count INTEGER,
            error_count INTEGER,
            flow_state BOOLEAN,
            productivity_score DOUBLE PRECISION,
            tasks_completed INTEGER,
            trigger_factors JSONB,
            task_type VARCHAR(100),
            self_awareness_score DOUBLE PRECISION,
            predicted_state VARCHAR(50),
            actual_state VARCHAR(50),
            context_notes TEXT,
            meta_data JSONB
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_emotional_states_user "
        "ON emotional_states (user_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_emotional_states_timestamp "
        "ON emotional_states (\"timestamp\");"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_emotional_states_flow "
        "ON emotional_states (flow_state);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_emotional_states_confidence "
        "ON emotional_states (confidence_level);"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS goals (
            id VARCHAR NOT NULL PRIMARY KEY,
            user_id VARCHAR NOT NULL
                REFERENCES users(id) ON DELETE CASCADE,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            specific TEXT,
            measurable TEXT,
            achievable TEXT,
            relevant TEXT,
            time_bound TIMESTAMPTZ,
            progress INTEGER,
            current_value DOUBLE PRECISION,
            target_value DOUBLE PRECISION NOT NULL,
            unit VARCHAR(50),
            status goalstatus,
            milestones JSONB,
            milestone_celebrations JSONB,
            is_at_risk BOOLEAN,
            risk_factors JSONB,
            predicted_completion TIMESTAMPTZ,
            velocity DOUBLE PRECISION,
            adjustments JSONB,
            lessons_learned JSONB,
            success_factors JSONB,
            challenges_faced JSONB,
            start_date TIMESTAMPTZ DEFAULT NOW(),
            target_date TIMESTAMPTZ NOT NULL,
            completed_at TIMESTAMPTZ,
            category VARCHAR(100),
            priority INTEGER,
            meta_data JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_goals_user ON goals (user_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_goals_status ON goals (status);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_goals_target_date "
        "ON goals (target_date);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_goals_at_risk ON goals (is_at_risk);"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS peer_comparisons (
            id VARCHAR NOT NULL PRIMARY KEY,
            user_id VARCHAR NOT NULL
                REFERENCES users(id) ON DELETE CASCADE,
            period_start DATE NOT NULL,
            period_end DATE NOT NULL,
            success_rate_percentile DOUBLE PRECISION,
            speed_percentile DOUBLE PRECISION,
            quality_percentile DOUBLE PRECISION,
            overall_percentile DOUBLE PRECISION,
            strengths JSONB,
            improvements JSONB,
            best_practices JSONB,
            is_anonymized BOOLEAN,
            noise_added BOOLEAN,
            k_anonymity INTEGER,
            peer_group_size INTEGER,
            peer_group_avg_success_rate DOUBLE PRECISION,
            meta_data JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_peer_comparisons_user "
        "ON peer_comparisons (user_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_peer_comparisons_period "
        "ON peer_comparisons (period_start, period_end);"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS diary_exports (
            id VARCHAR NOT NULL PRIMARY KEY,
            user_id VARCHAR NOT NULL
                REFERENCES users(id) ON DELETE CASCADE,
            format exportformat NOT NULL,
            date_from DATE NOT NULL,
            date_to DATE NOT NULL,
            file_path VARCHAR(512),
            file_size INTEGER,
            privacy_filter_applied BOOLEAN,
            redacted_fields JSONB,
            share_token VARCHAR(64),
            share_url VARCHAR(512),
            share_expires_at TIMESTAMPTZ,
            share_access_count INTEGER,
            is_public BOOLEAN,
            is_backup BOOLEAN,
            is_encrypted BOOLEAN,
            encryption_algorithm VARCHAR(50),
            meta_data JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_diary_exports_user "
        "ON diary_exports (user_id);"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_diary_exports_share_token "
        "ON diary_exports (share_token) WHERE share_token IS NOT NULL;"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_diary_exports_created "
        "ON diary_exports (created_at);"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS diary_exports CASCADE;")
    op.execute("DROP TABLE IF EXISTS peer_comparisons CASCADE;")
    op.execute("DROP TABLE IF EXISTS goals CASCADE;")
    op.execute("DROP TABLE IF EXISTS emotional_states CASCADE;")
    op.execute("DROP TABLE IF EXISTS learning_entries CASCADE;")
    op.execute("DROP TABLE IF EXISTS reflections CASCADE;")
    op.execute("DROP TABLE IF EXISTS insights CASCADE;")
    op.execute("DROP TABLE IF EXISTS diary_entries CASCADE;")

    op.execute("DROP TYPE IF EXISTS exportformat CASCADE;")
    op.execute("DROP TYPE IF EXISTS reflectiondepth CASCADE;")
    op.execute("DROP TYPE IF EXISTS goalstatus CASCADE;")
    op.execute("DROP TYPE IF EXISTS insightcategory CASCADE;")
