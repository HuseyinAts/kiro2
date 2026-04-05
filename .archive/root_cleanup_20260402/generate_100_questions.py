"""
100 ÖSYM Sorusu Oluşturma Script
Agent desteği ile otomatik soru üretimi
"""
import psycopg2
from psycopg2.extras import execute_batch
import random
import os
from datetime import datetime

# SECURITY FIX: PostgreSQL connection from environment variables
# Set environment variables: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
PG_CONN = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5434")),
    "database": os.getenv("DB_NAME", "turkiye_sinav_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD")  # REQUIRED: Must be set via environment
}

# Soru şablonları (ÖSYM tarzı)
QUESTION_TEMPLATES = {
    'TYT': {
        'Matematik': [
            {
                'text': 'Bir sayının 3 katının 5 fazlası {result} ise, bu sayı kaçtır?',
                'topic': 'Denklemler',
                'difficulty': 0.3,
                'discrimination': 1.2,
                'guessing': 0.2
            },
            {
                'text': '{a} ve {b} sayılarının EBOB\'u kaçtır?',
                'topic': 'Sayı Teorisi',
                'difficulty': 0.2,
                'discrimination': 1.3,
                'guessing': 0.2
            },
            {
                'text': 'Bir kenarı {side} cm olan karenin alanı kaç cm² dir?',
                'topic': 'Geometri',
                'difficulty': 0.1,
                'discrimination': 1.1,
                'guessing': 0.25
            },
            {
                'text': '{num} sayısının yüzde {percent}\'i kaçtır?',
                'topic': 'Yüzdeler',
                'difficulty': 0.25,
                'discrimination': 1.2,
                'guessing': 0.2
            },
            {
                'text': 'f(x) = {a}x + {b} fonksiyonunda f({input}) kaçtır?',
                'topic': 'Fonksiyonlar',
                'difficulty': 0.35,
                'discrimination': 1.4,
                'guessing': 0.2
            }
        ],
        'Türkçe': [
            {
                'text': 'Aşağıdaki cümlelerin hangisinde yazım yanlışı vardır?',
                'topic': 'Yazım Kuralları',
                'difficulty': 0.4,
                'discrimination': 1.3,
                'guessing': 0.25
            },
            {
                'text': 'Aşağıdaki sözcüklerden hangisi birleşik fiildir?',
                'topic': 'Sözcük Türleri',
                'difficulty': 0.45,
                'discrimination': 1.2,
                'guessing': 0.25
            },
            {
                'text': 'Aşağıdaki cümlelerin hangisinde anlam kayması vardır?',
                'topic': 'Anlam Bilgisi',
                'difficulty': 0.5,
                'discrimination': 1.5,
                'guessing': 0.2
            }
        ],
        'Fen': [
            {
                'text': '{mass} kg kütleli bir cismin {gravity} m/s² yer çekimi ivmesindeki ağırlığı kaç N\'dir?',
                'topic': 'Kuvvet ve Hareket',
                'difficulty': 0.3,
                'discrimination': 1.3,
                'guessing': 0.2
            },
            {
                'text': 'Periyodik tabloda {element} elementinin atom numarası kaçtır?',
                'topic': 'Atom ve Periyodik Sistem',
                'difficulty': 0.35,
                'discrimination': 1.2,
                'guessing': 0.25
            }
        ],
        'Sosyal': [
            {
                'text': 'Osmanlı İmparatorluğu hangi yüzyılda kurulmuştur?',
                'topic': 'Osmanlı Tarihi',
                'difficulty': 0.25,
                'discrimination': 1.1,
                'guessing': 0.25
            },
            {
                'text': 'Aşağıdaki haritalardan hangisi tematik haritadır?',
                'topic': 'Coğrafya',
                'difficulty': 0.4,
                'discrimination': 1.3,
                'guessing': 0.25
            }
        ]
    },
    'AYT': {
        'Matematik': [
            {
                'text': 'lim(x→{point}) ({a}x² + {b}x + {c}) limitinin değeri kaçtır?',
                'topic': 'Limitler',
                'difficulty': 0.6,
                'discrimination': 1.6,
                'guessing': 0.15
            },
            {
                'text': 'y = {a}x² + {b}x + {c} parabolünün tepe noktası hangi noktadır?',
                'topic': 'İkinci Dereceden Fonksiyonlar',
                'difficulty': 0.55,
                'discrimination': 1.5,
                'guessing': 0.2
            },
            {
                'text': 'sin({angle})° + cos({angle})° toplamının değeri kaçtır?',
                'topic': 'Trigonometri',
                'difficulty': 0.65,
                'discrimination': 1.7,
                'guessing': 0.15
            }
        ],
        'Fizik': [
            {
                'text': '{voltage} V potansiyel farkı altında {charge} C yük taşınırsa yapılan iş kaç J\'dür?',
                'topic': 'Elektrik',
                'difficulty': 0.5,
                'discrimination': 1.5,
                'guessing': 0.2
            },
            {
                'text': 'Yarılanma ömrü {halflife} yıl olan bir radyoaktif maddenin {time} yılda kalan miktarı kaçtır?',
                'topic': 'Nükleer Fizik',
                'difficulty': 0.7,
                'discrimination': 1.8,
                'guessing': 0.15
            }
        ],
        'Kimya': [
            {
                'text': '{mol} mol {compound} bileşiğinin kütlesi kaç gramdır?',
                'topic': 'Mol Kavramı',
                'difficulty': 0.45,
                'discrimination': 1.4,
                'guessing': 0.2
            }
        ],
        'Biyoloji': [
            {
                'text': 'Fotosentezde hangi pigment ana rol oynar?',
                'topic': 'Fotosentez',
                'difficulty': 0.3,
                'discrimination': 1.2,
                'guessing': 0.25
            }
        ]
    },
    'YDT': {
        'İngilizce': [
            {
                'text': 'The book _____ I read yesterday was very interesting.',
                'topic': 'Relative Clauses',
                'difficulty': 0.4,
                'discrimination': 1.3,
                'guessing': 0.25
            },
            {
                'text': 'If I _____ rich, I would travel around the world.',
                'topic': 'Conditionals',
                'difficulty': 0.5,
                'discrimination': 1.4,
                'guessing': 0.25
            }
        ]
    }
}

