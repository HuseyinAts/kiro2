"""L2 e-posta doğrulama — HTTP zinciri uçtan uca.

NE ÖLÇÜYOR
----------
Birim testleri (`tests/unit/test_eposta_dogrulama.py`) POLİTİKAYI çiviliyor:
flag, muafiyet, token deposu. Ama politika doğru olup **kablama** kopuk
olabilir. Bu depoda tam olarak bu sınıf hata defalarca çıktı:

  S225  uç 201 + success:true + "0/3 eklendi" döndürüyordu, 4 mock'lu test PASS
  S229  8 uç KOŞULSUZ 500 veriyordu; AsyncMock'lu testler bu sınıfı yapısal
        olarak GÖREMEZ (`.claude/rules/verification.md`)

Bu yüzden burada ölçülen şey "uç 200 döndü" DEĞİL:
  - gönderilen e-postadaki linkten token çıkarılıyor,
  - o token'la verify çağrılıyor,
  - `is_verified` GERÇEKTEN true oluyor mu diye kullanıcı nesnesi okunuyor,
  - aynı link ikinci kez çalışmıyor (replay),
  - kapı açıkken giriş GERÇEKTEN 403 veriyor, kapalıyken VERMİYOR.

VERİTABANI NEDEN SAHTE
----------------------
`backend/conftest.py` DATABASE_URL'i sqlite'a eziyor; in-process app gerçek
PostgreSQL'e bağlanamıyor. Burada ölçülen şey SQL değil **kablama ve uç
sözleşmesi**. Depo katmanının kendi testleri ayrı ve mutasyonla doğrulandı
(5/5 öldü). Kardeş akış `test_password_recovery_flow.py` de aynı dikişi
kullanıyor.
"""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from core.eposta_dogrulama import MUAFIYET_SINIRI

pytestmark = [pytest.mark.integration, pytest.mark.security]

_TOKEN_RE = re.compile(r"token=([A-Za-z0-9_\-]+)")


class _Sonuc:
    def __init__(self, satir: Any) -> None:
        self._satir = satir

    def fetchone(self) -> Any:
        return self._satir

    def scalar_one_or_none(self) -> Any:
        return self._satir


class _SahteOturum:
    """Asgari AsyncSession ikamesi — UPDATE'i GERÇEKTEN uygular.

    `is_verified` alanını yazan dalı taklit etmek zorunda: aksi hâlde "uç 200
    döndü" ölçülür ama "alan değişti mi" ÖLÇÜLMEZ — bu testin varlık sebebi tam
    olarak o farkı görmek.
    """

    def __init__(self) -> None:
        self.kullanicilar: dict[str, Any] = {}
        self.commit_sayisi = 0
        self.geri_alma_sayisi = 0
        self.uygulanan_update = 0

    def kaydet(self, user: Any) -> None:
        self.kullanicilar[user.email] = user
        self.kullanicilar[user.id] = user

    async def execute(self, stmt: Any, params: Any = None, *a: Any, **k: Any) -> _Sonuc:
        sql = str(stmt)
        params = params or {}

        if "UPDATE users" in sql and "is_verified" in sql:
            user = self.kullanicilar.get(params.get("uid"))
            if user is not None:
                user.is_verified = True
                self.uygulanan_update += 1
            return _Sonuc(None)

        if "FROM users" in sql and "lower(email)" in sql:
            return _Sonuc(self.kullanicilar.get(params.get("e")))

        # LoginCommand: select(DBUser).where(DBUser.email == ...)
        try:
            baglilar = [str(v) for v in stmt.compile().params.values()]
        except Exception:
            baglilar = []
        for deger in baglilar:
            if deger in self.kullanicilar:
                return _Sonuc(self.kullanicilar[deger])
        return _Sonuc(None)

    async def commit(self) -> None:
        self.commit_sayisi += 1

    async def rollback(self) -> None:
        """Geri alma SAYILIR — "hiç yazmadı" ile "yazıp geri aldı" ayrılabilsin.

        Boş bırakılsaydı bir test bu ikisini ayırt edemezdi: `is_verified`
        false kalır ve sebebi görünmezdi. Kardeş `test_password_recovery_flow.py`
        de aynı sebeple sayıyor.
        """
        self.geri_alma_sayisi += 1


