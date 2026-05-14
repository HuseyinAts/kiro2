"""
_apply_C3_scoring.py — read existing C3_SCORING.tsv, fill verdict/error_type/notes
based on pre-analysis (Claude session 156).
"""

from __future__ import annotations

import csv
from pathlib import Path

PILOTS = Path("C:/Users/husey/kiro2/backend/_pilots")
SRC = PILOTS / "20260515_audit_C3_SCORING.tsv"

# id -> (verdict, error_type, notes)
SCORING: dict[str, tuple[str, str, str]] = {
    "635a0d1a-3635-526c-8ef7-3e755f2a4150": (
        "fail",
        "garbage_text",
        "Hiz farki yon bilgisi gerektirir; A=10 hicbir senaryoda dogru degil",
    ),
    "b1b47537-4940-5b85-b369-6648a54568c0": (
        "pass",
        "",
        "Stokiyometri: 1 mol Br2 limiting, 40g Ca kullanildi, 120g kaldi; C=120 dogru",
    ),
    "41efea4a-0ef8-5891-ac74-36817761b158": (
        "fail",
        "incomplete",
        "Noktalar verilmemis, soru eksik",
    ),
    "ac7b00f2-d8ec-5983-9891-13cdfb50893f": ("pass", "", "P(0)=c trivial; D dogru"),
    "90481b04-86f6-5d8d-ab8c-6eedd5efc7e1": (
        "fail",
        "wrong_answer",
        "Alan = 20*sqrt(3) ~= 34.64; A=20 yanlis. FIZIK->GEOMETRI yanlis konu",
    ),
    "c8345387-47f1-5cc1-a6b3-779abb4f1204": (
        "pass",
        "",
        "(placeholder, will be overwritten)",
    ),  # bug guard
    "c8343387-47f1-5cc1-a6b3-779abb4f1204": (
        "fail",
        "garbage_text",
        "'Eski, Gelen' anlamsiz; OCR veya soru kotuluk",
    ),
    "5a98ee3b-865e-56ed-8e50-daca61bd29a8": (
        "fail",
        "incomplete",
        "5 cumle verilmemis",
    ),
    "3714a906-9886-5e52-8647-31039dac0180": (
        "fail",
        "incomplete",
        "Cumle yok, sadece sayi siklari",
    ),
    "056c1c5f-9fa1-5c02-bf80-3f8afca026ed": (
        "fail",
        "garbage_text",
        "Operasyon-sayi eslesmesi anlamsiz",
    ),
    "58cd4ea9-08ed-5fb4-bfc6-134ea3aee9b9": (
        "fail",
        "garbage_text",
        "Perisan tarih kavrami degil",
    ),
    "ff7f8586-6826-5954-9921-e740d98ca253": (
        "fail",
        "wrong_answer",
        "r = 12/(2pi) ~= 1.91; D=6 yanlis. OCR'da cap->cevre kaymis olabilir",
    ),
    "e8712643-0ab5-5e61-b6e5-b0b6faab7ce0": ("pass", "", "log_10(100) = 2; B dogru"),
    "3979f37e-f022-5976-8062-f95778a4e2ec": (
        "fail",
        "garbage_text",
        "'Mikro hemsarp' Turkce degil; soru anlamsiz",
    ),
    "d05ddd69-d12b-54c9-8b93-a7989fe5bfed": (
        "unclear",
        "missing_diagram",
        "Grafik gerekli; gorsel yok",
    ),
    "c9412ffe-2109-59f5-ad66-61c18636d786": (
        "fail",
        "garbage_text",
        "Siklar coğrafya 1965 sorusuyla alakasiz",
    ),
    "4245dcbf-7e32-55cb-bc89-2cae3cbb24f4": (
        "unclear",
        "ocr",
        "Question text cut off (degisime ug); tam metin yok",
    ),
    "40493f2d-b56b-5bc0-8919-4d1b38b74bcc": (
        "fail",
        "wrong_topic",
        "Kimya yerine matematik; siklar recursive sacma",
    ),
    "91502bd1-c078-5188-8e01-4b973b3e9091": (
        "unclear",
        "incomplete",
        "Hesap a=5 b=15 ab=75; soru ne soruyor cut off",
    ),
    "11d94792-8e47-58a5-83a0-a53fb366fd1f": (
        "unclear",
        "missing_diagram",
        "AB=4 mu 6 mi gorsel gerektirir; iki yorumda farkli cevap",
    ),
    "8f0fb2b8-4060-5c00-a0fd-85d8d9b89239": (
        "pass",
        "",
        "a=37, b=2, c=2 hepsi asal; toplam 41 dogru",
    ),
    "3ec083af-c12e-5081-85d3-011811de1c6d": (
        "fail",
        "garbage_text",
        "Siklar self-referential; soru sacma",
    ),
    "05c9a801-4994-5f6c-8b0e-933620ccfeee": (
        "unclear",
        "missing_diagram",
        "Sekil yok, dikdortgen alan hesaplanamaz",
    ),
    "83f6835a-a007-5bc3-9e48-15c4395503cb": (
        "unclear",
        "missing_diagram",
        "3D problem; gorsel olmadan zor dogrulanir",
    ),
    "0818982a-7444-5749-b9c1-370f9ccb9873": (
        "fail",
        "garbage_text",
        "FIZIK ile alakasiz KUAFOR raporu nonsense",
    ),
    "7988cfec-0fc1-5447-9ba0-f001efc46e2c": (
        "fail",
        "garbage_text",
        "Self-referential; carpilacak sayi yok",
    ),
    "84fb1d64-558e-57e2-8806-46429792222a": (
        "pass",
        "",
        "Etilen + O2 (yanma), + H2 (hidrojenasyon); D dogru",
    ),
    "e22de7a2-ced0-5bae-8f70-8a4b1bd0cb12": (
        "unclear",
        "ocr",
        "Question cut off (in...)",
    ),
    "307a540d-40fc-53ff-ade1-610a94c5c050": (
        "unclear",
        "missing_diagram",
        "Sekil 1 ve Sekil 2 gerekli",
    ),
    "62934412-f9cd-5451-803d-65b43e0316a7": (
        "fail",
        "wrong_topic",
        "Edebiyat yerine cebirsel ifade; x dogru ama yanlis konu",
    ),
    "a02c9d07-43fc-515a-b1d9-f9a55c8c06c4": (
        "pass",
        "",
        "Kokler pi/8, 5pi/8, 3pi/4; toplam 3pi/2 dogru",
    ),
}


def main() -> None:
    # Remove placeholder bug guard
    SCORING.pop("c8345387-47f1-5cc1-a6b3-779abb4f1204", None)

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

    # Verify by reading back
    verdict_count: dict[str, int] = {}
    error_count: dict[str, int] = {}
    with SRC.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter="\t", quotechar='"')
        next(reader)  # skip header
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
