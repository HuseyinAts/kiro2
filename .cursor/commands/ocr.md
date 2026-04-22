# OCR — KIRO2 Question OCR Pipeline

KIRO2'nin görüntüden soru çıkarma pipeline'ı: Gemini 2.0 Flash OCR +
Claude Opus vision fallback + Turkish text cleanup + IRT metadata.

## Ne Zaman Kullanılmalı

- Yeni kitap/kaynak eklerken (PDF + soru sayfası tarama)
- Mevcut soru stock'una ek dataset
- YKS önceki yıllar soru bankası import
- Manual input alternatifi (hızlandırıcı)

## Ne Zaman KULLANMA

- Tek soru için (manuel input daha hızlı)
- Yüksek kalite structured data zaten var (JSON/CSV)
- Kopyası çekilmiş netliği düşük görsel (OCR başarısı düşük)

## Pipeline Mimarisi

```
[PDF/Image]
    ↓
[Preprocessing] → resize, contrast, deskew
    ↓
[Gemini 2.0 Flash OCR] → primary, ~$0.25/kitap
    ↓ (düşük güven varsa)
[Claude Opus Vision] → fallback, ~$15/kitap
    ↓
[Turkish NLP Cleanup] → Zemberek + i/ı düzeltme
    ↓
[IRT Parametre Tahmini] → benzer sorularla karşılaştır
    ↓
[PostgreSQL question_bank insert] → is_active=True
    ↓
[ChromaDB embedding] → semantic search için
```

## Kullanım

```
/ocr <input_path> [--model gemini|opus|both] [--dry-run]
```

Örnekler:
- `/ocr uploads/matematik_kitabi_2024.pdf` — default (Gemini)
- `/ocr uploads/tyt_2023_cikmis.pdf --model both` — Gemini + Opus karşılaştırma
- `/ocr uploads/ornek.jpg --dry-run` — DB'ye yazmadan sadece parse

## Agent Protokolü

### Adım 1 — Input Doğrulama

```bash
file "${input_path}"  # gerçekten PDF/image mi?
identify "${input_path}"  # imagemagick ile detaylar
```

Kabul edilen formatlar: PDF, PNG, JPG, TIFF (DPI >= 200 önerilir)

### Adım 2 — Preprocessing

```python
from PIL import Image
from backend.app.services.ocr.preprocess import deskew, enhance_contrast

img = Image.open(input_path)
img = deskew(img)
img = enhance_contrast(img)
img.save(temp_path)
```

### Adım 3 — OCR Çağrısı

Primary: Gemini 2.0 Flash (önerilen — Session pilot testi: 61.3% reliable
ground truth accuracy, $0.25/kitap maliyet)

```python
from backend.app.services.ocr.gemini import gemini_ocr

result = await gemini_ocr(
    image_path=temp_path,
    prompt_template="kiro2_yks_question_v2",
    expected_schema=QuestionSchema,
)
```

Düşük güven skoru (`< 0.7`) → Claude Opus Vision fallback:

```python
if result.confidence < 0.7:
    from backend.app.services.ocr.claude import claude_vision_ocr
    result = await claude_vision_ocr(image_path=temp_path, prior=result)
```

### Adım 4 — Turkish NLP Cleanup

```python
from backend.mcp_servers.zemberek_nlp.cleanup import (
    fix_turkish_chars,  # i/ı düzeltme
    normalize_whitespace,
    fix_ocr_artifacts,  # 0/O, 1/l gibi yaygın hatalar
)

question_text = fix_turkish_chars(result.question_text)
question_text = normalize_whitespace(question_text)
question_text = fix_ocr_artifacts(question_text)
```

UTF-8 NFC normalization ZORUNLU:
```python
import unicodedata
question_text = unicodedata.normalize('NFC', question_text)
```

### Adım 5 — IRT Parametre Tahmini

Yeni soru için başlangıç IRT parametreleri — benzer sorulara göre:

```python
from backend.app.services.irt.estimate_from_similar import estimate_params

irt_params = await estimate_params(
    question_text=cleaned_text,
    subject=detected_subject,
    similar_k=20,  # en yakın 20 soruyla karşılaştır
)
# Returns: {difficulty: 0.3, discrimination: 1.2, guessing: 0.2}
```

Aralık kontrolü (zorunlu):
- difficulty: [-5.0, 4.0]
- discrimination: [0.1, 4.0]
- guessing: [0.0, 0.4]

