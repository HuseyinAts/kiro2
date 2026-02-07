# CLAUDE.md Self-Improvement Architecture

> **Version:** 1.0.0
> **Son Guncelleme:** 2026-01-19
> **Spec:** claude-md-self-improvement

## 1. System Overview

### 1.1 Purpose

CLAUDE.md Self-Improvement sistemi, agent configuration dosyasinin (CLAUDE.md) otomatik optimizasyonunu saglar:

- **Feedback Collection**: Task sonuclarini topla ve analiz et
- **Pattern Detection**: Basari/hata oruntularini tespit et
- **Rule Evolution**: Kurallari otomatik iyilestir
- **Safety Guardrails**: Zararli degisiklikleri onle

### 1.2 Architecture Diagram

```
                              +-------------------+
                              |   Task Execution  |
                              +--------+----------+
                                       |
                                       v
+------------------+          +--------+----------+
|  Exit Code 2     |<---------|   Hook Trigger    |
| (Block on Error) |          | (PostToolUse)     |
+------------------+          +--------+----------+
                                       |
         +-----------------------------+-----------------------------+
         |                             |                             |
         v                             v                             v
+--------+----------+        +---------+---------+        +---------+---------+
| FeedbackCollector |        | PatternDetector   |        | PerformanceMonitor|
| (feedback_service)|        | (pattern_service) |        | (perf_monitor_svc)|
+--------+----------+        +---------+---------+        +---------+---------+
         |                             |                             |
         | record_outcome()            | detect_patterns()           | detect_regression()
         | calculate_effectiveness()   | cluster_errors()            | capture_baseline()
         |                             |                             |
         v                             v                             v
+--------+----------+        +---------+---------+        +---------+---------+
| RuleEffectiveness |        | PatternDetection  |        |  Auto-Rollback    |
| (DB: PostgreSQL)  |        | (visualize)       |        |  (< 5s target)    |
+--------+----------+        +---------+---------+        +---------+---------+
         |                             |                             |
         +-----------------------------+-----------------------------+
                                       |
                                       v
                              +--------+----------+
                              |   RuleEvolver     |
                              | (rule_evolution)  |
                              +--------+----------+
                                       |
                                       v
                              +--------+----------+
                              |   A/B Testing     |
                              | (50-50 split)     |
                              +--------+----------+
                                       |
                                       v
                              +--------+----------+
                              |  SafetyValidator  |
                              | (risk scoring)    |
                              +--------+----------+
                                       |
                              risk > 0.7?
                              /        \
                             /          \
                            v            v
                   +--------+--+    +----+--------+
                   |  Manual   |    | Auto-Approve|
                   |  Approval |    |             |
                   +--------+--+    +----+--------+
                            \          /
                             \        /
                              v      v
                              +------+------+
                              | DocUpdater  |
                              | (CLAUDE.md) |
                              +------+------+
                                     |
                                     v
                              +------+------+
                              | Git Commit  |
                              | + Version   |
                              +-------------+
```

### 1.3 Component Relationships

| Component | Input | Output | Dependencies |
|-----------|-------|--------|--------------|
| FeedbackCollector | Task results | Effectiveness scores | PostgreSQL |
| PatternDetector | Feedback records | Pattern clusters | scikit-learn |
| RuleEvolver | Low-performing rules | Alternative rules | GitPython |
| ABTesting | Rule variants | Winner selection | scipy |
| MetaLearning | Learning history | Optimized params | scikit-optimize |
| DocUpdater | Approved changes | CLAUDE.md update | Git |
| PerformanceMonitor | Metrics | Regression alerts | numpy |
| SafetyValidator | Proposed changes | Risk assessment | - |

## 2. Feedback Collection Architecture (REQ-1)

### 2.1 Feedback Types

```python
class FeedbackType(Enum):
    EXPLICIT = "explicit"    # User ratings (1-5)
    IMPLICIT = "implicit"    # Retry count, edit frequency
    AUTOMATIC = "automatic"  # Test results (Boris Cherny)
```

### 2.2 Effectiveness Score Calculation

```
effectiveness = (explicit_weight * explicit_score) +
                (implicit_weight * implicit_score)

Where:
- explicit_weight = 0.7
- implicit_weight = 0.3
- explicit_score = success_count / total_count
- implicit_score = 1 - (retry_rate * 0.5 + edit_rate * 0.5)
```

### 2.3 30-Day Rolling Window

