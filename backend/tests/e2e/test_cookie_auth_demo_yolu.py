"""Demo yolu cookie-kimlik pariteси — tarayıcı neyi görüyorsa o ölçülür.

NEDEN VAR (2 Ağu 2026, yatırımcı demosu hazırlığı)
--------------------------------------------------
Frontend `/api/v1/auth/login/secure` ile giriyor ve oturumu **httpOnly
cookie**'de taşıyor (`Authorization` başlığı GÖNDERMİYOR — ölçüldü:
login sonrası 2 cookie, `authHeader=False`).

Bu yüzden **Bearer ile yapılan her ölçüm demoyu temsil etmez.** Canlı ölçüm
tam olarak bu farkı ortaya çıkardı:

    /api/v1/learning-style/detect/{sid}   COOKIE -> 401   BEARER -> 200
    /api/v1/learning-path/completion/{sid} COOKIE -> 200   BEARER -> 200

Kök neden: `core/learning_path_auth.py:24` `security = HTTPBearer(
auto_error=True)` — **yalnız Bearer**. `api/learning_style.py` bu bağımlılığı
**7 uçta** kullanıyor. Kardeşi `api/learning_path.py` ise
`core.dependencies.get_current_user`'ı (çift kimlik: cookie + Bearer,
CLAUDE.md'de belgeli) kullandığı için tarayıcıda ÇALIŞIYOR.

Yani kusur "auth bozuk" değil, **iki kardeş router'ın farklı kimlik
sözleşmesi kullanması**. Bearer'la koşan bir test bunu ASLA göremezdi.

BU DOSYA NE YAPAR
-----------------
Demo yolundaki uçları **yalnızca cookie ile** çağırır ve 401 görmediğini
iddia eder. Alet doğrulaması: cookie'siz istek 401 VERMELİ — vermiyorsa
ölçüm anlamsızdır (uç zaten korumasız demektir).
"""

from __future__ import annotations

import os

import httpx
import pytest

ARKA_UC = os.getenv("BACKEND_URL", "http://localhost:8000")
ZAMAN_ASIMI = 30.0

OGRENCI = {"email": "test@kiro2.com", "password": "Kiro2Beta2026@x"}

pytestmark = [pytest.mark.e2e]


@pytest.fixture(scope="module")
def cookie_istemcisi() -> httpx.Client:
    """Frontend'in kullandığı giriş yolu — Authorization başlığı YOK."""
    istemci = httpx.Client(base_url=ARKA_UC, timeout=ZAMAN_ASIMI)
    try:
        istemci.get("/health")
    except Exception as hata:
        istemci.close()
        pytest.skip(f"backend {ARKA_UC} erişilemiyor: {hata}")

    yanit = istemci.post("/api/v1/auth/login/secure", json=OGRENCI)
    if yanit.status_code == 429:
        istemci.close()
        pytest.skip("hız sınırı (429) — ölçüm geçersiz olurdu")
    if yanit.status_code != 200:
        istemci.close()
        pytest.skip(f"cookie girişi yok: {yanit.status_code}")

    assert (
        "Authorization" not in istemci.headers
    ), "Test Bearer başlığı taşıyor — bu ölçüm tarayıcıyı TEMSIL ETMEZ."
    assert len(istemci.cookies) > 0, "Cookie kurulmadı — ölçüm aleti arızalı."

    yield istemci
    istemci.close()


