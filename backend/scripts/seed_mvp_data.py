#!/usr/bin/env python3
"""
MVP Beta Launch - Seed Data Script
Creates test users directly in PostgreSQL for MVP testing.

Uses bcrypt (passlib) for password hashing - compatible with auth system.
Idempotent: skips users that already exist.

Usage:
    cd backend
    python scripts/seed_mvp_data.py
"""

import os
import sys
import uuid
from typing import Any

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg  # psycopg3 (requirements.txt: psycopg[binary]); psycopg2 CI'da yok
from passlib.context import CryptContext

# Password hasher (must match auth system)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# MVP password from env var (fallback for backwards compatibility)
MVP_DEFAULT_PASSWORD = os.getenv("MVP_PASSWORD", "Kiro2Beta2026@x")

# Database connection - strip asyncpg driver for sync psycopg3
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    sys.exit(
        "ERROR: DATABASE_URL env var required. Example: DATABASE_URL=postgresql+asyncpg://postgres:pass@localhost:5434/kiro2"
    )
# Convert async URL to sync: remove +asyncpg
SYNC_URL = DATABASE_URL.replace("+asyncpg", "").replace("postgresql://", "")
# Parse: user:pass@host:port/dbname
try:
    auth_host, dbname = SYNC_URL.rsplit("/", 1)
    userpass, hostport = auth_host.rsplit("@", 1)
    db_user, db_pass = userpass.split(":", 1)
    db_host, db_port = hostport.split(":", 1)
except ValueError:
    print(f"ERROR: Cannot parse DATABASE_URL: {DATABASE_URL}")
    print("Expected format: postgresql+asyncpg://user:pass@host:port/dbname")
    sys.exit(1)

# MVP Test Users
MVP_USERS = [
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "mvp-student@kiro2.com")),
        "email": "test@kiro2.com",
        "username": "test_user",
        "password": MVP_DEFAULT_PASSWORD,
        "first_name": "Test",
        "last_name": "User",
        "role": "STUDENT",
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "mvp-ogrenci@kiro2.com")),
        "email": "ogrenci@kiro2.com",
        "username": "ogrenci_mvp",
        "password": MVP_DEFAULT_PASSWORD,
        "first_name": "Demo",
        "last_name": "Ogrenci",
        "role": "STUDENT",
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "mvp-ogretmen@kiro2.com")),
        "email": "ogretmen@kiro2.com",
        "username": "ogretmen_mvp",
        "password": MVP_DEFAULT_PASSWORD,
        "first_name": "Demo",
        "last_name": "Ogretmen",
        "role": "TEACHER",
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "mvp-admin@kiro2.com")),
        "email": "admin@kiro2.com",
        "username": "admin_mvp",
        "password": MVP_DEFAULT_PASSWORD,
        "first_name": "Demo",
        "last_name": "Admin",
        "role": "ADMIN",
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "mvp-veli@kiro2.com")),
        "email": "veli@kiro2.com",
        "username": "veli_mvp",
        "password": MVP_DEFAULT_PASSWORD,
        "first_name": "Demo",
        "last_name": "Veli",
        "role": "PARENT",
    },
]

INSERT_SQL = """
INSERT INTO users (
    id, email, username, password_hash,
    first_name, last_name, role,
    is_active, is_verified,
    total_xp, level,
    is_premium, is_2fa_enabled,
    elo_rating, is_parent
)
VALUES (
    %(id)s, %(email)s, %(username)s, %(password_hash)s,
    %(first_name)s, %(last_name)s, %(role)s::userrole,
    TRUE, TRUE,
    0, 1,
    FALSE, FALSE,
    1000, FALSE
)
ON CONFLICT (email) DO NOTHING
"""


