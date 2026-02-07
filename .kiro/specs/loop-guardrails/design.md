# Design Document - Loop Guardrails Sistemi

## Overview

Loop Guardrails sistemi, AI agent'ların infinite loop'a girmesini önleyen çok katmanlı koruma mekanizmasıdır. maxTurns counter, timeout timer, circuit breaker, recursion depth limit, progress monitoring, resource limits, deadlock detection ve emergency stop ile %100 loop prevention sağlar.

**Temel Özellikler:**
- maxTurns counter ile iterasyon limiti
- Timeout timer ile zaman aşımı koruması
- Circuit breaker pattern ile cascade failure önleme
- Recursion depth limit ile stack overflow önleme
- Progress monitoring ile stall detection
- Resource limits ile exhaustion önleme
- Deadlock detection ile stuck process tespiti
- Emergency stop mechanism

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Agent Execution Start                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │ Agent    │───▶│ Task     │───▶│ Loop     │                  │
│  │ Init     │    │ Start    │    │ Begin    │                  │
│  └──────────┘    └──────────┘    └────┬─────┘                  │
└────────────────────────────────────────┼──────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Guardrail Initialization                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  GuardrailManager                                         │  │
│  │  - Initialize maxTurns counter (default: 100)            │  │
│  │  - Start timeout timer (default: 300s)                   │  │
│  │  - Initialize circuit breaker (closed state)             │  │
│  │  - Set recursion limit (default: 1000)                   │  │
│  │  - Start resource monitors                               │  │
│  │  - Initialize progress tracker                           │  │
│  └────────────────────┬─────────────────────────────────────┘  │
└─────────────────────────┼──────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Loop Execution with Monitoring                      │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Loop Iteration N                                        │   │
│  │  ┌──────────┐    ┌──────────┐    ┌──────────┐          │   │
│  │  │ Execute  │───▶│ Check    │───▶│ Continue │          │   │
│  │  │ Step     │    │ Guards   │    │ or Stop  │          │   │
│  │  └──────────┘    └────┬─────┘    └──────────┘          │   │
│  └────────────────────────┼──────────────────────────────────┘   │
│                           │                                      │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Parallel Guardrail Checks                              │   │
│  │                                                          │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │ maxTurns     │  │ Timeout      │  │ Circuit      │  │   │
│  │  │ Check        │  │ Check        │  │ Breaker      │  │   │
│  │  │              │  │              │  │ Check        │  │   │
│  │  │ counter++    │  │ elapsed_time │  │ failure_rate │  │   │
│  │  │ if > limit:  │  │ if > timeout:│  │ if open:     │  │   │
│  │  │   STOP       │  │   STOP       │  │   STOP       │  │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │   │
│  │         │                 │                 │           │   │
│  │  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐  │   │
│  │  │ Recursion    │  │ Progress     │  │ Resource     │  │   │
│  │  │ Depth        │  │ Monitor      │  │ Limits       │  │   │
│  │  │              │  │              │  │              │  │   │
│  │  │ depth++      │  │ check_stall()│  │ memory_check │  │   │
│  │  │ if > limit:  │  │ if stalled:  │  │ cpu_check    │  │   │
│  │  │   STOP       │  │   WARN       │  │ if exceeded: │  │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │   │
│  │         │                 │                 │           │   │
│  │  ┌──────┴───────┐  ┌──────┴───────┐                    │   │
│  │  │ Deadlock     │  │ Emergency    │                    │   │
│  │  │ Detection    │  │ Stop         │                    │   │
│  │  │              │  │              │                    │   │
│  │  │ check_locks()│  │ if triggered:│                    │   │
│  │  │ if deadlock: │  │   FORCE_STOP │                    │   │
│  │  │   STOP       │  │              │                    │   │
│  │  └──────┬───────┘  └──────┬───────┘                    │   │
│  └─────────┼──────────────────┼─────────────────────────────┘   │
│            │                  │                                  │
│            └──────────────────┘                                  │
│                     │                                            │
│                     ▼                                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Decision: Continue or Stop?                            │   │
│  │                                                          │   │
│  │  All Guards OK? ───▶ Continue to next iteration         │   │
│  │  Any Guard Failed? ─▶ Stop loop, return partial result  │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────┼──────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Loop Termination & Cleanup                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Cleanup Actions:                                         │  │
│  │  - Stop all timers                                        │  │
│  │  - Release resources                                      │  │
│  │  - Log final statistics                                   │  │
│  │  - Generate termination report                            │  │
│  │                                                           │  │
│  │  Return:                                                  │  │
│  │  - Partial result (if stopped early)                     │  │
│  │  - Complete result (if finished normally)                │  │
│  │  - Termination reason                                    │  │
│  │  - Statistics (iterations, time, resource usage)         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Component Architecture

