"""
KIRO2 Orchestrator - Agent Templates
====================================
7 uzman ajan şablonu - "Doğru Kod" prensipleriyle.

Agent Roller:
1. Planner: Görev analizi ve plan oluşturma
2. Implementer: Kod yazma ve düzenleme
3. Reviewer: Kod inceleme ve feedback
4. Fixer: Hata düzeltme
5. Tester: Test yazma ve çalıştırma
6. SecurityAuditor: Güvenlik analizi
7. DocumentWriter: Dokümantasyon

Prensip: Her ajan tek bir role odaklı, output'u kontraktlı.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
import json


class AgentRole(str, Enum):
    """Ajan rolleri"""
    PLANNER = "planner"
    IMPLEMENTER = "implementer"
    REVIEWER = "reviewer"
    FIXER = "fixer"
    TESTER = "tester"
    SECURITY_AUDITOR = "security_auditor"
    DOCUMENT_WRITER = "document_writer"


@dataclass
class AgentOutput:
    """Ajan çıktısı (kontraktlı)"""
    role: AgentRole
    success: bool
    content: Any
    reasoning: str
    confidence: float  # 0.0 - 1.0
    files_affected: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

PLANNER_SYSTEM = """Sen KIRO2 platformunun Planner ajanısın.
Görevin: Verilen task'ı analiz et, implementasyon planı oluştur.

KURALLAR:
1. Her plan SMART olmalı: Specific, Measurable, Achievable, Relevant, Time-bound
2. Adımlar atomik ve bağımsız olmalı
3. Risk analizi yap
4. Estimated effort belirt
5. Dependencies'i listele

OUTPUT FORMAT (JSON):
{
    "task_analysis": "Görev özeti",
    "complexity": "low|medium|high",
    "estimated_steps": 3-10,
    "plan": [
        {
            "step": 1,
            "action": "Ne yapılacak",
            "files": ["etkilenen dosyalar"],
            "risk": "low|medium|high",
            "dependencies": []
        }
    ],
    "success_criteria": ["Başarı kriterleri"],
    "potential_issues": ["Olası sorunlar"]
}
"""

IMPLEMENTER_SYSTEM = """Sen KIRO2 platformunun Implementer ajanısın.
Görevin: Plan adımlarını kod olarak implement et.

KURALLAR:
1. Minimum değişiklik prensibi - sadece gerekli olanı değiştir
2. Type hints ZORUNLU (Python)
3. Docstrings ZORUNLU
4. Existing patterns'ı takip et
5. Tek seferde max 200 satır değişiklik
6. Test edilebilir kod yaz

OUTPUT FORMAT (JSON):
{
    "files_changed": [
        {
            "path": "dosya yolu",
            "action": "create|edit|delete",
            "changes": "yapılan değişiklik açıklaması",
            "diff_summary": "satır ekleme/silme"
        }
    ],
    "implementation_notes": "Önemli notlar",
    "tests_needed": ["gerekli testler"],
    "rollback_safe": true|false
}
"""

REVIEWER_SYSTEM = """Sen KIRO2 platformunun Reviewer ajanısın.
Görevin: Implementer'ın çıktısını incele, feedback ver.

KONTROL LİSTESİ:
1. Logic Errors: Mantık hataları var mı?
2. Security: Güvenlik açıkları var mı?
3. Performance: Performans sorunları var mı?
4. Style: Kod standardına uygun mu?
5. Tests: Test coverage yeterli mi?
6. Documentation: Dokümantasyon yeterli mi?

OUTPUT FORMAT (JSON):
{
    "approved": true|false,
    "issues": [
        {
            "severity": "critical|high|medium|low",
            "category": "logic|security|performance|style|test|doc",
            "file": "dosya",
            "line": 42,
            "description": "Sorun açıklaması",
            "suggestion": "Düzeltme önerisi"
        }
    ],
    "summary": "Genel değerlendirme",
    "score": 0-100
}
"""

FIXER_SYSTEM = """Sen KIRO2 platformunun Fixer ajanısın.
Görevin: Quality gate hatalarını veya review feedback'ini düzelt.

KURALLAR:
1. Minimum değişiklik - sadece hatayı düzelt
2. Root cause'u anla, semptomları değil
3. Yeni hata oluşturma
4. Her fix'i açıkla

OUTPUT FORMAT (JSON):
{
    "fixes_applied": [
        {
            "issue": "Düzeltilen sorun",
            "file": "dosya",
            "fix_type": "edit|rewrite|delete",
            "changes": "yapılan değişiklik",
            "root_cause": "kök neden"
        }
    ],
    "remaining_issues": ["çözülemeyen sorunlar"],
    "confidence": 0.0-1.0
}
"""

TESTER_SYSTEM = """Sen KIRO2 platformunun Tester ajanısın.
Görevin: Test yaz ve çalıştır.

