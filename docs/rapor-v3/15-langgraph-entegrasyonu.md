# BÖLÜM 15: LangGraph Entegrasyonu

## 15.1 LangGraph Nedir?

### Tanım

LangGraph, LangChain ekibi tarafından geliştirilen, stateful multi-actor uygulamaları oluşturmak için bir framework'tür. Özellikle AI agent'ları için graph tabanlı workflow'lar oluşturmayı sağlar.

### Temel Özellikler

| Özellik | Açıklama |
|---------|----------|
| StateGraph | State yönetimli graph yapısı |
| Nodes | İşlem noktaları |
| Edges | Geçiş kuralları |
| Checkpoints | State persistence |
| Human-in-the-loop | İnsan müdahalesi desteği |

### Claude Code + LangGraph

Claude Code'u LangGraph ile entegre etmek, kompleks AI workflow'ları oluşturmayı sağlar:
- Plan → Execute → Review döngüleri
- Parallel agent execution
- Conditional routing
- State persistence

---

## 15.2 Temel Kavramlar

### StateGraph

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
from operator import add

class AgentState(TypedDict):
    messages: Annotated[list, add]
    current_step: str
    results: dict

graph = StateGraph(AgentState)
```

### Nodes (İşlem Noktaları)

```python
def planner_node(state: AgentState) -> AgentState:
    """Planlama adımı."""
    # State'i oku
    messages = state["messages"]
    
    # İşlem yap
    plan = create_plan(messages[-1])
    
    # Yeni state döndür
    return {
        "messages": [{"role": "assistant", "content": plan}],
        "current_step": "execute"
    }

# Node'u graph'a ekle
graph.add_node("planner", planner_node)
```

### Edges (Geçişler)

```python
# Normal edge
graph.add_edge("planner", "executor")

# Conditional edge
def should_continue(state: AgentState) -> str:
    if state["results"].get("success"):
        return "finish"
    else:
        return "retry"

graph.add_conditional_edges(
    "executor",
    should_continue,
    {
        "finish": END,
        "retry": "planner"
    }
)
```

---

## 15.3 KIRO2 StateGraph Tasarımı

### State Tanımı

```python
# orchestrator/core/state.py

from typing import TypedDict, Annotated, Optional, Literal
from operator import add
from datetime import datetime
from dataclasses import dataclass

@dataclass
class ValidationResult:
    passed: bool
    score: float
    issues: list[str]

class KIROState(TypedDict):
    """KIRO2 Orchestrator State."""
    
    # Mesajlar (accumulator)
    messages: Annotated[list[dict], add]
    
    # Mevcut görev
    task_id: str
    task_type: Literal["generate", "validate", "review", "fix"]
    task_input: dict
    
    # İşlem durumu
    current_node: str
    iteration: int
    max_iterations: int
    
    # Sonuçlar
    generated_content: Optional[dict]
    validation_result: Optional[ValidationResult]
    final_output: Optional[dict]
    
    # Metadata
    started_at: str
    updated_at: str
    error: Optional[str]
```

### Graph Yapısı

```
                    ┌─────────────┐
                    │    START    │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   ROUTER    │
                    └──────┬──────┘
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │  GENERATE   │ │  VALIDATE   │ │   REVIEW    │
    └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
           │               │               │
           ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │   VERIFY    │ │   CHECK     │ │   APPROVE   │
    └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
           │               │               │
           ├───────────────┴───────────────┤
           │                               │
           ▼                               ▼
    ┌─────────────┐                 ┌─────────────┐
    │     FIX     │                 │    END      │
    └──────┬──────┘                 └─────────────┘
           │
           └─────────────► ROUTER (loop)
```

### Graph Implementation

```python
# orchestrator/core/graph.py

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from .state import KIROState
from .nodes import (
    router_node,
    generate_node,
    validate_node,
    review_node,
    verify_node,
    check_node,
    approve_node,
    fix_node
)

def build_kiro_graph() -> StateGraph:
    """KIRO2 orchestrator graph'ını oluştur."""
    
    # Graph oluştur
    graph = StateGraph(KIROState)
    
    # Node'ları ekle
    graph.add_node("router", router_node)
    graph.add_node("generate", generate_node)
    graph.add_node("validate", validate_node)
    graph.add_node("review", review_node)
    graph.add_node("verify", verify_node)
    graph.add_node("check", check_node)
    graph.add_node("approve", approve_node)
    graph.add_node("fix", fix_node)
    
    # Entry point
    graph.set_entry_point("router")
    
    # Router'dan conditional edges
    graph.add_conditional_edges(
        "router",
        route_task,
        {
            "generate": "generate",
            "validate": "validate",
            "review": "review",
            "end": END
        }
    )
    
    # Generate → Verify
    graph.add_edge("generate", "verify")
    
    # Verify conditional
    graph.add_conditional_edges(
        "verify",
        check_verification,
        {
            "pass": END,
            "fail": "fix",
            "retry": "generate"
        }
    )
    
    # Validate → Check
    graph.add_edge("validate", "check")
    
    # Check conditional
    graph.add_conditional_edges(
        "check",
        check_validation,
        {
            "pass": END,
            "fail": "router"
        }
    )
    
    # Review → Approve
    graph.add_edge("review", "approve")
    
    # Approve conditional
    graph.add_conditional_edges(
        "approve",
        check_approval,
        {
            "approved": END,
            "rejected": "fix",
            "needs_human": "human_review"
        }
    )
    
    # Fix → Router (loop back)
    graph.add_edge("fix", "router")
    
    return graph


