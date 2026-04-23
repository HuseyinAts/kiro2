"""
YKS Test Questions - Konu Bazli Subagent Test Verileri
Task 17: Integration Testing

6 domain icin gercek YKS tarzinda sorular:
- matematik: Cebir, Geometri, Analiz, Olasilik
- fizik: Mekanik, Elektrik, Optik, Termodinamik
- turkce: Dilbilgisi, Edebiyat, Anlam Bilgisi
- sosyal: Tarih, Cografya, Felsefe
- biyoloji: Hucre, Genetik, Ekoloji
- yabanci_dil: Grammar, Vocabulary, Reading
"""

from dataclasses import dataclass


@dataclass
class TestQuestion:
    """Test sorusu veri yapisi"""

    question_id: str
    domain: str
    subdomain: str
    question_text: str
    expected_keywords: list[str]  # Yanitte beklenen anahtar kelimeler
    difficulty: str  # kolay, orta, zor
    is_multi_domain: bool = False
    secondary_domain: str | None = None


# Matematik Sorulari (REQ-1)
MATEMATIK_QUESTIONS: list[TestQuestion] = [
    TestQuestion(
        question_id="mat_cebir_001",
        domain="matematik",
        subdomain="cebir",
        question_text="2x + 3 = 7 denklemini cozunuz.",
        expected_keywords=["x = 2", "denklem", "cozum"],
        difficulty="kolay",
    ),
    TestQuestion(
        question_id="mat_cebir_002",
        domain="matematik",
        subdomain="cebir",
        question_text="x^2 - 5x + 6 = 0 ikinci dereceden denkleminin koklerini bulunuz.",
        expected_keywords=["x = 2", "x = 3", "kok", "delta"],
        difficulty="orta",
    ),
    TestQuestion(
        question_id="mat_geometri_001",
        domain="matematik",
        subdomain="geometri",
        question_text="Bir ucgenin iki kenari 5 cm ve 7 cm, aralarindaki aci 60 derece ise ucgenin alani kac cm2 dir?",
        expected_keywords=["alan", "sinüs", "formul", "cm2"],
        difficulty="orta",
    ),
    TestQuestion(
        question_id="mat_geometri_002",
        domain="matematik",
        subdomain="geometri",
        question_text="Yaricapi 4 cm olan bir cemberin cevresi kac cm dir?",
        expected_keywords=["cevre", "2*pi*r", "25.13", "cm"],
        difficulty="kolay",
    ),
    TestQuestion(
        question_id="mat_analiz_001",
        domain="matematik",
        subdomain="analiz",
        question_text="f(x) = x^3 - 3x^2 + 2x fonksiyonunun turevini bulunuz.",
        expected_keywords=["turev", "3x^2", "-6x", "+2"],
        difficulty="orta",
    ),
    TestQuestion(
        question_id="mat_analiz_002",
        domain="matematik",
        subdomain="analiz",
        question_text="Integral(x^2 dx) belirsiz integralini hesaplayiniz.",
        expected_keywords=["integral", "x^3/3", "+C"],
        difficulty="orta",
    ),
    TestQuestion(
        question_id="mat_olasilik_001",
        domain="matematik",
        subdomain="olasilik",
        question_text="Bir zar iki kez atiliyor. Toplamin 8'den buyuk olma olasiligi nedir?",
        expected_keywords=["olasilik", "sonuc", "10/36", "toplam"],
        difficulty="zor",
    ),
]

