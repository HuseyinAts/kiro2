"""
Empty Exception Handler Detector - Detects empty exception handlers.

Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6
"""

from __future__ import annotations

import sys

from ..analyzers.ast_analyzer import ASTAnalyzer
from ..analyzers.context_analyzer import ContextAnalyzer
from ..base_detector import BaseDetector
from ..config.patterns import REWARD_HACKING_PATTERNS
from ..exceptions import ASTParseError
from ..literal_spans import satir_bastirilmali
from ..models.detection_result import DetectionResult
from ..models.enums import PatternType, SeverityLevel


class EmptyExceptionDetector(BaseDetector):
    """
    Detects empty exception handlers.

    Patterns detected:
    - except: pass
    - except Exception: pass
    - bare except: without specific exception
    - Silent exception swallowing
    """

    name = "EmptyExceptionDetector"
    pattern_type = PatternType.EMPTY_EXCEPTION
    default_severity = SeverityLevel.CRITICAL

    def get_patterns(self) -> list[str]:
        """Get regex patterns for empty exception detection."""
        return REWARD_HACKING_PATTERNS.get("empty_exception", [])

    async def detect(self, file_path: str, content: str) -> list[DetectionResult]:
        """
        Detect empty exception handler patterns.

        Args:
            file_path: Path to file being analyzed
            content: File content

        Returns:
            List of DetectionResult objects
        """
        if not self.is_enabled():
            return []

        results: list[DetectionResult] = []

        # Initialize context analyzer
        context_analyzer = ContextAnalyzer(content, file_path)

        # 1. Regex-based detection
        regex_results = self._regex_detect(
            file_path=file_path,
            content=content,
            message_template="Empty exception handler detected: {pattern}",
        )

        for result in regex_results:
            if context_analyzer.should_ignore(result.line_number, "empty_exception"):
                continue

            # Check if exception is being logged or documented
            if self._has_logging_or_comment(content, result.line_number):
                # NOT: enum atanir (alan `SeverityLevel` tipinde, mypy oyle
                # ister) ama `use_enum_values=True` yuzunden _create_result
                # yolu duz string sakliyor. Yani severity'nin RUNTIME tipi
                # yola gore degisir ve `str()` biri icin "INFO", digeri icin
                # "SeverityLevel.INFO" uretir. Karsilastiran her kod bunu
                # normalize ETMEK ZORUNDA — test dosyasindaki `_sev()` bunu
                # yapiyor; ilk surumde yapmadigi icin bir iddia sessizce
                # gecmisti (#449).
                result.severity = SeverityLevel.INFO
                result.message = "Exception handler with logging/comment"

            modifier = context_analyzer.get_confidence_modifier(result.line_number)
            result.confidence *= modifier

            if result.confidence >= self.config.min_confidence:
                results.append(result)

        # 2. AST-based detection for Python files
        if file_path.endswith(".py"):
            ast_results = await self._ast_detect(file_path, content, context_analyzer)
            results.extend(ast_results)

        # 3. Detect bare except (without specific exception type)
        bare_except_results = self._detect_bare_except(file_path, content)
        results.extend(bare_except_results)

        return self._deduplicate(results)

    async def _ast_detect(
        self, file_path: str, content: str, context_analyzer: ContextAnalyzer
    ) -> list[DetectionResult]:
        """
        Perform AST-based detection for empty exception handlers.

        Args:
            file_path: Path to file
            content: File content
            context_analyzer: Context analyzer instance

        Returns:
            List of DetectionResult objects
        """
        results: list[DetectionResult] = []

        try:
            ast_analyzer = ASTAnalyzer(content, file_path)
            ast_analyzer.parse()

            for match in ast_analyzer.find_empty_except_handlers():
                if context_analyzer.should_ignore(match.line_number, "empty_exception"):
                    continue

                confidence = (
                    match.confidence
                    * context_analyzer.get_confidence_modifier(match.line_number)
                )

                if confidence >= self.config.min_confidence:
                    results.append(
                        self._create_result(
                            file_path=file_path,
                            line_number=match.line_number,
                            code_snippet=match.code,
                            message=f"AST analysis: {match.message}",
                            confidence=confidence,
                            column_number=match.column,
                        )
                    )

        except ASTParseError as hata:
            # 30 Tem 2026 (bandit B110): bekcinin KENDISI sessizce yutuyordu.
            # Parse hatasi normaldir (kismi/bozuk dosya) ama GORUNMEZ olmamali:
            # AST yolu duserse tespit sessizce zayiflar ve kimse fark etmez.
            print(
                f"Warning: {self.name} AST parse edemedi {file_path}: {hata}",
                file=sys.stderr,
            )
        except Exception as hata:
            print(
                f"Warning: {self.name} AST analizi basarisiz {file_path}: {hata}",
                file=sys.stderr,
            )

        return results

    def _has_logging_or_comment(self, content: str, line_number: int) -> bool:
        """
        Check if exception handler has logging or explanatory comment.

        Args:
            content: File content
            line_number: Line number of except clause

        Tarama HANDLER GOVDESIYLE SINIRLIDIR — eskiden `except` satirindan
        sonraki UC SATIRA bakiyordu ve blok sinirini gormuyordu. Sonuc: `try`
        blogu bittikten SONRAKI alakasiz bir `log.info()` bile "bu handler
        logluyor" sayiliyor, gercek bir `except: pass` yutmasi INFO'ya
        indirilip GORUNMEZ oluyordu. Olculdu (30 Tem 2026, #449):

            def f():
                try:
                    g()
                except:
                    pass
                log.info("devam")     # <- handler'in DISINDA
            -> tek bulgu, severity INFO

        Yakinlik sezgisi kapsam bilgisinin yerini tutmuyor. Artik govde,
        `except` satirindan DAHA GIRINTILI satirlarla sinirli; ilk dedent'te
        tarama biter.

        Sozlesme: tests/hooks/reward_hacking/test_bare_except_policy.py

        Returns:
            True if logging or comment present
        """
        lines = content.split("\n")
        if not 1 <= line_number <= len(lines):
            return False

        except_satiri = lines[line_number - 1]
        govde_girintisi = len(except_satiri) - len(except_satiri.lstrip())

        logging_patterns = [
            "logger.",
            "logging.",
            "log.",
            "print(",
            "# intentionally",
            "# silently",
            "# expected",
            "# ignore",
            "# suppress",
        ]

        for satir in lines[line_number:]:
            if not satir.strip():
                continue
            if len(satir) - len(satir.lstrip()) <= govde_girintisi:
                break  # dedent -> handler govdesi bitti
            if any(desen in satir.lower() for desen in logging_patterns):
                return True

        return False

    def _detect_bare_except(
        self, file_path: str, content: str
    ) -> list[DetectionResult]:
        """
        Detect bare except: clauses without specific exception type.

        Args:
            file_path: Path to file
            content: File content

        Returns:
            List of DetectionResult for bare excepts
        """
        import re

        results: list[DetectionResult] = []

        # Pattern for bare except (not followed by Exception type)
        pattern = r"^\s*except\s*:\s*$"

        lines = content.split("\n")
        for i, line in enumerate(lines):
            if re.match(pattern, line):
                # Fixture string'i icindeki bare except TEST VERISIDIR (30 Tem 2026).
                if satir_bastirilmali(file_path, content, i + 1, pattern):
                    continue

                # #449: bare except LOGLANMIS ise CRITICAL olamaz. Eskiden bu
                # yol log kontrolu HIC yapmiyordu, dolayisiyla
                # `except: log.warning(...)` ile `except: pass` AYNI sinifa
                # dusuyordu — dosyanin kendi `_has_logging_or_comment`
                # niyetiyle celisiyordu. Ama INFO'ya da indirilmez: bare
                # `except:` loglansa bile KeyboardInterrupt/SystemExit
                # yakalar, yani gerçek ama daha hafif bir kusurdur -> WARNING.
                loglu = self._has_logging_or_comment(content, i + 1)
                sonuc = self._create_result(
                    file_path=file_path,
                    line_number=i + 1,
                    code_snippet=line.strip(),
                    message=(
                        "Bare except: (loglanmis) - yine de "
                        "KeyboardInterrupt/SystemExit yakaliyor"
                        if loglu
                        else "Bare except: - use specific exception type"
                    ),
                    confidence=0.95,
                )
                if loglu:
                    sonuc.severity = SeverityLevel.WARNING
                results.append(sonuc)

        return results

    def _deduplicate(self, results: list[DetectionResult]) -> list[DetectionResult]:
        """Remove duplicate detections on the same line."""
        seen_lines: set = set()
        unique_results: list[DetectionResult] = []

        for result in results:
            key = (result.file_path, result.line_number)
            if key not in seen_lines:
                seen_lines.add(key)
                unique_results.append(result)

        return unique_results
