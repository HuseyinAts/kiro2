"""Toplu cevap yazma kuyrugunun ZEHIRLENME tetikleyicilerini CANLI olcer (S255).

NEDEN VAR
---------
S254'te bir tetikleyici bulundu ve kapatildi: frontend'in mesru `clearAnswer`'i
bos dizge gonderiyordu, `student_answers.check_selected_answer` bunu reddediyordu
ve `core/osym_exam_engine.py:707` toplu UPSERT'i patliyordu. Uc yine de 200
donuyordu (`:709` `except Exception` yutuyor), yani ayni batch'teki 1000'e kadar
cevap SESSIZCE kayboluyordu.

Devir notunda acik kalan soru suydu: **`""` disinda baska tetikleyici var mi?**
Bu prob onu OLCER, tahmin etmez.

TETIKLEYICI TANIMI
------------------
Batch ogesinin herhangi bir alani PostgreSQL tarafindan reddedilirse islem
patlar, `commit()`e hic ulasilmaz ve TUM batch geri alinir. Yani "tetikleyici"
= istemcinin ETKILEYEBILDIGI ve DB'nin REDDETTIGI her deger.

`student_answers` kisitlari (olculdu, 27 Agu 2026):
    check_selected_answer   : NULL veya 'A'..'E'
    selected_answer         : varchar(1)
    question_id  FK         : question_bank(id)
    exam_session_id FK      : exam_sessions(id)
    uq_student_answer       : UNIQUE (exam_session_id, question_id)

OLCUM YORDAMI
-------------
Her aday icin:
  1. ONCE  : oturumun DB satir sayisi + konteyner gunlugundeki
             "Bulk DB worker error" satir sayisi
  2. ES ZAMANLI atis: N gecerli cevap + 1 aday (ayni batch penceresine
             dusme sansini artirmak icin `asyncio.gather`)
  3. SONRA : ayni iki sayac
  4. Yargi : aday 200 dondu mu (yani DB katmanina ulasti mi) · gunluk hatasi
             delta'si · GECERLI komsu cevaplarin kaci kalici oldu

MUTLAK SAYI DEGIL DELTA olculur: gunlukte zaten eski hatalar olabilir.

Kullanim (host'tan):
    python backend/scripts/batch_zehirlenme_probu.py
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess  # nosec B404 - salt-olcum aleti; argv LISTE, shell yok
import sys
import uuid

import httpx

if hasattr(sys.stdout, "reconfigure"):  # mypy: TextIO taban sinifinda yok
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BACKEND = os.environ.get("BACKEND_URL", "http://localhost:8000")
PSQL = os.environ.get("PSQL_BIN", r"C:/Program Files/PostgreSQL/18/bin/psql.exe")
KONTEYNER = os.environ.get("BACKEND_CONTAINER", "kiro2-backend")
OGRENCI = {
    "email": "test@kiro2.com",
    "password": "Kiro2Beta2026@x",  # pragma: allowlist secret
}
HATA_DESENI = "Bulk DB worker error"

# Kac gecerli komsu cevap ayni atista gonderilsin (co-batch sansi).
KOMSU = 3


def _psql(sql: str) -> str:
    p = subprocess.run(  # nosec B603 - argv LISTE (shell yok); sabit psql yolu
        [PSQL, "-U", "postgres", "-p", "5434", "-d", "kiro2", "-t", "-A", "-c", sql],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if p.returncode != 0:
        raise RuntimeError(f"psql hatasi: {p.stderr[:300]}")
    return p.stdout.strip()


def _uuid_dogrula(session_id: str) -> str:
    """SQL'e giden TEK degisken. Enterpolasyondan once bicimi civilenir.

    `nosec B603` gerekcesi ancak bu dogrulama varsa DOGRUDUR: aksi halde
    'kullanici girdisi yok' iddiasi yanlis olurdu.
    """
    return str(uuid.UUID(session_id))


def db_satir_sayisi(session_id: str) -> int:
    return int(
        _psql(
            "SELECT count(*) FROM student_answers "  # nosec B608 - tek degisken UUID dogrulanir
            f"WHERE exam_session_id = '{_uuid_dogrula(session_id)}'"
        )
        or 0
    )


def gunluk_hata_sayisi() -> int:
    """Konteyner gunlugundeki toplu-yazma hatasi satir sayisi.

    ALET NOTU: `docker logs` konteynerin stdout'unu okur; prob AYRI bir surecte
    kostugu icin kendi ciktisi buraya karismaz. Yine de MUTLAK sayi degil DELTA
    kullaniliyor -- bir sayacin YESIL gorunmesi, olctugunu kanitlamaz.
    """
    p = subprocess.run(  # nosec B603 B607 - argv LISTE (shell yok); sabit docker komutu
        ["docker", "logs", "--tail", "20000", KONTEYNER],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return (p.stdout + p.stderr).count(HATA_DESENI)


async def kur(c: httpx.AsyncClient) -> tuple[str, dict[str, str], list[str]]:
    r = await c.post("/api/v1/auth/login", json=OGRENCI)
    r.raise_for_status()
    jeton = r.json()["access_token"]
    basliklar = {"Authorization": f"Bearer {jeton}"}

    r = await c.post(
        "/api/v1/osym-exam/create",
        headers=basliklar,
        json={
            "exam_type": "TYT",
            "custom_config": {
                "subject": "MATEMATIK",
                "difficulty": "medium",
                "question_count": KOMSU + 2,
                "time_limit": 30,
            },
        },
    )
    assert r.status_code == 200, f"create {r.status_code}: {r.text[:300]}"
    sid = r.json()["session_id"]

    r = await c.post(f"/api/v1/osym-exam/{sid}/start", headers=basliklar)
    assert r.status_code == 200, f"start {r.status_code}: {r.text[:200]}"

    sorular: list[str] = []
    for i in range(KOMSU + 2):
        r = await c.post(
            f"/api/v1/osym-exam/{sid}/navigate",
            headers=basliklar,
            json={"question_index": i},
        )
        if r.status_code != 200:
            break
        qid = r.json().get("id") or r.json().get("question_id")
        if qid and qid not in sorular:
            sorular.append(qid)
    assert len(sorular) >= KOMSU + 1, f"yeterli soru toplanamadi: {sorular}"
    return sid, basliklar, sorular


async def _kaydet(
    c: httpx.AsyncClient, sid: str, basliklar: dict[str, str], govde: dict
) -> int:
    r = await c.post(
        f"/api/v1/osym-exam/{sid}/save-answer", headers=basliklar, json=govde
    )
    return int(r.status_code)


def oturumu_temizle(session_id: str) -> None:
    """Aday olcumleri arasinda oturumun satirlarini sifirla.

    ZORUNLU: ayni (oturum, soru) ciftine ikinci yazim UPSERT'e duser ve satir
    sayisini ARTIRMAZ -- temizlik olmadan `satir_delta` ilk adaydan sonra her
    zaman 0 cikar, yani sayac YANLIS-SIFIR uretir ve "zehirlenme var" ile
    "zaten yazilmisti" ayirt edilemez. Kapsam yalniz bu probun kendi
    olusturdugu oturum.
    """
    _psql(
        "DELETE FROM student_answers WHERE exam_session_id = "  # nosec B608 - UUID dogrulanir
        f"'{_uuid_dogrula(session_id)}'"
    )


async def adayi_olc(
    c: httpx.AsyncClient,
    sid: str,
    basliklar: dict[str, str],
    komsu_sorular: list[str],
    ad: str,
    zehir: dict,
    zehir_gecerli: bool,
) -> dict:
    oturumu_temizle(sid)
    once_satir = db_satir_sayisi(sid)
    assert once_satir == 0, f"temizlik calismadi: {once_satir} satir kaldi"
    once_hata = gunluk_hata_sayisi()

    isler = [
        _kaydet(c, sid, basliklar, {"question_id": q, "selected_answer": "A"})
        for q in komsu_sorular
    ]
    isler.append(_kaydet(c, sid, basliklar, zehir))
    kodlar = await asyncio.gather(*isler, return_exceptions=True)

    await asyncio.sleep(2.5)
    sonra_satir = db_satir_sayisi(sid)
    sonra_hata = gunluk_hata_sayisi()

    zehir_kodu = kodlar[-1]
    komsu_kodlari = kodlar[:-1]
    # Zehir gecerliyse kendi satirini da yazar; degilse yalniz komsular beklenir.
    beklenen = len(komsu_sorular) + (1 if zehir_gecerli else 0)
    return {
        "aday": ad,
        "zehir_http": zehir_kodu,
        "komsu_http": sorted({str(k) for k in komsu_kodlari}),
        "yazilan": sonra_satir - once_satir,
        "beklenen": beklenen,
        "gunluk_hata_delta": sonra_hata - once_hata,
    }


async def main() -> int:
    async with httpx.AsyncClient(base_url=BACKEND, timeout=30.0) as c:
        sid, basliklar, sorular = await kur(c)
        print(f"oturum: {sid}")
        print(f"toplanan soru: {len(sorular)}")

        adaylar: list[tuple[str, dict]] = [
            (
                "T0 KONTROL KOLU: gecerli 'B'",
                {"question_id": sorular[-1], "selected_answer": "B"},
            ),
            (
                "T1 bos dizge (S254'te kapatildi)",
                {"question_id": sorular[-1], "selected_answer": ""},
            ),
            (
                "T2 A-E disi harf 'F'",
                {"question_id": sorular[-1], "selected_answer": "F"},
            ),
            (
                "T3 tek karakterden uzun 'AB'",
                {"question_id": sorular[-1], "selected_answer": "AB"},
            ),
            (
                "T4 var olmayan question_id (FK)",
                {"question_id": str(uuid.uuid4()), "selected_answer": "A"},
            ),
            (
                "T5 yalniz bosluk '  ' (S254 bunu kacirdi mi?)",
                {"question_id": sorular[-1], "selected_answer": "  "},
            ),
            (
                "T6 AYNI soruya es zamanli 2. yazim",
                {"question_id": sorular[0], "selected_answer": "C"},
            ),
        ]

        sonuclar = []
        for i, (ad, zehir) in enumerate(adaylar):
            # Yalniz T0 gecerli bir satir yazar; digerleri DB'de reddedilmeli.
            # T0 gecerli harf; T1/T5 "cevabi temizle" (bos/bosluk) -> NULL
            # satir YAZILIR. Digerleri DB'ye hic ulasmamali.
            gecerli = ad.startswith(("T0", "T1", "T5"))
            # Komsu sorular sabit; her aday oncesi oturum satirlari SIFIRLANIYOR
            # (bkz. oturumu_temizle) -- yoksa UPSERT yanlis-sifir uretirdi.
            komsu = sorular[:KOMSU]
            r = await adayi_olc(c, sid, basliklar, komsu, ad, zehir, gecerli)
            sonuclar.append(r)
            print(f"  [{i}] {json.dumps(r, ensure_ascii=False)}")

        print("\n=== OZET ===")
        print(f"{'aday':38} {'zehir':6} {'yaz/bek':9} {'gunlukD':8} yargi")
        for r in sonuclar:
            kayip = r["yazilan"] < r["beklenen"]
            canli = r["gunluk_hata_delta"] > 0
            if canli and kayip:
                yargi = "TETIKLEYICI + KOMSU KAYBI"
            elif canli:
                yargi = "TETIKLEYICI (komsu kurtuldu)"
            elif kayip:
                yargi = "KAYIP VAR ama gunlukte hata YOK (?)"
            else:
                yargi = "tetiklemedi"
            oran = f"{r['yazilan']}/{r['beklenen']}"
            print(
                f"{r['aday'][:38]:38} {r['zehir_http']!s:6} "
                f"{oran:9} {r['gunluk_hata_delta']:8} {yargi}"
            )
        # CALISTIRILMAZ: operatore gosterilen temizlik ipucu METNI.
        print(f"\ntemizlik icin: DELETE FROM exam_sessions WHERE id = '{sid}';")  # nosec B608
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
