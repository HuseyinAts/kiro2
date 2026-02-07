# Design Document - Reward Hacking Prevention Hooks Sistemi

## Overview

Reward Hacking Prevention Hooks sistemi, AI agent'ların sahte başarı göstermesini engelleyen pattern detection ve validation mekanizmasıdır. AST (Abstract Syntax Tree) analizi ve regex pattern matching ile `assert True`, `echo Success`, placeholder code gibi reward hacking pattern'lerini %100 tespit eder ve exit code 2 ile engeller.

**Temel Özellikler:**
- 8 farklı reward hacking detector (Assert True, Echo Success, Placeholder, Coverage Manipulation, Mock Abuse, Empty Exception, Hardcoded Test Data, CI/CD Bypass)
- AST + Regex hybrid detection
- Context-aware false positive reduction
- Exit code 2 ile blocking enforcement
- Remediation suggestion engine
- Pre-commit hook integration

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Developer Workflow                            │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │ Write    │───▶│ Commit   │───▶│ Push     │                  │
│  │ Code     │    │ Attempt  │    │ Success  │                  │
│  └──────────┘    └────┬─────┘    └──────────┘                  │
└────────────────────────┼──────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              PostToolUse Hook Trigger                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Hook Manager                                             │  │
│  │  - File type detection (*.py, *.sh, *.yml)               │  │
│  │  - Detector selection                                     │  │
│  │  - Parallel execution orchestration                       │  │
│  └────────────────────┬─────────────────────────────────────┘  │
└─────────────────────────┼──────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Pattern Detection Layer (Parallel)                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Assert   │  │ Echo     │  │ Place-   │  │ Coverage │       │
│  │ True     │  │ Success  │  │ holder   │  │ Manip    │       │
│  │ Detector │  │ Detector │  │ Detector │  │ Detector │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       │             │             │             │               │
│  ┌────┴─────┐  ┌────┴─────┐  ┌────┴─────┐  ┌────┴─────┐       │
│  │ Mock     │  │ Empty    │  │ Hardcoded│  │ CI/CD    │       │
│  │ Abuse    │  │ Exception│  │ Test Data│  │ Bypass   │       │
│  │ Detector │  │ Detector │  │ Detector │  │ Detector │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
└───────┼─────────────┼─────────────┼─────────────┼──────────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Result Aggregation & Decision                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Aggregator                                               │  │
│  │  - Collect all detector results                           │  │
│  │  - Severity classification (CRITICAL, WARNING, INFO)      │  │
│  │  - Exit code decision (0: Clean, 1: Warning, 2: Block)   │  │
│  │  - Remediation suggestion generation                      │  │
│  └────────────────────┬─────────────────────────────────────┘  │
└─────────────────────────┼──────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Developer Feedback                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  ❌ Reward Hacking Detected!                             │  │
│  │                                                           │  │
│  │  Pattern: Assert True                                    │  │
│  │  Location: tests/test_user.py:42                         │  │
│  │  Severity: CRITICAL                                      │  │
│  │                                                           │  │
│  │  Suggestion:                                             │  │
│  │  Replace `assert True` with meaningful assertion:        │  │
│  │  assert user.email == "test@example.com"                 │  │
│  │                                                           │  │
│  │  Exit Code: 2 (Commit Blocked)                           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Component Architecture

```
backend/
├── app/
│   ├── hooks/
│   │   ├── __init__.py
│   │   ├── reward_hacking/
│   │   │   ├── __init__.py
│   │   │   ├── hook_manager.py          # Hook orchestration
│   │   │   ├── detectors/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base_detector.py     # Abstract base class
│   │   │   │   ├── assert_true_detector.py
│   │   │   │   ├── echo_success_detector.py
│   │   │   │   ├── placeholder_detector.py
│   │   │   │   ├── coverage_manipulation_detector.py
│   │   │   │   ├── mock_abuse_detector.py
│   │   │   │   ├── empty_exception_detector.py
│   │   │   │   ├── hardcoded_test_data_detector.py
│   │   │   │   └── cicd_bypass_detector.py
│   │   │   ├── analyzers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── ast_analyzer.py      # AST-based analysis
│   │   │   │   ├── regex_analyzer.py    # Regex pattern matching
│   │   │   │   └── context_analyzer.py  # Context-aware validation
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── detection_result.py  # Detection result schema
│   │   │   │   └── remediation.py       # Remediation suggestion schema
│   │   │   └── config/
│   │   │       ├── __init__.py
│   │   │       └── patterns.py          # Pattern definitions
│   │   └── registry.py                  # Hook registry
├── tests/
│   └── hooks/
│       └── reward_hacking/
│           ├── test_detectors.py
│           ├── test_hook_manager.py
│           └── test_integration.py
└── .pre-commit-config.yaml              # Pre-commit hook config
```

