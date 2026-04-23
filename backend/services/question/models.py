"""
Soru Uretim Modelleri ve Sablonlari
REQ-48.33-48.40: Template system, Misconception database

Bu dosya soru uretim modulunun ortak veri yapilarini ve
template/misconception database'lerini icerir.
"""


# OSYM soru yapisi sablonlari
QUESTION_TEMPLATES: dict[str, list[str]] = {
    "matematik": [
        "Asagidaki {konu} problemi icin dogru cozum hangisidir?",
        "{konu} ile ilgili verilen ifadelerden hangisi dogrudur?",
        "Bir {konu} probleminde {durum} olduguna gore, sonuc nedir?",
    ],
    "turkce": [
        "Asagidaki cumlede {konu} acisindan hata var midir?",
        "{konu} ile ilgili asagidaki ifadelerden hangisi yanlisdir?",
        "Verilen metinde {konu} kullanimi nasildir?",
    ],
    "fen": [
        "{konu} ile ilgili asagidaki ifadelerden hangisi dogrudur?",
        "Bir {konu} deneyinde {durum} gozlemlenmistir. Bunun nedeni nedir?",
        "{konu} konusunda verilen bilgilerden hangisi yanlisdir?",
    ],
}


# Turk ogrencilerin sik yaptigi hatalar ve kavram yanilgilari
MISCONCEPTION_DATABASE: dict[str, dict[str, list[str]]] = {
    "matematik": {
        "kesirler": [
            "Paydalari toplamak (1/2 + 1/3 = 2/5 gibi)",
            "Kesir carpiminda payda carpmayi unutmak",
            "Kesir bolmede ters cevirmeyi unutmak",
        ],
        "uslu_sayilar": [
            "Usleri toplamak yerine carpmak (2^3 * 2^2 = 2^6 gibi)",
            "Negatif us ile negatif sayiyi karistirmak",
            "Sifirinci kuvveti sifir sanmak",
        ],
        "denklemler": [
            "Her iki tarafa farkli islem yapmak",
            "Eksi isaretini dagitmayi unutmak",
            "Parantez acarken isaret hatasi",
        ],
    },
    "turkce": {
        "yazim_kurallari": [
            "de/da baglaci ile -de/-da ekini karistirmak",
            "ki baglaci ile -ki ekini karistirmak",
            "Buyuk harf kullaniminda hata",
        ],
        "noktalama": [
            "Virgul yerine nokta kullanmak",
            "Soru isareti yerine nokta kullanmak",
            "Tirnak isareti kullanimi hatasi",
        ],
    },
    "fen": {
        "fizik": [
            "Hiz ile ivmeyi karistirmak",
            "Kutle ile agirligi karistirmak",
            "Kinetik ve potansiyel enerjiyi karistirmak",
        ],
        "kimya": [
            "Atom ile molekulu karistirmak",
            "Fiziksel ve kimyasal degisimi karistirmak",
            "Asit-baz kavramlarini yanlis anlamak",
        ],
    },
}


def get_question_templates(subject: str) -> list[str]:
    """Ders icin soru sablonlarini dondur."""
    subject_key = subject.lower()
    return QUESTION_TEMPLATES.get(subject_key, QUESTION_TEMPLATES["matematik"])


def get_misconceptions(subject: str, topic: str) -> list[str]:
    """Ders ve konu icin kavram yanilgilarini dondur."""
    subject_key = subject.lower()
    topic_key = topic.lower().replace(" ", "_")

    if subject_key in MISCONCEPTION_DATABASE:
        return MISCONCEPTION_DATABASE[subject_key].get(topic_key, [])
    return []
