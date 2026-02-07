# ZPD Maarif Property-Based Tests

## Overview

Property-based tests for the Turkish ZPD (Zone of Proximal Development) Maarif System using Hypothesis framework. These tests follow **Boris Cherny Standards** with 100+ iterations per property.

## Test File

`test_zpd_properties.py` - 18 comprehensive property tests

## Properties Tested

### 1. ZPD Probability Bounds (4 tests)
- **Property**: ZPD probability always in [0.15, 0.85] for optimal zone
- Tests:
  - Optimal zone within ZPD bounds
  - Acceptable zone within ZPD bounds
  - Too easy questions (P > 0.85)
  - Too hard questions (P < 0.15)

### 2. ZPD Classification Determinism (1 test)
- **Property**: Same (θ, b) parameters → same zone classification
- Tests:
  - Deterministic classification for identical inputs

### 3. Zone Ordering Consistency (2 tests)
- **Property**: TOO_HARD (< 0.15) < OPTIMAL [0.40, 0.60] < TOO_EASY (> 0.85)
- Tests:
  - Threshold ordering verification
  - Complete probability space coverage

### 4. Cultural Adjustment Factors (3 tests)
- **Property**: All cultural factors are positive and in valid ranges
- Tests:
  - ZPD expansion factors > 1.0
  - Default cultural factors in [0.0, 1.0]
  - Cultural context parameter validation

### 5. Maarif Subject Mapping (3 tests)
- **Property**: All subjects have non-empty Maarif value mappings
- Tests:
  - All subjects have values
  - Mapping determinism
  - Valid enum members

### 6. IRT Probability Monotonicity (3 tests)
- **Property**: Higher ability → higher probability
- Tests:
  - Higher θ → higher P(θ)
  - Higher difficulty → lower P(θ)
  - Higher discrimination → stronger separation

### 7. ZPD Probability Consistency (1 test)
- **Property**: Zone classification matches probability calculation
- Tests:
  - Classification-probability alignment

### 8. ZPD Expansion Behavior (1 test)
- **Property**: Cultural factors compound multiplicatively
- Tests:
  - Multiplicative expansion composition

## Test Statistics

```
Total Tests: 18
Max Examples per Test: 100
Total Test Runs: ~1,300+ (accounting for filtered examples)
Test Duration: ~4.65 seconds
Pass Rate: 100%
```

## Hypothesis Settings

```python
@settings(max_examples=100)
```

- 100 examples per property test (Boris Cherny standard)
- Automatic shrinking on failure
- Deterministic seed for reproducibility

## Strategy Definitions

### IRT Parameters
```python
valid_theta = st.floats(-4.0, 4.0)
valid_difficulty = st.floats(-4.0, 4.0)
valid_discrimination = st.floats(0.2, 4.0)
valid_guessing = st.floats(0.0, 0.35)
```

### Cultural Factors
```python
cultural_factor = st.floats(0.0, 1.0)
```

### Subjects
```python
valid_subjects = st.sampled_from([
    "tarih", "türkçe", "matematik", "fen", "sosyal", "din"
])
```

## Key Formulas Tested

### IRT 3PL Model
```
P(θ) = c + (1-c) / (1 + exp(-D*a*(θ-b)))

where:
  θ = student ability [-4, 4]
  b = difficulty [-4, 4]
  a = discrimination [0.2, 4.0]
  c = guessing [0.0, 0.35]
  D = 1.7 (scaling factor)
```

### ZPD Zones
```
TOO_HARD:    P < 0.15
ACCEPTABLE:  0.15 ≤ P ≤ 0.85 (excluding optimal)
OPTIMAL:     0.40 ≤ P ≤ 0.60
TOO_EASY:    P > 0.85
```

## Running Tests

### Basic Run
```bash
cd backend
pytest tests/property/test_zpd_properties.py -v
```

### With Statistics
```bash
pytest tests/property/test_zpd_properties.py -v --hypothesis-show-statistics
```

### With Coverage
```bash
pytest tests/property/test_zpd_properties.py --cov=algorithms.turkish_zpd_maarif_system
```

### Single Test Class
```bash
pytest tests/property/test_zpd_properties.py::TestZPDProbabilityBounds -v
```

## Validation Results

### Linting
```bash
ruff check tests/property/test_zpd_properties.py --select=E,F,W --ignore=E501
✅ All checks passed!
```

### Test Execution
```
✅ 18 passed, 1 warning in 4.65s
```

### Hypothesis Statistics
- **Optimal tests**: 100 examples each
- **Monotonicity tests**: 100 valid examples (54-61% filtered by assume())
- **Subject mapping**: 6 examples (all subjects covered)

## Anti-Patterns Avoided

### NO Reward Hacking
```python
# ❌ FORBIDDEN
assert True
assert 1 == 1
pass

# ✅ CORRECT
assert zone == "optimal"
assert prob >= ZPD_LOWER_BOUND
```

### NO Fake Assertions
All assertions test real properties with meaningful error messages:
```python
assert (
    ZPD_LOWER_BOUND <= prob <= ZPD_UPPER_BOUND
), f"P={prob:.3f} outside ZPD bounds [{ZPD_LOWER_BOUND}, {ZPD_UPPER_BOUND}]"
```

## Integration with Existing Tests

This file complements:
- `tests/unit/algorithms/test_zpd_boundaries.py` - Unit tests for ZPD
- `tests/property/test_pipeline_irt.py` - Property tests for IRT

Together they provide:
- Unit tests (deterministic cases)
- Property tests (randomized validation)
- Edge case coverage
- Mathematical invariant verification

## Mathematical Properties Verified

1. **Probability Bounds**: P(θ) ∈ [c, 1.0]
2. **Monotonicity**: θ₁ < θ₂ ⇒ P(θ₁) ≤ P(θ₂)
3. **Difficulty Inverse**: b₁ < b₂ ⇒ P(b₁) ≥ P(b₂)
4. **Discrimination Effect**: Higher a → stronger separation
5. **Zone Consistency**: Classification ⟺ Probability range
6. **Factor Composition**: expansion = ∏(cultural_factors)
7. **Determinism**: Same input → same output
8. **Completeness**: ∀P ∈ [0,1], ∃ unique zone

## References

- **Boris Cherny Standards**: Verification feedback loops with 100+ examples
- **Hypothesis Documentation**: https://hypothesis.readthedocs.io/
- **IRT Theory**: 3-Parameter Logistic Model
- **Vygotsky ZPD**: Zone of Proximal Development
- **MEB Maarif**: Turkish Educational Values System

## Maintenance

When modifying ZPD system:
1. Run property tests first: `pytest tests/property/test_zpd_properties.py`
2. Check for new invariants to add
3. Update strategies if parameter ranges change
4. Verify all 18 tests still pass
5. Check Hypothesis statistics for coverage

## Success Criteria

- ✅ All 18 tests passing
- ✅ 100 examples per @settings test
- ✅ No reward hacking patterns
- ✅ Meaningful error messages
- ✅ Type hints on all functions
- ✅ Docstrings on all test classes
- ✅ Follows Boris Cherny standards
- ✅ Clean ruff/mypy checks

---

**Created**: 2025-02-02
**Last Updated**: 2025-02-02
**Test Framework**: pytest + hypothesis
**Standard**: Boris Cherny Verification Feedback Loops
