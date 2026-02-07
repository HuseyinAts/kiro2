---
name: education-algorithms
description: Eğitim algoritmaları için parametre doğrulama. IRT 3PL model, FSRS aralıklı tekrar, ZPD optimal zorluk. Algoritma implementasyonunda otomatik yüklenir.
user-invocable: false
allowed-tools: Read, Grep, Glob
skills: kiro2-specific
---

# Education Algorithms Skill - KIRO2

Eğitim algoritmaları için parametre doğrulama ve best practices.

## IRT (Madde Tepki Kuramı)

3-Parametreli Logistik Model (3PL):
```
P(θ) = c + (1-c) / (1 + e^(-a(θ-b)))
```

### Parametre Sınırları (P0 - KRİTİK)

| Parametre | Aralık | Tipik | Uyarı |
|-----------|--------|-------|-------|
| Zorluk (b) | [-4, 4] | 0 | \|b\| > 3.5 |
| Ayırt Edicilik (a) | [0.2, 4] | 1.0-1.5 | a < 0.5 veya a > 2.5 |
| Şans (c) | [0, 0.35] | 0.2 | c > 0.3 |

### Pydantic Model

```python
from pydantic import BaseModel, Field, model_validator

class IRTParameters(BaseModel):
    difficulty: float = Field(..., ge=-4.0, le=4.0,
        description="Zorluk parametresi (b): logit ölçeği")
    discrimination: float = Field(..., ge=0.2, le=4.0,
        description="Ayırt edicilik (a): pozitif olmalı")
    guessing: float = Field(default=0.2, ge=0.0, le=0.35,
        description="Şans parametresi (c): 5 şıklı MCQ için ~0.20")
    
    @model_validator(mode='after')
    def validate_irt_consistency(self) -> 'IRTParameters':
        # Düşük ayırt edicilik + aşırı zorluk = problematik soru
        if self.discrimination < 0.4 and abs(self.difficulty) > 3.0:
            raise ValueError(
                'Düşük ayırt edicilik (<0.4) ile aşırı zorluk (|b|>3) '
                'kombinasyonu uygunsuz - soru kalibrasyonu gerekli'
            )
        return self
```

### Başarı Olasılığı Hesaplama

```python
import math

def calculate_success_probability(
    theta: float,  # Öğrenci yeteneği
    a: float,      # Ayırt edicilik
    b: float,      # Zorluk
    c: float = 0.2 # Şans
) -> float:
    """3PL IRT modeli ile başarı olasılığı"""
    exponent = -a * (theta - b)
    return c + (1 - c) / (1 + math.exp(exponent))
```

## FSRS (Free Spaced Repetition Scheduler)

Bellek stabilitesi ve hatırlanabilirlik hesaplamaları.

### Parametre Sınırları (P0 - KRİTİK)

| Parametre | Aralık | Açıklama |
|-----------|--------|----------|
| Stabilite (S) | [0.1, 3650] | Gün cinsinden (max ~10 yıl) |
| Zorluk (D) | [0, 10] | Kart zorluğu |
| Hatırlanabilirlik (R) | [0, 1] | Olasılık |

### Hatırlanabilirlik Formülü

```
R(t) = e^(-t/S)
```

### Pydantic Model

```python
import math
from pydantic import BaseModel, Field, field_validator

class FSRSParameters(BaseModel):
    stability: float = Field(..., ge=0.1, le=3650,
        description="Bellek stabilitesi (gün)")
    difficulty: float = Field(..., ge=0.0, le=10.0,
        description="Kart zorluğu (0-10)")
    retrievability: float = Field(..., ge=0.0, le=1.0,
        description="Hatırlanabilirlik olasılığı")
    elapsed_days: float = Field(default=0, ge=0)
    
    @model_validator(mode='after')
    def validate_retrievability(self) -> 'FSRSParameters':
        """R(t) = e^(-t/S) formülü ile doğrulama"""
        if self.elapsed_days > 0:
            expected_r = math.exp(-self.elapsed_days / self.stability)
            if abs(self.retrievability - expected_r) > 0.01:
                raise ValueError(
                    f'Hesaplanan R: {expected_r:.3f}, '
                    f'verilen: {self.retrievability:.3f}'
                )
        return self
```