## Components and Interfaces

### 1. Base Detector

```python
from abc import ABC, abstractmethod
from typing import List
from pydantic import BaseModel

class DetectionResult(BaseModel):
    """Detection result schema"""
    detector_name: str
    pattern_type: str
    severity: str  # CRITICAL, WARNING, INFO
    file_path: str
    line_number: int
    code_snippet: str
    message: str
    remediation: str
    confidence: float  # 0.0 - 1.0

class BaseDetector(ABC):
    """Abstract base class for reward hacking detectors"""
    
    def __init__(self, config: dict):
        self.config = config
        self.name = self.__class__.__name__
    
    @abstractmethod
    async def detect(self, file_path: str, content: str) -> List[DetectionResult]:
        """
        Detect reward hacking patterns in file content
        
        Args:
            file_path: Path to file being analyzed
            content: File content as string
            
        Returns:
            List of detection results
        """
        pass
    
    @abstractmethod
    def get_patterns(self) -> List[str]:
        """Get regex patterns for this detector"""
        pass
```

### 2. Assert True Detector

```python
import ast
import re
from typing import List

class AssertTrueDetector(BaseDetector):
    """Detects assert True and similar fake assertions"""
    
    def get_patterns(self) -> List[str]:
        return [
            r"assert\s+True\b",
            r"ASSERT_TRUE\(true\)",
            r"self\.assertTrue\(True\)",
        ]
    
    async def detect(self, file_path: str, content: str) -> List[DetectionResult]:
        results = []
        
        # Regex-based detection
        for pattern in self.get_patterns():
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                line_content = content.split('\n')[line_num - 1]
                
                # Context analysis to reduce false positives
                if self._is_legitimate_use(line_content):
                    continue
                
                results.append(DetectionResult(
                    detector_name=self.name,
                    pattern_type="assert_true",
                    severity="CRITICAL",
                    file_path=file_path,
                    line_number=line_num,
                    code_snippet=line_content.strip(),
                    message="Fake assertion detected: assert True",
                    remediation="Replace with meaningful assertion: assert actual_value == expected_value",
                    confidence=0.95
                ))
        
        # AST-based detection for more complex cases
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Assert):
                    if isinstance(node.test, ast.Constant) and node.test.value is True:
                        results.append(DetectionResult(
                            detector_name=self.name,
                            pattern_type="assert_true_ast",
                            severity="CRITICAL",
                            file_path=file_path,
                            line_number=node.lineno,
                            code_snippet=ast.unparse(node),
                            message="AST analysis: Fake assertion detected",
                            remediation="Write meaningful test assertion",
                            confidence=1.0
                        ))
        except SyntaxError:
            pass  # Skip files with syntax errors
        
        return results
    
    def _is_legitimate_use(self, line: str) -> bool:
        """Check if assert True is legitimate (e.g., in documentation)"""
        # Example: docstring or comment
        if line.strip().startswith('#') or '"""' in line:
            return True
        return False
```

### 3. Hook Manager

