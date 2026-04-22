---
name: yks-generator
description: YKS/TYT/AYT/YDT formatında soru üretir. IRT parametreleri, ZPD analizi, MEB müfredatı uyumu ile kaliteli eğitim içeriği oluşturur.
---

# YKS Soru Üretici

KIRO2'nin core content generation skill'i. Konu verildiğinde YKS formatında
soru üretir, IRT parametreleri kalibrasyona uygun.

## Ne Zaman Yüklenmeli

- Soru üretim pipeline'ı çalıştırılırken
- OCR sonrası soru validate/enrich ederken
- Dataset augmentation yaparken
- YKS content tools geliştirirken

## Desteklenen Sınav Türleri

| Sınav | Kapsam | Şık sayısı |
|---|---|---|
| TYT | Temel Yeterlilik | 4 (A-D) |
| AYT-SAY | Sayısal (Mat/Fiz/Kim/Bio) | 5 (A-E) |
| AYT-EA | Eşit Ağırlık (Mat/Edeb/Tar/Coğ) | 5 (A-E) |
| AYT-SÖZ | Sözel (Edeb/Tar/Coğ/Fel) | 5 (A-E) |
| YDT | Yabancı Dil | 5 (A-E) |

## Soru Şeması

```json
{
  "exam_type": "TYT|AYT-SAY|AYT-EA|AYT-SOZ|YDT",
  "subject": "Matematik",
  "topic": "Fonksiyonlar",
  "subtopic": "Bileşke Fonksiyon",
  "question_text": "LaTeX destekli",
  "options": {"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."},
  "correct_answer": "B",
  "solution": "Adım adım çözüm",
  "irt_parameters": {"difficulty": 0.5, "discrimination": 1.2, "guessing": 0.2},
  "metadata": {
    "curriculum_code": "MEB-MAT-9-3.2",
    "cognitive_level": "Uygulama",
    "estimated_time_seconds": 120
  }
}
```

## IRT Parametre Aralıkları

- Difficulty: [-4.0, 4.0], tipik 0
- Discrimination: [0.2, 4.0], tipik 1.0-1.5
- Guessing: [0.0, 0.35]
  - TYT (4 şık) max 0.25
  - AYT (5 şık) max 0.20

## Üretim Protokolü (5 Adım)

1. **Konu Analizi** — MEB müfredatına uygun mu, prerequisite var mı?
2. **Soru Tasarımı** — Bloom taksonomisi seviyesi, distraktör tasarımı
3. **Türkçe Kalite** — Zemberek ile yazım + terminoloji tutarlılığı
4. **IRT Parametre Tahmini** — Benzer sorularla karşılaştırma
5. **Doğrulama** — Tek doğru cevap, şık tutarlılığı, format

## KABUL vs RED

**KABUL:**
- Türkçe dilbilgisi hatasız
- Tek doğru cevap
- Mantıklı distraktör
- IRT aralığında
- MEB müfredatına uygun

**RED:**
- Yazım hatası
- Çoklu doğru cevap
- Anlamsız şık
- IRT parametre ihlali
- Müfredat dışı

## KIRO2 Pipeline Entegrasyonu

Üretilen soru:
1. ChromaDB'ye embed olarak kaydedilir
2. PostgreSQL `question_bank` tablosuna yazılır (Dual Table Trap: `questions` DEĞIL)
3. IRT kalibrasyon kuyruğuna girer
4. ZPD analizi için işaretlenir

## Detaylı Rehber

Full şablon, MCP tool kullanımı, örnek komutlar:
- `.claude/skills/yks-generator/SKILL.md`
- `.cursor/skills/education-algorithms/SKILL.md` (IRT/ZPD sınırları)
- `.cursor/skills/turkish-nlp/SKILL.md` (dil kontrolü)
