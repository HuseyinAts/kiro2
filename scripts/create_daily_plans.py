import psycopg2, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = psycopg2.connect(host='localhost',port=5434,dbname='kiro2',
                        user='postgres',password='changeme_strong_password_here')
cur = conn.cursor()

# 1. daily_plans tablosu
cur.execute("""
CREATE TABLE IF NOT EXISTS daily_plans (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id         UUID NOT NULL,
    plan_date       DATE NOT NULL,
    exam_date       DATE,
    days_remaining  INT,
    total_minutes   INT,
    plan_json       JSONB DEFAULT '{}'::JSONB,
    weak_subject    TEXT,
    strong_subject  TEXT,
    motivational_note TEXT,
    generated_at    TIMESTAMPTZ DEFAULT NOW(),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT daily_plans_user_date_unique UNIQUE (user_id, plan_date),
    CONSTRAINT daily_plans_user_fk FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE
);
""")

# 2. Index
cur.execute("CREATE INDEX IF NOT EXISTS idx_daily_plans_user_date ON daily_plans(user_id, plan_date DESC);")
cur.execute("CREATE INDEX IF NOT EXISTS idx_daily_plans_date ON daily_plans(plan_date);")
conn.commit()
print("daily_plans tablosu OK")

# 3. yks_exam_goals tablosu kontrol (task bunu kullanıyor)
cur.execute("SELECT to_regclass('public.yks_exam_goals')")
r = cur.fetchone()[0]
print("yks_exam_goals:", r if r else "YOK - olusturuluyor...")
if not r:
    cur.execute("""
    CREATE TABLE IF NOT EXISTS yks_exam_goals (
        id               UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        user_id          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        exam_type        TEXT NOT NULL DEFAULT 'TYT',
        exam_date        DATE NOT NULL,
        daily_minutes    INT DEFAULT 120,
        target_university TEXT,
        target_department TEXT,
        created_at       TIMESTAMPTZ DEFAULT NOW(),
        CONSTRAINT yks_exam_goals_user_unique UNIQUE (user_id)
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_yks_goals_user ON yks_exam_goals(user_id);")
    conn.commit()
    print("yks_exam_goals olusturuldu")

# 4. Mevcut kullanicilara varsayilan hedef ekle (plan olusturabilmek icin)
cur.execute("SELECT COUNT(*) FROM yks_exam_goals")
print("yks_exam_goals kayit sayisi:", cur.fetchone()[0])

cur.execute("SELECT COUNT(*) FROM student_abilities")
print("student_abilities kayit sayisi:", cur.fetchone()[0])

# 5. Dogrulama
cur.execute("SELECT to_regclass('public.daily_plans'), to_regclass('public.yks_exam_goals')")
print("Tablolar:", cur.fetchone())
