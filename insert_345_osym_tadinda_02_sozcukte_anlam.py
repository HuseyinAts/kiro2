# -*- coding: utf-8 -*-
"""
KIRO2 - 345 Yayinevi TYT Turkce Soru Bankasi 2025
OSYM Tadinda Sorular 2 = Sayfa 16-17 = SOZCUKTE ANLAM
8 soru INSERT (idempotent, hash dedupe ile)

Cevap anahtari: sayfa 432 zoom screenshot, 1 May 2026 (pixel-dogrulandi)
1.A 2.D 3.D 4.B 5.B 6.A 7.E 8.A

S1: TYT 2023 CIKMIS SORU (kirmizi cerceveli, "OSYM kosesi" etiketli, osym_year=2023)
Diger 7 soru osym_year=null.

Topic: TUR.ANL Anlam Bilgisi (c1350eca-9173-43e7-a6ec-175e42081510)
W4r workflow + kitap-bazli kalibrasyon (sol [480,1100] sag [1000,1750]) ile uretildi.
"""

import json
import hashlib
import re
import psycopg2
from psycopg2.extras import Json
from datetime import datetime, timezone

DB_DSN = "postgresql://postgres:1470@localhost:5434/kiro2"

PRIMARY_TOPIC_ID = "c1350eca-9173-43e7-a6ec-175e42081510"
BOOK_NAME = "345 Yayinevi TYT Turkce Soru Bankasi 2025"
SOURCE_BOOK = "345 Yayinevi TYT Turkce Soru Bankasi 2025"
TEST_NAME = "OSYM Tadinda Sorular 2 - Sozcukte Anlam"
SOURCE_PAGES = "16-17"
ANSWER_KEY_PAGE = "432"

OCR_METHOD = "claude_opus_4_7_v1"
OCR_DATE = "2026-05-01"
MERGE_SOURCE = "claude_opus_4_7_v1"
OCR_SESSION = "2026-05-01_345_tyt_tr_osym_tadinda_02"


