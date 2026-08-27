"""save_answer UPSERT parite bekcisi -- AST tabanli, DB GEREKTIRMEZ.

Kusur (K2): ``core/osym_exam_engine.py::save_answer`` icinde IKI ayri
``on_conflict_do_update`` dali var ve ikisi FARKLI SOZLESME yaziyordu:

* uretim dali  -> ``_db_worker`` (toplu/batch UPSERT, TESTING kapaliyken)
* senkron dal  -> ``_sync_save`` (yalniz ``TESTING=true`` iken kosar)

Senkron dalin ``set_`` sozlugu ``is_correct`` anahtarini ICERIYORDU, uretim
dalininki ICERMIYORDU. Sonuc: ogrenci cevabini DEGISTIRDIGINDE (conflict yolu)
uretimde ``student_answers.is_correct`` eski degerinde kalir -- yeniden
derecelendirilmez. Mevcut testlerin tamami ``TESTING=true`` ile kostugu icin
bu farki YAPISAL OLARAK goremez.

Bu bekci METIN ARAMASI DEGIL **AST** kullanir. Sebep: bu docstring'in kendisi
``is_correct`` kelimesini iceriyor; bir metin dedektoru onu kod sanardi ve
kusur giderilmese bile YESIL kalirdi. Bkz. ``.claude/rules/audit-methodology.md``
-- "bir deseni ANLATAN yorum, o deseni ICERIR".
"""

from __future__ import annotations

import ast
from pathlib import Path

ENGINE_PATH = Path(__file__).resolve().parents[2] / "core" / "osym_exam_engine.py"

# Senkron dalin bugun yazdigi, yuk tasiyan anahtarlar. Kontrol kolu icin:
# pariteyi "sync dalindan anahtar silerek" saglamak sayilmaz.
SYNC_ZORUNLU_ANAHTARLAR = frozenset(
    {
        "selected_answer",
        "response_time_seconds",
        "is_correct",
        "answered_at",
        "answer_changes",
    }
)


def _save_answer_dugumu() -> ast.AST:
    """``save_answer`` tanimini AST'den cikar (tekil olmasi sart)."""
    kaynak = ENGINE_PATH.read_bytes().decode("utf-8")
    agac = ast.parse(kaynak)
    adaylar = [
        n
        for n in ast.walk(agac)
        if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)
        and n.name == "save_answer"
    ]
    assert len(adaylar) == 1, f"save_answer tanimi beklendi=1 bulundu={len(adaylar)}"
    return adaylar[0]


def _ic_fonksiyon(kapsam: ast.AST, ad: str) -> ast.AST:
    for n in ast.walk(kapsam):
        if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef) and n.name == ad:
            return n
    raise AssertionError(f"ic fonksiyon bulunamadi: {ad}")


def _upsert_set_anahtarlari(kapsam: ast.AST) -> list[tuple[int, frozenset[str]]]:
    """Kapsamdaki her ``on_conflict_do_update`` cagrisinin ``set_`` anahtarlari.

    Donen: [(satir_no, anahtar_kumesi), ...]
    """
    bulunan: list[tuple[int, frozenset[str]]] = []
    for dugum in ast.walk(kapsam):
        if not isinstance(dugum, ast.Call):
            continue
        f = dugum.func
        if not (isinstance(f, ast.Attribute) and f.attr == "on_conflict_do_update"):
            continue
        set_kw = next((k for k in dugum.keywords if k.arg == "set_"), None)
        assert (
            set_kw is not None
        ), f"satir {dugum.lineno}: on_conflict_do_update cagrisinda set_ kwarg yok"
        assert isinstance(
            set_kw.value, ast.Dict
        ), f"satir {dugum.lineno}: set_ bir dict literal degil, AST ile okunamaz"
        anahtarlar = set()
        for k in set_kw.value.keys:
            assert isinstance(k, ast.Constant) and isinstance(
                k.value, str
            ), f"satir {dugum.lineno}: set_ icinde sabit-olmayan anahtar var"
            anahtarlar.add(k.value)
        bulunan.append((dugum.lineno, frozenset(anahtarlar)))
    return bulunan


def test_alet_dogrulamasi_iki_upsert_dali_bulunuyor() -> None:
    """ALET DOGRULAMASI: kusurun premisi (iki ayri UPSERT dali) hala gecerli mi?

    Bu test duserse parite testinin olctugu sey ortadan kalkmis demektir
    (dallar birlestirilmis veya AST desenimiz bayatlamis). O durumda parite
    testi BOS KUMEYLE gecer -- yanlis-yesil. Once burasi cakilir.
    """
    save_answer = _save_answer_dugumu()
    bulunan = _upsert_set_anahtarlari(save_answer)

    assert len(bulunan) == 2, (
        "save_answer icinde 2 on_conflict_do_update bekleniyordu, "
        f"bulunan={len(bulunan)} (satirlar={[s for s, _ in bulunan]})"
    )
    for satir, anahtarlar in bulunan:
        assert (
            anahtarlar
        ), f"satir {satir}: set_ bos -- UPSERT hicbir kolonu guncellemiyor"