@pytest.fixture(scope="module")
def app_ve_oturum():
    """Uygulamayı bir kez içe aktar ve DB bağımlılığını devral."""
    from core.dependencies import get_db
    from main import app

    session = _SahteOturum()

    async def _override():
        yield session

    app.dependency_overrides[get_db] = _override
    try:
        yield app, session
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture(autouse=True)
def _temiz_depo():
    """Her teste taze depo — süreç-ömürlü tekil, olay döngüsüne bağlı.

    `core.eposta_dogrulama._depo` Redis istemcisini önbelleğe alır ve o istemci
    kendisini yaratan olay döngüsüne bağlıdır. pytest her teste YENİ döngü açar
    → önbellekteki istemci ikinci testte "Event loop is closed" verir. Kardeş
    akışta (`test_password_recovery_flow.py:102`) birebir aynı tuzak ölçüldü.
    """
    import core.eposta_dogrulama as modul

    modul._depo = modul._Depo()
    yield


@pytest.fixture(autouse=True)
def _kapi_varsayilan_kapali(monkeypatch: pytest.MonkeyPatch):
    """Testler flag'i açıkça kurar; ortamdan sızan değer sonucu belirlemesin."""
    monkeypatch.delenv("EPOSTA_DOGRULAMA_ZORUNLU", raising=False)
    yield


@pytest.fixture
def gonderilen(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, str]]:
    """`send_email` çağrılarını yakala — SMTP kimlik bilgisi olmadan ölç.

    `core.email_util.send_email` yamalanıyor, `core.eposta_dogrulama` DEĞİL:
    orada import fonksiyon İÇİNDE yapılıyor, yani çağrı anında kaynak modülden
    çözülüyor.
    """
    kayitlar: list[dict[str, str]] = []

    def _sahte(to: str, subject: str, html_body: str, blocking: bool = False) -> bool:
        kayitlar.append({"to": to, "subject": subject, "html": html_body})
        return True

    monkeypatch.setattr("core.email_util.send_email", _sahte)
    return kayitlar


def _kullanici_uret(session: _SahteOturum, *, created_at: datetime, dogrulanmis: bool):
    from models.database import User as DBUser

    benzersiz = uuid.uuid4().hex[:10]
    user = DBUser(
        id=f"user-dogrulama-{benzersiz}",
        email=f"dogrulama-{benzersiz}@kiro2ornek.com",
        username=f"dogrulama-{benzersiz}",
        password_hash="bcrypt-yerine-gecici",  # noqa: S106
    )
    user.is_active = True
    user.is_verified = dogrulanmis
    user.created_at = created_at
    session.kaydet(user)
    return user


@pytest.fixture
def client(app_ve_oturum):
    from fastapi.testclient import TestClient

    app, _session = app_ve_oturum
    with TestClient(app) as c:
        yield c


def _token_cikar(kayitlar: list[dict[str, str]]) -> str:
    assert kayitlar, "hiç e-posta gönderilmedi"
    eslesme = _TOKEN_RE.search(kayitlar[-1]["html"])
    assert eslesme, f"e-postada doğrulama linki yok: {kayitlar[-1]['html'][:200]}"
    return eslesme.group(1)


def _kapiya_takildi(resp: Any) -> bool:
    """Yanıt E-POSTA DOĞRULAMA kapısından mı döndü?

    Salt `status_code == 403`'e bakmak yetmez: başka bir 403 üreticisi de
    olabilir. Kapının kendi kodunu arıyoruz.
    """
    if resp.status_code != 403:
        return False
    govde = resp.json()
    detay = govde.get("detail")
    return isinstance(detay, dict) and detay.get("code") == "EPOSTA_DOGRULANMAMIS"


