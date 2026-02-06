#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KIRO2 Intelligent Orchestrator v2.0
Automatically routes every prompt to the most appropriate agent
"""

import asyncio
import json
import logging
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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
    
    # General purpose
    GENERAL = "general-purpose"


class ExecutionMode(Enum):
    """Execution modes for agent tasks"""
    DIRECT = "direct"          # Direct Claude execution
    TASK = "task"             # Via Task tool
    MCP = "mcp"               # Via MCP server
    PIPELINE = "pipeline"     # Multi-step pipeline
    PARALLEL = "parallel"     # Parallel execution


class RequestType(Enum):
    """Types of user requests"""
    CODE_GENERATION = "code_generation"
    BUG_FIX = "bug_fix"
    CODE_REVIEW = "code_review"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    CONTENT_MANAGEMENT = "content_management"
    PERFORMANCE = "performance"
    SECURITY = "security"
    DATABASE = "database"
    FRONTEND = "frontend"
    BACKEND = "backend"
    DOCUMENTATION = "documentation"
    ANALYSIS = "analysis"
    GENERAL = "general"


@dataclass
class PromptAnalysis:
    """Detailed analysis of a user prompt"""
    text: str
    language: str
    keywords: List[str]
    entities: Dict[str, Any]
    intent: RequestType
    complexity: float
    confidence: float
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RoutingDecision:
    """Routing decision for a prompt"""
    primary_agent: AgentType
    secondary_agents: List[AgentType]
    execution_mode: ExecutionMode
    confidence: float
    reasoning: str
    parallel: bool = False
    pipeline_steps: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "primary_agent": self.primary_agent.value,
            "secondary_agents": [a.value for a in self.secondary_agents],
            "execution_mode": self.execution_mode.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "parallel": self.parallel,
            "pipeline_steps": self.pipeline_steps
        }


class TurkishNLPAnalyzer:
    """Advanced NLP analysis for Turkish and English prompts"""
    
    # Enhanced keyword patterns for better detection
    KEYWORDS = {
        RequestType.CODE_GENERATION: {
            "tr": ["oluştur", "yaz", "ekle", "implement", "geliştir", "kodla", "yarat"],
            "en": ["create", "write", "add", "implement", "develop", "code", "build", "make"]
        },
        RequestType.BUG_FIX: {
            "tr": ["hata", "düzelt", "çöz", "tamir", "onar", "bug", "sorun", "problem", "çalışmıyor", "bozuk", "patlıyor"],
            "en": ["error", "fix", "solve", "repair", "bug", "issue", "problem", "broken", "failing", "crash"]
        },
        RequestType.CODE_REVIEW: {
            "tr": ["incele", "review", "kontrol", "gözden geçir", "değerlendir", "analiz"],
            "en": ["review", "check", "inspect", "analyze", "evaluate", "examine", "audit"]
        },
        RequestType.TESTING: {
            "tr": ["test", "sına", "dene", "doğrula", "coverage", "unit test", "integration"],
            "en": ["test", "verify", "validate", "coverage", "unit", "integration", "e2e"]
        },
        RequestType.DEPLOYMENT: {
            "tr": ["deploy", "yayınla", "canlı", "production", "dağıt", "kur", "başlat"],
            "en": ["deploy", "release", "publish", "production", "distribute", "install", "launch"]
        },
        RequestType.CONTENT_MANAGEMENT: {
            "tr": ["soru", "içerik", "yükle", "ekle", "osym", "yks", "tyt", "ayt", "import"],
            "en": ["question", "content", "upload", "load", "import", "add", "insert"]
        },
        RequestType.FRONTEND: {
            "tr": ["react", "component", "komponent", "arayüz", "ui", "ux", "sayfa", "frontend", "css", "tsx"],
            "en": ["react", "component", "interface", "ui", "ux", "page", "frontend", "css", "tsx", "view"]
        },
        RequestType.BACKEND: {
            "tr": ["api", "endpoint", "veritabanı", "backend", "sunucu", "fastapi", "database", "migration"],
            "en": ["api", "endpoint", "database", "backend", "server", "fastapi", "db", "migration", "route"]
        },
        RequestType.PERFORMANCE: {
            "tr": ["performans", "hız", "optimize", "yavaş", "hızlandır", "iyileştir", "cache"],
            "en": ["performance", "speed", "optimize", "slow", "fast", "improve", "cache", "efficient"]
        },
        RequestType.SECURITY: {
            "tr": ["güvenlik", "auth", "kimlik", "yetki", "token", "jwt", "şifre", "koruma"],
            "en": ["security", "auth", "authentication", "authorization", "token", "jwt", "password", "protect"]
        }
    }
    
    # Entity patterns for extraction
    ENTITY_PATTERNS = {
        "file": r"(\w+\.(py|js|ts|tsx|css|html|json|yaml|yml|md))",
        "function": r"(def|function|const|class)\s+(\w+)",
        "endpoint": r"(@app\.|router\.|api/|/api/)",
        "component": r"(<\w+|Component|component)",
        "table": r"(table|Table|model|Model)\s+(\w+)",
    }
    
    def analyze(self, prompt: str) -> PromptAnalysis:
        """Analyze prompt to extract intent, keywords, and entities"""
        prompt_lower = prompt.lower()
        
        # Language detection
        language = self._detect_language(prompt_lower)
        
        # Extract keywords
        keywords = self._extract_keywords(prompt_lower)
        
        # Detect intent
        intent = self._detect_intent(prompt_lower, keywords)
        
        # Extract entities
        entities = self._extract_entities(prompt)
        
        # Calculate complexity
        complexity = self._calculate_complexity(prompt, entities, keywords)
        
        # Calculate confidence
        confidence = self._calculate_confidence(keywords, intent)
        
        return PromptAnalysis(
            text=prompt,
            language=language,
            keywords=keywords,
            entities=entities,
            intent=intent,
            complexity=complexity,
            confidence=confidence,
            context=self._gather_context()
        )
    
    def _detect_language(self, text: str) -> str:
        """Detect if prompt is Turkish or English"""
        turkish_chars = set("çğıöşüÇĞİÖŞÜ")
        turkish_words = ["ve", "veya", "için", "ile", "bu", "bir", "olan", "olarak"]
        
        has_turkish_chars = any(char in text for char in turkish_chars)
        turkish_word_count = sum(1 for word in turkish_words if word in text.split())
        
        if has_turkish_chars or turkish_word_count >= 2:
            return "tr"
        return "en"
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text"""
        keywords = []
        
        for request_type, patterns in self.KEYWORDS.items():
            for lang_patterns in patterns.values():
                for pattern in lang_patterns:
                    if pattern in text:
                        keywords.append(pattern)
        
        return list(set(keywords))
    
    def _detect_intent(self, text: str, keywords: List[str]) -> RequestType:
        """Detect the primary intent of the prompt"""
        intent_scores = {}
        
        for request_type, patterns in self.KEYWORDS.items():
            score = 0
            for lang_patterns in patterns.values():
                for pattern in lang_patterns:
                    if pattern in text:
                        score += 2 if pattern in keywords else 1
            
            if score > 0:
                intent_scores[request_type] = score
        
        if intent_scores:
            return max(intent_scores, key=intent_scores.get)
        
        return RequestType.GENERAL
    
    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract named entities from text"""
        entities = {}
        
        for entity_type, pattern in self.ENTITY_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                entities[entity_type] = matches
        
        return entities
    
    def _calculate_complexity(self, text: str, entities: Dict, keywords: List[str]) -> float:
        """Calculate prompt complexity (0.0 to 1.0)"""
        factors = [
            len(text) / 500,  # Text length factor
            len(entities) / 5,  # Entity count factor
            len(keywords) / 10,  # Keyword density factor
            len(text.split('\n')) / 10  # Multi-line factor
        ]
        
        complexity = min(1.0, sum(factors) / len(factors))
        return complexity
    
    def _calculate_confidence(self, keywords: List[str], intent: RequestType) -> float:
        """Calculate confidence in the analysis"""
        base_confidence = 0.5
        
        # Increase confidence based on keyword matches
        keyword_bonus = min(0.3, len(keywords) * 0.05)
        
        # Increase confidence if intent is not general
        intent_bonus = 0.2 if intent != RequestType.GENERAL else 0
        
        confidence = min(1.0, base_confidence + keyword_bonus + intent_bonus)
        return confidence
    
    def _gather_context(self) -> Dict[str, Any]:
        """Gather additional context"""
        return {
            "timestamp": datetime.now().isoformat(),
            "cwd": os.getcwd(),
            "platform": sys.platform
        }


class IntelligentRouter:
    """Routes prompts to the most appropriate agents"""
    
    # Agent capability mapping
    AGENT_CAPABILITIES = {
        AgentType.BACKEND_API: [
            RequestType.BACKEND,
            RequestType.DATABASE,
            RequestType.SECURITY,
            RequestType.CODE_GENERATION
        ],
        AgentType.FRONTEND_SPECIALIST: [
            RequestType.FRONTEND,
            RequestType.CODE_GENERATION
        ],
        AgentType.CONTENT_MANAGER: [
            RequestType.CONTENT_MANAGEMENT
        ],
        AgentType.DEVOPS_ENGINEER: [
            RequestType.DEPLOYMENT,
            RequestType.PERFORMANCE
        ],
        AgentType.DEBUGGER: [
            RequestType.BUG_FIX
        ],
        AgentType.CODE_REVIEWER: [
            RequestType.CODE_REVIEW,
            RequestType.SECURITY
        ],
        AgentType.TEST_RUNNER: [
            RequestType.TESTING
        ],
        AgentType.TURKISH_NLP: [
            RequestType.CONTENT_MANAGEMENT,
            RequestType.ANALYSIS
        ]
    }
    
    def route(self, analysis: PromptAnalysis) -> RoutingDecision:
        """Determine the best agent and execution mode"""
        
        # Find agents that can handle this intent
        capable_agents = self._find_capable_agents(analysis.intent)
        
        if not capable_agents:
            return self._create_fallback_decision(analysis)
        
        # Score and rank agents
        agent_scores = self._score_agents(capable_agents, analysis)
        
        # Select primary and secondary agents
        primary = max(agent_scores, key=agent_scores.get)
        secondary = self._select_secondary_agents(agent_scores, primary, analysis)
        
        # Determine execution mode
        execution_mode = self._determine_execution_mode(primary, analysis)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(primary, analysis, agent_scores[primary])
        
        return RoutingDecision(
            primary_agent=primary,
            secondary_agents=secondary,
            execution_mode=execution_mode,
            confidence=agent_scores[primary],
            reasoning=reasoning,
            parallel=len(secondary) > 0 and analysis.complexity > 0.7
        )
    
    def _find_capable_agents(self, intent: RequestType) -> List[AgentType]:
        """Find agents capable of handling the intent"""
        capable = []
        
        for agent, capabilities in self.AGENT_CAPABILITIES.items():
            if intent in capabilities:
                capable.append(agent)
        
        return capable
    
    def _score_agents(self, agents: List[AgentType], analysis: PromptAnalysis) -> Dict[AgentType, float]:
        """Score each agent based on capability match"""
        scores = {}
        
        for agent in agents:
            # Base score from capability match
            base_score = 0.7
            
            # Keyword match bonus
            keyword_bonus = self._calculate_keyword_bonus(agent, analysis.keywords)
            
            # Entity match bonus
            entity_bonus = self._calculate_entity_bonus(agent, analysis.entities)
            
            # Language preference bonus
            language_bonus = 0.1 if agent == AgentType.TURKISH_NLP and analysis.language == "tr" else 0
            
            scores[agent] = min(1.0, base_score + keyword_bonus + entity_bonus + language_bonus)
        
        return scores
    
    def _calculate_keyword_bonus(self, agent: AgentType, keywords: List[str]) -> float:
        """Calculate bonus score based on keyword matches"""
        agent_keywords = {
            AgentType.BACKEND_API: ["api", "endpoint", "backend", "database", "fastapi"],
            AgentType.FRONTEND_SPECIALIST: ["react", "component", "frontend", "ui", "tsx"],
            AgentType.CONTENT_MANAGER: ["soru", "question", "content", "yks", "osym"],
            AgentType.DEVOPS_ENGINEER: ["deploy", "docker", "kubernetes", "ci/cd"],
            AgentType.DEBUGGER: ["hata", "error", "bug", "fix", "debug"],
            AgentType.CODE_REVIEWER: ["review", "incele", "kontrol", "check"],
            AgentType.TEST_RUNNER: ["test", "pytest", "coverage", "unit"],
            AgentType.TURKISH_NLP: ["türkçe", "turkish", "nlp", "analiz"]
        }
        
        if agent not in agent_keywords:
            return 0
        
        matches = sum(1 for kw in keywords if any(ak in kw for ak in agent_keywords[agent]))
        return min(0.2, matches * 0.05)
    
    def _calculate_entity_bonus(self, agent: AgentType, entities: Dict) -> float:
        """Calculate bonus based on entity matches"""
        if not entities:
            return 0
        
        entity_preferences = {
            AgentType.BACKEND_API: ["endpoint", "table", "function"],
            AgentType.FRONTEND_SPECIALIST: ["component", "file"],
            AgentType.CONTENT_MANAGER: ["file"],
            AgentType.DEBUGGER: ["function", "file"],
            AgentType.CODE_REVIEWER: ["function", "file"],
            AgentType.TEST_RUNNER: ["function", "file"]
        }
        
        if agent not in entity_preferences:
            return 0
        
        matches = sum(1 for et in entity_preferences[agent] if et in entities)
        return min(0.1, matches * 0.03)
    
    def _select_secondary_agents(self, scores: Dict, primary: AgentType, analysis: PromptAnalysis) -> List[AgentType]:
        """Select secondary agents for complex tasks"""
        if analysis.complexity < 0.5:
            return []
        
        secondary = []
        sorted_agents = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        for agent, score in sorted_agents[1:3]:  # Top 2 after primary
            if score > 0.6 and agent != primary:
                secondary.append(agent)
        
        return secondary
    
    def _determine_execution_mode(self, agent: AgentType, analysis: PromptAnalysis) -> ExecutionMode:
        """Determine the best execution mode"""
        # Complex tasks use pipeline
        if analysis.complexity > 0.8:
            return ExecutionMode.PIPELINE
        
        # Multiple entities suggest parallel execution
        if len(analysis.entities) > 3:
            return ExecutionMode.PARALLEL
        
        # Testing always uses task mode
        if agent == AgentType.TEST_RUNNER:
            return ExecutionMode.TASK
        
        # Default to task mode for specific agents
        return ExecutionMode.TASK
    
    def _generate_reasoning(self, agent: AgentType, analysis: PromptAnalysis, score: float) -> str:
        """Generate human-readable reasoning"""
        reasons = []
        
        # Intent-based reasoning
        reasons.append(f"Intent: {analysis.intent.value}")
        
        # Keyword-based reasoning
        if analysis.keywords:
            reasons.append(f"Keywords: {', '.join(analysis.keywords[:3])}")
        
        # Confidence reasoning
        confidence_level = "high" if score > 0.8 else "medium" if score > 0.6 else "low"
        reasons.append(f"Confidence: {confidence_level} ({score:.1%})")
        
        return " | ".join(reasons)
    
    def _create_fallback_decision(self, analysis: PromptAnalysis) -> RoutingDecision:
        """Create fallback decision when no specific agent matches"""
        return RoutingDecision(
            primary_agent=AgentType.GENERAL,
            secondary_agents=[],
            execution_mode=ExecutionMode.DIRECT,
            confidence=0.5,
            reasoning="No specific pattern matched, using general agent"
        )


class OrchestratorV2:
    """Main orchestrator that coordinates all components"""
    
    def __init__(self):
        self.analyzer = TurkishNLPAnalyzer()
        self.router = IntelligentRouter()
        self._initialize_logging()
    
    def _initialize_logging(self):
        """Setup logging configuration"""
        log_dir = Path(".claude/orchestration/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Add file handler
        fh = logging.FileHandler(log_dir / f"orchestrator_{datetime.now():%Y%m%d}.log")
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    def process(self, prompt: str) -> Dict:
        """Main orchestration pipeline"""
        try:
            logger.info(f"Processing prompt: {prompt[:100]}...")
            
            # Analyze prompt
            analysis = self.analyzer.analyze(prompt)
            logger.info(f"Analysis complete - Intent: {analysis.intent.value}, Confidence: {analysis.confidence:.2f}")
            
            # Route to agent
            routing = self.router.route(analysis)
            logger.info(f"Routing decision - Agent: {routing.primary_agent.value}, Mode: {routing.execution_mode.value}")
            
            # Generate output
            output = self._generate_output(prompt, analysis, routing)
            
            # Log decision
            self._log_decision(prompt, analysis, routing)
            
            return output
            
        except Exception as e:
            logger.error(f"Error processing prompt: {e}", exc_info=True)
            return self._create_error_output(str(e))
    
    def _generate_output(self, prompt: str, analysis: PromptAnalysis, routing: RoutingDecision) -> Dict:
        """Generate orchestrator output"""
        output = {
            "analysis": {
                "language": analysis.language,
                "intent": analysis.intent.value,
                "keywords": analysis.keywords,
                "entities": analysis.entities,
                "complexity": analysis.complexity,
                "confidence": analysis.confidence
            },
            "routing": routing.to_dict(),
            "recommendations": self._generate_recommendations(routing),
            "visual_output": self._generate_visual_output(routing),
            "timestamp": datetime.now().isoformat()
        }
        
        return output
    
    def _generate_recommendations(self, routing: RoutingDecision) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Primary recommendation
        recommendations.append(
            f"Use Task tool with subagent_type='{routing.primary_agent.value}'"
        )
        
        # Secondary agents recommendation
        if routing.secondary_agents:
            for agent in routing.secondary_agents:
                recommendations.append(
                    f"Consider also using '{agent.value}' for comprehensive coverage"
                )
        
        # Execution mode recommendation
        if routing.execution_mode == ExecutionMode.PIPELINE:
            recommendations.append("Break down into smaller tasks for pipeline execution")
        elif routing.execution_mode == ExecutionMode.PARALLEL:
            recommendations.append("Execute subtasks in parallel for efficiency")
        
        return recommendations
    
    def _generate_visual_output(self, routing: RoutingDecision) -> str:
        """Generate visual output for terminal display"""
        lines = []
        lines.append("")
        lines.append("=" * 60)
        lines.append("🤖 AKILLI ORKESTRATÖR - Yönlendirme Analizi")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"📌 Ana Agent: {routing.primary_agent.value}")
        lines.append(f"🎯 Güven: {routing.confidence:.1%}")
        lines.append(f"⚙️  Mod: {routing.execution_mode.value}")
        lines.append(f"💡 Sebep: {routing.reasoning}")
        
        if routing.secondary_agents:
            lines.append(f"🔄 Yardımcı: {', '.join(a.value for a in routing.secondary_agents)}")
        
        if routing.parallel:
            lines.append("⚡ Paralel yürütme öneriliyor")
        
        lines.append("")
        lines.append("🎯 ÖNERİ:")
        lines.append(f"   Task tool kullan: subagent_type='{routing.primary_agent.value}'")
        lines.append("")
        lines.append("=" * 60)
        lines.append("")
        
        return "\n".join(lines)
    
    def _log_decision(self, prompt: str, analysis: PromptAnalysis, routing: RoutingDecision):
        """Log routing decision for learning"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "analysis": {
                "intent": analysis.intent.value,
                "confidence": analysis.confidence,
                "complexity": analysis.complexity
            },
            "routing": {
                "agent": routing.primary_agent.value,
                "mode": routing.execution_mode.value,
                "confidence": routing.confidence
            }
        }
        
        # Save to learning log
        log_file = Path(".claude/orchestration/logs/decisions.jsonl")
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    def _create_error_output(self, error_msg: str) -> Dict:
        """Create error output"""
        return {
            "error": error_msg,
            "routing": {
                "primary_agent": AgentType.GENERAL.value,
                "execution_mode": ExecutionMode.DIRECT.value,
                "confidence": 0.5
            },
            "recommendations": ["Fallback to general Claude processing"],
            "timestamp": datetime.now().isoformat()
        }


def main():
    """Main entry point for command line usage"""
    # Configure UTF-8 output for Windows
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "No prompt provided",
            "usage": "python orchestrator_v2.py '<prompt>'"
        }, indent=2))
        sys.exit(1)
    
    prompt = sys.argv[1]
    
    # Initialize orchestrator
    orchestrator = OrchestratorV2()
    
    # Process prompt
    result = orchestrator.process(prompt)
    
    # Output visual display
    if "visual_output" in result:
        print(result["visual_output"])
    
    # Output JSON for programmatic use
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()