# Fizik Sorulari (REQ-2)
FIZIK_QUESTIONS: list[TestQuestion] = [
    TestQuestion(
        question_id="fiz_mekanik_001",
        domain="fizik",
        subdomain="mekanik",
        question_text="2 kg kutleye 10 N kuvvet uygulanirsa ivme kac m/s2 olur?",
        expected_keywords=["F=ma", "a = 5", "m/s2", "Newton"],
        difficulty="kolay",
    ),
    TestQuestion(
        question_id="fiz_mekanik_002",
        domain="fizik",
        subdomain="mekanik",
        question_text="5 m/s hizla hareket eden 4 kg kutleli bir cismin kinetik enerjisi nedir?",
        expected_keywords=["Ek = 1/2 * m * v^2", "50", "joule"],
        difficulty="orta",
    ),
    TestQuestion(
        question_id="fiz_elektrik_001",
        domain="fizik",
        subdomain="elektrik",
        question_text="5 ohm direncten 2 A akim gecerse potansiyel fark kac volt olur?",
        expected_keywords=["V = I * R", "10", "volt", "Ohm"],
        difficulty="kolay",
    ),
    TestQuestion(
        question_id="fiz_elektrik_002",
        domain="fizik",
        subdomain="elektrik",
        question_text="Seri bagli 3 ohm ve 6 ohm direncler uzerindeki toplam direnc nedir?",
        expected_keywords=["seri", "toplam", "9", "ohm"],
        difficulty="kolay",
    ),
    TestQuestion(
        question_id="fiz_optik_001",
        domain="fizik",
        subdomain="optik",
        question_text="Odak uzakligi 10 cm olan yakinlastirici mercege 30 cm uzakliktan duran cismin goruntusu nereden olusur?",
        expected_keywords=["mercek", "1/f = 1/d + 1/d'", "goruntu", "cm"],
        difficulty="zor",
    ),
    TestQuestion(
        question_id="fiz_termo_001",
        domain="fizik",
        subdomain="termodinamik",
        question_text="300 K sicaklikta 2 mol ideal gazin ic enerjisi nedir? (R = 8.314 J/mol.K)",
        expected_keywords=["U = 3/2 * n * R * T", "enerji", "joule"],
        difficulty="orta",
    ),
]

# Turkce Sorulari (REQ-3)
TURKCE_QUESTIONS: list[TestQuestion] = [
    TestQuestion(
        question_id="tur_dilbilgisi_001",
        domain="turkce",
        subdomain="dilbilgisi",
        question_text="'Kitap okumak, insani gelistirir.' cumlesindeki ek eylemi bulunuz.",
        expected_keywords=["ek eylem", "fiilimsi", "-mAk", "isim-fiil"],
        difficulty="orta",
    ),
    TestQuestion(
        question_id="tur_dilbilgisi_002",
        domain="turkce",
        subdomain="dilbilgisi",
        question_text="'Guzel bir gun basladi.' cumlesinde sifat olan kelimeyi belirleyiniz.",
        expected_keywords=["sifat", "guzel", "niteleme"],
        difficulty="kolay",
    ),
    TestQuestion(
        question_id="tur_edebiyat_001",
        domain="turkce",
        subdomain="edebiyat",
        question_text="Namik Kemal'in eserleri hangi edebi akima aittir ve ozellikleri nelerdir?",
        expected_keywords=["Tanzimat", "vatan", "hurriyet", "tiyatro", "Intibah"],
        difficulty="orta",
    ),
    TestQuestion(
        question_id="tur_edebiyat_002",
        domain="turkce",
        subdomain="edebiyat",
        question_text="Divan edebiyatinda 'gazel' nazim biciminin ozelliklerini aciklayiniz.",
        expected_keywords=["gazel", "beyit", "kafiye", "matla", "makta"],
        difficulty="orta",
    ),
    TestQuestion(
        question_id="tur_anlam_001",
        domain="turkce",
        subdomain="anlam_bilgisi",
        question_text="'Goz' sozcugunun mecaz anlami ile kullanildigi bir cumle yaziniz.",
        expected_keywords=["mecaz", "goz", "anlam", "igne gozunden"],
        difficulty="orta",
    ),
    TestQuestion(
        question_id="tur_anlam_002",
        domain="turkce",
        subdomain="anlam_bilgisi",
        question_text="'El' sozcugundeki anlam genislemesini orneklerle aciklayiniz.",
        expected_keywords=["anlam genislemesi", "el", "yabanci", "yardim"],
        difficulty="zor",
    ),
]

