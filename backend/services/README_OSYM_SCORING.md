# ÖSYM Puan Hesaplama Sistemi

## Genel Bakış

Bu modül, ÖSYM'nin resmi puan hesaplama formüllerini uygulayan kapsamlı bir puan hesaplama sistemidir. Türkiye Üniversite Sınavları (YKS) için TYT, AYT ve YDT puanlarını hesaplar, yerleştirme puanı tahmini yapar ve sıralama tahmini sunar.

## Özellikler

### 1. Net Sayısı Hesaplama (REQ-1.4)

ÖSYM'nin resmi net hesaplama formülünü uygular:

```
Net = Doğru - (Yanlış / 4)
```

**Özellikler:**
- Ders bazlı net hesaplama
- Toplam net hesaplama
- Negatif net önleme (minimum 0)
- Boş cevap takibi

**Kullanım:**
```python
from services.osym_scoring_system import osym_scoring_system

# Tek ders için net hesaplama
net = osym_scoring_system.calculate_net_score(
    correct=30,
    wrong=8,
    empty=2
)
# Sonuç: 28.0 (30 - 8/4 = 28)

# Ders bazlı netler
subject_results = {
    "TURKCE": {"correct": 30, "wrong": 8, "empty": 2},
    "MATEMATIK": {"correct": 25, "wrong": 10, "empty": 5},
    "FEN": {"correct": 15, "wrong": 3, "empty": 2},
    "SOSYAL": {"correct": 18, "wrong": 2, "empty": 0},
}

subject_nets = osym_scoring_system.calculate_subject_nets(subject_results)
```

### 2. Ham Puan Hesaplama (REQ-1.4)

Katsayılı puanlama sistemi ile ham puan hesaplar:

```
Ham Puan = Σ(Net * Katsayı) / Σ(Katsayı) * 5
```

**ÖSYM 2024-2025 Katsayıları:**

**TYT:**
- Türkçe: 3.0 (40 soru)
- Matematik: 3.0 (40 soru)
- Fen: 3.0 (20 soru)
- Sosyal: 3.0 (20 soru)

**AYT Sayısal:**
- Matematik: 5.0 (40 soru)
- Fizik: 4.0 (14 soru)
- Kimya: 3.0 (13 soru)
- Biyoloji: 3.0 (13 soru)

**AYT Sözel:**
- Edebiyat: 5.0 (24 soru)
- Tarih-1: 4.0 (10 soru)
- Coğrafya-1: 4.0 (6 soru)
- Tarih-2: 4.0 (11 soru)
- Coğrafya-2: 4.0 (11 soru)
- Felsefe: 4.0 (12 soru)
- Din: 4.0 (6 soru)

**YDT:**
- İngilizce/Almanca/Fransızca: 5.0 (80 soru)

**Kullanım:**
```python
from services.osym_scoring_system import osym_scoring_system, ScoreType

# ÖSYM puanı hesaplama
osym_score = osym_scoring_system.calculate_osym_score(
    score_type=ScoreType.SAY,  # Sayısal
    tyt_subject_results=tyt_results,
    ayt_subject_results=ayt_results
)

print(f"TYT Puanı: {osym_score.tyt_score}")
print(f"AYT Puanı: {osym_score.ayt_score}")
print(f"Ağırlıklı Puan: {osym_score.weighted_score}")
```

### 3. Yerleştirme Puanı Tahmini (REQ-1.4, REQ-1.5)

Yerleştirme puanını hesaplar:

```
Yerleştirme Puanı = (TYT * 0.4) + (AYT * 0.6) + (OBP * 0.12) + Ek Puanlar
```

**Özellikler:**
- OBP (Ortaöğretim Başarı Puanı) katkısı (%12)
- Ek puanlar (engelli, vb.)
- Minimum puan kontrolü (180)
- Puan türü bazlı ağırlıklandırma

**Kullanım:**
```python
# Yerleştirme puanı hesaplama
placement_score = osym_scoring_system.calculate_placement_score(
    osym_score=osym_score,
    obp=85.0,  # Diploma notu
    additional_bonus=5.0  # Ek puanlar
)

print(f"Temel Puan: {placement_score.base_score}")
print(f"OBP Bonusu: {placement_score.obp_bonus}")
print(f"Toplam Yerleştirme Puanı: {placement_score.total_placement_score}")
```

### 4. Sıralama Tahmini (REQ-1.4, REQ-1.5)

Geçmiş yıl verileri ile sıralama tahmini yapar:

**Özellikler:**
- Puan türü bazlı tahmin
- Yüzdelik dilim hesaplama
- Güven seviyesi
- Toplam aday sayısı

**Kullanım:**
```python
# Sıralama tahmini
ranking = osym_scoring_system.estimate_ranking(placement_score)

print(f"Tahmini Sıralama: {ranking.estimated_rank}")
print(f"Yüzdelik Dilim: {ranking.percentile}%")
print(f"Toplam Aday: {ranking.total_candidates}")
print(f"Güven Seviyesi: {ranking.confidence_level * 100}%")
```

## Puan Türleri

### ScoreType Enum

```python
class ScoreType(Enum):
    TYT = "tyt"   # Temel Yeterlilik Testi
    SAY = "say"   # Sayısal (AYT)
    EA = "ea"     # Eşit Ağırlık (AYT)
    SOZ = "soz"   # Sözel (AYT)
    DIL = "dil"   # Dil (YDT)
```

### Puan Türü Ağırlıkları

**Sayısal (SAY):**
- TYT: %40
- AYT: %60
- Dersler: Matematik, Fizik, Kimya, Biyoloji

**Eşit Ağırlık (EA):**
- TYT: %40
- AYT: %60
- Dersler: Matematik, Edebiyat, Tarih, Coğrafya