def route_task(state: KIROState) -> str:
    """Görev tipine göre routing."""
    
    # Max iteration kontrolü
    if state["iteration"] >= state["max_iterations"]:
        return "end"
    
    task_type = state["task_type"]
    
    if task_type == "generate":
        return "generate"
    elif task_type == "validate":
        return "validate"
    elif task_type == "review":
        return "review"
    else:
        return "end"


def check_verification(state: KIROState) -> str:
    """Doğrulama sonucunu kontrol et."""
    
    result = state.get("validation_result")
    
    if result is None:
        return "retry"
    
    if result.passed and result.score >= 0.8:
        return "pass"
    elif state["iteration"] < 3:
        return "retry"
    else:
        return "fail"


def check_validation(state: KIROState) -> str:
    """Validation sonucunu kontrol et."""
    
    result = state.get("validation_result")
    
    if result and result.passed:
        return "pass"
    else:
        return "fail"


def check_approval(state: KIROState) -> str:
    """Onay durumunu kontrol et."""
    
    result = state.get("validation_result")
    
    if result is None:
        return "needs_human"
    
    if result.score >= 0.9:
        return "approved"
    elif result.score >= 0.7:
        return "needs_human"
    else:
        return "rejected"
```

---

## 15.4 Node Implementasyonları

### Router Node

```python
# orchestrator/core/nodes/router.py

from ..state import KIROState
from datetime import datetime

def router_node(state: KIROState) -> KIROState:
    """Görevi yönlendir ve state'i güncelle."""
    
    return {
        "current_node": "router",
        "iteration": state["iteration"] + 1,
        "updated_at": datetime.utcnow().isoformat()
    }
```

### Generate Node (Claude Entegrasyonu)

```python
# orchestrator/core/nodes/generate.py

import anthropic
from ..state import KIROState
from typing import Optional

client = anthropic.Anthropic()

def generate_node(state: KIROState) -> KIROState:
    """İçerik üret (Claude ile)."""
    
    task_input = state["task_input"]
    
    # Prompt oluştur
    prompt = build_generation_prompt(task_input)
    
    # Claude'u çağır
    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        system=get_system_prompt(),
        messages=[{"role": "user", "content": prompt}]
    )
    
    # Yanıtı parse et
    content = parse_generated_content(response.content[0].text)
    
    return {
        "current_node": "generate",
        "generated_content": content,
        "messages": [{
            "role": "assistant",
            "content": f"Generated content: {content.get('question_id', 'N/A')}"
        }]
    }


def build_generation_prompt(task_input: dict) -> str:
    """Üretim prompt'u oluştur."""
    
    topic = task_input.get("topic", "")
    difficulty = task_input.get("difficulty", 3)
    exam_type = task_input.get("exam_type", "AYT")
    
    return f"""Generate a {exam_type} question:
    
    Topic: {topic}
    Difficulty: {difficulty}/5
    
    Return a valid JSON object with all required fields.
    """


def get_system_prompt() -> str:
    return """You are KIRO2 Question Generator.
    Generate YKS exam questions in JSON format.
    Use LaTeX for math, UTF-8 for Turkish characters.
    """


def parse_generated_content(text: str) -> dict:
    """Claude yanıtını parse et."""
    import json
    
    # JSON bloğunu bul
    start = text.find("{")
    end = text.rfind("}") + 1
    
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    
    return {"error": "Failed to parse response", "raw": text}
```

### Verify Node

```python
# orchestrator/core/nodes/verify.py

from ..state import KIROState, ValidationResult
from ..validators import (
    SchemaValidator,
    ContentValidator,
    PedagogicalValidator
)

def verify_node(state: KIROState) -> KIROState:
    """Üretilen içeriği doğrula."""
    
    content = state.get("generated_content")
    
    if content is None or "error" in content:
        return {
            "current_node": "verify",
            "validation_result": ValidationResult(
                passed=False,
                score=0.0,
                issues=["No content to verify"]
            )
        }
    
    # Çoklu doğrulama
    validators = [
        SchemaValidator(),
        ContentValidator(),
        PedagogicalValidator()
    ]
    
    all_issues = []
    total_score = 0
    
    for validator in validators:
        result = validator.validate(content)
        all_issues.extend(result.get("issues", []))
        total_score += result.get("score", 0) * validator.weight
    
    passed = len(all_issues) == 0 and total_score >= 0.7
    
    return {
        "current_node": "verify",
        "validation_result": ValidationResult(
            passed=passed,
            score=total_score,
            issues=all_issues
        )
    }
