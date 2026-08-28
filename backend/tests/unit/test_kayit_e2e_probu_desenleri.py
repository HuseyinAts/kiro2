"""`kayit_e2e_probu.py`'nin grep desenleri kaynakla hizalı mı.

NEDEN BU BEKÇİ VAR
------------------
Prob, gönderim yargısını `docker logs` içinde bir dize sayarak veriyor:

    DESEN_GONDERILDI = "email gönderildi:"   ->  core/email_util.py:77
    DESEN_HATA       = "email gönderim hatası" ->  core/email_util.py:79
    DESEN_DOGRULAMA_ANAHTARI = "eposta_dogrulama_token:*"
                                             ->  core/eposta_dogrulama.py:187
    (ad "TOKEN" icermez: ruff S105 degeri degil DEGISKEN ADINI deseniyor)

Bu dizeler **kopyadır**. Kaynaktaki log mesajı değişirse prob hiçbir hata
vermez — sonsuza kadar `Δ0` ölçer ve "gönderim olmadı" der. Yani sessiz
**yanlış-SIFIR**: bir ilerleme sayacındaki tek kabul edilemez hata türü, ve
tam olarak `smtp_dogrulama_probu.py`'nin :29-33'te ve `kayit_e2e_probu.py`'nin
kendi docstring'inde belgelediği kusur sınıfı.

Bekçi SABİT bir metin beklemiyor — **iki bağımsız kaynağı karşılaştırıyor**:
probun sabiti ile üretim modülünün gerçek `logger` çağrısındaki biçim dizesi.
Biri değişip diğeri değişmezse test düşer.

⚠️ Karşılaştırma AST üzerinden yapılır, ham metin üzerinden DEĞİL: bu dosyanın
kendi docstring'i o desenleri İÇERİYOR ve metin araması onları "kaynakta var"
sanardı (`.claude/rules/audit-methodology.md` — "bir deseni anlatan yorum onu
içerir"). Yorum ve docstring AST'de yoktur; tuzak yapısal olarak imkânsız.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[2]
PROB = BACKEND / "scripts" / "kayit_e2e_probu.py"
EMAIL_UTIL = BACKEND / "core" / "email_util.py"
DOGRULAMA = BACKEND / "core" / "eposta_dogrulama.py"


def _agac(yol: Path) -> ast.Module:
    return ast.parse(yol.read_text(encoding="utf-8"))


def _modul_sabiti(yol: Path, ad: str) -> str:
    """Modül düzeyindeki `AD = "..."` atamasının değeri (AST'den)."""
    for dugum in _agac(yol).body:
        if isinstance(dugum, ast.Assign):
            for hedef in dugum.targets:
                if isinstance(hedef, ast.Name) and hedef.id == ad:
                    assert isinstance(dugum.value, ast.Constant)
                    return str(dugum.value.value)
    raise AssertionError(f"{yol.name} içinde modül sabiti {ad} yok")


def _sinif_sabiti(yol: Path, sinif: str, ad: str) -> str:
    for dugum in ast.walk(_agac(yol)):
        if isinstance(dugum, ast.ClassDef) and dugum.name == sinif:
            for govde in dugum.body:
                if isinstance(govde, ast.Assign):
                    for hedef in govde.targets:
                        if isinstance(hedef, ast.Name) and hedef.id == ad:
                            assert isinstance(govde.value, ast.Constant)
                            return str(govde.value.value)
    raise AssertionError(f"{yol.name}::{sinif}.{ad} yok")


def _logger_bicimleri(yol: Path) -> list[str]:
    """`logger.<seviye>("biçim", ...)` çağrılarındaki ilk sabit argümanlar."""
    bicimler: list[str] = []
    for dugum in ast.walk(_agac(yol)):
        if not isinstance(dugum, ast.Call):
            continue
        fn = dugum.func
        if not isinstance(fn, ast.Attribute):
            continue
        if fn.attr not in ("debug", "info", "warning", "error", "exception"):
            continue
        if not (isinstance(fn.value, ast.Name) and fn.value.id == "logger"):
            continue
        if dugum.args and isinstance(dugum.args[0], ast.Constant):
            deger = dugum.args[0].value
            if isinstance(deger, str):
                bicimler.append(deger)
    return bicimler


# --------------------------------------------------------------------------
# Alet doğrulaması — ayrıştırıcı gerçekten bir şey buluyor mu?
# --------------------------------------------------------------------------


def test_alet_dogrulamasi_logger_ayristirici_bos_donmuyor() -> None:
    """Ayrıştırıcı 0 biçim bulursa sonraki testler BOŞ geçer (yanlış-yeşil)."""
    bicimler = _logger_bicimleri(EMAIL_UTIL)
    assert len(bicimler) >= 3, (
        f"email_util.py'de yalnız {len(bicimler)} logger biçimi bulundu; "
        "ayrıştırıcı kırık olabilir — bu sayı düşerse aşağıdaki hizalama "
        "testleri hiçbir şey ölçmez"
    )


def test_alet_dogrulamasi_docstring_ast_disinda_kaliyor() -> None:
    """Bu dosyanın kendi docstring'i desenleri içeriyor; AST onu görmemeli.

    Ham metin araması yapsaydık bu dosya kendi kendini "doğrular" ve bekçi
    ölü doğardı.
    """
    kendi = Path(__file__)
    assert "email gönderildi:" in kendi.read_text(
        encoding="utf-8"
    ), "ön koşul: bu dosya deseni metin olarak içermeli"
    assert "email gönderildi:" not in _logger_bicimleri(
        kendi
    ), "AST bu dosyanın docstring'inden desen çıkarıyor — ayrıştırıcı yanlış"


# --------------------------------------------------------------------------
# Hizalama — iki bağımsız kaynak
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("sabit_adi", "kaynak"),
    [("DESEN_GONDERILDI", EMAIL_UTIL), ("DESEN_HATA", EMAIL_UTIL)],
)
def test_prob_deseni_uretim_log_bicimiyle_hizali(sabit_adi: str, kaynak: Path) -> None:
    desen = _modul_sabiti(PROB, sabit_adi)
    bicimler = _logger_bicimleri(kaynak)
    assert any(b.startswith(desen) for b in bicimler), (
        f"kayit_e2e_probu.{sabit_adi} = {desen!r} artık {kaynak.name} içindeki "
        f"hiçbir logger biçiminin başlangıcı değil. Bulunanlar: {bicimler}. "
        "Prob bu haliyle SESSİZCE her zaman Δ0 ölçer (yanlış-SIFIR)."
    )


