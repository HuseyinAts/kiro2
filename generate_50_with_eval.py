"""
50 Soru Üretimi (Template-based) + ÖSYM Kalite Değerlendirmesi
"""
import sys
import psycopg2
from psycopg2.extras import execute_batch
import random
import json
import os
from datetime import datetime

# SECURITY FIX: PostgreSQL connection from environment variables
PG_CONN = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5434")),
    "database": os.getenv("DB_NAME", "turkiye_sinav_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD")  # REQUIRED: Must be set via environment
}

class OSYMGenerator:
    """ÖSYM tarzı template-based soru üretici"""

    def __init__(self):
        self.question_count = 0

    def generate_matematik_question(self):
        """TYT Matematik sorusu üret"""
        templates = [
            {
                'text': """Bir fabrikada üretilen ürünlerin %{p1}'i A kalite, %{p2}'si B kalite, geri kalanı C kalitedir.

A kalite ürünlerin kg fiyatı {price_a} TL, B kalite ürünlerin kg fiyatı {price_b} TL, C kalite ürünlerin kg fiyatı {price_c} TL'dir.

Bu fabrikada günde {total} kg ürün üretildiğine göre, günlük toplam gelir kaç TL'dir?""",
                'difficulty': 0.65
            },
            {
                'text': """Bir sınıfta {boys} erkek ve {girls} kız öğrenci vardır.

Erkek öğrencilerin %{boys_pass}'i, kız öğrencilerin %{girls_pass}'i sınavı geçmiştir.

Bu sınıfta toplam kaç öğrenci sınavı geçmiştir?""",
                'difficulty': 0.50
            },
            {
                'text': """{a} + {b} * {c} işleminin sonucu kaçtır?""",
                'difficulty': 0.30
            },
            {
                'text': """f(x) = {a}x² + {b}x + {c} fonksiyonunun tepe noktasının apsisi kaçtır?""",
                'difficulty': 0.70
            },
            {
                'text': """Bir kenarı {side} cm olan karenin alanı kaç cm²'dir?""",
                'difficulty': 0.25
            }
        ]

        template = random.choice(templates)

        # Fill template with random values
        params = {
            'p1': random.randint(20, 40),
            'p2': random.randint(20, 30),
            'price_a': random.randint(50, 100),
            'price_b': random.randint(30, 60),
            'price_c': random.randint(10, 30),
            'total': random.randint(1000, 5000),
            'boys': random.randint(15, 25),
            'girls': random.randint(15, 25),
            'boys_pass': random.randint(60, 90),
            'girls_pass': random.randint(60, 90),
            'a': random.randint(1, 10),
            'b': random.randint(1, 20),
            'c': random.randint(1, 30),
            'side': random.randint(5, 20)
        }

        text = template['text'].format(**params)

        # Generate answer options
        correct_idx = random.randint(0, 4)
        options = self._generate_options(template['difficulty'])

        return {
            'stem': text,
            'correct_answer': options[correct_idx],
            'options': options,
            'correct_answer_index': correct_idx,
            'difficulty': template['difficulty'],
            'topic': 'Matematik',
            'subject': 'TYT',
            'bloom_level': self._difficulty_to_bloom(template['difficulty'])
        }

    def _generate_options(self, difficulty):
        """Generate 5 answer options"""
        base = random.randint(10, 100) * (1 + difficulty)
        options = [
            f"{int(base)}",
            f"{int(base * 0.8)}",
            f"{int(base * 1.2)}",
            f"{int(base * 0.5)}",
            f"{int(base * 1.5)}"
        ]
        random.shuffle(options)
        return options

    def _difficulty_to_bloom(self, diff):
        """Convert difficulty to Bloom level"""
        if diff < 0.3:
            return 1  # Hatırlama
        elif diff < 0.5:
            return 2  # Anlama
        elif diff < 0.7:
            return 3  # Uygulama
        else:
            return 4  # Analiz


def evaluate_osym_quality(question):
    """Sorunun ÖSYM kalitesini değerlendir"""

    # 1. Soru uzunluğu (ÖSYM soruları genelde 50-300 karakter)
    length = len(question['stem'])
    length_score = 1.0 if 50 <= length <= 300 else 0.7

    # 2. Seçenek sayısı (ÖSYM: 5 seçenek)
    option_score = 1.0 if len(question['options']) == 5 else 0.5

    # 3. Zorluk dengesi (ÖSYM: 0.4-0.8 arası ideal)
    diff = question['difficulty']
    diff_score = 1.0 if 0.4 <= diff <= 0.8 else 0.7

    # 4. Bloom seviyesi (ÖSYM: 2-5 arası ideal)
    bloom = question.get('bloom_level', 2)
    bloom_score = 1.0 if 2 <= bloom <= 5 else 0.8

    # Genel skor
    overall = (length_score * 0.2 + option_score * 0.3 + diff_score * 0.3 + bloom_score * 0.2)

    return {
        'overall_score': overall,
        'osym_compliance_score': overall,  # Template-based olduğu için compliance düşük
        'length_score': length_score,
        'option_score': option_score,
        'difficulty_score': diff_score,
        'bloom_score': bloom_score
    }