```

### Fix Node

```python
# orchestrator/core/nodes/fix.py

import anthropic
from ..state import KIROState

client = anthropic.Anthropic()

def fix_node(state: KIROState) -> KIROState:
    """Sorunları düzelt."""
    
    content = state.get("generated_content", {})
    validation = state.get("validation_result")
    
    if validation is None:
        return {"current_node": "fix"}
    
    issues = validation.issues
    
    # Fix prompt oluştur
    prompt = f"""Fix the following issues in this question:

    Current content:
    {content}
    
    Issues to fix:
    {chr(10).join(f'- {issue}' for issue in issues)}
    
    Return the corrected JSON.
    """
    
    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )
    
    fixed_content = parse_fixed_content(response.content[0].text)
    
    return {
        "current_node": "fix",
        "generated_content": fixed_content,
        "task_type": "validate",  # Tekrar validate et
        "messages": [{
            "role": "assistant",
            "content": f"Fixed {len(issues)} issues"
        }]
    }
```

---

## 15.5 Checkpointing ve Persistence

### SQLite Checkpointer

```python
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

# Checkpoint database
conn = sqlite3.connect("kiro2_checkpoints.db", check_same_thread=False)
checkpointer = SqliteSaver(conn)

# Graph'ı compile et
app = build_kiro_graph().compile(checkpointer=checkpointer)
```

### PostgreSQL Checkpointer (Production)

```python
from langgraph.checkpoint.postgres import PostgresSaver
import psycopg2

# PostgreSQL connection
conn = psycopg2.connect(
    host="localhost",
    port=5434,
    database="kiro2",
    user="kiro2_user",
    password="password"
)

checkpointer = PostgresSaver(conn)
app = build_kiro_graph().compile(checkpointer=checkpointer)
```

### State Recovery

```python
# Thread ID ile state'i geri yükle
config = {"configurable": {"thread_id": "task-123"}}

# Son checkpoint'tan devam et
result = app.invoke(None, config)

# Veya belirli bir checkpoint'tan
result = app.invoke(None, {
    "configurable": {
        "thread_id": "task-123",
        "checkpoint_id": "checkpoint-456"
    }
})
```

---

## 15.6 Human-in-the-Loop

### Interrupt Points

```python
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# Human review node'u öncesinde interrupt
graph.add_node("human_review", human_review_node)

# Compile with interrupt
app = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=["human_review"]
)
```

### Human Review Implementation

```python
def run_with_human_review(task_input: dict) -> dict:
    """Human review ile çalıştır."""
    
    config = {"configurable": {"thread_id": f"task-{task_input['id']}"}}
    
    # İlk çalıştırma
    result = app.invoke(
        {"task_input": task_input, "task_type": "generate"},
        config
    )
    
    # Interrupt'a ulaşıldı mı?
    state = app.get_state(config)
    
    if state.next == ("human_review",):
        # Human review gerekli
        print("Human review needed:")
        print(state.values.get("generated_content"))
        
        # Human input al
        approval = input("Approve? (y/n): ")
        
        # State'i güncelle ve devam et
        app.update_state(
            config,
            {"human_approved": approval == "y"},
            as_node="human_review"
        )
        
        # Devam et
        result = app.invoke(None, config)
    
    return result
```

---

## 15.7 LangSmith Entegrasyonu

### Tracing Setup

```python
import os

# LangSmith environment variables
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "your-api-key"
os.environ["LANGCHAIN_PROJECT"] = "kiro2-orchestrator"
```

### Trace Visualization

LangSmith Dashboard'da görebilecekleriniz:
- Node execution timeline
- State transitions
- Token usage per node
- Error traces
- Latency metrics

### Custom Metadata

```python
from langsmith import traceable

@traceable(
    name="generate_question",
    metadata={"module": "kiro2", "type": "generation"}
)
def generate_node(state: KIROState) -> KIROState:
    # ...
```

---

## 15.8 Özet

### Checklist

- [ ] StateGraph tanımlandı
- [ ] Node'lar implement edildi
- [ ] Conditional edges eklendi
- [ ] Checkpointing yapılandırıldı
- [ ] Human-in-the-loop entegre edildi
- [ ] LangSmith tracing aktif

### Quick Reference

```python
# Temel graph oluşturma
graph = StateGraph(MyState)
graph.add_node("node_name", node_function)
graph.add_edge("from", "to")
graph.add_conditional_edges("from", condition_func, {"a": "node_a", "b": "node_b"})
graph.set_entry_point("start_node")
app = graph.compile(checkpointer=checkpointer)

# Çalıştırma
result = app.invoke(initial_state, config)
```

### Metrikler

| Metrik | Hedef |
|--------|-------|
| Graph execution time | < 30s |
| Node success rate | > 95% |
| Checkpoint recovery | 100% |
| State consistency | 100% |

---

**Önceki Bölüm:** [14 - GitHub Actions Entegrasyonu](./14-github-actions.md)  
**Sonraki Bölüm:** [16 - Test ve Kalite](./16-test-ve-kalite.md)
