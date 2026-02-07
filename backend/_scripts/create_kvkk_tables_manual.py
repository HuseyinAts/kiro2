"""Manually create KVKK tables"""
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:changeme_strong_password_here@localhost/kiro2_db')

try:
    with engine.begin() as conn:
        # Create enum types
        print("[1/6] Creating enum types...")
        conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE consent_status AS ENUM ('given', 'withdrawn', 'expired');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))

        conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE data_processing_purpose AS ENUM (
                    'service_provision', 'account_management', 'authentication',
                    'communication', 'notifications', 'support',
                    'analytics', 'performance_monitoring', 'product_improvement',
                    'marketing', 'personalization',
                    'legal_compliance', 'fraud_prevention',
                    'exam_evaluation', 'progress_tracking', 'content_recommendation'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))

        conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE export_request_status AS ENUM (
                    'pending', 'processing', 'completed', 'failed', 'expired'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))

        conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE deletion_request_status AS ENUM (
                    'pending', 'approved', 'processing', 'completed', 'rejected'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))
        print("[OK] Enum types created")

        # 1. KVKK Consents
        print("[2/6] Creating kvkk_consents table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS kvkk_consents (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                purpose data_processing_purpose NOT NULL,
                status consent_status NOT NULL,
                consent_text TEXT NOT NULL,
                privacy_policy_version VARCHAR(20) NOT NULL,
                given_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                withdrawn_at TIMESTAMPTZ,
                expires_at TIMESTAMPTZ,
                ip_address VARCHAR(45),
                user_agent VARCHAR(500),
                additional_data JSONB
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_kvkk_consents_user_id ON kvkk_consents(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_kvkk_consents_purpose ON kvkk_consents(purpose)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_kvkk_consents_status ON kvkk_consents(status)"))
        print("[OK] kvkk_consents created")

        # 2. Privacy Policy Versions
        print("[3/6] Creating kvkk_privacy_policy_versions table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS kvkk_privacy_policy_versions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                version VARCHAR(20) NOT NULL UNIQUE,
                title VARCHAR(200) NOT NULL,
                content TEXT NOT NULL,
                is_active BOOLEAN DEFAULT FALSE,
                effective_date TIMESTAMPTZ NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                created_by UUID REFERENCES users(id)
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_kvkk_policy_version ON kvkk_privacy_policy_versions(version)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_kvkk_policy_active ON kvkk_privacy_policy_versions(is_active)"))
        print("[OK] kvkk_privacy_policy_versions created")

        # 3. Data Export Requests
        print("[4/6] Creating kvkk_data_export_requests table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS kvkk_data_export_requests (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                status export_request_status NOT NULL,
                request_reason TEXT,
                export_format VARCHAR(20) NOT NULL DEFAULT 'json',
                data_categories JSONB,
                file_path VARCHAR(500),
                file_size_bytes INTEGER,
                download_url VARCHAR(500),
                download_expires_at TIMESTAMPTZ,
                requested_at TIMESTAMPTZ DEFAULT NOW(),
                processed_at TIMESTAMPTZ,
                completed_at TIMESTAMPTZ,
                error_message TEXT
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_kvkk_export_user_id ON kvkk_data_export_requests(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_kvkk_export_status ON kvkk_data_export_requests(status)"))
        print("[OK] kvkk_data_export_requests created")

        # 4. Data Deletion Requests
        print("[5/6] Creating kvkk_data_deletion_requests table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS kvkk_data_deletion_requests (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                status deletion_request_status NOT NULL,
                request_reason TEXT NOT NULL,
                deletion_type VARCHAR(50) NOT NULL DEFAULT 'full',
                data_categories JSONB,
                reviewed_by UUID REFERENCES users(id),
                review_notes TEXT,
                rejection_reason TEXT,
                requested_at TIMESTAMPTZ DEFAULT NOW(),
                reviewed_at TIMESTAMPTZ,
                processed_at TIMESTAMPTZ,
                completed_at TIMESTAMPTZ
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_kvkk_deletion_user_id ON kvkk_data_deletion_requests(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_kvkk_deletion_status ON kvkk_data_deletion_requests(status)"))
        print("[OK] kvkk_data_deletion_requests created")

        # 5. Audit Logs
        print("[6/6] Creating kvkk_audit_logs table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS kvkk_audit_logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id),
                accessed_by UUID REFERENCES users(id),
                action VARCHAR(100) NOT NULL,
                resource_type VARCHAR(100),
                resource_id VARCHAR,
                purpose data_processing_purpose,
                ip_address VARCHAR(45),
                user_agent VARCHAR(500),
                request_method VARCHAR(10),
                request_path VARCHAR(500),
                details JSONB,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_kvkk_audit_user_id ON kvkk_audit_logs(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_kvkk_audit_accessed_by ON kvkk_audit_logs(accessed_by)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_kvkk_audit_action ON kvkk_audit_logs(action)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_kvkk_audit_created_at ON kvkk_audit_logs(created_at)"))
        print("[OK] kvkk_audit_logs created")

        print("\nSUCCESS: All KVKK compliance tables created!")

except Exception as e:
    print(f'ERROR: {e}')