```python
import asyncio
from typing import List, Dict
from pathlib import Path

class HookManager:
    """Orchestrates reward hacking detection hooks"""
    
    def __init__(self):
        self.detectors: List[BaseDetector] = []
        self._register_detectors()
    
    def _register_detectors(self):
        """Register all detectors"""
        from .detectors import (
            AssertTrueDetector,
            EchoSuccessDetector,
            PlaceholderDetector,
            CoverageManipulationDetector,
            MockAbuseDetector,
            EmptyExceptionDetector,
            HardcodedTestDataDetector,
            CICDBypassDetector,
        )
        
        config = self._load_config()
        self.detectors = [
            AssertTrueDetector(config),
            EchoSuccessDetector(config),
            PlaceholderDetector(config),
            CoverageManipulationDetector(config),
            MockAbuseDetector(config),
            EmptyExceptionDetector(config),
            HardcodedTestDataDetector(config),
            CICDBypassDetector(config),
        ]
    
    async def run_hooks(self, file_paths: List[str]) -> Dict[str, any]:
        """
        Run all detectors on given files
        
        Args:
            file_paths: List of file paths to analyze
            
        Returns:
            Aggregated results with exit code
        """
        all_results = []
        
        # Run detectors in parallel for each file
        for file_path in file_paths:
            if not self._should_analyze(file_path):
                continue
            
            content = Path(file_path).read_text(encoding='utf-8')
            
            # Run all detectors concurrently
            tasks = [detector.detect(file_path, content) for detector in self.detectors]
            detector_results = await asyncio.gather(*tasks)
            
            # Flatten results
            for results in detector_results:
                all_results.extend(results)
        
        # Aggregate and decide exit code
        return self._aggregate_results(all_results)
    
    def _should_analyze(self, file_path: str) -> bool:
        """Check if file should be analyzed"""
        extensions = {'.py', '.sh', '.yml', '.yaml'}
        return Path(file_path).suffix in extensions
    
    def _aggregate_results(self, results: List[DetectionResult]) -> Dict[str, any]:
        """Aggregate results and determine exit code"""
        critical_count = sum(1 for r in results if r.severity == "CRITICAL")
        warning_count = sum(1 for r in results if r.severity == "WARNING")
        
        # Exit code logic
        if critical_count > 0:
            exit_code = 2  # Block commit
        elif warning_count > 0:
            exit_code = 1  # Warning
        else:
            exit_code = 0  # Clean
        
        return {
            "exit_code": exit_code,
            "total_detections": len(results),
            "critical_count": critical_count,
            "warning_count": warning_count,
            "results": [r.dict() for r in results],
            "summary": self._generate_summary(results)
        }
    
    def _generate_summary(self, results: List[DetectionResult]) -> str:
        """Generate human-readable summary"""
        if not results:
            return "✅ No reward hacking patterns detected"
        
        summary = "❌ Reward Hacking Detected!\n\n"
        for result in results:
            summary += f"[{result.severity}] {result.pattern_type}\n"
            summary += f"  Location: {result.file_path}:{result.line_number}\n"
            summary += f"  Code: {result.code_snippet}\n"
            summary += f"  Suggestion: {result.remediation}\n\n"
        
        return summary
    
    def _load_config(self) -> dict:
        """Load detector configuration"""
        return {
            "assert_true": {"enabled": True, "severity": "CRITICAL"},
            "echo_success": {"enabled": True, "severity": "CRITICAL"},
            "placeholder": {"enabled": True, "severity": "CRITICAL"},
            "coverage_manipulation": {"enabled": True, "severity": "CRITICAL"},
            "mock_abuse": {"enabled": True, "severity": "WARNING"},
            "empty_exception": {"enabled": True, "severity": "CRITICAL"},
            "hardcoded_test_data": {"enabled": True, "severity": "WARNING"},
            "cicd_bypass": {"enabled": True, "severity": "CRITICAL"},
        }
```

## Data Models

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class SeverityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"

class PatternType(str, Enum):
    ASSERT_TRUE = "assert_true"
    ECHO_SUCCESS = "echo_success"
    PLACEHOLDER = "placeholder"
    COVERAGE_MANIPULATION = "coverage_manipulation"
    MOCK_ABUSE = "mock_abuse"
    EMPTY_EXCEPTION = "empty_exception"
    HARDCODED_TEST_DATA = "hardcoded_test_data"
    CICD_BYPASS = "cicd_bypass"

class DetectionResult(BaseModel):
    detector_name: str = Field(..., description="Name of detector that found the issue")
    pattern_type: PatternType = Field(..., description="Type of reward hacking pattern")
    severity: SeverityLevel = Field(..., description="Severity level")
    file_path: str = Field(..., description="Path to file with issue")
    line_number: int = Field(..., ge=1, description="Line number of issue")
    code_snippet: str = Field(..., description="Code snippet showing the issue")
    message: str = Field(..., description="Human-readable message")
    remediation: str = Field(..., description="Suggested fix")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")