def test_uretim_upsert_seti_senkron_dali_kapsiyor() -> None:
    """Uretim dalinin set_ kumesi, senkron dalinkini KAPSAMALI (superset).

    Neden ``==`` degil ``issuperset``: uretim dali toplu/batch yol oldugu icin
    ileride yalniz orada anlamli bir anahtar (or. batch'e ozgu bir sayac)
    eklenebilir. ``==`` boyle mesru bir eklemede yanlis-kirmizi verir.
    Bizi ilgilendiren tek yon: senkron dalda (testlerin kostugu dalda)
    guncellenen HER kolon uretimde de guncellenmeli -- aksi halde testler
    uretimde olmayan bir davranisi dogruluyor olur.
    """
    save_answer = _save_answer_dugumu()
    uretim = _upsert_set_anahtarlari(_ic_fonksiyon(save_answer, "_db_worker"))
    senkron = _upsert_set_anahtarlari(_ic_fonksiyon(save_answer, "_sync_save"))

    assert len(uretim) == 1, f"_db_worker icinde 1 UPSERT bekleniyordu: {uretim}"
    assert len(senkron) == 1, f"_sync_save icinde 1 UPSERT bekleniyordu: {senkron}"

    uretim_satir, uretim_anahtarlar = uretim[0]
    _, senkron_anahtarlar = senkron[0]

    eksik = senkron_anahtarlar - uretim_anahtarlar
    assert uretim_anahtarlar.issuperset(senkron_anahtarlar), (
        f"uretim UPSERT'i (satir {uretim_satir}) su anahtarlari GUNCELLEMIYOR: "
        f"{sorted(eksik)} -- senkron dal guncelliyor. Iki dal ayni sozlesmeyi "
        "yazmali, yoksa TESTING dalini kosan testler kusuru goremez."
    )


def test_kontrol_kolu_senkron_dal_hala_yuk_tasiyor() -> None:
    """KONTROL KOLU: pariteyi senkron daldan anahtar SILEREK saglamak sayilmaz.

    Ustteki superset testi, senkron dalin ``set_``i bosaltilirsa TRIVIAL olarak
    gecer. Bu test o kacamagi kapatir: senkron dal bilinen yuk tasiyan
    anahtarlari yazmaya devam etmeli.
    """
    save_answer = _save_answer_dugumu()
    (_, senkron_anahtarlar) = _upsert_set_anahtarlari(
        _ic_fonksiyon(save_answer, "_sync_save")
    )[0]

    eksik = SYNC_ZORUNLU_ANAHTARLAR - senkron_anahtarlar
    assert (
        not eksik
    ), f"senkron UPSERT'ten yuk tasiyan anahtar(lar) dusmus: {sorted(eksik)}"


# ---------------------------------------------------------------------------
# DEGER duzeyi civi (B3 -- denetim mutasyonla bir bosluk buldu, 27 Agu 2026)
# ---------------------------------------------------------------------------
#
# Ustteki testler set_ ANAHTARLARINI civiliyor, DEGERLERINI degil. Bagimsiz
# denetim bunu mutasyonla olctu ve boslugu gosterdi:
#
#     "is_correct": stmt.excluded.is_correct   ->   "is_correct": False
#     -> 0 YENI test dustu (bekci HAYATTA KALDI)
#
# Yani K2'nin kapattigi kusur sinifinin TAM KENDISI (uretimde is_correct'in
# yanlis yazilmasi) bekciyi yesil gecerek geri gelebilirdi. Anahtar dogru,
# semantik korunmuyordu.
#
# Sozlesme: UPSERT'te CEVAP YUKUNU tasiyan kolonlar GELEN SATIRDAN alinir
# (stmt.excluded.*). `answered_at` ve `answer_changes` ise BILEREK turetilir
# (sunucu saati / sayac artisi) -- onlari excluded'a baglamak sayaci bozardi.
EXCLUDED_ZORUNLU_ANAHTARLAR = frozenset(
    {"selected_answer", "response_time_seconds", "is_correct"}
)
TURETILEN_ANAHTARLAR = frozenset({"answered_at", "answer_changes"})


def _upsert_set_degerleri(kapsam: ast.AST) -> list[tuple[int, dict[str, str]]]:
    """Her ``on_conflict_do_update`` cagrisinin ``set_`` deger IFADELERI.

    Donen: [(satir_no, {anahtar: ast.unparse(deger)}), ...]
    Metin degil AST: bu dosyanin kendi yorumlari "stmt.excluded.is_correct"
    dizgesini ICERIYOR ve metin aramasi onu kod sanardi.
    """
    bulunan: list[tuple[int, dict[str, str]]] = []
    for dugum in ast.walk(kapsam):
        if not isinstance(dugum, ast.Call):
            continue
        f = dugum.func
        if not (isinstance(f, ast.Attribute) and f.attr == "on_conflict_do_update"):
            continue
        set_kw = next((k for k in dugum.keywords if k.arg == "set_"), None)
        if set_kw is None or not isinstance(set_kw.value, ast.Dict):
            continue
        esleme: dict[str, str] = {}
        for k, v in zip(set_kw.value.keys, set_kw.value.values, strict=True):
            if isinstance(k, ast.Constant) and isinstance(k.value, str):
                esleme[k.value] = ast.unparse(v)
        bulunan.append((dugum.lineno, esleme))
    return bulunan


