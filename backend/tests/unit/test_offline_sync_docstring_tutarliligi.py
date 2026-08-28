"""Docstring'in VAAT ETTIGI yazim, kodda GERCEKTEN olmali.

NEDEN BU BEKCI VAR (23 Agu 2026, S249/I5 -- kutuk X11 2. kol)
------------------------------------------------------------
`process_sync_results` docstring'i "student-answers tablosuna kayit ekler"
diye bir vaat tasiyordu. Olculdu: o ORM sembolu bu modulde SIFIR kez geciyordu
ve `git log -S` hic gecmedigini gosteriyor. Tek yazim `db.add(card)` (FSRS
karti). Yani uc `synced_count: 1` donerken ogrencinin cevabini cope atiyordu.

Kutuk X11 birebir "IKI AYRI FIX" diyordu ve "(1) kapali oldugu icin (2)
tetiklenemez" notu dusuyordu. S248'in rebuild'i (1)'i acti -> (2) ULASILABILIR
bir kod yoluna dondu. Karar C uygulandi: ozellik YAZILMADI (tuketici yok,
exam_session_id NOT NULL sentetik-oturum tasarim karari acar, canli istemci
zaten /api/v1/sync/* kullaniyor), docstring koda uyduruldu.

BU TEST NEYI CIVILIYOR
----------------------
Vaadin geri gelmesini. Biri docstring'e yeniden "yazar" der ama yazimi
eklemezse test duser. Tersi de gecerli: yazim GERCEKTEN eklenirse vaat serbest
kalir -- yani bu bir ozellik yasagi degil, TUTARLILIK kapisi.

🔴 KENDI KUSURUM (mutasyon yakaladi, S249)
------------------------------------------
Ilk surum yazimi HAM METINDE ariyordu. Ama duzeltilmis docstring'in kendisi o
ORM sembolunu ANLATIYOR ("... appears zero times in this module"), dolayisiyla
dedektor yazimin VAR oldugunu saniyordu ve M1 mutasyonu (vaadi geri koy)
HAYATTA KALDI -- olu bekci commit'lenecekti.

Ayni tuzak bu oturumda UC kez isirdi: (1) I2 bekcisi docstring'i tanim sandi,
(2) I5 docstring'i eski yalani ALINTILAYINCA `grep` yine 1 donuyordu,
(3) burada. `audit-methodology.md`: "Bir deseni ANLATAN yorum, o deseni ICERIR."

FIX: VAAT proza'da aranir (vaatler zaten orada yasar), YAZIM ise YALNIZ KODDA
(yorum/docstring atilmis metinde) aranir. Iki taraf farkli metinlere bakar.
"""

from __future__ import annotations

import ast
import io
import re
import tokenize
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]

MODUL = Path(__file__).resolve().parents[2] / "services" / "offline_sync_service.py"

# Docstring/yorumda "student_answers'a yazar/ekler" anlamina gelen ifadeler.
# Turkce ve Ingilizce; kelime araligi genis tutuldu ki yeniden ifade edilse de
# yakalansin.
_VAAT = re.compile(
    r"(insert|inserts|inserting|writes?|persists?|kayit ekler|yazar|kaydeder)"
    r"[^.\n]{0,80}student[_ ]answers",
    re.IGNORECASE,
)

# Gercek yazimin imzasi: ORM sembolu ya da ham INSERT. YALNIZ KODDA aranir.
_YAZIM = re.compile(r"StudentAnswer|INSERT\s+INTO\s+student_answers", re.IGNORECASE)

# OLUMSUZLAMA. Bu bekci ilk surumunde KENDI docstring'imin "NOT PERSISTED:
# student answers" basligini VAAT sandi: regex "PERSISTED"i gordu, onundeki
# "NOT"u gormedi. `audit-methodology.md`: "Pozitif kanit ara" -- bir vaadi
# ararken olumsuzlanmis hali VAAT DEGILDIR.
_OLUMSUZ = re.compile(
    r"\b(not|never|no longer|does not|doesn't|isn't|degil|değil|yazmaz|eklenmez|"
    r"kalicilasmaz)\b",
    re.IGNORECASE,
)


def _vaat_bul(metin: str) -> re.Match[str] | None:
    """Olumsuzlanmamis ilk vaadi dondurur.

    Eslesmeden onceki 60 karakterde bir olumsuzlama varsa o eslesme vaat
    sayilmaz -- "NOT PERSISTED: student answers" bir vaat degil, tam tersi.
    """
    for eslesme in _VAAT.finditer(metin):
        onceki = metin[max(0, eslesme.start() - 60) : eslesme.start()]
        # Eslesmenin kendi basi da olumsuzlama tasiyabilir ("NOT PERSISTED")
        if _OLUMSUZ.search(onceki + eslesme.group(0)):
            continue
        return eslesme
    return None


