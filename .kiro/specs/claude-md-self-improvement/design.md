# Design Document - CLAUDE.md Self-Improvement

## Architecture Overview

CLAUDE.md otomatik self-improvement sistemi. Feedback loop, pattern detection, A/B testing, meta-learning ile sürekli kural iyileştirmesi sağlar.

## Components

### 1. Feedback Collector (backend/services/feedback_service.py)
- **Purpose**: Agent performance feedback toplama
- **Dependencies**: None
- **Key Features**:
  - Success/failure outcome tracking
  - User rating (1-5) + comments
  - Implicit feedback (retry count, edit frequency)
  - Per-rule effectiveness scoring
  - 30-day rolling window
  - Improvement trigger (threshold-based)

### 2. Pattern Detector (backend/services/pattern_service.py)
- **Purpose**: Recurring pattern tespiti
- **Dependencies**: scikit-learn>=1.4.0
- **Key Features**:
  - Error pattern clustering
  - Success pattern identification
  - Anti-pattern detection
  - Statistical significance (>= 0.95)
  - Heatmap + graph visualization
  - Actionable recommendations

### 3. Rule Evolver (backend/services/rule_evolution_service.py)
- **Purpose**: Kural otomatik iyileştirme
- **Dependencies**: git>=2.40.0
- **Key Features**:
  - Alternative formulation generation
  - Conflict resolution
  - A/B testing validation
  - Version control tracking
  - Rollback capability
  - Before/after metrics comparison

### 4. A/B Testing Framework (backend/services/ab_testing_service.py)
- **Purpose**: Rule değişikliği validation
- **Dependencies**: scipy>=1.12.0
- **Key Features**:
  - 50-50 traffic split
  - Minimum 1000 samples
  - Statistical significance (p < 0.05)
  - Multi-metric evaluation
  - Winner selection
  - Confidence interval + effect size

### 5. Meta-Learning System (backend/services/meta_learning_service.py)
- **Purpose**: Learning optimization
- **Dependencies**: scikit-optimize>=0.9.0
- **Key Features**:
  - Learning rate optimization
  - Transfer learning
  - Epsilon-greedy exploration
  - Bayesian optimization
  - Plateau detection
  - Knowledge graph persistence

### 6. Documentation Updater (backend/services/doc_updater_service.py)
- **Purpose**: CLAUDE.md otomatik güncelleme
- **Dependencies**: git>=2.40.0
- **Key Features**:
  - Auto-update on rule change
  - Best practice examples
  - Migration guides
  - Semantic versioning
  - Before/after diff
  - Human-in-the-loop approval

### 7. Performance Monitor (backend/services/performance_monitor_service.py)
- **Purpose**: İyileşme tracking
- **Dependencies**: pandas>=2.2.0
- **Key Features**:
  - Baseline snapshot
  - Success rate, latency, quality comparison
  - Automatic rollback on regression
  - Trend analysis (moving average, seasonality)
  - Anomaly detection (Z-score > 3)
  - Real-time dashboard

### 8. Safety Guardrails (backend/services/safety_service.py)
- **Purpose**: Zararlı değişiklik önleme
- **Dependencies**: None
- **Key Features**:
  - Safety policy compliance
  - Manual approval for risky changes
  - Sandbox testing
  - Fast rollback (< 5s)
  - Audit logging (who, what, when, why)
  - Emergency stop

### 9. Hook Integration Layer (backend/hooks/claude_md_improvement/)
- **Purpose**: Mevcut hook altyapısıyla entegrasyon
- **Dependencies**: backend/hooks/reward_hacking/* (mevcut)
- **Key Features**:
  - PostToolUse hook ile otomatik feedback toplama
  - Exit Code 2 mekanizması (Daisy Stanton standard)
  - verification-agent, test-runner subagent tetikleme
  - .claude/hooks/ ile senkronizasyon
  - Boris Cherny verification feedback loops

### 10. MCP Integration Layer (backend/mcp_servers/claude_md_improvement_mcp.py)
- **Purpose**: MCP server'larla entegrasyon
- **Dependencies**: chromadb-mcp, zemberek-mcp (mevcut)
- **Key Features**:
  - Semantic search ile pattern tespiti
  - Türkçe metin analizi
  - Rule embedding storage
  - KIRO2 YKS platform entegrasyonu

## Data Flow

```
TaskCompletion → [Hook Trigger] → FeedbackCollector → PatternDetector → RuleEvolver
                      ↓                                                      ↓
              verification-agent                                        ABTesting
              test-runner (subagent)                                         ↓
                                                                       MetaLearning
                                                                             ↓
                                                                       DocUpdater
                                                                             ↓
                                                                   PerformanceMonitor
                                                                             ↓
                                                               SafetyGuardrails → [Exit Code 2 if blocked]
                                                                             ↓
                                                               [MCP: chromadb-mcp, zemberek-mcp]
```

## Correctness Properties

### Property 1: Feedback Aggregation
```python
@given(outcomes=st.lists(st.booleans()))
def test_feedback_aggregation(outcomes):
    score = feedback_service.calculate_effectiveness(outcomes)
    assert 0 <= score <= 1
```

### Property 2: Statistical Significance
```python
@given(control=st.lists(st.floats()), treatment=st.lists(st.floats()))
def test_statistical_significance(control, treatment):
    result = ab_testing_service.test(control, treatment)
    if result['significant']:
        assert result['p_value'] < 0.05
```

### Property 3: Rollback Safety
```python
@given(version=st.integers(min_value=1, max_value=100))
def test_rollback_safety(version):
    rule_evolver.rollback(version)
    current = rule_evolver.get_current_version()
    assert current == version
```

### Property 4: Pattern Confidence
```python
@given(pattern_data=st.lists(st.floats()))
def test_pattern_confidence(pattern_data):
    patterns = pattern_detector.detect(pattern_data)
    assert all(p['confidence'] >= 0.95 for p in patterns)
```

## Performance Targets

| Metric | Target | Critical |
|--------|--------|----------|
| Feedback processing | < 1s | < 2s |
| Pattern detection | < 10s | < 20s |
| A/B test evaluation | < 5s | < 10s |
| Rollback time | < 5s | < 10s |
| Task success improvement | >= 25% | >= 15% |

## Security Considerations

- Safety policy validation
- Manual approval workflow
- Sandbox environment
- Audit logging
- Emergency stop mechanism
- Version control (git)

## Monitoring

- Task success rate (%)
- Rule effectiveness (%)
- A/B test win rate (%)
- Regression count
- Safety compliance (%)