def test_alet_dogrulamasi_deger_okuyucu_bos_donmuyor() -> None:
    """Deger okuyucu 0 anahtar dondurse alttaki testler BOS KUMEDE gecerdi."""
    save_answer = _save_answer_dugumu()
    (_, degerler) = _upsert_set_degerleri(_ic_fonksiyon(save_answer, "_db_worker"))[0]
    assert len(degerler) >= 5, f"deger okuyucu eksik okudu: {degerler}"


def test_uretim_upsert_cevap_yukunu_gelen_satirdan_aliyor() -> None:
    """Cevap yuku tasiyan kolonlar ``stmt.excluded.<ayni anahtar>`` olmali.

    Sabit (or. ``False``) veya baska bir kolona baglamak, cakisma aninda
    gelen cevabi SESSIZCE atar -- kolon guncellenmis gorunur ama degeri
    yanlistir. Anahtar-kumesi testi bunu goremez.
    """
    save_answer = _save_answer_dugumu()
    (satir, degerler) = _upsert_set_degerleri(_ic_fonksiyon(save_answer, "_db_worker"))[
        0
    ]

    for anahtar in sorted(EXCLUDED_ZORUNLU_ANAHTARLAR):
        assert anahtar in degerler, (
            f"satir {satir}: uretim UPSERT'inde '{anahtar}' yok "
            f"(mevcut: {sorted(degerler)})"
        )
        assert degerler[anahtar] == f"stmt.excluded.{anahtar}", (
            f"satir {satir}: '{anahtar}' gelen satirdan ALINMIYOR. "
            f"Beklenen 'stmt.excluded.{anahtar}', bulunan {degerler[anahtar]!r}. "
            "Cakismada gelen cevap sessizce atilir."
        )


def test_kontrol_kolu_turetilen_anahtarlar_excluded_a_baglanmamis() -> None:
    """KONTROL KOLU: her seyi ``excluded``a baglayarak ustteki testi gecme.

    ``answer_changes`` bir SAYAC (``... + 1``), ``answered_at`` sunucu saati.
    Ikisini de gelen satirdan almak, istemcinin sayaci ezmesine izin verirdi.
    Bu test o kacamagi kapatir ve ayni zamanda ustteki kuralin KAPSAMINI
    (hangi anahtarlar icin gecerli oldugunu) civiler.
    """
    save_answer = _save_answer_dugumu()
    (satir, degerler) = _upsert_set_degerleri(_ic_fonksiyon(save_answer, "_db_worker"))[
        0
    ]

    for anahtar in sorted(TURETILEN_ANAHTARLAR):
        assert anahtar in degerler, f"satir {satir}: '{anahtar}' UPSERT'ten dusmus"
        assert degerler[anahtar] != f"stmt.excluded.{anahtar}", (
            f"satir {satir}: '{anahtar}' gelen satirdan aliniyor. Bu kolon "
            "BILEREK turetiliyor (sayac / sunucu saati); excluded'a baglamak "
            "istemcinin degeri ezmesine izin verir."
        )


def test_iki_dal_ortak_anahtarlarda_ayni_ifadeyi_yaziyor() -> None:
    """Iki dalin ORTAK anahtarlarinda deger IFADELERI birebir ayni olmali.

    Ustteki ``..._gelen_satirdan_aliyor`` testi MUTLAK sozlesmeyi civiler
    (uretim dali excluded'dan almali). Bu test ise GORECE olani civiler:
    dallar birbirinden KAYMAMALI. Ikisi birlikte gerekli --
      * yalniz mutlak test olsaydi: senkron dal sessizce kayabilirdi
        (ve testler senkron dali kostugu icin kusur gizli kalirdi),
      * yalniz parite testi olsaydi: IKI dal AYNI ANDA yanlis yazilirsa
        (or. ikisi de ``False``) test yesil gecerdi.
    """
    save_answer = _save_answer_dugumu()
    (uretim_satir, uretim) = _upsert_set_degerleri(
        _ic_fonksiyon(save_answer, "_db_worker")
    )[0]
    (senkron_satir, senkron) = _upsert_set_degerleri(
        _ic_fonksiyon(save_answer, "_sync_save")
    )[0]

    ortak = sorted(set(uretim) & set(senkron))
    assert ortak, "iki dalin ortak anahtari yok -- AST desenimiz bayatlamis olabilir"

    farklar = {a: (uretim[a], senkron[a]) for a in ortak if uretim[a] != senkron[a]}
    assert not farklar, (
        f"uretim (satir {uretim_satir}) ile senkron (satir {senkron_satir}) "
        f"dallari ortak anahtarlarda FARKLI ifade yaziyor: {farklar}. "
        "Testler senkron dali kosar; dallar kayarsa test uretimde olmayan bir "
        "davranisi dogrular."
    )