```sql
SELECT rule_id,
       AVG(CASE WHEN outcome = 'success' THEN 1 ELSE 0 END) as effectiveness
FROM feedback_records
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY rule_id;
```

### 2.4 Improvement Trigger Logic

```python
if effectiveness < 0.6:  # REQ-1.5 threshold
    create_improvement_trigger(
        rule_id=rule_id,
        trigger_type="low_effectiveness",
        suggested_actions=["review", "a_b_test", "evolve"]
    )
```

## 3. Pattern Detection System (REQ-2)

### 3.1 K-Means Clustering

```python
# Error Pattern Clustering
from sklearn.cluster import KMeans

kmeans = KMeans(n_clusters=5, random_state=42)
error_clusters = kmeans.fit_predict(error_features)
```

### 3.2 Statistical Significance

```python
from scipy import stats

# Binomial test for pattern confidence
p_value = stats.binom_test(successes, total, p=0.5)
confidence = 1 - p_value

# REQ-2.4: Require >= 0.95 confidence
if confidence >= 0.95:
    report_pattern(pattern)
```

### 3.3 Visualization Output

```
Heatmap: rule_id x outcome (success/failure rates)
Graph: nodes=rules, edges=co-occurrence
Export: HTML with Plotly interactive charts
```

## 4. Rule Evolution Mechanism (REQ-3)

### 4.1 Alternative Formulation Generation

| Strategy | Description | Example |
|----------|-------------|---------|
| Simplify | Remove complex clauses | "Always X when Y" -> "Always X" |
| Specify | Add concrete examples | "Use async" -> "Use async for I/O" |
| Merge | Combine related rules | Rule A + Rule B -> Rule AB |

### 4.2 Conflict Resolution

```python
def resolve_contradiction(rule_a: str, rule_b: str) -> str:
    # Strategy: Keep higher-performing rule
    if get_effectiveness(rule_a) > get_effectiveness(rule_b):
        return rule_a
    return rule_b
```

### 4.3 Version Control Integration

```
CLAUDE.md Version: 2.3.1
  - Major: Breaking changes (e.g., rule removal)
  - Minor: New features (e.g., new rule)
  - Patch: Bug fixes (e.g., typo fix)

Git tag: claude-md-v2.3.1
```

## 5. A/B Testing Framework (REQ-4)

### 5.1 Traffic Splitting

```python
def get_variant(user_id: str) -> Variant:
    # Consistent hashing for 50-50 split
    hash_val = hashlib.md5(user_id.encode()).hexdigest()
    if int(hash_val, 16) % 2 == 0:
        return Variant.CONTROL
    return Variant.TREATMENT
```

### 5.2 Sample Size Requirements

- **Minimum samples per variant:** 1000 (REQ-4.2)
- **Maximum test duration:** 14 days
- **Significance threshold:** p < 0.05 (REQ-4.3)

### 5.3 Multi-Metric Evaluation

```python
metrics = {
    "success_rate": 0.5,      # Weight
    "latency": 0.3,           # Weight
    "quality_score": 0.2,     # Weight
}

composite_score = sum(
    weight * normalize(metric)
    for metric, weight in metrics.items()
)
```

## 6. Meta-Learning System (REQ-5)

### 6.1 Bayesian Optimization

```python
from skopt import gp_minimize
from skopt.space import Real

# Optimize learning rate
space = [Real(0.001, 0.1, name='learning_rate')]
result = gp_minimize(
    objective_function,
    space,
    n_calls=50,
    random_state=42
)
```

### 6.2 Epsilon-Greedy Exploration

```python
@dataclass
class LearningState:
    epsilon: float = 0.3      # Initial exploration rate
    decay_rate: float = 0.99  # Per-episode decay

def get_action(state: LearningState) -> Action:
    if random.random() < state.epsilon:
        return random_action()  # Explore
    return best_known_action()  # Exploit
```

### 6.3 Knowledge Graph Persistence

```python
import networkx as nx

# Store task relationships
graph = nx.DiGraph()
graph.add_edge(task_a, task_b, weight=similarity_score)

# Query for transfer learning
similar_tasks = nx.neighbors(graph, current_task)
```

## 7. Safety Guardrails (REQ-8)

### 7.1 Risk Scoring Algorithm

```python
RISKY_PATTERNS = [
    ("delete", 0.8),
    ("drop", 0.9),
    ("truncate", 0.9),
    ("rm -rf", 1.0),
    ("eval", 0.7),
    ("exec", 0.7),
]

def calculate_risk(change: str) -> float:
    risk = 0.0
    for pattern, weight in RISKY_PATTERNS:
        if pattern.lower() in change.lower():
            risk = max(risk, weight)
    return risk
```

