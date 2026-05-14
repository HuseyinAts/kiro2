"""
_apply_C2_scoring.py — Claude session 156 pre-analysis (50 math/geometry questions).
"""

from __future__ import annotations

import csv
from pathlib import Path

PILOTS = Path("C:/Users/husey/kiro2/backend/_pilots")
SRC = PILOTS / "20260515_audit_C2_SCORING.tsv"

SCORING: dict[str, tuple[str, str, str]] = {
    "9fc756a1-7f80-5901-9d63-407848320c97": (
        "fail",
        "incomplete",
        "log b verilmemis, ifade hesaplanamaz",
    ),
    "ebd6e4ba-1ddc-5a5a-9e3d-a483b0742a8f": ("fail", "ocr", "Text cut off (oy...)"),
    "0186e3d9-77bf-5db7-826c-8c104f1b8d1d": (
        "unclear",
        "ocr",
        "Text cut off; g(x) tepe (-4,9) hesap, ama soru ne sorduğu belirsiz",
    ),
    "4b53254d-3b37-5308-8df1-f9116f4db78b": (
        "pass",
        "",
        "a=1 b=2, a+b=3=A dogal okuma",
    ),
    "ad1b8275-205b-5781-b971-52e104ff9305": (
        "fail",
        "wrong_answer",
        "x=33/2 cikar, B=3/2 yanlis (olasi OCR 33/2 -> 3/2)",
    ),
    "a1e83207-eee9-5904-8c82-d1f6e1ef4a7c": (
        "fail",
        "incomplete",
        "Yukarida verilen 5 aci listesi yok",
    ),
    "ed27de1c-df37-5387-aba8-f777d15815d1": (
        "fail",
        "incomplete",
        "f'(3) verilmemis, sadece f(3)=1; chain rule eksik",
    ),
    "204c37e6-da60-5f74-9b76-b3331d9e046d": (
        "fail",
        "wrong_answer",
        "P(x)=5x^2+3 -> der[xP(x^2)]=5, C=9 yanlis (integral x^5 OCR'da x^7 olsa C dogru)",
    ),
    "c45f79fe-dd56-5743-8560-65c7eaef861b": (
        "fail",
        "wrong_answer",
        "4 kok dogrulandi (pi/6, 5pi/6, 7pi/6, 11pi/6); E=8 yanlis",
    ),
    "26335fac-96da-54b2-98a1-5c1742b5b852": ("fail", "ocr", "Text cut off (Bur...)"),
    "593d482b-97bc-52f5-9a13-385f818f80e9": (
        "fail",
        "wrong_answer",
        "Bire bir icin a > -8; smallest int = -7 = B; D=-9 yanlis (overlap)",
    ),
    "8c365bc0-32f0-58f7-af18-7f736ac38ef3": ("fail", "ocr", "Text cut off (sayini...)"),
    "38269b1c-bbbd-58d8-a779-aada25e12b0f": (
        "pass",
        "",
        "Vieta: m=6 n=2, m*n=12=D (m-n notation OCR olasi)",
    ),
    "28a9ac44-bb73-55ed-b42a-03366e5e4786": (
        "fail",
        "wrong_answer",
        "Optimizasyon: a=12/(9+4sqrt(3))=A; E=6/(9+4sqrt(3)) yanlis (tam yarisi)",
    ),
    "64bad36d-4377-5559-8b45-4c8a0a70fe61": (
        "fail",
        "wrong_answer",
        "Q(x)=(x-1)^2(x-2)^2, Q(3)=4, Q(4)=36, P(4)=44=C; E=48 yanlis",
    ),
    "fb09ff13-0ebf-5c6b-b752-e4c1ca9160de": (
        "pass",
        "",
        "Devirli ondalik: 2.1231 < 2.1232 < 2.1233 -> a<b<c=A",
    ),
    "c754c95d-8993-52e9-a0a6-16e2200b95ca": (
        "pass",
        "",
        "YASEMIN 21 kez, 147 harf/6 = 24 parca + 3 harf MIN=C",
    ),
    "9451ced4-3b41-5174-980e-74c396fdfd9c": ("fail", "ocr", "Text cut off (onc...)"),
    "c3fa6f17-48b1-5f6a-b325-fcd802602617": (
        "fail",
        "wrong_answer",
        "2a1+7d=24, 3a1+21d=48 -> a1=8; A=6 yanlis",
    ),
    "e8fdca37-a155-54e8-bee2-730d2e165932": ("unclear", "ocr", "Text cut off (He...)"),
    "a4b29dd0-13d0-505f-9392-455c37b9243e": (
        "unclear",
        "ocr",
        "Tersten okunu cut off; palindrome bilgin sayi mi?",
    ),
    "f4fcc920-214d-52fc-8db0-f2088cfcae1c": (
        "pass",
        "",
        "(sqrt(6)-sqrt(2))(sqrt(6)+sqrt(2)) = 6-2 = 4 = A",
    ),
    "885e5e08-78e6-5ded-a51a-2c2cfaac41dc": (
        "fail",
        "wrong_answer",
        "Domain x>=3, sadece x=3 sifirlar; cozum {3} only; E={3,18} yanlis",
    ),
    "dd302950-5207-56ef-b746-f83d1dec0f6f": (
        "unclear",
        "ocr",
        "S_n=2^(n-1) ile a_n geometrik degil; OCR'da S_n=2^n-1 olabilir, o zaman A=2^(n-1) dogru",
    ),
    "fb9e614e-76fb-5314-bb22-e191621e1606": (
        "fail",
        "incomplete",
        "(x*z)/y orani sorulan ama z tanimsiz",
    ),
    "3ec959c4-0147-53e4-8f93-fe041c88d146": (
        "pass",
        "",
        "Tuz toplam=6+10=16g; 16/100=%16=C",
    ),
    "8a252415-c7b3-51b1-a37d-ee980ece53dc": (
        "fail",
        "wrong_answer",
        "q(p-q+r)=323=17*19; q=17 -> p+q+r=53, q=19 -> 55; D=37 hicbir senaryoda cikmiyor",
    ),
    "46e543ab-2d13-56ce-970b-f9fa42762ce7": (
        "pass",
        "",
        "Reel/nominal = 1.14/1.20 = 0.95; %5 azalis = D",
    ),
    "5794b9d0-c10c-5842-a370-2ebc5c27b605": (
        "fail",
        "wrong_answer",
        "(0,pi/2) cozumsuz; sin a=-3/5 cikar (4. bolge); B=3/4 sign/domain yanlis",
    ),
    "2e4b671c-e6bb-56f5-b337-eadc1db4b4a6": (
        "unclear",
        "ocr",
        "'gercek ve sa...' cut off; III ifade hesap zor",
    ),
    "11049fe5-0af4-5075-b150-1786c9562509": (
        "unclear",
        "ocr",
        "B... cut off; 3.24*10^8 hesap ama option uymuyor",
    ),
    "3d069c33-f540-581a-948a-641fe1ead793": (
        "pass",
        "",
        "Max alan: A=90 + AM-GM (8,8); area=32=D",
    ),
    "c7aa977d-150e-5c1a-a365-5ac16df213a4": (
        "unclear",
        "incomplete",
        "AB=A*B notation muglak; (10-11)+(12-13)+...+(xy)=450 belirsiz",
    ),
    "681ac45c-7d8e-55c2-8799-5ebd74e3395a": (
        "pass",
        "",
        "f'(1)=6+6=12=E (turevin tanim limit'i)",
    ),
    "3296fda3-4057-5056-90fb-bffc7c6010be": (
        "pass",
        "",
        "A subset B degil -> s(A)>=8; max s(B\\A) = 32-8-7 = 17 = D",
    ),
    "7c6391fa-6b65-5afe-8060-9bd822563f57": (
        "pass",
        "",
        "x^3-6x = x(x^2-6); bolum = x*Q(x)+5 = D",
    ),
    "ea011eae-45e3-508a-9d00-b1944369d854": (
        "pass",
        "",
        "Hizlar 8/12 + 9/15 = 19/15; sure=120s; Osman 3/5*120 = 72 = B",
    ),
    "8cd2888c-bab9-5faa-8ed5-ca593efd5911": (
        "unclear",
        "wrong_answer",
        "1<a<b<c<21 asal: 8 sayi -> C(8,3)=56 farkli urun; B=8 ve E=8! optionlari uymuyor",
    ),
    "85e2c969-593e-5737-9987-036d9f457d99": (
        "fail",
        "wrong_answer",
        "ODE: f=-(x^2+x+1), f(1)=-3 (C=0 ile); integral=-7/6 (problemde +7/6 isaret hatasi); E=-2 yanlis",
    ),
    "afbf2550-7616-51ba-afd8-5ed5bf9b0903": (
        "unclear",
        "ocr",
        "ger... cut off; telefon faturasi taahhut hesabi",
    ),
    "25a06185-ab2f-5e71-b2af-9112d1719f1d": (
        "fail",
        "wrong_answer",
        "log 640 = 2k-2m+1; D=1+3m = log 270 (OCR 640<->270 olabilir)",
    ),
    "13c9c9df-c238-548d-9d2c-2e2649205e88": (
        "fail",
        "wrong_answer",
        "f^-1(x)=(x+3)/2; g(u)=8u-13; g(3)=11; E=1 yanlis",
    ),
    "1e746bc5-6280-5313-8492-cdb905ea6f17": (
        "fail",
        "wrong_answer",
        "g'(x)=4x-6 -> g(x)=2x^2-6x+C; f'(t)=g(t)=2x^2-6x+C; A=6x^2+9 yanlis",
    ),
    "1e2d96f1-f7d9-5211-a255-45ea5574e284": (
        "pass",
        "",
        "Yuzey alan 2x: d=a/6, (a-d)/d = 5 = D",
    ),
    "d1ed1e86-126c-5b83-ba9c-87de73c1dcd6": (
        "fail",
        "wrong_answer",
        "1 = 3^(a-1) -> a-1=0 -> a=1; A=11 yanlis",
    ),
    "12c9b206-ef6b-5e16-9a26-dd2e38e655af": (
        "pass",
        "",
        "tan a = 4/3 -> 3-4-5 ucgen -> sin a = 4/5 = C",
    ),
    "e55c126c-a685-5656-a88e-4e434eaff0a2": (
        "fail",
        "wrong_answer",
        "u^2-5u-24=0 -> u=8, x=64 (eger sqrt ile); D=16 plug-in -212 yanlis",
    ),
    "578755e0-de7a-50cd-8922-9cfe33707cec": (
        "unclear",
        "ocr",
        "3. denklem cut off; sembol bulma puzzle",
    ),
    "dd51f5e0-5a97-517e-a2eb-60076502393f": (
        "fail",
        "wrong_answer",
        "real-50<=170<=real+30 -> 140<=x<=220 = E; D=120-200 yanlis",
    ),
    "bffe0c31-1c1b-573b-bef9-05534da4e649": (
        "pass",
        "",
        "I (p iff not p = 0): TRUE, II (iff = and biconditional): TRUE, III (1 iff 0 = 0): TRUE; E hepsi",
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
        print(f"WARNING: {len(missing)} ID mapping eksik:")
        for m in missing:
            print(f"  - {m}")
        return

    with SRC.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerows(rows)

    print(f"[OK] {updated}/50 satir guncellendi")

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
        pct = 100.0 * n / 50
        print(f"  {v:10s} {n:>3d} ({pct:5.1f}%)")

    print("\nError type dagilimi (non-pass):")
    for e, n in sorted(error_count.items(), key=lambda x: -x[1]):
        print(f"  {e:20s} {n:>3d}")


if __name__ == "__main__":
    main()
