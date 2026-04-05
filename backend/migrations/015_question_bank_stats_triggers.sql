-- Migration 015: question_bank istatistik trigger'lari
-- Tarih: 2026-03-31
-- Aciklama: student_answers ve kiro2_learning_events INSERT'lerinde
--           question_bank.times_asked/correct/wrong otomatik guncellenir.

-- Trigger 1: kiro2_learning_events -> question_bank
CREATE OR REPLACE FUNCTION fn_update_qb_stats_from_le()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.event_type NOT IN ('exam_answer', 'cat_answer') THEN
        RETURN NEW;
    END IF;
    UPDATE question_bank SET
        times_asked    = times_asked + 1,
        times_correct  = times_correct + CASE WHEN NEW.is_correct THEN 1 ELSE 0 END,
        times_wrong    = times_wrong   + CASE WHEN NEW.is_correct THEN 0 ELSE 1 END,
        last_used_date = NOW()
    WHERE id::text = NEW.question_id::text;
    RETURN NEW;
EXCEPTION WHEN OTHERS THEN
    RAISE WARNING 'fn_update_qb_stats_from_le hata: %', SQLERRM;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_update_qb_stats ON kiro2_learning_events;
CREATE TRIGGER trg_update_qb_stats
AFTER INSERT ON kiro2_learning_events
FOR EACH ROW EXECUTE FUNCTION fn_update_qb_stats_from_le();

-- Trigger 2: student_answers -> question_bank (exam sistemi icin)
CREATE OR REPLACE FUNCTION fn_update_qb_stats_from_sa()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    UPDATE question_bank SET
        times_asked   = times_asked + 1,
        times_correct = times_correct + CASE WHEN NEW.is_correct THEN 1 ELSE 0 END,
        times_wrong   = times_wrong   + CASE WHEN NEW.is_correct THEN 0 ELSE 1 END,
        last_used_date = NOW()
    WHERE id::text = NEW.question_id::text;
    RETURN NEW;
EXCEPTION WHEN OTHERS THEN
    RAISE WARNING 'fn_update_qb_stats_from_sa hata: %', SQLERRM;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_update_qb_stats_sa ON student_answers;
CREATE TRIGGER trg_update_qb_stats_sa
AFTER INSERT ON student_answers
FOR EACH ROW EXECUTE FUNCTION fn_update_qb_stats_from_sa();

-- Geri donuk guncelleme: mevcut student_answers verisini question_bank'e yansit
UPDATE question_bank qb SET
    times_asked   = GREATEST(qb.times_asked, sub.asked),
    times_correct = GREATEST(qb.times_correct, sub.correct),
    times_wrong   = GREATEST(qb.times_wrong, sub.wrong)
FROM (
    SELECT
        question_id::text AS qid,
        COUNT(*) AS asked,
        SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) AS correct,
        SUM(CASE WHEN NOT is_correct THEN 1 ELSE 0 END) AS wrong
    FROM student_answers
    GROUP BY question_id
) sub
WHERE qb.id::text = sub.qid;

-- Geri donuk guncelleme: kiro2_learning_events gercek yanitlari
UPDATE question_bank qb SET
    times_asked   = GREATEST(qb.times_asked, sub.asked),
    times_correct = GREATEST(qb.times_correct, sub.correct),
    times_wrong   = GREATEST(qb.times_wrong, sub.wrong)
FROM (
    SELECT
        question_id::text AS qid,
        COUNT(*) AS asked,
        SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) AS correct,
        SUM(CASE WHEN NOT is_correct THEN 1 ELSE 0 END) AS wrong
    FROM kiro2_learning_events
    WHERE event_type IN ('exam_answer', 'cat_answer')
    GROUP BY question_id
) sub
WHERE qb.id::text = sub.qid;
