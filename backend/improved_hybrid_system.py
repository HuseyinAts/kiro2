"""
Improved Hybrid AI System
Gemini 3 Pro + Claude Sonnet 4.5
Her modelin güçlü yönlerini optimal kullanım
"""

import asyncio
from typing import Optional, Dict, Any, List
from enum import Enum
import structlog

logger = structlog.get_logger()


class QueryType(Enum):
    """Query tipleri"""
    SIMPLE_QUESTION = "simple_question"
    CODE_REVIEW = "code_review"
    MULTI_TOOL = "multi_tool"
    DIAGRAM_ANALYSIS = "diagram_analysis"
    DEEP_ANALYSIS = "deep_analysis"
    TURKISH_CONTENT = "turkish_content"
    TOOL_ORCHESTRATION = "tool_orchestration"


class ModelRole(Enum):
    """Model rolleri"""
    CLAUDE_DIRECT = "claude_direct"  # Hızlı yanıt
    CLAUDE_CODE_REVIEW = "claude_code_review"  # Basit kod review
    CLAUDE_ORCHESTRATOR = "claude_orchestrator"  # Tool coordination
    GEMINI_THINKING = "gemini_thinking"  # Derin analiz
    GEMINI_MULTIMODAL = "gemini_multimodal"  # Diagram/image
    GEMINI_STANDARD = "gemini_standard"  # Standart kullanım


