# -*- coding: utf-8 -*-
"""
KIRO2 - 345 Yayinevi TYT Turkce Soru Bankasi 2025
Test 4 = Sayfa 12-13 = SOZCUKTE ANLAM Kazanim Odakli Sorular 4
11 soru INSERT (idempotent, hash dedupe ile)

Cevap anahtari: sayfa 432 zoom screenshot, 1 Mayis 2026
1.D 2.C 3.E 4.C 5.A 6.B 7.E 8.E 9.C 10.B 11.C

Topic: TUR.ANL Anlam Bilgisi (c1350eca-9173-43e7-a6ec-175e42081510)
Sema: Test 3 sablonu ile birebir, sadece test/sayfa/icerik degisti.
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
TEST_NAME = "Test 4 - Sozcukte Anlam Kazanim Odakli Sorular 4"
SOURCE_PAGES = "12-13"
ANSWER_KEY_PAGE = "432"

OCR_METHOD = "claude_opus_4_7_v1"
OCR_DATE = "2026-05-01"
MERGE_SOURCE = "claude_opus_4_7_v1"
OCR_SESSION = "2026-05-01_345_tyt_tr_test04"

# ==================== 11 SORU ====================

QUESTIONS = [
    {
        "q_no": 1,
        "page": 12,
        "question_text": (
            "Aşağıdaki cümlelerde geçen altı çizili sözcüklerden hangileri ortak "
            "köklüdür?"
        ),
        "option_a": (
            "Her yaz bu sahil kasabasına tatil için gelirdik. / "
            "Tahtadaki sorunun çözümünü defterine yaz."
        ),
        "option_b": (
            "Genç yaşta kırlaşan saçları çok şey anlatıyordu. / "
            "İhtiyar adam, güvercinlere darı tanelerini saçıyor."
        ),
        "option_c": (
            "Ocakta iki haftalığına Uludağ'a gideceğim. / "
            "Ocakta çok ısıttığım yemeğin dibi tutmuştu."
        ),
        "option_d": (
            "İki taraf arasındaki savaş, antlaşmayla sona erdi. / "
            "Ordular bu meydanda yirmi gün boyunca savaştı."
        ),
        "option_e": (
            "Hoş kokulu, al güllerden güzel bir demet yaptı. / "
            "Bu kitabı bir ay önce almama rağmen okuyamadım."
        ),
        "correct_answer": "D",
        "osym_year": None,
    },
    {
        "q_no": 2,
        "page": 12,
        "question_text": (
            "İnsana ait bir özelliği insan dışındaki varlıklara aktarmaya "
            "\"insandan doğaya aktarma\" denir.\n\n"
            "Aşağıdaki cümlelerin hangisinde bu bilgiyi örneklendiren bir kullanım "
            "vardır?"
        ),
        "option_a": "Ümitle açılıp kazançla kapatılan bir kitap, iyi bir kitaptır.",
        "option_b": "Bir insanın değeri, okuduğu kitapların değeri ile ölçülür.",
        "option_c": "Kitabın elinden tutan insanlar, hayatta yalnız yürümezler.",
        "option_d": "Kitap hiç solmayacak ve kokusu azalmayacak bir bitkidir.",
        "option_e": "Gençlerini kitapla beslemeyen milletlerin sonu çok acıdır.",
        "correct_answer": "C",
        "osym_year": None,
    },
    {
        "q_no": 3,
        "page": 12,
        "question_text": (
            "\"Tutmak\" sözcüğü aşağıdaki cümlelerin hangisinde "
            "\"beğenmek, benimsemek\" anlamında kullanılmıştır?"
        ),
        "option_a": (
            "Burada bir yazlık tuttum, yazın üç ay boyunca güneş ve denizleyiz."
        ),
        "option_b": (
            "Şaşırtıcı bir şekilde arkadaşımın tahmini ile benimki birbirini tuttu."
        ),
        "option_c": (
            "Hele şu kar iyice bir tutsun da yarın sabah bir kardan adam yapalım."
        ),
        "option_d": (
            "Böylesi hırçın bir kaptanı bu dayanıksız kafeste nasıl tutabilirdiniz?"
        ),
        "option_e": (
            "O dönemde sanatçılar klasisizmi tutmuş ve eserlerinde uygulamıştı."
        ),
        "correct_answer": "E",
        "osym_year": None,
    },
    {
        "q_no": 4,
        "page": 12,
        "question_text": (
            "Onun bu eşsiz dizelerini okuyup da sarsılmayan bir okur yoktur.\n\n"
            "\"Sarsılmak\" sözcüğü, yukarıdaki cümlede hangi anlamda "
            "kullanılmıştır?"
        ),
        "option_a": "Tedirgin olmak",
        "option_b": "Titremek",
        "option_c": "Çok etkilenmek",
        "option_d": "Sevinmek",
        "option_e": "Bilincini yitirmek",
        "correct_answer": "C",
        "osym_year": None,
    },
    {
        "q_no": 5,
        "page": 12,
        "question_text": (
            "Aşağıdaki cümlelerin hangisinde bir duyu ile ilgili ayrıntı bir başka "
            "duyuya aktarılmıştır?"
        ),
        "option_a": (
            "Bu birbirinden lezzetli nağmeleri dinledikçe beni bir memnuniyet "
            "alıyordu."
        ),
        "option_b": (
            "Toplantıda söz alamayan üyeler, ertesi gün yönetim kuruluna sitem "
            "etmişti."
        ),
        "option_c": (
            "Kütüphaneye girdiğimizde en başta hırıltılı bir ses ve sayfa "
            "hışırtıları işittik."
        ),
        "option_d": (
            "Burada nereye baksan yeşilin binbir tonuyla süslenmiş tepecikler "
            "görürsün."
        ),
        "option_e": (
            "Kitabın kapağını kaldırdığımda beni karşılayan leylak, çok güzel "
            "kokuyordu."
        ),
        "correct_answer": "A",
        "osym_year": None,
    },
    {
        "q_no": 6,
        "page": 12,
        "question_text": (
            "Beş duyu organının en az biri ile algılanabilen varlıkları karşılayan "
            "sözcüklere \"somut anlamlı sözcük\" denir.\n\n"
            "Buna göre, aşağıdaki cümlelerin hangisinde geçen altı çizili sözcük "
            "somuttur?"
        ),
        "option_a": (
            "Öyle anlar olur ki aklımdan geçenleri bir kâğıda yazmadan duramam."
        ),
        "option_b": (
            "Tayfalardan biri yüksekçe bir yere çıkıp çevreyi gözetlemeye başladı."
        ),
        "option_c": (
            "Gözleriniz ve sözlerinizden sizde dev bir zekâ bulunduğu anlaşılıyor."
        ),
        "option_d": (
            "Şair bu şiirinde özgün düşleri ve eşine az rastlanır imajları "
            "kullanmış."
        ),
        "option_e": (
            "Buradaki herkese göre Cevdet Bey'in endişelerinde haklılık payı var."
        ),
        "correct_answer": "B",
        "osym_year": None,
    },
    {
        "q_no": 7,
        "page": 13,
        "question_text": (
            "Aşağıdaki cümlelerin hangisinde geçen altı çizili sözcük nitel "
            "anlamlıdır?"
        ),
        "option_a": (
            "Yazarın şimdiye kadarki en kalın kitabı dört yüz elli sayfadan "
            "oluşuyor."
        ),
        "option_b": (
            "Şehirde termometrelerin kaydettiği en yüksek sıcaklık otuz dereceydi."
        ),
        "option_c": (
            "Eşyaların yerleştirildiği kolilerden ağır olanları kamyona yüklediler."
        ),
        "option_d": (
            "Deterjanımız, düşük sıcaklıklarda bile çamaşırları tertemiz yapıyor."
        ),
        "option_e": (
            "Bu ince davranışınız, ne denli anlayışlı ve kibar olduğunuzu "
            "gösteriyor."
        ),
        "correct_answer": "E",
        "osym_year": None,
    },
    {
        "q_no": 8,
        "page": 13,
        "question_text": (
            "Laf kalabalığı yapıp da büyük şairler sınıfına giren şair yoktur. "
            "Bakın Cahit Sıtkı Tarancı'ya. Türk edebiyatının bu büyük şairi, "
            "zımparayı sık sık kullanmıştır.\n\n"
            "Bu parçada geçen \"zımparayı sık sık kullanmak\" sözünün kattığı "
            "anlam aşağıdakilerin hangisidir?"
        ),
        "option_a": "Sade dille şiir yazmak",
        "option_b": "Dolaylı ifadelerden kaçınmak",
        "option_c": "Söz oyunlarından bolca yararlanmak",
        "option_d": "Şairane söyleyişlere başvurmak",
        "option_e": "Şiiri fazlalıklardan arındırmak",
        "correct_answer": "E",
        "osym_year": None,
    },
    {
        "q_no": 9,
        "page": 13,
        "question_text": (
            "\"Üstüne\" sözcüğü aşağıdaki cümlelerin hangisinde \"hakkında\" "
            "anlamında kullanılmıştır?"
        ),
        "option_a": "Çok üşüyen ihtiyar adamın üstüne bir yorgan attılar.",
        "option_b": "O gün misafirler, tam da yemeğin üstüne gelmişlerdi.",
        "option_c": "Türk edebiyatı üstüne pek çok makale kaleme almıştı.",
        "option_d": "Baudelaire'in üstüne sembolist şair tanımam, diyordu.",
        "option_e": "Dolabın üstüne anneannemin dantellerinden serdiler.",
        "correct_answer": "C",
        "osym_year": None,
    },
    {
        "q_no": 10,
        "page": 13,
        "question_text": (
            "Geçtiğimiz yüzyılın(I) başlarında(II) bazı sanat düşünürleri "
            "sanatın psikolojinin temeli olması gerektiği görüşünü "
            "savunmuşlardır. Bu düşüncenin(III) kaynağında estetiğin "
            "ayrıntılı(IV) bir biçimde ve psikolojik anlamda çözümlenmesi "
            "amaçlanmaktadır. Sanatsal objenin kendine özgü(V) yönü ancak onu "
            "izleyenin algı yetisi, düş gücü sayesinde anlaşılabilmektedir. "
            "Sanat dediğimiz şey, davranışların ürünüdür. Davranış dendiğinde "
            "de akla psikoloji gelmektedir. Bu sebeple insanın psikolojisi ile "
            "onun estetik algılayışı arasında bir ilişkiden bahsedilebilir.\n\n"
            "Bu parçadaki altı çizili sözcüklerden hangisinin yerine anlamdaşı "
            "getirilemez?"
        ),
        "option_a": "I",
        "option_b": "II",
        "option_c": "III",
        "option_d": "IV",
        "option_e": "V",
        "correct_answer": "B",
        "osym_year": None,
    },
    {
        "q_no": 11,
        "page": 13,
        "question_text": (
            "I.   Bugünün Sarayları ve Nilgün, Refik Halit Karay'ın "
            "eserlerindendir.\n"
            "II.  Burak, arkadaşlarının arasında hitabet ve yazı gücüyle öne "
            "çıkıyordu.\n"
            "III. Bu projeyi zamanında teslim etmek için gece gündüz "
            "çalışıyorlarmış.\n"
            "IV.  Roman, edebiyat türlerinin en popüler ve önemli olanlarından "
            "biridir.\n"
            "V.   Dünkü derste, felsefe akımlarından egzistansiyalizm üzerinde "
            "durduk.\n\n"
            "Numaralanmış cümlelerin hangisinde genelden özele sıralama "
            "yapılmıştır?"
        ),
        "option_a": "II",
        "option_b": "IV",
        "option_c": "V",
        "option_d": "III",
        "option_e": "I",
        "correct_answer": "C",
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
                "ocr_session": OCR_SESSION,
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
        "answer_key_source": "sayfa 432 zoom screenshot, 1 May 2026",
        "total_questions": len(QUESTIONS),
        "inserted_count": len(inserted),
        "skipped_count": len(skipped),
        "error_count": len(errors),
        "inserted": inserted,
        "skipped": skipped,
        "errors": errors,
    }

    with open(r"C:\Users\husey\kiro2\insert_345_test04_sozcukte_anlam_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n=== OZET ===")
    print(f"Inserted: {len(inserted)}")
    print(f"Skipped:  {len(skipped)}")
    print(f"Errors:   {len(errors)}")


if __name__ == "__main__":
    main()