# GF6w / admin soru ekleme: soru_bankasi_service MATEMATIK topic_hierarchy satırı ister (taze CI DB).
MVP_MAT_TOPIC_ID = str(uuid.uuid5(uuid.NAMESPACE_DNS, "kiro2.mvp.topic.MVP.MAT.GOLDEN"))
ENSURE_TOPIC_SQL = """
INSERT INTO topic_hierarchy (
    id, level, parent_id, code, name_tr, name_en,
    subject_area, osym_relevance, osym_frequency, total_questions,
    average_difficulty, is_active, created_at, updated_at
) VALUES (
    %s, 1, NULL, 'MVP.MAT.GOLDEN', 'MVP Matematik (Golden seed)',
    'MVP Math Golden', 'MATEMATIK', 0, 0, 0, 0, true, NOW(), NOW()
)
ON CONFLICT (code) DO NOTHING
"""


PROFILE_INSERT_SQL = """
INSERT INTO student_profiles (
    id, user_id, grade_level, veli_onay,
    current_level, total_study_hours,
    total_questions_solved, correct_answers,
    irt_ability, hedef_sinav
)
VALUES (
    %(id)s, %(id)s, 12, TRUE,
    0.5, 0, 0, 0, 0.0, 'TYT'
)
ON CONFLICT (id) DO NOTHING
"""


ORG_INSERT_SQL = """
INSERT INTO organizations (
    id, name, org_type, status, kvkk_role, license_seats
)
VALUES (
    'org_legacy_default', 'Varsayilan Organizasyon', 'school', 'active', 'controller', 0
)
ON CONFLICT (id) DO NOTHING
"""


