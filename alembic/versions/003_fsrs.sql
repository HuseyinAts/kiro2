-- KIRO2 FSRS Migration v3
-- FK YOK — users/kullanicilar tablosu garantili degil
-- question_id TEXT: question_bank.id VARCHAR ile eslesir

CREATE TABLE IF NOT EXISTS user_item_fsrs (
    user_id         UUID        NOT NULL,
    question_id     TEXT        NOT NULL,
    stability       DECIMAL(10,4) NOT NULL DEFAULT 1.0,
    difficulty      DECIMAL(4,2)  NOT NULL DEFAULT 5.0,
    due_date        TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    last_review     TIMESTAMPTZ,
    scheduled_days  INTEGER       NOT NULL DEFAULT 0,
    elapsed_days    DECIMAL(8,2)  NOT NULL DEFAULT 0.0,
    state           SMALLINT      NOT NULL DEFAULT 0
                        CHECK (state IN (0,1,2,3)),
    reps            SMALLINT      NOT NULL DEFAULT 0,
    lapses          SMALLINT      NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, question_id)
);

CREATE INDEX IF NOT EXISTS idx_fsrs_due
    ON user_item_fsrs (user_id, due_date)
    WHERE state IN (1,2,3);

CREATE INDEX IF NOT EXISTS idx_fsrs_user_state
    ON user_item_fsrs (user_id, state);

CREATE OR REPLACE FUNCTION update_fsrs_updated_at()
RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = NOW(); RETURN NEW; END; $$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_fsrs_updated_at ON user_item_fsrs;
CREATE TRIGGER trg_fsrs_updated_at
    BEFORE UPDATE ON user_item_fsrs
    FOR EACH ROW EXECUTE FUNCTION update_fsrs_updated_at();
