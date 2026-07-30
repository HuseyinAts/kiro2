"""
Base Detector abstract class for Reward Hacking Prevention.

All detectors inherit from this class and implement the detect() method.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod

from .config.patterns import REMEDIATION_SUGGESTIONS
from .literal_spans import bulgu_bastirilmali
from .models.detection_result import DetectionResult, DetectorConfig
from .models.enums import PatternType, SeverityLevel

# Bu eşiğin ALTINDAKİ bulgular tavsiyedir (WARNING), commit/push'u bloklamaz.
# Değer ÖLÇÜLDÜ, seçilmedi — dedektörlerdeki fiili confidence dağılımı:
#   0.95x3 · 0.90 · 0.85 · 0.80x2 · 0.75 · 0.70  -> gerçek tespitler (bloklamalı)
#   0.60 · 0.50                                   -> "Consider ..." tavsiyeleri
# Yeni bir kural eklerken: bloklaması gereken bir tespite 0.7'nin ALTINDA değer
# verirsen sessizce etkisiz kalır. Ölçümü tazele:
#   grep -rn 'confidence=' backend/hooks/reward_hacking/detectors/
ADVISORY_CONFIDENCE_THRESHOLD = 0.7


class BaseDetector(ABC):
    """
    Abstract base class for reward hacking pattern detectors.

    All detectors must implement:
    - detect(): Main detection method
    - get_patterns(): Returns regex patterns for this detector
    - pattern_type: Class attribute for pattern type
    - default_severity: Class attribute for default severity
    """

    # Subclasses must define these
    pattern_type: PatternType
    default_severity: SeverityLevel = SeverityLevel.CRITICAL
    name: str = "BaseDetector"

    def __init__(self, config: DetectorConfig | None = None):
        """
        Initialize detector with optional configuration.

        Args:
            config: Optional detector configuration. If not provided,
                   default configuration will be used.
        """
        self.config = config or DetectorConfig()
        self._compiled_patterns: list[re.Pattern] = []
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex patterns for efficient matching."""
        all_patterns = self.get_patterns()
        if self.config.patterns:
            all_patterns.extend(self.config.patterns)

        self._compiled_patterns = []
        for pattern in all_patterns:
            try:
                self._compiled_patterns.append(
                    re.compile(pattern, re.MULTILINE | re.IGNORECASE)
                )
            except re.error:
                # Skip invalid patterns
                continue

    @abstractmethod
    def get_patterns(self) -> list[str]:
        """
        Get regex patterns for this detector.

        Returns:
            List of regex pattern strings
        """

    @abstractmethod
    async def detect(self, file_path: str, content: str) -> list[DetectionResult]:
        """
        Detect reward hacking patterns in file content.

        Args:
            file_path: Path to the file being analyzed
            content: File content as string

        Returns:
            List of DetectionResult objects for each detection
        """

    def _is_in_exception(self, line: str, line_num: int, content: str) -> bool:
        """
        Check if match is a legitimate exception (false positive reduction).

        Args:
            line: The line containing the match
            line_num: Line number in the file
            content: Full file content

        Returns:
            True if this is a legitimate use (should be ignored)
        """
        # UYARI (30 Tem 2026, #451): asagidaki iki dal KABA ve bilinen hatalari
        # var, ama TEMIZLIK DIYE KALDIRMAYIN. Ikisi de olculdu:
        #
        # 1) Yorum dali — tek basina yorum satirindaki bulgulari atiyor
        #    (`# pragma: no cover`, `# noqa`, `# TODO: implement` kor kaliyor;
        #    satir-sonu bicimleri yakalaniyor). Bu bir HOLE, ama kaldirmanin
        #    250 gercek dosyada kazanci: +0 bulgu (845 -> 845). Yani pratik
        #    etkisi SIFIR; risk almaya deger bir kazanc yok.
        #
        # 2) Docstring dali — sayac hatali: `if '"""' in satir` satirdaki
        #    ADEDE bakmaz, bir kez donderir. Tek satirlik docstring'den sonra
        #    durum "icindeyim"de takilip kalabilir. Buna ragmen KALDIRILAMAZ:
        #    olculdu, kaldirinca 250 dosyada +232 bulgu / 231'i CRITICAL ve
        #    ornekler GERCEK kod satirlari — `except Exception:`, `MagicMock()`,
        #    `@patch(...)`, `AsyncMock(return_value=None)`, `email="test@..."`.
        #    Bunlar siradan test deyimleri. Bloklamaya baslamak mock kullanan
        #    her test dosyasini push edilemez yapar ve `--no-verify`'i
        #    aliskanliga cevirir (bkz .pre-commit-config.yaml'daki ayni uyari).
        #
        # Yani bu dal HATALI OLDUGU HALDE YUK TASIYOR: bekciyi kullanilabilir
        # tutan sey o. Gercek is bu dali silmek degil, desen kumesinin
        # confidence/severity kalibrasyonunu duzeltmek (mock/hardcoded-data
        # kurallari CRITICAL olmamali). O ayri gorev.
        #
        # Yasayan isaretci: test_string_literal_immunity.py icindeki
        # xfail(strict=True) testi — davranis degisirse kirmiziya doner.
        #
        # NOT: string literalleri artik BURADA degil literal_spans.py'de,
        # karakter-dogru ve desen-bazli olarak ele aliniyor.

        # Skip comments
        stripped = line.strip()
        if stripped.startswith("#") and "assert" not in stripped.lower():
            return True

        # Skip docstrings
        lines = content.split("\n")
        in_docstring = False
        for i, satir in enumerate(lines):
            if '"""' in satir or "'''" in satir:
                in_docstring = not in_docstring
            if i == line_num - 1 and in_docstring:
                return True

        return False

    def _get_remediation(self) -> str:
        """Get remediation suggestion for this pattern type."""
        return REMEDIATION_SUGGESTIONS.get(
            self.pattern_type.value, "Review and fix the detected pattern."
        )

    def _create_result(
        self,
        file_path: str,
        line_number: int,
        code_snippet: str,
        message: str,
        confidence: float = 0.95,
        column_number: int | None = None,
    ) -> DetectionResult:
        """
        Create a DetectionResult object.

        Args:
            file_path: Path to file with issue
            line_number: Line number of issue
            code_snippet: Code snippet showing the issue
            message: Human-readable message
            confidence: Detection confidence (0.0-1.0)
            column_number: Optional column number

        Returns:
            DetectionResult object
        """
        severity = self.config.severity if self.config else self.default_severity

        # Düşük güvenli bulgu TAVSİYEDİR, ihlal değil — commit/push'u bloklayamaz.
        # 29 Tem 2026: "Consider Hypothesis for property-based testing" (confidence=0.5)
        # CRITICAL sayılıp push'u durdurdu. `confidence` sonuca yazılıyordu ama severity'ye
        # hiç etki etmiyordu, dolayısıyla 0.5'lik tavsiye 0.95'lik `assert True` ile aynı
        # sınıfa düşüyordu. Eşik ÖLÇÜLDÜ, seçilmedi: dedektörlerdeki dağılım
        # 0.95x3/0.90/0.85/0.80x2/0.75/0.70 (gerçek tespitler) vs 0.60/0.50 (iki tavsiye).
        # Sözleşme + körleşme bekçisi: tests/hooks/reward_hacking/test_severity_from_confidence.py
        if confidence < ADVISORY_CONFIDENCE_THRESHOLD:
            severity = SeverityLevel.WARNING

        return DetectionResult(
            detector_name=self.name,
            pattern_type=self.pattern_type,
            severity=severity,
            file_path=file_path,
            line_number=line_number,
            column_number=column_number,
            code_snippet=code_snippet.strip(),
            message=message,
            remediation=self._get_remediation(),
            confidence=confidence,
        )

    def _regex_detect(
        self, file_path: str, content: str, message_template: str
    ) -> list[DetectionResult]:
        """
        Perform regex-based detection using compiled patterns.

        Args:
            file_path: Path to file being analyzed
            content: File content
            message_template: Message template with {pattern} placeholder

        Returns:
            List of DetectionResult objects
        """
        results: list[DetectionResult] = []

        for pattern in self._compiled_patterns:
            for match in pattern.finditer(content):
                # String literali TEST VERISIDIR, kod degil (30 Tem 2026).
                # Bekci kendi fixture korpusunu ihlal sayip 3 test dosyasini
                # push'ta blokluyordu. Karakter granulerligi ZORUNLU:
                # `assert True, "aciklama"` gercek ihlaldir ve satirinda
                # string de vardir. Bkz literal_spans.py
                if bulgu_bastirilmali(
                    file_path, content, match.start(), pattern.pattern
                ):
                    continue

                # Calculate line number
                line_num = content[: match.start()].count("\n") + 1

                # Get the line content
                lines = content.split("\n")
                if line_num <= len(lines):
                    line_content = lines[line_num - 1]
                else:
                    line_content = match.group(0)

                # Check for false positives
                if self._is_in_exception(line_content, line_num, content):
                    continue

                # Skip if below confidence threshold
                if self.config.min_confidence > 0.9:
                    continue

                results.append(
                    self._create_result(
                        file_path=file_path,
                        line_number=line_num,
                        code_snippet=line_content,
                        message=message_template.format(pattern=pattern.pattern),
                        confidence=0.95,
                        column_number=match.start()
                        - content.rfind("\n", 0, match.start())
                        - 1,
                    )
                )

        return results

    def is_enabled(self) -> bool:
        """Check if detector is enabled."""
        return self.config.enabled if self.config else True

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(pattern_type={self.pattern_type}, enabled={self.is_enabled()})>"
