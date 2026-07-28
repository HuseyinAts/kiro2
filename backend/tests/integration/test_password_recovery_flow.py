"""Şifre kurtarma uçtan uca — kullanıcı gerçekten yeni şifresiyle giriyor mu?

28 Tem 2026 ÖLÇÜMÜ (satışa hazırlık blocker #1):

    backend/api/auth.py:1463   # TODO: Send email with reset link

`/auth/forgot-password` token üretip Redis'e yazıyor, kullanıcıya "Şifre
sıfırlama bağlantısı e-posta adresinize gönderildi" diyor ve HİÇBİR ŞEY
göndermiyor. Ödeme yapmış bir kullanıcı hesabını kalıcı olarak kaybediyor.

Ekran (`frontend/src/kiro/screens/HesapKurtarmaPage.tsx`) 6 haneli kod için
tasarlanmış ama tamamen mock: kodu ISTEMCIDE doğruluyor, 3. adımda sunucuya
hiç gitmiyor. Backend ise 32 byte'lık link token'ı üretiyordu — iki uç farklı
akış konuşuyor.

BU TESTİN ÖLÇTÜĞÜ ŞEY: e-postaya giden kodu yakalayıp zinciri sonuna kadar
koşmak — forgot -> (koddan) verify -> reset -> parolanın gerçekten değişmesi.
"Uç 200 döndü" yetmez; 28 Tem'de bu depoda 200 dönen ama hiçbir şey yapmayan
bir uç zaten vardı.

VERİTABANI NEDEN SAHTE
----------------------
`backend/conftest.py:22` DATABASE_URL'i sqlite'a eziyor, yani in-process app
gerçek PostgreSQL'e bağlanamıyor. Burada test edilen şey SQL değil, kodun
yaşam döngüsü ve uç sözleşmesi; kullanıcı arama tek bir `select().where()`.
Bu yüzden DB bir DİKİŞ olarak sahteleniyor, kod deposu ve e-posta yolu ise
GERÇEK. Depo katmanının kendi testleri ayrıca var ve mutasyonla doğrulandı:
`tests/unit/test_password_reset_codes.py` + `scripts/mutation_check_password_reset.py`.
"""

from __future__ import annotations

import re
import uuid
from typing import Any

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.security]

NEW_PASSWORD = "Kiro2Yeni!2026"  # noqa: S105  # pragma: allowlist secret

_CODE_RE = re.compile(r"\b(\d{6})\b")


class _FakeResult:
    def __init__(self, obj: Any) -> None:
        self._obj = obj

    def scalar_one_or_none(self) -> Any:
        return self._obj


class _FakeSession:
    """Kayıtlı kullanıcıları e-posta/id ile tanıyan asgari AsyncSession ikamesi."""

    def __init__(self) -> None:
        self.kullanicilar: dict[str, Any] = {}
        self.commit_sayisi = 0

    def kaydet(self, user: Any) -> None:
        self.kullanicilar[user.email] = user
        self.kullanicilar[user.id] = user

    async def execute(self, stmt: Any, *args: Any, **kwargs: Any) -> _FakeResult:
        try:
            baglilar = [str(v) for v in stmt.compile().params.values()]
        except Exception:
            baglilar = []
        for deger in baglilar:
            if deger in self.kullanicilar:
                return _FakeResult(self.kullanicilar[deger])
        return _FakeResult(None)

    async def commit(self) -> None:
        self.commit_sayisi += 1

    async def rollback(self) -> None:  # pragma: no cover - hata yolu
        pass