# Sosyal Bilimler Sorulari (REQ-4)
SOSYAL_QUESTIONS: list[TestQuestion] = [
    TestQuestion(
        question_id="sos_tarih_001",
        domain="sosyal",
        subdomain="tarih",
        question_text="Kurtuluş Savaşı'nın temel aşamalarını kronolojik olarak sıralayınız.",
        expected_keywords=["Kuva-yi Milliye", "TBMM", "Sakarya", "Buyuk Taarruz"],
        difficulty="orta",
    ),
    TestQuestion(
        question_id="sos_tarih_002",
        domain="sosyal",
        subdomain="tarih",
        question_text="Osmanlı Devleti'nin gerileme donemine girmesinin nedenleri nelerdir?",
        expected_keywords=["gerileme", "islahat", "kapitulasyon", "savas"],
        difficulty="zor",
    ),
    TestQuestion(
        question_id="sos_cografya_001",
        domain="sosyal",
        subdomain="cografya",
        question_text="Turkiye'nin iklim cesitliliginin nedenlerini aciklayiniz.",
        expected_keywords=["iklim", "enlem", "yukseklik", "deniz", "karasal"],
        difficulty="orta",
    ),
    TestQuestion(
        question_id="sos_cografya_002",
        domain="sosyal",
        subdomain="cografya",
        question_text="Akdeniz ikliminin genel ozellikleri nelerdir?",
        expected_keywords=["Akdeniz", "yaz", "kurak", "kis", "yagisli"],
        difficulty="kolay",
    ),
    TestQuestion(
        question_id="sos_felsefe_001",
        domain="sosyal",
        subdomain="felsefe",
        question_text="Platon'un idea teorisini aciklayiniz.",
        expected_keywords=["Platon", "idea", "gerceklik", "magaranin"],
        difficulty="zor",
    ),
    TestQuestion(
        question_id="sos_felsefe_002",
        domain="sosyal",
        subdomain="felsefe",
        question_text="Epistemoloji (bilgi teorisi) nedir ve temel sorulari nelerdir?",
        expected_keywords=["epistemoloji", "bilgi", "dogruluk", "kaynak"],
        difficulty="orta",
    ),
]

# Biyoloji Sorulari (REQ-5)
BIYOLOJI_QUESTIONS: list[TestQuestion] = [
    TestQuestion(
        question_id="bio_hucre_001",
        domain="biyoloji",
        subdomain="hucre",
        question_text="Mitokondri'nin hucredeki gorevi nedir?",
        expected_keywords=["mitokondri", "ATP", "enerji", "solinum"],
        difficulty="kolay",
    ),
    TestQuestion(
        question_id="bio_hucre_002",
        domain="biyoloji",
        subdomain="hucre",
        question_text="Hayvan hucresi ile bitki hucresi arasindaki farklari aciklayiniz.",
        expected_keywords=["hucre", "duvar", "kloroplast", "vakuol"],
        difficulty="orta",
    ),
    TestQuestion(
        question_id="bio_genetik_001",
        domain="biyoloji",
        subdomain="genetik",
        question_text="Aa x Aa caprazlamasinda fenotip oranini bulunuz.",
        expected_keywords=["Punnett", "3:1", "dominant", "resesif"],
        difficulty="orta",
    ),
    TestQuestion(
        question_id="bio_genetik_002",
        domain="biyoloji",
        subdomain="genetik",
        question_text="DNA replikasyonu hangi adimlarda gerceklesir?",
        expected_keywords=["replikasyon", "helikaz", "primaz", "polimeraz"],
        difficulty="zor",
    ),
    TestQuestion(
        question_id="bio_ekoloji_001",
        domain="biyoloji",
        subdomain="ekoloji",
        question_text="Besin zinciri ve besin agi arasindaki farki aciklayiniz.",
        expected_keywords=["besin", "zincir", "ag", "enerji", "tuketici"],
        difficulty="orta",
    ),
    TestQuestion(
        question_id="bio_ekoloji_002",
        domain="biyoloji",
        subdomain="ekoloji",
        question_text="Ekosistemde enerji akisi nasil gerceklesir?",
        expected_keywords=["enerji", "uretici", "tuketici", "ayristirici"],
        difficulty="orta",
    ),
]

