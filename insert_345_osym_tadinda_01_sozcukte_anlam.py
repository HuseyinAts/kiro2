# -*- coding: utf-8 -*-
"""
KIRO2 - 345 Yayinevi TYT Turkce Soru Bankasi 2025
OSYM Tadinda Sorular 1 = Sayfa 14-15 = SOZCUKTE ANLAM
8 soru INSERT (idempotent, hash dedupe ile)

Cevap anahtari: sayfa 432 zoom screenshot, 1 May 2026
1.D 2.A 3.B 4.E 5.D 6.E 7.D 8.C

S3: TYT 2025 CIKMIS SORU (kirmizi cerceveli, "ÖSYM kösesi" etiketli, osym_year=2025)
Diger 7 soru osym_year=null.

Topic: TUR.ANL Anlam Bilgisi (c1350eca-9173-43e7-a6ec-175e42081510)
Sema: Test 4 sablonu ile birebir, sadece test/sayfa/icerik/sayi degisti.
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
TEST_NAME = "OSYM Tadinda Sorular 1 - Sozcukte Anlam"
SOURCE_PAGES = "14-15"
ANSWER_KEY_PAGE = "432"

OCR_METHOD = "claude_opus_4_7_v1"
OCR_DATE = "2026-05-01"
MERGE_SOURCE = "claude_opus_4_7_v1"
OCR_SESSION = "2026-05-01_345_tyt_tr_osym_tadinda_01"

# ==================== 8 SORU ====================

QUESTIONS = [
    {
        "q_no": 1,
        "page": 14,
        "question_text": (
            "Felsefe sıradan ve üstünkörü bir düşünme şekli değildir. Felsefe "
            "alanında güçlü eserler ortaya koyabilmek için ciddi anlamda bir "
            "Türkçe felsefe dili oluşturmak zorundayız. Aksi hâlde felsefe ile "
            "olan tanışıklığımız, gelip geçici bir düzeyde kalacaktır. "
            "Yapılması gereken şey, kuvvetli bir Türkçe felsefe dili oluşturmak "
            "ve kültürümüzü kavramlaştırmaktır. Türkiye'de felsefenin varlık "
            "şartı budur. Bunun sağlanmasıyla bizde de felsefe gelişme ortamı "
            "bulacak ve biz de dünyada bu alanda söz sahibi olacağız. Kendini "
            "uluslararası arenada kanıtlamış filozoflarımızın yetişmesine "
            "uygun bir zemin hazırlayacağız.\n\n"
            "I.   Yerli bir felsefe dili meydana getirmek\n"
            "II.  Kavramlaştırmış bir kültür oluşturmak\n"
            "III. Felsefi düşünüşe önem vermek\n\n"
            "Bu parçadaki altı çizili sözle numaralanmış yargılardan hangilerine "
            "gönderme yapılmıştır?"
        ),
        "option_a": "Yalnız I",
        "option_b": "Yalnız II",
        "option_c": "Yalnız III",
        "option_d": "I ve II",
        "option_e": "II ve III",
        "correct_answer": "D",
        "osym_year": None,
    },
    {
        "q_no": 2,
        "page": 14,
        "question_text": (
            "• Saymak: Kabul etmek\n"
            "• Bakmak: İlgilenmek\n"
            "• Sert: Güçlü, kuvvetli\n\n"
            "Aşağıdaki cümlelerin hangisinde \"saymak, bakmak, sert\" sözcükleri "
            "belirtilen anlamlarını karşılayacak şekilde kullanılmıştır?"
        ),
        "option_a": (
            "Sert adımlarla ilerlerken bu ziyareti saymadığını, en kısa sürede "
            "tekrar görüşmeyi umduğunu ve o güne kadar emanetlere gözü gibi "
            "bakacağını belirtti."
        ),
        "option_b": (
            "Baktığım hiçbir kitapta, böylesine sert ve küçük bir cismin "
            "yumuşak sayılabileceği yazılmamıştı."
        ),
        "option_c": (
            "Sert bir rüzgâr esti ansızın ve saymakta zorluk çektiğimiz düşman "
            "askerlerinin şaşkınlıkla sağa sola baktığını fark ettik."
        ),
        "option_d": (
            "Bunca yıl garibanlara seve seve baktığı gibi onlara hiç sert "
            "sözler sarf etmemiş, o masumları kendi öz evladı saymıştı."
        ),
        "option_e": (
            "Sert ve asabi zannedildiği hâlde büyük küçük demeden herkesi "
            "sayar, sever; konuşurken samimiyetten olsa gerek muhatabının ta "
            "gözlerinin içine bakardı."
        ),
        "correct_answer": "A",
        "osym_year": None,
    },
    {
        "q_no": 3,
        "page": 14,
        "question_text": (
            "Tiyatro tıpkı destanlar gibi toplumsal bir özellik(I) (nitelik) "
            "taşır. Çoğu zaman, ele aldığı(II) (incelediği) konular ve "
            "başvurduğu tekniklerle bireyciliğin kurallarını göz ardı eder(III) "
            "(boşa çıkarır). Sahnedeki doğal performanslar sayesinde(IV) "
            "(aracılığıyla) izleyicilere daha yakından dokunur. Beğenilerdeki "
            "benzerlikler üzerinden kişilerle değil kitlelerle temas kurmayı(V) "
            "(bağlantı sağlamayı) başarır.\n\n"
            "Bu parçada numaralanmış sözlerden hangisinin anlamı parantez ( ) "
            "içinde verilen açıklamayla uyuşmamaktadır?"
        ),
        "option_a": "V",
        "option_b": "III",
        "option_c": "I",
        "option_d": "II",
        "option_e": "IV",
        "correct_answer": "B",
        "osym_year": 2025,
    },
    {
        "q_no": 4,
        "page": 14,
        "question_text": (
            "\"Çalakalem tamamlayıp bastırdığınız bu şiirlerin dikkat çekici "
            "bir yönü yok.\" cümlesindeki altı çizili sözcüğün yakın anlamlısı "
            "aşağıdakilerin hangisinde bulunmaktadır?"
        ),
        "option_a": (
            "Onun romanı bir şaheser olmasa da vasatın üzerine çıkmayı "
            "başarıyor."
        ),
        "option_b": (
            "İnsanı çeşitli hislerin seline kaptıran mısralarla bezenmiş bir "
            "anlatı bu."
        ),
        "option_c": (
            "Üslubunuzdaki titizliğe ve kelime seçiminizdeki hassasiyete "
            "bayıldım."
        ),
        "option_d": (
            "Binbir zahmetle tamamladığınız bu ansiklopedi, alanında çığır "
            "açacak."
        ),
        "option_e": (
            "Gelişigüzel bir anlatı tekniğiyle kalıcı eserler üretmek mümkün "
            "değildir."
        ),
        "correct_answer": "E",
        "osym_year": None,
    },
    {
        "q_no": 5,
        "page": 15,
        "question_text": (
            "Oktay Akbal, sıcak üslubuyla bizim insanımızı anlattı. Gündelik "
            "yaşamda karşılaşılabilecek tipleri eserlerine konu etti. "
            "Özellikle \"Önce Ekmekler Bozuldu\" adlı kitabındaki öykülerde "
            "estetik bir realizm ağır basar. Öyle ki bu kitaptaki anlatı "
            "kişileri kitaptan taşıp okurun yaşamına eklemlenir.\n\n"
            "Bu parçada geçen \"kitaptan taşıp okurun yaşamına eklemlenmek\" "
            "sözüyle anlatılmak istenen düşünce aşağıdaki cümlelerin "
            "hangisinde vardır?"
        ),
        "option_a": (
            "Her şiirde bir önceki şiirinin üstüne çıkmaya çalışan şairleri "
            "okumaktan keyif alırım."
        ),
        "option_b": (
            "Bence her yazar, anlatısına mutlaka özgeçmişinden bir şeyler "
            "eklemelidir."
        ),
        "option_c": (
            "Okuyucunun dünyasını değiştiren ve onu başka yaşamlarla "
            "tanıştıran eserleri okumak isterim."
        ),
        "option_d": (
            "Okuduğum romanlardaki karakterlerin gerçekçi bir biçimde "
            "anlatılıp beni etkilemesini önemserim."
        ),
        "option_e": (
            "Bence hikâyeler, okurun dolduracağı boşluk ve belirsizlikler "
            "barındırmalıdır."
        ),
        "correct_answer": "D",
        "osym_year": None,
    },
    {
        "q_no": 6,
        "page": 15,
        "question_text": (
            "Usta sanatçı, durakları atarak hece ölçüsünde yeni uyumlar aradı. "
            "\"Şairin sorumluluğu ve onuru sesle başlar, sesle biter. Yoksa "
            "sözcüğün tek başına anlamından beklenen güzellik, nesir sınırları "
            "içine girer. Şiir, sonuçta bir sözcük işidir; duygular, fikirler, "
            "buluşlar sonra gelir.\" görüşünü savundu. Türkçenin olanaklarını "
            "kullanmada başarılıydı. Etkili şiirleriyle kendisinden sonra "
            "yetişen kuşaklara yeni söyleyiş ufukları açtı.\n\n"
            "I.   Oktay Rifat'ın orijinal imgelerle şiirimizin anlatım "
            "olanaklarını genişletmesi\n"
            "II.  Ahmet Haşim'in dizelerinde bireysel izlekleri öne çıkarması\n"
            "III. Cahit Zarifoğlu'nun şiirlerinde düş gücünün önemli yer "
            "tutması\n\n"
            "Bu parçada geçen \"yeni söyleyiş ufukları açtı\" ifadesini "
            "yukarıdakilerden hangileri örnekler?"
        ),
        "option_a": "Yalnız II",
        "option_b": "I ve III",
        "option_c": "Yalnız III",
        "option_d": "I ve II",
        "option_e": "Yalnız I",
        "correct_answer": "E",
        "osym_year": None,
    },
    {
        "q_no": 7,
        "page": 15,
        "question_text": (
            "Romancı, yaşamdan aldıklarını dili ustaca kullanarak ve "
            "kurgulamaya başvurarak anlatır. O, tarihçi veya haberci değildir. "
            "Bu ikisi, olanı biteni olduğu gibi ve objektif aktarmaya çalışır "
            "ki doğrusu da budur. Romancının ise böyle bir kaygısı yoktur. "
            "Ayrıca romancı, yaşamı her hâliyle aktarır. Yani romancı, "
            "okuyucusunu okyanusta yüzdürür, hikâyeci gibi havuzda değil.\n\n"
            "Bu parçadaki altı çizili sözle anlatılmak istenen "
            "aşağıdakilerin hangisidir?"
        ),
        "option_a": "Hayatın belli bir kesitini okurla paylaşmak",
        "option_b": (
            "Anlatılanların okurda yaşanmışlık duygusu uyandırmasını sağlamak"
        ),
        "option_c": "Yaşamın bütün gizli kalmış yönlerini açığa çıkarmak",
        "option_d": "Okura hayatın bütün yönlerini anlatmak",
        "option_e": "Toplumun genelini ilgilendirecek konuları ele almak",
        "correct_answer": "D",
        "osym_year": None,
    },
    {
        "q_no": 8,
        "page": 15,
        "question_text": (
            "I.   Öyle şairler tanıdım ki her daim taze ve anlamlı dizeler "
            "kaleme alıyorlardı.\n"
            "II.  Genç bir yazarken bir cümle üzerinde kimi kez yarım saat "
            "düşünürdüm.\n"
            "III. Ferdî konuları ele alan ozanın şiirlerinde sosyal temalar "
            "belli belirsizdi.\n"
            "IV.  Yoğun iş temposuna rağmen zaman zaman tiyatro izlemeye "
            "gidiyordu.\n"
            "V.   Yazarın bu romanı bence olsa olsa iki yüz sayfa ve on bölüm "
            "olmalıydı.\n\n"
            "Yukarıda numaralanmış cümlelerin hangilerinde geçen altı çizili "
            "sözler, anlamca birbirine en yakındır?"
        ),
        "option_a": "I ve II",
        "option_b": "II ve III",
        "option_c": "II ve IV",
        "option_d": "III ve IV",
        "option_e": "IV ve V",
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
            print(f"  Q{q['q_no']:2d}: OK   (id={new_id}, ans={q['correct_answer']}, p={q['page']}, osym={q['osym_year']})")

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

    with open(r"C:\Users\husey\kiro2\insert_345_osym_tadinda_01_sozcukte_anlam_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n=== OZET ===")
    print(f"Inserted: {len(inserted)}")
    print(f"Skipped:  {len(skipped)}")
    print(f"Errors:   {len(errors)}")


if __name__ == "__main__":
    main()