```
backend/
├── app/
│   ├── guardrails/
│   │   ├── __init__.py
│   │   ├── manager.py                   # GuardrailManager orchestration
│   │   ├── guards/
│   │   │   ├── __init__.py
│   │   │   ├── base_guard.py            # Abstract base guard
│   │   │   ├── max_turns_guard.py
│   │   │   ├── timeout_guard.py
│   │   │   ├── circuit_breaker_guard.py
│   │   │   ├── recursion_depth_guard.py
│   │   │   ├── progress_monitor_guard.py
│   │   │   ├── resource_limit_guard.py
│   │   │   ├── deadlock_detection_guard.py
│   │   │   └── emergency_stop_guard.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── guard_result.py          # Guard check result
│   │   │   ├── termination_report.py    # Loop termination report
│   │   │   └── guard_config.py          # Guard configuration
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── resource_monitor.py      # CPU, memory monitoring
│   │       └── lock_tracker.py          # Lock dependency tracking
├── tests/
│   └── guardrails/
│       ├── test_guards.py
│       ├── test_manager.py
│       └── test_integration.py
└── examples/
    └── guardrails_demo.py               # Usage examples
```

## Components and Interfaces

### 1. Base Guard

```python
from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel
from enum import Enum

class GuardStatus(str, Enum):
    OK = "OK"
    WARNING = "WARNING"
    STOP = "STOP"

class GuardResult(BaseModel):
    guard_name: str
    status: GuardStatus
    message: str
    details: dict
    should_stop: bool

class BaseGuard(ABC):
    """Abstract base class for loop guardrails"""
    
    def __init__(self, config: dict):
        self.config = config
        self.name = self.__class__.__name__.replace("Guard", "")
    
    @abstractmethod
    async def check(self, context: dict) -> GuardResult:
        """
        Check if guard condition is violated
        
        Args:
            context: Execution context (iteration count, elapsed time, etc.)
            
        Returns:
            Guard result with status and details
        """
        pass
    
    @abstractmethod
    def reset(self):
        """Reset guard state for new execution"""
        pass
```

### 2. maxTurns Guard

```python
class MaxTurnsGuard(BaseGuard):
    """Enforces maximum iteration limit"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.max_turns = config.get("max_turns", 100)
        self.current_turn = 0
    
    async def check(self, context: dict) -> GuardResult:
        self.current_turn += 1
        
        if self.current_turn > self.max_turns:
            return GuardResult(
                guard_name=self.name,
                status=GuardStatus.STOP,
                message=f"Maximum iterations exceeded: {self.current_turn}/{self.max_turns}",
                details={
                    "current_turn": self.current_turn,
                    "max_turns": self.max_turns,
                },
                should_stop=True
            )
        
        # Warning at 80% threshold
        if self.current_turn >= self.max_turns * 0.8:
            return GuardResult(
                guard_name=self.name,
                status=GuardStatus.WARNING,
                message=f"Approaching iteration limit: {self.current_turn}/{self.max_turns}",
                details={
                    "current_turn": self.current_turn,
                    "max_turns": self.max_turns,
                },
                should_stop=False
            )
        
        return GuardResult(
            guard_name=self.name,
            status=GuardStatus.OK,
            message=f"Iteration {self.current_turn}/{self.max_turns}",
            details={
                "current_turn": self.current_turn,
                "max_turns": self.max_turns,
            },
            should_stop=False
        )
    
    def reset(self):
        self.current_turn = 0
```

### 3. Circuit Breaker Guard