### Adım 6 — Quality Gate

Kabul kriterleri:
- OCR confidence >= 0.7
- Türkçe karakter doğru (spot check: i/ı, ğ, ş, ç, ö, ü)
- Tek doğru cevap var (multiple choice için)
- IRT parametreleri aralıkta
- Benzer soru yok (duplicate detection, BERTScore < 0.85)

Fail → flag for manual review, DB'ye yazma.

### Adım 7 — Insert (is_active=True)

```python
from backend.app.models.question_bank import QuestionBankItem

q = QuestionBankItem(
    content=cleaned_text,
    subject=detected_subject,
    exam_type=detected_exam_type,  # TYT/AYT UPPERCASE
    options=[...],
    correct_answer=result.correct_answer,
    difficulty=irt_params['difficulty'],
    discrimination=irt_params['discrimination'],
    guessing=irt_params['guessing'],
    source=f"OCR:{input_path.name}",
    is_active=True,
)
db.add(q)
await db.commit()
```

### Adım 8 — ChromaDB Embedding

```python
from backend.mcp_servers.chromadb_mcp import embed_question

await embed_question(
    question_id=q.id,
    content=cleaned_text,
    metadata={
        "subject": q.subject,
        "exam_type": q.exam_type,
        "difficulty": q.difficulty,
    },
)
```

### Adım 9 — Rapor

```markdown
## OCR Pipeline Raporu

**Input:** uploads/matematik_kitabi_2024.pdf (124 sayfa, 480 soru)
**Süre:** 42 dakika
**Maliyet:** $2.15 Gemini Flash + $0 Opus (fallback tetiklenmedi)

### Sonuç
- ✅ 456 soru başarıyla işlendi (% 95)
- ⚠️ 18 soru low confidence → manuel review (flag)
- ❌ 6 soru reject (duplicate, IRT out of range)

### Kategori Dağılımı
- Matematik: 380
- Geometri: 76
- TYT: 320, AYT: 136

### Sonraki Adım
- Manuel review: 18 soru (`flagged/` dizininde)
- IRT kalibrasyonu: 30+ yanıt biriktikten sonra
```

## Maliyet Yönetimi

Session pilot testinde:
- Gemini 2.0 Flash: ~$0.25/kitap (~500 soru), 42.9% blended accuracy, 61.3% on reliable ground truth
- Gemini 2.5 Flash: Daha pahalı, sadece marjinal iyileşme — **önerilmez**
- Claude Opus Vision: ~$15/kitap, fallback için saklı tut

**Hedef:** 120K record (STEM-only), ~$17 toplam maliyet (önceki analiz)

## KIRO2 Sağlık Kontrolü

OCR sonrası her soru için:
- [ ] `is_active=True` set edildi
- [ ] Türkçe karakterler doğru (NFC normalized)
- [ ] IRT parametreleri aralıkta
- [ ] Duplicate değil (BERTScore < 0.85)
- [ ] Source belirtildi (audit trail)
- [ ] ChromaDB embedding oluşturuldu
- [ ] Subject/exam_type doğru UPPERCASE

## Anti-pattern'lar

- **Gemini 2.5 Flash'a geçmek** — 2.0 Flash daha iyi (pilot sonucu)
- **Güven skoruna bakmadan insert** — düşük kalite soru DB kirletir
- **NFC normalization atlama** — i/ı ve kombinasyon karakterleri bozulur
- **IRT parametre default olarak b=0, a=1** — kalibrasyona kadar ZPD yanlış seçer
- **Fallback'i atlamak** — düşük güvenli sorular flagged/'da birikir

## Paralel İşlem

Büyük dataset için parallel OCR:

```
/worktree

Task: 5 farklı kitap OCR + aşağıdaki 5 branch paralel:
- branch/ocr-math-2021, ocr-math-2022, ocr-math-2023, ocr-phys-2023, ocr-chem-2023

Her worktree kendi DB namespace'inde çalışır (KIRO2_WORKTREE env var).
```

## Referans

- `.claude/skills/resume-pipeline/SKILL.md` — pipeline durum takibi
- `.claude/skills/question-quality-multi/SKILL.md` — kalite skorlama
- `.claude/skills/yks-generator/SKILL.md` — OCR'ı takip eden enrichment
- `backend/app/services/ocr/` — kod implementasyonu
- `backend/mcp_servers/zemberek_nlp/` — Türkçe cleanup