@pytest.fixture(scope="module")
def app_ve_oturum():
    """Uygulamayı bir kez içe aktar (~30 sn) ve DB bağımlılığını devral."""
    from core.dependencies import get_db
    from main import app

    session = _FakeSession()

    async def _override():
        yield session

    app.dependency_overrides[get_db] = _override
    try:
        yield app, session
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def kullanici(app_ve_oturum):
    """HER TESTE KENDİ hesabı.

    Ortak e-posta kullanınca testler birbirinin *hesap başına saatlik kod
    limitini* tüketiyordu ve 4. test "e-posta gönderilmedi" diye kırmızıya
    dönüyordu — ürün hatası değil, sıraya bağımlı test. Ayrıca zincir testi
    parolayı değiştiriyor; paylaşılan kullanıcı bunu diğer testlere taşırdı.
    """
    from models.database import User as DBUser

    _app, session = app_ve_oturum
    benzersiz = uuid.uuid4().hex[:10]
    user = DBUser(
        id=f"user-kurtarma-{benzersiz}",
        email=f"kurtarma-{benzersiz}@kiro2.test",
        username=f"kurtarma-{benzersiz}",
        password_hash="eski-hash-yerine-gecici",  # noqa: S106
    )
    session.kaydet(user)
    return user


@pytest.fixture
def client(app_ve_oturum):
    from fastapi.testclient import TestClient

    app, _session = app_ve_oturum
    with TestClient(app) as c:
        yield c


@pytest.fixture
def gonderilen(monkeypatch):
    """`send_email` çağrılarını yakala — SMTP kimlik bilgisi olmadan da ölçelim."""
    kayitlar: list[dict[str, str]] = []

    def _sahte(to: str, subject: str, html_body: str, blocking: bool = False) -> bool:
        kayitlar.append({"to": to, "subject": subject, "html": html_body})
        return True

    monkeypatch.setattr("api.auth.send_email", _sahte)
    return kayitlar


def _kodu_ayikla(html: str) -> str:
    eslesme = _CODE_RE.search(html)
    assert eslesme, f"e-posta gövdesinde 6 haneli kod yok: {html[:300]}"
    return eslesme.group(1)


def _kod_iste(client, gonderilen, email: str) -> str:
    resp = client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert resp.status_code == 200, resp.text
    assert gonderilen, "forgot-password hiç e-posta göndermedi"
    return _kodu_ayikla(gonderilen[-1]["html"])


def test_forgot_password_sends_a_six_digit_code(client, gonderilen, kullanici):
    """En temel iddia: uç gerçekten bir e-posta üretiyor mu?

    RED turunda bu test `AttributeError: module 'api.auth' has no attribute
    'send_email'` ile kırmızıydı — `auth.py:1463` yalnızca bir TODO yorumuydu.
    """
    resp = client.post("/api/v1/auth/forgot-password", json={"email": kullanici.email})

    assert resp.status_code == 200, resp.text
    assert len(gonderilen) == 1, "tam olarak bir e-posta beklenirdi"
    assert gonderilen[0]["to"] == kullanici.email
    kod = _kodu_ayikla(gonderilen[0]["html"])
    assert len(kod) == 6


def test_full_chain_changes_the_password(client, gonderilen, kullanici, app_ve_oturum):
    """forgot -> verify -> reset zinciri parolayı GERÇEKTEN değiştirmeli.

    Son adımda "200 döndü" ile yetinmiyoruz: yeni parolanın hash'ini
    doğruluyoruz. Uç 200 döndürüp hiçbir şey yazmasaydı bu satır yakalardı —
    bu depoda 28 Tem'de tam olarak öyle bir uç vardı.
    """
    from api.auth import pwd_context

    _app, session = app_ve_oturum
    onceki_commit = session.commit_sayisi
    kod = _kod_iste(client, gonderilen, kullanici.email)

    dogrula = client.post(
        "/api/v1/auth/verify-reset-code",
        json={"email": kullanici.email, "code": kod},
    )
    assert dogrula.status_code == 200, dogrula.text
    token = dogrula.json().get("token")
    assert token, f"doğrulama token vermedi: {dogrula.text}"

    sifirla = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "newPassword": NEW_PASSWORD},
    )
    assert sifirla.status_code == 200, sifirla.text
    assert sifirla.json().get("success") is True, sifirla.text

    assert session.commit_sayisi > onceki_commit, "parola yazılmadı (commit yok)"
    assert pwd_context.verify(
        NEW_PASSWORD, kullanici.password_hash
    ), "kullanıcının parola hash'i yeni parolayla eşleşmiyor"


