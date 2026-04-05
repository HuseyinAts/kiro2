"""
Update Bloom levels for questions using AI analysis
"""
import sys
import io
import sqlite3
import re

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Bloom Taxonomy Analysis Rules
def analyze_bloom_level(stem):
    """Analyze question stem to determine appropriate Bloom level"""

    stem_lower = stem.lower()

    # Bloom 6 (Değerlendirme) - Karar verme, yargılama
    if any(word in stem_lower for word in ['değerlendiriniz', 'eleştiriniz', 'savununuz', 'hangi en iyisidir', 'öncelik']):
        return 6, 'değerlendirme'

    # Bloom 5 (Sentez) - Yeni şeyler yaratma, plan yapma
    if any(word in stem_lower for word in ['tasarlayınız', 'oluşturunuz', 'geliştiriniz', 'öneriniz', 'planlayınız']):
        return 5, 'sentez'

    # Bloom 4 (Analiz) - Ayırma, ilişkilendirme, karşılaştırma
    if any(word in stem_lower for word in [
        'analiz', 'karşılaştır', 'ilişki', 'neden', 'sebep',
        'fark', 'benzer', 'ayırt', 'incele', 'çıkarımda bulun',
        'kaç farklı', 'buna göre', 'olduğuna göre'
    ]):
        return 4, 'analiz'

    # Bloom 3 (Uygulama) - Formül, hesaplama, problem çözme
    if any(word in stem_lower for word in [
        'hesaplayınız', 'bulunuz', 'çözünüz', 'kaçtır',
        'kaç cm', 'kaç m/s', 'kaç j', 'kaç atm', 'kaç gram',
        'uygulay', 'göster', 'kullan', '=', '+', '-', 'x', '÷'
    ]) or re.search(r'\d+.*\d+', stem):  # Sayılar içeren hesaplama soruları
        return 3, 'uygulama'

    # Bloom 2 (Kavrama) - Açıklama, tanımlama
    if any(word in stem_lower for word in [
        'açıklayınız', 'tanımlayınız', 'özetleyiniz', 'anlamı nedir',
        'nedir', 'nasıldır', 'kimdir', 'ne demektir'
    ]):
        return 2, 'kavrama'

    # Bloom 1 (Hatırlama) - Basit hatırlama
    if any(word in stem_lower for word in [
        'aşağıdakilerden hangisi', 'hangi seçenek', 'hangi',
        'listele', 'say', 'belirt', 'tanımla'
    ]):
        # Ama eğer "hangi" ile birlikte hesaplama varsa, Bloom 3
        if any(word in stem_lower for word in ['kaçtır', 'hesap', 'bul']):
            return 3, 'uygulama'
        # "hangisi yanlıştır" analiz gerektirir
        if 'yanlış' in stem_lower or 'doğru değil' in stem_lower:
            return 4, 'analiz'
        return 2, 'kavrama'

    # Default: Eğer hiçbiri yoksa, içeriğe göre
    if len(stem) > 200:  # Uzun sorular genelde analiz
        return 4, 'analiz'
    return 3, 'uygulama'  # ÖSYM için tipik seviye


print("=" * 100)
print(">>> BLOOM SEVİYELERİNİ GÜNCELLEME")
print("=" * 100)
print()

conn = sqlite3.connect('backend/kiro2.db')
cursor = conn.cursor()

# Get all questions
cursor.execute('SELECT id, question_id, stem, bloom_level FROM osym_questions')
questions = cursor.fetchall()

print(f"Toplam {len(questions)} soru analiz ediliyor...")
print()

updated_count = 0
bloom_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}

for q_id, question_id, stem, old_bloom in questions:
    # Analyze bloom level
    new_bloom, bloom_category = analyze_bloom_level(stem)

    # Update if different
    if new_bloom != old_bloom:
        cursor.execute('''
            UPDATE osym_questions
            SET bloom_level = ?,
                bloom_category = ?,
                bloom_confidence = 0.85
            WHERE id = ?
        ''', (new_bloom, bloom_category, q_id))

        conn.commit()
        updated_count += 1

        # Show first 80 chars of stem
        stem_preview = stem[:80] + '...' if len(stem) > 80 else stem
        print(f"[UPDATE] {question_id}")
        print(f"   {stem_preview}")
        print(f"   Bloom: {old_bloom} → {new_bloom} ({bloom_category})")
        print()

    bloom_distribution[new_bloom] += 1

conn.close()

print("=" * 100)
print(">>> ÖZET")
print("=" * 100)
print(f"Güncellenen soru: {updated_count}/{len(questions)}")
print()

print("Bloom Seviyesi Dağılımı:")
print("-" * 100)
bloom_names = {
    1: "Hatırlama",
    2: "Kavrama",
    3: "Uygulama",
    4: "Analiz",
    5: "Sentez",
    6: "Değerlendirme"
}

for level in range(1, 7):
    count = bloom_distribution[level]
    pct = count / len(questions) * 100 if questions else 0
    bar = '█' * int(pct / 5)
    print(f"Seviye {level} ({bloom_names[level]:15s}): {count:2d} soru ({pct:5.1f}%) {bar}")

print()
print("[OK] Güncelleme tamamlandı!")
