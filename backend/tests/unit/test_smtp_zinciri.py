"""SMTP zinciri sozlesmesi — F20 · F21 · F21-yeni (#466).

30 Tem denetimi + 1 Agu dogrulamasi uc ayri kusur olctu. Ucu de ayni sinifta:
**gonderim sessizce oluyor ama sistem "basarili" diyor.**

F20 — ANAHTAR AYRISIMI (olculdu, 1 Agu)
---------------------------------------
    SMTP_HOST   okuyanlar: startup_validator.py · validate_production_env.py
                           scripts/backup_database.py     (hepsi DOGRULAYICI)
    SMTP_SERVER okuyanlar: core/email_util.py · core/kvkk_compliance.py
                           analytics/health_audit_service.py  (hepsi TUKETICI)

Operator dokumante edilen `SMTP_HOST`'u doldurursa **startup validator GECER**
ama `send_email` `SMTP_SERVER` bos oldugu icin sessizce `False` doner.
Yani sistem "yapilandirma tamam" der, e-posta hic gitmez. Bu, kusurun en
kotu turu: yanlis pozitif bir saglik sinyali.

F21 — DONUS DEGERI YUTULUYOR
----------------------------
`_send_veli_onay_email` `None` donduruyor ve `send_email`in sonucunu hic
okumuyordu. Karsilastirma: sifre sifirlama yolu (`auth.py:1568`)
`kuyruga_alindi = send_email(...)` ile sonucu YAKALIYOR ve logluyor.
Veli onayi (KVKK acik riza) daha kritik olmasina ragmen geride kalmisti.

F21-yeni — "GONDERILDI" YALANI
------------------------------
`/veli-onay/resend` gonderim olse bile kosulsuz
`"Onay e-postasi tekrar gonderildi"` donduruyordu. Bu tam olarak
`2d5d82f7e`de admin tarafinda kapatilan **yanlis-basari** sinifi.
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.security]

SMTP_ANAHTARLARI = (
    "SMTP_HOST",
    "SMTP_SERVER",
    "SMTP_USERNAME",
    "SMTP_PASSWORD",
    "SMTP_PORT",
    "EMAIL_FROM",
)


@pytest.fixture
def temiz_smtp_ortami(monkeypatch):
    """Testler arasi sizinti olmasin — tum SMTP anahtarlarini kaldir."""
    for anahtar in SMTP_ANAHTARLARI:
        monkeypatch.delenv(anahtar, raising=False)
    return monkeypatch


@pytest.fixture
def sahte_smtp(monkeypatch):
    """smtplib.SMTP'yi taklit et; gercek baglanti KURULMAZ."""
    from core import email_util

    gonderilenler: list[str] = []

    class _SahteSMTP:
        def __init__(self, sunucu, port):
            gonderilenler.append(f"baglanti:{sunucu}:{port}")

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def starttls(self):
            pass

        def login(self, kullanici, parola):
            pass

        def send_message(self, msg):
            gonderilenler.append("gonderildi")

    monkeypatch.setattr(email_util.smtplib, "SMTP", _SahteSMTP)
    return gonderilenler


def _kimlik_doldur(mp, host_anahtari: str) -> None:
    mp.setenv(host_anahtari, "smtp.ornek.com")
    mp.setenv("SMTP_USERNAME", "kullanici")
    mp.setenv("SMTP_PASSWORD", "parola")  # pragma: allowlist secret


# ---------------------------------------------------------------------------
# F20 — anahtar ayrisimi
# ---------------------------------------------------------------------------


def test_kontrol_kolu_hicbir_kimlik_yoksa_false(temiz_smtp_ortami, sahte_smtp) -> None:
    """KONTROL KOLU: kimlik yokken False donmeli.

    Bu gecmezse asagidaki testlerin "True dondu" sonuclari degersizdir —
    fonksiyon her kosulda True donuyor olabilirdi.
    """
    from core.email_util import send_email

    assert send_email("a@b.com", "konu", "<p>x</p>", blocking=True) is False
    assert sahte_smtp == [], "kimlik yokken baglanti KURULMAMALIYDI"


def test_smtp_server_ile_gonderim_calisir(temiz_smtp_ortami, sahte_smtp) -> None:
    """Geriye donuk uyum: mevcut ad calismaya devam etmeli."""
    from core.email_util import send_email

    _kimlik_doldur(temiz_smtp_ortami, "SMTP_SERVER")
    assert send_email("a@b.com", "konu", "<p>x</p>", blocking=True) is True
    assert "gonderildi" in sahte_smtp