```python
import time
from enum import Enum

class CircuitState(str, Enum):
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Blocking requests
    HALF_OPEN = "HALF_OPEN"  # Testing recovery

class CircuitBreakerGuard(BaseGuard):
    """Circuit breaker pattern to prevent cascade failures"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.failure_threshold = config.get("failure_threshold", 5)
        self.timeout = config.get("timeout", 60)  # seconds
        self.half_open_max_calls = config.get("half_open_max_calls", 3)
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
    
    async def check(self, context: dict) -> GuardResult:
        current_time = time.time()
        
        # Check if circuit is open
        if self.state == CircuitState.OPEN:
            # Check if timeout has passed
            if current_time - self.last_failure_time >= self.timeout:
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
            else:
                return GuardResult(
                    guard_name=self.name,
                    status=GuardStatus.STOP,
                    message="Circuit breaker is OPEN, blocking execution",
                    details={
                        "state": self.state,
                        "failure_count": self.failure_count,
                        "time_until_retry": self.timeout - (current_time - self.last_failure_time),
                    },
                    should_stop=True
                )
        
        # Record success or failure from context
        if context.get("last_operation_failed", False):
            self.failure_count += 1
            self.last_failure_time = current_time
            
            if self.state == CircuitState.HALF_OPEN:
                # Failure in half-open state, reopen circuit
                self.state = CircuitState.OPEN
                return GuardResult(
                    guard_name=self.name,
                    status=GuardStatus.STOP,
                    message="Circuit breaker reopened due to failure in HALF_OPEN state",
                    details={"state": self.state, "failure_count": self.failure_count},
                    should_stop=True
                )
            
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                return GuardResult(
                    guard_name=self.name,
                    status=GuardStatus.STOP,
                    message=f"Circuit breaker opened after {self.failure_count} failures",
                    details={"state": self.state, "failure_count": self.failure_count},
                    should_stop=True
                )
        else:
            self.success_count += 1
            
            if self.state == CircuitState.HALF_OPEN:
                self.half_open_calls += 1
                if self.half_open_calls >= self.half_open_max_calls:
                    # Enough successes, close circuit
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
        
        return GuardResult(
            guard_name=self.name,
            status=GuardStatus.OK,
            message=f"Circuit breaker state: {self.state}",
            details={
                "state": self.state,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
            },
            should_stop=False
        )
    
    def reset(self):
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
```

### 4. Guardrail Manager

```python
import asyncio
import time
from typing import List, Dict

class GuardrailManager:
    """Orchestrates all loop guardrails"""
    
    def __init__(self, config: Dict[str, any]):
        self.config = config
        self.guards: List[BaseGuard] = []
        self.start_time = None
        self._register_guards()
    
    def _register_guards(self):
        """Register all guards"""
        from .guards import (
            MaxTurnsGuard,
            TimeoutGuard,
            CircuitBreakerGuard,
            RecursionDepthGuard,
            ProgressMonitorGuard,
            ResourceLimitGuard,
            DeadlockDetectionGuard,
            EmergencyStopGuard,
        )
        
        self.guards = [
            MaxTurnsGuard(self.config.get("max_turns", {})),
            TimeoutGuard(self.config.get("timeout", {})),
            CircuitBreakerGuard(self.config.get("circuit_breaker", {})),
            RecursionDepthGuard(self.config.get("recursion_depth", {})),
            ProgressMonitorGuard(self.config.get("progress_monitor", {})),
            ResourceLimitGuard(self.config.get("resource_limits", {})),
            DeadlockDetectionGuard(self.config.get("deadlock_detection", {})),
            EmergencyStopGuard(self.config.get("emergency_stop", {})),
        ]
    
    async def check_all_guards(self, context: Dict[str, any]) -> Dict[str, any]:
        """
        Check all guards in parallel
        
        Args:
            context: Execution context
            
        Returns:
            Aggregated guard results
        """
        # Add elapsed time to context
        if self.start_time:
            context["elapsed_time"] = time.time() - self.start_time
        
        # Check all guards in parallel
        tasks = [guard.check(context) for guard in self.guards]
        results = await asyncio.gather(*tasks)
        
        # Aggregate results
        should_stop = any(r.should_stop for r in results)
        warnings = [r for r in results if r.status == GuardStatus.WARNING]
        stops = [r for r in results if r.status == GuardStatus.STOP]
        
        return {
            "should_stop": should_stop,
            "guard_results": [r.dict() for r in results],
            "warnings": [r.dict() for r in warnings],
            "stops": [r.dict() for r in stops],
            "summary": self._generate_summary(results)
        }
    
    def start_execution(self):
        """Start execution timer"""
        self.start_time = time.time()
        for guard in self.guards:
            guard.reset()
    
    def _generate_summary(self, results: List[GuardResult]) -> str:
        """Generate human-readable summary"""
        stops = [r for r in results if r.status == GuardStatus.STOP]
        if stops:
            return f"⛔ Loop stopped: {stops[0].message}"
        
        warnings = [r for r in results if r.status == GuardStatus.WARNING]
        if warnings:
            return f"⚠️ Warnings: {', '.join(w.message for w in warnings)}"
        
        return "✅ All guardrails OK"
```

