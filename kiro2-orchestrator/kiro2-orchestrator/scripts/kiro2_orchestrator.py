#!/usr/bin/env python3
"""
KIRO2 Claude Flow Orchestrator
==============================
Multi-agent orchestration for KIRO2 EdTech platform.

Usage:
    python kiro2_orchestrator.py "soru üret: TYT matematik"
    python kiro2_orchestrator.py --pipeline yks_question_generation
    python kiro2_orchestrator.py --dry-run "test routing"
"""

import os
import sys
import json
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Try to import yaml, provide fallback
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    print("⚠️  PyYAML not installed. Run: pip install pyyaml")

# ============================================================================
# CONFIGURATION - Windows paths
# ============================================================================

SCRIPT_DIR = Path(__file__).parent
ORCHESTRATOR_DIR = SCRIPT_DIR.parent  # kiro2-orchestrator/kiro2-orchestrator
CONFIG_DIR = ORCHESTRATOR_DIR / "config"
AGENTS_DIR = ORCHESTRATOR_DIR / "agents"
PIPELINES_DIR = ORCHESTRATOR_DIR / "pipelines"
WRAPPERS_DIR = ORCHESTRATOR_DIR / "wrappers"

# Windows path for KIRO2
KIRO2_ROOT = Path(r"C:\Users\husey\kiro2")
LOG_DIR = Path.home() / ".kiro2-orchestrator" / "logs"
HISTORY_FILE = Path.home() / ".kiro2-orchestrator" / "history.json"

# ============================================================================
# ENUMS & DATA CLASSES
# ============================================================================

class ModelType(Enum):
    CLAUDE_OPUS = "claude-opus-4"
    CLAUDE_SONNET = "claude-sonnet-4"
    CODEX = "codex"

class AgentType(Enum):
    CONTENT = "content_agent"
    API = "api_agent"
    DATA = "data_agent"
    UI = "ui_agent"
    QUALITY = "quality_agent"

@dataclass
class TaskResult:
    success: bool
    output: str
    agent: str
    model: str
    duration_seconds: float
    cost_estimate: float

# ============================================================================
# HARDCODED ROUTING RULES (fallback if no YAML)
# ============================================================================

DEFAULT_ROUTING = {
    "turkish_nlp": {
        "keywords": ["türkçe", "turkish", "nlp", "qwen", "sentiment", "duygu", "embedding"],
        "agent": "content_agent",
        "model": "claude-opus-4",
        "weight": 0.9
    },
    "yks_content": {
        "keywords": ["soru", "question", "yks", "tyt", "ayt", "ösym", "test"],
        "agent": "content_agent",
        "model": "claude-sonnet-4",
        "weight": 0.8
    },
    "backend": {
        "keywords": ["fastapi", "api", "endpoint", "backend", "route", "service"],
        "agent": "api_agent",
        "model": "codex",
        "weight": 0.7
    },
    "frontend": {
        "keywords": ["react", "component", "jsx", "tsx", "frontend", "ui", "css", "tailwind"],
        "agent": "ui_agent",
        "model": "codex",
        "weight": 0.8
    },
    "database": {
        "keywords": ["postgres", "sql", "database", "migration", "schema", "query"],
        "agent": "data_agent",
        "model": "claude-sonnet-4",
        "weight": 0.7
    },
    "testing": {
        "keywords": ["test", "jest", "pytest", "coverage", "unit"],
        "agent": "quality_agent",
        "model": "codex",
        "weight": 0.7
    },
    "security": {
        "keywords": ["security", "auth", "vulnerability", "idor", "injection", "xss"],
        "agent": "quality_agent",
        "model": "claude-opus-4",
        "weight": 0.9
    },
    "devops": {
        "keywords": ["docker", "kubernetes", "ci/cd", "github actions", "deploy"],
        "agent": "api_agent",
        "model": "codex",
        "weight": 0.6
    }
}

# ============================================================================
# SMART ROUTER
# ============================================================================

class SmartRouter:
    """Route tasks to appropriate agents."""
    
    def __init__(self):
        self.routing_rules = DEFAULT_ROUTING
    
    def route(self, task: str) -> Tuple[str, str, str, float]:
        """
        Route task to agent and model.
        
        Returns:
            (agent_name, model, category, confidence)
        """
        task_lower = task.lower()
        
        scores = {}
        
        for category, config in self.routing_rules.items():
            keywords = config["keywords"]
            weight = config["weight"]
            
            matched = sum(1 for kw in keywords if kw in task_lower)
            if matched > 0:
                scores[category] = matched * weight
        
        if scores:
            best_category = max(scores, key=scores.get)
            config = self.routing_rules[best_category]
            confidence = min(scores[best_category] / 3, 1.0)  # Normalize to 0-1
            
            return (
                config["agent"],
                config["model"],
                best_category,
                confidence
            )
        
        # Fallback
        return ("content_agent", "codex", "general", 0.3)

