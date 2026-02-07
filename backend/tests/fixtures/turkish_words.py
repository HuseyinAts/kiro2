"""
Turkish word fixtures for testing Zemberek NLP tools.

Contains:
- Common Turkish words
- Dictionary-verified correct words
- Inflected forms with known lemmas
- Test sentences
"""

# Common Turkish words (valid dictionary entries)
TURKISH_WORDS = [
    "kitap", "okumak", "yazmak", "guzel", "buyuk", "kucuk",
    "ev", "araba", "insan", "cocuk", "kadin", "erkek",
    "su", "ekmek", "yemek", "gelmek", "gitmek", "almak",
    "vermek", "bilmek", "istemek", "sevmek", "anlamak",
    "gormek", "duymak", "icmek", "yemek", "uyumak",
    "calismak", "oynamak", "kosmak", "yuzmek", "ucmak",
    "turkce", "ingilizce", "matematik", "fizik", "kimya",
    "tarih", "cografya", "biyoloji", "edebiyat", "felsefe",
    "okul", "universite", "sinif", "ogretmen", "ogrenci",
    "anne", "baba", "kardes", "arkadas", "aile",
    "sehir", "koy", "mahalle", "sokak", "cadde",
    "gun", "ay", "yil", "hafta", "saat", "dakika",
    "sabah", "aksam", "gece", "gunduz", "yarin", "dun",
    "para", "is", "meslek", "sirket", "fabrika", "ofis",
    "telefon", "bilgisayar", "internet", "televizyon",
]

# Dictionary-verified correct words (all should pass spell check)
DICTIONARY_WORDS = [
    "merhaba", "hosgeldiniz", "tesekkurler", "lutfen",
    "gunaydın", "iyi aksamlar", "iyi geceler",
    "evet", "hayir", "belki", "mumkun", "imkansiz",
    "dogru", "yanlis", "guzel", "cirkin", "iyi", "kotu",
    "buyuk", "kucuk", "uzun", "kisa", "genis", "dar",
    "sicak", "soguk", "yeni", "eski", "zor", "kolay",
    "hizli", "yavas", "erken", "gec", "yakın", "uzak",
]

# Inflected forms with known lemmas
INFLECTED_FORMS = {
    # Noun inflections
    "kitaplar": "kitap",
    "kitabi": "kitap",
    "kitapta": "kitap",
    "kitaptan": "kitap",
    "evler": "ev",
    "evde": "ev",
    "evden": "ev",
    "arabalar": "araba",
    "arabasi": "araba",
    "cocuklar": "cocuk",
    "cocuga": "cocuk",
    "insanlar": "insan",
    "insanin": "insan",

    # Verb inflections
    "okuyorum": "okumak",
    "okuduk": "okumak",
    "okuyacak": "okumak",
    "yaziyorum": "yazmak",
    "yazdim": "yazmak",
    "yazacagim": "yazmak",
    "geliyorum": "gelmek",
    "geldim": "gelmek",
    "gelecek": "gelmek",
    "gidiyorum": "gitmek",
    "gittim": "gitmek",
    "gidecek": "gitmek",
    "aliyorum": "almak",
    "aldim": "almak",
    "alacak": "almak",
    "veriyorum": "vermek",
    "verdim": "vermek",
    "verecek": "vermek",
    "biliyorum": "bilmek",
    "bildim": "bilmek",
    "bilecek": "bilmek",
    "seviyorum": "sevmek",
    "sevdim": "sevmek",
    "sevecek": "sevmek",

    # Possessive suffixes
    "kitabim": "kitap",
    "kitabin": "kitap",
    "arkadasim": "arkadas",
    "arkadasin": "arkadas",
    "annem": "anne",
    "babam": "baba",

    # Case + possessive combinations
    "kitabimda": "kitap",
    "evimizde": "ev",
    "okulumuzda": "okul",
}

# Test sentences (Turkish)
TEST_SENTENCES = [
    "Merhaba, nasilsiniz?",
    "Bugun hava cok guzel.",
    "Istanbul Turkiye'nin en buyuk sehridir.",
    "Okula gitmek icin erken kalktim.",
    "Kitap okumak cok faydalidir.",
    "Yarin toplanti yapacagiz.",
    "Bu sorunun cevabi nedir?",
    "Matematik dersini cok seviyorum.",
    "Annem cok guzel yemek yapar.",
    "Tatilde denize gitmek istiyorum.",
]

# Misspelled words with corrections
MISSPELLED_WORDS = {
    "yalniz": "yalnız",
    "sekerli": "şekerli",
    "gormek": "görmek",
    "turkce": "türkçe",
    "ogretmen": "öğretmen",
    "ogrenci": "öğrenci",
    "universite": "üniversite",
    "guzell": "güzel",  # Repeated letter
    "kitaap": "kitap",  # Repeated letter
    "merhba": "merhaba",  # Missing letter
}

# Turkish alphabet for property testing
TURKISH_ALPHABET = "abcçdefgğhıijklmnoöprsştuüvyz"
TURKISH_UPPER_ALPHABET = "ABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ"
TURKISH_FULL_ALPHABET = TURKISH_ALPHABET + TURKISH_UPPER_ALPHABET

# Named entities for NER testing
NAMED_ENTITIES = {
    "PERSON": [
        "Mustafa Kemal Ataturk",
        "Fatih Sultan Mehmet",
        "Mimar Sinan",
        "Dr. Mehmet Oz",
        "Prof. Ali Yilmaz",
    ],
    "LOCATION": [
        "Istanbul",
        "Ankara",
        "Izmir",
        "Turkiye",
        "Karadeniz",
        "Ege Denizi",
        "Taksim Meydani",
    ],
    "ORGANIZATION": [
        "Turkiye Cumhuriyeti",
        "TBMM",
        "Istanbul Universitesi",
        "Turk Telekom",
        "Garanti Bankasi",
    ],
}
