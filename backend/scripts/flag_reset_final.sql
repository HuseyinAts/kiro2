-- Flag reset v3 - En basit, en hızlı
-- Kanıt: 77,336 history kaydının TAMAMI standard_error=0, convergence_iterations=0
-- = 0 gerçek kalibrasyon yok, hepsi bootstrap
-- Bu yüzden is_calibrated=TRUE olan HER ŞEYI FALSE yapabiliriz

BEGIN;

UPDATE question_bank
SET
    is_calibrated           = FALSE,
    calibration_sample_size = 0,
    calibration_quality_score = 0
WHERE is_calibrated = TRUE;

-- Sahte history de temizle
DELETE FROM irt_calibration_history
WHERE standard_error = 0
  AND convergence_iterations = 0
  AND log_likelihood = 0;

COMMIT;

SELECT
    COUNT(*)                                    AS toplam,
    COUNT(*) FILTER (WHERE is_calibrated=TRUE)  AS kalibre_true,
    COUNT(*) FILTER (WHERE is_calibrated=FALSE) AS kalibre_false
FROM question_bank WHERE is_active=TRUE;

SELECT COUNT(*) AS history_kalan FROM irt_calibration_history;
