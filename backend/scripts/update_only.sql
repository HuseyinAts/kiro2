-- Batch UPDATE: is_calibrated=TRUE olanları FALSE yap
-- index var (idx_qbank_calibrated) - hızlı olmalı

UPDATE question_bank
SET
    is_calibrated           = FALSE,
    calibration_sample_size = 0,
    calibration_quality_score = 0
WHERE is_calibrated = TRUE;

SELECT
  COUNT(*) FILTER (WHERE is_calibrated=TRUE)  AS true_kalan,
  COUNT(*) FILTER (WHERE is_calibrated=FALSE) AS false_olan
FROM question_bank;