def _istek_isleyiciye_ulasti(resp: Any) -> None:
    """PREMİS KONTROLÜ — 422 gelirse aşağıdaki 'engellenmedi' assert'i BOŞTUR.

    İlk koşumda tam bu oldu: fixture `@kiro2.test` kullanıyordu, giriş uçları
    `EmailStr` ile doğruluyor ve `.test` özel-kullanım TLD'si reddediliyor.
    İki NEGATİF test (kapı kapalıyken 403 yok) bu yüzden YANLIŞ YERE geçti —
    istek doğrulama katmanında ölüyor, kapı hiç koşmuyordu.
    """
    assert (
        resp.status_code != 422
    ), f"istek gövde doğrulamasında öldü, kapı HİÇ koşmadı: {resp.text[:200]}"


# ---------------------------------------------------------------------------
# Zincir: gönder -> linkten token -> verify -> alan GERÇEKTEN değişti mi
# ---------------------------------------------------------------------------


def test_zincir_gonder_verify_alan_degisiyor(client, app_ve_oturum, gonderilen):
    _app, session = app_ve_oturum
    user = _kullanici_uret(session, created_at=datetime.now(UTC), dogrulanmis=False)

    gonder = client.post(
        "/api/v1/auth/eposta-dogrula/gonder", json={"email": user.email}
    )
    assert gonder.status_code == 200, gonder.text

    token = _token_cikar(gonderilen)

    assert user.is_verified is False, "verify ÖNCESİ alan zaten true — ölçüm anlamsız"

    verify = client.post("/api/v1/auth/eposta-dogrula/verify", json={"token": token})
    assert verify.status_code == 200, verify.text
    assert verify.json()["status"] == "verified"

    # ASIL ASSERT: uç 200 döndü diye alan değişmiş olmaz.
    assert user.is_verified is True, "uç 200 döndü ama is_verified DEĞİŞMEDİ"
    assert session.uygulanan_update == 1
    # Yazma KALICI mı: commit edildi ve geri alınmadı. Bu iki assert olmadan
    # "yazdı ama transaction geri döndü" senaryosu testten sızardı.
    assert session.commit_sayisi >= 1, "UPDATE yapıldı ama commit EDİLMEDİ"
    assert session.geri_alma_sayisi == 0, "yazma geri alındı"


def test_token_tek_kullanimlik(client, app_ve_oturum, gonderilen):
    _app, session = app_ve_oturum
    user = _kullanici_uret(session, created_at=datetime.now(UTC), dogrulanmis=False)
    client.post("/api/v1/auth/eposta-dogrula/gonder", json={"email": user.email})
    token = _token_cikar(gonderilen)

    assert (
        client.post(
            "/api/v1/auth/eposta-dogrula/verify", json={"token": token}
        ).status_code
        == 200
    )
    ikinci = client.post("/api/v1/auth/eposta-dogrula/verify", json={"token": token})
    assert ikinci.status_code == 400, "aynı doğrulama linki İKİNCİ kez çalıştı (replay)"


def test_gecersiz_token_400(client):
    resp = client.post(
        "/api/v1/auth/eposta-dogrula/verify", json={"token": "boyle-bir-token-yok-123"}
    )
    assert resp.status_code == 400


def test_bilinmeyen_eposta_ayni_yaniti_verir(client, app_ve_oturum, gonderilen):
    """Numaralandırma kapalı: yanıt e-postanın kayıtlı olup olmadığını sızdırmaz."""
    _app, session = app_ve_oturum
    kayitli = _kullanici_uret(session, created_at=datetime.now(UTC), dogrulanmis=False)

    var = client.post(
        "/api/v1/auth/eposta-dogrula/gonder", json={"email": kayitli.email}
    )
    yok = client.post(
        "/api/v1/auth/eposta-dogrula/gonder", json={"email": "hicyok@kiro2ornek.com"}
    )

    assert var.status_code == yok.status_code == 200
    assert var.json() == yok.json(), "yanıt e-postanın varlığını sızdırıyor"
    # Kontrol kolu: yanıtlar aynı OLSA DA e-posta yalnız kayıtlıya gitmeli.
    assert len(gonderilen) == 1
    assert gonderilen[0]["to"] == kayitli.email


# ---------------------------------------------------------------------------
# Giriş kapısı — kablanmış mı
# ---------------------------------------------------------------------------