# ============================================================================
# EXECUTION ENGINE
# ============================================================================

class ExecutionEngine:
    """Execute tasks using Claude Code or Codex CLI."""
    
    def __init__(self):
        self.claude_available = self._check_claude()
        self.codex_available = self._check_codex()
    
    def _check_claude(self) -> bool:
        """Check if Claude CLI is available."""
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                shell=True
            )
            return result.returncode == 0
        except:
            return False
    
    def _check_codex(self) -> bool:
        """Check if Codex CLI is available."""
        try:
            result = subprocess.run(
                ["codex", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                shell=True
            )
            return result.returncode == 0
        except:
            return False
    
    def execute(self, task: str, model: str, dry_run: bool = False) -> TaskResult:
        """Execute task with appropriate tool."""
        
        if dry_run:
            return TaskResult(
                success=True,
                output=f"[DRY RUN] Would execute with {model}:\n{task[:200]}...",
                agent="dry_run",
                model=model,
                duration_seconds=0,
                cost_estimate=0
            )
        
        if model == "codex":
            return self._execute_codex(task)
        else:
            return self._execute_claude(task, model)
    
    def _execute_claude(self, task: str, model: str) -> TaskResult:
        """Execute with Claude Code CLI."""
        start_time = datetime.now()
        
        if not self.claude_available:
            return TaskResult(
                success=False,
                output="❌ Claude CLI not available. Install: npm install -g @anthropic-ai/claude-code",
                agent="claude",
                model=model,
                duration_seconds=0,
                cost_estimate=0
            )
        
        try:
            cmd = f'claude -p "{task}"'
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(KIRO2_ROOT),
                shell=True
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return TaskResult(
                success=result.returncode == 0,
                output=result.stdout or result.stderr or "(no output)",
                agent="claude",
                model=model,
                duration_seconds=duration,
                cost_estimate=self._estimate_cost(model, len(task), len(result.stdout or ""))
            )
            
        except subprocess.TimeoutExpired:
            return TaskResult(
                success=False,
                output="⏱️ Timeout: Task exceeded 300 seconds",
                agent="claude",
                model=model,
                duration_seconds=300,
                cost_estimate=0
            )
        except Exception as e:
            return TaskResult(
                success=False,
                output=f"❌ Error: {str(e)}",
                agent="claude",
                model=model,
                duration_seconds=0,
                cost_estimate=0
            )
    
    def _execute_codex(self, task: str) -> TaskResult:
        """Execute with Codex CLI."""
        start_time = datetime.now()
        
        if not self.codex_available:
            return TaskResult(
                success=False,
                output="❌ Codex CLI not available. Install: npm install -g @openai/codex",
                agent="codex",
                model="codex",
                duration_seconds=0,
                cost_estimate=0
            )
        
        try:
            cmd = f'codex "{task}"'
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(KIRO2_ROOT),
                shell=True
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return TaskResult(
                success=result.returncode == 0,
                output=result.stdout or result.stderr or "(no output)",
                agent="codex",
                model="codex",
                duration_seconds=duration,
                cost_estimate=self._estimate_cost("codex", len(task), len(result.stdout or ""))
            )
            
        except subprocess.TimeoutExpired:
            return TaskResult(
                success=False,
                output="⏱️ Timeout: Task exceeded 300 seconds",
                agent="codex",
                model="codex",
                duration_seconds=300,
                cost_estimate=0
            )
        except Exception as e:
            return TaskResult(
                success=False,
                output=f"❌ Error: {str(e)}",
                agent="codex",
                model="codex",
                duration_seconds=0,
                cost_estimate=0
            )
    
    def _estimate_cost(self, model: str, input_chars: int, output_chars: int) -> float:
        """Estimate API cost."""
        input_tokens = input_chars / 4
        output_tokens = output_chars / 4
        
        costs = {
            "claude-opus-4": (0.015, 0.075),
            "claude-sonnet-4": (0.003, 0.015),
            "codex": (0.001, 0.002)
        }
        
        input_cost, output_cost = costs.get(model, (0.003, 0.015))
        return (input_tokens * input_cost / 1000) + (output_tokens * output_cost / 1000)

# ============================================================================
# MAIN ORCHESTRATOR
# ============================================================================

class KIRO2Orchestrator:
    """Main orchestrator for KIRO2 platform."""
    
    def __init__(self):
        self._ensure_directories()
        self.router = SmartRouter()
        self.engine = ExecutionEngine()
        self.history = self._load_history()
    
    def _ensure_directories(self):
        """Ensure required directories exist."""
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_history(self) -> List[dict]:
        """Load execution history."""
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_history(self):
        """Save execution history."""
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.history[-1000:], f, indent=2, ensure_ascii=False)
    
    def run(self, task: str, dry_run: bool = False, verbose: bool = False) -> TaskResult:
        """Run a task through the orchestrator."""
        
        # Route task
        agent, model, category, confidence = self.router.route(task)
        
        # Print routing decision
        print(f"\n{'='*60}")
        print(f"[*] KIRO2 ORCHESTRATOR")
        print(f"{'='*60}")
        print(f"Task: {task[:80]}{'...' if len(task) > 80 else ''}")
        print(f"{'-'*60}")
        print(f"Category: {category}")
        print(f"Agent: {agent}")
        print(f"Model: {model}")
        print(f"Confidence: {confidence:.0%}")
        print(f"{'-'*60}")
        
        # Check tool availability
        if model == "codex":
            tool_icon = "[OK]" if self.engine.codex_available else "[X]"
            print(f"{tool_icon} Codex CLI: {'Available' if self.engine.codex_available else 'Not found'}")
        else:
            tool_icon = "[OK]" if self.engine.claude_available else "[X]"
            print(f"{tool_icon} Claude CLI: {'Available' if self.engine.claude_available else 'Not found'}")
        
        # Execute
        if dry_run:
            print(f"\n[DRY RUN] - No actual execution")
            result = TaskResult(
                success=True,
                output=f"Would execute with {model}",
                agent=agent,
                model=model,
                duration_seconds=0,
                cost_estimate=0
            )
        else:
            print(f"\n[...] Executing...")
            result = self.engine.execute(task, model, dry_run)
        
        # Print results
        print(f"\n{'='*60}")
        print(f"RESULTS")
        print(f"{'='*60}")
        status_icon = "[OK]" if result.success else "[FAIL]"
        print(f"{status_icon} Status: {'Success' if result.success else 'Failed'}")
        print(f"Duration: {result.duration_seconds:.2f}s")
        print(f"Est. Cost: ${result.cost_estimate:.4f}")
        
        if verbose and result.output:
            print(f"\n{'-'*60}")
            print(f"OUTPUT:")
            print(f"{'-'*60}")
            print(result.output[:2000])
            if len(result.output) > 2000:
                print(f"\n... (truncated, {len(result.output)} total chars)")
        
        # Save to history
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "task": task[:200],
            "category": category,
            "agent": agent,
            "model": model,
            "confidence": confidence,
            "success": result.success,
            "duration": result.duration_seconds,
            "cost": result.cost_estimate
        })
        self._save_history()
        
        return result
    
    def show_stats(self):
        """Show orchestrator statistics."""
        print(f"\n{'='*60}")
        print(f"KIRO2 ORCHESTRATOR STATISTICS")
        print(f"{'='*60}")
        
        if not self.history:
            print("No history yet.")
            return
        
        total = len(self.history)
        success = sum(1 for h in self.history if h.get("success"))
        
        # Model distribution
        model_counts = {}
        for h in self.history:
            model = h.get("model", "unknown")
            model_counts[model] = model_counts.get(model, 0) + 1
        
        # Category distribution
        cat_counts = {}
        for h in self.history:
            cat = h.get("category", "unknown")
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
        
        total_cost = sum(h.get("cost", 0) for h in self.history)
        total_duration = sum(h.get("duration", 0) for h in self.history)
        
        print(f"Total tasks: {total}")
        print(f"Success rate: {success/total*100:.1f}%")
        print(f"Total est. cost: ${total_cost:.4f}")
        print(f"Total duration: {total_duration:.1f}s")
        
        print(f"\nBy Model:")
        for model, count in sorted(model_counts.items(), key=lambda x: -x[1]):
            print(f"   {model}: {count} ({count/total*100:.1f}%)")
        
        print(f"\nBy Category:")
        for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
            print(f"   {cat}: {count} ({count/total*100:.1f}%)")

# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="KIRO2 Claude + Codex Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python kiro2_orchestrator.py "FastAPI endpoint oluştur"
  python kiro2_orchestrator.py --dry-run "React component yaz"
  python kiro2_orchestrator.py "TYT matematik sorusu üret" -v
  python kiro2_orchestrator.py --stats
        """
    )
    
    parser.add_argument("task", nargs="?", default=None, help="Task to execute")
    parser.add_argument("--dry-run", "-d", action="store_true", help="Show routing without execution")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--stats", "-s", action="store_true", help="Show statistics")
    
    args = parser.parse_args()
    
    orchestrator = KIRO2Orchestrator()
    
    if args.stats:
        orchestrator.show_stats()
        return
    
    if not args.task:
        parser.print_help()
        print("\n[ERROR] Task is required unless using --stats")
        sys.exit(1)
    
    result = orchestrator.run(args.task, dry_run=args.dry_run, verbose=args.verbose)
    
    sys.exit(0 if result.success else 1)

if __name__ == "__main__":
    main()
