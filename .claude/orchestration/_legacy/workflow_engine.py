"""
Workflow Engine - DAG-based Workflow Execution

Agent'lari sirali veya paralel olarak calistiran is akisi motoru.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
import json


class WorkflowStatus(Enum):
    """Workflow durumu"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class StepType(Enum):
    """Workflow adim tipi"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    LOOP = "loop"


@dataclass
class WorkflowStep:
    """Workflow adimi"""
    step_id: str
    name: str
    agent_id: str
    step_type: StepType = StepType.SEQUENTIAL
    input_mapping: dict = field(default_factory=dict)  # previous_step -> input_key
    condition: Optional[str] = None  # Condition expression for CONDITIONAL
    max_iterations: int = 10  # For LOOP type
    timeout_seconds: int = 300  # 5 dakika default
    retry_count: int = 3
    depends_on: list[str] = field(default_factory=list)  # Step IDs

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "name": self.name,
            "agent_id": self.agent_id,
            "step_type": self.step_type.value,
            "input_mapping": self.input_mapping,
            "condition": self.condition,
            "max_iterations": self.max_iterations,
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "depends_on": self.depends_on,
        }


@dataclass
class StepResult:
    """Adim sonucu"""
    step_id: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    tokens_used: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "tokens_used": self.tokens_used,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class WorkflowDefinition:
    """Workflow tanimi"""
    workflow_id: str
    name: str
    description: str = ""
    steps: list[WorkflowStep] = field(default_factory=list)
    initial_input: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "steps": [s.to_dict() for s in self.steps],
            "initial_input": self.initial_input,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowDefinition":
        steps = [
            WorkflowStep(
                step_id=s["step_id"],
                name=s["name"],
                agent_id=s["agent_id"],
                step_type=StepType(s.get("step_type", "sequential")),
                input_mapping=s.get("input_mapping", {}),
                condition=s.get("condition"),
                max_iterations=s.get("max_iterations", 10),
                timeout_seconds=s.get("timeout_seconds", 300),
                retry_count=s.get("retry_count", 3),
                depends_on=s.get("depends_on", []),
            )
            for s in data.get("steps", [])
        ]

        return cls(
            workflow_id=data["workflow_id"],
            name=data["name"],
            description=data.get("description", ""),
            steps=steps,
            initial_input=data.get("initial_input", {}),
            metadata=data.get("metadata", {}),
        )


@dataclass
class WorkflowExecution:
    """Workflow calisma durumu"""
    execution_id: str
    workflow: WorkflowDefinition
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_step_index: int = 0
    step_results: dict[str, StepResult] = field(default_factory=dict)
    context: dict = field(default_factory=dict)  # Shared context between steps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    @property
    def duration_ms(self) -> float:
        if not self.started_at:
            return 0.0
        end = self.completed_at or datetime.now()
        return (end - self.started_at).total_seconds() * 1000

    def to_dict(self) -> dict:
        return {
            "execution_id": self.execution_id,
            "workflow": self.workflow.to_dict(),
            "status": self.status.value,
            "current_step_index": self.current_step_index,
            "step_results": {k: v.to_dict() for k, v in self.step_results.items()},
            "context": self.context,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "duration_ms": self.duration_ms,
        }


# Agent executor function type
AgentExecutor = Callable[[str, dict], Any]


class WorkflowEngine:
    """
    Workflow Engine - DAG-based execution

    Ozellikler:
    - Sequential execution
    - Parallel execution
    - Conditional branching
    - Loop support
    - Retry logic
    - Timeout handling
    - Context sharing between steps
    """

    def __init__(self, agent_executor: Optional[AgentExecutor] = None):
        self.agent_executor = agent_executor or self._default_executor
        self._executions: dict[str, WorkflowExecution] = {}
        self._lock = asyncio.Lock()

    async def _default_executor(self, agent_id: str, input_data: dict) -> Any:
        """Default agent executor - placeholder"""
        # Bu MetaOrchestrator tarafindan override edilecek
        return {"status": "success", "agent": agent_id, "input": input_data}

    def set_executor(self, executor: AgentExecutor) -> None:
        """Agent executor'u ayarla"""
        self.agent_executor = executor

    async def execute_workflow(
        self,
        workflow: WorkflowDefinition,
        initial_context: Optional[dict] = None
    ) -> WorkflowExecution:
        """
        Workflow'u calistir

        Args:
            workflow: Workflow tanimi
            initial_context: Baslangic context'i

        Returns:
            WorkflowExecution sonucu
        """
        execution = WorkflowExecution(
            execution_id=f"exec-{workflow.workflow_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            workflow=workflow,
            context=initial_context or workflow.initial_input.copy(),
            started_at=datetime.now(),
        )

        async with self._lock:
            self._executions[execution.execution_id] = execution

        try:
            execution.status = WorkflowStatus.RUNNING

            # Build dependency graph
            dep_graph = self._build_dependency_graph(workflow.steps)

            # Execute steps respecting dependencies
            await self._execute_steps(execution, dep_graph)

            execution.status = WorkflowStatus.COMPLETED
        except asyncio.CancelledError:
            execution.status = WorkflowStatus.CANCELLED
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error = str(e)
        finally:
            execution.completed_at = datetime.now()

        return execution

    def _build_dependency_graph(self, steps: list[WorkflowStep]) -> dict[str, list[str]]:
        """Bagimliilik grafigi olustur"""
        graph = {}
        for step in steps:
            graph[step.step_id] = step.depends_on.copy()
        return graph

    async def _execute_steps(
        self,
        execution: WorkflowExecution,
        dep_graph: dict[str, list[str]]
    ) -> None:
        """Adimlari dependency sirasina gore calistir"""
        completed = set()
        steps_by_id = {s.step_id: s for s in execution.workflow.steps}

        while len(completed) < len(execution.workflow.steps):
            # Find steps ready to execute (all dependencies satisfied)
            ready_steps = []
            for step_id, deps in dep_graph.items():
                if step_id not in completed and all(d in completed for d in deps):
                    ready_steps.append(steps_by_id[step_id])

            if not ready_steps:
                raise RuntimeError("Circular dependency detected or no steps available")

            # Group by step type for parallel execution
            parallel_steps = [s for s in ready_steps if s.step_type == StepType.PARALLEL]
            sequential_steps = [s for s in ready_steps if s.step_type != StepType.PARALLEL]

            # Execute parallel steps together
            if parallel_steps:
                results = await self._execute_parallel(execution, parallel_steps)
                for step, result in zip(parallel_steps, results):
                    execution.step_results[step.step_id] = result
                    if result.success:
                        self._update_context(execution, step, result)
                        completed.add(step.step_id)
                    else:
                        raise RuntimeError(f"Step {step.step_id} failed: {result.error}")

            # Execute sequential steps one by one
            for step in sequential_steps:
                result = await self._execute_step(execution, step)
                execution.step_results[step.step_id] = result

                if result.success:
                    self._update_context(execution, step, result)
                    completed.add(step.step_id)
                else:
                    raise RuntimeError(f"Step {step.step_id} failed: {result.error}")

    async def _execute_step(
        self,
        execution: WorkflowExecution,
        step: WorkflowStep
    ) -> StepResult:
        """Tek adimi calistir"""
        start_time = datetime.now()

        # Prepare input from context
        step_input = self._prepare_step_input(execution, step)

        # Handle different step types
        if step.step_type == StepType.CONDITIONAL:
            return await self._execute_conditional(execution, step, step_input)
        elif step.step_type == StepType.LOOP:
            return await self._execute_loop(execution, step, step_input)
        else:
            return await self._execute_with_retry(step, step_input, start_time)

    async def _execute_with_retry(
        self,
        step: WorkflowStep,
        step_input: dict,
        start_time: datetime
    ) -> StepResult:
        """Retry logic ile calistir"""
        last_error = None

        for attempt in range(step.retry_count):
            try:
                # Execute with timeout
                result = await asyncio.wait_for(
                    self.agent_executor(step.agent_id, step_input),
                    timeout=step.timeout_seconds
                )

                duration = (datetime.now() - start_time).total_seconds() * 1000

                return StepResult(
                    step_id=step.step_id,
                    success=True,
                    output=result,
                    duration_ms=duration,
                )
            except asyncio.TimeoutError:
                last_error = f"Timeout after {step.timeout_seconds}s"
            except Exception as e:
                last_error = str(e)

            # Wait before retry
            if attempt < step.retry_count - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        duration = (datetime.now() - start_time).total_seconds() * 1000
        return StepResult(
            step_id=step.step_id,
            success=False,
            error=last_error,
            duration_ms=duration,
        )

    async def _execute_parallel(
        self,
        execution: WorkflowExecution,
        steps: list[WorkflowStep]
    ) -> list[StepResult]:
        """Paralel adimlari calistir"""
        tasks = []
        for step in steps:
            step_input = self._prepare_step_input(execution, step)
            task = self._execute_with_retry(step, step_input, datetime.now())
            tasks.append(task)

        return await asyncio.gather(*tasks)

    async def _execute_conditional(
        self,
        execution: WorkflowExecution,
        step: WorkflowStep,
        step_input: dict
    ) -> StepResult:
        """Kosullu adim calistir"""
        if not step.condition:
            return await self._execute_with_retry(step, step_input, datetime.now())

        # Evaluate condition
        try:
            condition_result = self._evaluate_condition(step.condition, execution.context)
            if condition_result:
                return await self._execute_with_retry(step, step_input, datetime.now())
            else:
                return StepResult(
                    step_id=step.step_id,
                    success=True,
                    output={"skipped": True, "reason": "Condition not met"},
                )
        except Exception as e:
            return StepResult(
                step_id=step.step_id,
                success=False,
                error=f"Condition evaluation failed: {e}",
            )

    async def _execute_loop(
        self,
        execution: WorkflowExecution,
        step: WorkflowStep,
        step_input: dict
    ) -> StepResult:
        """Loop adim calistir"""
        results = []
        start_time = datetime.now()

        for iteration in range(step.max_iterations):
            # Add iteration to input
            iteration_input = {**step_input, "_iteration": iteration}

            result = await self._execute_with_retry(step, iteration_input, datetime.now())

            if not result.success:
                return result

            results.append(result.output)

            # Check break condition
            if step.condition:
                should_continue = self._evaluate_condition(step.condition, {
                    **execution.context,
                    "_result": result.output,
                    "_iteration": iteration,
                })
                if not should_continue:
                    break

        duration = (datetime.now() - start_time).total_seconds() * 1000
        return StepResult(
            step_id=step.step_id,
            success=True,
            output={"iterations": len(results), "results": results},
            duration_ms=duration,
        )

    def _prepare_step_input(
        self,
        execution: WorkflowExecution,
        step: WorkflowStep
    ) -> dict:
        """Adim icin input hazirla"""
        step_input = {}

        # Add context
        step_input["_context"] = execution.context

        # Map from previous step results
        for prev_step_id, input_key in step.input_mapping.items():
            if prev_step_id in execution.step_results:
                step_input[input_key] = execution.step_results[prev_step_id].output

        return step_input

    def _update_context(
        self,
        execution: WorkflowExecution,
        step: WorkflowStep,
        result: StepResult
    ) -> None:
        """Context'i sonuc ile guncelle"""
        if result.output and isinstance(result.output, dict):
            execution.context[step.step_id] = result.output
        else:
            execution.context[step.step_id] = {"output": result.output}

    def _evaluate_condition(self, condition: str, context: dict) -> bool:
        """Kosul ifadesini degerlendir"""
        # Simple condition evaluation - guvenlik icin sinirli
        # Format: "key operator value"
        # Ornek: "success == true", "count > 5"

        try:
            # Create safe evaluation context
            safe_context = {k: v for k, v in context.items() if not k.startswith("_")}
            safe_context.update({"true": True, "false": False, "null": None})

            # Very basic evaluation
            return eval(condition, {"__builtins__": {}}, safe_context)
        except Exception:
            return False

    async def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Execution bilgisi getir"""
        return self._executions.get(execution_id)

    async def cancel_execution(self, execution_id: str) -> bool:
        """Execution'i iptal et"""
        if execution_id in self._executions:
            self._executions[execution_id].status = WorkflowStatus.CANCELLED
            return True
        return False

    async def pause_execution(self, execution_id: str) -> bool:
        """Execution'i duraklat"""
        if execution_id in self._executions:
            self._executions[execution_id].status = WorkflowStatus.PAUSED
            return True
        return False


