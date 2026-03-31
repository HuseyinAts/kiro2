"""
IRT Calibration Runner — Manuel çalıştırma scripti
===================================================
Çalıştırma:
  python scripts/irt_calibration_runner.py --dry-run
  python scripts/irt_calibration_runner.py --limit 50
  python scripts/irt_calibration_runner.py --min-responses 50
  python scripts/irt_calibration_runner.py --subject MATEMATIK
  python scripts/irt_calibration_runner.py  (tümü)
"""

import argparse
import os
import sys
import time

import numpy as np
import psycopg2

sys.path.insert(0, r"C:\Users\husey\kiro2\backend")
from app.services.irt_calibrator import MIN_RESPONSES_CTT, calibrate_item

DB = dict(
    host=os.environ.get("PGHOST", "localhost"),
    port=int(os.environ.get("PGPORT", "5434")),
    dbname=os.environ.get("PGDATABASE", "kiro2"),
    user=os.environ.get("PGUSER", "postgres"),
    password=os.environ["PGPASSWORD"],
)

FETCH_CANDIDATES_SQL = """
SELECT
    q.id::text AS question_id,
    q.subject_area,
    q.irt_discrimination AS cur_a,
    q.irt_difficulty     AS cur_b,
    q.irt_guessing       AS cur_c,
    q.is_calibrated,
    vc.n_responses
FROM question_bank q
JOIN v_calibration_candidates vc ON vc.question_id = q.id::text
WHERE q.is_active = TRUE
  AND q.is_calibrated = FALSE
  AND vc.n_responses >= %(min_responses)s
  {subject_filter}
ORDER BY vc.n_responses DESC
LIMIT %(limit)s
"""

FETCH_RESPONSES_SQL = """
SELECT is_correct::int AS r
FROM (
    SELECT is_correct, occurred_at ts
    FROM kiro2_learning_events
    WHERE question_id::text = %(qid)s
      AND event_type IN ('cat_answer','exam_answer')
      AND is_correct IS NOT NULL
) x ORDER BY ts
"""

UPDATE_SQL = """
UPDATE question_bank SET
    irt_discrimination=%(a)s, irt_difficulty=%(b)s, irt_guessing=%(c)s,
    is_calibrated=%(calibrated)s, calibration_sample_size=%(n)s,
    calibration_quality_score=%(qs)s, updated_at=NOW()
WHERE id::text=%(qid)s
"""

INSERT_HISTORY_SQL = """
INSERT INTO irt_calibration_history (
    id, question_id, calibration_date, calibration_method,
    sample_size, old_discrimination, old_difficulty, old_guessing, old_upper_asymptote,
    new_discrimination, new_difficulty, new_guessing, new_upper_asymptote,
    standard_error, convergence_iterations, log_likelihood,
    discrimination_ci_lower, discrimination_ci_upper,
    difficulty_ci_lower, difficulty_ci_upper
) VALUES (
    gen_random_uuid(), %(qid)s, NOW(), %(method)s,
    %(n)s, %(old_a)s, %(old_b)s, %(old_c)s, 1.0,
    %(new_a)s, %(new_b)s, %(new_c)s, 1.0,
    %(se)s, %(iters)s, %(ll)s,
    %(a_lo)s, %(a_hi)s, %(b_lo)s, %(b_hi)s
)
"""


def quality_score(result) -> float:
    s = 0.0
    if result.converged:
        s += 0.40
    if result.item_df > 0 and (result.item_chi2 / result.item_df) < 2.0:
        s += 0.30
    if result.is_acceptable:
        s += 0.20
    if result.n_responses >= 200:
        s += 0.10
    return round(s, 2)


