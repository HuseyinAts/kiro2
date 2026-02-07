---
name: taxonomy-validate
description: Soru metninin Bloom+SOLO+Marzano+Webb DOK etiketlerinin tutarlılığını kontrol eder
user-invocable: true
allowed-tools:
  - Read
  - Bash
---

# Taxonomy Validation Skill

Bu skill, verilen soru metninin çoklu taksonomi etiketlerini doğrular ve tutarlılık raporu oluşturur.

## Kullanım
```bash
/taxonomy-validate <soru_metni_veya_soru_id>
```

## İşlem Adımları

1. **Soru Alma**
   - Metin veya ID ile soru al
   - Mevcut etiketleri çek (varsa)

2. **Bloom Seviyesi Belirleme**
   - backend/services/bloom_taxonomy_classifier.py kullan
   - 6 seviye: hatırlama, anlama, uygulama, analiz, sentez, değerlendirme

3. **SOLO Seviyesi Belirleme**
   - backend/services/taxonomy/solo_classifier.py kullan
   - 5 seviye: ön-yapısal, tek-yapısal, çok-yapısal, ilişkisel, genişletilmiş soyut

4. **Marzano Sistem ve Bilişsel Seviye**
   - backend/services/taxonomy/marzano_classifier.py kullan
   - Sistem: bilgi, zihinsel işlemler, psikomotor
   - Bilişsel: hatırlama, anlama, analiz, bilgi kullanımı

5. **Webb DOK Seviyesi**
   - backend/services/taxonomy/webb_dok_classifier.py kullan
   - 4 seviye: hatırlama, beceri/kavram, stratejik düşünme, genişletilmiş düşünme

6. **Çapraz Doğrulama**
   - backend/services/taxonomy/multi_taxonomy_analyzer.py kullan
   - Tutarlılık matrisi ile skor hesapla
   - Uyumsuzlukları tespit et

7. **Rapor Oluşturma**
   - JSON veya Markdown formatında çıktı

## Çıktı Formatı

```markdown
# Taxonomy Validation Report

## Soru
[Soru metni]

## Analiz Sonuçları

### Bloom Taxonomy
- **Seviye:** Analiz
- **Güven:** 0.85

### SOLO Taxonomy
- **Seviye:** İlişkisel
- **Güven:** 0.78

### Marzano Taxonomy
- **Sistem:** Zihinsel İşlemler
- **Bilişsel Seviye:** Analiz
- **Güven:** 0.82

### Webb DOK
- **Seviye:** 3 (Stratejik Düşünme)
- **Güven:** 0.88

## Tutarlılık Analizi

- **Genel Tutarlılık Skoru:** 0.83 / 1.00
- **Durum:** ✅ Tutarlı

### Detaylı Çapraz Doğrulama

| Karşılaştırma | Beklenen | Gerçek | Uyumlu? |
|---------------|----------|--------|---------|
| Bloom → SOLO | İlişkisel | İlişkisel | ✅ |
| Bloom → Marzano | Analiz | Analiz | ✅ |
| Bloom → Webb DOK | 3 | 3 | ✅ |
| SOLO → Marzano | Analiz | Analiz | ✅ |

## Uyumsuzluklar
[Uyumsuzluk varsa burada listelenir]

## Öneriler
1. [Düzeltme önerisi 1]
2. [Düzeltme önerisi 2]
```

## Tutarlılık Matris Kuralları

### Bloom → SOLO Eşleştirme

| Bloom | Beklenen SOLO |
|-------|---------------|
| Hatırlama | Tek-yapısal |
| Anlama | Çok-yapısal |
| Uygulama | Çok-yapısal / İlişkisel |
| Analiz | İlişkisel |
| Sentez | Genişletilmiş Soyut |
| Değerlendirme | Genişletilmiş Soyut |

### Bloom → Webb DOK Eşleştirme

| Bloom | Beklenen DOK |
|-------|--------------|
| Hatırlama | 1 |
| Anlama | 2 |
| Uygulama | 2 / 3 |
| Analiz | 3 |
| Sentez | 4 |
| Değerlendirme | 4 |

### Tutarlılık Skoru Hesaplama

```python
def calculate_consistency_score(
    bloom: str,
    solo: str,
    marzano: dict,
    webb_dok: int,
) -> float:
    """
    Çoklu taksonomi tutarlılık skoru hesapla.

    Returns:
        0.0-1.0 arası tutarlılık skoru
    """
    matches = 0
    total = 4

    # Bloom → SOLO
    if is_bloom_solo_consistent(bloom, solo):
        matches += 1

    # Bloom → Marzano
    if is_bloom_marzano_consistent(bloom, marzano['cognitive_level']):
        matches += 1

    # Bloom → Webb DOK
    if is_bloom_dok_consistent(bloom, webb_dok):
        matches += 1

    # SOLO → Marzano
    if is_solo_marzano_consistent(solo, marzano['cognitive_level']):
        matches += 1

    return matches / total
```

## Kullanılan Dosyalar

### Backend Services
- `backend/services/bloom_taxonomy_classifier.py` - Bloom sınıflandırıcı
- `backend/services/taxonomy/solo_classifier.py` - SOLO sınıflandırıcı
- `backend/services/taxonomy/marzano_classifier.py` - Marzano sınıflandırıcı
- `backend/services/taxonomy/webb_dok_classifier.py` - Webb DOK sınıflandırıcı
- `backend/services/taxonomy/multi_taxonomy_analyzer.py` - Çapraz doğrulama

### Models
- `backend/models/soru_model.py` - Soru modeli (bloom_level, solo_level vb.)

## Örnek Kullanım

```bash
# Metin ile doğrulama
/taxonomy-validate "Aşağıdaki seçeneklerden hangisi fotosent ezin temel aşamalarından biridir?"

# ID ile doğrulama
/taxonomy-validate --question-id 12345

# JSON çıktı
/taxonomy-validate --format json "Soru metni..."
```

## Hata Durumları

| Hata Kodu | Açıklama | Çözüm |
|-----------|----------|-------|
| TAX_001 | Soru metni boş | Geçerli soru metni gir |
| TAX_002 | Soru ID bulunamadı | Mevcut ID kontrol et |
| TAX_003 | Sınıflandırıcı hatası | Backend loglarını kontrol et |
| TAX_004 | Düşük güven skoru (< 0.5) | Manuel kontrol gerekli |

## Uyarılar

- Tutarlılık skoru < 0.6: ⚠️ Uyumsuzluk var
- Tutarlılık skoru < 0.4: ❌ Ciddi uyumsuzluk
- Güven skoru < 0.5: Manuel kontrol önerilir

## Performans

- Ortalama süre: ~2-3 saniye
- Cache kullanımı: Var (aynı soru tekrar sorulursa)
- API limiti: 100 istek/dakika