### Tekrar Aralığı Doğrulama

| Değerlendirme | Stabilite Çarpanı | Min Aralık | Max Aralık |
|---------------|-------------------|------------|------------|
| Again (1) | 0.2-0.5 | 1 gün | 3 gün |
| Hard (2) | 0.8-1.2 | önceki | önceki × 1.2 |
| Good (3) | 1.5-2.5 | önceki × 1.5 | 180 gün |
| Easy (4) | 2.5-4.0 | önceki × 2.5 | 365 gün |

## ZPD (Yakınsal Gelişim Alanı)

Vygotsky'nin öğrenme teorisine dayalı optimal zorluk atama.

### Bölge Sınıflandırması (P0 - KRİTİK)

| Bölge | Başarı Tahmini | Açıklama |
|-------|----------------|----------|
| TOO_EASY | > 85% | Öğrenme potansiyeli düşük |
| **OPTIMAL** | **15% - 85%** | **İdeal öğrenme bölgesi** |
| TOO_HARD | < 15% | Motivasyon düşüşü riski |

### Pydantic Model

```python
from enum import Enum
from pydantic import BaseModel, Field, model_validator

class ZPDZone(str, Enum):
    TOO_EASY = "too_easy"
    OPTIMAL = "optimal"
    TOO_HARD = "too_hard"

class ZPDAssignment(BaseModel):
    student_ability: float = Field(..., ge=-5.0, le=5.0)
    question_difficulty: float = Field(..., ge=-4.0, le=4.0)
    predicted_success: float = Field(..., ge=0.0, le=1.0)
    zone: ZPDZone
    
    @model_validator(mode='after')
    def validate_zone_classification(self) -> 'ZPDAssignment':
        expected_zone = self._calculate_zone(self.predicted_success)
        if self.zone != expected_zone:
            raise ValueError(
                f'Bölge uyumsuzluğu: beklenen {expected_zone}, '
                f'verilen {self.zone} (başarı: {self.predicted_success:.2%})'
            )
        return self
    
    @staticmethod
    def _calculate_zone(success_prob: float) -> ZPDZone:
        if success_prob > 0.85:
            return ZPDZone.TOO_EASY
        elif success_prob < 0.15:
            return ZPDZone.TOO_HARD
        else:
            return ZPDZone.OPTIMAL
```

### Optimal Soru Seçimi

```python
def select_optimal_question(
    student_ability: float,
    questions: list[dict]
) -> dict | None:
    """ZPD'de olan en uygun soruyu seç"""
    optimal_questions = []
    
    for q in questions:
        prob = calculate_success_probability(
            theta=student_ability,
            a=q['discrimination'],
            b=q['difficulty'],
            c=q['guessing']
        )
        
        # ZPD kontrolü
        if 0.15 <= prob <= 0.85:
            # 0.50'ye yakınlık skoru
            distance = abs(prob - 0.50)
            optimal_questions.append((q, distance))
    
    if not optimal_questions:
        return None
    
    # En optimal soruyu döndür (0.50'ye en yakın)
    optimal_questions.sort(key=lambda x: x[1])
    return optimal_questions[0][0]
```

## YKS Zorluk Dağılımı (ÖSYM Kalıpları)

| Seviye | Hedef Oran | IRT Zorluk |
|--------|------------|------------|
| Kolay | ~30% | b < -1.0 |
| Orta | ~40% | -1.0 ≤ b ≤ 1.0 |
| Zor | ~25% | 1.0 < b ≤ 2.5 |
| Çok Zor | ~5% | b > 2.5 |

## Doğrulama Kontrol Listesi

- [ ] IRT parametreleri sınırlar içinde
- [ ] Düşük ayırt edicilik + aşırı zorluk kombinasyonu yok
- [ ] FSRS stabilite 0.1-3650 gün arasında
- [ ] Hatırlanabilirlik formül ile tutarlı
- [ ] ZPD bölge ataması doğru
- [ ] Soru seçimi optimal bölgeden yapılıyor
- [ ] YKS zorluk dağılımı ÖSYM kalıplarına uygun