def test_kapi_acikken_dogrulanmamis_yeni_hesap_403(
    client, app_ve_oturum, monkeypatch: pytest.MonkeyPatch
):
    # S251: kapi artik SMTP olmadan ACILMIYOR (kalici kilitlenme yaptirimi).
    # Bayrak TEK BASINA yetmez -- on kosul burada GORUNUR birakiliyor.
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_USERNAME", "kiro2@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "x")
    monkeypatch.setenv("EPOSTA_DOGRULAMA_ZORUNLU", "true")
    _app, session = app_ve_oturum
    user = _kullanici_uret(
        session,
        created_at=MUAFIYET_SINIRI + timedelta(days=1),
        dogrulanmis=False,
    )

    resp = client.post(
        "/api/v1/auth/giris", json={"email": user.email, "sifre": "HerhangiBirSifre1!"}
    )
    _istek_isleyiciye_ulasti(resp)
    assert _kapiya_takildi(
        resp
    ), f"kapı açıkken doğrulanmamış hesap girebiliyor: {resp.status_code} {resp.text[:200]}"


def test_kapi_kapaliyken_403_donmez(client, app_ve_oturum):
    """KONTROL KOLU: kapı hep-engelle olsaydı bu test düşerdi."""
    _app, session = app_ve_oturum
    user = _kullanici_uret(
        session,
        created_at=MUAFIYET_SINIRI + timedelta(days=1),
        dogrulanmis=False,
    )

    resp = client.post(
        "/api/v1/auth/giris", json={"email": user.email, "sifre": "HerhangiBirSifre1!"}
    )
    _istek_isleyiciye_ulasti(resp)
    assert not _kapiya_takildi(resp), "kapı KAPALIYKEN doğrulama 403'ü döndü"


def test_kapi_acikken_eski_hesap_engellenmez(
    client, app_ve_oturum, monkeypatch: pytest.MonkeyPatch
):
    """21 mevcut hesabın kilitlenmemesini HTTP düzeyinde çivileyen assert."""
    # S251: kapi artik SMTP olmadan ACILMIYOR (kalici kilitlenme yaptirimi).
    # Bayrak TEK BASINA yetmez -- on kosul burada GORUNUR birakiliyor.
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_USERNAME", "kiro2@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "x")
    monkeypatch.setenv("EPOSTA_DOGRULAMA_ZORUNLU", "true")
    _app, session = app_ve_oturum
    user = _kullanici_uret(
        session,
        created_at=MUAFIYET_SINIRI - timedelta(days=30),
        dogrulanmis=False,
    )

    resp = client.post(
        "/api/v1/auth/giris", json={"email": user.email, "sifre": "HerhangiBirSifre1!"}
    )
    _istek_isleyiciye_ulasti(resp)
    assert not _kapiya_takildi(resp), "muafiyet sınırından ESKİ hesap kilitlendi"


def test_kapi_iki_giris_ucunda_da_var(
    client, app_ve_oturum, monkeypatch: pytest.MonkeyPatch
):
    """`/login/secure` atlatma yolu olmamalı.

    Kapı yalnız `/giris`e konsaydı bu test düşerdi — ve gerçek bir bypass
    olurdu, çünkü frontend httpOnly-cookie akışında bu ucu kullanıyor.
    """
    # S251: kapi artik SMTP olmadan ACILMIYOR (kalici kilitlenme yaptirimi).
    # Bayrak TEK BASINA yetmez -- on kosul burada GORUNUR birakiliyor.
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_USERNAME", "kiro2@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "x")
    monkeypatch.setenv("EPOSTA_DOGRULAMA_ZORUNLU", "true")
    _app, session = app_ve_oturum
    user = _kullanici_uret(
        session,
        created_at=MUAFIYET_SINIRI + timedelta(days=1),
        dogrulanmis=False,
    )

    resp = client.post(
        "/api/v1/auth/login/secure",
        json={"email": user.email, "sifre": "HerhangiBirSifre1!"},
    )
    _istek_isleyiciye_ulasti(resp)
    assert _kapiya_takildi(
        resp
    ), f"/login/secure kapıyı ATLIYOR: {resp.status_code} {resp.text[:200]}"
