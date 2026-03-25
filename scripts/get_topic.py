import psycopg2
conn = psycopg2.connect(host='localhost',port=5434,dbname='kiro2',user='postgres',password='changeme_strong_password_here')
cur = conn.cursor()
cur.execute('SELECT id FROM topic_hierarchy LIMIT 1')
row = cur.fetchone()
print('topic_id:', row[0] if row else 'YOK')
conn.close()