# Yabanci Dil Sorulari (REQ-6)
YABANCI_DIL_QUESTIONS: list[TestQuestion] = [
    TestQuestion(
        question_id="eng_grammar_001",
        domain="yabanci_dil",
        subdomain="grammar",
        question_text="Complete the sentence: 'If I ___ (know) the answer, I would tell you.'",
        expected_keywords=["knew", "conditional", "second", "past"],
        difficulty="orta",
    ),
    TestQuestion(
        question_id="eng_grammar_002",
        domain="yabanci_dil",
        subdomain="grammar",
        question_text="What is the difference between 'present perfect' and 'past simple' tenses?",
        expected_keywords=["present perfect", "past simple", "have", "finished"],
        difficulty="orta",
    ),
    TestQuestion(
        question_id="eng_vocab_001",
        domain="yabanci_dil",
        subdomain="vocabulary",
        question_text="What does 'ubiquitous' mean? Give an example sentence.",
        expected_keywords=["ubiquitous", "everywhere", "common", "present"],
        difficulty="zor",
    ),
    TestQuestion(
        question_id="eng_vocab_002",
        domain="yabanci_dil",
        subdomain="vocabulary",
        question_text="Give 3 synonyms for the word 'happy'.",
        expected_keywords=["happy", "joyful", "glad", "pleased", "content"],
        difficulty="kolay",
    ),
    TestQuestion(
        question_id="eng_reading_001",
        domain="yabanci_dil",
        subdomain="reading",
        question_text="What strategies can be used to find the main idea of a paragraph?",
        expected_keywords=["main idea", "topic sentence", "context", "summary"],
        difficulty="orta",
    ),
    TestQuestion(
        question_id="eng_reading_002",
        domain="yabanci_dil",
        subdomain="reading",
        question_text="How can you infer the meaning of an unknown word from context?",
        expected_keywords=["context", "clues", "surrounding", "infer"],
        difficulty="orta",
    ),
]

# Multi-Domain Sorular (REQ-7.5)
MULTI_DOMAIN_QUESTIONS: list[TestQuestion] = [
    TestQuestion(
        question_id="multi_mat_fiz_001",
        domain="matematik",
        subdomain="analiz",
        question_text="Newton'un hareket yasalari ve turev iliskisini aciklayiniz. Hiz fonksiyonunun turevi ivmeyi nasil verir?",
        expected_keywords=["Newton", "F=ma", "turev", "hiz", "ivme"],
        difficulty="zor",
        is_multi_domain=True,
        secondary_domain="fizik",
    ),
    TestQuestion(
        question_id="multi_tur_sos_001",
        domain="turkce",
        subdomain="edebiyat",
        question_text="Tanzimat donemi edebiyatinin ortaya cikisinda Osmanli Devleti'ndeki siyasi gelismelerin etkisini inceleyiniz.",
        expected_keywords=["Tanzimat", "Gulhane", "Batililasma", "edebiyat"],
        difficulty="zor",
        is_multi_domain=True,
        secondary_domain="sosyal",
    ),
    TestQuestion(
        question_id="multi_bio_fiz_001",
        domain="biyoloji",
        subdomain="hucre",
        question_text="Hucre zarindan madde gecisinde osmoz ve difuzyonun fiziksel prensiplerini aciklayiniz.",
        expected_keywords=["osmoz", "difuzyon", "konsantrasyon", "zar"],
        difficulty="zor",
        is_multi_domain=True,
        secondary_domain="fizik",
    ),
]

