# -*- coding: utf-8 -*-
"""
KIRO2 - 345 Yayinevi TYT Turkce Soru Bankasi 2025
Test 3 = Sayfa 10-11 = SOZCUKTE ANLAM Kazanim Odakli Sorular 3
11 soru INSERT (idempotent, hash dedupe ile)

Cevap anahtari: sayfa 432 zoom screenshot, 30 Nisan 2026
1.A 2.C 3.D 4.C 5.C 6.D 7.C 8.C 9.D 10.D 11.E

Topic: TUR.ANL Anlam Bilgisi (c1350eca-9173-43e7-a6ec-175e42081510)
Sema: Aromat'taki calismis kayit sablonu (35f939b8...) baz alindi
"""

import json
import hashlib
import re
import psycopg2
from psycopg2.extras import Json
from datetime import datetime, timezone

# ==================== KONFIGURASYON ====================
DB_DSN = "postgresql://postgres:1470@localhost:5434/kiro2"

PRIMARY_TOPIC_ID = "c1350eca-9173-43e7-a6ec-175e42081510"  # TUR.ANL Anlam Bilgisi
BOOK_NAME = "345 Yayinevi TYT Turkce Soru Bankasi 2025"
SOURCE_BOOK = "345 Yayinevi TYT Turkce Soru Bankasi 2025"
TEST_NAME = "Test 3 - Sozcukte Anlam Kazanim Odakli Sorular 3"
SOURCE_PAGES = "10-11"
ANSWER_KEY_PAGE = "432"

OCR_METHOD = "claude_opus_4_7_v1"
OCR_DATE = "2026-04-30"
MERGE_SOURCE = "claude_opus_4_7_v1"

# ==================== 11 SORU ====================

