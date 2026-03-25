"""
IRT Sentetik Veri Üretici
=========================
Gerçek öğrenci olmadan pipeline'ı test etmek için kullanılır.
Kalibrasyon havuzundaki sorulara simüle edilmiş yanıtlar üretir.

UYARI: Bu veriler SADECE pipeline testi içindir.
Üretilen is_calibrated=TRUE kayıtları 'synthetic' methodu ile işaretlenir
ve gerçek kalibrasyonla karışmaz.

Çalıştırma:
  python scripts/generate_synthetic_responses.py --dry-run
  python scripts/generate_synthetic_responses.py --n-students 50
  python scripts/generate_synthetic_responses.py --n-students 200 --clear
"""
import argparse, math, random, uuid
from datetime import datetime, timedelta, timezone
import numpy as np
import psycopg2

DB = dict(host="localhost", port=5434, dbname="kiro2",
          user="postgres", password="changeme_strong_password_here")

ADMIN_USER = "de384ad3-93f6-4ff4-8efb-d430bdc55733"


def p3pl(theta: float, a: float, b: float, c: float) -> float:
    """3PL ICC - bir öğrencinin soruyu doğru yanıtlama olasılığı."""
    return c + (1.0 - c) / (1.0 + math.exp(-a * (theta - b)))


def simulate_student(theta_true: float, questions: list) -> list:
    """
    Gerçek yeteneği theta_true olan bir öğrencinin yanıtlarını simüle et.
    Her soru için P(doğru|θ, a, b, c) ile Bernoulli çek.
    """
    responses = []
    for q in questions:
        prob = p3pl(theta_true, q["a"], q["b"], q["c"])
        is_correct = random.random() < prob
        responses.append({
            "question_id": q["id"],
            "is_correct": is_correct,
            "response_ms": random.randint(8000, 120000),
        })
    return responses


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-students",  type=int, default=100,
                        help="Simüle edilecek öğrenci sayısı")
    parser.add_argument("--dry-run",     action="store_true",
                        help="DB'ye yazma, sadece istatistikleri göster")
    parser.add_argument("--clear",       action="store_true",
                        help="Önceki sentetik verileri temizle")
    parser.add_argument("--subject",     type=str, default="",
                        help="Sadece bu dersi işle (örn. MATEMATIK)")
    args = parser.parse_args()

    conn = psycopg2.connect(**DB)
    cur  = conn.cursor()

    # Önceki sentetik verileri temizle
    if args.clear and not args.dry_run:
        cur.execute("""
            DELETE FROM kiro2_learning_events
            WHERE event_type = 'synthetic_response'
        """)
        conn.commit()
        print("Eski sentetik veriler temizlendi.")

    # Kalibrasyon havuzundaki soruları çek
    subj_filter = "AND subject_area = %s" if args.subject else ""
    cur.execute(f"""
        SELECT id::text, subject_area,
               irt_discrimination AS a,
               irt_difficulty     AS b,
               irt_guessing       AS c
        FROM question_bank
        WHERE is_calib_pool = TRUE
          AND is_active = TRUE
          {subj_filter}
        ORDER BY subject_area, irt_difficulty
    """, (args.subject,) if args.subject else ())
    questions = [dict(zip(["id","subject","a","b","c"], row)) for row in cur.fetchall()]
    print(f"Kalibrasyon havuzu: {len(questions)} soru")
    print(f"Simüle edilecek: {args.n_students} öğrenci")

    if not questions:
        print("Kalibrasyon havuzu boş! Önce add_calib_pool.sql çalıştır.")
        conn.close(); return

    # Öğrenci theta dağılımı: N(0, 1) - YKS öğrenci popülasyonu
    thetas = np.random.normal(0.0, 1.0, args.n_students)
    thetas = np.clip(thetas, -3.0, 3.0)

    inserted = 0
    subject_counts: dict = {}

    for i, theta_true in enumerate(thetas):
        # Her öğrenci rastgele 10-20 soru görür (tüm havuzu değil)
        n_q = random.randint(10, 20)
        sample = random.sample(questions, min(n_q, len(questions)))

        responses = simulate_student(float(theta_true), sample)
        sim_user_id = str(uuid.uuid4())  # Her öğrenci için sahte UUID
        sim_time = datetime.now(timezone.utc) - timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23)
        )

        for resp in responses:
            subj = next(q["subject"] for q in questions if q["id"] == resp["question_id"])
            subject_counts[subj] = subject_counts.get(subj, 0) + 1

            if not args.dry_run:
                cur.execute("""
                    INSERT INTO kiro2_learning_events (
                        id, user_id, question_id, session_id,
                        event_type, is_correct, theta_after, response_ms, occurred_at
                    ) VALUES (%s, %s, %s, NULL, 'synthetic_response', %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    str(uuid.uuid4()),
                    sim_user_id,
                    resp["question_id"],
                    resp["is_correct"],
                    round(float(theta_true), 3),
                    resp["response_ms"],
                    sim_time + timedelta(seconds=random.randint(0, 3600)),
                ))
                inserted += 1

        if (i + 1) % 20 == 0:
            if not args.dry_run:
                conn.commit()
            print(f"  {i+1}/{args.n_students} öğrenci işlendi...")

    if not args.dry_run:
        conn.commit()

    # İstatistikler
    total_resp = sum(subject_counts.values())
    print(f"\n{'='*60}")
    print(f"SONUÇ: {args.n_students} öğrenci × ort. {total_resp//args.n_students} soru = {total_resp} yanıt")
    print(f"{'DRY RUN - DB yazılmadı' if args.dry_run else f'{inserted} yanıt DB yazıldı'}")

    print(f"\nDers bazında yanıt sayıları:")
    for subj, cnt in sorted(subject_counts.items(), key=lambda x: -x[1]):
        avg_per_q = cnt / (len([q for q in questions if q["subject"] == subj]) or 1)
        status = "[CTT OK]" if avg_per_q >= 50 else ("[3PL?]" if avg_per_q >= 20 else "[wait]")
        print(f"  {status} {subj:12s}: {cnt:5d} yanıt | soru başına ort: {avg_per_q:.1f}")

    if not args.dry_run:
        # Kalibre edilebilir soru sayısı kontrol
        cur.execute("""
            SELECT COUNT(DISTINCT question_id) AS kalibre_adayi
            FROM (
                SELECT question_id, COUNT(*) AS n
                FROM kiro2_learning_events
                WHERE event_type IN ('cat_answer','exam_answer','synthetic_response')
                  AND is_correct IS NOT NULL
                GROUP BY question_id
                HAVING COUNT(*) >= 50
            ) sub
        """)
        kalibre = cur.fetchone()[0]
        print(f"\n{'='*60}")
        print(f"Kalibre edilebilir soru (>=50 yanıt): {kalibre}")
        print(f"Çalıştır: python scripts/irt_calibration_runner.py --min-responses 50 --limit 100")

    conn.close()


if __name__ == "__main__":
    main()