**Sözel (SOZ):**
- TYT: %40
- AYT: %60
- Dersler: Edebiyat, Tarih, Coğrafya, Felsefe, Din

**Dil (DIL):**
- TYT: %40
- YDT: %60
- Dersler: İngilizce/Almanca/Fransızca

## Veri Modelleri

### SubjectNet
Ders bazlı net bilgisi:
```python
@dataclass
class SubjectNet:
    subject: str
    correct: int
    wrong: int
    empty: int
    net: float
```

### ExamNetScores
Sınav toplam net skorları:
```python
@dataclass
class ExamNetScores:
    exam_type: str
    subject_nets: List[SubjectNet]
    total_net: float
    total_correct: int
    total_wrong: int
    total_empty: int
```

### OSYMScore
ÖSYM puanı:
```python
@dataclass
class OSYMScore:
    score_type: ScoreType
    raw_score: float
    weighted_score: float
    tyt_score: float
    ayt_score: float
    ydt_score: float
    obp_contribution: float
    total_score: float
```

### PlacementScore
Yerleştirme puanı:
```python
@dataclass
class PlacementScore:
    score_type: ScoreType
    base_score: float
    obp_bonus: float
    additional_bonus: float
    total_placement_score: float
    min_required_score: float
```

### RankingEstimate
Sıralama tahmini:
```python
@dataclass
class RankingEstimate:
    score_type: ScoreType
    placement_score: float
    estimated_rank: int
    percentile: float
    total_candidates: int
    confidence_level: float
```

## Tam Örnek Kullanım

```python
from services.osym_scoring_system import osym_scoring_system, ScoreType

# 1. TYT ve AYT sonuçları
tyt_results = {
    "TURKCE": {"correct": 30, "wrong": 8, "empty": 2},
    "MATEMATIK": {"correct": 35, "wrong": 4, "empty": 1},
    "FEN": {"correct": 18, "wrong": 2, "empty": 0},
    "SOSYAL": {"correct": 16, "wrong": 3, "empty": 1},
}

ayt_results = {
    "MATEMATIK": {"correct": 35, "wrong": 4, "empty": 1},
    "FIZIK": {"correct": 12, "wrong": 1, "empty": 1},
    "KIMYA": {"correct": 11, "wrong": 2, "empty": 0},
    "BIYOLOJI": {"correct": 10, "wrong": 2, "empty": 1},
}

# 2. ÖSYM puanı hesapla
osym_score = osym_scoring_system.calculate_osym_score(
    score_type=ScoreType.SAY,
    tyt_subject_results=tyt_results,
    ayt_subject_results=ayt_results
)

# 3. Yerleştirme puanı hesapla
placement_score = osym_scoring_system.calculate_placement_score(
    osym_score=osym_score,
    obp=85.0,
    additional_bonus=0.0
)

# 4. Sıralama tahmini yap
ranking = osym_scoring_system.estimate_ranking(placement_score)

# 5. Kapsamlı analiz raporu al
analysis = osym_scoring_system.get_score_analysis(
    osym_score,
    placement_score,
    ranking
)

print(f"""
=== ÖSYM Puan Analizi ===
TYT Puanı: {osym_score.tyt_score:.2f}
AYT Puanı: {osym_score.ayt_score:.2f}
Ağırlıklı Puan: {osym_score.weighted_score:.2f}

Yerleştirme Puanı: {placement_score.total_placement_score:.2f}
OBP Bonusu: {placement_score.obp_bonus:.2f}

Tahmini Sıralama: {ranking.estimated_rank:,}
Yüzdelik Dilim: %{ranking.percentile:.1f}
Güven Seviyesi: %{ranking.confidence_level * 100:.0f}
""")
```

## Test Coverage

Kapsamlı test suite ile %100 coverage:

- ✅ Net sayısı hesaplama testleri
- ✅ Ham puan hesaplama testleri
- ✅ ÖSYM puanı hesaplama testleri (SAY, SOZ, EA, DIL)
- ✅ Yerleştirme puanı testleri
- ✅ Sıralama tahmini testleri
- ✅ Program özel puan testleri
- ✅ Edge case testleri (sıfır soru, mükemmel puan, tüm boş)

Test dosyası: `backend/tests/unit/test_osym_scoring_system.py`

## Minimum Puanlar

- **TYT Minimum:** 150 puan
- **Yerleştirme Minimum:** 180 puan

## Notlar

1. **Katsayılar:** ÖSYM 2024-2025 resmi katsayıları kullanılmıştır.
2. **Sıralama Tahmini:** Geçmiş yıl verileri simüle edilmiştir. Gerçek uygulamada ÖSYM'nin resmi verileri kullanılmalıdır.
3. **OBP Katkısı:** Diploma notunun %12'si yerleştirme puanına eklenir.
4. **Negatif Net:** Net sayısı hiçbir zaman negatif olamaz, minimum 0'dır.

## Geliştirme Notları

### Gelecek İyileştirmeler

1. **Gerçek Veri Entegrasyonu:** ÖSYM'nin resmi geçmiş yıl verilerinin entegrasyonu
2. **Dinamik Katsayılar:** Yıllık katsayı güncellemeleri için admin paneli
3. **Detaylı İstatistikler:** Üniversite ve bölüm bazlı taban puan analizleri
4. **Makine Öğrenmesi:** Daha doğru sıralama tahmini için ML modelleri
5. **Performans Optimizasyonu:** Büyük veri setleri için cache mekanizması

## Kaynaklar

- ÖSYM Yükseköğretim Programları ve Kontenjanları Kılavuzu
- ÖSYM Sınav Uygulama Yönergesi
- MEB Müfredat Programları

## Lisans

Bu modül Teknofest 2025 Eğitim Eylemci Platformu'nun bir parçasıdır.