# ---------------------------------------------------------------------------
# Golden Flow soru seti (28 Agu 2026, GF3c/GF2wB/GF12/GF13/GF40/GF128 zinciri)
# ---------------------------------------------------------------------------
# Bos CI veritabaninda sinav-uretimi akislari calisamiyordu: exam create,
# placement/start, CAT start ve osym/random-questions hepsi safe_for_beta
# kapisindan soru ceker. Kapinin filtreleri (core/quality_gate.py +
# mv_safe_for_beta): quality_review_status='human_verified',
# pipeline_metadata.student_coherent=true, is_ai_generated=false,
# question_text >= 50 karakter, secenekler >= 2 karakter ve birbirinden
# farkli. Asagidaki 12 soru bu filtrelerin TAMAMINI saglar; cevap anahtari
# elle dogrulanmistir (reward-hacking-check: oracle icerikten okunur).
GOLDEN_QUESTIONS: list[dict[str, Any]] = [
    {
        "n": 1,
        "anchor": True,
        "diff": "EASY",
        "b": -1.2,
        "text": "Bir sayının 3 katının 5 fazlası 41 olduğuna göre bu sayı kaçtır?",
        "a": "10",
        "b_opt": "11",
        "c": "12",
        "d": "13",
        "ans": "C",
        "exp": "3x + 5 = 41 ise 3x = 36, x = 12 olur.",
    },
    {
        "n": 2,
        "anchor": False,
        "diff": "HARD",
        "b": 1.0,
        "text": "İki basamaklı bir doğal sayının rakamları toplamı 9'dur. Rakamları yer değiştirdiğinde sayı 27 artmaktadır. Buna göre bu sayı kaçtır?",
        "a": "27",
        "b_opt": "36",
        "c": "45",
        "d": "63",
        "ans": "B",
        "exp": "Sayı 10a+b; b+a=9 ve 10b+a-(10a+b)=27 ise b-a=3, a=3, b=6; sayı 36.",
    },
    {
        "n": 3,
        "anchor": False,
        "diff": "MEDIUM",
        "b": -0.2,
        "text": "x + 2y = 16 ve x - y = 1 denklemlerini birlikte sağlayan x + y toplamı kaçtır?",
        "a": "10",
        "b_opt": "11",
        "c": "12",
        "d": "13",
        "ans": "B",
        "exp": "x = y + 1; (y+1) + 2y = 16 ise y = 5, x = 6; x + y = 11.",
    },
    {
        "n": 4,
        "anchor": True,
        "diff": "MEDIUM",
        "b": 0.0,
        "text": "Ardışık üç çift doğal sayının toplamı 42 olduğuna göre bu sayıların en büyüğü kaçtır?",
        "a": "12",
        "b_opt": "14",
        "c": "16",
        "d": "18",
        "ans": "C",
        "exp": "n-2, n, n+2 toplami 3n = 42; n = 14, en buyuk 16.",
    },
    {
        "n": 5,
        "anchor": False,
        "diff": "EASY",
        "b": -1.0,
        "text": "Bir kenarının uzunluğu 6 santimetre olan karenin çevresi kaç santimetredir?",
        "a": "18 cm",
        "b_opt": "20 cm",
        "c": "24 cm",
        "d": "36 cm",
        "ans": "C",
        "exp": "Kare cevresi 4 kenar: 4 x 6 = 24 cm.",
    },
    {
        "n": 6,
        "anchor": False,
        "diff": "MEDIUM",
        "b": 0.2,
        "text": "Yüzde 20'si 15 olan bir sayının yüzde 40'ı kaçtır? İşlemlerinizi oran orantı kurarak yapınız.",
        "a": "25",
        "b_opt": "30",
        "c": "35",
        "d": "45",
        "ans": "B",
        "exp": "Sayi 15 / 0.20 = 75; 75 x 0.40 = 30.",
    },
    {
        "n": 7,
        "anchor": True,
        "diff": "EASY",
        "b": -0.8,
        "text": "2 üzeri 5 ile 2 üzeri 3 sayılarının çarpımı olan işlemin sonucu kaçtır?",
        "a": "64",
        "b_opt": "128",
        "c": "256",
        "d": "512",
        "ans": "C",
        "exp": "2^5 x 2^3 = 2^8 = 256.",
    },
    {
        "n": 8,
        "anchor": False,
        "diff": "HARD",
        "b": 0.8,
        "text": "Bir bölme işleminde bölünen 85, bölen 7 olduğuna göre bölüm ile kalanın toplamı kaçtır?",
        "a": "11",
        "b_opt": "12",
        "c": "13",
        "d": "14",
        "ans": "C",
        "exp": "85 = 7 x 12 + 1; bolum 12, kalan 1; toplam 13.",
    },
    {
        "n": 9,
        "anchor": False,
        "diff": "HARD",
        "b": 1.2,
        "text": "|x - 3| = 5 denklemini sağlayan x değerlerinin çarpımı kaçtır? Mutlak değer tanımını kullanınız.",
        "a": "-16",
        "b_opt": "-10",
        "c": "10",
        "d": "16",
        "ans": "A",
        "exp": "x - 3 = 5 veya x - 3 = -5; x = 8 veya x = -2; carpim -16.",
    },
    {
        "n": 10,
        "anchor": False,
        "diff": "MEDIUM",
        "b": -0.3,
        "text": "f(x) = 3x + 2 biçiminde tanımlanan fonksiyon için f(6) değeri kaçtır?",
        "a": "18",
        "b_opt": "20",
        "c": "22",
        "d": "24",
        "ans": "B",
        "exp": "f(6) = 3 x 6 + 2 = 20.",
    },
    {
        "n": 11,
        "anchor": True,
        "diff": "MEDIUM",
        "b": 0.3,
        "text": "3, 7, 11, 15, ... biçiminde devam eden sayı örüntüsünün 10. terimi kaçtır?",
        "a": "35",
        "b_opt": "39",
        "c": "43",
        "d": "47",
        "ans": "B",
        "exp": "a_n = 3 + (n-1) x 4; a_10 = 3 + 36 = 39.",
    },
    {
        "n": 12,
        "anchor": False,
        "diff": "MEDIUM",
        "b": 0.1,
        "text": "Bir torbada 4 kırmızı ve 6 mavi top vardır. Torbadan rastgele çekilen bir topun kırmızı olma olasılığı kaçtır?",
        "a": "1/5",
        "b_opt": "2/5",
        "c": "3/5",
        "d": "1/2",
        "ans": "B",
        "exp": "P(kirmizi) = 4 / (4 + 6) = 2/5.",
    },
]