def ci_params(result) -> dict:
    se_a = result.rmse * 0.5 + 0.05
    se_b = result.rmse * 0.8 + 0.10
    ll = round(-result.rmse * result.n_responses, 4) if result.n_responses else -1.0
    return dict(
        se=round(se_b, 4),
        iters=max(1, 0 if result.method == "ctt_fallback" else 10),
        ll=ll,
        a_lo=round(result.a - 1.96 * se_a, 4),
        a_hi=round(result.a + 1.96 * se_a, 4),
        b_lo=round(result.b - 1.96 * se_b, 4),
        b_hi=round(result.b + 1.96 * se_b, 4),
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--min-responses", type=int, default=MIN_RESPONSES_CTT)
    parser.add_argument("--subject", type=str, default="")
    parser.add_argument(
        "--force",
        action="store_true",
        help="is_calibrated=TRUE olanları da yeniden kalibre et",
    )
    parser.add_argument(
        "--include-synthetic",
        action="store_true",
        help="Sentetik yanıtları da dahil et (kiro2_learning_events_synthetic)",
    )
    args = parser.parse_args()

    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    # Minimum gercek event guard
    cur.execute(
        "SELECT COUNT(*) FROM kiro2_learning_events"
        " WHERE event_type IN ('cat_answer', 'exam_answer')"
    )
    real_count = cur.fetchone()[0]
    if real_count < 500 and not args.force:
        print(
            f"UYARI: Sadece {real_count} gercek event var. "
            "Kalibrasyon icin minimum 500 gerekli."
        )
        print("--force ile zorlayabilirsiniz.")
        conn.close()
        return

    # Aday sorular
    subj = f"AND q.subject_area = '{args.subject}'" if args.subject else ""
    if args.force:
        fetch_sql = FETCH_CANDIDATES_SQL.replace("AND q.is_calibrated = FALSE", "")
    else:
        fetch_sql = FETCH_CANDIDATES_SQL
    fetch_sql = fetch_sql.format(subject_filter=subj)

    cur.execute(fetch_sql, {"limit": args.limit, "min_responses": args.min_responses})
    candidates = cur.fetchall()

    print("=" * 70)
    print(f"IRT CALIBRATION RUNNER  (dry_run={args.dry_run})")
    print("=" * 70)
    print(f"Aday soru: {len(candidates)}")
    if not candidates:
        print("Yeterli yanıt biriken soru yok.")
        print(f"Minimum eşik: {args.min_responses} yanıt/soru")
        cur.execute(
            """
            SELECT
              SUM(CASE WHEN (le_cnt + sa_cnt) >= %(t)s THEN 1 ELSE 0 END) AS ready,
              MAX(le_cnt + sa_cnt) AS max_resp
            FROM (
              SELECT q.id,
                (SELECT COUNT(*) FROM kiro2_learning_events le WHERE le.question_id::text=q.id::text) AS le_cnt,
                (SELECT COUNT(*) FROM student_answers sa WHERE sa.question_id::text=q.id::text) AS sa_cnt
              FROM question_bank q WHERE q.is_active=TRUE AND q.is_calibrated=FALSE
              LIMIT 500
            ) sub
        """,
            {"t": args.min_responses},
        )
        row = cur.fetchone()
        print(f"Hazır soru (>={args.min_responses} yanıt): {row[0] or 0}")
        print(f"En çok yanıt alan soru: {row[1] or 0} yanıt")
        print(
            f"\nSonraki kontrol: {args.min_responses} yanıt birikince tekrar çalıştır."
        )
        conn.close()
        return

    # Tum adaylar zaten view'da filtrelenmis
    filtered = list(candidates)
    print(f"Esigi gecen: {len(filtered)} (>={args.min_responses} yanit)")

    if not filtered:
        print("Esigi gecen soru yok.")
        conn.close()
        return

    # Kalibrasyon
    results_summary = []
    ok3pl = ok_ctt = skipped = failed = 0
    t_start = time.time()

    for i, (qid, subj_area, old_a, old_b, old_c, was_cal, n_resp) in enumerate(
        filtered
    ):
        cur.execute(FETCH_RESPONSES_SQL, {"qid": qid})
        rows = cur.fetchall()
        vec = np.array([float(r[0]) for r in rows])

        t0 = time.time()
        res = calibrate_item(qid, vec)
        dt = round(time.time() - t0, 2)

        qs = quality_score(res)
        ci = ci_params(res)

        status_icon = {
            "3pl_em": "[3PL]",
            "ctt_fallback": "[CTT]",
            "skipped": "[SKP]",
        }.get(res.method, "[???]")

        print(
            f"[{i + 1:>4}/{len(filtered)}] {status_icon} "
            f"| n={res.n_responses:>4} | "
            f"a={res.a:.3f} b={res.b:+.3f} c={res.c:.3f} "
            f"| conv={'Y' if res.converged else 'N'} "
            f"| fit={res.item_chi2 / res.item_df:.1f}"
            if res.item_df
            else f"[{i + 1:>4}/{len(filtered)}] {status_icon} | n={res.n_responses:>4} | "
            f"a={res.a:.3f} b={res.b:+.3f} c={res.c:.3f}"
            f" ({dt}s) {res.warning[:40] if res.warning else ''}"
        )

        if res.method == "3pl_em":
            ok3pl += 1
        elif res.method == "ctt_fallback":
            ok_ctt += 1
        else:
            skipped += 1

        if not args.dry_run and res.method in ("3pl_em", "ctt_fallback"):
            try:
                cur.execute(
                    UPDATE_SQL,
                    dict(
                        a=round(res.a, 4),
                        b=round(res.b, 4),
                        c=round(res.c, 4),
                        calibrated=res.converged,
                        n=res.n_responses,
                        qs=qs,
                        qid=qid,
                    ),
                )
                cur.execute(
                    INSERT_HISTORY_SQL,
                    dict(
                        qid=qid,
                        method=res.method,
                        n=res.n_responses,
                        old_a=old_a,
                        old_b=old_b,
                        old_c=old_c,
                        new_a=round(res.a, 4),
                        new_b=round(res.b, 4),
                        new_c=round(res.c, 4),
                        **ci,
                    ),
                )
                if (i + 1) % 20 == 0:
                    conn.commit()
                    print(f"  [CP] {i + 1} soru işlendi, commit yapıldı")
            except Exception as e:
                failed += 1
                print(f"  FAIL DB hata: {e}")

    if not args.dry_run:
        conn.commit()

    total_time = round(time.time() - t_start, 1)
    print("\n" + "=" * 70)
    print(f"SONUÇ: 3PL={ok3pl} | CTT={ok_ctt} | Atlandı={skipped} | Hata={failed}")
    print(
        f"Süre: {total_time}s | {'DRY RUN — DB YAZILMADI' if args.dry_run else 'DB GÜNCELLENDİ ✅'}"
    )
    if args.dry_run:
        print(
            f"\nUygulamak için: python scripts/irt_calibration_runner.py --limit {args.limit}"
        )
    conn.close()


if __name__ == "__main__":
    main()