QUESTIONS = [
    {
        "q_no": 1,
        "page": 16,
        "question_text": (
            "• açmak: Yakışmak, güzel göstermek.\n"
            "• basamak: Derece, aşama, kerte, evre.\n"
            "• çekmek: Güç durumlara dayanmak, katlanmak.\n\n"
            "Aşağıdaki cümlelerin hangisinde \"açmak, basamak, çekmek\" "
            "sözcükleri belirtilen anlamlarını karşılayacak şekilde "
            "kullanılmıştır?"
        ),
        "option_a": (
            "Başarının basamaklarını tırmanırken pek çok zorluk çeken "
            "öğrenci, kendini açtığına inandığı beyaz elbisesiyle "
            "diplomasını aldı."
        ),
        "option_b": (
            "Çetin kış şartlarının daha çekilebilir olması için evin "
            "basamaklarına döşenen kilimler içimizi açıyordu."
        ),
        "option_c": (
            "Kilitli tahta kapıyı açıp basamaklardan ağır ağır inen kedi, "
            "çıkardığı seslerle tüm dikkatleri üzerine çekti."
        ),
        "option_d": (
            "Rüzgâr, bulutları eteklerinden çekerek havanın açmasını ve "
            "gökyüzünde basamak basamak gökkuşağının oluşmasını sağlamıştı."
        ),
        "option_e": (
            "Okuldan dönen kardeşim, defterini açarak ödevini yapmaya "
            "başlamış ve sayı basamakları konusunda çektiği zorlukların "
            "üstesinden gelmişti."
        ),
        "correct_answer": "A",
        "osym_year": 2023,
    },
    {
        "q_no": 2,
        "page": 16,
        "question_text": (
            "Havanın yağmurlu olduğunu fark ederek evden çıkmadan "
            "şemsiyesini aldı. Caddede bir müddet yürüdükten sonra "
            "boğazında garip bir gıcıklanma hissetmiş olacak ki bir "
            "büfeden su aldı. Parkın yakınındaydı. Bir banka oturarak "
            "suyunu yudum yudum içmeye koyuldu. Bir rüzgâr esmeye başladı "
            "hafif hafif. Yağmur da dinmişti. \"Ah şu rüzgâr bendeki tüm "
            "derdi, elemi alsa... Şöyle kafam ve ruhum rahat bir gün "
            "geçirsem.\" diye iç geçirdi. Suyu bitirmişti. Boş şişeyi "
            "atabileceği bir geri dönüşüm kutusunu aradı gözleri. "
            "Göremeyince elindeki küçük poşete koymayı düşündü şişeyi. "
            "Tam da tahmin ettiği gibi poşet, zar zor da olsa şişeyi aldı.\n\n"
            "Bu parçada \"almak\" sözcüğü aşağıdaki anlamlardan hangisine "
            "karşılık gelecek şekilde kullanılmamıştır?"
        ),
        "option_a": "İçine sığdırmak",
        "option_b": "Yanında bulundurmak",
        "option_c": "Satın almak",
        "option_d": "Yutmak, kullanmak",
        "option_e": "Varlığını sonlandırmak, uzaklaştırmak",
        "correct_answer": "D",
        "osym_year": None,
    },
    {
        "q_no": 3,
        "page": 16,
        "question_text": (
            "1867 senesinde Türkistan Genel Valiliğinin kurulmasından "
            "itibaren Taşkent'te bulunan bölgesel yönetim ile Petersburg "
            "arasında Türkistan'ın idaresi hakkındaki görüş farklılıkları, "
            "Türkistan'da tam teşekküllü bir Rus idari mevzuatının "
            "gelişmesine engel oldu. 1871-1883 yıllarında Taşkent yönetimi "
            "tarafından hazırlanan nizamname tasarılarının Petersburg "
            "tarafından reddedilmesi, Petersburg ve bölgesel yönetim "
            "arasında Türkistan Genel Valiliğinin idari yapısı hakkında "
            "fikir anlaşmazlıklarının olduğunu gösteriyordu.\n\n"
            "I.   Hem Petersburg'un hem de Taşkent'in ekonomik yönden "
            "sorunlar yaşaması\n"
            "II.  Taşkent yönetimince hazırlanan nizamname tasarılarının "
            "Petersburg tarafından reddedilmesi\n"
            "III. Petersburg ile bölgesel yönetimin idari bir meselede "
            "uzlaşamaması\n\n"
            "Bu parçada geçen \"fikir anlaşmazlıklarının olduğunu "
            "göstermek\" ifadesini yukarıdakilerden hangileri destekler?"
        ),
        "option_a": "Yalnız I",
        "option_b": "I ve II",
        "option_c": "Yalnız III",
        "option_d": "II ve III",
        "option_e": "Yalnız II",
        "correct_answer": "D",
        "osym_year": None,
    },
    {
        "q_no": 4,
        "page": 16,
        "question_text": (
            "Günümüzde sanat ve edebiyat iki ayrı koldan akıyor(I) (farklı "
            "engellemelere uğruyor). Bir yanda popüler kültürden beslenen, "
            "halk realitelerine kör(II) (toplumsal gerçekleri göremeyen), "
            "okuyucusuna da sadece kaçış fırsatı sağlayan ticari ve ucuz "
            "faaliyetler(III) (kolaycılığa kaçan çalışmalar) var. Öte "
            "yanda, geçmişi ve geleceği ile bu coğrafyanın gerçeklerinin "
            "ayrımına varmak isteyen(IV) (fark etmeyi arzulayan), toplumun "
            "ve bireylerin gerçek sorunlarını yansıtmak isteyen, gönlünü "
            "edebiyata kaptırmış(V) (edebiyat sevdalısı) bir avuç yazar var.\n\n"
            "Bu parçadaki numaralanmış sözlerden hangisinin anlamı, ayraç "
            "içindeki sözün anlamıyla örtüşmemektedir?"
        ),
        "option_a": "III",
        "option_b": "I",
        "option_c": "V",
        "option_d": "II",
        "option_e": "IV",
        "correct_answer": "B",
        "osym_year": None,
    },
    {
        "q_no": 5,
        "page": 17,
        "question_text": (
            "Eserlerimi bir tabloya benzetecek olursam bu tabloda ferdî "
            "rengimin ağır bastığını söyleyebilirim. Bu, okurlarımın "
            "renklerini hiçe saydığım anlamına gelmiyor elbette. Çünkü "
            "dünya üzerinde sayısız rengin var olduğunun bilincindeyim. "
            "Hatta okur sayısı kadar çok renk olduğunu ve her rengin özgün "
            "güzellikler taşıdığını biliyorum. Ne var ki eserlerinden "
            "kendi bireyselliğinin taşmasını istemek, bir sanatçının en "
            "doğal hakkı. Üstelik ben, bunu çok taşırmadığıma da inanıyorum.\n\n"
            "Bu parçada geçen \"ferdî rengi ağır basmak\" sözünü anlamca "
            "karşılayabilecek bir kullanım aşağıdakilerin hangisinde vardır?"
        ),
        "option_a": (
            "Bireysel temaları işlediği eserlerinde daha başarılıydı."
        ),
        "option_b": (
            "O, eserlerinde kendi his ve fikirlerini öne çıkaran bir "
            "hikâyeciydi."
        ),
        "option_c": (
            "Şiirlerinin yanı sıra öykü ve romanlarında da toplumsallık "
            "belirgindi."
        ),
        "option_d": (
            "Romanlarında kendi düşüncelerini kahramanları aracılığıyla "
            "vermiştir."
        ),
        "option_e": (
            "Realist romancılar, romanlarını öznel bir yaklaşımla kaleme "
            "alırdı."
        ),
        "correct_answer": "B",
        "osym_year": None,
    },
    {
        "q_no": 6,
        "page": 17,
        "question_text": (
            "Edebiyat dergilerini az çok bilirsiniz. Edebiyat ortamını "
            "zenginleştirmesi ve ozanlar ile okurlar arasında bir köprü "
            "vazifesi görmesi bakımından önemlidir edebiyat dergileri. "
            "Kimler geldi kimler geçti o dergilerden? Umut vaat eden nice "
            "genç ozan binbir emekle yazdığı şiirleri yolladı o dergilere. "
            "Yayımlandıktan sonra beğenilenler, el üstünde tutulanlar da "
            "oldu. Ne var ki çoğu şiir, okurda bir karşılık "
            "bulamadığından edebiyat ortamında kaybolup gitti.\n\n"
            "Bu parçada geçen altı çizili sözün cümleye kattığı anlam "
            "aşağıdakilerin hangisinde vardır?"
        ),
        "option_a": (
            "Söz konusu yazar, bunca yıl deneme yazdığı hâlde ne okundu "
            "ne de tanındı."
        ),
        "option_b": (
            "Edebiyatın her türünde eser yazmak için güçlü bir kaleme "
            "sahip olunmalıdır."
        ),
        "option_c": (
            "Bazı yazarlar şiirlerinde imgeli bir anlatımı, düzyazılarında "
            "sadeliği benimserse uzun soluklu olabilir."
        ),
        "option_d": (
            "Bu yazarımız uzun aralıklarla kitap çıkarsa da okurun "
            "gönlünden silinmiyor."
        ),
        "option_e": (
            "Birçok nitelikli eser veren sanatçımızdan uzun süredir ses "
            "seda çıkmıyor."
        ),
        "correct_answer": "A",
        "osym_year": None,
    },
    {
        "q_no": 7,
        "page": 17,
        "question_text": (
            "Edebiyat tarihi incelemeleri bağlamında bir edebiyat tarihi, "
            "en başta aldıkları ve dışarıda bıraktıklarıyla "
            "karakteristiğini bulur. Edebiyat ürünlerini yapısal "
            "özelliklerine, benzeşen ve benzeşmeyen yönlerine göre "
            "kümelendirme çalışmaları Aristo'dan bu yana süregelir.\n\n"
            "I.   Belirgin özelliklerini kazanmak\n"
            "II.  Öncekinin tersi bir kimliğe bürünmek\n"
            "III. Kendi niteliklerine ulaşmak\n\n"
            "Bu parçada geçen \"karakteristiğini bulur\" ifadesine "
            "yukarıdakilerden hangileri uymaktadır?"
        ),
        "option_a": "Yalnız I",
        "option_b": "II ve III",
        "option_c": "I, II ve III",
        "option_d": "I ve II",
        "option_e": "I ve III",
        "correct_answer": "E",
        "osym_year": None,
    },
    {
        "q_no": 8,
        "page": 17,
        "question_text": (
            "Büyük yapıt güncel yapıt mıdır? Bu soruya genellikle "
            "\"Hayır.\" cevabını verdim. \"Evet.\" cevabını verseydim "
            "aramızdan uzun zaman önce ayrılan Shakespeare, Moliere, "
            "Tolstoy gibi ustalara haksızlık etmiş sayılacaktım. Gerçek "
            "şu ki büyük yapıt, güncelin acımasız testeresinin dişlerini "
            "düzleyen yapıttır. Bu tarz yapıtlar okuyucunun ilgisine "
            "mazhar olmuş ve yazarlarının zamana yenik düşmesini "
            "engellemiştir. Gücünü böylesine etkili bir eserden alan "
            "sanatçının edebiyat sahasından silinmesi ve okuyucunun "
            "hafızasından kaybolması pek de olası değildir.\n\n"
            "Yukarıdaki altı çizili sözün parçaya kattığı anlam "
            "aşağıdakilerin hangisinde vardır?"
        ),
        "option_a": (
            "Geleceğe kalacak eser, bugünün yıpratıcı etkisine karşı "
            "koyabilen eserdir."
        ),
        "option_b": (
            "Büyük yapıtlar, güncel konuları güzel bir dille ele alan "
            "eserlerdir."
        ),
        "option_c": (
            "Geçmişteki edebî yapıtları aktüel veriler ışığında okumak "
            "bizi yanıltabilir."
        ),
        "option_d": (
            "Nitelikli bir edebiyat yapıtı geçmişle gelecek arasında "
            "köprü görevi üstlenir."
        ),
        "option_e": (
            "İyi bir yazar, değişime açık olup edebiyatın yenilenen "
            "yüzüne dönüşmelidir."
        ),
        "correct_answer": "A",
        "osym_year": None,
    },
]


