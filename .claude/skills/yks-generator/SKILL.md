---
name: yks-generator
description: YKS/TYT/AYT/YDT formatında soru üretir. IRT parametreleri, ZPD analizi ve Türkçe NLP entegrasyonu ile kaliteli eğitim içeriği oluşturur.
context: fork
agent: turkish-nlp-specialist
model: sonnet
allowed-tools: Read, Grep, Glob, Bash
skills: turkish-nlp, education-algorithms
---

# YKS Soru Üretici: $ARGUMENTS

Bu skill, belirtilen konu için YKS formatında soru üretir.

## Desteklenen Sınav Türleri

| Sınav | Açıklama | Kapsam |
|-------|----------|--------|
| TYT | Temel Yeterlilik Testi | Türkçe, Matematik, Fen, Sosyal |
| AYT-SAY | Sayısal | Matematik, Fizik, Kimya, Biyoloji |
| AYT-EA | Eşit Ağırlık | Matematik, Türk Dili, Tarih, Coğrafya |
| AYT-SÖZ | Sözel | Türk Dili, Tarih, Coğrafya, Felsefe |
| YDT | Yabancı Dil | İngilizce, Almanca, Fransızca |

## Soru Şablonu

```json
{
  "id": "uuid",
  "exam_type": "TYT|AYT-SAY|AYT-EA|AYT-SOZ|YDT",
  "subject": "Matematik",
  "topic": "Fonksiyonlar",
  "subtopic": "Bileşke Fonksiyon",
  "question_text": "Soru metni (LaTeX destekli)",
  "options": {
    "A": "Şık A",
    "B": "Şık B",
    "C": "Şık C",
    "D": "Şık D",
    "E": "Şık E (AYT için)"
  },
  "correct_answer": "B",
  "solution": "Çözüm adımları",
  "irt_parameters": {
    "difficulty": 0.5,        // [-4.0, 4.0]
    "discrimination": 1.2,    // [0.2, 4.0]
    "guessing": 0.2,          // [0.0, 0.35]
    "upper_asymptote": 1.0    // [0.0, 1.0]
  },
  "metadata": {
    "source": "AI-Generated",
    "curriculum_code": "MEB-MAT-9-3.2",
    "cognitive_level": "Uygulama",
    "keywords": ["fonksiyon", "bileşke"],
    "estimated_time_seconds": 120
  }
}
```

## IRT Parametre Kuralları

### Difficulty (Zorluk)
```
-4.0 ← Çok Kolay ← -2.0 ← Kolay ← 0.0 ← Orta → 2.0 → Zor → 4.0 → Çok Zor
```

### Discrimination (Ayırt Edicilik)
```
0.2-0.5: Düşük ayırt edicilik
0.5-1.0: Orta ayırt edicilik
1.0-2.0: İyi ayırt edicilik
2.0-4.0: Çok yüksek ayırt edicilik
```

### Guessing (Tahmin)
```
TYT (4 şık): max 0.25
AYT (5 şık): max 0.20
```

## ZPD (Zone of Proximal Development)

Optimal soru seçimi için:
```
Başarı Olasılığı: %15 - %85 arası
Optimal: %50 civarı
```

## Üretim Protokolü

### Adım 1: Konu Analizi
- MEB müfredatı uyumu kontrolü
- Konu ağacında konum belirleme
- Prerequisite kontrolü

### Adım 2: Soru Tasarımı
- Bloom taksonomisi seviyesi belirleme
- Distraktör (yanlış şık) tasarımı
- Çözüm yolu planlaması

### Adım 3: Türkçe Kalite Kontrolü
- Zemberek ile yazım kontrolü
- Cümle yapısı analizi
- Terminoloji tutarlılığı

### Adım 4: IRT Parametre Tahmini
- Benzer sorularla karşılaştırma
- Zorluk seviyesi belirleme
- Ayırt edicilik tahmini

### Adım 5: Doğrulama
- Çözüm doğruluğu
- Şık tutarlılığı
- Format kontrolü

## Örnek Kullanım

```bash
# Belirli konu
/yks-generator "TYT Matematik - Olasılık - Orta zorluk"

# Zorluk belirterek
/yks-generator "AYT Fizik - Elektrik - difficulty:1.5"

# Çoklu soru
/yks-generator "TYT Türkçe - Paragraf - count:5"

# Belirli cognitive level
/yks-generator "AYT Kimya - Organik - level:Analiz"
```

## Çıktı Formatı

```markdown
## Üretilen Soru

**Sınav:** TYT
**Ders:** Matematik
**Konu:** $ARGUMENTS

### Soru
[Soru metni]

### Şıklar
A) ...
B) ...
C) ...
D) ...

### Doğru Cevap
B

### Çözüm
[Adım adım çözüm]

### IRT Parametreleri
- Zorluk: 0.5 (Orta)
- Ayırt Edicilik: 1.2 (İyi)
- Tahmin: 0.25

### MEB Müfredat Kodu
MEB-MAT-9-3.2
```

## Kalite Kontrol Kuralları

### ✅ KABUL KRİTERLERİ
- Türkçe dilbilgisi hatasız
- Tek doğru cevap var
- Distractörler mantıklı
- IRT parametreleri geçerli aralıkta
- MEB müfredatına uygun

### ❌ RED KRİTERLERİ
- Yazım hatası
- Çoklu doğru cevap
- Anlamsız şık
- IRT parametre ihlali
- Müfredat dışı içerik

## KIRO2 Entegrasyonu

Üretilen sorular:
1. ChromaDB'ye embedding olarak kaydedilir
2. PostgreSQL'e metadata ile eklenir
3. IRT kalibrasyon kuyruğuna girer
4. ZPD analizi için işaretlenir

## MCP Tool Kullanımı

```python
# ChromaDB'ye kaydet
mcp__chromadb__embed_content(content=question_text, metadata=irt_params)

# Kalite doğrulama
mcp__chromadb__verify_question_quality(content=question_text, expected_subject=subject)
```

## Notlar

- Bu skill Sonnet model kullanır
- İzole context'te çalışır
- Türkçe NLP skill'i otomatik yüklenir
- IRT validasyonu zorunludur