def test_smtp_host_ile_de_gonderim_calisir(temiz_smtp_ortami, sahte_smtp) -> None:
    """F20'nin ta kendisi: dokumante edilen `SMTP_HOST` de kabul edilmeli.

    Fix ONCESI: `email_util` yalniz `SMTP_SERVER` okuyordu -> operator
    `SMTP_HOST` doldurdugunda validator GECIYOR ama gonderim sessizce
    olüyordu. Bu test o tuzagi civiler.
    """
    from core.email_util import send_email

    _kimlik_doldur(temiz_smtp_ortami, "SMTP_HOST")
    assert send_email("a@b.com", "konu", "<p>x</p>", blocking=True) is True, (
        "SMTP_HOST ile gonderim yapilamadi — dogrulayicilarin okudugu anahtar "
        "tuketici tarafindan taninmiyor (F20)"
    )
    assert "gonderildi" in sahte_smtp


def test_iki_anahtar_da_varsa_catisma_yok(temiz_smtp_ortami, sahte_smtp) -> None:
    """Ikisi birden set edilirse belirsizlik olmamali."""
    from core.email_util import send_email

    _kimlik_doldur(temiz_smtp_ortami, "SMTP_HOST")
    temiz_smtp_ortami.setenv("SMTP_SERVER", "smtp.ikinci.com")
    assert send_email("a@b.com", "konu", "<p>x</p>", blocking=True) is True


# ---------------------------------------------------------------------------
# F21 / F21-yeni — donus degeri ve yanlis basari
# ---------------------------------------------------------------------------


def test_veli_onay_maili_donus_degeri_dondurur(temiz_smtp_ortami, sahte_smtp) -> None:
    """F21: `_send_veli_onay_email` sonucu YUTMAMALI.

    Fix ONCESI `None` donuyordu; cagiran taraf gonderimin olup olmadigini
    bilemiyordu. Karsilastirma: sifre sifirlama yolu (auth.py:1568) sonucu
    zaten yakaliyor.
    """
    from api.auth import _send_veli_onay_email

    # Kimlik YOK -> gonderim olur -> False beklenir (None DEGIL)
    sonuc = _send_veli_onay_email("veli@ornek.com", "tok123")
    assert sonuc is False, (
        f"donus {sonuc!r} — kimlik yokken False beklenirdi. "
        "None donuyorsa sonuc hala yutuluyor (F21)."
    )

    # Kimlik VAR -> True
    _kimlik_doldur(temiz_smtp_ortami, "SMTP_HOST")
    assert _send_veli_onay_email("veli@ornek.com", "tok123") is True


def test_gonderim_olurken_basari_mesaji_uretilmemeli() -> None:
    """F21-yeni: `/veli-onay/resend` yanit sozlesmesi.

    Uc, gonderim basarisiz oldugunda "tekrar gonderildi" DEMEMELI.
    Router govdesi AST ile denetleniyor: `_send_veli_onay_email` cagrisinin
    sonucu bir dala baglanmali (atama veya kosul), atilmamali.

    Not: HTTP katmanindan sinamak icin authed istemci gerekiyor; bu depoda
    authed istek asiliyor (bkz. test_admin_content_delete.py notu). Bu yuzden
    sozlesme KAYNAK duzeyinde civileniyor.
    """
    import ast
    import inspect

    from api import auth

    kaynak = inspect.getsource(auth)
    agac = ast.parse(kaynak)

    hedef = next(
        (
            d
            for d in ast.walk(agac)
            if isinstance(d, ast.AsyncFunctionDef) and "resend" in d.name.lower()
        ),
        None,
    )
    assert hedef is not None, "resend fonksiyonu bulunamadi — test hedefi kaybolmus"

    # `_send_veli_onay_email(...)` CIPLAK bir ifade olarak durmamali.
    ciplak_cagri = [
        d
        for d in ast.walk(hedef)
        if isinstance(d, ast.Expr)
        and isinstance(d.value, ast.Call)
        and getattr(d.value.func, "id", "") == "_send_veli_onay_email"
    ]
    assert not ciplak_cagri, (
        "`_send_veli_onay_email` sonucu kullanilmadan cagriliyor -> uc, gonderim "
        "olse bile 'tekrar gonderildi' der (F21-yeni). Sonucu bir dala bagla."
    )