class HookResult(BaseModel):
    exit_code: int = Field(..., ge=0, le=2, description="Exit code (0: clean, 1: warning, 2: block)")
    total_detections: int = Field(..., ge=0, description="Total number of detections")
    critical_count: int = Field(..., ge=0, description="Number of critical issues")
    warning_count: int = Field(..., ge=0, description="Number of warnings")
    results: List[DetectionResult] = Field(default_factory=list, description="All detection results")
    summary: str = Field(..., description="Human-readable summary")
    execution_time_ms: float = Field(..., description="Hook execution time in milliseconds")

class DetectorConfig(BaseModel):
    enabled: bool = Field(default=True, description="Whether detector is enabled")
    severity: SeverityLevel = Field(default=SeverityLevel.CRITICAL, description="Default severity")
    patterns: List[str] = Field(default_factory=list, description="Regex patterns to match")
    exceptions: List[str] = Field(default_factory=list, description="Exception patterns (legitimate uses)")
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system.*

### Property 1: Detection Completeness
*For any* file containing a reward hacking pattern from the banned patterns list, *the hook manager SHALL detect it and return a non-zero exit code.*

**Validates: Requirements 1.1, 1.2, 2.1, 2.2, 3.1, 3.3, 4.1, 4.3, 5.1, 6.1, 6.2, 7.1, 8.1, 8.2**

### Property 2: Exit Code Consistency
*For any* detection result with severity CRITICAL, *the aggregated exit code SHALL be 2 (blocking).*

**Validates: Requirements 1.2, 2.2, 3.3, 4.3, 6.2, 8.2**

### Property 3: False Positive Minimization
*For any* legitimate code pattern (e.g., assert True in docstring), *the context analyzer SHALL exclude it from critical detections.*

**Validates: Requirements 1.5, 2.5, 4.6, 6.6**

### Property 4: Remediation Completeness
*For any* detection result, *there SHALL exist a non-empty remediation suggestion.*

**Validates: Requirements 1.6, 2.6, 3.6, 4.6, 5.6, 6.6, 7.6, 8.6**

### Property 5: Parallel Execution Safety
*For any* set of files analyzed concurrently, *the detection results SHALL be deterministic and order-independent.*

**Validates: All requirements (system-wide property)**

### Property 6: Pattern Coverage
*For any* detector, *the number of regex patterns + AST checks SHALL cover all acceptance criteria for that detector.*

**Validates: Requirements 1.1-1.6, 2.1-2.6, 3.1-3.6, 4.1-4.6, 5.1-5.6, 6.1-6.6, 7.1-7.6, 8.1-8.6**

## Error Handling

```python
class RewardHackingError(Exception):
    """Base exception for reward hacking detection"""
    pass

class DetectorError(RewardHackingError):
    """Detector execution error"""
    pass

class ASTParseError(RewardHackingError):
    """AST parsing error"""
    pass

# Error handling in HookManager
async def run_hooks(self, file_paths: List[str]) -> Dict[str, any]:
    try:
        # ... detection logic ...
    except DetectorError as e:
        logger.error(f"Detector error: {e}")
        return {
            "exit_code": 1,
            "error": str(e),
            "summary": "⚠️ Detection partially failed, review manually"
        }
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return {
            "exit_code": 0,  # Fail open to not block development
            "error": str(e),
            "summary": "⚠️ Hook execution failed, manual review required"
        }
```

## Testing Strategy

### Unit Tests
- Test each detector independently with known patterns
- Test context analyzer with edge cases
- Test AST analyzer with malformed Python code
- Test regex analyzer with boundary cases

### Property-Based Tests
- Generate random code with/without reward hacking patterns
- Verify detection completeness property
- Verify exit code consistency property
- Verify false positive rate < 5%

### Integration Tests
- Test full hook manager workflow
- Test pre-commit hook integration
- Test parallel execution with multiple files
- Test performance with large codebases

**Test Configuration**: Minimum 100 iterations per property test

## Performance Considerations

- **Parallel Detection**: Run all detectors concurrently using asyncio
- **AST Caching**: Cache parsed AST trees for repeated analysis
- **Regex Compilation**: Pre-compile all regex patterns at initialization
- **File Filtering**: Skip non-relevant files early (e.g., .md, .json)
- **Target Latency**: < 500ms for typical commit (10-20 files)

## Security Considerations

- **Code Injection**: Never execute analyzed code, only parse/analyze
- **Path Traversal**: Validate file paths before reading
- **Resource Limits**: Set timeout for detector execution (5s per file)
- **Logging**: Sanitize code snippets in logs to avoid sensitive data exposure