QUESTIONS = [
    {
        "q_no": 1,
        "page": 10,
        "question_text": (
            "Özellikle nezle veya grip olduğumuzda gündüz saatlerinde görece(I) "
            "(genellikle) daha iyi hissederken gece olduğunda hastalık belirtilerini(II) "
            "(göstergelerini) daha şiddetli hissederiz. Bunun nedeni, vücudun bağışıklık "
            "sisteminin belli bir düzen(III) (uyum) içinde olmasıdır. Gün boyunca(IV) "
            "(süresince) vücudu savunan bağışıklık sistemi aktifken(V) (çalışırken) "
            "geceleri dinlenmeye geçer ve hücresel savunma azalır.\n\n"
            "Bu parçada numaralanmış sözcüklerden hangisinin anlamı, ayraç içinde "
            "verilenle uyuşmamaktadır?"
        ),
        "option_a": "I",
        "option_b": "II",
        "option_c": "III",
        "option_d": "IV",
        "option_e": "V",
        "correct_answer": "A",
        "osym_year": 2022,
    },
    {
        "q_no": 2,
        "page": 10,
        "question_text": (
            "Dünya değişiyor dostlarım. Günün birinde gökyüzünde, güz mevsiminde artık "
            "esmer lekeler göremeyeceksiniz. Günün birinde yol kenarlarında toprak "
            "anamızın koyu yeşil saçlarını göremeyeceksiniz. Bizim için değil ama "
            "çocuklar, sizin için kötü olacak. Bir kuşları ve yeşillikleri çok gördük. "
            "Sizin için kötü olacak. Berden hikayesi.\n\n"
            "Bu parçadaki \"koyu yeşil saç\" ifadesi, benzerlik ilgisiyle \"çimen\"lerin "
            "yerine kullanılmıştır. Benzer bir kullanım aşağıdaki cümlelerin hangisinde "
            "vardır?"
        ),
        "option_a": "Bu yazımızın hem şiirler hem de romanları yazdığı bilinmektedir.",
        "option_b": "Kitap okumanın insana tarifsiz bir mutluluk verdiğini biliyorum.",
        "option_c": "Son yıllarda nice elmas, edebiyat dergilerinde öykü yazmaya başladı.",
        "option_d": "Edebiyatın pek çok türünde eser yazmış ünlü bir sanatçımızdır o.",
        "option_e": "Şiirde felsefi düşünceler ile ilgili bir makale yazmayı düşünüyor.",
        "correct_answer": "C",
        "osym_year": None,
    },
    {
        "q_no": 3,
        "page": 10,
        "question_text": (
            "Dikkat, algılama, anımsama, düşünme ve öğrenme yönlerimiz genelde somut "
            "değil, soyuttur. Diğer bir deyişle bilişsel yaşamımızda çoğunlukla "
            "kategorize eder, betimler, sınıflandırır ve adlandırırız. Bununla birlikte "
            "pek çok gerçekliği olduğu şekliyle kavramayız. Deneyimlerimizin büyük "
            "bölümü kategorilerimizin, kurgularımızın ve kurallarımızın süzgecinden "
            "geçirilir.\n\n"
            "Bu parçada geçen aşağıdaki sözcüklerden hangileri anlamca birbirine en "
            "yakındır?"
        ),
        "option_a": "Yaşam – deneyim",
        "option_b": "Bilişsel – düşünme",
        "option_c": "Algılama – öğrenme",
        "option_d": "Genelde – çoğunlukla",
        "option_e": "Anımsama – düşünme",
        "correct_answer": "D",
        "osym_year": None,
    },
    {
        "q_no": 4,
        "page": 10,
        "question_text": (
            "I.   Roman, bireyin açmazlarını dile getirmesi açısından önemli "
            "tespitlerde bulunmuş.\n"
            "II.  Aslında gazeteci, haber kaynağını söyleyerek doğru olanı yaptı.\n"
            "III. Yazar, sosyal meseleleri dile getirmeden kalıcı olamaz.\n"
            "IV.  Konferansa gelenlere doyurucu bilgiler sunan akademisyen, kendinden "
            "emin görünüyordu.\n"
            "V.   Şair, çocukluk anılarını kullanarak bugünkü duygularını açıklamaya "
            "çalışmış.\n\n"
            "Yukarıdaki numaralanmış cümlelerin hangisinde altı çizili sözcük genel "
            "anlamıyla kullanılmıştır?"
        ),
        "option_a": "I",
        "option_b": "II",
        "option_c": "III",
        "option_d": "IV",
        "option_e": "V",
        "correct_answer": "C",
        "osym_year": None,
    },
    {
        "q_no": 5,
        "page": 10,
        "question_text": (
            "Aşağıdaki cümlelerin hangisinde altı çizili sözcük temel anlamıyla "
            "kullanılmamıştır?"
        ),
        "option_a": "Kime yeterli kadarı az gelirse ona hiçbir şey yetmez.",
        "option_b": "Bir kalbi fethetmek, bir şehri fethetmekten daha zordur.",
        "option_c": "İnsan, ortalığı kırıp geçirmeden de kahraman olabilir.",
        "option_d": (
            "Gizli kalan kabiliyetler, killi toprağa benzer; önemli olan onların nasıl "
            "kullanılacağıdır."
        ),
        "option_e": "Kahramanca ölmekten çok, kahramanca yaşamak zordur.",
        "correct_answer": "C",
        "osym_year": None,
    },
    {
        "q_no": 6,
        "page": 11,
        "question_text": (
            "\"Sarmak\" sözcüğü aşağıdakilerin hangisinde \"Bu yazarın anlatımı beni "
            "sardı ki öykülerini okumaya doyamadım.\" cümlesindeki anlamıyla "
            "kullanılmıştır?"
        ),
        "option_a": (
            "Bir annenin bebeğini nasıl sevgiyle sararsa biz Türkler yurdumuzu öyle "
            "severiz."
        ),
        "option_b": (
            "Güvenlik güçleri otuz katlı gökdelenin etrafını sardı ve gerekli "
            "tedbirleri aldı."
        ),
        "option_c": (
            "Örümcek, yakaladığı avı iplikleri sardı ve avlanmaya bir süre daha devam "
            "etti."
        ),
        "option_d": (
            "Beni her film sarmaz, özellikle macera ve komedi filmlerinden zevk alırım."
        ),
        "option_e": (
            "Eşyaları satın aldılar, hediye ambalajına sardılar ve öğrencilere "
            "dağıttılar."
        ),
        "correct_answer": "D",
        "osym_year": None,
    },
    {
        "q_no": 7,
        "page": 11,
        "question_text": (
            "I.   Ana caddeden yükselen sesler, bazen sofadaki konuşmalara karışırdı.\n"
            "II.  Nurettin Bey daha konağa ulaşmadan köşe bucak pırıl pırıl olurdu.\n"
            "III. İsa'nın gramofonu cızır cızır ettiğinde müziğin başladığını anlardık.\n"
            "IV.  Bu ihtiyar yaslıda bir başıma beklemek, beni sıkıntıdan bunaltmıştı.\n"
            "V.   O zamanlar seyyar satıcıların bağrışmaları sokaklardan eksik olmazdı.\n\n"
            "Yukarıdaki numaralanmış cümlelerin hangisinde yansıma sözcük "
            "kullanılmıştır?"
        ),
        "option_a": "V",
        "option_b": "IV",
        "option_c": "III",
        "option_d": "I",
        "option_e": "II",
        "correct_answer": "C",
        "osym_year": None,
    },
    {
        "q_no": 8,
        "page": 11,
        "question_text": (
            "Aşağıdaki cümlelerin hangisinde geçen altı çizili sözcük mecaz anlamlıdır?"
        ),
        "option_a": "Paslanmış menteşeler ahşap kapıyı zar zor tutuyordu.",
        "option_b": "Kadı Efendi yorulmuş olacak ki bir iskemleye oturdu.",
        "option_c": "Konuşmasından fikirlerimize sıcak baktığını anlıyorum.",
        "option_d": "Bir dakikalık bir gecikme yüzünden otobüsü kaçırdık.",
        "option_e": "Uçsuz bucaksız denizi seyredip anılara daldım bir an.",
        "correct_answer": "C",
        "osym_year": None,
    },
    {
        "q_no": 9,
        "page": 11,
        "question_text": (
            "Sayılabilen, ölçülebilen, tartılabilen varlık, durum ve nitelikleri "
            "karşılayan sözcükler nicel anlamlıdır.\n\n"
            "Buna göre, aşağıdaki altı çizili sözcüklerden hangisi nicelik "
            "bildirmektedir?"
        ),
        "option_a": (
            "Kıskançlık; tanımlanan duyguların en korkuncu, yıpratıcısı ve "
            "yenilmezidir."
        ),
        "option_b": (
            "Tarihte yön ve şan veren büyük insanlar, ideallerinin ardından "
            "gidenlerdir."
        ),
        "option_c": (
            "Kelimeler şairin ruhundan fışkırmazsa okurun duygu süzücüğü dinemez."
        ),
        "option_d": (
            "Nasıl ki dünyayı aydınlatan tek bir güneş varsa zihni aydınlatan da "
            "bilgidir."
        ),
        "option_e": (
            "Yüksek bir karaktere sahip olmak, erdemli insanın akla ilk gelen "
            "özelliğidir."
        ),
        "correct_answer": "D",
        "osym_year": None,
    },
    {
        "q_no": 10,
        "page": 11,
        "question_text": (
            "Eleştirmen, ele aldığı eserde belirli bir yöntemin ölçütlerine uyarak "
            "inceleme yapar ve bir türde yoğunlaşırsa başarılı olur.\n\n"
            "\"Yoğunlaşmak\" sözcüğünün bu cümleye kattığı anlam aşağıdakilerin "
            "hangisinde vardır?"
        ),
        "option_a": "Bu yazarımız, üslubunu yetkin biçime ulaştırırsa kalıcılaşabilir.",
        "option_b": "Toplumsal izlekleri ustaca ele almasıyla öne çıkmıştır.",
        "option_c": "Artık bir metin türünde karar vermek zorundaydı.",
        "option_d": "Bu alanda uzmanlaşmak gerektiğinin bilincindeydi.",
        "option_e": (
            "Makale türündeki metinlerle tanınırsam amacıma ulaşmış olurum."
        ),
        "correct_answer": "D",
        "osym_year": None,
    },
    {
        "q_no": 11,
        "page": 11,
        "question_text": (
            "(I) Günler günleri, haftalar haftaları kovalıyordu. (II) Suda sabun gibi "
            "eriyordu aylar. (III) Ben ise kalemi elime alamıyordum nedense. (IV) Daha "
            "doğrusu kalemi elime alsam da bir türlü işletemiyordum. (V) Şiirime güç "
            "katacak imge ve ölçüyü inşa edemiyordum bir türlü.\n\n"
            "Bu parçadaki numaralanmış cümlelerin hangisinde terim anlamlı bir sözcük "
            "kullanılmıştır?"
        ),
        "option_a": "I",
        "option_b": "II",
        "option_c": "III",
        "option_d": "IV",
        "option_e": "V",
        "correct_answer": "E",
        "osym_year": None,
    },
]

