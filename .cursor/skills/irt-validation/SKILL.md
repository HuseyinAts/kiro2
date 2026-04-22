---
name: irt-validation
description: IRT 3PL model parametre doğrulama. NaN/Inf kontrolü, aralık doğrulaması, Pydantic validator, ZPD entegrasyonu, MLE ability estimation.
---

# IRT Validation — 3PL Model Parametre Doğrulama

`education-algorithms` skill'ine derinlik katan IRT-özel doğrulama rehberi.
IRT kod değiştirirken veya kalibrasyon yaparken yüklenmeli.

## Parametre Sınırları (YENİDEN)

| Parametre | Sembol | Aralık | Pydantic Validator |
|---|---|---|---|
| Difficulty | b | [-4.0, 4.0] | `ge=-4.0, le=4.0` |
| Discrimination | a | [0.2, 4.0] | `ge=0.2, le=4.0` |
| Guessing | c | [0.0, 0.35] | `ge=0.0, le=0.35` |
| Ability | θ | [-4.0, 4.0] | `ge=-4.0, le=4.0` |

## Tutarlılık Kuralı

Düşük ayırt edicilik + aşırı zorluk = PROBLEMATIK SORU:

```python
@model_validator(mode='after')
def validate_irt_consistency(self):
    if self.discrimination < 0.4 and abs(self.difficulty) > 3.0:
        raise ValueError(
            'Düşük ayırt edicilik (<0.4) + aşırı zorluk (|b|>3) '
            'kombinasyonu geçersiz — kalibrasyon gerekli'
        )
    return self
```

## NaN/Inf Koruması

```python
import math

def is_valid_number(x: float) -> bool:
    return not (math.isnan(x) or math.isinf(x))
```

Pydantic model'de her float alan için bu kontrol otomatik yapılmaz — custom
validator gerekir.

## Hata Kodları (KIRO2 standardı)

| Kod | Mesaj | Fix |
|---|---|---|
| IRT_001 | Difficulty out of range | b ∈ [-4, 4] |
| IRT_002 | Discrimination too low | a ≥ 0.2 |
| IRT_003 | Discrimination too high | a ≤ 4.0 |
| IRT_004 | Guessing too high | c ≤ 0.35 |
| IRT_005 | Invalid number (NaN/Inf) | Input kontrol et |
| ZPD_001 | Question too difficult | Daha kolay öner |
| ZPD_002 | Question too easy | Daha zor öner |

## CAT — Adaptive Testing

Fisher Information ile sonraki soru seçimi:
```python
def fisher_information(item, ability):
    p = calculate_probability(item, ability)
    q = 1 - p
    return (item.a ** 2) * ((p - item.c) ** 2) / ((1 - item.c) ** 2 * p * q)
```

Bir sonraki soru = Fisher Information max olan. Administered list'i takip et.

## MLE Ability Estimation

```python
from scipy.optimize import minimize

def estimate_ability(responses, item_params):
    def neg_log_likelihood(theta):
        ll = 0
        for resp, params in zip(responses, item_params):
            p = calculate_probability(params, theta[0])
            ll += math.log(p + 1e-10) if resp else math.log(1 - p + 1e-10)
        return -ll
    return minimize(neg_log_likelihood, [0.0], bounds=[(-4, 4)]).x[0]
```

## Detaylı Rehber

Test örnekleri, full Pydantic template, ZPD soru seçim algoritması:
`.claude/skills/irt-validation/SKILL.md`
