"""
Zemberek Bridge Exceptions
Custom exception classes for JPype bridge operations
"""


class ZemberekError(Exception):
    """Base exception for all Zemberek operations"""



class JVMInitializationError(ZemberekError):
    """JVM failed to initialize"""

    def __init__(self, message: str = "JVM initialization failed"):
        self.message = message
        super().__init__(self.message)


class JVMNotStartedError(ZemberekError):
    """JVM is not started"""

    def __init__(self, message: str = "JVM is not started. Call initialize() first."):
        self.message = message
        super().__init__(self.message)


class AnalysisError(ZemberekError):
    """Morphological analysis failed"""

    def __init__(self, word: str, message: str = ""):
        self.word = word
        self.message = message or f"Analysis failed for word: {word}"
        super().__init__(self.message)


class SpellCheckError(ZemberekError):
    """Spell check operation failed"""

    def __init__(self, word: str, message: str = ""):
        self.word = word
        self.message = message or f"Spell check failed for word: {word}"
        super().__init__(self.message)


class TokenizationError(ZemberekError):
    """Tokenization failed"""

    def __init__(self, text: str, message: str = ""):
        self.text = text[:50] + "..." if len(text) > 50 else text
        self.message = message or f"Tokenization failed for text: {self.text}"
        super().__init__(self.message)


class NERError(ZemberekError):
    """Named Entity Recognition failed"""

    def __init__(self, text: str, message: str = ""):
        self.text = text[:50] + "..." if len(text) > 50 else text
        self.message = message or f"NER failed for text: {self.text}"
        super().__init__(self.message)


class SegmentationError(ZemberekError):
    """Sentence segmentation failed"""

    def __init__(self, text: str, message: str = ""):
        self.text = text[:50] + "..." if len(text) > 50 else text
        self.message = message or f"Segmentation failed for text: {self.text}"
        super().__init__(self.message)


class NormalizationError(ZemberekError):
    """Text normalization failed"""

    def __init__(self, text: str, message: str = ""):
        self.text = text[:50] + "..." if len(text) > 50 else text
        self.message = message or f"Normalization failed for text: {self.text}"
        super().__init__(self.message)
