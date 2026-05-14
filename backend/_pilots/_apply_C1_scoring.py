"""
_apply_C1_scoring.py — Claude session 156 pre-analysis.
"""

from __future__ import annotations

import csv
from pathlib import Path

PILOTS = Path("C:/Users/husey/kiro2/backend/_pilots")
SRC = PILOTS / "20260515_audit_C1_SCORING.tsv"

SCORING: dict[str, tuple[str, str, str]] = {
    "a47ecdd1-59dc-5d46-943d-ab383843d057": (
        "fail",
        "missing_diagram",
        "Boyali A ve B alanlari gorsel zorunlu",
    ),
    "c4b4a746-3547-5da8-9814-b442d7d7ac5d": ("unclear", "ocr", "Text cut off (ko...)"),
    "5a4df668-ce78-572a-ac10-c8b9a33701b4": (
        "fail",
        "missing_diagram",
        "Sekil-I direkt referans; kuvvet vektorleri gorselden",
    ),
    "68bcb586-92f7-5197-90cd-1493838da155": (
        "fail",
        "missing_diagram",
        "P noktasi tanimsiz + cut off",
    ),
    "f43b278d-676b-5575-9f55-5a94f85f7133": (
        "unclear",
        "missing_diagram",
        "Hesap mumkun ama konfigurasyon gorsel; koni yuks 4cm vs girme 5cm tutarsizlik",
    ),
    "71630290-d706-589e-92cc-80a33c4a2aee": (
        "pass",
        "",
        "Tum uzunluklar verilmis (|AG|=6 |DC|=11 |GD|=|BC|); text-only cozulebilir",
    ),
    "b88a914c-dc8d-51f8-bf1a-c6acb667c7d6": (
        "fail",
        "missing_diagram",
        "A ve C noktalari metin-only tanimsiz",
    ),
    "05171108-f7a8-5e50-82f5-e5b84c043820": (
        "unclear",
        "ocr",
        "Text cut off; A ile B noktasi sorusu eksik",
    ),
    "d01da84f-f116-5d0c-b167-938fad2fa47e": (
        "fail",
        "missing_diagram",
        "Sicaklik-zaman grafigi gorsel zorunlu",
    ),
    "4c976607-fe9f-5d97-9a22-0c05a84d1e07": (
        "pass",
        "",
        "Saf cebirsel optimizasyon (y=4, y-eksen, y=x^2); gorsel gereksiz",
    ),
    "e5933a22-0dc0-5c15-9a69-00e29564af62": (
        "fail",
        "missing_diagram",
        "Yolcu sayisi tablosu gorsel + cut off",
    ),
    "19a92cb1-bff2-5bff-8e73-1a7af8cc4907": (
        "unclear",
        "ocr",
        "Text cut off; kavramsal mi diyagram mi belirsiz",
    ),
    "c0be7032-18b4-5571-aca1-9cf70f09a5e8": (
        "unclear",
        "missing_diagram",
        "Yay yon/konfigurasyon gorselden okunur",
    ),
    "854959f2-240e-5ab8-8f67-b62cc2c5cb2f": (
        "fail",
        "missing_diagram",
        "Plastik uzunluk tablosu gorsel + cut off",
    ),
    "279f6fce-6abe-54a9-b8db-50d8c1933b5e": (
        "fail",
        "missing_diagram",
        "Egik duzlem acisi gorselden + cut off",
    ),
    "7e1f81a5-62cc-56df-b9d1-86f749e1a023": (
        "fail",
        "missing_diagram",
        "C ve D noktalari tanimsiz",
    ),
    "3df07c9e-9b46-584f-923a-7b686b963301": (
        "fail",
        "missing_diagram",
        "Pergel konstruksiyon gorsel + cut off",
    ),
    "afe2bcbd-c71a-5949-85c3-9d789bcb7c8d": (
        "fail",
        "missing_diagram",
        "Donme dolap kabin sirasi gorsel + cut off",
    ),
    "7e624cbd-1dc6-5d55-9254-9f49c3a19ca3": (
        "fail",
        "missing_diagram",
        "Dikdortgen+yamuk iki sekil referansi + cut off",
    ),
    "ad11e4fd-6afe-5b17-a2d2-a0203f92448f": (
        "unclear",
        "missing_diagram",
        "E konumu metinden tek anlamli cikmaz; EF=2 tutarsiz 10luk kareyle",
    ),
    "65d6731b-7abf-52c2-b097-f6efe6bfc693": (
        "fail",
        "missing_diagram",
        "Sekil + cut off",
    ),
    "23db5e12-0e20-55e3-a8d1-4ba60c07edb3": (
        "unclear",
        "missing_diagram",
        "A, B kokler varsayimi ile m=32; ama acik tanim yok",
    ),
    "77ecc3b5-c742-5deb-84a9-3fde70235676": (
        "fail",
        "missing_diagram",
        "Tarali bolge gorsel + D tanimsiz",
    ),
    "0fe32a13-f5c6-590a-b4a8-86201e023f16": (
        "fail",
        "missing_diagram",
        "Tasima yonleri (1, 2) gorselden",
    ),
    "7094ee56-53a4-5988-83b9-4a4577fd7a88": (
        "unclear",
        "ocr",
        "Deney sonuc tablosu cut off",
    ),
    "5202f256-db5b-5f20-bef5-2d1506ca9894": (
        "fail",
        "missing_diagram",
        "Iki gorsel referans (kap + tablo)",
    ),
    "d33523af-b7fc-536b-9a13-05a971ac0a33": (
        "fail",
        "missing_diagram",
        "Mavi tarali alan gorsel",
    ),
    "390f120d-7d15-5b51-87e9-ac3745f00e14": (
        "unclear",
        "ocr",
        "Olasilik problemi cut off",
    ),
    "2020dc05-915a-5d9c-b2bb-2616adfb0d48": (
        "fail",
        "missing_diagram",
        "Optik konfigurasyon (kaynaklar+kure+perde) gorsel",
    ),
    "4fdb0c39-950b-51d6-820f-152afa448b92": (
        "fail",
        "missing_diagram",
        "Iki sekil referansi (Sekil I + Sekil II)",
    ),
}


