"""emergency content - execute_values ile guvenli insert"""
import psycopg2
from psycopg2 import sql
import uuid

conn = psycopg2.connect(
    host='localhost', port=5434, dbname='kiro2',
    user='postgres', password='changeme_strong_password_here'
)
cur = conn.cursor()
cur.execute("SELECT id FROM topic_hierarchy LIMIT 1")
TOPIC = cur.fetchone()[0]
cur.execute("SELECT grade_level, bloom_level, bloom_category, osym_format_compliant, student_success_rate, difficulty_update_count, calibration_sample_size, calibration_quality_score, morphology_complexity, word_count, unique_word_count, average_word_length, readability_score, times_asked, times_correct, times_wrong, times_skipped, average_response_time, median_response_time, exposure_rate FROM question_bank LIMIT 1")
t = cur.fetchone()
(grade_level, bloom_level, bloom_cat, osym, success_rate, diff_upd, cal_size, cal_qual,
 morph, wc, uwc, awl, readability, t_asked, t_correct, t_wrong, t_skipped, avg_rt, med_rt, exp_rate) = t

questions = [
    ('3 basamakli en buyuk cift sayi ile 2 basamakli en kucuk tek sayinin toplami?', '1009', '1010', '1011', '1012', 'A', 'TYT', 'MATEMATIK', -0.5),
    ('Bir sayinin yuzde 20si 40 ise yuzde 30u kactir?', '50', '60', '70', '80', 'B', 'TYT', 'MATEMATIK', -0.3),
    ('3x-7=2x+5 denkleminin cozumu?', '{10}', '{11}', '{12}', '{13}', 'C', 'TYT', 'MATEMATIK', -0.4),
    ('Bir karenin cevresi 48 cm ise alani kac cm kare?', '121', '132', '144', '156', 'C', 'TYT', 'MATEMATIK', -0.2),
    ('5 faktoriyel kactir?', '60', '100', '120', '125', 'C', 'TYT', 'MATEMATIK', -0.3),
    ('Asagidakilerden hangisi asal sayidir?', '91', '87', '97', '93', 'C', 'TYT', 'MATEMATIK', -0.1),
    ('2 uzeri 10 kactir?', '512', '1024', '2048', '256', 'B', 'TYT', 'MATEMATIK', 0.0),
    ('Bir ucgenin ic acilari toplami kac derecedir?', '90', '180', '270', '360', 'B', 'TYT', 'MATEMATIK', -0.8),
    ('0.5 carpı 0.5 kactir?', '0.025', '0.05', '0.25', '0.50', 'C', 'TYT', 'MATEMATIK', -0.9),
    ('Dogal sayilarin en kucugu hangisidir?', '0', '1', 'Belirsiz', 'Yok', 'A', 'TYT', 'MATEMATIK', -0.6),
    ('Su kac derecede kaynar?', '90', '95', '100', '105', 'C', 'TYT', 'FEN', -0.7),
    ('Hucrenin enerji merkezi hangi organeldir?', 'Ribozom', 'Mitokondri', 'Golgi', 'Lizozom', 'B', 'TYT', 'FEN', -0.3),
    ('DNA yapisinda hangi baz bulunmaz?', 'Adenin', 'Guanin', 'Sitozin', 'Urasil', 'D', 'TYT', 'FEN', 0.2),
    ('Atom numarasi neyi ifade eder?', 'Notron sayisi', 'Proton sayisi', 'Elektron sayisi', 'Kutle sayisi', 'B', 'TYT', 'FEN', -0.2),
    ('Isik en hizli hangi ortamda yayilir?', 'Su', 'Cam', 'Hava', 'Vakum', 'D', 'TYT', 'FEN', 0.0),
    ('Fiil nedir?', 'Varlik karsilayan', 'Sifat belirten', 'Is hareket bildiren', 'Baglama yapan', 'C', 'TYT', 'TURKCE', -0.5),
    ('Ozne-yuklem uyumsuzlugu hangi cumlede vardir?', 'Ben gidiyorum', 'Sen geliyor', 'O okuyor', 'Biz calisiyoruz', 'B', 'TYT', 'TURKCE', 0.0),
    ('Turkce kokenli sozcuk hangisidir?', 'kalem', 'kitap', 'okul', 'sinema', 'C', 'TYT', 'TURKCE', 0.1),
    ('Cogul eki almis sozcuk hangisidir?', 'masa', 'kapi', 'kitaplar', 'kalem', 'C', 'TYT', 'TURKCE', -0.4),
    ('Nesne nedir?', 'Eylemi yapan', 'Eylem uzerinde gerceklesen', 'Eylemi niteleyen', 'Eylemle biten', 'B', 'TYT', 'TURKCE', -0.2),
]

INSERT_SQL = """
INSERT INTO question_bank (
    id, question_text, option_a, option_b, option_c, option_d, correct_answer,
    primary_topic_id, bloom_level, bloom_category, difficulty_level, irt_based_difficulty,
    student_success_rate, difficulty_update_count,
    irt_discrimination, irt_difficulty, irt_guessing, irt_upper_asymptote,
    is_calibrated, calibration_sample_size, calibration_quality_score,
    morphology_complexity, word_count, unique_word_count, average_word_length, readability_score,
    times_asked, times_correct, times_wrong, times_skipped,
    average_response_time, median_response_time, exposure_rate,
    exam_type, subject_area, grade_level, osym_format_compliant,
    quality_score, quality_review_status, is_active, is_public,
    created_by, created_at, updated_at
) VALUES (
    %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, 'MEDIUM', 'medium',
    %s, %s,
    1.2, %s, 0.25, 1.0,
    TRUE, %s, %s,
    %s, %s, %s, %s, %s,
    0, 0, 0, 0,
    %s, %s, %s,
    %s, %s, %s, %s,
    0.8, 'approved', TRUE, FALSE,
    'de384ad3-93f6-4ff4-8efb-d430bdc55733', NOW(), NOW()
)
"""

inserted = 0
for q in questions:
    qtext, a, b, c, d, ans, exam, subj, irt_diff = q
    cur.execute(INSERT_SQL, (
        str(uuid.uuid4()), qtext, a, b, c, d, ans,
        TOPIC, bloom_level, bloom_cat,
        success_rate, diff_upd,
        irt_diff,
        cal_size, cal_qual,
        morph, wc, uwc, awl, readability,
        avg_rt, med_rt, exp_rate,
        exam, subj, grade_level, osym,
    ))
    inserted += 1

conn.commit()
print(f"Eklendi: {inserted}")
cur.execute("SELECT COUNT(*) FROM question_bank WHERE created_by='emergency_import'")
print("Emergency:", cur.fetchone()[0])
cur.execute("SELECT COUNT(*) FROM question_bank")
print("Toplam:", cur.fetchone()[0])
conn.close()