# Tum sorulari domain'e gore grupla
ALL_QUESTIONS: dict[str, list[TestQuestion]] = {
    "matematik": MATEMATIK_QUESTIONS,
    "fizik": FIZIK_QUESTIONS,
    "turkce": TURKCE_QUESTIONS,
    "sosyal": SOSYAL_QUESTIONS,
    "biyoloji": BIYOLOJI_QUESTIONS,
    "yabanci_dil": YABANCI_DIL_QUESTIONS,
}

# Domain-specific keywords for contamination detection
DOMAIN_SPECIFIC_KEYWORDS: dict[str, list[str]] = {
    "matematik": [
        "denklem",
        "turev",
        "integral",
        "fonksiyon",
        "polinom",
        "geometri",
        "ucgen",
        "cember",
        "olasilik",
        "permutasyon",
        "kombinasyon",
        "sinüs",
        "kosinüs",
        "logaritma",
        "uslu",
    ],
    "fizik": [
        "kuvvet",
        "ivme",
        "hiz",
        "enerji",
        "momentum",
        "elektrik",
        "akim",
        "gerilim",
        "direnc",
        "optik",
        "mercek",
        "ayna",
        "dalga",
        "frekans",
        "termodinamik",
    ],
    "turkce": [
        "fiil",
        "isim",
        "sifat",
        "zamir",
        "zarf",
        "cumle",
        "ozne",
        "yuklem",
        "nesne",
        "ekleme",
        "turetme",
        "edat",
        "baglac",
        "edebiyat",
        "siir",
    ],
    "sosyal": [
        "tarih",
        "savas",
        "antlasma",
        "medeniyet",
        "cografya",
        "iklim",
        "bolge",
        "nufus",
        "felsefe",
        "etik",
        "estetik",
        "mantik",
        "ontoloji",
    ],
    "biyoloji": [
        "hucre",
        "mitokondri",
        "ribozom",
        "DNA",
        "RNA",
        "gen",
        "kromozom",
        "protein",
        "enzim",
        "hormon",
        "organ",
        "sistem",
        "metabolizma",
        "ekoloji",
    ],
    "yabanci_dil": [
        "tense",
        "verb",
        "noun",
        "adjective",
        "adverb",
        "grammar",
        "vocabulary",
        "sentence",
        "clause",
        "phrase",
        "conditional",
        "passive",
        "perfect",
    ],
}


def get_questions_by_domain(domain: str) -> list[TestQuestion]:
    """Belirli domain icin sorulari dondur"""
    return ALL_QUESTIONS.get(domain, [])


def get_all_single_domain_questions() -> list[TestQuestion]:
    """Tum tek-domain sorularini dondur"""
    questions = []
    for domain_questions in ALL_QUESTIONS.values():
        questions.extend(domain_questions)
    return questions


def get_multi_domain_questions() -> list[TestQuestion]:
    """Multi-domain sorularini dondur"""
    return MULTI_DOMAIN_QUESTIONS


def get_domain_keywords(domain: str) -> list[str]:
    """Domain-specific anahtar kelimeleri dondur"""
    return DOMAIN_SPECIFIC_KEYWORDS.get(domain, [])


def calculate_contamination_rate(
    response_text: str, expected_domain: str
) -> float:
    """
    Cross-domain contamination oranini hesapla.

    Args:
        response_text: Agent yaniti
        expected_domain: Beklenen domain

    Returns:
        Contamination orani [0, 1]
    """
    response_lower = response_text.lower()
    total_foreign_keywords = 0
    total_keywords_found = 0

    for domain, keywords in DOMAIN_SPECIFIC_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in response_lower:
                total_keywords_found += 1
                if domain != expected_domain:
                    total_foreign_keywords += 1

    if total_keywords_found == 0:
        return 0.0

    return total_foreign_keywords / total_keywords_found
