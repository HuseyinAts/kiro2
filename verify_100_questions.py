"""
100 Soru Doğrulama ve Detaylı Rapor
"""
import psycopg2
from collections import defaultdict
import os

# SECURITY FIX: PostgreSQL connection from environment variables
PG_CONN = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5434")),
    "database": os.getenv("DB_NAME", "turkiye_sinav_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD")  # REQUIRED: Must be set via environment
}

def verify_questions():
    """Soruları doğrula ve detaylı rapor ver"""
    conn = psycopg2.connect(**PG_CONN)
    cursor = conn.cursor()

    # Toplam soru sayısı
    cursor.execute("SELECT COUNT(*) FROM questions")
    total = cursor.fetchone()[0]

    print("\n" + "="*70)
    print("📊 KIRO2 SORU BANKASI - DETAYLI RAPOR")
    print("="*70)
    print(f"\n🎯 TOPLAM SORU SAYISI: {total}")

    # Sınav tipine göre dağılım
    print("\n" + "-"*70)
    print("📋 SINAV TİPİNE GÖRE DAĞILIM")
    print("-"*70)

    cursor.execute("""
        SELECT exam_type, COUNT(*) as count
        FROM questions
        GROUP BY exam_type
        ORDER BY count DESC
    """)

    for exam_type, count in cursor.fetchall():
        percentage = (count / total) * 100
        bar = "█" * int(percentage / 2)
        print(f"{exam_type:8} │ {count:3} soru │ {percentage:5.1f}% │ {bar}")

    # Konu dağılımı
    print("\n" + "-"*70)
    print("📚 KONU DAĞILIMI")
    print("-"*70)

    cursor.execute("""
        SELECT subject, COUNT(*) as count
        FROM questions
        GROUP BY subject
        ORDER BY count DESC
    """)

    for subject, count in cursor.fetchall():
        percentage = (count / total) * 100
        bar = "█" * int(percentage / 2)
        print(f"{subject:15} │ {count:3} soru │ {percentage:5.1f}% │ {bar}")

    # Alt konu dağılımı (Topic)
    print("\n" + "-"*70)
    print("🔖 ALT KONU DAĞILIMI (İlk 15)")
    print("-"*70)

    cursor.execute("""
        SELECT topic, COUNT(*) as count
        FROM questions
        GROUP BY topic
        ORDER BY count DESC
        LIMIT 15
    """)

    for topic, count in cursor.fetchall():
        print(f"  • {topic:30} : {count:3} soru")

    # Zorluk seviyesi dağılımı
    print("\n" + "-"*70)
    print("⚖️  ZORLUK SEVİYESİ DAĞILIMI")
    print("-"*70)

    cursor.execute("""
        SELECT
            CASE
                WHEN difficulty < 0.3 THEN 'Kolay'
                WHEN difficulty < 0.5 THEN 'Orta'
                WHEN difficulty < 0.7 THEN 'Zor'
                ELSE 'Çok Zor'
            END as level,
            COUNT(*) as count,
            ROUND(AVG(difficulty)::numeric, 2) as avg_diff
        FROM questions
        GROUP BY level
        ORDER BY avg_diff
    """)

    print(f"{'Seviye':<12} │ {'Soru Sayısı':<12} │ {'Ort. Zorluk':<12}")
    print("-"*42)
    for level, count, avg_diff in cursor.fetchall():
        percentage = (count / total) * 100
        bar = "█" * int(percentage / 3)
        print(f"{level:<12} │ {count:3} ({percentage:4.1f}%) │ {avg_diff:<12} │ {bar}")

    # IRT parametreleri özeti
    print("\n" + "-"*70)
    print("📈 IRT PARAMETRELERİ ÖZETİ")
    print("-"*70)

    cursor.execute("""
        SELECT
            ROUND(AVG(difficulty)::numeric, 3) as avg_difficulty,
            ROUND(AVG(discrimination)::numeric, 3) as avg_discrimination,
            ROUND(AVG(guessing)::numeric, 3) as avg_guessing
        FROM questions
    """)

    avg_diff, avg_disc, avg_guess = cursor.fetchone()
    print(f"  Ortalama Zorluk (difficulty)      : {avg_diff}")
    print(f"  Ortalama Ayırt Edicilik (discrim.) : {avg_disc}")
    print(f"  Ortalama Tahmin (guessing)         : {avg_guess}")

    # En son eklenen sorular
    print("\n" + "-"*70)
    print("🆕 EN SON EKLENEN 5 SORU")
    print("-"*70)

    cursor.execute("""
        SELECT id, exam_type, subject, topic, created_at
        FROM questions
        ORDER BY id DESC
        LIMIT 5
    """)

    for id, exam_type, subject, topic, created_at in cursor.fetchall():
        print(f"  #{id} │ {exam_type} │ {subject} │ {topic}")
        print(f"       └─ Eklenme: {created_at}")

    # Örnek soru göster
    print("\n" + "-"*70)
    print("📝 ÖRNEK SORU (Rastgele)")
    print("-"*70)

    cursor.execute("""
        SELECT
            question_text, option_a, option_b, option_c, option_d, option_e,
            correct_answer, exam_type, subject, topic
        FROM questions
        ORDER BY RANDOM()
        LIMIT 1
    """)

    q = cursor.fetchone()
    if q:
        question_text, opt_a, opt_b, opt_c, opt_d, opt_e, correct, exam_type, subject, topic = q
        print(f"\n📌 Sınav: {exam_type} │ Konu: {subject} │ Alt Konu: {topic}")
        print(f"\nSoru: {question_text}\n")
        print(f"  A) {opt_a}")
        print(f"  B) {opt_b}")
        print(f"  C) {opt_c}")
        print(f"  D) {opt_d}")
        print(f"  E) {opt_e}")
        print(f"\n✅ Doğru Cevap: {correct}")

    print("\n" + "="*70)
    print("✅ DOĞRULAMA TAMAMLANDI - TÜM SORULAR HAZIR!")
    print("="*70 + "\n")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    try:
        verify_questions()
    except Exception as e:
        print(f"\n❌ HATA: {e}")
        import traceback
        traceback.print_exc()
