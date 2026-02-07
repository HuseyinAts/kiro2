"""
KIRO2 Math Verification Service
SymPy ile matematik çözümlerinin doğrulanması (REQ-4)

Desteklenen problem tipleri:
- Algebra: Denklem çözümü, polinomlar, rasyonel ifadeler
- Geometry: Geometrik hesaplamalar
- Calculus: Türev, integral, limit

Türkiye YKS/TYT/AYT müfredatına uygun.
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

# SymPy import - lazy loading for optional dependency
_sympy_available = False
_sympy_modules: dict[str, Any] = {}

def _load_sympy():
    """Lazy load SymPy modules."""
    global _sympy_available, _sympy_modules
    if _sympy_available:
        return True
    try:
        import sympy
        from sympy import (
            symbols, Symbol, Eq, solve, simplify, expand, factor,
            diff, integrate, limit, sqrt, Rational, pi, E,
            sin, cos, tan, log, exp, oo,
            parse_expr, sympify,
        )
        from sympy.parsing.sympy_parser import (
            parse_expr as parse_expression,
            standard_transformations,
            implicit_multiplication_application,
            convert_xor,
        )
        _sympy_modules = {
            'sympy': sympy,
            'symbols': symbols,
            'Symbol': Symbol,
            'Eq': Eq,
            'solve': solve,
            'simplify': simplify,
            'expand': expand,
            'factor': factor,
            'diff': diff,
            'integrate': integrate,
            'limit': limit,
            'sqrt': sqrt,
            'Rational': Rational,
            'pi': pi,
            'E': E,
            'sin': sin,
            'cos': cos,
            'tan': tan,
            'log': log,
            'exp': exp,
            'oo': oo,
            'parse_expr': parse_expr,
            'sympify': sympify,
            'parse_expression': parse_expression,
            'standard_transformations': standard_transformations,
            'implicit_multiplication_application': implicit_multiplication_application,
            'convert_xor': convert_xor,
        }
        _sympy_available = True
        logger.info("SymPy loaded successfully")
        return True
    except ImportError as e:
        logger.warning(f"SymPy not available: {e}")
        return False


class MathProblemType(str, Enum):
    """Matematik problem tipleri."""
    ALGEBRA = "algebra"
    GEOMETRY = "geometry"
    CALCULUS = "calculus"
    TRIGONOMETRY = "trigonometry"
    STATISTICS = "statistics"
    UNKNOWN = "unknown"


@dataclass
class VerificationResult:
    """Doğrulama sonucu."""
    is_correct: bool
    confidence: float  # 0.0 - 1.0
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    sympy_result: Any = None
    error: str | None = None


class MathVerificationService:
    """
    SymPy tabanlı matematik doğrulama servisi.

    Kullanım:
        svc = MathVerificationService()
        result = await svc.verify_algebra("x^2 + 5x + 6 = 0", "x = -2, x = -3")
        print(f"Doğru mu: {result.is_correct}")
    """

    def __init__(self):
        """Servisi başlat."""
        self._sympy_loaded = _load_sympy()
        if not self._sympy_loaded:
            logger.warning("MathVerificationService: SymPy yüklenemedi, LLM-based fallback kullanılacak")

    @property
    def sympy_available(self) -> bool:
        """SymPy kullanılabilir mi?"""
        return self._sympy_loaded

    def detect_problem_type(self, problem: str) -> MathProblemType:
        """
        Problem metninden matematik tipini tespit et.

        Args:
            problem: Problem metni (Türkçe)

        Returns:
            MathProblemType enum değeri
        """
        problem_lower = problem.lower()

        # Calculus keywords (Türkçe)
        calculus_keywords = [
            'türev', 'integral', 'limit', 'diferansiyel',
            'derivative', 'differentiate', 'd/dx', '∫',
            'belirsiz integral', 'belirli integral',
        ]
        if any(kw in problem_lower for kw in calculus_keywords):
            return MathProblemType.CALCULUS

        # Geometry keywords
        geometry_keywords = [
            'üçgen', 'kare', 'dikdörtgen', 'çember', 'daire',
            'alan', 'çevre', 'hacim', 'açı', 'kenar',
            'pisagor', 'öklid', 'geometri', 'koordinat',
            'triangle', 'square', 'rectangle', 'circle',
        ]
        if any(kw in problem_lower for kw in geometry_keywords):
            return MathProblemType.GEOMETRY

        # Trigonometry keywords
        trig_keywords = [
            'sin', 'cos', 'tan', 'cot', 'sec', 'csc',
            'sinüs', 'kosinüs', 'tanjant', 'kotanjant',
            'trigonometri', 'radyan', 'derece',
        ]
        if any(kw in problem_lower for kw in trig_keywords):
            return MathProblemType.TRIGONOMETRY

        # Statistics keywords
        stats_keywords = [
            'ortalama', 'medyan', 'mod', 'standart sapma',
            'varyans', 'olasılık', 'kombinasyon', 'permütasyon',
            'mean', 'median', 'mode', 'probability',
        ]
        if any(kw in problem_lower for kw in stats_keywords):
            return MathProblemType.STATISTICS

        # Algebra keywords (default for equations)
        algebra_keywords = [
            'denklem', 'polinom', 'faktör', 'çarpan',
            'kök', 'çözüm', 'eşitsizlik', 'fonksiyon',
            'equation', 'solve', 'factor', 'polynomial',
            '=', 'x', 'y', 'bilinmeyen',
        ]
        if any(kw in problem_lower for kw in algebra_keywords):
            return MathProblemType.ALGEBRA

        return MathProblemType.UNKNOWN

    def _parse_expression(self, expr_str: str) -> Any:
        """
        String ifadeyi SymPy expression'a çevir.

        Türkçe matematik notasyonunu destekler:
        - ^ yerine ** (üs)
        - x2 yerine x**2
        """
        if not self._sympy_loaded:
            return None

        # Normalize expression
        expr_str = expr_str.strip()

        # Turkish to standard conversions
        expr_str = expr_str.replace('^', '**')
        expr_str = expr_str.replace('²', '**2')
        expr_str = expr_str.replace('³', '**3')
        expr_str = expr_str.replace('√', 'sqrt')
        expr_str = expr_str.replace('π', 'pi')

        # Handle implicit multiplication: 2x -> 2*x
        expr_str = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', expr_str)

        try:
            transformations = (
                _sympy_modules['standard_transformations'] +
                (_sympy_modules['implicit_multiplication_application'],
                 _sympy_modules['convert_xor'])
            )
            return _sympy_modules['parse_expression'](
                expr_str,
                transformations=transformations,
                local_dict={
                    'x': _sympy_modules['Symbol']('x'),
                    'y': _sympy_modules['Symbol']('y'),
                    'z': _sympy_modules['Symbol']('z'),
                    'a': _sympy_modules['Symbol']('a'),
                    'b': _sympy_modules['Symbol']('b'),
                    'c': _sympy_modules['Symbol']('c'),
                    'n': _sympy_modules['Symbol']('n'),
                    'pi': _sympy_modules['pi'],
                    'e': _sympy_modules['E'],
                }
            )
        except Exception as e:
            logger.warning(f"Expression parse failed: {expr_str} - {e}")
            return None

    def _extract_equation_parts(self, equation: str) -> tuple[str, str] | None:
        """
        Denklemden sol ve sağ tarafı ayır.

        "x^2 + 5x + 6 = 0" -> ("x^2 + 5x + 6", "0")
        """
        if '=' not in equation:
            return None

        parts = equation.split('=')
        if len(parts) != 2:
            return None

        return parts[0].strip(), parts[1].strip()

    def _extract_solutions(self, solution_str: str) -> list[str]:
        """
        Çözüm string'inden değerleri çıkar.

        "x = -2 veya x = -3" -> ["-2", "-3"]
        "x = 2, x = 3" -> ["2", "3"]
        "x = {-2, -3}" -> ["-2", "-3"]
        """
        solution_str = solution_str.strip()

        # Remove x = prefix variations
        solution_str = re.sub(r'x\s*=\s*', '', solution_str)

        # Split by common separators
        separators = [' veya ', ' veya', ' ya da ', ', ', '; ', ' ve ']
        for sep in separators:
            if sep in solution_str:
                return [s.strip() for s in solution_str.split(sep) if s.strip()]

        # Handle set notation {-2, -3}
        if '{' in solution_str and '}' in solution_str:
            inner = re.search(r'\{([^}]+)\}', solution_str)
            if inner:
                return [s.strip() for s in inner.group(1).split(',') if s.strip()]

        # Single solution
        return [solution_str] if solution_str else []

    async def verify_algebra(
        self,
        equation: str,
        proposed_solution: str,
    ) -> VerificationResult:
        """
        Cebir denklem çözümünü doğrula.

        Args:
            equation: Denklem string'i (örn: "x^2 + 5x + 6 = 0")
            proposed_solution: Önerilen çözüm (örn: "x = -2 veya x = -3")

        Returns:
            VerificationResult
        """
        if not self._sympy_loaded:
            return VerificationResult(
                is_correct=False,
                confidence=0.0,
                message="SymPy yüklü değil, doğrulama yapılamadı",
                error="sympy_not_available"
            )

        try:
            # Parse equation
            eq_parts = self._extract_equation_parts(equation)
            if not eq_parts:
                return VerificationResult(
                    is_correct=False,
                    confidence=0.3,
                    message="Denklem formatı tanınamadı",
                    error="invalid_equation_format"
                )

            left_str, right_str = eq_parts
            left_expr = self._parse_expression(left_str)
            right_expr = self._parse_expression(right_str)

            if left_expr is None or right_expr is None:
                return VerificationResult(
                    is_correct=False,
                    confidence=0.2,
                    message="Denklem ifadesi parse edilemedi",
                    error="parse_error"
                )

            # Create equation and solve
            x = _sympy_modules['Symbol']('x')
            eq = _sympy_modules['Eq'](left_expr, right_expr)
            sympy_solutions = _sympy_modules['solve'](eq, x)

            # Extract proposed solutions
            proposed_values = self._extract_solutions(proposed_solution)

            if not proposed_values:
                return VerificationResult(
                    is_correct=False,
                    confidence=0.3,
                    message="Çözüm değerleri ayıklanamadı",
                    error="no_solutions_extracted"
                )

            # Parse proposed solutions to SymPy
            proposed_sympy = []
            for val in proposed_values:
                parsed = self._parse_expression(val)
                if parsed is not None:
                    proposed_sympy.append(_sympy_modules['simplify'](parsed))

            # Simplify SymPy solutions for comparison
            sympy_simplified = [_sympy_modules['simplify'](s) for s in sympy_solutions]

            # Compare solutions
            if not sympy_simplified:
                return VerificationResult(
                    is_correct=False,
                    confidence=0.5,
                    message="Denklemin çözümü yok",
                    details={"sympy_solutions": [], "proposed": proposed_values}
                )

            # Check if proposed solutions match
            correct_count = 0
            for proposed in proposed_sympy:
                for correct in sympy_simplified:
                    if _sympy_modules['simplify'](proposed - correct) == 0:
                        correct_count += 1
                        break

            # Calculate accuracy
            total_correct = len(sympy_simplified)
            is_fully_correct = (
                correct_count == total_correct and
                len(proposed_sympy) == total_correct
            )

            confidence = correct_count / max(total_correct, len(proposed_sympy))

            return VerificationResult(
                is_correct=is_fully_correct,
                confidence=confidence,
                message=(
                    "Çözüm doğru!" if is_fully_correct
                    else f"Doğru: {correct_count}/{total_correct}"
                ),
                details={
                    "sympy_solutions": [str(s) for s in sympy_simplified],
                    "proposed_solutions": proposed_values,
                    "correct_count": correct_count,
                    "total_solutions": total_correct,
                },
                sympy_result=sympy_solutions
            )

        except Exception as e:
            logger.error(f"Algebra verification error: {e}")
            return VerificationResult(
                is_correct=False,
                confidence=0.0,
                message=f"Doğrulama hatası: {str(e)}",
                error=str(e)
            )

    async def verify_calculus(
        self,
        expression: str,
        result: str,
        operation: str,  # "derivative", "integral", "limit"
        variable: str = "x",
        **kwargs,  # limit_point for limits
    ) -> VerificationResult:
        """
        Calculus işlemini doğrula.

        Args:
            expression: Orijinal ifade (örn: "x^2 + 3x")
            result: Önerilen sonuç (örn: "2x + 3")
            operation: İşlem tipi ("derivative", "integral", "limit")
            variable: Değişken (default: "x")
            **kwargs: limit_point (limit için)

        Returns:
            VerificationResult
        """
        if not self._sympy_loaded:
            return VerificationResult(
                is_correct=False,
                confidence=0.0,
                message="SymPy yüklü değil",
                error="sympy_not_available"
            )

        try:
            expr = self._parse_expression(expression)
            proposed = self._parse_expression(result)
            var = _sympy_modules['Symbol'](variable)

            if expr is None or proposed is None:
                return VerificationResult(
                    is_correct=False,
                    confidence=0.2,
                    message="İfade parse edilemedi",
                    error="parse_error"
                )

            # Calculate correct result based on operation
            if operation.lower() in ["derivative", "türev", "diff"]:
                correct = _sympy_modules['diff'](expr, var)
            elif operation.lower() in ["integral", "integrate"]:
                correct = _sympy_modules['integrate'](expr, var)
            elif operation.lower() in ["limit"]:
                limit_point = kwargs.get('limit_point', 0)
                if isinstance(limit_point, str):
                    if limit_point in ['oo', 'inf', 'infinity', 'sonsuz']:
                        limit_point = _sympy_modules['oo']
                    elif limit_point in ['-oo', '-inf', '-infinity', '-sonsuz']:
                        limit_point = -_sympy_modules['oo']
                    else:
                        limit_point = self._parse_expression(limit_point)
                correct = _sympy_modules['limit'](expr, var, limit_point)
            else:
                return VerificationResult(
                    is_correct=False,
                    confidence=0.0,
                    message=f"Bilinmeyen işlem: {operation}",
                    error="unknown_operation"
                )

            # Compare results (simplify both)
            correct_simplified = _sympy_modules['simplify'](correct)
            proposed_simplified = _sympy_modules['simplify'](proposed)

            # Check equality
            diff = _sympy_modules['simplify'](correct_simplified - proposed_simplified)
            is_correct = diff == 0

            # For integrals, check if difference is a constant (C)
            if not is_correct and operation.lower() in ["integral", "integrate"]:
                diff_derivative = _sympy_modules['diff'](diff, var)
                is_correct = _sympy_modules['simplify'](diff_derivative) == 0

            return VerificationResult(
                is_correct=is_correct,
                confidence=1.0 if is_correct else 0.0,
                message="Sonuç doğru!" if is_correct else "Sonuç yanlış",
                details={
                    "operation": operation,
                    "correct_result": str(correct_simplified),
                    "proposed_result": str(proposed_simplified),
                    "difference": str(diff),
                },
                sympy_result=correct
            )

        except Exception as e:
            logger.error(f"Calculus verification error: {e}")
            return VerificationResult(
                is_correct=False,
                confidence=0.0,
                message=f"Doğrulama hatası: {str(e)}",
                error=str(e)
            )

    async def verify_geometry(
        self,
        problem: str,
        construction_steps: list[str],
        final_result: str,
    ) -> VerificationResult:
        """
        Geometri problemini doğrula.

        Note: Geometri doğrulaması sınırlıdır, sadece sayısal
        hesaplamaları kontrol edebilir (alan, çevre, vb.)

        Args:
            problem: Problem açıklaması
            construction_steps: İnşa adımları
            final_result: Final sayısal sonuç

        Returns:
            VerificationResult
        """
        if not self._sympy_loaded:
            return VerificationResult(
                is_correct=False,
                confidence=0.0,
                message="SymPy yüklü değil",
                error="sympy_not_available"
            )

        try:
            # Extract numerical calculations from steps
            # This is a simplified verification - check if final numeric result is consistent

            # Try to parse final result
            result_expr = self._parse_expression(final_result)
            if result_expr is None:
                return VerificationResult(
                    is_correct=False,
                    confidence=0.3,
                    message="Sonuç parse edilemedi",
                    error="parse_error"
                )

            # Simplify the result
            simplified = _sympy_modules['simplify'](result_expr)

            # Check if result is a valid positive number (for area, perimeter, etc.)
            try:
                numeric_value = float(simplified.evalf())
                is_positive = numeric_value > 0
            except (ValueError, TypeError):
                is_positive = True  # Cannot evaluate, assume valid

            if not is_positive:
                return VerificationResult(
                    is_correct=False,
                    confidence=0.7,
                    message="Geometrik değer negatif olamaz",
                    details={"result": str(simplified)},
                    error="negative_geometric_value"
                )

            # Basic validation passed
            return VerificationResult(
                is_correct=True,
                confidence=0.6,  # Lower confidence for geometry
                message="Geometrik sonuç formatı doğru (tam doğrulama sınırlı)",
                details={
                    "result": str(simplified),
                    "construction_steps": construction_steps,
                    "note": "Tam geometri doğrulaması için görsel/manuel kontrol gerekir"
                },
                sympy_result=simplified
            )

        except Exception as e:
            logger.error(f"Geometry verification error: {e}")
            return VerificationResult(
                is_correct=False,
                confidence=0.0,
                message=f"Doğrulama hatası: {str(e)}",
                error=str(e)
            )

    async def verify(
        self,
        problem: str,
        solution: str,
        problem_type: MathProblemType | None = None,
        **kwargs,
    ) -> VerificationResult:
        """
        Genel doğrulama metodu - problem tipine göre yönlendirir.

        Args:
            problem: Problem ifadesi
            solution: Önerilen çözüm
            problem_type: Problem tipi (None ise otomatik tespit)
            **kwargs: Ek parametreler (operation, limit_point, vb.)

        Returns:
            VerificationResult
        """
        # Auto-detect problem type if not provided
        if problem_type is None:
            problem_type = self.detect_problem_type(problem)

        if problem_type == MathProblemType.ALGEBRA:
            return await self.verify_algebra(problem, solution)

        elif problem_type == MathProblemType.CALCULUS:
            operation = kwargs.get('operation', 'derivative')
            return await self.verify_calculus(
                problem, solution, operation,
                limit_point=kwargs.get('limit_point')
            )

        elif problem_type == MathProblemType.GEOMETRY:
            steps = kwargs.get('construction_steps', [])
            return await self.verify_geometry(problem, steps, solution)

        elif problem_type == MathProblemType.TRIGONOMETRY:
            # Trigonometry uses algebra verification
            return await self.verify_algebra(problem, solution)

        else:
            return VerificationResult(
                is_correct=False,
                confidence=0.0,
                message=f"Desteklenmeyen problem tipi: {problem_type}",
                error="unsupported_problem_type"
            )


# Singleton instance
_math_verification_service: MathVerificationService | None = None

def get_math_verification_service() -> MathVerificationService:
    """Get singleton MathVerificationService instance."""
    global _math_verification_service
    if _math_verification_service is None:
        _math_verification_service = MathVerificationService()
    return _math_verification_service
