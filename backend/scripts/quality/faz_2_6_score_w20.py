#!/usr/bin/env python3
"""
Faz 2.6 W20 — Claude-vision scoring (text-only Pareto).

LLM-CIRCULAR RISK: Bu scoring Claude tarafından yapıldı. Ground truth değil,
preliminary baseline. Beta student feedback ile cross-check zorunlu.

Strateji:
  - Text-only ile karar verilebilen sample'lar: direkt verdict
  - Image-driven sample'lar: verdict=unclear, error_type=needs_image
    (vision spot check sonraki seans veya beta feedback bekler)

Output: SCORING.tsv'leri yerinde günceller, verdict/error_type/notes doldurur.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
PILOTS_DIR = PROJECT_ROOT / "backend" / "_pilots"

# Marker for Claude-scored rows
CLAUDE_TAG = "claude-vision-w20"


# ============================================================================
# REJECT POOL VERDICTS (30 sample)
# ============================================================================
# verdict: 'pass' = filter wrongly rejected (FALSE NEGATIVE = good question rejected)
#          'fail' = filter correctly rejected (CONFIRMED bad question)
#          'unclear' = need vision or human review

REJECT_VERDICTS = {
    "76172b7f-be7d-52d6-91a9-295804d4f600": (
        "unclear",
        "needs_image",
        "BIYOLOJI organ şeması, image gerek. C&D opt overlap risk.",
    ),
    "faf871b2-31dd-5a68-9d63-21c1290ef016": (
        "fail",
        "incomplete_text",
        "OCR garbled: '...parçanın dörtte biri parçanın dörtte biri...' repeat",
    ),
    "d3ab2dff-b771-56c0-b4b5-2b03158342e7": (
        "fail",
        "incomplete_text",
        "Text nonsensical: 'digitlerin hafızası nasıl geliştirilebilir' + sayı options",
    ),
    "36200a4a-6ac9-5ee2-a7e8-476b278fc3bd": (
        "fail",
        "incomplete_text",
        "Options have 'A)' prefix, no actual content; question stub only",
    ),
    "3bd5f668-1562-514f-b092-795444784dcc": (
        "fail",
        "wrong_answer",
        "2000*2/5=800, 2000*3/5=1200 → C doğru; pool B=600+1200 yanlış",
    ),
    "8e99f63b-6fc5-5895-931a-27b20d048dec": (
        "fail",
        "other",
        "Nonsense AI-generated text about papagan-biber",
    ),
    "b6ede2cb-166d-581f-91ed-ea5e3c629241": (
        "fail",
        "wrong_answer",
        "a+b=2019 max a*b çok büyük (~10^6); options 2015-2019 makul değil",
    ),
    "51362bd8-a1e7-5b9c-a61a-1e14cbfb7a13": (
        "pass",
        "false_negative",
        "a²+b²=13, a-b=1 → (3,2) A doğru; soru kaliteli, legacy_v3 yanlış reddetti",
    ),
    "8d641572-aaae-5e30-acd3-d52e85f0012f": (
        "unclear",
        "needs_image",
        "Renkli kareler şeması image-driven",
    ),
    "3f5a5066-1d0c-5dcd-a288-3254a365546d": (
        "fail",
        "incomplete_text",
        "Dikdörtgen 2 köşe verilmiş, eksen-paralel mi belirsiz; ifade kötü",
    ),
    "e36e777a-12aa-5dc7-966b-a84caa3040a9": (
        "unclear",
        "needs_image",
        "Aromat reject (R2); f'(x) grafiği image gerek",
    ),
    "4ffb640d-2da5-5abb-b302-b2667223caa0": (
        "unclear",
        "ambiguous_answer",
        "Yüklem türü: A (fiil neg.) vs D (isim cümlesi) ayırım yorum açık",
    ),
    "28d63129-643a-5e54-8653-3b01e2e1ce13": (
        "unclear",
        "needs_image",
        "Aromat reject (R2); robot süpürge şekil image gerek",
    ),
    "2c0dc435-5ab6-568e-8baf-be759ee8f8fc": (
        "pass",
        "false_negative",
        "a+b=10, a-b=2 → a=6,b=4 C doğru; basit ama doğru soru, legacy_v3 yanlış reddetti",
    ),
    "032c626e-01dc-58a7-8da0-9a05de78acf5": (
        "unclear",
        "needs_image",
        "Edebiyat Sokagi solution-leak suspect; image içinde çözüm risk",
    ),
    "b306a1e3-9183-5032-b633-62598e391987": (
        "fail",
        "incomplete_text",
        "'Bir köşegenin dik açı yapması' — hangi şekil? Bağlam eksik",
    ),
    "665efc50-cbf6-5606-9adb-3a299beab213": (
        "fail",
        "incomplete_text",
        "'Taban alanının genişliği' garip ifade; taban boyutları eksik",
    ),
    "f1e66b73-b443-502e-93de-b686b88ce936": (
        "pass",
        "false_negative",
        "CH₃CH₂COOCH₂CH₃ 10H atom; pool E doğru; ifade küçük hatalı ama soru kaliteli",
    ),
    "fab0cb97-b875-5cfb-a2f2-16b665878128": (
        "fail",
        "wrong_answer",
        "a=5 zorunlu (R'de tanımlılık), f(6)=2; pool E=1 yanlış",
    ),
    "c32af9e0-b669-54c3-8c43-4cc23208fc2d": (
        "fail",
        "incomplete_text",
        "Text garbled '17. yüzyılda bilinen bilgileri...' bağlamsız",
    ),
    "29ae04d8-53d8-5250-ab0f-a0be3d253aa5": (
        "fail",
        "wrong_topic",
        "Aromat tag KIMYA ama içerik FIZIK (virajda hareket); v²=g*r*tanθ=400→v=20; pool E=50 yanlış",
    ),
    "5bc9e21e-6522-5c85-94ca-4d424208f317": (
        "fail",
        "incomplete_text",
        "OCR garbled paragraf; cümle yapıları bozuk",
    ),
    "8e095358-8b92-5b9f-9831-cba944b7075d": (
        "unclear",
        "needs_image",
        "Aromat reject; yüklü parçacık kare konum image gerek",
    ),
    "608bb930-2495-51e1-aca4-078008808216": (
        "fail",
        "wrong_answer",
        "Üçgen kenarlar 10+12+8=30; pool C=34 yanlış",
    ),
    "ee61df92-f123-533a-8063-54529c6ecf26": (
        "fail",
        "wrong_topic",
        "Aromat KIMYA tag; içerik trivial atom-numarası; AI-generated low-quality",
    ),
    "fe808a8c-64ec-5969-8a08-4be9e0869b3a": (
        "fail",
        "incomplete_text",
        "Meta-text 'Bu soru genelde...'; gerçek soru yok",
    ),
    "bee0daa3-9f7f-5eb7-89fd-0b4a42e813c4": (
        "unclear",
        "ambiguous_answer",
        "TARIH soru; B 'iç geçinilmesi' OCR typo, doğru cevap belirsiz",
    ),
    "87b49aff-8ed9-56f2-978c-a27061ac88e4": (
        "fail",
        "wrong_topic",
        "Aromat KIMYA tag yanlış (içerik SOSYAL); E mi A mı belirsiz",
    ),
    "2558856a-83af-57c2-9160-a8cfb211a3ef": (
        "fail",
        "incomplete_text",
        "OCR garbled 'SÜTLENDİRLİ GAZLARI...' caps + anlamsız",
    ),
    "948cff7f-3b10-52df-a033-cdf60edac670": (
        "fail",
        "incomplete_text",
        "Matematik konu özetinin OCR çıktısı; gerçek soru yok, ders metni",
    ),
}


# ============================================================================
# GOLD POOL VERDICTS (30 sample)
# ============================================================================
# verdict: 'pass' = good question (filter correctly promoted)
#          'fail' = bad question (filter wrongly promoted = FALSE POSITIVE)
#          'unclear' = image-required, needs vision

GOLD_VERDICTS = {
    "7f7eb0eb-bd44-5fbf-a27a-d92b969a6c81": (
        "unclear",
        "needs_image",
        "Tramvay istasyon mesafe haritası image-driven",
    ),
    "368f21f4-7263-5249-9964-ab0258143032": (
        "unclear",
        "needs_image",
        "8 kare çift/tek artan; text-only kalkül 48/50 verir, pool E=51",
    ),
    "36a9b20e-e8d5-58a3-9324-223f0ecc9ee1": (
        "unclear",
        "needs_image",
        "y=f(x) grafiği limit hesabı image gerek",
    ),
    "885195e9-cc9a-5990-944b-81f39f943302": (
        "pass",
        None,
        "g'(3)=(1/2)[f(3)+3*f'(3)]=(1/2)[1+21]=11; pool E=11 doğru",
    ),
    "f3c861bc-8cae-50cc-a889-6c968e3bc106": (
        "pass",
        None,
        "ΔΦ=5*2*0.5=5, emk=5/0.1=50V; pool D=50 doğru",
    ),
    "2362fa63-f260-5043-98dd-a84a3dc3c6ec": (
        "unclear",
        "needs_image",
        "Tel uzunluğu image-bound",
    ),
    "26c6c257-4d7b-513b-8896-62bd31ba2ce8": (
        "unclear",
        "needs_image",
        "Harita yeşil/kırmızı yol oranları image-bound",
    ),
    "d890f4af-417a-5340-af3d-4c2270fbf8f0": (
        "unclear",
        "needs_image",
        "Iraksak mercek ışın diyagramı",
    ),
    "5c086724-4b92-50a4-9c9e-b7748742d84d": (
        "unclear",
        "needs_image",
        "Gönye döndürme; ABC,DCD geometri image-bound",
    ),
    "763a53fb-8adc-54a8-b775-b6d60ea11c3e": (
        "unclear",
        "needs_image",
        "Haziran takvim daire içinde günler image-bound",
    ),
    "27b3830b-00fb-54f4-98f4-09c6cba1d7c8": (
        "unclear",
        "needs_image",
        "Yüzdelik dağılım; başlangıç dağılım image-bound",
    ),
    "e0e5125a-9093-5f7e-90d0-d17413ba490a": (
        "unclear",
        "ambiguous_text",
        "Lewis notasyon karışık; 'beklenmez' soru ifadesi çelişkili",
    ),
    "63b28631-4d72-593d-beee-3aaaac7eb48f": (
        "unclear",
        "needs_image",
        "Riemann benzeri sarı/mavi alan toplam",
    ),
    "df39c9ad-2315-5a90-92c5-5650b38e1dea": (
        "unclear",
        "needs_image",
        "ABC eşkenar, ADE katlama; A'C hesabı image-bound geometri",
    ),
    "360069bf-b5d7-5c6c-a9f3-948d2e2c320f": (
        "pass",
        None,
        "AH+BC=12, Alan=(1/2)*b*h max=(1/2)*6*6=18; pool C=18 doğru (AM-GM)",
    ),
    "e79c6d38-c2a7-5e41-b006-0341156870fb": (
        "unclear",
        "needs_image",
        "K,L,M araç sürat tablosu image-bound",
    ),
    "38ba305a-c1fd-53b1-b243-00214024a784": (
        "unclear",
        "needs_image",
        "X,Y,Z taşırma kabı; denge şekilleri image-bound",
    ),
    "ef3a77dc-86c7-5a63-afd3-98da3ec2ed93": (
        "unclear",
        "needs_image",
        "Kare 12x12 kesim, dikdörtgen boyutlar image-bound (pool E=60 olası)",
    ),
    "e70eac5a-3a2f-5c09-9918-c5621598e6ca": (
        "unclear",
        "needs_image",
        "Renkli tahtalar k sayısı image-bound",
    ),
    "a116f9a1-688c-5828-9cb5-d7a019be02d0": (
        "unclear",
        "needs_image",
        "Mayoz evre sıralama image-driven",
    ),
    "252e58b6-164d-5b44-b07c-7154dac45830": (
        "unclear",
        "needs_image",
        "A,B orbital şekli image-bound (pool E=ml=-2 d-orbital implies)",
    ),
    "94fd2383-9755-5e09-a852-e2973a5f124f": (
        "unclear",
        "needs_image",
        "12 top yeşil/kırmızı dağılım image-bound",
    ),
    "89542cad-4c34-58c9-b663-df9414e17521": (
        "fail",
        "wrong_answer",
        "AC ∈ {5..11} → 7 farklı tam sayı; pool B=6 yanlış (üçgen eşitsizliği)",
    ),
    "b8b16260-7d1f-54cf-a306-1d4eedf0c85e": (
        "pass",
        None,
        "10x/(120+10x)=0.4 → x=8; pool C=8 doğru",
    ),
    "b655b4ff-d795-53e0-bc41-13cb80474590": (
        "unclear",
        "needs_image",
        "Fındık ezme initial composition pie chart image-bound",
    ),
    "bf76ddf9-d143-550e-8222-b78dc2cc6bad": (
        "pass",
        None,
        "Nehir t1=4V/(V²-VA²), göl t2=4/V, t1>t2 her zaman → Yalnız I; pool A doğru",
    ),
    "87b1befa-9245-51b0-98c8-087e5eb44561": (
        "unclear",
        "needs_image",
        "f'(x) grafiği üzerinden f artan aralık image-bound",
    ),
    "feca44c9-28c8-5515-9575-fa37a0122b45": (
        "unclear",
        "needs_image",
        "Yay atma K,L,M noktaları image-bound",
    ),
    "155e66de-336f-5ccc-bc62-543b54bacf98": (
        "unclear",
        "needs_image",
        "Pergel-cetvel ABC dik üçgen; AC=r√2 ama r image-bound",
    ),
    "91b73fa1-56a7-57dc-b56d-1c9d085a11ff": (
        "unclear",
        "needs_image",
        "K cismi kaldırma kuvveti; X,Y derinlik image-bound",
    ),
}


def update_tsv(path: Path, verdicts: dict[str, tuple[str, str | None, str]]) -> int:
    """Update SCORING.tsv with verdict/error_type/notes columns."""
    rows = []
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        fieldnames = reader.fieldnames
        for row in reader:
            qid = row.get("id", "")
            if qid in verdicts:
                verdict, error_type, notes = verdicts[qid]
                row["verdict"] = verdict
                row["error_type"] = error_type or ""
                row["notes"] = f"{CLAUDE_TAG}: {notes}"
            rows.append(row)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=fieldnames, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    return len(rows)


def summarize(verdicts: dict[str, tuple[str, str | None, str]], label: str) -> None:
    from collections import Counter

    v_counter = Counter(v[0] for v in verdicts.values())
    e_counter = Counter(v[1] or "none" for v in verdicts.values())
    total = sum(v_counter.values())

    print(f"\n=== {label} (n={total}) ===")
    print("Verdict:")
    for k in ("pass", "fail", "unclear"):
        n = v_counter.get(k, 0)
        pct = 100.0 * n / total if total else 0
        print(f"  {k:10s} {n:3d}  ({pct:.0f}%)")
    print("Error type:")
    for k, n in e_counter.most_common():
        print(f"  {k:25s} {n}")


def main() -> int:
    gold_path = PILOTS_DIR / "20260517_weekly_gold_RAW_SCORING.tsv"
    reject_path = PILOTS_DIR / "20260517_weekly_reject_RAW_SCORING.tsv"

    print(f"[input] {gold_path}")
    print(f"[input] {reject_path}")

    g = update_tsv(gold_path, GOLD_VERDICTS)
    r = update_tsv(reject_path, REJECT_VERDICTS)
    print(f"\n[updated] Gold: {g} satır, Reject: {r} satır")

    summarize(GOLD_VERDICTS, "GOLD POOL (v_safe_for_beta sample)")
    summarize(REJECT_VERDICTS, "REJECT POOL (false-negative check)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
