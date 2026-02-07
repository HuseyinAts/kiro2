"""
Bionic Reading Türkçe Modülü
REQ-1 ile REQ-8 arası tüm gereksinimleri karşılar

Modüller:
- syllabifier: Turkish syllabification (REQ-2)
- fixation: Fixation point detection (REQ-1)
- formatter: Multi-format output (REQ-6)
- speed_tracker: Reading speed optimization (REQ-3)
- comprehension: Comprehension testing (REQ-4)
- accessibility: Accessibility features (REQ-7)
"""

from .syllabifier import TurkishSyllabifier
from .fixation import FixationPointDetector
from .formatter import BionicFormatter, OutputFormat
from .speed_tracker import ReadingSpeedTracker
from .comprehension import ComprehensionValidator
from .accessibility import AccessibilityManager

__all__ = [
    "TurkishSyllabifier",
    "FixationPointDetector",
    "BionicFormatter",
    "OutputFormat",
    "ReadingSpeedTracker",
    "ComprehensionValidator",
    "AccessibilityManager",
]