def _kaynak() -> str:
    return MODUL.read_text(encoding="utf-8", errors="replace")


def _yalniz_kod(metin: str) -> str:
    """Yorum ve docstring'leri atar; geriye YALNIZ kod kalir.

    Ayristirma patlarsa ham metin doner -- korlesme testi bunu yakalar.
    """
    try:
        belirtecler = [
            t
            for t in tokenize.generate_tokens(io.StringIO(metin).readline)
            if t.type != tokenize.COMMENT
        ]
        kod = tokenize.untokenize(belirtecler)
        agac = ast.parse(kod)
    except (SyntaxError, tokenize.TokenError, IndentationError):
        return metin

    for dugum in ast.walk(agac):
        if isinstance(
            dugum, ast.Module | ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
        ):
            belge = ast.get_docstring(dugum, clean=False)
            if belge:
                kod = kod.replace(belge, "")
    return kod


def test_korlesme_modul_bulunuyor_ve_bos_degil():
    """Bu assert olmadan asagidaki denetim BOS metin uzerinde gecerdi."""
    assert MODUL.is_file(), f"modul yok: {MODUL}"
    metin = _kaynak()
    assert len(metin) > 5_000, (
        f"modul beklenenden kucuk ({len(metin)} karakter) -- yanlis yol veya "
        "kesik okuma. ALET ARIZASI."
    )


def test_korlesme_desenler_bilinen_ornegi_yakaliyor():
    """Dedektorler calisiyor mu? Sentetik bozma ile dogrula (yanlis-SIFIR bekcisi)."""
    assert _VAAT.search("Inserts a record into student_answers (synthetic)")
    assert _YAZIM.search("db.add(StudentAnswer(...))")
    assert _YAZIM.search("INSERT INTO student_answers (id) VALUES (:id)")
    # Ilgisiz metinde ATESLENMEMELI:
    assert _VAAT.search("Updates FSRS card scheduling.") is None
    assert _YAZIM.search("db.add(card)") is None
    # OLUMSUZLAMA: tersini soyleyen cumle VAAT DEGILDIR (kendi basligim buydu)
    assert _vaat_bul("NOT PERSISTED: student answers") is None
    assert _vaat_bul("Answers are NOT persisted to student_answers.") is None
    assert _vaat_bul("student_answers'a kayit eklenmez") is None
    # Ama gercek vaat YAKALANMALI (kontrol kolu):
    assert _vaat_bul("Inserts a record into student_answers.") is not None


def test_korlesme_kod_ayiklama_prozayi_gercekten_atiyor():
    """`_yalniz_kod` docstring'i atmiyorsa asil denetim ANLAMSIZDIR.

    Bu testin varlik sebebi: ilk surum bu ayiklamayi YAPMIYORDU ve
    duzeltilmis docstring'in kendisi ORM sembolunu anlattigi icin bekci
    olmustu (M1 mutasyonu hayatta kaldi).
    """
    ornek = '"""Bir docstring: StudentAnswer diye bir sey anlatiyor."""\nx = 1\n'
    kod = _yalniz_kod(ornek)
    assert _YAZIM.search(ornek), "kontrol kolu: desen ham metinde eslesmeliydi"
    assert not _YAZIM.search(
        kod
    ), "docstring atilmadi -- `_yalniz_kod` calismyor, denetim guvenilmez"
    # Ve GERCEK kod ayiklamadan SAG cikmali:
    assert _YAZIM.search(_yalniz_kod("db.add(StudentAnswer())\n"))


def test_vaat_edilen_yazim_kodda_gercekten_var():
    """Docstring student_answers yazimi VAAT ediyorsa KOD onu YAPMALI."""
    metin = _kaynak()
    vaat = _vaat_bul(metin)
    yazim = _YAZIM.search(_yalniz_kod(metin))  # <-- YALNIZ KOD, proza degil

    assert not (vaat and not yazim), (
        "Docstring student_answers'a yazim VAAT ediyor ama KODDA o yazim YOK.\n"
        f"  vaat  : {vaat.group(0)[:120] if vaat else None}\n"
        "  yazim : bulunamadi (ne ORM sembolu ne ham INSERT)\n"
        "23 Agu 2026'da tam bu durum olculdu (kutuk X11, 2. kol): uc "
        "synced_count: 1 donerken ogrencinin cevabi HIC kalicilasmiyordu.\n"
        "Yazimi ekliyorsaniz exam_session_id NOT NULL kisitini ve "
        "/api/v1/sync/* ile cift-yazim riskini once cozun."
    )