### 7.2 Approval Workflow

```
risk <= 0.3: Auto-approve
0.3 < risk <= 0.7: Auto-approve with warning
risk > 0.7: Manual approval required (REQ-8.2)
```

### 7.3 Emergency Stop Mechanism

```python
class Orchestrator:
    def emergency_stop(self) -> None:
        """
        Pause all auto-improvement.
        REQ-8.6: All processes halted.
        """
        self._running = False
        self._save_state()
        notify_stakeholders("Emergency stop activated")
```

## 8. Integration Points

### 8.1 MCP Server Integration

```json
{
    "mcpServers": {
        "claude-md-improvement": {
            "command": "python",
            "args": ["backend/mcp_servers/claude_md_improvement_mcp.py"],
            "env": {"PYTHONPATH": "backend"}
        }
    }
}
```

### 8.2 Available MCP Tools

| Tool | Description |
|------|-------------|
| `record_feedback` | Record task feedback |
| `get_rule_effectiveness` | Query rule scores |
| `analyze_improvements` | Trigger analysis |
| `safety_check` | Validate changes |
| `orchestrator_status` | Get system status |

### 8.3 Hook System Integration

```bash
# .claude/hooks/post-tool-use.sh
#!/bin/bash
# Trigger feedback collection after tool use
if [ "$TOOL_NAME" = "Edit" ] || [ "$TOOL_NAME" = "Write" ]; then
    python -c "from backend.hooks.claude_md_improvement.feedback_hook import collect"
fi
```

### 8.4 Database Schema

```
Tables:
- claude_md_feedback_records (task feedback)
- claude_md_rule_effectiveness (per-rule scores)
- claude_md_improvement_triggers (trigger events)
- claude_md_pattern_detections (detected patterns)
- claude_md_rule_versions (version history)
- claude_md_audit_logs (audit trail)
```

## 9. Performance Targets

| Metric | Target | Critical |
|--------|--------|----------|
| Feedback processing | < 1s | < 2s |
| Pattern detection | < 10s | < 20s |
| A/B test evaluation | < 5s | < 10s |
| Rollback time | < 5s | < 10s |

## 10. Success Metrics

| Metric | Target |
|--------|--------|
| Task success rate improvement | >= 25% |
| Rule effectiveness | >= 80% |
| A/B test win rate | >= 60% |
| Regression prevention | 100% |
| Safety compliance | 100% |

## 11. KIRO2 Platform Integration

### 11.1 Turkish Text Support

```python
# Zemberek MCP integration for Turkish NLP
from backend.mcp_servers.zemberek_mcp import analyze_turkish

# Proper I/ı handling
text.replace("I", "I").replace("i", "i")  # Turkish locale
```

### 11.2 IRT/ZPD Validation

```python
# REQ-10.1: IRT parameter bounds
assert -4.0 <= difficulty <= 4.0

# REQ-10.3: ZPD optimal range
assert 0.15 <= success_probability <= 0.85
```

### 11.3 Database Configuration

```
PostgreSQL: localhost:5434 (NOT 5432!)
Redis: localhost:6379
```

## 12. Boris Cherny Standards

### 12.1 Verification Feedback Loops

> "Giving Claude the opportunity to verify its work increases
> the quality of the final result by 200-300%."

```python
# After every code change:
1. ruff check . --fix           # Linting
2. mypy --ignore-missing-imports  # Type check
3. pytest -x --tb=short         # Tests
```

### 12.2 Exit Code 2 Mechanism (Daisy Stanton)

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | Continue |
| 2 | Blocking error | STOP and fix |
| Other | Warning | Show to user |

## 13. File Reference

| File | Lines | Purpose |
|------|-------|---------|
| feedback_service.py | 635 | REQ-1 implementation |
| pattern_service.py | 794 | REQ-2 implementation |
| rule_evolution_service.py | 805 | REQ-3 implementation |
| ab_testing_service.py | 807 | REQ-4 implementation |
| meta_learning_service.py | 878 | REQ-5 implementation |
| doc_updater_service.py | 940 | REQ-6 implementation |
| performance_monitor_service.py | 821 | REQ-7 implementation |
| safety_service.py | 810 | REQ-8 implementation |
| claude_md_improvement_mcp.py | 406 | MCP server |
| claude_md_improvement_models.py | 339 | DB models |