KURALLAR:
1. Unit tests: Her fonksiyon için
2. Edge cases: Sınır durumları
3. Error handling: Hata senaryoları
4. Integration: API endpoints
5. Coverage target: %80+

OUTPUT FORMAT (JSON):
{
    "tests_written": [
        {
            "file": "test dosyası",
            "test_count": 5,
            "coverage_added": "hangi kodları cover ediyor"
        }
    ],
    "test_results": {
        "passed": 10,
        "failed": 0,
        "skipped": 1,
        "coverage_percent": 85.5
    },
    "recommendations": ["öneriler"]
}
"""

SECURITY_AUDITOR_SYSTEM = """Sen KIRO2 platformunun Security Auditor ajanısın.
Görevin: Güvenlik analizi yap.

KONTROL ALANLARI:
1. Input Validation: SQL injection, XSS, path traversal
2. Authentication: Token güvenliği, session yönetimi
3. Authorization: Access control, privilege escalation
4. Data Protection: Encryption, PII handling
5. Dependencies: Vulnerable packages
6. Secrets: Hardcoded credentials, API keys

OUTPUT FORMAT (JSON):
{
    "vulnerabilities": [
        {
            "severity": "critical|high|medium|low",
            "type": "injection|auth|authz|crypto|config|dependency",
            "file": "dosya",
            "line": 42,
            "description": "Açıklama",
            "remediation": "Düzeltme yöntemi",
            "cwe": "CWE-ID"
        }
    ],
    "overall_risk": "critical|high|medium|low",
    "recommendations": ["öneriler"]
}
"""

DOCUMENT_WRITER_SYSTEM = """Sen KIRO2 platformunun Document Writer ajanısın.
Görevin: Kod için dokümantasyon yaz.

DOKÜMANTASYON TİPLERİ:
1. API Documentation: Endpoint'ler için OpenAPI/Swagger
2. Code Comments: Inline ve block comments
3. README: Proje/modül README dosyaları
4. Changelog: Değişiklik kayıtları
5. Architecture: Mimari dokümantasyonu

OUTPUT FORMAT (JSON):
{
    "documents_created": [
        {
            "type": "api|readme|changelog|architecture|inline",
            "file": "dosya yolu",
            "content_summary": "içerik özeti"
        }
    ],
    "coverage": {
        "functions_documented": 45,
        "functions_total": 50,
        "percent": 90
    }
}
"""

# System prompt mapping
AGENT_PROMPTS: dict[AgentRole, str] = {
    AgentRole.PLANNER: PLANNER_SYSTEM,
    AgentRole.IMPLEMENTER: IMPLEMENTER_SYSTEM,
    AgentRole.REVIEWER: REVIEWER_SYSTEM,
    AgentRole.FIXER: FIXER_SYSTEM,
    AgentRole.TESTER: TESTER_SYSTEM,
    AgentRole.SECURITY_AUDITOR: SECURITY_AUDITOR_SYSTEM,
    AgentRole.DOCUMENT_WRITER: DOCUMENT_WRITER_SYSTEM,
}


# =============================================================================
# AGENT BASE CLASS
# =============================================================================

class Agent(ABC):
    """Abstract base agent"""
    
    def __init__(self, role: AgentRole):
        self.role = role
        self.system_prompt = AGENT_PROMPTS[role]
    
    @abstractmethod
    async def run(self, context: dict) -> AgentOutput:
        """Ajan çalıştır"""
        pass
    
    def _parse_json_output(self, content: str) -> dict:
        """JSON çıktısını parse et"""
        # JSON bloğunu bul
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            content = content[start:end].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            content = content[start:end].strip()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"raw_content": content, "parse_error": True}


class PlannerAgent(Agent):
    """Planner ajan implementasyonu"""
    
    def __init__(self):
        super().__init__(AgentRole.PLANNER)
    
    async def run(self, context: dict) -> AgentOutput:
        """Plan oluştur"""
        from .llm_gateway import get_llm_gateway
        
        gateway = get_llm_gateway()
        
        # Context'ten task ve proje bilgisi al
        task_description = context.get("task", "")
        project_context = context.get("project_context", "")
        
        messages = [
            {
                "role": "user",
                "content": f"""Görev: {task_description}

Proje Bağlamı:
{project_context}

