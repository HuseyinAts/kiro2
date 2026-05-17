#!/usr/bin/env python3
"""
Faz 6.6 — Reject pile audit verdict mapping (100 sample).

Claude text-only scoring. LLM-CIRCULAR RISK: bu scoring filter'ı
türeten LLM ile aynı. Beta student feedback ile cross-check zorunlu.

KEY FINDING:
  - R1 false-negative rate: 12/50 = 24% (W20 sample %10'un üstünde)
  - R2 false-negative rate: 47/50 = 94% (sürpriz — single-subject Aromat correct)
  - R2 sadece "Model Sorular" + "Fen Bilimleri" multi-disiplin volumlere uygulanmalıydı.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
PILOTS_DIR = PROJECT_ROOT / "backend" / "_pilots"
CLAUDE_TAG = "claude-text-faz-6-6"


# ============================================================================
# R1 (legacy_v3 mass reject) — 50 sample verdicts
# ============================================================================
R1_VERDICTS = {
    "bf43b1c4-68e3-53d4-bce7-851359f95580": (
        "pass",
        "false_negative",
        "Balkan Antantı sorusu well-formed; EDEBIYAT tag yanlış (içerik TARIH) ama R1 mass reject yine de yanlış",
    ),
    "b92d8898-7f40-5d24-bcf1-3edf9d8fd474": (
        "fail",
        "incomplete_text",
        "x+y=10 tek kısıt ile x²+y² belirsiz; soru ifadesi eksik",
    ),
    "70906336-53c5-5ff3-9356-96f32c0ebb21": (
        "pass",
        "false_negative",
        "Osmanlı borçlar TARIH; well-formed, '1.' OCR prefix",
    ),
    "7f344fd9-99f3-567e-b140-c38407442616": (
        "fail",
        "incomplete_text",
        "Soru kalıbı eksik, options '10 Arı' anlamsız",
    ),
    "f19d0476-6059-5901-bfae-c4420a2e4e06": (
        "unclear",
        "ambiguous_text",
        "Simetrik ekseni belirsiz; (x+1)²→(-x+1)²=A doğru ama soru eksik",
    ),
    "c6eb2b96-8028-503d-bd05-dca404c86c9d": (
        "fail",
        "incomplete_text",
        "Meta-text 'yanlış sonuç veren soru' garbage",
    ),
    "e468b89d-6f09-50ce-b01b-2eeeb57efee4": (
        "pass",
        "false_negative",
        "O2/H2S mol karşılaştırma; eşit ağırlık→daha küçük M daha fazla mol=O2(A); doğru",
    ),
    "96a0304f-06e6-5b92-9cef-8f7da9ee44d9": (
        "fail",
        "low_quality",
        "a+b=c, a-b=d, a+b? trivial; gerçek YKS değil",
    ),
    "d110df81-de36-5869-b50d-51a5f7eaa9d8": (
        "fail",
        "wrong_answer",
        "204/10=20.4 tam sayı değil; cevap mantıksız",
    ),
    "2afe1f46-f6d5-559e-8cbd-cfd7b86abb64": (
        "unclear",
        "wrong_topic",
        "KIMYA tag elektrik tüketim grafik = wrong_topic + image-bound",
    ),
    "a8e7733b-79e3-5b69-aa19-df15131afb30": (
        "fail",
        "wrong_topic",
        "KIMYA tag polinom grafik = MATEMATIK content; wrong_topic",
    ),
    "ac60eb37-8f8b-5fc9-92c9-6fc1ed9767cf": (
        "unclear",
        "needs_image",
        "GENEL grafik image-bound",
    ),
    "ee7c124a-e0ac-5e9b-bcac-257a6314a4eb": (
        "unclear",
        "solution_leak_suspect",
        "Edebiyat Sokagi paragraph well-formed ama solution leak risk",
    ),
    "6946b31e-633a-5e27-9acf-5367e8bd5781": (
        "pass",
        "false_negative",
        "Kevlar polimer well-formed YKS soru; pool C=I,II,III doğru",
    ),
    "92c98b7b-e24e-5050-b121-4b099406b0d4": (
        "fail",
        "wrong_topic",
        "Aromat TURKCE tag, content MATEMATIK + nonsense",
    ),
    "c423b8cb-3be0-50d6-8740-bf2f8cbda94e": (
        "fail",
        "incomplete_text",
        "ÖRNEK + 'öğrenci numarası a*b²' text garbled",
    ),
    "3fe64080-0593-5fc5-aac1-577d2577c5b5": (
        "fail",
        "wrong_answer",
        "Trapez alan=(10+14)/2*8=96; pool B=50 yanlış",
    ),
    "1dc3ccd8-73a9-510f-9e74-e3719efb5f35": (
        "fail",
        "wrong_topic",
        "TARIH tag, komşu açılar MATEMATIK content",
    ),
    "8672c1d6-a7b7-55fe-a3ea-4951b1079d4a": (
        "unclear",
        "needs_image",
        "f(a) sıralama grafik image-bound",
    ),
    "9529aa96-e153-5fa3-9da5-d8a7fbdcd81f": (
        "fail",
        "other",
        "'Amerikan Bay 5 ayakir' nonsense AI",
    ),
    "9e64e2ab-be8f-53e6-b490-4b98cf549fbd": (
        "fail",
        "other",
        "'1923 Ankara Savaşı Demokrat Parti' anakronizm",
    ),
    "af076833-3b27-5c53-a0f0-0f7d132d7e27": (
        "unclear",
        "needs_image",
        "Renkli bölge alanları image-bound",
    ),
    "2b5e362c-787e-5fd0-9f09-c873f829fbba": (
        "unclear",
        "needs_image",
        "ABC/KLM üçgen kümeleri image-bound",
    ),
    "f766cb2a-e32b-5a23-842a-06b53b51db18": (
        "fail",
        "other",
        "'Sarımsık kökleri 50kg' nonsense",
    ),
    "84df60fe-1561-5ae1-a92a-9cedec7fe871": (
        "pass",
        "false_negative",
        "arctan toplamı π well-known trig; well-formed YKS-style",
    ),
    "31d435e7-c34a-5d78-8c1c-e5a20ad873a8": (
        "fail",
        "wrong_answer",
        "Tuzlu su+sıcaklık+sabun: I✓ II✓ III✗ → I,II=A; pool D=Yalnız I yanlış",
    ),
    "a950fb0f-4017-588b-a9a0-594e960e708f": (
        "pass",
        "false_negative",
        "İyon uygarlığı Batı Anadolu=İzmir(B); well-formed soru",
    ),
    "df0fa333-79e5-577d-8454-03cff9e71819": (
        "fail",
        "duplicate_options",
        "Tüm options 'Döngü' duplicate",
    ),
    "a083ffde-143f-5d64-8e23-cd8d37719c28": (
        "fail",
        "low_quality",
        "1+1=2 trivial; gerçek YKS değil",
    ),
    "0a1238a6-8716-5236-a572-ed81861bd14e": (
        "fail",
        "duplicate_options",
        "Aromat options 'Bir öğrenci biri' duplicate",
    ),
    "078a2288-eb91-5d1f-b790-7205040e5329": (
        "fail",
        "incomplete_text",
        "'polinomelik sayı' anlamsız jargon",
    ),
    "b96e845e-d211-59dc-a3b4-43e3adf6c52a": (
        "pass",
        "false_negative",
        "Amerikan romanı paragraf well-formed; yazarlık hakları tarihçesi",
    ),
    "3ad9fc0f-ec37-505b-97e4-6985b5005ed7": (
        "pass",
        "false_negative",
        "Haçlı Seferleri harita; SOSYAL well-formed",
    ),
    "c6052578-b3a2-5094-acb8-cfc04174232a": (
        "unclear",
        "needs_image",
        "Akdeniz/savan iklim haritası image-bound",
    ),
    "972d7e88-adbe-51be-8126-feac195939f2": (
        "fail",
        "incomplete_text",
        "'Aşağıdaki fonksiyonun grafiğini çiziniz' soru değil",
    ),
    "679eed8c-a77b-56a0-aa1a-4eb7fd6641eb": (
        "fail",
        "wrong_answer",
        "I endo ✓, II exo (40kJ açığa), III endo ✓ → I,III=D; pool C=I,II yanlış",
    ),
    "c65de086-bd5c-56e1-aa4d-2bcffa31886f": (
        "fail",
        "incomplete_text",
        "'o ekseni ile teşet eğimli görsel' OCR garbled",
    ),
    "1e2ad5cc-1b8c-5b9a-b438-54a5d1c0046e": (
        "fail",
        "low_quality",
        "'100 eşit parçadan üçgen köşesinden 2 doğru parçası' anlamsız",
    ),
    "10bceaae-cf43-5ac3-937d-f29c7142c2be": (
        "pass",
        "false_negative",
        "5-12-13 Pisagor üçgen alan=30=A; well-formed; soru basit ama doğru",
    ),
    "0bd297be-92a5-53c1-95f6-97b02e7b6499": (
        "fail",
        "wrong_topic",
        "KIMYA tag dikdörtgen koordinat MATEMATIK; ifade eksik",
    ),
    "ccbdd71b-9d21-5bcd-b63f-58e02bd0c42c": (
        "fail",
        "low_quality",
        "'magnezyum atom büyük yaptık elektron?' pseudoscience",
    ),
    "6d4fbf91-af5e-520d-a83e-ce4b612c57b5": (
        "fail",
        "wrong_answer",
        "an=3n+1: a1+a2+a3=4+7+10=21; pool C=14 yanlış (options'da yok)",
    ),
    "3a7cb794-6abe-589d-87ef-e31245077971": (
        "fail",
        "incomplete_text",
        "Soru ifadesi yok, sadece konu adı",
    ),
    "27d66c80-5696-5a45-9d7a-abc5321d382c": (
        "fail",
        "wrong_topic",
        "FIZIK tag dikdörtgen geometri MATEMATIK content",
    ),
    "e711f669-4d95-5968-bc99-9757c5c0d58d": (
        "fail",
        "incomplete_text",
        "ABCDEF pentagram 6 köşe + tutarsız uzaklık verileri, anlamsız",
    ),
    "9caf4096-88f6-5f87-88c6-c1442322b56a": (
        "pass",
        "false_negative",
        "Kubilay Çıtak haberi + ödev davranışı well-formed felsefe sorusu",
    ),
    "aed55d8f-9d1d-5352-950d-b905b54b22a1": (
        "pass",
        "false_negative",
        "Ayaklı kütüphane paragraf well-formed yorum sorusu",
    ),
    "d8dddc6c-28f0-539a-8a48-7bdeb793d5c5": (
        "unclear",
        "ambiguous_text",
        "Organik kimya yapı listesi vs option dien adlandırma uyumsuz",
    ),
    "57d8d114-79ec-572e-af9b-2efc9411fb81": (
        "unclear",
        "needs_image",
        "'Çizilen grafik hangi fonksiyon' image-bound",
    ),
    "01c019eb-d6f6-5138-80a1-cd57fb19116d": (
        "pass",
        "false_negative",
        "Kediler evcilleştirme paragraf well-formed",
    ),
}


# ============================================================================
# R2 (Aromat wrong_topic) — 50 sample verdicts
# ============================================================================
# CRITICAL FINDING: Single-subject Aromat books (Matematik, Fizik) labels DOĞRU.
# R2 sadece 'Model Sorular' + 'Fen Bilimleri Net 30' multi-disiplin volumlere
# uygulanmalıydı. Şu an %94 false-negative.
R2_VERDICTS = {
    "7f369c6d-fae6-5ef6-bd67-520fad96038f": (
        "pass",
        "false_negative",
        "Aromat Matematik kitabı, MATEMATIK tag DOĞRU; futbol parabol soru well-formed",
    ),
    "a9e8a622-ded3-5103-b681-c2f79dfbb7c8": (
        "pass",
        "false_negative",
        "Aromat Ayt Matematik, MATEMATIK tag DOĞRU; dizi pozitif terim soru",
    ),
    "b073670e-a055-55b0-8fd7-6aabd8b66dca": (
        "fail",
        "wrong_topic",
        "Aromat Tyt Sosyal Bilimler Model Sorular: KIMYA tag content COGRAFYA(harita seli) → wrong_topic CONFIRMED",
    ),
    "57429cc7-f13d-59f8-9a27-db9bbf1916e6": (
        "pass",
        "false_negative",
        "Aromat Tyt Fizik, FIZIK tag DOĞRU; kafes kuşu basınç well-formed",
    ),
    "ce09d121-62b2-550c-a465-907bb47d1149": (
        "pass",
        "false_negative",
        "Aromat Tyt Fizik, FIZIK tag DOĞRU; portakal yoğunluk well-formed",
    ),
    "3cb94f32-bcfd-516c-b79f-980de39efbaa": (
        "pass",
        "false_negative",
        "Aromat Ayt Matematik, MATEMATIK tag DOĞRU; birim fonksiyon noktalar",
    ),
    "1e35b74b-60f2-5648-bebc-8dd6c7a68d1f": (
        "pass",
        "false_negative",
        "Aromat Fen Bilimleri KIMYA tag, content KIMYA (entalpi) DOĞRU",
    ),
    "e99054c5-be42-596f-b113-e6776dbcf3a7": (
        "pass",
        "false_negative",
        "Aromat Tyt Fizik, FIZIK tag DOĞRU; motor güç well-formed",
    ),
    "f775b906-e6d2-5ed5-ab48-4a55b9b7bc39": (
        "pass",
        "false_negative",
        "Aromat Fen Bilimleri Model Sorular FIZIK tag DOĞRU (AC devre); not multi-disp content",
    ),
    "1d570564-40ab-5fb5-bbcd-6ec996e229c4": (
        "pass",
        "false_negative",
        "Aromat Tyt Matematik Net 30, MATEMATIK tag DOĞRU; mantık önerme well-formed",
    ),
    "de364d25-73fb-524f-a990-e861f98959bf": (
        "fail",
        "wrong_topic",
        "Aromat Fen Bilimleri KIMYA tag content BIYOLOJI (dolaşım); wrong_topic",
    ),
    "4c0d5f4d-593e-5cd8-bdde-858bafdc3893": (
        "pass",
        "false_negative",
        "Aromat Ayt Fizik, FIZIK tag DOĞRU; dişli oran well-formed",
    ),
    "fa47fb7b-cb71-5060-879a-14234b4177b5": (
        "pass",
        "false_negative",
        "Aromat Tyt Fizik, FIZIK tag DOĞRU; pusula+pil well-formed",
    ),
    "9e7ef978-7931-5e1a-8221-cc265f976ec2": (
        "pass",
        "false_negative",
        "Aromat Tyt Fizik, FIZIK tag DOĞRU; su damlası enerji",
    ),
    "635c250c-add8-5759-92eb-f84106f3ec6c": (
        "pass",
        "false_negative",
        "Aromat Ayt Matematik, MATEMATIK tag DOĞRU; integral öteleme alan",
    ),
    "b3cd58c4-3acf-5fd5-90b8-5f18b7e2e419": (
        "pass",
        "false_negative",
        "Aromat Matematik, MATEMATIK tag DOĞRU; lego desenleri kombinatorik",
    ),
    "3387ce7b-c741-5150-9d5b-11238f99a092": (
        "pass",
        "false_negative",
        "Aromat Tyt Fizik, FIZIK tag DOĞRU; çukur ayna görüntü",
    ),
    "ef4540a2-ad6d-56b3-a59b-bcc61ba16182": (
        "pass",
        "false_negative",
        "Aromat Ayt Fizik, FIZIK tag DOĞRU; fotoelektrik well-formed",
    ),
    "0d3d7342-2de3-52d5-b1f8-5b92844d23d6": (
        "pass",
        "false_negative",
        "Aromat Fen Bilimleri FIZIK tag content FIZIK (patlama momentum) DOĞRU",
    ),
    "2f5945df-a7e4-5496-a102-639d36aaaf73": (
        "pass",
        "false_negative",
        "Aromat Ayt Fizik, FIZIK tag DOĞRU; momentum çarpışma",
    ),
    "6d3257eb-6eae-57b2-bb40-60a3dc3fe20c": (
        "pass",
        "false_negative",
        "Aromat Ayt Fizik, FIZIK tag DOĞRU; ışık girişim deseni",
    ),
    "3eea4f81-714b-5baa-bae9-f5be16dc20ce": (
        "pass",
        "false_negative",
        "Aromat Matematik, MATEMATIK tag DOĞRU; kitap dağıtım problem",
    ),
    "341bdce2-b024-52a9-b659-acf953934ba5": (
        "pass",
        "false_negative",
        "Aromat Matematik, MATEMATIK tag DOĞRU; hedef tahtası puan",
    ),
    "f2ad440f-960f-55d4-8eb3-18f6c7d0f668": (
        "pass",
        "false_negative",
        "Aromat Tyt Fizik, FIZIK tag DOĞRU; kırılma indisi",
    ),
    "e4b39b62-9059-51d7-8c6f-3008f79a6dc6": (
        "pass",
        "false_negative",
        "Aromat Matematik, MATEMATIK tag DOĞRU; Venn şeması çokgen",
    ),
    "48733191-91b8-58f8-96ba-6220118b4e69": (
        "pass",
        "false_negative",
        "Aromat Tyt Türkçe, TURKCE tag DOĞRU; bağlaç/edat well-formed",
    ),
    "e39cedc8-9ed8-54d8-989c-c37c3bb9f3fd": (
        "pass",
        "false_negative",
        "Aromat Ayt Matematik, MATEMATIK tag DOĞRU; integral A1:A2:A3 oran",
    ),
    "a0c6269c-c932-5cae-b2d4-8de365aaa5de": (
        "pass",
        "false_negative",
        "Aromat Ayt Fizik, FIZIK tag DOĞRU; patlama parça momentum",
    ),
    "dbc9d901-6e6b-57d9-9f25-3900266d5244": (
        "pass",
        "false_negative",
        "Aromat Ayt Fizik, FIZIK tag DOĞRU; harmonik hareket",
    ),
    "667364b2-da14-580a-a947-a9c5c64cb985": (
        "pass",
        "false_negative",
        "Aromat Ayt Fizik, FIZIK tag DOĞRU; Doppler well-formed",
    ),
    "23bb2864-ef38-55cc-adc4-24d39b5e03ac": (
        "pass",
        "false_negative",
        "Aromat Ayt Fizik, FIZIK tag DOĞRU; bisiklet noktalar hız",
    ),
    "bf9e5fcd-5b4d-5214-9cbf-eeb2afd18cdc": (
        "pass",
        "false_negative",
        "Aromat Fen Bilimleri Net 30 KIMYA tag content KIMYA (VSEPR) DOĞRU",
    ),
    "98f00dd5-29c2-5acf-86a7-62eb6f418ae9": (
        "pass",
        "false_negative",
        "Aromat Fen Bilimleri KIMYA tag content KIMYA (alkin Tollens) DOĞRU",
    ),
    "5d2f68d5-7659-5a3a-a7a5-6099e784f33b": (
        "pass",
        "false_negative",
        "Aromat Paragraf TURKCE tag DOĞRU; otobüs paragrafı",
    ),
    "0f760b9d-743e-57e8-9682-4ce0c2a088f6": (
        "pass",
        "false_negative",
        "Aromat Tyt Fizik, FIZIK tag DOĞRU; iş tanımı",
    ),
    "6207a95a-a4b2-520b-9aed-44f6adcb55c2": (
        "pass",
        "false_negative",
        "Aromat Matematik, MATEMATIK tag DOĞRU; ardışık sayı dizilim",
    ),
    "7a1d9f90-08b8-51dd-b4dc-f7912b2d8392": (
        "pass",
        "false_negative",
        "Aromat Ayt Matematik, MATEMATIK tag DOĞRU; ekstremum teğet uzaklık",
    ),
    "9a623d3a-ff92-568c-82fe-41fa083327af": (
        "pass",
        "false_negative",
        "Aromat Ayt Fizik, FIZIK tag DOĞRU; ivme kütle değişim",
    ),
    "f5478636-19a8-5b61-82e8-2e706dd5100c": (
        "pass",
        "false_negative",
        "Aromat Ayt Fizik, FIZIK tag DOĞRU; merkezi esnek çarpışma",
    ),
    "930ef9ea-4c49-5575-8962-14ac45a6d20c": (
        "pass",
        "false_negative",
        "Aromat Matematik, MATEMATIK tag DOĞRU; seçim oy yüzde",
    ),
    "0ce25da7-9df0-5dce-b674-bf34a473cea1": (
        "pass",
        "false_negative",
        "Aromat Ayt Matematik, MATEMATIK tag DOĞRU; polinom bölünebilirlik",
    ),
    "83894688-fae1-5a2b-bf56-419df77304b5": (
        "fail",
        "wrong_topic",
        "Aromat Fen Bilimleri Model Sorular Net 30 KIMYA tag content BIYOLOJI (fermantasyon); wrong_topic",
    ),
    "c75159a0-750a-544f-afe2-e61b1efc43c2": (
        "pass",
        "false_negative",
        "Aromat Tyt Fizik, FIZIK tag DOĞRU; elektromıknatıs uygulamalar",
    ),
    "bc9c5592-ddb6-58fc-91be-b15e9a9e8cc1": (
        "pass",
        "false_negative",
        "Aromat Tyt Fizik, FIZIK tag DOĞRU; yay yansıma",
    ),
    "a7f13f6e-d994-5a46-82bd-0fb677721fc3": (
        "pass",
        "false_negative",
        "Aromat Fen Bilimleri Model Sorular FIZIK tag content FIZIK (elektrik alan) DOĞRU",
    ),
    "ce3ce342-eb2b-5448-b691-14af9174c53c": (
        "pass",
        "false_negative",
        "Aromat Ayt Fizik, FIZIK tag DOĞRU; açısal momentum",
    ),
    "ad06598b-4681-564a-bbe7-f520bb19bfeb": (
        "pass",
        "false_negative",
        "Aromat Ayt Fizik, FIZIK tag DOĞRU; yay enerji P,R",
    ),
    "48c61b1c-767b-5189-8880-acff557dd7a9": (
        "pass",
        "false_negative",
        "Aromat Fen Bilimleri Model Sorular BIYOLOJI tag content BIYOLOJI (östrojen) DOĞRU",
    ),
    "98870f9e-9d03-5d9e-8745-6a0bb40a382b": (
        "pass",
        "false_negative",
        "Aromat Tyt Fizik, FIZIK tag DOĞRU; eş değer direnç",
    ),
    "c4365a19-e881-5959-992e-f873575ba176": (
        "pass",
        "false_negative",
        "Aromat Matematik, MATEMATIK tag DOĞRU; memur maaş tablo",
    ),
}


def update_tsv(path: Path, verdicts: dict) -> int:
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


def summarize_by_rule() -> None:
    from collections import Counter

    for rule, verdicts in [("R1_legacy_v3", R1_VERDICTS), ("R2_aromat", R2_VERDICTS)]:
        v_counter = Counter(v[0] for v in verdicts.values())
        e_counter = Counter(v[1] or "none" for v in verdicts.values())
        total = sum(v_counter.values())
        print(f"\n=== {rule} (n={total}) ===")
        print("Verdict:")
        for k in ("pass", "fail", "unclear"):
            n = v_counter.get(k, 0)
            pct = 100.0 * n / total if total else 0
            print(f"  {k:10s} {n:3d}  ({pct:.0f}%)")
        fn = v_counter.get("pass", 0)
        print(f"  FALSE-NEGATIVE rate: {fn}/{total} = {100.0 * fn / total:.1f}%")
        print("Error type:")
        for k, n in e_counter.most_common():
            print(f"  {k:25s} {n}")


def main() -> int:
    path = PILOTS_DIR / "20260517_faz_6_6_reject_audit_RAW.tsv"
    print(f"[input] {path}")

    # Merge both dicts
    combined = {**R1_VERDICTS, **R2_VERDICTS}
    n = update_tsv(path, combined)
    print(f"[updated] {n} satır")

    summarize_by_rule()

    # Overall
    total_pass = sum(1 for v in combined.values() if v[0] == "pass")
    total_fail = sum(1 for v in combined.values() if v[0] == "fail")
    total_unclear = sum(1 for v in combined.values() if v[0] == "unclear")
    n_total = len(combined)
    print(f"\n=== OVERALL (n={n_total}) ===")
    print(
        f"  pass (false-negative): {total_pass}/{n_total} = {100.0 * total_pass / n_total:.1f}%"
    )
    print(
        f"  fail (confirmed):      {total_fail}/{n_total} = {100.0 * total_fail / n_total:.1f}%"
    )
    print(
        f"  unclear:               {total_unclear}/{n_total} = {100.0 * total_unclear / n_total:.1f}%"
    )

    # Population-weighted estimate
    r1_fn = sum(1 for v in R1_VERDICTS.values() if v[0] == "pass") / len(R1_VERDICTS)
    r2_fn = sum(1 for v in R2_VERDICTS.values() if v[0] == "pass") / len(R2_VERDICTS)
    weighted = (r1_fn * 18397 + r2_fn * 2932) / 21329
    estimated_lost = int(weighted * 21329)
    print("\n=== POPULATION-WEIGHTED ESTIMATE ===")
    print(
        f"  R1 FN rate: {r1_fn * 100:.1f}% × 18,397 = {int(r1_fn * 18397):,} lost good"
    )
    print(f"  R2 FN rate: {r2_fn * 100:.1f}% × 2,932 = {int(r2_fn * 2932):,} lost good")
    print(f"  Weighted FN rate: {weighted * 100:.1f}%")
    print(
        f"  Estimated TOTAL LOST: ~{estimated_lost:,} good questions (out of 21,329 rejected)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
