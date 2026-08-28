"""Demo yolu prova kosucusu — 2 Agu 2026 yatirimci sunumu icin.

NE YAPAR
--------
Yatirimciya gosterilecek 8 adimlik akisin cagirdigi GERCEK uclari,
frontend'in kullandigi kimlik dogrulama seklinde (cookie tabanli
`/auth/login/secure`) sirayla vurur ve HTTP kodlarini raporlar.

NEDEN COOKIE
------------
`frontend/src/services/*` `/api/v1/auth/login/secure` kullaniyor ve oturumu
httpOnly cookie'de tasiyor. Bearer ile olcum yapmak DEMOYU TEMSIL ETMEZ —
tarayicidaki akis farkli bir kimlik yolundan gecer. Ikisi de olculur.

KULLANIM
--------
    python backend/scripts/demo_yolu_probu.py            # tam prova
    python backend/scripts/demo_yolu_probu.py --kisa     # sadece ozet

CIKIS KODU
----------
    0  demo yolunda 5xx YOK
    1  en az bir 5xx var  (demoda gosterilemez)
"""

from __future__ import annotations

import argparse
import sys

import httpx

TEMEL = "http://localhost:8000"
ZAMAN_ASIMI = 30.0

# Tohum (seed) demo hesaplari — backend/scripts/seed_mvp_data.py ile kurulur.
# URETIM KIMLIGI DEGIL; ayni degerler tests/e2e/test_golden_flows.py:58-62'de de var.
KULLANICILAR = {
    "ogrenci": {
        "email": "test@kiro2.com",
        "password": "Kiro2Beta2026@x",  # pragma: allowlist secret
    },
    "ogretmen": {
        "email": "ogretmen@kiro2.com",
        "password": "Kiro2Beta2026@x",  # pragma: allowlist secret
    },
    "veli": {
        "email": "veli@kiro2.com",
        "password": "Kiro2Beta2026@x",  # pragma: allowlist secret
    },
}

# (adim, rol, metot, yol, govde) — frontend'in GERCEKTEN cagirdigi uclar
ADIMLAR: list[tuple[str, str, str, str, dict | None]] = [
    # --- 2. Ogrenci girisi ---
    ("2 giris", "ogrenci", "GET", "/api/v1/auth/me", None),
    ("2 giris", "ogrenci", "GET", "/api/v1/student-dashboard/profil", None),
    # --- 3. Ogrenci paneli ---
    ("3 panel", "ogrenci", "GET", "/api/v1/gamification/profile", None),
    ("3 panel", "ogrenci", "GET", "/api/v1/leagues/current", None),
    ("3 panel", "ogrenci", "GET", "/api/v1/student-dashboard/istatistikler", None),
    ("3 panel", "ogrenci", "GET", "/api/v1/analytics/student/{uid}", None),
    # --- 4. Ogrenme yolu ---
    ("4 yol", "ogrenci", "GET", "/api/v1/learning-path/completion/{sid}", None),
    ("4 yol", "ogrenci", "GET", "/api/v1/learning-style/detect/{sid}", None),
    # --- 5. Soru cozme ---
    (
        "5 soru",
        "ogrenci",
        "POST",
        "/api/v1/osym-exam/beta-practice",
        {"soru_sayisi": 5},
    ),
    # --- 6. Tekrar (FSRS) ---
    ("6 tekrar", "ogrenci", "GET", "/api/v1/fsrs/due?limit=20", None),
    ("6 tekrar", "ogrenci", "GET", "/api/v1/fsrs/due-count", None),
    ("6 tekrar", "ogrenci", "GET", "/api/v1/fsrs/stats", None),
    # --- 7. Ogretmen ---
    ("7 ogretmen", "ogretmen", "GET", "/api/v1/auth/me", None),
    ("7 ogretmen", "ogretmen", "GET", "/api/v1/teacher/classes", None),
    ("7 ogretmen", "ogretmen", "GET", "/api/v1/teacher/students", None),
    ("7 ogretmen", "ogretmen", "GET", "/api/v1/teacher/exams", None),
    ("7 ogretmen", "ogretmen", "GET", "/api/v1/teacher/assignments", None),
    ("7 ogretmen", "ogretmen", "GET", "/api/v1/teacher/reports", None),
    # --- 8. Sinav ---
    ("8 sinav", "ogrenci", "GET", "/api/v1/osym-exam/exam-configs", None),
    ("8 sinav", "ogrenci", "GET", "/api/v1/osym-exam/my-exams", None),
    ("8 sinav", "ogrenci", "GET", "/api/v1/student-dashboard/sinav-gecmisi", None),
    # --- Veli (opsiyonel yuzey) ---
    ("9 veli", "veli", "GET", "/api/v1/parent/children", None),
    ("9 veli", "veli", "GET", "/api/v1/parent/notifications", None),
]


_SID_ONBELLEK: dict[int, str] = {}


