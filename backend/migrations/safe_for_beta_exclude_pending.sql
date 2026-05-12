BEGIN;

ALTER VIEW public.v_safe_for_beta
  RENAME TO v_safe_for_beta_unfiltered;

CREATE VIEW public.v_safe_for_beta AS
SELECT *
  FROM public.v_safe_for_beta_unfiltered
 WHERE quality_review_status IN ('approved', 'unverified');

COMMENT ON VIEW public.v_safe_for_beta IS
  'Beta-safe soru havuzu. Wrapper view: pending haric. 13 May 2026.';

COMMIT;