def generate_random_value(template_text):
    """Template değişkenlerini rastgele sayılarla doldur"""
    replacements = {
        '{result}': str(random.randint(10, 100)),
        '{a}': str(random.randint(2, 9)),
        '{b}': str(random.randint(1, 9)),
        '{c}': str(random.randint(1, 9)),
        '{num}': str(random.randint(100, 1000)),
        '{percent}': str(random.randint(10, 50)),
        '{side}': str(random.randint(5, 20)),
        '{input}': str(random.randint(1, 5)),
        '{mass}': str(random.randint(5, 50)),
        '{gravity}': '10',
        '{element}': random.choice(['Hidrojen', 'Oksijen', 'Karbon']),
        '{point}': str(random.randint(1, 5)),
        '{angle}': str(random.choice([30, 45, 60, 90])),
        '{voltage}': str(random.randint(10, 100)),
        '{charge}': str(random.randint(1, 10)),
        '{halflife}': str(random.randint(10, 100)),
        '{time}': str(random.randint(20, 200)),
        '{mol}': str(random.randint(1, 5)),
        '{compound}': random.choice(['H2O', 'CO2', 'NaCl'])
    }

    text = template_text
    for key, value in replacements.items():
        text = text.replace(key, value)
    return text

def generate_options(correct_answer_value):
    """Doğru cevap etrafında 4 yanlış seçenek oluştur"""
    if isinstance(correct_answer_value, (int, float)):
        options = [correct_answer_value]
        base = correct_answer_value
        for _ in range(4):
            offset = random.randint(-10, 10)
            if offset == 0:
                offset = random.randint(1, 5)
            option = base + offset
            if option not in options and option > 0:
                options.append(option)

        while len(options) < 5:
            options.append(random.randint(1, 100))

        random.shuffle(options)
        correct_index = options.index(correct_answer_value)
        return [str(opt) for opt in options], chr(65 + correct_index)  # A, B, C, D, E
    else:
        # Metin tabanlı sorular için standart seçenekler
        return ['A şıkkı', 'B şıkkı', 'C şıkkı', 'D şıkkı', 'E şıkkı'], random.choice(['A', 'B', 'C', 'D', 'E'])