def compute_hash(qtext, a, b, c, d, e):
    e_safe = e if e is not None else ""
    payload = qtext.lower().strip() + "|" + a + "|" + b + "|" + c + "|" + d + "|" + e_safe
    return hashlib.md5(payload.encode("utf-8")).hexdigest()


def text_stats(text):
    words = re.findall(r"\w+", text, re.UNICODE)
    word_count = len(words)
    unique = len(set(w.lower() for w in words))
    avg_len = round(sum(len(w) for w in words) / word_count, 2) if word_count else 0.0
    return word_count, unique, avg_len


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

            cur.execute(
                "SELECT id FROM question_bank WHERE soru_hash = %s LIMIT 1",
                (soru_hash,),
            )
            existing = cur.fetchone()
            if existing:
                skipped.append({"q_no": q["q_no"], "reason": "hash_exists",
                                "existing_id": str(existing[0]), "hash": soru_hash})
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
                "workflow": "W4r_kalibre",
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
                    0, 0,
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
                    q["option_a"], q["option_b"], q["option_c"], q["option_d"], q["option_e"],
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
                "q_no": q["q_no"], "id": str(new_id), "hash": soru_hash,
                "answer": q["correct_answer"], "osym_year": q["osym_year"],
                "page": q["page"],
            })
            print(f"  Q{q['q_no']:2d}: OK   (id={new_id}, ans={q['correct_answer']}, p={q['page']}, osym={q['osym_year']})")

        except Exception as e:
            errors.append({"q_no": q["q_no"], "error": str(e)})
            print(f"  Q{q['q_no']:2d}: ERR  {e}")
            conn.rollback()

    if errors:
        conn.rollback()
        print(f"\n{len(errors)} hata, rollback")
    else:
        conn.commit()
        print(f"\nCommit OK")

    cur.close()
    conn.close()

    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "book": BOOK_NAME, "test": TEST_NAME,
        "topic_id": PRIMARY_TOPIC_ID, "topic_name": "TUR.ANL Anlam Bilgisi",
        "answer_key_source": "sayfa 432 zoom (pixel-dogrulandi 1 May 2026)",
        "total_questions": len(QUESTIONS),
        "inserted_count": len(inserted),
        "skipped_count": len(skipped),
        "error_count": len(errors),
        "inserted": inserted, "skipped": skipped, "errors": errors,
    }

    with open(r"C:\Users\husey\kiro2\insert_345_osym_tadinda_02_sozcukte_anlam_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n=== OZET ===")
    print(f"Inserted: {len(inserted)}")
    print(f"Skipped:  {len(skipped)}")
    print(f"Errors:   {len(errors)}")


if __name__ == "__main__":
    main()
