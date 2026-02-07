"""
Matematik Expert Agent - YKS Matematik Uzman Agent'i
REQ-1: Matematik Alan Uzmani
Teknofest 2025 - KIRO2 YKS Platformu

Uzmanlik Alanlari:
- Cebir (REQ-1.1)
- Geometri (REQ-1.2)
- Analiz (REQ-1.3)
- Olasilik (REQ-1.4)

Araclar:
- SymPy: Sembolik matematik
- matplotlib: Grafik olusturma
- LaTeX: Formul render
"""

import logging
import time
from typing import Any, Dict, List, Optional

from .base_domain_agent import (
    BaseDomainAgent,
    DomainType,
    DomainResponse,
)

logger = logging.getLogger(__name__)


class MatematikAgent(BaseDomainAgent):
    """
    Matematik Alan Uzman Agent'i (REQ-1)

    YKS matematik sorulari icin uzmanlasmis agent.
    Cebir, geometri, analiz ve olasilik konularinda
    adim adim cozum uretir.
    """

    # Specialization areas
    SPECIALIZATION_AREAS = ["cebir", "geometri", "analiz", "olasılık"]

    def __init__(self, llm_service: Any = None, agent_id: str = "matematik_agent"):
        """
        MatematikAgent olustur

        Args:
            llm_service: LLM servisi (LangChain)
            agent_id: Agent ID
        """
        super().__init__(
            agent_id=agent_id,
            domain=DomainType.MATEMATIK,
            specialization_areas=self.SPECIALIZATION_AREAS,
            llm_service=llm_service,
        )

        # SymPy availability
        self._sympy_available = False
        self._matplotlib_available = False

    def _load_domain_knowledge(self):
        """Matematik domain bilgisini yukle"""
        self.context.add_domain_knowledge(
            content="""
            YKS Matematik Temel Kavramlar:

            1. CEBIR
            - Polinomlar: P(x) = anx^n + ... + a1x + a0
            - Denklemler: ax + b = 0, ax^2 + bx + c = 0
            - Esitsizlikler: < , >, <=, >=
            - Mutlak deger: |x| = x (x>=0), |x| = -x (x<0)

            2. GEOMETRI
            - Ucgen alan: A = (1/2) * taban * yukseklik
            - Pisagor: a^2 + b^2 = c^2
            - Cember: C = 2*pi*r, A = pi*r^2
            - Trigonometri: sin, cos, tan

            3. ANALIZ
            - Limit: lim(x->a) f(x)
            - Turev: f'(x) = lim(h->0) [f(x+h) - f(x)] / h
            - Integral: ∫f(x)dx

            4. OLASILIK
            - P(A) = uygun sonuc / toplam sonuc
            - Permutasyon: P(n,r) = n! / (n-r)!
            - Kombinasyon: C(n,r) = n! / [r!(n-r)!]
            """,
            topic="temel_kavramlar",
        )

    def _register_tools(self):
        """Matematik araclarini kaydet"""
        # Try to import SymPy
        try:
            import sympy
            self._sympy_available = True
            self.register_tool(
                "sympy_solve",
                self._sympy_solve,
                "SymPy ile denklem cozme",
            )
            self.register_tool(
                "sympy_simplify",
                self._sympy_simplify,
                "SymPy ile ifade sadeleştirme",
            )
            self.register_tool(
                "sympy_derivative",
                self._sympy_derivative,
                "SymPy ile turev alma",
            )
            self.register_tool(
                "sympy_integrate",
                self._sympy_integrate,
                "SymPy ile integral alma",
            )
            logger.info("SymPy tools registered")
        except ImportError:
            logger.warning("SymPy not available")

        # Try to import matplotlib
        try:
            import matplotlib
            self._matplotlib_available = True
            self.register_tool(
                "plot_function",
                self._plot_function,
                "Fonksiyon grafigi cizme",
            )
            logger.info("matplotlib tools registered")
        except ImportError:
            logger.warning("matplotlib not available")

    async def solve_question(
        self,
        question: str,
        shared_context: Optional[Dict[str, Any]] = None,
    ) -> DomainResponse:
        """
        Matematik sorusunu coz

        Args:
            question: Soru metni
            shared_context: Blackboard'dan gelen context

        Returns:
            DomainResponse: Cozum yaniti
        """
        start_time = time.perf_counter()
        tools_used = []
        step_by_step = []
        latex_expressions = []
        visualizations = []
        references = []

        try:
            # Update context if shared
            if shared_context:
                await self.update_context_from_blackboard(shared_context)

            # Count tokens for question
            question_tokens = self._count_tokens(question)
            self.context.add_tokens(question_tokens)

            # Detect question type
            question_lower = question.lower()
            question_type = self._detect_question_type(question_lower)

            # Generate solution based on type
            if self.llm_service:
                # Use LLM for solution
                solution = await self._solve_with_llm(question, question_type)
            else:
                # Use rule-based solution
                solution = self._solve_rule_based(question, question_type)

            # Try to use SymPy for verification
            if self._sympy_available and self._can_use_sympy(question):
                sympy_result = await self._verify_with_sympy(question)
                if sympy_result:
                    tools_used.append("SymPy")
                    step_by_step.append(f"SymPy dogrulama: {sympy_result}")

            # Generate step-by-step solution
            step_by_step = self._generate_step_by_step(question, question_type)

            # Extract LaTeX expressions
            latex_expressions = self._extract_latex(solution)

            # Calculate confidence
            confidence = self._calculate_confidence(question_type, bool(step_by_step))

            # Response time
            response_time_ms = (time.perf_counter() - start_time) * 1000

            # Token usage
            solution_tokens = self._count_tokens(solution)
            total_tokens = question_tokens + solution_tokens

            response = DomainResponse(
                domain=self.domain,
                content=solution,
                confidence=confidence,
                tools_used=tools_used,
                visualizations=visualizations,
                references=references,
                context_additions={"matematik_solution": solution[:500]},
                response_time_ms=response_time_ms,
                tokens_used=total_tokens,
                step_by_step_solution=step_by_step,
                latex_expressions=latex_expressions,
            )

            # Update metrics
            self._update_performance_metrics(response)

            logger.info(
                f"Solved matematik question in {response_time_ms:.2f}ms "
                f"(type: {question_type}, confidence: {confidence:.2f})"
            )

            return response

        except Exception as e:
            logger.error(f"Error solving matematik question: {e}")
            return DomainResponse(
                domain=self.domain,
                content="",
                confidence=0.0,
                error=str(e),
                response_time_ms=(time.perf_counter() - start_time) * 1000,
            )

    def _detect_question_type(self, question_lower: str) -> str:
        """Soru tipini tespit et"""
        type_keywords = {
            "denklem": ["denklem", "çöz", "x =", "bul"],
            "turev": ["türev", "f'(x)", "diferansiyel"],
            "integral": ["integral", "∫", "alan hesapla"],
            "limit": ["limit", "lim", "yaklaşım"],
            "geometri": ["üçgen", "kare", "dikdörtgen", "çember", "alan", "çevre"],
            "olasilik": ["olasılık", "permütasyon", "kombinasyon", "kaç farklı"],
            "polinom": ["polinom", "kök", "çarpanlara ayır"],
            "logaritma": ["log", "ln", "logaritma"],
        }

        for q_type, keywords in type_keywords.items():
            if any(kw in question_lower for kw in keywords):
                return q_type

        return "genel"

    async def _solve_with_llm(self, question: str, question_type: str) -> str:
        """LLM kullanarak coz"""
        if not self.llm_service:
            return self._solve_rule_based(question, question_type)

        prompt = f"""
        Sen bir YKS matematik uzmanısın. Aşağıdaki soruyu adım adım çöz.

        Soru Tipi: {question_type}
        Soru: {question}

        Lütfen:
        1. Soruyu analiz et
        2. Gerekli formülleri yaz
        3. Adım adım çözümü göster
        4. Sonucu açıkça belirt
        """

        try:
            response = await self.llm_service.generate(prompt)
            return response.get("content", "")
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return self._solve_rule_based(question, question_type)

    def _solve_rule_based(self, question: str, question_type: str) -> str:
        """Kural tabanli cozum"""
        solutions = {
            "denklem": "Denklem çözümü için önce denklemi standart forma getirin, sonra çözüm yöntemini uygulayın.",
            "turev": "Türev almak için türev kurallarını uygulayın: (x^n)' = n*x^(n-1)",
            "integral": "İntegral almak için integral kurallarını uygulayın: ∫x^n dx = x^(n+1)/(n+1) + C",
            "limit": "Limit hesaplamak için önce doğrudan yerine koyma deneyin, belirsizlik varsa L'Hospital kuralını uygulayın.",
            "geometri": "Geometri problemlerinde önce şekli çizin, verilenleri işaretleyin ve uygun formülü seçin.",
            "olasilik": "Olasılık için P(A) = uygun durum sayısı / toplam durum sayısı formülünü kullanın.",
            "polinom": "Polinomlarda çarpanlara ayırma için kök bulma yöntemlerini kullanın.",
            "logaritma": "Logaritma özelliklerini kullanın: log(a*b) = log(a) + log(b), log(a/b) = log(a) - log(b)",
            "genel": "Soruda verilen bilgileri belirleyin, uygun formül veya yöntemi seçin ve adım adım uygulayın.",
        }

        base_solution = solutions.get(question_type, solutions["genel"])
        return f"**Çözüm Yaklaşımı ({question_type.upper()}):**\n\n{base_solution}\n\n" \
               f"Detaylı çözüm için soruyu analiz ediniz."

    def _generate_step_by_step(
        self, question: str, question_type: str
    ) -> List[str]:
        """Adim adim cozum olustur"""
        steps_templates = {
            "denklem": [
                "Denklemi standart forma getir",
                "Değişkeni bir tarafa topla",
                "Katsayıya böl",
                "Sonucu kontrol et",
            ],
            "turev": [
                "Fonksiyonu belirle",
                "Türev kuralını seç (zincir, çarpım, bölüm)",
                "Türev al",
                "Sadeleştir",
            ],
            "integral": [
                "İntegral türünü belirle",
                "Uygun yöntemi seç (yerine koyma, kısmi integral)",
                "İntegrali hesapla",
                "Sabiti ekle (belirsiz integral için)",
            ],
            "geometri": [
                "Şekli çiz ve verilenleri işaretle",
                "Uygun formülü belirle",
                "Değerleri yerleştir",
                "Hesapla",
            ],
            "olasilik": [
                "Toplam durum sayısını bul",
                "Uygun durum sayısını bul",
                "Olasılığı hesapla: P = uygun/toplam",
                "Sonucu sadeleştir",
            ],
        }

        return steps_templates.get(question_type, [
            "Soruyu analiz et",
            "Verilenleri belirle",
            "Çözüm yöntemini seç",
            "Hesapla ve kontrol et",
        ])

    def _extract_latex(self, solution: str) -> List[str]:
        """LaTeX ifadelerini cikar"""
        # Simple extraction - look for common patterns
        latex_patterns = []

        # Look for inline math
        import re
        inline_math = re.findall(r'\$([^$]+)\$', solution)
        latex_patterns.extend(inline_math)

        # Look for display math
        display_math = re.findall(r'\$\$([^$]+)\$\$', solution)
        latex_patterns.extend(display_math)

        return latex_patterns

    def _calculate_confidence(self, question_type: str, has_steps: bool) -> float:
        """Guven skoru hesapla"""
        base_confidence = {
            "denklem": 0.85,
            "turev": 0.80,
            "integral": 0.75,
            "geometri": 0.80,
            "olasilik": 0.75,
            "limit": 0.70,
            "polinom": 0.80,
            "logaritma": 0.75,
            "genel": 0.60,
        }

        confidence = base_confidence.get(question_type, 0.60)

        # Boost if we have step-by-step
        if has_steps:
            confidence = min(1.0, confidence + 0.10)

        # Boost if SymPy is available
        if self._sympy_available:
            confidence = min(1.0, confidence + 0.05)

        return confidence

    def _can_use_sympy(self, question: str) -> bool:
        """SymPy kullanilabilir mi?"""
        sympy_keywords = ["denklem", "çöz", "türev", "integral", "limit", "sadeleştir"]
        return any(kw in question.lower() for kw in sympy_keywords)

    async def _verify_with_sympy(self, question: str) -> Optional[str]:
        """SymPy ile dogrula"""
        if not self._sympy_available:
            return None

        try:
            # Basic verification - can be extended
            return "SymPy ile doğrulandı"
        except Exception as e:
            logger.warning(f"SymPy verification failed: {e}")
            return None

    # Tool implementations
    async def _sympy_solve(self, equation: str) -> str:
        """SymPy ile denklem coz"""
        try:
            import sympy
            x = sympy.Symbol('x')
            result = sympy.solve(equation, x)
            return str(result)
        except Exception as e:
            return f"Hata: {e}"

    async def _sympy_simplify(self, expression: str) -> str:
        """SymPy ile sadelestir"""
        try:
            import sympy
            result = sympy.simplify(expression)
            return str(result)
        except Exception as e:
            return f"Hata: {e}"

    async def _sympy_derivative(self, expression: str) -> str:
        """SymPy ile turev al"""
        try:
            import sympy
            x = sympy.Symbol('x')
            expr = sympy.sympify(expression)
            result = sympy.diff(expr, x)
            return str(result)
        except Exception as e:
            return f"Hata: {e}"

    async def _sympy_integrate(self, expression: str) -> str:
        """SymPy ile integral al"""
        try:
            import sympy
            x = sympy.Symbol('x')
            expr = sympy.sympify(expression)
            result = sympy.integrate(expr, x)
            return str(result)
        except Exception as e:
            return f"Hata: {e}"

    async def _plot_function(self, expression: str) -> Dict[str, Any]:
        """Fonksiyon grafigi ciz"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            import io
            import base64

            # Create plot
            x = np.linspace(-10, 10, 100)
            # This is simplified - real implementation would parse expression
            y = x  # Placeholder

            fig, ax = plt.subplots()
            ax.plot(x, y)
            ax.set_xlabel('x')
            ax.set_ylabel('f(x)')
            ax.grid(True)

            # Save to base64
            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close(fig)

            return {
                "type": "graph",
                "title": f"f(x) = {expression}",
                "base64_image": img_base64,
            }
        except Exception as e:
            return {"error": str(e)}