def test_token_deseni_gercek_redis_anahtar_onekiyle_hizali() -> None:
    desen = _modul_sabiti(PROB, "DESEN_DOGRULAMA_ANAHTARI")
    onek = _sinif_sabiti(DOGRULAMA, "EpostaDogrulamaStore", "KEY_DOGRULAMA")
    assert desen == f"{onek}:*", (
        f"prob {desen!r} tarıyor ama üretim anahtarı {onek!r} önekiyle yazılıyor "
        f"({DOGRULAMA.name}). Token sayacı hiçbir anahtar görmez."
    )


def test_prob_gonderim_yargisini_ayri_surecte_olcmuyor() -> None:
    """Log seviyesini ayrı bir süreçte ölçmek ilk sürümde yanlış-SIFIR üretti.

    O meta-ölçüm kaldırıldı; geri gelirse bu test düşer.

    🔴 Arama AST üzerinde: probun docstring'i kaldırılan kusuru ANLATIYOR ve
    bu yüzden `getEffectiveLevel` dizesini İÇERİYOR. İlk sürüm ham metin
    arıyordu ve bu docstring'e eşleşip anında kırmızı verdi — bu dosyanın
    kendi başındaki uyarının birebir tekrarı. Yorum ve docstring AST'de
    yoktur; kod içindeki gerçek çağrı ise `ast.Attribute` olarak durur.
    """
    # TEK ağaç: `_agac()` her çağrıda YENİ düğümler üretir, dolayısıyla
    # `id()` karşılaştırması iki ayrı ağaç arasında ASLA tutmaz (ölçüldü).
    agac = _agac(PROB)
    dugumler = list(ast.walk(agac))

    nitelikler = {d.attr for d in dugumler if isinstance(d, ast.Attribute)}
    isimler = {d.id for d in dugumler if isinstance(d, ast.Name)}

    # `ast.get_docstring()` metni cleandoc'lar; ham `Constant.value` ile
    # eşleşmez ve metin çıkarması sessizce tutmaz (ölçüldü). Bu yüzden
    # docstring DÜĞÜMLERİ kimlikle elenir, metinle değil.
    docstring_dugumleri: set[int] = set()
    for d in dugumler:
        if not isinstance(
            d, ast.Module | ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
        ):
            continue
        govde = d.body
        if not govde:
            continue
        ilk = govde[0]
        if (
            isinstance(ilk, ast.Expr)
            and isinstance(ilk.value, ast.Constant)
            and isinstance(ilk.value.value, str)
        ):
            docstring_dugumleri.add(id(ilk.value))

    # Kod, `docker exec … python -c "<dize>"` biçiminde de yazılabilir; bu
    # yüzden docstring OLMAYAN sabit dizelere de bakılır.
    kod_dizeleri = {
        d.value
        for d in dugumler
        if isinstance(d, ast.Constant)
        and isinstance(d.value, str)
        and id(d) not in docstring_dugumleri
    }
    assert kod_dizeleri, "alet doğrulaması: probda hiç kod-dizesi bulunamadı"

    assert (
        "getEffectiveLevel" not in nitelikler | isimler
    ), "prob log seviyesini doğrudan çağırarak yeniden ölçmeye başlamış."
    assert not any("getEffectiveLevel" in s for s in kod_dizeleri), (
        "prob log seviyesini alt-süreç dizesi içinde yeniden ölçmeye başlamış. "
        "Bu ölçüm uygulamanın logging kurulumunu hiç koşmamış TAZE bir "
        "yorumlayıcıda yapılır ve daima WARNING döner -> gerçek delta artmışken "
        "adım [OLCULMEDI] damgası vurur. Yargı YALNIZ Δ'dan çıkarılmalı."
    )
