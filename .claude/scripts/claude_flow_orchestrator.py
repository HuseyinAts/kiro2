#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Flow Orchestrator
Automatically routes user prompts to appropriate specialized agents

This script analyzes user input and determines which agent(s) should handle the request.
It provides context-aware routing for the KIRO2 educational platform.
"""

import json
import re
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class AgentType(Enum):
    """Available specialized agents"""
    # Core development agents
    BACKEND_API = "kiro2-backend-api"
    FRONTEND_SPECIALIST = "kiro2-frontend-specialist"
    CONTENT_MANAGER = "kiro2-content-manager"
    DEVOPS_ENGINEER = "kiro2-devops-engineer"

    # Specialized agents
    TURKISH_NLP = "turkish-nlp-specialist"
    CODE_REVIEWER = "code-reviewer"
    DEBUGGER = "debugger"
    TEST_RUNNER = "test-runner"
    PYTHON_PRO = "python-pro"

    # Planning and design
    SPEC_REQUIREMENTS = "spec-requirements"
    SPEC_DESIGN = "spec-design"
    SPEC_TASKS = "spec-tasks"
    SPEC_IMPL = "spec-impl"
    SPEC_TEST = "spec-test"
    SPEC_JUDGE = "spec-judge"

    # General purpose
    EXPLORE = "Explore"
    PLAN = "Plan"
    GENERAL = "general-purpose"


@dataclass
class RoutingDecision:
    """Routing decision for a user prompt"""
    primary_agent: AgentType
    secondary_agents: list[AgentType]
    confidence: float
    reasoning: str
    parallel_execution: bool = False
    context: dict = None

    def to_dict(self) -> dict:
        return {
            "primary_agent": self.primary_agent.value,
            "secondary_agents": [a.value for a in self.secondary_agents],
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "parallel_execution": self.parallel_execution,
            "context": self.context or {}
        }


class ClaudeFlowOrchestrator:
    """
    Orchestrator that routes user prompts to specialized agents
    """

    # Turkish keywords for better detection
    TURKISH_KEYWORDS = {
        "backend": ["api", "endpoint", "fastapi", "veritabani", "database", "backend", "sunucu", "server"],
        "frontend": ["react", "component", "komponent", "ui", "arayuz", "frontend", "sayfa", "page", "tsx", "css"],
        "content": ["soru", "question", "icerik", "content", "yukle", "upload", "osym", "yks", "tyt", "ayt"],
        "devops": ["deploy", "docker", "kubernetes", "ci/cd", "monitoring", "performans", "pipeline"],
        "testing": ["test", "pytest", "jest", "unittest", "coverage", "calistir"],
        "nlp": ["turkce", "turkish", "nlp", "dil", "language", "analiz", "metin", "text"],
        "debug": ["hata", "error", "bug", "fix", "duzelt", "calis", "calismadi", "patla"],
        "review": ["review", "incele", "kontrol", "kalite", "quality", "gozden gecir"],
        "plan": ["plan", "tasarla", "design", "mimari", "architecture", "strateji"],
        "explore": ["ara", "bul", "find", "search", "nerede", "where"],
    }

    # Patterns for specific task types
    TASK_PATTERNS = {
        "api_creation": r"(api|endpoint|route)\s*(oluştur|ekle|yaz|create|add)",
        "bug_fix": r"(hata|error|bug|sorun|problem)\s*(düzelt|fix|çöz|gider)",
        "test_run": r"(test|pytest|jest)\s*(çalıştır|run|koş)",
        "deployment": r"(deploy|yayınla|canlı|production)",
        "question_load": r"(soru|question)\s*(yükle|load|ekle|add)",
        "performance": r"(performans|hız|speed|optimize|yavaş|slow)",
        "security": r"(güvenlik|security|auth|kimlik|token|jwt)",
        "database": r"(veritabanı|database|migration|tablo|table|sql)",
        "frontend_component": r"(component|komponent|sayfa|page)\s*(oluştur|ekle|yaz)",
        "code_review": r"(incele|review|kontrol|check)\s*(kod|code|pr|pull)",
    }

    def __init__(self):
        self.context = {}

    def analyze_prompt(self, prompt: str) -> RoutingDecision:
        """Analyze user prompt and determine routing"""
        prompt_lower = prompt.lower()

        # Check for explicit agent mentions
        explicit_agent = self._check_explicit_agent(prompt_lower)
        if explicit_agent:
            return RoutingDecision(
                primary_agent=explicit_agent,
                secondary_agents=[],
                confidence=1.0,
                reasoning="Explicit agent request detected",
            )

        # Check for specific task patterns
        task_match = self._match_task_patterns(prompt_lower)
        if task_match:
            return task_match

        # Keyword-based routing
        keyword_match = self._match_keywords(prompt_lower)
        if keyword_match:
            return keyword_match

        # Default to general purpose
        return RoutingDecision(
            primary_agent=AgentType.GENERAL,
            secondary_agents=[],
            confidence=0.5,
            reasoning="No specific pattern matched, using general agent",
        )

    def _check_explicit_agent(self, prompt: str) -> Optional[AgentType]:
        """Check if user explicitly requests an agent"""
        agent_mappings = {
            "backend agent": AgentType.BACKEND_API,
            "backend-api": AgentType.BACKEND_API,
            "frontend agent": AgentType.FRONTEND_SPECIALIST,
            "frontend-specialist": AgentType.FRONTEND_SPECIALIST,
            "content agent": AgentType.CONTENT_MANAGER,
            "content-manager": AgentType.CONTENT_MANAGER,
            "devops agent": AgentType.DEVOPS_ENGINEER,
            "devops-engineer": AgentType.DEVOPS_ENGINEER,
            "nlp agent": AgentType.TURKISH_NLP,
            "turkish-nlp": AgentType.TURKISH_NLP,
            "code reviewer": AgentType.CODE_REVIEWER,
            "debugger": AgentType.DEBUGGER,
            "test runner": AgentType.TEST_RUNNER,
        }

        for pattern, agent in agent_mappings.items():
            if pattern in prompt:
                return agent
        return None

    def _match_task_patterns(self, prompt: str) -> Optional[RoutingDecision]:
        """Match specific task patterns"""

        # API/Backend tasks
        if re.search(self.TASK_PATTERNS["api_creation"], prompt):
            return RoutingDecision(
                primary_agent=AgentType.BACKEND_API,
                secondary_agents=[AgentType.TEST_RUNNER],
                confidence=0.9,
                reasoning="API creation task detected",
                parallel_execution=False,
            )

        # Bug fixing
        if re.search(self.TASK_PATTERNS["bug_fix"], prompt):
            return RoutingDecision(
                primary_agent=AgentType.DEBUGGER,
                secondary_agents=[AgentType.TEST_RUNNER],
                confidence=0.85,
                reasoning="Bug fix task detected",
            )

        # Test running
        if re.search(self.TASK_PATTERNS["test_run"], prompt):
            return RoutingDecision(
                primary_agent=AgentType.TEST_RUNNER,
                secondary_agents=[],
                confidence=0.95,
                reasoning="Test execution requested",
            )

        # Deployment
        if re.search(self.TASK_PATTERNS["deployment"], prompt):
            return RoutingDecision(
                primary_agent=AgentType.DEVOPS_ENGINEER,
                secondary_agents=[AgentType.TEST_RUNNER],
                confidence=0.9,
                reasoning="Deployment task detected",
            )

        # Question/Content loading
        if re.search(self.TASK_PATTERNS["question_load"], prompt):
            return RoutingDecision(
                primary_agent=AgentType.CONTENT_MANAGER,
                secondary_agents=[AgentType.BACKEND_API],
                confidence=0.9,
                reasoning="Content loading task detected",
            )

        # Performance optimization
        if re.search(self.TASK_PATTERNS["performance"], prompt):
            return RoutingDecision(
                primary_agent=AgentType.DEVOPS_ENGINEER,
                secondary_agents=[AgentType.BACKEND_API, AgentType.FRONTEND_SPECIALIST],
                confidence=0.8,
                reasoning="Performance optimization task",
                parallel_execution=True,
            )

        # Security
        if re.search(self.TASK_PATTERNS["security"], prompt):
            return RoutingDecision(
                primary_agent=AgentType.BACKEND_API,
                secondary_agents=[AgentType.CODE_REVIEWER],
                confidence=0.85,
                reasoning="Security-related task detected",
            )

        # Database
        if re.search(self.TASK_PATTERNS["database"], prompt):
            return RoutingDecision(
                primary_agent=AgentType.BACKEND_API,
                secondary_agents=[],
                confidence=0.85,
                reasoning="Database task detected",
            )

        # Frontend component
        if re.search(self.TASK_PATTERNS["frontend_component"], prompt):
            return RoutingDecision(
                primary_agent=AgentType.FRONTEND_SPECIALIST,
                secondary_agents=[AgentType.TEST_RUNNER],
                confidence=0.9,
                reasoning="Frontend component task detected",
            )

        # Code review
        if re.search(self.TASK_PATTERNS["code_review"], prompt):
            return RoutingDecision(
                primary_agent=AgentType.CODE_REVIEWER,
                secondary_agents=[],
                confidence=0.9,
                reasoning="Code review requested",
            )

        return None

    def _match_keywords(self, prompt: str) -> Optional[RoutingDecision]:
        """Match based on keywords"""
        scores = {}

        for category, keywords in self.TURKISH_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in prompt)
            if score > 0:
                scores[category] = score

        if not scores:
            return None

        # Get highest scoring category
        best_category = max(scores, key=scores.get)
        confidence = min(0.9, 0.5 + (scores[best_category] * 0.1))

        agent_mapping = {
            "backend": AgentType.BACKEND_API,
            "frontend": AgentType.FRONTEND_SPECIALIST,
            "content": AgentType.CONTENT_MANAGER,
            "devops": AgentType.DEVOPS_ENGINEER,
            "testing": AgentType.TEST_RUNNER,
            "nlp": AgentType.TURKISH_NLP,
            "debug": AgentType.DEBUGGER,
            "review": AgentType.CODE_REVIEWER,
            "plan": AgentType.PLAN,
            "explore": AgentType.EXPLORE,
        }

        primary = agent_mapping.get(best_category, AgentType.GENERAL)

        # Determine secondary agents
        secondary = []
        if len(scores) > 1:
            sorted_categories = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
            for cat in sorted_categories[1:3]:  # Max 2 secondary
                if cat in agent_mapping:
                    secondary.append(agent_mapping[cat])

        return RoutingDecision(
            primary_agent=primary,
            secondary_agents=secondary,
            confidence=confidence,
            reasoning=f"Keyword match: {best_category} (score: {scores[best_category]})",
            parallel_execution=len(secondary) > 0,
        )

    def generate_task_prompt(self, user_prompt: str, decision: RoutingDecision) -> str:
        """Generate a task prompt for the selected agent"""
        agent_instructions = {
            AgentType.BACKEND_API: "Backend API geliştirme, veritabanı operasyonları ve endpoint implementasyonu için çalış.",
            AgentType.FRONTEND_SPECIALIST: "React 18 bileşenleri, TypeScript optimizasyonu ve UI/UX geliştirmesi için çalış.",
            AgentType.CONTENT_MANAGER: "KIRO2 içerik yönetimi, soru yükleme ve eğitim materyalleri için çalış.",
            AgentType.DEVOPS_ENGINEER: "Deployment, CI/CD, monitoring ve performans optimizasyonu için çalış.",
            AgentType.TURKISH_NLP: "Türkçe NLP, soru analizi ve eğitim algoritmaları için çalış.",
            AgentType.DEBUGGER: "Hata ayıklama, stack trace analizi ve root cause tespiti için çalış.",
            AgentType.CODE_REVIEWER: "Kod incelemesi, güvenlik/performans kontrolü ve kalite analizi için çalış.",
            AgentType.TEST_RUNNER: "Test çalıştırma, coverage analizi ve test yazımı için çalış.",
        }

        instruction = agent_instructions.get(
            decision.primary_agent,
            "Genel amaçlı yazılım geliştirme görevi."
        )

        return f"""
{instruction}

KULLANICI İSTEĞİ:
{user_prompt}

BAĞLAM:
- Platform: KIRO2 YKS Hazırlık Platformu
- Dil: Türkçe öncelikli
- Hedef: Production-ready kod

Lütfen bu görevi yerine getir.
"""


def main():
    """Main entry point"""
    # Ensure UTF-8 output on Windows
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "No prompt provided",
            "usage": "python claude_flow_orchestrator.py '<user_prompt>'"
        }))
        sys.exit(1)

    user_prompt = sys.argv[1]

    orchestrator = ClaudeFlowOrchestrator()
    decision = orchestrator.analyze_prompt(user_prompt)

    output = {
        "routing": decision.to_dict(),
        "task_prompt": orchestrator.generate_task_prompt(user_prompt, decision),
        "recommended_action": f"Use Task tool with subagent_type='{decision.primary_agent.value}'",
    }

    print(json.dumps(output, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
