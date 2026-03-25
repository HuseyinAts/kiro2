DELETE FROM irt_calibration_history
WHERE standard_error=0
  AND convergence_iterations=0
  AND log_likelihood=0;

SELECT COUNT(*) AS history_remaining FROM irt_calibration_history;