def _sid(istemci: httpx.Client) -> str:
    """Ogrenme-yolu `STU_xxx` kimligi — `users.id` DEGIL.

    Ilk olcumde `users.id` gonderilmisti ve 403 alinmisti; o bir ALET
    hatasiydi (IDOR kapisi dogru davraniyordu), urun kusuru degil.
    """
    anahtar = id(istemci)
    if anahtar not in _SID_ONBELLEK:
        yanit = istemci.get("/api/v1/learning-path/my-profile")
        deger = ""
        if yanit.status_code == 200:
            govde = yanit.json()
            deger = str(
                govde.get("student_id") or govde.get("data", {}).get("student_id") or ""
            )
        _SID_ONBELLEK[anahtar] = deger or "SID-COZULEMEDI"
    return _SID_ONBELLEK[anahtar]


def _oturum_ac(rol: str) -> tuple[httpx.Client, str]:
    """Cookie tabanli giris — frontend'in kullandigi yol.

    Basarisiz olursa Bearer'a duser ve bunu isaretler; ikisi de olmazsa
    RuntimeError. Sessizce devam ETMEZ.
    """
    istemci = httpx.Client(base_url=TEMEL, timeout=ZAMAN_ASIMI, follow_redirects=True)
    kimlik = KULLANICILAR[rol]

    yanit = istemci.post("/api/v1/auth/login/secure", json=kimlik)
    if yanit.status_code == 200 and istemci.cookies:
        govde = yanit.json()
        uid = str(govde.get("user", {}).get("id") or govde.get("id") or "")
        if uid:
            return istemci, uid

    yanit = istemci.post("/api/v1/auth/login", json=kimlik)
    if yanit.status_code != 200:
        raise RuntimeError(
            f"{rol} girisi BASARISIZ: {yanit.status_code} {yanit.text[:200]}"
        )
    govde = yanit.json()
    jeton = govde.get("access_token")
    istemci.headers["Authorization"] = f"Bearer {jeton}"
    uid = str(
        govde.get("user", {}).get("id") or govde.get("kullanici", {}).get("id") or ""
    )
    if not uid:
        me = istemci.get("/api/v1/auth/me")
        if me.status_code == 200:
            uid = str(me.json().get("id") or me.json().get("user", {}).get("id") or "")
    return istemci, uid


def main() -> int:
    ayristirici = argparse.ArgumentParser()
    ayristirici.add_argument("--kisa", action="store_true")
    argumanlar = ayristirici.parse_args()

    oturumlar: dict[str, tuple[httpx.Client, str]] = {}
    for rol in KULLANICILAR:
        try:
            oturumlar[rol] = _oturum_ac(rol)
            print(f"[giris] {rol:9} OK  (uid={oturumlar[rol][1][:8]}...)")
        except Exception as hata:
            print(f"[giris] {rol:9} COKTU: {hata}")

    if "ogrenci" not in oturumlar:
        print("\nOGRENCI GIRISI YOK — demo yolu olculemez.")
        return 1

    sonuclar: list[tuple[str, str, int, str]] = []
    for adim, rol, metot, yol_sablonu, govde in ADIMLAR:
        if rol not in oturumlar:
            sonuclar.append((adim, yol_sablonu, -1, "giris yok"))
            continue
        istemci, uid = oturumlar[rol]
        yol = yol_sablonu.replace("{uid}", uid).replace("{sid}", _sid(istemci))
        try:
            yanit = istemci.request(metot, yol, json=govde)
            ozet = yanit.text[:70].replace("\n", " ")
            sonuclar.append((adim, yol, yanit.status_code, ozet))
        except Exception as hata:
            sonuclar.append((adim, yol, -2, f"{type(hata).__name__}: {hata}"))

    print("\n" + "=" * 78)
    print("DEMO YOLU — ADIM ADIM")
    print("=" * 78)
    onceki = ""
    for adim, yol, kod, ozet in sonuclar:
        if adim != onceki:
            print(f"\n--- ADIM {adim} ---")
            onceki = adim
        isaret = "OK " if 200 <= kod < 400 else ("4xx" if 400 <= kod < 500 else "5XX")
        satir = f"  [{isaret}] {kod:>4}  {yol}"
        if not argumanlar.kisa and kod >= 400:
            satir += f"\n         {ozet}"
        print(satir)

    bes_yuzler = [(a, y, k) for a, y, k, _ in sonuclar if k >= 500 or k < 0]
    print("\n" + "=" * 78)
    if bes_yuzler:
        print(f"SONUC: {len(bes_yuzler)} KIRIK — demoda gosterilemez:")
        for adim, yol, kod in bes_yuzler:
            print(f"  {kod:>4}  [{adim}]  {yol}")
        return 1

    dort_yuzler = sum(1 for _, _, k, _ in sonuclar if 400 <= k < 500)
    print(
        f"SONUC: 5xx YOK. ({dort_yuzler} adet 4xx var — anlamli olabilir, kontrol et)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
