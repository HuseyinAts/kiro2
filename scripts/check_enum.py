import psycopg2
conn = psycopg2.connect(host='localhost',port=5434,dbname='kiro2',user='postgres',password='changeme_strong_password_here')
cur = conn.cursor()
cur.execute("SELECT enumlabel FROM pg_enum JOIN pg_type ON pg_enum.enumtypid=pg_type.oid WHERE typname='difficulty_enum' OR typname LIKE '%difficulty%'")
rows = cur.fetchall()
print('Enum values:', rows)
# Var olan bir sorudan da alalim
cur.execute("SELECT difficulty_level FROM question_bank WHERE difficulty_level IS NOT NULL LIMIT 3")
rows2 = cur.fetchall()
print('Ornek deger:', rows2)
conn.close()