def generate_questions(num_questions=100):
    """100 soru oluştur"""
    questions = []

    # Dağılım: TYT: 50, AYT: 40, YDT: 10
    distribution = {
        'TYT': 50,
        'AYT': 40,
        'YDT': 10
    }

    for exam_type, count in distribution.items():
        subjects = list(QUESTION_TEMPLATES[exam_type].keys())

        for i in range(count):
            # Rastgele konu seç
            subject = random.choice(subjects)
            templates = QUESTION_TEMPLATES[exam_type][subject]
            template = random.choice(templates)

            # Soru metni oluştur
            question_text = generate_random_value(template['text'])

            # Seçenekler oluştur
            correct_value = random.randint(10, 100)
            options, correct_answer = generate_options(correct_value)

            # Açıklama
            explanation = f"Bu soru {template['topic']} konusundan çıkmıştır. Doğru cevap {correct_answer} şıkkıdır."

            question = {
                'question_text': question_text,
                'option_a': options[0],
                'option_b': options[1],
                'option_c': options[2],
                'option_d': options[3],
                'option_e': options[4],
                'correct_answer': correct_answer,
                'explanation': explanation,
                'exam_type': exam_type,
                'subject': subject,
                'topic': template['topic'],
                'difficulty': template['difficulty'],
                'discrimination': template['discrimination'],
                'guessing': template['guessing']
            }

            questions.append(question)

    return questions

def save_to_postgresql(questions):
    """PostgreSQL'e kaydet"""
    conn = psycopg2.connect(**PG_CONN)
    cursor = conn.cursor()

    # Tablo var mı kontrol et, yoksa oluştur
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id SERIAL PRIMARY KEY,
            question_text TEXT NOT NULL,
            option_a TEXT,
            option_b TEXT,
            option_c TEXT,
            option_d TEXT,
            option_e TEXT,
            correct_answer VARCHAR(1),
            explanation TEXT,
            exam_type VARCHAR(50),
            subject VARCHAR(100),
            topic VARCHAR(200),
            difficulty FLOAT,
            discrimination FLOAT,
            guessing FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Sorular ekle
    insert_query = """
        INSERT INTO questions (
            question_text, option_a, option_b, option_c, option_d, option_e,
            correct_answer, explanation, exam_type, subject, topic,
            difficulty, discrimination, guessing
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    data = [
        (
            q['question_text'],
            q['option_a'],
            q['option_b'],
            q['option_c'],
            q['option_d'],
            q['option_e'],
            q['correct_answer'],
            q['explanation'],
            q['exam_type'],
            q['subject'],
            q['topic'],
            q['difficulty'],
            q['discrimination'],
            q['guessing']
        )
        for q in questions
    ]

    execute_batch(cursor, insert_query, data)
    conn.commit()

    # Doğrulama
    cursor.execute("SELECT COUNT(*), exam_type FROM questions GROUP BY exam_type")
    results = cursor.fetchall()

    print("\n✅ SORULAR BAŞARIYLA KAYDEDİLDİ!")
    print("=" * 60)
    print(f"Toplam: {sum(r[0] for r in results)} soru")
    print("\nDağılım:")
    for count, exam_type in results:
        print(f"  {exam_type}: {count} soru")

    cursor.close()
    conn.close()

def main():
    """Ana fonksiyon"""
    print("🚀 100 ÖSYM SORUSU OLUŞTURULUYOR...")
    print("=" * 60)

    # Sorular oluştur
    print("\n1️⃣  Sorular oluşturuluyor...")
    questions = generate_questions(100)
    print(f"   ✅ {len(questions)} soru hazırlandı")

    # Dağılımı göster
    print("\n2️⃣  Soru Dağılımı:")
    exam_counts = {}
    for q in questions:
        exam_type = q['exam_type']
        exam_counts[exam_type] = exam_counts.get(exam_type, 0) + 1

    for exam_type, count in exam_counts.items():
        print(f"   {exam_type}: {count} soru")

    # PostgreSQL'e kaydet
    print("\n3️⃣  PostgreSQL'e kaydediliyor...")
    save_to_postgresql(questions)

    print("\n" + "=" * 60)
    print("✅ İŞLEM TAMAMLANDI!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ HATA: {e}")
        import traceback
        traceback.print_exc()