@pytest.fixture(scope="module")
def ogrenci_kimligi(cookie_istemcisi: httpx.Client) -> str:
    """Öğrenme yolu uçları `STU_xxx` bekler — `users.id` DEĞİL.

    İlk ölçümde `users.id` gönderilmişti ve 403 alınmıştı; o bir ALET
    hatasıydı (IDOR kapısı doğru davranıyordu), ürün kusuru değil.
    """
    yanit = cookie_istemcisi.get("/api/v1/auth/me")
    assert yanit.status_code == 200, "cookie oturumu /auth/me'de çalışmıyor"
    kullanici_id = str(yanit.json().get("id") or "")

    profil = cookie_istemcisi.get(f"/api/v1/learning-path/completion/{kullanici_id}")
    if profil.status_code == 200:
        return kullanici_id

    # STU_ kimliğini öğrenme-yolu profilinden türet
    liste = cookie_istemcisi.get("/api/v1/learning-path/my-profile")
    if liste.status_code == 200:
        sid = str(liste.json().get("student_id") or "")
        if sid:
            return sid
    pytest.skip("STU_ kimliği bulunamadı — demo öğrencisinin profili yok")


# Demo yolunda tarayıcının çağırdığı, öğrenci-kimliği alan uçlar
COOKIE_ILE_CALISMALI = [
    "/api/v1/auth/me",
    "/api/v1/student-dashboard/profil",
    "/api/v1/student-dashboard/istatistikler",
    "/api/v1/gamification/profile",
    "/api/v1/fsrs/due?limit=20",
    "/api/v1/osym-exam/exam-configs",
]


@pytest.mark.parametrize("yol", COOKIE_ILE_CALISMALI)
def test_demo_ucu_cookie_ile_401_vermez(
    cookie_istemcisi: httpx.Client, yol: str
) -> None:
    """Tarayıcı oturumuyla çağrılan uç 401 DÖNMEMELİ."""
    yanit = cookie_istemcisi.get(yol)
    assert yanit.status_code != 401, (
        f"{yol} cookie oturumunu REDDETTI (401). Frontend Bearer göndermiyor; "
        "bu uç tarayıcıda kırık demektir."
    )


def test_ogrenme_stili_ucu_cookie_ile_401_vermez(
    cookie_istemcisi: httpx.Client, ogrenci_kimligi: str
) -> None:
    """ASIL BULGU: learning-style yalnız Bearer kabul ediyordu.

    Fix'ten ÖNCE KIRMIZI: COOKIE -> 401, BEARER -> 200.
    """
    yanit = cookie_istemcisi.get(f"/api/v1/learning-style/detect/{ogrenci_kimligi}")
    assert yanit.status_code != 401, (
        "learning-style/detect cookie oturumunu reddetti — "
        "core/learning_path_auth.py HTTPBearer(auto_error=True) yalnız Bearer "
        "kabul ediyor, frontend ise cookie kullanıyor."
    )


def test_ogrenme_yolu_kardesi_cookie_ile_calisiyor(
    cookie_istemcisi: httpx.Client, ogrenci_kimligi: str
) -> None:
    """KONTROL KOLU — kardeş router zaten cookie kabul ediyor.

    Bu test fix'ten ÖNCE de YEŞİL. Yeşil kalması, yukarıdaki kırmızının
    'cookie hiç çalışmıyor' değil **router'a özgü** olduğunu kanıtlar.
    """
    yanit = cookie_istemcisi.get(f"/api/v1/learning-path/completion/{ogrenci_kimligi}")
    assert (
        yanit.status_code != 401
    ), "Kardeş router da cookie reddediyor -> teşhis yanlış, sorun daha genel."


def test_alet_dogrulamasi_kimliksiz_istek_reddedilir() -> None:
    """KONTROL KOLU — uç gerçekten korumalı mı?

    Kimliksiz istek 401/403 vermezse, yukarıdaki 'cookie çalışıyor'
    iddiaları anlamsızdır: uç zaten herkese açıktır.
    """
    with httpx.Client(base_url=ARKA_UC, timeout=ZAMAN_ASIMI) as istemci:
        try:
            istemci.get("/health")
        except Exception as hata:
            pytest.skip(f"backend erişilemiyor: {hata}")
        yanit = istemci.get("/api/v1/auth/me")

    assert yanit.status_code in (401, 403), (
        f"Kimliksiz istek {yanit.status_code} döndü — uç korumasız, "
        "bu dosyadaki ölçümler geçersiz."
    )