def main() -> None:
    with SRC.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter="\t", quotechar='"')
        rows = list(reader)

    header = rows[0]
    id_idx = header.index("id")
    v_idx = header.index("verdict")
    e_idx = header.index("error_type")
    n_idx = header.index("notes")

    updated = 0
    missing: list[str] = []
    for row in rows[1:]:
        qid = row[id_idx]
        if qid in SCORING:
            v, e, n = SCORING[qid]
            row[v_idx] = v
            row[e_idx] = e
            row[n_idx] = n
            updated += 1
        else:
            missing.append(qid)

    if missing:
        print(f"WARNING: {len(missing)} ID mapping eksik: {missing}")
        return

    with SRC.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerows(rows)

    print(f"[OK] {updated}/30 satir guncellendi")

    # Verify
    verdict_count: dict[str, int] = {}
    error_count: dict[str, int] = {}
    with SRC.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter="\t", quotechar='"')
        next(reader)
        for row in reader:
            v = row[v_idx]
            e = row[e_idx] or "(none)"
            verdict_count[v] = verdict_count.get(v, 0) + 1
            if v != "pass":
                error_count[e] = error_count.get(e, 0) + 1

    print("\nVerdict dagilimi:")
    for v, n in sorted(verdict_count.items(), key=lambda x: -x[1]):
        pct = 100.0 * n / 30
        print(f"  {v:10s} {n:>3d} ({pct:5.1f}%)")

    print("\nError type dagilimi (non-pass):")
    for e, n in sorted(error_count.items(), key=lambda x: -x[1]):
        print(f"  {e:20s} {n:>3d}")


if __name__ == "__main__":
    main()
