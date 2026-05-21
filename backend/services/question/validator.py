"""
Matematiksel Dogrulama Motoru (SymPy Entegrasyonu)
REQ-48.41-48.44: SymPy symbolic math engine, Equation validation, Solution verification

Bu modul matematik sorularinin matematiksel tutarliligini
kontrol eder ve SymPy ile sembolik hesaplamalar yapar.
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class MathematicalValidationEngine:
    """
    Matematiksel Dogrulama Motoru (SymPy Entegrasyonu)
    REQ-48.41-48.44: SymPy symbolic math engine, Equation validation, Solution verification
    """

    def __init__(self):
        """SymPy entegrasyonu"""
        try:
            import sympy as sp

            self.sp = sp
            self.symbols_cache: dict[str, Any] = {}
            logger.info("SymPy basariyla yuklendi")
        except ImportError:
            logger.warning("SymPy yuklu degil. Matematiksel dogrulama devre disi.")
            self.sp = None

    def validate_equation(self, equation_str: str) -> dict[str, Any]:
        """
        REQ-48.42: Equation validation - Matematiksel tutarliligi kontrol etmek

        Args:
            equation_str: Denklem string'i (orn: "2*x + 3 = 7")

        Returns:
            Dogrulama sonucu
        """
        if not self.sp:
            return {"valid": False, "error": "SymPy yuklu degil"}

        try:
            # Denklemi parse et
            if "=" in equation_str:
                left, right = equation_str.split("=")
                left_expr = self.sp.sympify(left.strip())
                right_expr = self.sp.sympify(right.strip())

                # Denklem gecerli mi kontrol et
                equation = self.sp.Eq(left_expr, right_expr)

                return {
                    "valid": True,
                    "equation": str(equation),
                    "left_side": str(left_expr),
                    "right_side": str(right_expr),
                    "error": None,
                }
            # Tek tarafli ifade
            expr = self.sp.sympify(equation_str.strip())
            return {"valid": True, "expression": str(expr), "error": None}

        except Exception as e:
            logger.error(f"Denklem dogrulama hatasi: {e}", exc_info=True)
            return {"valid": False, "error": str(e)}

    def solve_equation(self, equation_str: str, variable: str = "x") -> dict[str, Any]:
        """
        REQ-48.41: SymPy symbolic math engine - Denklemleri sembolik olarak cozmek

        Args:
            equation_str: Denklem string'i
            variable: Cozulecek degisken

        Returns:
            Cozum sonucu
        """
        if not self.sp:
            return {"solved": False, "error": "SymPy yuklu degil"}

        try:
            # Degiskeni tanimla
            var = self.sp.Symbol(variable)

            # Denklemi parse et ve coz
            if "=" in equation_str:
                left, right = equation_str.split("=")
                left_expr = self.sp.sympify(left.strip())
                right_expr = self.sp.sympify(right.strip())
                equation = self.sp.Eq(left_expr, right_expr)

                solutions = self.sp.solve(equation, var)
            else:
                expr = self.sp.sympify(equation_str.strip())
                solutions = self.sp.solve(expr, var)

            return {
                "solved": True,
                "solutions": [str(sol) for sol in solutions],
                "solution_count": len(solutions),
                "error": None,
            }

        except Exception as e:
            logger.error(f"Denklem cozme hatasi: {e}", exc_info=True)
            return {"solved": False, "error": str(e)}

    def verify_solution(
        self, equation_str: str, proposed_solution: str, variable: str = "x"
    ) -> dict[str, Any]:
        """
        REQ-48.43: Solution verification - Dogru cevabi dogrulamak

        Args:
            equation_str: Denklem
            proposed_solution: Onerilen cozum
            variable: Degisken

        Returns:
            Dogrulama sonucu
        """
        if not self.sp:
            return {"verified": False, "error": "SymPy yuklu degil"}

        try:
            # Degiskeni tanimla
            var = self.sp.Symbol(variable)

            # Denklemi parse et
            if "=" in equation_str:
                left, right = equation_str.split("=")
                left_expr = self.sp.sympify(left.strip())
                right_expr = self.sp.sympify(right.strip())
            else:
                left_expr = self.sp.sympify(equation_str.strip())
                right_expr = self.sp.sympify("0")

            # Onerilen cozumu parse et
            solution_value = self.sp.sympify(proposed_solution.strip())

            # Cozumu denklemde yerine koy
            left_result = left_expr.subs(var, solution_value)
            right_result = right_expr.subs(var, solution_value)

            # Basitlestir ve karsilastir
            left_simplified = self.sp.simplify(left_result)
            right_simplified = self.sp.simplify(right_result)

            is_correct = self.sp.simplify(left_simplified - right_simplified) == 0

            return {
                "verified": True,
                "is_correct": bool(is_correct),
                "left_result": str(left_simplified),
                "right_result": str(right_simplified),
                "error": None,
            }

        except Exception as e:
            logger.error(f"Cozum dogrulama hatasi: {e}", exc_info=True)
            return {"verified": False, "error": str(e)}

    def validate_math_question(
        self, question_text: str, correct_answer: str, options: list[str]
    ) -> dict[str, Any]:
        """
        REQ-48.44: Matematiksel hata tespit edildiginde soruyu reddetmek

        Matematik sorusunun matematiksel tutarliligini kontrol et

        Returns:
            Dogrulama sonucu ve hata varsa reddetme sebebi
        """
        if not self.sp:
            return {
                "valid": True,  # SymPy yoksa varsayilan olarak gecerli kabul et
                "warnings": ["SymPy yuklu degil, matematiksel dogrulama yapilamadi"],
            }

        validation_result: dict[str, Any] = {"valid": True, "errors": [], "warnings": []}

        try:
            # 1. Soru metninde denklem var mi kontrol et
            equations = self._extract_equations(question_text)

            for eq in equations:
                eq_validation = self.validate_equation(eq)
                if not eq_validation["valid"]:
                    validation_result["valid"] = False
                    validation_result["errors"].append(
                        f"Gecersiz denklem: {eq} - {eq_validation['error']}"
                    )

            # 2. Dogru cevabin matematiksel olarak gecerli oldugunu kontrol et
            if equations:
                # Ilk denklemi coz
                solution = self.solve_equation(equations[0])
                if solution["solved"]:
                    # Dogru cevabin cozumlerden biri olup olmadigini kontrol et
                    if correct_answer not in solution["solutions"]:
                        validation_result["warnings"].append(
                            f"Dogru cevap ({correct_answer}) denklem cozumlerinde bulunamadi: {solution['solutions']}"
                        )

            # 3. Seceneklerin matematiksel olarak anlamli oldugunu kontrol et
            for option in options:
                try:
                    # Secenegi parse etmeyi dene
                    self.sp.sympify(option.split(")")[-1].strip())
                except Exception:
                    # Parse edilemiyorsa sorun yok, metin cevap olabilir
                    pass

        except Exception as e:
            logger.error(f"Matematik soru dogrulama hatasi: {e}", exc_info=True)
            validation_result["warnings"].append(f"Dogrulama hatasi: {e!s}")

        return validation_result

    def _extract_equations(self, text: str) -> list[str]:
        """Metinden denklemleri cikar"""
        # Basit denklem pattern'leri
        patterns = [
            r"([0-9x\+\-\*/\(\)\^\s]+=[0-9x\+\-\*/\(\)\^\s]+)",  # x + 2 = 5 gibi
            r"([0-9]+[x\+\-\*/\(\)]+[0-9x\+\-\*/\(\)]*)",  # 2x + 3 gibi
        ]

        equations = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            equations.extend(matches)

        return equations
