import psycopg2, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = psycopg2.connect(host='localhost',port=5434,dbname='kiro2',
                        user='postgres',password='changeme_strong_password_here')
cur = conn.cursor()

# 1. subjects tablosunu olustur
cur.execute("""
CREATE TABLE IF NOT EXISTS subjects (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    display_name TEXT,
    exam_type   TEXT DEFAULT 'TYT',
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
""")
conn.commit()
print("subjects tablosu OK")

# 2. Bilinen dersleri ekle
subjects_data = [
    ('MATEMATIK',  'Matematik',       'TYT_AYT'),
    ('GEOMETRI',   'Geometri',        'TYT_AYT'),
    ('TURKCE',     'Türkçe',          'TYT'),
    ('EDEBIYAT',   'Türk Dili Edeb.', 'AYT'),
    ('FIZIK',      'Fizik',           'AYT'),
    ('KIMYA',      'Kimya',           'AYT'),
    ('BIYOLOJI',   'Biyoloji',        'AYT'),
    ('TARIH',      'Tarih',           'AYT'),
    ('COGRAFYA',   'Coğrafya',        'AYT'),
    ('SOSYAL',     'Sosyal Bilimler', 'TYT'),
    ('FEN',        'Fen Bilimleri',   'TYT'),
    ('GENEL',      'Genel Kültür',    'TYT'),
]
for name, display, exam_t in subjects_data:
    cur.execute("""
        INSERT INTO subjects (name, display_name, exam_type)
        VALUES (%s, %s, %s)
        ON CONFLICT (name) DO UPDATE SET display_name=EXCLUDED.display_name
    """, (name, display, exam_t))
conn.commit()
cur.execute("SELECT COUNT(*) FROM subjects"); print("subjects kayit:", cur.fetchone()[0])

# 3. student_abilities'i doldur — kiro2_learning_events + question_bank JOIN
cur.execute("""
INSERT INTO student_abilities (student_id, subject_id, theta, theta_se, updated_at)
SELECT
    le.user_id::text,
    s.id,
    ROUND(COALESCE(AVG(le.theta_after) FILTER (WHERE le.theta_after IS NOT NULL
          AND le.theta_after BETWEEN -4 AND 4), 0.0)::numeric, 3),
    0.5,
    MAX(le.occurred_at)
FROM kiro2_learning_events le
JOIN question_bank qb ON qb.id::text = le.question_id::text
JOIN subjects s ON s.name = qb.subject_area
WHERE le.event_type IN ('exam_answer', 'cat_answer')
  AND le.is_correct IS NOT NULL
GROUP BY le.user_id, s.id
ON CONFLICT (student_id, subject_id) DO UPDATE SET
    theta      = EXCLUDED.theta,
    theta_se   = EXCLUDED.theta_se,
    updated_at = EXCLUDED.updated_at
""")
conn.commit()
print("learning_events -> student_abilities:", cur.rowcount, "satir guncellendi")

# 4. yks_exam_goals sahibi kullanicilara eksik ders satirlari ekle (varsayilan theta=0)
cur.execute("""
INSERT INTO student_abilities (student_id, subject_id, theta, theta_se, updated_at)
SELECT g.user_id::text, s.id, 0.0, 0.5, NOW()
FROM yks_exam_goals g
CROSS JOIN subjects s
WHERE NOT EXISTS (
    SELECT 1 FROM student_abilities sa
    WHERE sa.student_id = g.user_id::text AND sa.subject_id = s.id
)
ON CONFLICT DO NOTHING
""")
conn.commit()
print("Eksik ders satirlari eklendi:", cur.rowcount)

# 5. Son durum
cur.execute("SELECT COUNT(*), COUNT(DISTINCT student_id) FROM student_abilities")
total, students = cur.fetchone()
print(f"student_abilities: {total} satir, {students} benzersiz ogrenci")

cur.execute("""
SELECT s.name, COUNT(sa.student_id), ROUND(AVG(sa.theta)::numeric,3)
FROM student_abilities sa JOIN subjects s ON s.id = sa.subject_id
GROUP BY s.name ORDER BY s.name
""")
print("\nDers bazinda dagilim:")
for r in cur.fetchall():
    print(f"  {r[0]:12} {r[1]:3} ogrenci  avg_theta={r[2]}")

# 6. Trigger: yeni learning_event gelince student_abilities de guncelle
cur.execute("""
CREATE OR REPLACE FUNCTION fn_update_student_ability()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE v_subject_id INT;
BEGIN
    IF NEW.event_type NOT IN ('exam_answer','cat_answer') THEN RETURN NEW; END IF;
    IF NEW.theta_after IS NULL THEN RETURN NEW; END IF;
    SELECT s.id INTO v_subject_id FROM question_bank qb
    JOIN subjects s ON s.name = qb.subject_area
    WHERE qb.id::text = NEW.question_id::text LIMIT 1;
    IF v_subject_id IS NULL THEN RETURN NEW; END IF;
    INSERT INTO student_abilities (student_id, subject_id, theta, theta_se, updated_at)
    VALUES (NEW.user_id::text, v_subject_id, ROUND(NEW.theta_after::numeric,3), 0.4, NOW())
    ON CONFLICT (student_id, subject_id) DO UPDATE SET
        theta      = ROUND(EXCLUDED.theta::numeric,3),
        theta_se   = GREATEST(student_abilities.theta_se - 0.02, 0.3),
        updated_at = NOW();
    RETURN NEW;
EXCEPTION WHEN OTHERS THEN RETURN NEW;
END; $$;
DROP TRIGGER IF EXISTS trg_update_student_ability ON kiro2_learning_events;
CREATE TRIGGER trg_update_student_ability
AFTER INSERT ON kiro2_learning_events
FOR EACH ROW EXECUTE FUNCTION fn_update_student_ability();
""")
conn.commit()
print("\nTrigger trg_update_student_ability OK")

conn.close()