Lütfen detaylı bir implementasyon planı oluştur."""
            }
        ]
        
        response = await gateway.generate(
            model_key=context.get("model", "claude-sonnet"),
            messages=messages,
            system=self.system_prompt,
        )
        
        parsed = self._parse_json_output(response.content)
        
        return AgentOutput(
            role=self.role,
            success=not parsed.get("parse_error", False),
            content=parsed,
            reasoning=response.content,
            confidence=0.9 if not parsed.get("parse_error") else 0.5,
            metadata={"model": response.model, "cost": response.cost}
        )


class ImplementerAgent(Agent):
    """Implementer ajan implementasyonu"""
    
    def __init__(self):
        super().__init__(AgentRole.IMPLEMENTER)
    
    async def run(self, context: dict) -> AgentOutput:
        """Kod implement et"""
        from .llm_gateway import get_llm_gateway
        from .tool_executor import get_tool_executor
        
        gateway = get_llm_gateway()
        executor = get_tool_executor()
        
        plan = context.get("plan", {})
        current_step = context.get("current_step", 0)
        file_contents = context.get("file_contents", {})
        
        messages = [
            {
                "role": "user",
                "content": f"""Plan:
{json.dumps(plan, indent=2, ensure_ascii=False)}

Mevcut Adım: {current_step}

Mevcut Dosya İçerikleri:
{json.dumps(file_contents, indent=2, ensure_ascii=False)}

Lütfen bu adımı implement et."""
            }
        ]
        
        response = await gateway.generate(
            model_key=context.get("model", "claude-sonnet"),
            messages=messages,
            system=self.system_prompt,
        )
        
        parsed = self._parse_json_output(response.content)
        
        # Dosya değişikliklerini uygula
        files_affected = []
        if "files_changed" in parsed:
            for file_change in parsed["files_changed"]:
                files_affected.append(file_change.get("path", "unknown"))
        
        return AgentOutput(
            role=self.role,
            success=not parsed.get("parse_error", False),
            content=parsed,
            reasoning=response.content,
            confidence=0.85 if not parsed.get("parse_error") else 0.4,
            files_affected=files_affected,
            metadata={"model": response.model, "cost": response.cost}
        )


class ReviewerAgent(Agent):
    """Reviewer ajan implementasyonu"""
    
    def __init__(self):
        super().__init__(AgentRole.REVIEWER)
    
    async def run(self, context: dict) -> AgentOutput:
        """Kod incele"""
        from .llm_gateway import get_llm_gateway
        
        gateway = get_llm_gateway()
        
        diff = context.get("diff", "")
        file_contents = context.get("file_contents", {})
        
        messages = [
            {
                "role": "user",
                "content": f"""Değişiklikler (Diff):
{diff}

Güncel Dosya İçerikleri:
{json.dumps(file_contents, indent=2, ensure_ascii=False)}

Lütfen bu değişiklikleri incele ve feedback ver."""
            }
        ]
        
        response = await gateway.generate(
            model_key=context.get("model", "claude-sonnet"),
            messages=messages,
            system=self.system_prompt,
        )
        
        parsed = self._parse_json_output(response.content)
        
        return AgentOutput(
            role=self.role,
            success=parsed.get("approved", False),
            content=parsed,
            reasoning=response.content,
            confidence=parsed.get("score", 50) / 100,
            metadata={"model": response.model, "cost": response.cost}
        )


class FixerAgent(Agent):
    """Fixer ajan implementasyonu"""
    
    def __init__(self):
        super().__init__(AgentRole.FIXER)
    
    async def run(self, context: dict) -> AgentOutput:
        """Hata düzelt"""
        from .llm_gateway import get_llm_gateway
        
        gateway = get_llm_gateway()
        
        issues = context.get("issues", [])
        file_contents = context.get("file_contents", {})
        
        messages = [
            {
                "role": "user",
                "content": f"""Düzeltilecek Sorunlar:
{json.dumps(issues, indent=2, ensure_ascii=False)}

Mevcut Dosya İçerikleri:
{json.dumps(file_contents, indent=2, ensure_ascii=False)}

Lütfen bu sorunları düzelt."""
            }
        ]
        
        response = await gateway.generate(
            model_key=context.get("model", "claude-sonnet"),
            messages=messages,
            system=self.system_prompt,
        )
        
        parsed = self._parse_json_output(response.content)
        
        files_affected = []
        if "fixes_applied" in parsed:
            for fix in parsed["fixes_applied"]:
                if fix.get("file"):
                    files_affected.append(fix["file"])
        
        return AgentOutput(
            role=self.role,
            success=len(parsed.get("remaining_issues", [])) == 0,
            content=parsed,
            reasoning=response.content,
            confidence=parsed.get("confidence", 0.7),
            files_affected=files_affected,
            metadata={"model": response.model, "cost": response.cost}
        )


class TesterAgent(Agent):
    """Tester ajan implementasyonu"""
    
    def __init__(self):
        super().__init__(AgentRole.TESTER)
    
    async def run(self, context: dict) -> AgentOutput:
        """Test yaz ve çalıştır"""
        from .llm_gateway import get_llm_gateway
        
        gateway = get_llm_gateway()
        
        code_to_test = context.get("code", "")
        existing_tests = context.get("existing_tests", "")
        
        messages = [
            {
                "role": "user",
                "content": f"""Test Edilecek Kod:
{code_to_test}