QB_INSERT = """
INSERT INTO question_bank
    (id, soru_hash, primary_topic_id, is_active, is_public,
     is_ai_generated, review_status, is_anchor, created_at, updated_at)
VALUES
    (%(id)s, %(hash)s, %(topic)s, TRUE, TRUE,
     FALSE, 'APPROVED', %(anchor)s, NOW(), NOW())
ON CONFLICT (id) DO NOTHING
"""

QC_INSERT = """
INSERT INTO question_content
    (id, question_text, option_a, option_b, option_c, option_d,
     correct_answer, explanation)
VALUES
    (%(id)s, %(text)s, %(a)s, %(b)s, %(c)s, %(d)s, %(ans)s, %(exp)s)
ON CONFLICT (id) DO NOTHING
"""

QM_INSERT = """
INSERT INTO question_metadata
    (id, bloom_level, bloom_category, exam_type, subject_area, grade_level,
     osym_format_compliant, pipeline_metadata,
     morphology_complexity, word_count, unique_word_count,
     average_word_length, readability_score, pedagogical_status)
VALUES
    (%(id)s, 3, 'Uygulama', 'TYT', 'MATEMATIK', 11,
     TRUE, %(pm)s,
     0.35, %(wc)s, %(uwc)s, %(awl)s, 65.0, 'ACTIVE')
ON CONFLICT (id) DO NOTHING
"""

QS_INSERT = """
INSERT INTO question_statistics
    (id, difficulty_level, irt_based_difficulty, student_success_rate,
     difficulty_update_count, irt_discrimination, irt_difficulty,
     irt_guessing, irt_upper_asymptote, is_calibrated,
     calibration_sample_size, calibration_quality_score,
     irt_a, irt_b, irt_c, irt_calibrated, irt_n_responses, irt_method,
     is_calib_pool, times_asked, times_correct, times_wrong, times_skipped,
     average_response_time, median_response_time, exposure_rate,
     quality_score, quality_review_status, reviewed_at)
VALUES
    (%(id)s, %(diff)s, %(diff_l)s, 0.55,
     0, 1.0, %(b)s,
     0.25, 1.0, TRUE,
     200, 0.9,
     1.0, %(b)s, 0.25, TRUE, 200, 'seed',
     TRUE, 0, 0, 0, 0,
     45.0, 45.0, 0.0,
     0.9, 'human_verified', NOW())
ON CONFLICT (id) DO NOTHING
"""


def seed_golden_questions(cur) -> int:
    """12 golden soruyu 4 tabloya idempotent yazar; eklenen bank sayisini doner."""
    import hashlib
    import json

    created = 0
    for q in GOLDEN_QUESTIONS:
        # safe_for_beta / sinav motoru filtre on-kontrolleri — filtreyi
        # gecemeyecek bir soru sessizce yutulmasin, seed aninda patlasin.
        assert len(q["text"]) >= 50, f"golden q{q['n']}: metin < 50 karakter"
        opts = [q["a"], q["b_opt"], q["c"], q["d"]]
        assert all(len(o) >= 2 for o in opts), f"golden q{q['n']}: kisa secenek"
        assert len(set(opts)) == 4, f"golden q{q['n']}: tekrarli secenek"
        assert q["ans"] in ("A", "B", "C", "D"), f"golden q{q['n']}: cevap harfi"

        qid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"gf-golden-q{q['n']}@kiro2.com"))
        words = q["text"].split()
        params_common = {"id": qid}
        cur.execute(
            QB_INSERT,
            {
                **params_common,
                "hash": hashlib.sha256(qid.encode()).hexdigest()[:32],
                "topic": MVP_MAT_TOPIC_ID,
                "anchor": q["anchor"],
            },
        )
        created += cur.rowcount
        cur.execute(
            QC_INSERT,
            {
                **params_common,
                "text": q["text"],
                "a": q["a"],
                "b": q["b_opt"],
                "c": q["c"],
                "d": q["d"],
                "ans": q["ans"],
                "exp": q["exp"],
            },
        )
        cur.execute(
            QM_INSERT,
            {
                **params_common,
                # mv_safe_for_beta kosulu: pipeline_metadata.student_coherent
                "pm": json.dumps({"student_coherent": True, "source": "seed_mvp_data"}),
                "wc": len(words),
                "uwc": len({w.lower() for w in words}),
                "awl": round(sum(len(w) for w in words) / max(len(words), 1), 2),
            },
        )
        cur.execute(
            QS_INSERT,
            {
                **params_common,
                "diff": q["diff"],
                "diff_l": q["diff"].lower(),
                "b": q["b"],
            },
        )

    # Konu sayaci durust kalsin (engine'ler cogunlukla question_* tablolarindan
    # sayar ama topic_hierarchy.total_questions=0 yaniltici olur).
    cur.execute(
        "UPDATE topic_hierarchy SET total_questions = ("
        "  SELECT COUNT(*) FROM question_bank WHERE primary_topic_id = %s"
        ") WHERE id = %s",
        (MVP_MAT_TOPIC_ID, MVP_MAT_TOPIC_ID),
    )
    return created