class ImprovedRouter:
    """İyileştirilmiş akıllı router - Her modelin güçlü yönlerini kullanır"""
    
    def classify_query(self, query: str, context: Optional[Dict] = None) -> QueryType:
        """Query tipini belirle"""
        query_lower = query.lower()
        
        # Diagram analizi mi?
        if context and context.get("image_path"):
            return QueryType.DIAGRAM_ANALYSIS
        
        # Kod review mu?
        if any(kw in query_lower for kw in ["kod", "code", "incele", "review"]):
            if context and context.get("code"):
                return QueryType.CODE_REVIEW
        
        # Multi-tool mu?
        if context and len(context.keys()) > 2:  # Birden fazla dosya
            return QueryType.MULTI_TOOL
        
        # Türkçe içerik mi?
        turkish_keywords = ["lgs", "yks", "soru üret", "türkçe", "eğitim"]
        if any(kw in query_lower for kw in turkish_keywords):
            return QueryType.TURKISH_CONTENT
        
        # Derin analiz mi?
        analysis_keywords = ["analiz", "değerlendir", "detaylı", "adım adım"]
        if any(kw in query_lower for kw in analysis_keywords):
            return QueryType.DEEP_ANALYSIS
        
        # Tool orchestration mu?
        if "ve" in query_lower and len(query.split()) > 15:
            return QueryType.TOOL_ORCHESTRATION
        
        # Default: Basit soru
        return QueryType.SIMPLE_QUESTION
    
    def analyze_code_complexity(self, code: str) -> int:
        """Kod karmaşıklığını analiz et (0-10)"""
        score = 0
        
        # Satır sayısı
        lines = len(code.split('\n'))
        if lines > 100:
            score += 3
        elif lines > 50:
            score += 2
        elif lines > 20:
            score += 1
        
        # Fonksiyon sayısı
        func_count = code.count('def ') + code.count('function ')
        if func_count > 5:
            score += 2
        elif func_count > 2:
            score += 1
        
        # Class sayısı
        class_count = code.count('class ')
        if class_count > 3:
            score += 2
        elif class_count > 1:
            score += 1
        
        # Nested yapılar
        if '    ' * 4 in code:  # 4+ level indentation
            score += 2
        
        return min(score, 10)
    
    def route(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Optimal routing - Her modelin güçlü yönlerini kullan
        
        Returns:
            {
                "primary": Model adı,
                "mode": Kullanım modu,
                "secondary": İkincil model (opsiyonel),
                "estimated_time": Tahmini süre,
                "reason": Karar gerekçesi
            }
        """
        query_type = self.classify_query(query, context)
        
        # Simple Question → Claude (Hız)
        if query_type == QueryType.SIMPLE_QUESTION:
            return {
                "primary": "claude",
                "role": ModelRole.CLAUDE_DIRECT,
                "estimated_time": 1.5,
                "estimated_cost": 0.003,
                "reason": "Basit soru - Claude hızlı ve yeterli"
            }
        
        # Code Review → Complexity-based
        elif query_type == QueryType.CODE_REVIEW:
            code = context.get("code", "")
            complexity = self.analyze_code_complexity(code)
            
            if complexity < 5:
                return {
                    "primary": "claude",
                    "role": ModelRole.CLAUDE_CODE_REVIEW,
                    "estimated_time": 3.0,
                    "estimated_cost": 0.004,
                    "reason": f"Basit kod (complexity: {complexity}) - Claude yeterli ve hızlı"
                }
            else:
                return {
                    "primary": "gemini",
                    "role": ModelRole.GEMINI_THINKING,
                    "estimated_time": 10.0,
                    "estimated_cost": 0.008,
                    "reason": f"Karmaşık kod (complexity: {complexity}) - Gemini thinking gerekli"
                }
        
        # Multi-Tool → Claude Orchestrator + Gemini Executor
        elif query_type == QueryType.MULTI_TOOL:
            return {
                "primary": "claude",
                "role": ModelRole.CLAUDE_ORCHESTRATOR,
                "secondary": "gemini",
                "estimated_time": 15.0,
                "estimated_cost": 0.012,
                "reason": "Multi-tool - Claude orchestrate, Gemini execute (parallel)"
            }
        
        # Diagram Analysis → Gemini Multimodal
        elif query_type == QueryType.DIAGRAM_ANALYSIS:
            return {
                "primary": "gemini",
                "role": ModelRole.GEMINI_MULTIMODAL,
                "estimated_time": 8.0,
                "estimated_cost": 0.007,
                "reason": "Diagram analizi - Gemini multimodal yeteneği"
            }
        
        # Deep Analysis → Gemini Thinking
        elif query_type == QueryType.DEEP_ANALYSIS:
            return {
                "primary": "gemini",
                "role": ModelRole.GEMINI_THINKING,
                "estimated_time": 20.0,
                "estimated_cost": 0.010,
                "reason": "Derin analiz - Gemini thinking mode"
            }
        
        # Turkish Content → Gemini
        elif query_type == QueryType.TURKISH_CONTENT:
            return {
                "primary": "gemini",
                "role": ModelRole.GEMINI_STANDARD,
                "estimated_time": 5.0,
                "estimated_cost": 0.006,
                "reason": "Türkçe içerik - Gemini native Turkish support"
            }
        
        # Tool Orchestration → Claude
        elif query_type == QueryType.TOOL_ORCHESTRATION:
            return {
                "primary": "claude",
                "role": ModelRole.CLAUDE_ORCHESTRATOR,
                "secondary": "gemini",
                "estimated_time": 12.0,
                "estimated_cost": 0.010,
                "reason": "Tool orchestration - Claude'un güçlü yönü"
            }
        
        # Default
        else:
            return {
                "primary": "claude",
                "role": ModelRole.CLAUDE_DIRECT,
                "estimated_time": 2.0,
                "estimated_cost": 0.003,
                "reason": "Default routing"
            }


class ClaudeOrchestrator:
    """Claude'un tool orchestration yeteneğini kullan"""
    
    async def orchestrate_parallel_analysis(
        self,
        tasks: List[Dict[str, Any]]
    ) -> List[Any]:
        """
        Paralel analiz orchestration
        
        Args:
            tasks: [
                {"type": "code_review", "data": code},
                {"type": "design_analysis", "data": design},
                {"type": "requirements_analysis", "data": requirements}
            ]
        
        Returns:
            Paralel sonuçlar
        """
        logger.info(
            "claude_orchestration_started",
            task_count=len(tasks)
        )
        
        # Paralel execution
        async_tasks = []
        for task in tasks:
            if task["type"] == "code_review":
                async_tasks.append(self._gemini_code_review(task["data"]))
            elif task["type"] == "design_analysis":
                async_tasks.append(self._gemini_design_analysis(task["data"]))
            elif task["type"] == "requirements_analysis":
                async_tasks.append(self._gemini_requirements_analysis(task["data"]))
        
        # Paralel çalıştır
        results = await asyncio.gather(*async_tasks, return_exceptions=True)
        
        logger.info(
            "claude_orchestration_completed",
            success_count=sum(1 for r in results if not isinstance(r, Exception))
        )
        
        return results
    
    async def _gemini_code_review(self, code: str) -> str:
        """Gemini kod review (simulated)"""
        await asyncio.sleep(0.1)
        return f"[Gemini Code Review] {code[:50]}..."
    
    async def _gemini_design_analysis(self, design: str) -> str:
        """Gemini design analysis (simulated)"""
        await asyncio.sleep(0.1)
        return f"[Gemini Design Analysis] {design[:50]}..."
    
    async def _gemini_requirements_analysis(self, requirements: str) -> str:
        """Gemini requirements analysis (simulated)"""
        await asyncio.sleep(0.1)
        return f"[Gemini Requirements Analysis] {requirements[:50]}..."


class ImprovedHybridSystem:
    """İyileştirilmiş hibrit sistem - Her modelin güçlü yönlerini kullanır"""
    
    def __init__(self):
        self.router = ImprovedRouter()
        self.orchestrator = ClaudeOrchestrator()
        
        # Metrics
        self.metrics = {
            "claude_direct": 0,
            "claude_code_review": 0,
            "claude_orchestrator": 0,
            "gemini_thinking": 0,
            "gemini_multimodal": 0,
            "gemini_standard": 0
        }
    
    async def process_query(
        self,
        query: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Query'yi optimal şekilde işle"""
        
        # Routing
        routing = self.router.route(query, context)
        
        logger.info(
            "query_routed",
            query_type=routing.get("reason"),
            primary=routing["primary"],
            role=routing["role"].value
        )
        
        # Model çağrısı
        if routing["role"] == ModelRole.CLAUDE_ORCHESTRATOR:
            # Multi-tool orchestration
            result = await self._handle_orchestration(query, context, routing)
        else:
            # Single model
            result = await self._handle_single_model(query, context, routing)
        
        # Metrics
        self.metrics[routing["role"].value] += 1
        
        return result
    
    async def _handle_orchestration(
        self,
        query: str,
        context: Dict,
        routing: Dict
    ) -> Dict[str, Any]:
        """Claude orchestration handling"""
        
        # Hangi task'lar gerekli?
        tasks = []
        
        if context.get("code"):
            tasks.append({"type": "code_review", "data": context["code"]})
        if context.get("design"):
            tasks.append({"type": "design_analysis", "data": context["design"]})
        if context.get("requirements"):
            tasks.append({"type": "requirements_analysis", "data": context["requirements"]})
        
        # Paralel execution
        results = await self.orchestrator.orchestrate_parallel_analysis(tasks)
        
        # Claude synthesizes results
        synthesis = f"[Claude Synthesis] Combined {len(results)} analyses"
        
        return {
            "response": synthesis,
            "details": results,
            "routing": routing,
            "parallel": True
        }
    
    async def _handle_single_model(
        self,
        query: str,
        context: Optional[Dict],
        routing: Dict
    ) -> Dict[str, Any]:
        """Single model handling"""
        
        # Simulated API call
        await asyncio.sleep(0.1)
        
        response = f"[{routing['primary'].upper()}] Response to: {query[:50]}..."
        
        return {
            "response": response,
            "routing": routing,
            "parallel": False
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Kullanım metriklerini döndür"""
        total = sum(self.metrics.values())
        
        return {
            "total_requests": total,
            "usage_breakdown": self.metrics,
            "usage_percentage": {
                k: (v / total * 100) if total > 0 else 0
                for k, v in self.metrics.items()
            }
        }


# Test
async def main():
    """Test scenarios"""
    system = ImprovedHybridSystem()
    
    test_cases = [
        {
            "name": "Basit Soru",
            "query": "Python nedir?",
            "context": None
        },
        {
            "name": "Basit Kod Review",
            "query": "Bu kodu incele",
            "context": {"code": "def hello(): print('hi')"}
        },
        {
            "name": "Karmaşık Kod Review",
            "query": "Bu kodu incele",
            "context": {"code": "class Complex:\n" + "    def method():\n" * 20}
        },
        {
            "name": "Multi-Tool Orchestration",
            "query": "Tüm dosyaları analiz et",
            "context": {
                "code": "def test(): pass",
                "design": "# Design doc",
                "requirements": "# Requirements"
            }
        },
        {
            "name": "Türkçe İçerik",
            "query": "8. sınıf için LGS sorusu üret",
            "context": None
        }
    ]
    
    print("\n" + "=" * 80)
    print("İYİLEŞTİRİLMİŞ HİBRİT SİSTEM TEST")
    print("=" * 80 + "\n")
    
    for test in test_cases:
        print(f"\n📝 Test: {test['name']}")
        print(f"Query: {test['query']}")
        
        result = await system.process_query(test['query'], test['context'])
        
        routing = result['routing']
        print(f"✓ Primary: {routing['primary']}")
        print(f"✓ Role: {routing['role'].value}")
        print(f"✓ Time: {routing['estimated_time']}s")
        print(f"✓ Cost: ${routing['estimated_cost']:.4f}")
        print(f"✓ Reason: {routing['reason']}")
        print(f"✓ Parallel: {result.get('parallel', False)}")
    
    print("\n" + "=" * 80)
    print("KULLANIM METRİKLERİ")
    print("=" * 80 + "\n")
    
    metrics = system.get_metrics()
    print(f"Total Requests: {metrics['total_requests']}\n")
    
    print("Usage Breakdown:")
    for role, count in metrics['usage_breakdown'].items():
        percentage = metrics['usage_percentage'][role]
        print(f"  {role}: {count} ({percentage:.1f}%)")


if __name__ == "__main__":
    asyncio.run(main())
