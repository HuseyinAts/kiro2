---
name: irt-validation
description: IRT 3PL model parametre doğrulama
user-invocable: false
allowed-tools:
  - Read
---

# IRT Validation Skill

Bu skill, IRT (Item Response Theory) 3PL model parametrelerinin doğrulanması için kullanılır.
YKS Generator ve Education Algorithms skill'leri tarafından otomatik yüklenir.

## IRT 3PL Model Parametreleri

### Geçerli Aralıklar

| Parametre | Sembol | Aralık | Açıklama |
|-----------|--------|--------|----------|
| Difficulty | b | [-4.0, 4.0] | Soru zorluğu |
| Discrimination | a | [0.2, 4.0] | Ayırt edicilik |
| Guessing | c | [0.0, 0.35] | Şans başarısı |
| Ability | θ | [-4.0, 4.0] | Öğrenci yeteneği |

### Doğrulama Kuralları

1. **Tüm parametreler float olmalı**
   - Integer kabul edilebilir (otomatik dönüşüm)
   - String REJECT
   - NaN/Inf REJECT

2. **Aralık dışı değerler REJECT**
   ```python
   def validate_difficulty(b: float) -> bool:
       return -4.0 <= b <= 4.0

   def validate_discrimination(a: float) -> bool:
       return 0.2 <= a <= 4.0

   def validate_guessing(c: float) -> bool:
       return 0.0 <= c <= 0.35
   ```

3. **NaN/Inf değerler REJECT**
   ```python
   import math

   def is_valid_number(x: float) -> bool:
       return not (math.isnan(x) or math.isinf(x))
   ```

## IRT 3PL Formülü

Başarı olasılığı hesaplama:

```
P(θ) = c + (1-c) / (1 + exp(-a(θ-b)))
```

Burada:
- P(θ): Başarı olasılığı
- θ: Öğrenci yeteneği
- a: Ayırt edicilik
- b: Zorluk
- c: Şans parametresi

### Python Implementasyonu

```python
import math
from dataclasses import dataclass
from typing import Literal

@dataclass
class IRTParameters:
    difficulty: float       # b: [-4.0, 4.0]
    discrimination: float   # a: [0.2, 4.0]
    guessing: float         # c: [0.0, 0.35]

def calculate_probability(params: IRTParameters, ability: float) -> float:
    """
    IRT 3PL modeliyle başarı olasılığı hesapla.

    Args:
        params: IRT parametreleri
        ability: Öğrenci yeteneği (θ)

    Returns:
        Başarı olasılığı [0, 1]
    """
    a = params.discrimination
    b = params.difficulty
    c = params.guessing

    exponent = -a * (ability - b)
    probability = c + (1 - c) / (1 + math.exp(exponent))

    return probability
```

## ZPD Entegrasyonu

### ZPD (Zone of Proximal Development) Kuralları

**Optimal ZPD Bölgesi:** %15-85 başarı olasılığı

```python
ZPD_MIN = 0.15  # Frustration zone altı
ZPD_MAX = 0.85  # Comfort zone üstü

def is_in_zpd(probability: float) -> bool:
    """Soru optimal zorlukta mı?"""
    return ZPD_MIN <= probability <= ZPD_MAX

def get_zpd_zone(probability: float) -> Literal["frustration", "zpd", "comfort"]:
    """Öğrencinin hangi bölgede olduğunu belirle."""
    if probability < ZPD_MIN:
        return "frustration"  # Çok zor
    elif probability > ZPD_MAX:
        return "comfort"      # Çok kolay
    else:
        return "zpd"          # Optimal
```

### ZPD Tabanlı Soru Seçimi

```python
def select_optimal_question(
    questions: list[IRTParameters],
    student_ability: float,
) -> IRTParameters | None:
    """
    Öğrenci için optimal zorlukta soru seç.

    Args:
        questions: Aday sorular
        student_ability: Öğrenci yeteneği

    Returns:
        ZPD'de olan soru veya None
    """
    for q in questions:
        prob = calculate_probability(q, student_ability)
        if is_in_zpd(prob):
            return q
    return None
```

## Parametre Kestirimi

### Maximum Likelihood Estimation (MLE)

```python
from scipy.optimize import minimize

def estimate_ability(
    responses: list[bool],
    item_params: list[IRTParameters],
) -> float:
    """
    Öğrenci yeteneğini MLE ile kestirir.

    Args:
        responses: Cevap vektörü (True=doğru, False=yanlış)
        item_params: Soru IRT parametreleri

    Returns:
        Kestirilen yetenek (θ)
    """
    def neg_log_likelihood(theta):
        ll = 0
        for resp, params in zip(responses, item_params):
            p = calculate_probability(params, theta[0])
            if resp:
                ll += math.log(p + 1e-10)
            else:
                ll += math.log(1 - p + 1e-10)
        return -ll

    result = minimize(neg_log_likelihood, [0.0], bounds=[(-4, 4)])
    return result.x[0]
```