# Helper functions for building workflows
def create_sequential_workflow(
    name: str,
    agent_ids: list[str],
    initial_input: Optional[dict] = None
) -> WorkflowDefinition:
    """Basit sirali workflow olustur"""
    steps = []
    for i, agent_id in enumerate(agent_ids):
        step = WorkflowStep(
            step_id=f"step-{i}",
            name=f"Step {i}: {agent_id}",
            agent_id=agent_id,
            step_type=StepType.SEQUENTIAL,
            depends_on=[f"step-{i-1}"] if i > 0 else [],
        )
        steps.append(step)

    return WorkflowDefinition(
        workflow_id=f"wf-{name}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        name=name,
        steps=steps,
        initial_input=initial_input or {},
    )


def create_parallel_workflow(
    name: str,
    agent_ids: list[str],
    initial_input: Optional[dict] = None
) -> WorkflowDefinition:
    """Paralel workflow olustur"""
    steps = [
        WorkflowStep(
            step_id=f"step-{i}",
            name=f"Parallel Step: {agent_id}",
            agent_id=agent_id,
            step_type=StepType.PARALLEL,
        )
        for i, agent_id in enumerate(agent_ids)
    ]

    return WorkflowDefinition(
        workflow_id=f"wf-{name}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        name=name,
        steps=steps,
        initial_input=initial_input or {},
    )