# ==================== HELPER ====================

def compute_hash(qtext, a, b, c, d, e):
    """Backend backfill_soru_hash.py ile ayni formul"""
    e_safe = e if e is not None else ""
    payload = (
        qtext.lower().strip()
        + "|" + a + "|" + b + "|" + c + "|" + d + "|" + e_safe
    )
    return hashlib.md5(payload.encode("utf-8")).hexdigest()


def text_stats(text):
    """word_count, unique_word_count, average_word_length"""
    words = re.findall(r"\w+", text, re.UNICODE)
    word_count = len(words)
    unique = len(set(w.lower() for w in words))
    if word_count == 0:
        avg_len = 0.0
    else:
        avg_len = round(sum(len(w) for w in words) / word_count, 2)
    return word_count, unique, avg_len


# ==================== MAIN ====================

def main():
    conn = psycopg2.connect(DB_DSN)
    conn.autocommit = False
    cur = conn.cursor()

    inserted = []
    skipped = []
    errors = []

    print(f"Toplam {len(QUESTIONS)} soru islenecek\n")

    for q in QUESTIONS:
        try:
            soru_hash = compute_hash(
                q["question_text"],
                q["option_a"], q["option_b"], q["option_c"],
                q["option_d"], q["option_e"],
            )

            # Idempotent check
            cur.execute(
                "SELECT id FROM question_bank WHERE soru_hash = %s LIMIT 1",
                (soru_hash,),
            )
            existing = cur.fetchone()
            if existing:
                skipped.append({
                    "q_no": q["q_no"],
                    "reason": "hash_exists",
                    "existing_id": str(existing[0]),
                    "hash": soru_hash,
                })
                print(f"  Q{q['q_no']:2d}: SKIP (hash exists, id={existing[0]})")
                continue

            wc, uwc, awl = text_stats(q["question_text"])

            pipeline_metadata = {
                "merge_source": MERGE_SOURCE,
                "ocr_method": OCR_METHOD,
                "ocr_date": OCR_DATE,
                "book": BOOK_NAME,
                "test": TEST_NAME,
                "source_pages": SOURCE_PAGES,
                "answer_key_page": ANSWER_KEY_PAGE,
                "test_question_no": q["q_no"],
                "topic_label": "Sozcukte Anlam",
                "ocr_session": "2026-04-30_345_tyt_tr_test03",
            }

            cur.execute(
                """
                INSERT INTO question_bank (
                    id,
                    question_text,
                    option_a, option_b, option_c, option_d, option_e,
                    correct_answer,
                    primary_topic_id,
                    bloom_level, bloom_category,
                    difficulty_level, irt_based_difficulty,
                    student_success_rate,
                    difficulty_update_count,
                    irt_discrimination, irt_difficulty, irt_guessing, irt_upper_asymptote,
                    is_calibrated, calibration_sample_size, calibration_quality_score,
                    morphology_complexity,
                    word_count, unique_word_count, average_word_length, readability_score,
                    times_asked, times_correct, times_wrong, times_skipped,
                    average_response_time, median_response_time, exposure_rate,
                    exam_type, subject_area, grade_level,
                    osym_format_compliant, osym_year,
                    quality_score, quality_review_status,
                    source_book, source_page,
                    pipeline_metadata,
                    is_active, is_public,
                    soru_hash,
                    irt_calibrated, irt_n_responses, is_calib_pool,
                    created_at, updated_at
                ) VALUES (
                    gen_random_uuid()::text,
                    %s,
                    %s, %s, %s, %s, %s,
                    %s,
                    %s,
                    2, 'understand',
                    'MEDIUM', 'medium',
                    0,
                    0,
                    1, 0, 0.2, 1,
                    FALSE, 0, 0.95,
                    0.4,
                    %s, %s, %s, 70,
                    0, 0, 0, 0,
                    0, 0, 0,
                    'TYT', 'TURKCE', 12,
                    TRUE, %s,
                    95, 'approved',
                    %s, %s,
                    %s,
                    TRUE, TRUE,
                    %s,
                    FALSE, 0, FALSE,
                    NOW(), NOW()
                )
                RETURNING id
                """,
                (
                    q["question_text"],
                    q["option_a"], q["option_b"], q["option_c"],
                    q["option_d"], q["option_e"],
                    q["correct_answer"],
                    PRIMARY_TOPIC_ID,
                    wc, uwc, awl,
                    q["osym_year"],
                    SOURCE_BOOK, q["page"],
                    Json(pipeline_metadata),
                    soru_hash,
                ),
            )
            new_id = cur.fetchone()[0]
            inserted.append({
                "q_no": q["q_no"],
                "id": str(new_id),
                "hash": soru_hash,
                "answer": q["correct_answer"],
                "osym_year": q["osym_year"],
                "page": q["page"],
            })
            print(f"  Q{q['q_no']:2d}: OK   (id={new_id}, ans={q['correct_answer']}, p={q['page']})")

        except Exception as e:
            errors.append({"q_no": q["q_no"], "error": str(e)})
            print(f"  Q{q['q_no']:2d}: ERR  {e}")
            conn.rollback()

    if errors:
        print(f"\n{len(errors)} hata var, rollback yapildi")
        conn.rollback()
    else:
        conn.commit()
        print(f"\nCommit yapildi")

    cur.close()
    conn.close()

    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "book": BOOK_NAME,
        "test": TEST_NAME,
        "topic_id": PRIMARY_TOPIC_ID,
        "topic_name": "TUR.ANL Anlam Bilgisi",
        "answer_key_source": "sayfa 432 zoom screenshot, 30 Nis 2026",
        "total_questions": len(QUESTIONS),
        "inserted_count": len(inserted),
        "skipped_count": len(skipped),
        "error_count": len(errors),
        "inserted": inserted,
        "skipped": skipped,
        "errors": errors,
    }

    with open(r"C:\Users\husey\kiro2\insert_345_test03_sozcukte_anlam_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n=== OZET ===")
    print(f"Inserted: {len(inserted)}")
    print(f"Skipped:  {len(skipped)}")
    print(f"Errors:   {len(errors)}")


if __name__ == "__main__":
    main()
