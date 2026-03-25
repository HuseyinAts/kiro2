-- Batch DELETE: sahte history kayıtları sil
-- 10K'lık batch'ler halinde - VACUUM baskısı azaltır

DO $$
DECLARE
  deleted INT;
  total   INT := 0;
BEGIN
  LOOP
    DELETE FROM irt_calibration_history
    WHERE id IN (
      SELECT id FROM irt_calibration_history
      WHERE standard_error = 0
        AND convergence_iterations = 0
        AND log_likelihood = 0
      LIMIT 5000
    );
    GET DIAGNOSTICS deleted = ROW_COUNT;
    total := total + deleted;
    EXIT WHEN deleted = 0;
    RAISE NOTICE 'Silindi: % (toplam: %)', deleted, total;
    PERFORM pg_sleep(0.1);
  END LOOP;
  RAISE NOTICE 'TAMAMLANDI: % satir silindi', total;
END;
$$;

SELECT COUNT(*) AS history_kalan FROM irt_calibration_history;