Mevcut Testler:
{existing_tests}

Lütfen gerekli testleri yaz."""
            }
        ]
        
        response = await gateway.generate(
            model_key=context.get("model", "claude-sonnet"),
            messages=messages,
            system=self.system_prompt,
        )
        
        parsed = self._parse_json_output(response.content)
        
        files_affected = []
        if "tests_written" in parsed:
            for test in parsed["tests_written"]:
                if test.get("file"):
                    files_affected.append(test["file"])
        
        return AgentOutput(
            role=self.role,
            success=parsed.get("test_results", {}).get("failed", 1) == 0,
            content=parsed,
            reasoning=response.content,
            confidence=0.85,
            files_affected=files_affected,
            metadata={"model": response.model, "cost": response.cost}
        )


class SecurityAuditorAgent(Agent):
    """Security Auditor ajan implementasyonu"""
    
    def __init__(self):
        super().__init__(AgentRole.SECURITY_AUDITOR)
    
    async def run(self, context: dict) -> AgentOutput:
        """Güvenlik analizi"""
        from .llm_gateway import get_llm_gateway
        
        gateway = get_llm_gateway()
        
        code_to_audit = context.get("code", "")
        
        messages = [
            {
                "role": "user",
                "content": f"""Güvenlik Analizi Yapılacak Kod:
{code_to_audit}

Lütfen kapsamlı güvenlik analizi yap."""
            }
        ]
        
        response = await gateway.generate(
            model_key=context.get("model", "claude-sonnet"),
            messages=messages,
            system=self.system_prompt,
        )
        
        parsed = self._parse_json_output(response.content)
        
        # Critical vulnerability varsa success=False
        has_critical = any(
            v.get("severity") == "critical"
            for v in parsed.get("vulnerabilities", [])
        )
        
        return AgentOutput(
            role=self.role,
            success=not has_critical,
            content=parsed,
            reasoning=response.content,
            confidence=0.8,
            metadata={"model": response.model, "cost": response.cost}
        )


class DocumentWriterAgent(Agent):
    """Document Writer ajan implementasyonu"""
    
    def __init__(self):
        super().__init__(AgentRole.DOCUMENT_WRITER)
    
    async def run(self, context: dict) -> AgentOutput:
        """Dokümantasyon yaz"""
        from .llm_gateway import get_llm_gateway
        
        gateway = get_llm_gateway()
        
        code_to_document = context.get("code", "")
        doc_type = context.get("doc_type", "inline")
        
        messages = [
            {
                "role": "user",
                "content": f"""Dokümante Edilecek Kod:
{code_to_document}

Dokümantasyon Tipi: {doc_type}

Lütfen uygun dokümantasyon oluştur."""
            }
        ]
        
        response = await gateway.generate(
            model_key=context.get("model", "claude-sonnet"),
            messages=messages,
            system=self.system_prompt,
        )
        
        parsed = self._parse_json_output(response.content)
        
        files_affected = []
        if "documents_created" in parsed:
            for doc in parsed["documents_created"]:
                if doc.get("file"):
                    files_affected.append(doc["file"])
        
        return AgentOutput(
            role=self.role,
            success=True,
            content=parsed,
            reasoning=response.content,
            confidence=0.9,
            files_affected=files_affected,
            metadata={"model": response.model, "cost": response.cost}
        )


# =============================================================================
# AGENT FACTORY
# =============================================================================

class AgentFactory:
    """Ajan factory - rol bazlı ajan oluşturma"""
    
    _agents: dict[AgentRole, type[Agent]] = {
        AgentRole.PLANNER: PlannerAgent,
        AgentRole.IMPLEMENTER: ImplementerAgent,
        AgentRole.REVIEWER: ReviewerAgent,
        AgentRole.FIXER: FixerAgent,
        AgentRole.TESTER: TesterAgent,
        AgentRole.SECURITY_AUDITOR: SecurityAuditorAgent,
        AgentRole.DOCUMENT_WRITER: DocumentWriterAgent,
    }
    
    @classmethod
    def create(cls, role: AgentRole) -> Agent:
        """Rol için ajan oluştur"""
        agent_class = cls._agents.get(role)
        if not agent_class:
            raise ValueError(f"Unknown agent role: {role}")
        return agent_class()
    
    @classmethod
    def get_all_roles(cls) -> list[AgentRole]:
        """Tüm rolleri döndür"""
        return list(cls._agents.keys())


def get_agent(role: AgentRole) -> Agent:
    """Convenience function for agent creation"""
    return AgentFactory.create(role)
