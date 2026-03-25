-- student_answers -> kiro2_learning_events köprü trigger
-- Her yeni sınav yanıtı otomatik olarak learning_events'e de yazar

CREATE OR REPLACE FUNCTION fn_sync_answer_to_learning_events()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
    v_user_id TEXT;
BEGIN
    SELECT student_id INTO v_user_id
    FROM exam_sessions
    WHERE id = NEW.exam_session_id
    LIMIT 1;

    IF v_user_id IS NULL THEN
        RETURN NEW;
    END IF;

    IF EXISTS (
        SELECT 1 FROM kiro2_learning_events
        WHERE question_id::text = NEW.question_id
          AND user_id::text = v_user_id
          AND event_type = 'exam_answer'
          AND occurred_at::date = NEW.answered_at::date
    ) THEN
        RETURN NEW;
    END IF;

    INSERT INTO kiro2_learning_events (
        id, user_id, question_id, session_id,
        event_type, is_correct, theta_after, response_ms, occurred_at
    ) VALUES (
        gen_random_uuid(),
        v_user_id::uuid,
        NEW.question_id::uuid,
        NULL,
        'exam_answer',
        NEW.is_correct,
        NULL,
        (NEW.response_time_seconds * 1000)::int,
        NEW.answered_at
    );

    RETURN NEW;
EXCEPTION WHEN OTHERS THEN
    RAISE WARNING 'fn_sync_answer_to_learning_events hata: %', SQLERRM;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_sync_answer_to_le ON student_answers;

CREATE TRIGGER trg_sync_answer_to_le
AFTER INSERT OR UPDATE OF is_correct
ON student_answers
FOR EACH ROW
WHEN (NEW.is_correct IS NOT NULL)
EXECUTE FUNCTION fn_sync_answer_to_learning_events();

SELECT 'Trigger kuruldu' AS durum;