def main():
    print(f"Connecting to PostgreSQL: {db_host}:{db_port}/{dbname}")
    try:
        conn = psycopg.connect(
            host=db_host,
            port=int(db_port),
            dbname=dbname,
            user=db_user,
            password=db_pass,
        )
    except psycopg.OperationalError as e:
        print(f"ERROR: DB connection failed: {e}")
        print("Check DATABASE_URL in .env.mvp")
        sys.exit(1)
    conn.autocommit = False
    cur = conn.cursor()

    # org_legacy_default: users.organization_id DB-default'u buna FK baglar; bos CI
    # semasi tabloyu kurar ama satiri degil — kullanicilardan ONCE bu org olmali.
    cur.execute(ORG_INSERT_SQL)
    if cur.rowcount:
        print("  CREATE: organizations org_legacy_default")

    created = 0
    skipped = 0

    for user in MVP_USERS:
        # Check if already exists
        cur.execute("SELECT id FROM users WHERE email = %s", (user["email"],))
        if cur.fetchone():
            print(f"  SKIP: {user['email']} (already exists)")
            skipped += 1
            continue

        # Hash password with bcrypt
        password_hash = pwd_context.hash(user["password"])

        cur.execute(
            INSERT_SQL,
            {
                "id": user["id"],
                "email": user["email"],
                "username": user["username"],
                "password_hash": password_hash,
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "role": user["role"],
            },
        )

        # Create student profile for STUDENT users
        if user["role"] == "STUDENT":
            cur.execute(PROFILE_INSERT_SQL, {"id": user["id"]})
            print(f"  CREATE: {user['email']} ({user['role']}) + student_profile")
        else:
            print(f"  CREATE: {user['email']} ({user['role']})")
        created += 1

    # Topic row for admin question create (K4 / GF6w) on empty topic_hierarchy DBs
    cur.execute(ENSURE_TOPIC_SQL, (MVP_MAT_TOPIC_ID,))
    if cur.rowcount:
        print(f"  CREATE: topic_hierarchy MVP.MAT.GOLDEN ({MVP_MAT_TOPIC_ID})")

    q_created = seed_golden_questions(cur)
    if q_created:
        print(f"  CREATE: {q_created} golden MATEMATIK TYT sorusu (question_bank)")

    # Sorular eklendikten sonra kalite kapisinin matview'unu tazele; yoksa
    # safe_for_beta_sql() kapili uclar yeni sorulari goremez (0001_baseline
    # ilk REFRESH'i bos DB'de yapar, iceriksiz kalir).
    cur.execute("REFRESH MATERIALIZED VIEW mv_safe_for_beta")

    conn.commit()
    cur.close()
    conn.close()

    print(f"\nDone: {created} created, {skipped} skipped")
    print("\nMVP Login Credentials:")
    print("-" * 50)
    for user in MVP_USERS:
        print(f"  {user['role']:8s} | {user['email']} | ****")


if __name__ == "__main__":
    main()