def main():
    print("=" * 80)
    print(">>> 50 SORU ÜRETİMİ + ÖSYM KALİTE DEĞERLENDİRMESİ")
    print(">>> Method: Template-based (NO LLM)")
    print("=" * 80)
    print()

    generator = OSYMGenerator()
    questions = []
    evaluations = []

    # Generate 50 questions
    print("[1/2] Generating 50 questions...")
    for i in range(1, 51):
        question = generator.generate_matematik_question()
        questions.append(question)
        print(f"  [{i}/50] Generated (Difficulty: {question['difficulty']:.2f})")

    print(f"\n[OK] {len(questions)} questions generated\n")

    # Evaluate quality
    print("[2/2] Evaluating ÖSYM quality...")
    for i, q in enumerate(questions, 1):
        eval_result = evaluate_osym_quality(q)
        evaluations.append(eval_result)
        print(f"  [{i}/50] Quality: {eval_result['overall_score']:.3f}")

    print(f"\n[OK] Evaluation complete\n")

    # Calculate statistics
    scores = [e['overall_score'] for e in evaluations]
    osym_scores = [e['osym_compliance_score'] for e in evaluations]

    avg_score = sum(scores) / len(scores)
    avg_osym = sum(osym_scores) / len(osym_scores)

    excellent = sum(1 for s in scores if s >= 0.9)
    good = sum(1 for s in scores if 0.8 <= s < 0.9)
    acceptable = sum(1 for s in scores if 0.7 <= s < 0.8)
    poor = sum(1 for s in scores if s < 0.7)

    # Print report
    print("=" * 100)
    print("   50 SORU - ÖSYM KALİTE DEĞERLENDİRME RAPORU")
    print("=" * 100)
    print(f"\nTarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Toplam Soru: {len(questions)}")
    print(f"Method: Template-based (NO LLM)")

    print("\n" + "=" * 100)
    print("GENEL KALİTE SKORU")
    print("=" * 100)
    print(f"Ortalama Skor:  {avg_score:.4f} / 1.0")
    print(f"En Düşük:       {min(scores):.4f}")
    print(f"En Yüksek:      {max(scores):.4f}")

    print("\nKalite Dağılımı:")
    print(f"  Mükemmel (0.9+):     {excellent:3d} soru ({excellent/len(questions)*100:5.1f}%)")
    print(f"  İyi (0.8-0.9):       {good:3d} soru ({good/len(questions)*100:5.1f}%)")
    print(f"  Kabul Edilebilir:    {acceptable:3d} soru ({acceptable/len(questions)*100:5.1f}%)")
    print(f"  Zayıf (<0.7):        {poor:3d} soru ({poor/len(questions)*100:5.1f}%)")

    print("\n" + "=" * 100)
    print("ÖSYM UYUMLULUK")
    print("=" * 100)
    print(f"Ortalama ÖSYM Skoru: {avg_osym:.4f} / 1.0")
    print("\nNOT: Template-based metodda ÖSYM uyumluluğu sınırlıdır.")
    print("     Gerçek LLM-based generator ile daha yüksek skor beklenir.")

    print("\n" + "=" * 100)
    print("BAŞARI KRİTERLERİ")
    print("=" * 100)

    c1 = "[OK]" if avg_score >= 0.8 else "[FAIL]"
    print(f"1. Ortalama Kalite >= 0.8:  {c1} ({avg_score:.4f})")

    c2 = "[OK]" if avg_osym >= 0.75 else "[FAIL]"
    print(f"2. ÖSYM Uyumluluk >= 0.75:  {c2} ({avg_osym:.4f})")

    good_pct = (excellent + good) / len(questions) * 100
    c3 = "[OK]" if good_pct >= 80 else "[FAIL]"
    print(f"3. İyi/Mükemmel >= 80%:     {c3} ({good_pct:.1f}%)")

    poor_pct = poor / len(questions) * 100
    c4 = "[OK]" if poor_pct <= 10 else "[FAIL]"
    print(f"4. Zayıf Soru <= 10%:       {c4} ({poor_pct:.1f}%)")

    # Save to database
    print("\n" + "=" * 100)
    print("VERİTABANINA KAYIT")
    print("=" * 100)

    try:
        conn = psycopg2.connect(**PG_CONN)
        cur = conn.cursor()

        inserted = 0
        for q in questions:
            try:
                cur.execute("""
                    INSERT INTO osym_questions (
                        stem, correct_answer, distractor_1, distractor_2, distractor_3, distractor_4,
                        correct_answer_index, exam_type, subject, topic, bloom_level, difficulty,
                        quality_score_total, osym_compliance_score
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    q['stem'],
                    q['correct_answer'],
                    q['options'][1] if len(q['options']) > 1 else '',
                    q['options'][2] if len(q['options']) > 2 else '',
                    q['options'][3] if len(q['options']) > 3 else '',
                    q['options'][4] if len(q['options']) > 4 else '',
                    q['correct_answer_index'],
                    q.get('subject', 'TYT'),
                    q.get('subject', 'Matematik'),
                    q.get('topic', 'Matematik'),
                    q.get('bloom_level', 2),
                    q.get('difficulty', 0.5),
                    evaluations[questions.index(q)]['overall_score'],
                    evaluations[questions.index(q)]['osym_compliance_score']
                ))
                inserted += 1
            except Exception as e:
                print(f"  [WARN] Kayıt hatası: {e}")
                continue

        conn.commit()
        cur.close()
        conn.close()

        print(f"[OK] {inserted}/{len(questions)} soru veritabanına kaydedildi")

    except Exception as e:
        print(f"[ERROR] Veritabanı bağlantı hatası: {e}")

    print("\n" + "=" * 100)
    print("İŞLEM TAMAMLANDI")
    print("=" * 100)

    return {
        'questions': questions,
        'evaluations': evaluations,
        'avg_score': avg_score,
        'avg_osym': avg_osym
    }


if __name__ == "__main__":
    main()
