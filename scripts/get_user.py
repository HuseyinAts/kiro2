import psycopg2
conn=psycopg2.connect(host='localhost',port=5434,dbname='kiro2',user='postgres',password='changeme_strong_password_here')
cur=conn.cursor()
cur.execute("SELECT id FROM users LIMIT 1")
print(cur.fetchone()[0])
conn.close()