## Validasyon Hataları

### Hata Tipleri

| Hata Kodu | Açıklama | Çözüm |
|-----------|----------|-------|
| IRT_001 | Difficulty out of range | b'yi [-4, 4] aralığına çek |
| IRT_002 | Discrimination too low | a'yı minimum 0.2 yap |
| IRT_003 | Discrimination too high | a'yı maksimum 4.0 yap |
| IRT_004 | Guessing too high | c'yi maksimum 0.35 yap |
| IRT_005 | Invalid number (NaN/Inf) | Girdiyi kontrol et |
| ZPD_001 | Question too difficult | Daha kolay soru öner |
| ZPD_002 | Question too easy | Daha zor soru öner |

### Hata Mesajı Formatı

```python
@dataclass
class ValidationError:
    code: str
    message: str
    parameter: str
    value: float
    valid_range: tuple[float, float]

def validate_irt_params(params: IRTParameters) -> list[ValidationError]:
    errors = []

    if not -4.0 <= params.difficulty <= 4.0:
        errors.append(ValidationError(
            code="IRT_001",
            message="Difficulty out of range",
            parameter="difficulty",
            value=params.difficulty,
            valid_range=(-4.0, 4.0),
        ))

    # ... diğer kontroller

    return errors
```

## KIRO2 Entegrasyonu

### Soru Oluşturma Validasyonu

```python
from pydantic import BaseModel, validator

class QuestionCreate(BaseModel):
    text: str
    options: list[str]
    correct_answer: int
    difficulty: float
    discrimination: float
    guessing: float

    @validator('difficulty')
    def validate_difficulty(cls, v):
        if not -4.0 <= v <= 4.0:
            raise ValueError(f'difficulty must be in [-4.0, 4.0], got {v}')
        return v

    @validator('discrimination')
    def validate_discrimination(cls, v):
        if not 0.2 <= v <= 4.0:
            raise ValueError(f'discrimination must be in [0.2, 4.0], got {v}')
        return v

    @validator('guessing')
    def validate_guessing(cls, v):
        if not 0.0 <= v <= 0.35:
            raise ValueError(f'guessing must be in [0.0, 0.35], got {v}')
        return v
```

### CAT (Computerized Adaptive Testing) Entegrasyonu

```python
def select_next_item_cat(
    available_items: list[IRTParameters],
    current_ability: float,
    administered_items: list[str],
) -> IRTParameters:
    """
    CAT için sonraki soruyu seç (Fisher Information maksimizasyonu).
    """
    best_item = None
    best_info = -float('inf')

    for item in available_items:
        if item.id in administered_items:
            continue

        info = fisher_information(item, current_ability)
        if info > best_info:
            best_info = info
            best_item = item

    return best_item

def fisher_information(item: IRTParameters, ability: float) -> float:
    """Fisher bilgisi hesapla."""
    p = calculate_probability(item, ability)
    q = 1 - p

    a = item.discrimination
    c = item.guessing

    info = (a ** 2) * ((p - c) ** 2) / ((1 - c) ** 2 * p * q)
    return info
```

## Test Örnekleri

```python
import pytest

def test_valid_parameters():
    params = IRTParameters(difficulty=0.0, discrimination=1.0, guessing=0.2)
    errors = validate_irt_params(params)
    assert len(errors) == 0

def test_invalid_difficulty():
    params = IRTParameters(difficulty=5.0, discrimination=1.0, guessing=0.2)
    errors = validate_irt_params(params)
    assert any(e.code == "IRT_001" for e in errors)

def test_zpd_optimal():
    params = IRTParameters(difficulty=0.0, discrimination=1.0, guessing=0.2)
    prob = calculate_probability(params, ability=0.0)
    assert is_in_zpd(prob), f"Probability {prob} should be in ZPD"

def test_probability_bounds():
    params = IRTParameters(difficulty=0.0, discrimination=1.0, guessing=0.2)
    for ability in [-4.0, -2.0, 0.0, 2.0, 4.0]:
        prob = calculate_probability(params, ability)
        assert 0.0 <= prob <= 1.0
```

## Referanslar

- Baker, F.B. & Kim, S.H. (2004). Item Response Theory: Parameter Estimation Techniques
- Embretson, S.E. & Reise, S.P. (2000). Item Response Theory for Psychologists
- van der Linden, W.J. (2016). Handbook of Item Response Theory
