#!/usr/bin/env python3
"""Questions tablosu şemasını kontrol et"""

import psycopg2
from psycopg2.extras import RealDictCursor

def check_schema():
    conn = psycopg2.connect(
        host="localhost",
        port=5434,
        database="kiro2",
        user="postgres",
        cursor_factory=RealDictCursor
    )
    
    with conn.cursor() as cur:
        # Tablo sütunlarını kontrol et
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'questions'
            ORDER BY ordinal_position
        """)
        
        print("Questions tablosu sütunları:")
        print("-" * 50)
        for col in cur.fetchall():
            print(f"{col['column_name']:30} {col['data_type']:20} {col['is_nullable']}")
        
        # Toplam soru sayısı
        cur.execute("SELECT COUNT(*) as total FROM questions")
        total = cur.fetchone()
        print(f"\nToplam soru sayısı: {total['total']}")
        
        # İlk 3 soruyu kontrol et
        cur.execute("SELECT * FROM questions LIMIT 3")
        rows = cur.fetchall()
        
        if rows:
            print("\nÖrnek soru alanları:")
            print("-" * 50)
            for key in rows[0].keys():
                print(f"- {key}")
    
    conn.close()

if __name__ == "__main__":
    check_schema()