def test_verify_rejects_a_wrong_code(client, gonderilen, kullanici):
    kod = _kod_iste(client, gonderilen, kullanici.email)
    yanlis = "000000" if kod != "000000" else "111111"

    resp = client.post(
        "/api/v1/auth/verify-reset-code",
        json={"email": kullanici.email, "code": yanlis},
    )

    assert resp.status_code == 200, resp.text
    assert resp.json().get("success") is False
    assert not resp.json().get("token")


def test_verify_locks_after_five_wrong_codes(client, gonderilen, kullanici):
    """5 yanlış denemeden sonra DOĞRU kod da reddedilmeli (kaba kuvvet kapısı)."""
    kod = _kod_iste(client, gonderilen, kullanici.email)
    yanlis = "000000" if kod != "000000" else "111111"

    for _ in range(5):
        client.post(
            "/api/v1/auth/verify-reset-code",
            json={"email": kullanici.email, "code": yanlis},
        )

    resp = client.post(
        "/api/v1/auth/verify-reset-code",
        json={"email": kullanici.email, "code": kod},
    )
    assert resp.json().get("success") is False, "kilit tutmadı"
    assert not resp.json().get("token")


def test_unknown_email_looks_identical_and_sends_nothing(client, gonderilen, kullanici):
    """Numaralandırma önleme: bilinmeyen adres aynı yanıtı almalı, mail GİTMEMELİ."""
    bilinen = client.post(
        "/api/v1/auth/forgot-password", json={"email": kullanici.email}
    )
    gonderilen.clear()
    bilinmeyen = client.post(
        "/api/v1/auth/forgot-password", json={"email": "yok@kiro2.test"}
    )

    assert bilinmeyen.status_code == bilinen.status_code
    assert (
        bilinmeyen.json() == bilinen.json()
    ), "bilinmeyen adres farklı yanıt aldı — e-posta numaralandırması mümkün"
    assert not gonderilen, "var olmayan adrese e-posta gönderildi"


def test_verify_does_not_reveal_whether_email_exists(client, kullanici):
    """Doğrulama ucu da 'böyle bir kullanıcı yok' dememeli."""
    bilinmeyen = client.post(
        "/api/v1/auth/verify-reset-code",
        json={"email": "yok@kiro2.test", "code": "123456"},
    )
    bilinen = client.post(
        "/api/v1/auth/verify-reset-code",
        json={"email": kullanici.email, "code": "123456"},
    )

    # Uç HİÇ YOKKEN ikisi de 404 döner ve "aynı yanıt" iddiası boşa geçerdi —
    # RED turunda bu testin tek başına yeşil kalması bunu gösterdi. Önce ucun
    # var olduğunu şart koşuyoruz.
    assert bilinen.status_code == 200, (
        f"/auth/verify-reset-code yok ya da hata veriyor: "
        f"{bilinen.status_code} {bilinen.text[:200]}"
    )
    assert bilinmeyen.status_code == bilinen.status_code
    assert (
        bilinmeyen.json() == bilinen.json()
    ), "doğrulama yanıtı adresin varlığını sızdırıyor"


def test_reset_password_enforces_password_policy(client, gonderilen, kullanici):
    """Sunucu politikası son söz — ekran kuralları bununla aynı olmalı.

    `auth.py:_validate_password` 5 kural uyguluyor (uzunluk, büyük, küçük,
    rakam, özel karakter). Ekran yalnız 3'ünü gösteriyordu (>=8, harf+rakam,
    "tahmini zor"), yani `abcd1234` üç tiki de yeşil yapıp sunucudan hata
    yiyordu — hem de kullanıcı e-postayı alıp kodu girdikten SONRA. Bu test
    sunucu tarafını sabitler; ekran tarafı ayrıca hizalanır.
    """
    kod = _kod_iste(client, gonderilen, kullanici.email)
    token = client.post(
        "/api/v1/auth/verify-reset-code",
        json={"email": kullanici.email, "code": kod},
    ).json()["token"]

    resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "newPassword": "abcd1234"},
    )

    assert (
        resp.json().get("success") is False
    ), "büyük harf ve özel karakter içermeyen parola kabul edildi"
