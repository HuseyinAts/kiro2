-- =========================================================================
-- S255 -- student_answers.is_correct FOSIL SATIR DUZELTMESI (27 Agu 2026)
-- =========================================================================
--
-- NEDEN
-- -----
-- S254'ten once uretim UPSERT'i cakisma dalinda `is_correct`i GUNCELLEMIYORDU
-- (yalniz TESTING dali guncelliyordu, bu yuzden testler kusuru yapisal olarak
-- goremiyordu). Iki fosil sinifi olustu:
--
--   A) cevap TEMIZLENMIS (selected_answer IS NULL) ama not DURUYOR   -> 5 satir
--   B) cevap DEGISTIRILMIS, not eski cevaptan kalmis                 -> 1 satir
--
-- OLCUM (27 Agu 2026, karar oncesi):
--   toplam satir            545   (98 oturum)
--   cevapli satir           457   -> 456 dogru / 1 yanlis
--   temizlenmis+notlu         5
--   TOPLAM fosil              6   (%1,1)
--   satirlarin sahibi       hepsi test/prob hesabi -- GERCEK OGRENCI 0
--
-- URETICI DURUMU: duzelmis. Uc gecis de CANLI olculdu (27 Agu 2026):
--   dogru cevap -> E|true   ·   temizle -> <NULL>|<NULL>   ·   yanlisa degis -> A|false
-- Davranis bekcisi: tests/integration/test_save_answer_clear_persists.py
--                   ::test_is_correct_cevapla_birlikte_hareket_eder
--
-- Yani bu script SEMPTOMU degil, uretici duzeldikten SONRA kalan ARTIGI temizler.
--
-- KOSUM (Turkce icerikli SQL -> DAIMA -f, inline -c DEGIL):
--   "C:/Program Files/PostgreSQL/18/bin/psql.exe" -U postgres -p 5434 -d kiro2 \
--       -f backend/scripts/is_correct_fosil_backfill_20260827.sql
--
-- GERI ALMA (yedek tablo duruyorken):
--   UPDATE student_answers sa SET is_correct = y.is_correct
--   FROM student_answers_is_correct_yedek_20260827 y WHERE y.id = sa.id;
-- =========================================================================

\set ON_ERROR_STOP on

BEGIN;

-- -------------------------------------------------------------------------
-- 1) YEDEK -- TUM satirlar (545, ucuz). `IF NOT EXISTS` KULLANILMIYOR:
--    tablo zaten varsa script SESSIZCE yedeksiz devam ederdi.
-- -------------------------------------------------------------------------
CREATE TABLE student_answers_is_correct_yedek_20260827 AS
SELECT id,
       exam_session_id,
       question_id,
       selected_answer,
       is_correct,
       answer_changes,
       now() AS yedek_alindi
FROM student_answers;

-- -------------------------------------------------------------------------
-- 2) GUVENLIK DURDURMASI -- karar 6 satirlik bir olcume dayaniyordu.
--    Sayi buyuduyse olcum bayatlamistir; sessizce devam ETME.
-- -------------------------------------------------------------------------
DO $$
DECLARE
    temizlenmis_notlu int;
    uyusmaz int;
    toplam int;
BEGIN
    SELECT count(*) INTO temizlenmis_notlu
    FROM student_answers
    WHERE selected_answer IS NULL AND is_correct IS NOT NULL;

    SELECT count(*) INTO uyusmaz
    FROM student_answers sa
    JOIN question_content qc ON qc.id = sa.question_id
    WHERE sa.selected_answer IS NOT NULL
      AND sa.is_correct IS DISTINCT FROM
          (upper(btrim(sa.selected_answer)) = upper(btrim(qc.correct_answer)));

    toplam := temizlenmis_notlu + uyusmaz;
    RAISE NOTICE 'duzeltilecek: temizlenmis+notlu=% , uyusmaz=% , TOPLAM=%',
        temizlenmis_notlu, uyusmaz, toplam;

    IF toplam > 50 THEN
        RAISE EXCEPTION
            'GUVENLIK DURDURMASI: % satir duzeltilecekti, karar 6 satirlik olcume dayaniyordu (tavan 50). Olcumu yenile ve elle incele.',
            toplam;
    END IF;
END $$;

-- -------------------------------------------------------------------------
-- 3) SINIF A -- cevap yoksa NOT DA OLMAMALI
--    "Ogrenci cevap vermedi" ile "yanlis cevapladi" ayri seylerdir; ikincisi
--    mastery/analitigi kirletir.
-- -------------------------------------------------------------------------
UPDATE student_answers
SET is_correct = NULL
WHERE selected_answer IS NULL
  AND is_correct IS NOT NULL;

-- -------------------------------------------------------------------------
-- 4) SINIF B -- cevapli satirda not GERCEKLE uyusmali
--    Yalniz UYUSMAYAN satirlara dokunulur: 456 dogru satir YENIDEN YAZILMAZ
--    (gereksiz yazim, `answered_at` gurultusu ve genis kilit istemiyoruz).
-- -------------------------------------------------------------------------
UPDATE student_answers sa
SET is_correct = (upper(btrim(sa.selected_answer)) = upper(btrim(qc.correct_answer)))
FROM question_content qc
WHERE qc.id = sa.question_id
  AND sa.selected_answer IS NOT NULL
  AND sa.is_correct IS DISTINCT FROM
      (upper(btrim(sa.selected_answer)) = upper(btrim(qc.correct_answer)));

COMMIT;

-- -------------------------------------------------------------------------
-- 5) DOGRULAMA -- ikisi de 0 olmali, yedek satir sayisi kaynakla esit olmali
-- -------------------------------------------------------------------------
SELECT 'kalan temizlenmis+notlu' AS olcum,
       count(*) AS deger
FROM student_answers
WHERE selected_answer IS NULL AND is_correct IS NOT NULL
UNION ALL
SELECT 'kalan uyusmaz',
       count(*)
FROM student_answers sa
JOIN question_content qc ON qc.id = sa.question_id
WHERE sa.selected_answer IS NOT NULL
  AND sa.is_correct IS DISTINCT FROM
      (upper(btrim(sa.selected_answer)) = upper(btrim(qc.correct_answer)))
UNION ALL
SELECT 'yedek satir', count(*) FROM student_answers_is_correct_yedek_20260827
UNION ALL
SELECT 'kaynak satir', count(*) FROM student_answers
UNION ALL
SELECT 'yedekte FARKLI olan (=duzeltilen)',
       count(*)
FROM student_answers sa
JOIN student_answers_is_correct_yedek_20260827 y ON y.id = sa.id
WHERE sa.is_correct IS DISTINCT FROM y.is_correct;
