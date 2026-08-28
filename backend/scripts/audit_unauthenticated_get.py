"""Canlı auth'suz GET taraması — hangi uçlar token olmadan 200 + veri dönüyor?

NEDEN CANLI: statik AST taraması 367 "auth izi olmayan" uç buldu ama bu sayı
tek başına anlamsız. Bazıları meşru açık (login, register, health), bazıları
router seviyesinde `dependencies=[...]` ile korunuyor olabilir, bazıları da
middleware tarafından. Tek güvenilir ölçüm gerçek HTTP.

GÜVENLİ: yalnız GET çağırır. POST/PUT/PATCH/DELETE'e hiç dokunmaz — onlar
durum değiştirir.

Kullanım:
    python scripts/audit_unauthenticated_get.py            # özet
    python scripts/audit_unauthenticated_get.py --json out.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys

import httpx

# Windows konsolu cp1254; bu olmadan Türkçe çıktı okunmaz.
# Satır sonundaki bastırma gerekli: stub `TextIO` diyor ama çalışma
# zamanındaki nesne `TextIOWrapper` ve `reconfigure` Python 3.7'den beri var.
# NOT: bu açıklama satırı bastırma direktifinin metnini BİLEREK tekrarlamıyor —
# mypy onu düz yorumda bile direktif sanıp "geçersiz" diye düşüyor (aynı
# tuzağa ruff da RUF100 ile düşmüştü, bkz. elasticsearch_service.py).
sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

BASE = "http://localhost:8000"
TIMEOUT = 8

# Yol parametreleri için doldurulacak zararsız değerler. Yanlış değer 404/422
# verir — bu da bilgi: uç en azından auth'tan ÖNCE düşmüyor demektir.
PLACEHOLDERS = {
    "subject": "MATEMATIK",
    "subject_id": "MATEMATIK",
    "exam_type": "TYT",
    "topic_id": "00000000-0000-0000-0000-000000000000",
    "question_id": "00000000-0000-0000-0000-000000000000",
    "session_id": "00000000-0000-0000-0000-000000000000",
    "user_id": "00000000-0000-0000-0000-000000000000",
    "student_id": "00000000-0000-0000-0000-000000000000",
}
DEFAULT_PLACEHOLDER = "1"

# Gövdede görülürse "hassas" say. Sadece ipucu — insan doğrulaması şart.
SENSITIVE = (
    "correct_answer",
    "dogru_cevap",
    "password",
    "hashed_password",
    "secret",
    "api_key",
    "access_token",
    "refresh_token",
    "tc_kimlik",
)


def fill(path: str) -> str:
    def sub(m: re.Match[str]) -> str:
        return PLACEHOLDERS.get(m.group(1), DEFAULT_PLACEHOLDER)

    return re.sub(r"\{([^}]+)\}", sub, path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", dest="json_out")
    ap.add_argument("--base", default=BASE)
    args = ap.parse_args()

    client = httpx.Client(base_url=args.base, timeout=TIMEOUT, follow_redirects=False)
    spec = client.get("/openapi.json", timeout=30).json()

    gets = [(p, d) for p, ops in spec.get("paths", {}).items() if (d := ops.get("get"))]
    print(f"OpenAPI'de {len(gets)} GET ucu var. Auth'suz deneniyor...\n")

    acik: list[dict] = []
    sayac = {"200": 0, "401/403": 0, "404": 0, "diger": 0, "hata": 0}

    for i, (path, op) in enumerate(sorted(gets), 1):
        yol = fill(path)
        try:
            resp = client.get(yol)
        except httpx.HTTPError:
            sayac["hata"] += 1
            continue
        code, body = resp.status_code, resp.text[:4000]

        if code == 200:
            sayac["200"] += 1
            bulgu = [s for s in SENSITIVE if s in body]
            acik.append(
                {
                    "path": path,
                    "url": yol,
                    "summary": (op.get("summary") or "")[:60],
                    "sensitive": bulgu,
                    "preview": body[:160],
                }
            )
        elif code in (401, 403):
            sayac["401/403"] += 1
        elif code == 404:
            sayac["404"] += 1
        else:
            sayac["diger"] += 1

        if i % 100 == 0:
            print(f"  ...{i}/{len(gets)}")

    hassas = [a for a in acik if a["sensitive"]]
    print(f"\n{'=' * 62}")
    print(f"AUTH'SUZ 200 DÖNEN     : {sayac['200']}")
    print(f"  ...hassas alan içeren: {len(hassas)}   <-- İNCELENECEK")
    print(f"401/403 (korunuyor)    : {sayac['401/403']}")
    print(f"404                    : {sayac['404']}")
    print(f"diğer                  : {sayac['diger']}")
    print(f"ulaşılamadı            : {sayac['hata']}")

    if hassas:
        print(f"\n--- HASSAS ALAN İÇEREN AUTH'SUZ UÇLAR ({len(hassas)}) ---")
        for a in hassas:
            print(f"  {a['path']}")
            print(f"     alanlar: {a['sensitive']}")
            print(f"     önizleme: {a['preview'][:110]}")

    if args.json_out:
        from pathlib import Path

        Path(args.json_out).write_text(
            json.dumps(acik, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"\nTam liste: {args.json_out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