## Data Models

```python
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from enum import Enum

class GuardStatus(str, Enum):
    OK = "OK"
    WARNING = "WARNING"
    STOP = "STOP"

class GuardResult(BaseModel):
    guard_name: str = Field(..., description="Name of the guard")
    status: GuardStatus = Field(..., description="Guard status")
    message: str = Field(..., description="Human-readable message")
    details: Dict[str, any] = Field(default_factory=dict, description="Detailed information")
    should_stop: bool = Field(..., description="Whether execution should stop")

class TerminationReport(BaseModel):
    reason: str = Field(..., description="Termination reason")
    total_iterations: int = Field(..., description="Total iterations completed")
    elapsed_time_seconds: float = Field(..., description="Total elapsed time")
    guard_results: List[GuardResult] = Field(..., description="Final guard results")
    partial_result: Optional[any] = Field(None, description="Partial result if stopped early")
    resource_usage: Dict[str, any] = Field(default_factory=dict, description="Resource usage statistics")

class GuardConfig(BaseModel):
    max_turns: int = Field(default=100, description="Maximum iterations")
    timeout_seconds: int = Field(default=300, description="Timeout in seconds")
    failure_threshold: int = Field(default=5, description="Circuit breaker failure threshold")
    recursion_limit: int = Field(default=1000, description="Maximum recursion depth")
    memory_limit_mb: int = Field(default=1024, description="Memory limit in MB")
    cpu_limit_percent: float = Field(default=80.0, description="CPU usage limit percentage")
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system.*

### Property 1: maxTurns Enforcement
*For any* loop execution with maxTurns=N, *the loop SHALL terminate after at most N iterations.*

**Validates: Requirements 1.1, 1.2, 1.3, 1.4**

### Property 2: Timeout Enforcement
*For any* loop execution with timeout=T seconds, *the loop SHALL terminate within T seconds.*

**Validates: Requirements 2.1, 2.2, 2.3**

### Property 3: Circuit Breaker State Transitions
*For any* circuit breaker with failure_threshold=F, *after F consecutive failures, the state SHALL transition to OPEN.*

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

### Property 4: Recursion Depth Enforcement
*For any* recursive call with depth_limit=D, *recursion SHALL not exceed D levels.*

**Validates: Requirements 4.1, 4.2, 4.3**

### Property 5: Resource Limit Enforcement
*For any* execution with memory_limit=M MB, *if memory usage exceeds M, the execution SHALL be terminated.*

**Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6**

### Property 6: Emergency Stop Responsiveness
*For any* emergency stop signal, *the execution SHALL terminate within 1 second.*

**Validates: Requirements 8.1, 8.2, 8.3**

## Error Handling

```python
class GuardrailError(Exception):
    """Base exception for guardrails"""
    pass

class MaxTurnsExceeded(GuardrailError):
    """Maximum iterations exceeded"""
    pass

class TimeoutExceeded(GuardrailError):
    """Timeout exceeded"""
    pass

class CircuitBreakerOpen(GuardrailError):
    """Circuit breaker is open"""
    pass

# Error handling in manager
async def check_all_guards(self, context: Dict[str, any]) -> Dict[str, any]:
    try:
        # ... guard checking logic ...
    except Exception as e:
        logger.exception(f"Guard check error: {e}")
        return {
            "should_stop": True,
            "error": str(e),
            "summary": "⛔ Guardrail system error, stopping execution"
        }
```

## Testing Strategy

### Unit Tests
- Test each guard independently
- Test guard reset functionality
- Test edge cases (e.g., timeout at exactly limit)

### Property-Based Tests
- Generate random execution scenarios
- Verify maxTurns property
- Verify timeout property
- Verify circuit breaker state transitions

### Integration Tests
- Test full guardrail manager
- Test multiple guards triggering simultaneously
- Test emergency stop

**Test Configuration**: Minimum 100 iterations per property test
