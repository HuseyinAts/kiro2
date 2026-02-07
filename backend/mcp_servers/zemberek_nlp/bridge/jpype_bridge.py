"""
Zemberek JPype Bridge
Thread-safe singleton bridge to Zemberek Java library via JPype

Usage:
    bridge = get_bridge()
    bridge.initialize()
    result = bridge.analyze_word("kitaplar")
"""

import asyncio
import logging
import os
import platform
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from .exceptions import (
    AnalysisError,
    JVMInitializationError,
    JVMNotStartedError,
    NERError,
    NormalizationError,
    SegmentationError,
    SpellCheckError,
    TokenizationError,
)

logger = logging.getLogger(__name__)

# JPype lazy import
jpype = None


def _import_jpype():
    """Lazy import JPype to avoid import errors when not installed"""
    global jpype
    if jpype is None:
        try:
            import jpype as _jpype
            import jpype.imports

            jpype = _jpype
        except ImportError as e:
            logger.error(f"JPype not installed: {e}")
            raise JVMInitializationError(
                "JPype1 is not installed. Install with: pip install JPype1"
            )
    return jpype


class ZemberekJPypeBridge:
    """
    Thread-safe singleton bridge to Zemberek Java library.

    This class provides access to Zemberek NLP components through JPype.
    It uses a singleton pattern to ensure only one JVM instance is created.

    Attributes:
        morphology: TurkishMorphology instance
        spell_checker: TurkishSpellChecker instance
        tokenizer: TurkishTokenizer instance
        sentence_extractor: TurkishSentenceExtractor instance
    """

    _instance: Optional["ZemberekJPypeBridge"] = None
    _lock = threading.Lock()
    _initialized = False

    # Zemberek Java classes (populated after JVM init)
    _TurkishMorphology = None
    _TurkishSpellChecker = None
    _TurkishTokenizer = None
    _TurkishSentenceExtractor = None
    _TurkishSentenceNormalizer = None
    _PerceptronNer = None

    def __new__(cls) -> "ZemberekJPypeBridge":
        """Create or return singleton instance"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize instance (called once due to singleton)"""
        # Instance attributes
        self.morphology = None
        self.spell_checker = None
        self.tokenizer = None
        self.sentence_extractor = None
        self.sentence_normalizer = None
        self.ner = None

    @property
    def is_initialized(self) -> bool:
        """Check if JVM and Zemberek components are initialized"""
        return self._initialized

    @property
    def jvm_started(self) -> bool:
        """Check if JVM is started"""
        try:
            jp = _import_jpype()
            return jp.isJVMStarted()
        except Exception:
            return False

    def initialize(
        self,
        jar_path: Optional[str] = None,
        java_home: Optional[str] = None,
        jvm_options: Optional[List[str]] = None,
    ) -> bool:
        """
        Initialize JVM with Zemberek JAR.

        Args:
            jar_path: Path to Zemberek JAR file (auto-detected if None)
            java_home: JAVA_HOME path (uses env var if None)
            jvm_options: Additional JVM options

        Returns:
            True if initialized successfully

        Raises:
            JVMInitializationError: If JVM fails to start
        """
        if self._initialized:
            logger.debug("ZemberekJPypeBridge already initialized")
            return True

        with self._lock:
            if self._initialized:
                return True

            try:
                jp = _import_jpype()

                # Find JAR path
                jar_path = jar_path or self._find_zemberek_jar()
                if not jar_path or not os.path.exists(jar_path):
                    raise JVMInitializationError(
                        f"Zemberek JAR not found at: {jar_path}. "
                        "Download from Maven Central or run download_zemberek_jar.py"
                    )

                logger.info(f"Using Zemberek JAR: {jar_path}")

                # Start JVM if not already started
                if not jp.isJVMStarted():
                    jvm_path = self._get_jvm_path(java_home)

                    # Build classpath with platform-specific separator
                    classpath = self._build_classpath(jar_path)

                    # Build JVM arguments
                    jvm_args = [f"-Djava.class.path={classpath}"]
                    if jvm_options:
                        jvm_args.extend(jvm_options)

                    logger.info(f"Starting JVM with path: {jvm_path}")
                    logger.debug(f"JVM classpath: {classpath}")

                    jp.startJVM(jvm_path, *jvm_args, convertStrings=True)

                    logger.info("JVM started successfully")

                # Import Zemberek classes
                self._import_zemberek_classes()

                # Initialize components
                self._init_morphology()
                self._init_spell_checker()
                self._init_tokenizer()
                self._init_sentence_extractor()
                self._init_sentence_normalizer()
                self._init_ner()

                self._initialized = True
                logger.info("ZemberekJPypeBridge initialized successfully")
                return True

            except Exception as e:
                logger.error(f"Failed to initialize ZemberekJPypeBridge: {e}")
                raise JVMInitializationError(str(e))

    def _get_jvm_path(self, java_home: Optional[str] = None) -> str:
        """Get JVM path based on platform"""
        jp = _import_jpype()

        # Try user-provided JAVA_HOME first
        java_home = java_home or os.environ.get("JAVA_HOME")

        if java_home:
            if platform.system() == "Windows":
                jvm_path = os.path.join(java_home, "bin", "server", "jvm.dll")
                if not os.path.exists(jvm_path):
                    jvm_path = os.path.join(java_home, "jre", "bin", "server", "jvm.dll")
            else:
                jvm_path = os.path.join(java_home, "lib", "server", "libjvm.so")
                if not os.path.exists(jvm_path):
                    jvm_path = os.path.join(java_home, "jre", "lib", "amd64", "server", "libjvm.so")

            if os.path.exists(jvm_path):
                return jvm_path

        # Fall back to JPype default
        return jp.getDefaultJVMPath()

    def _build_classpath(self, jar_path: str) -> str:
        """Build classpath with platform-specific separator"""
        separator = ";" if platform.system() == "Windows" else ":"
        paths = [jar_path]

        # Add lib directory JARs if they exist
        lib_dir = Path(jar_path).parent
        for jar_file in lib_dir.glob("*.jar"):
            if str(jar_file) != jar_path:
                paths.append(str(jar_file))

        return separator.join(paths)

    def _find_zemberek_jar(self) -> Optional[str]:
        """Find Zemberek JAR file in common locations"""
        # Check environment variable
        env_path = os.environ.get("ZEMBEREK_JAR_PATH")
        if env_path and os.path.exists(env_path):
            return env_path

        # Check common locations
        search_paths = [
            # Project lib directory
            Path(__file__).parent.parent.parent.parent / "lib" / "zemberek",
            Path(__file__).parent.parent.parent.parent / "lib",
            # Backend root
            Path(__file__).parent.parent.parent.parent,
            # Current directory
            Path.cwd() / "lib" / "zemberek",
            Path.cwd() / "lib",
            Path.cwd(),
        ]

        jar_names = [
            "zemberek-full.jar",
            "zemberek-full-0.17.1.jar",
            "zemberek-full-0.18.0.jar",
        ]

        for search_path in search_paths:
            for jar_name in jar_names:
                jar_path = search_path / jar_name
                if jar_path.exists():
                    return str(jar_path)

        return None

    def _import_zemberek_classes(self):
        """Import Zemberek Java classes"""
        try:
            # Import morphology
            from zemberek.morphology import TurkishMorphology

            self._TurkishMorphology = TurkishMorphology

            # Import tokenizer
            from zemberek.tokenization import TurkishTokenizer

            self._TurkishTokenizer = TurkishTokenizer

            # Import spell checker
            from zemberek.normalization import TurkishSpellChecker

            self._TurkishSpellChecker = TurkishSpellChecker

            # Import sentence extractor
            from zemberek.tokenization import TurkishSentenceExtractor

            self._TurkishSentenceExtractor = TurkishSentenceExtractor

            # Import sentence normalizer (may not exist in all versions)
            try:
                from zemberek.normalization import TurkishSentenceNormalizer

                self._TurkishSentenceNormalizer = TurkishSentenceNormalizer
            except ImportError:
                logger.warning("TurkishSentenceNormalizer not available")
                self._TurkishSentenceNormalizer = None

            # Import NER (may not exist in all versions)
            try:
                from zemberek.ner import PerceptronNer

                self._PerceptronNer = PerceptronNer
            except ImportError:
                logger.warning("PerceptronNer not available")
                self._PerceptronNer = None

            logger.debug("Zemberek classes imported successfully")

        except Exception as e:
            raise JVMInitializationError(f"Failed to import Zemberek classes: {e}")

    def _init_morphology(self):
        """Initialize TurkishMorphology"""
        try:
            self.morphology = self._TurkishMorphology.createWithDefaults()
            logger.debug("TurkishMorphology initialized")
        except Exception as e:
            logger.error(f"Failed to init morphology: {e}")
            raise JVMInitializationError(f"Morphology init failed: {e}")

    def _init_spell_checker(self):
        """Initialize TurkishSpellChecker"""
        try:
            self.spell_checker = self._TurkishSpellChecker(self.morphology)
            logger.debug("TurkishSpellChecker initialized")
        except Exception as e:
            logger.warning(f"Failed to init spell checker: {e}")
            self.spell_checker = None

    def _init_tokenizer(self):
        """Initialize TurkishTokenizer"""
        try:
            self.tokenizer = self._TurkishTokenizer.DEFAULT
            logger.debug("TurkishTokenizer initialized")
        except Exception as e:
            logger.warning(f"Failed to init tokenizer: {e}")
            self.tokenizer = None

    def _init_sentence_extractor(self):
        """Initialize TurkishSentenceExtractor"""
        try:
            self.sentence_extractor = self._TurkishSentenceExtractor.DEFAULT
            logger.debug("TurkishSentenceExtractor initialized")
        except Exception as e:
            logger.warning(f"Failed to init sentence extractor: {e}")
            self.sentence_extractor = None

    def _init_sentence_normalizer(self):
        """Initialize TurkishSentenceNormalizer"""
        if self._TurkishSentenceNormalizer is None:
            self.sentence_normalizer = None
            return

        try:
            self.sentence_normalizer = self._TurkishSentenceNormalizer(self.morphology)
            logger.debug("TurkishSentenceNormalizer initialized")
        except Exception as e:
            logger.warning(f"Failed to init sentence normalizer: {e}")
            self.sentence_normalizer = None

    def _init_ner(self):
        """Initialize PerceptronNer"""
        if self._PerceptronNer is None:
            self.ner = None
            return

        try:
            # NER may require model path
            self.ner = self._PerceptronNer.loadModel()
            logger.debug("PerceptronNer initialized")
        except Exception as e:
            logger.warning(f"Failed to init NER: {e}")
            self.ner = None

    def _ensure_initialized(self):
        """Ensure bridge is initialized"""
        if not self._initialized:
            raise JVMNotStartedError()

    # ===== Morphological Analysis =====

    def analyze_word(self, word: str) -> List[Dict[str, Any]]:
        """
        Perform morphological analysis on a Turkish word.

        Args:
            word: Turkish word to analyze

        Returns:
            List of analysis results with root, lemma, POS, suffixes
        """
        self._ensure_initialized()

        try:
            analyses = self.morphology.analyze(word)
            results = []

            for analysis in analyses:
                result = {
                    "root": str(analysis.getDictionaryItem().root),
                    "lemma": str(analysis.getDictionaryItem().lemma),
                    "pos": str(analysis.getDictionaryItem().primaryPos),
                    "suffixes": [str(m) for m in analysis.getMorphemes()],
                    "formatted": str(analysis.formatLong()),
                    "stem": str(analysis.getStem()) if hasattr(analysis, "getStem") else None,
                }
                results.append(result)

            return results

        except Exception as e:
            raise AnalysisError(word, str(e))

    def lemmatize(self, word: str) -> str:
        """
        Get lemma (dictionary form) of a Turkish word.

        Args:
            word: Turkish word to lemmatize

        Returns:
            Lemma form of the word
        """
        self._ensure_initialized()

        try:
            analyses = self.morphology.analyze(word)
            if analyses and len(analyses) > 0:
                return str(analyses[0].getDictionaryItem().lemma)
            return word
        except Exception as e:
            raise AnalysisError(word, f"Lemmatization failed: {e}")

    def lemmatize_all(self, word: str) -> List[str]:
        """
        Get all possible lemmas for a word.

        Args:
            word: Turkish word to lemmatize

        Returns:
            List of all possible lemmas
        """
        self._ensure_initialized()

        try:
            analyses = self.morphology.analyze(word)
            lemmas = []
            for analysis in analyses:
                lemma = str(analysis.getDictionaryItem().lemma)
                if lemma not in lemmas:
                    lemmas.append(lemma)
            return lemmas if lemmas else [word]
        except Exception as e:
            raise AnalysisError(word, f"Lemmatization failed: {e}")

    # ===== Spell Checking =====

    def check_spelling(self, word: str) -> Dict[str, Any]:
        """
        Check spelling of a Turkish word.

        Args:
            word: Word to check

        Returns:
            Dict with is_correct and suggestions
        """
        self._ensure_initialized()

        if self.spell_checker is None:
            # Fallback: use morphology
            analyses = self.morphology.analyze(word)
            return {
                "word": word,
                "is_correct": len(analyses) > 0,
                "suggestions": [],
            }

        try:
            is_correct = self.spell_checker.check(word)
            suggestions = []

            if not is_correct:
                suggestion_list = self.spell_checker.suggestForWord(word)
                suggestions = [str(s) for s in suggestion_list][:5]

            return {
                "word": word,
                "is_correct": is_correct,
                "suggestions": suggestions,
            }
        except Exception as e:
            raise SpellCheckError(word, str(e))

    # ===== Tokenization =====

    def tokenize(self, text: str) -> List[Dict[str, Any]]:
        """
        Tokenize Turkish text.

        Args:
            text: Text to tokenize

        Returns:
            List of tokens with text and type
        """
        self._ensure_initialized()

        if self.tokenizer is None:
            # Fallback: simple split
            return [{"text": w, "type": "Word"} for w in text.split()]

        try:
            tokens = self.tokenizer.tokenize(text)
            results = []

            for token in tokens:
                results.append({
                    "text": str(token.getText()),
                    "type": str(token.getType()),
                    "start": token.getStart(),
                    "end": token.getEnd(),
                })

            return results
        except Exception as e:
            raise TokenizationError(text, str(e))

    # ===== Sentence Segmentation =====

    def segment_sentences(self, text: str) -> List[str]:
        """
        Segment text into sentences.

        Args:
            text: Text to segment

        Returns:
            List of sentences
        """
        self._ensure_initialized()

        if self.sentence_extractor is None:
            # Fallback: simple split on punctuation
            import re
            sentences = re.split(r'[.!?]+', text)
            return [s.strip() for s in sentences if s.strip()]

        try:
            sentences = self.sentence_extractor.fromParagraph(text)
            return [str(s) for s in sentences]
        except Exception as e:
            raise SegmentationError(text, str(e))

    # ===== Text Normalization =====

    def normalize(self, text: str) -> Dict[str, Any]:
        """
        Normalize informal Turkish text.

        Args:
            text: Text to normalize

        Returns:
            Dict with original and normalized text
        """
        self._ensure_initialized()

        if self.sentence_normalizer is None:
            # Fallback: return as-is
            return {
                "original": text,
                "normalized": text,
                "changes": [],
            }

        try:
            normalized = self.sentence_normalizer.normalize(text)
            changes = []

            # Track changes
            if normalized != text:
                changes.append({
                    "original": text,
                    "normalized": str(normalized),
                })

            return {
                "original": text,
                "normalized": str(normalized),
                "changes": changes,
            }
        except Exception as e:
            raise NormalizationError(text, str(e))

    # ===== Named Entity Recognition =====

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from text.

        Args:
            text: Text to analyze

        Returns:
            List of entities with text, type, start, end
        """
        self._ensure_initialized()

        if self.ner is None:
            # Fallback: return empty (NER not available)
            return []

        try:
            entities_result = self.ner.find(text)
            results = []

            for entity in entities_result:
                results.append({
                    "text": str(entity.getText()),
                    "type": str(entity.getType()),
                    "start": entity.getStart(),
                    "end": entity.getEnd(),
                })

            return results
        except Exception as e:
            raise NERError(text, str(e))

    # ===== Health Check =====

    def get_health(self) -> Dict[str, Any]:
        """
        Get health status of the bridge.

        Returns:
            Dict with status and component availability
        """
        return {
            "initialized": self._initialized,
            "jvm_started": self.jvm_started,
            "components": {
                "morphology": self.morphology is not None,
                "spell_checker": self.spell_checker is not None,
                "tokenizer": self.tokenizer is not None,
                "sentence_extractor": self.sentence_extractor is not None,
                "sentence_normalizer": self.sentence_normalizer is not None,
                "ner": self.ner is not None,
            },
        }

    # ===== Async Wrappers =====

    async def analyze_word_async(self, word: str) -> List[Dict[str, Any]]:
        """Async wrapper for analyze_word"""
        return await asyncio.to_thread(self.analyze_word, word)

    async def lemmatize_async(self, word: str) -> str:
        """Async wrapper for lemmatize"""
        return await asyncio.to_thread(self.lemmatize, word)

    async def check_spelling_async(self, word: str) -> Dict[str, Any]:
        """Async wrapper for check_spelling"""
        return await asyncio.to_thread(self.check_spelling, word)

    async def tokenize_async(self, text: str) -> List[Dict[str, Any]]:
        """Async wrapper for tokenize"""
        return await asyncio.to_thread(self.tokenize, text)

    async def segment_sentences_async(self, text: str) -> List[str]:
        """Async wrapper for segment_sentences"""
        return await asyncio.to_thread(self.segment_sentences, text)

    async def normalize_async(self, text: str) -> Dict[str, Any]:
        """Async wrapper for normalize"""
        return await asyncio.to_thread(self.normalize, text)

    async def extract_entities_async(self, text: str) -> List[Dict[str, Any]]:
        """Async wrapper for extract_entities"""
        return await asyncio.to_thread(self.extract_entities, text)


# Global bridge instance
_bridge: Optional[ZemberekJPypeBridge] = None


def get_bridge() -> ZemberekJPypeBridge:
    """Get or create global bridge instance"""
    global _bridge
    if _bridge is None:
        _bridge = ZemberekJPypeBridge()
    return _bridge
