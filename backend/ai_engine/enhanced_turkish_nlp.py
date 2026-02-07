"""
Enhanced Turkish NLP Engine
Advanced Turkish language processing with machine learning
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from transformers import pipeline
import torch

logger = logging.getLogger(__name__)


class TextComplexityLevel(Enum):
    """Text complexity levels for Turkish education"""

    BEGINNER = "başlangıç"
    ELEMENTARY = "temel"
    INTERMEDIATE = "orta"
    ADVANCED = "ileri"
    EXPERT = "uzman"


class EducationalContext(Enum):
    """Educational contexts for content adaptation"""

    TYT = "tyt"
    AYT = "ayt"
    YKS = "yks"
    LGS = "lgs"
    KPSS = "kpss"
    GENERAL = "genel"


@dataclass
class TurkishTextAnalysis:
    """Comprehensive Turkish text analysis result"""

    text: str
    complexity_level: TextComplexityLevel
    readability_score: float  # 0-100
    vocabulary_difficulty: float  # 0-1
    syntactic_complexity: float  # 0-1
    semantic_richness: float  # 0-1

    # Linguistic features
    morphological_complexity: float
    compound_word_ratio: float
    foreign_word_ratio: float
    technical_term_ratio: float

    # Educational features
    educational_context: Optional[EducationalContext]
    key_concepts: List[str]
    prerequisite_concepts: List[str]
    difficulty_factors: List[str]

    # Suggestions for improvement
    simplification_suggestions: List[str] = field(default_factory=list)
    vocabulary_alternatives: Dict[str, List[str]] = field(default_factory=dict)

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConceptEntity:
    """Educational concept entity"""

    concept: str
    category: str  # matematik, fizik, kimya, etc.
    difficulty_level: float
    prerequisites: List[str]
    related_concepts: List[str]
    definition: Optional[str] = None
    examples: List[str] = field(default_factory=list)


class EnhancedTurkishNLP:
    """Advanced Turkish NLP engine for educational content"""

    def __init__(self):
        self.ready = False
        self.models = {}
        self.vectorizers = {}
        self.concept_database = {}

        # Turkish specific patterns
        self.turkish_suffixes = [
            "lar",
            "ler",
            "da",
            "de",
            "ta",
            "te",
            "dan",
            "den",
            "tan",
            "ten",
            "nın",
            "nin",
            "nun",
            "nün",
            "sı",
            "si",
            "su",
            "sü",
            "ı",
            "i",
            "u",
            "ü",
        ]

        self.technical_terms_patterns = {
            "matematik": r"\b(denk(?:lem|lik)|fonksiyon|türev|integral|matris|vektör)\b",
            "fizik": r"\b(kuvvet|enerji|momentum|elektrik|manyetik|dalgalar?)\b",
            "kimya": r"\b(element|bileşik|reaksiyon|asit|baz|mol|atom)\b",
            "biyoloji": r"\b(hücre|gen|protein|enzim|metabolizma|ekosistem)\b",
        }

        # Initialize asyncio
        self.loop = None

    async def initialize(self):
        """Initialize NLP models and resources"""
        if self.ready:
            return

        logger.info("Initializing Enhanced Turkish NLP Engine...")

        try:
            # Initialize Turkish language model
            await self._load_language_models()

            # Initialize concept database
            await self._load_concept_database()

            # Initialize vectorizers
            await self._initialize_vectorizers()

            self.ready = True
            logger.info("Enhanced Turkish NLP Engine initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize NLP engine: {e}")
            raise

    async def _load_language_models(self):
        """Load language models for Turkish processing"""
        try:
            # Load Turkish BERT model for semantic analysis
            self.models["turkish_bert"] = pipeline(
                "feature-extraction",
                model="dbmdz/bert-base-turkish-cased",
                tokenizer="dbmdz/bert-base-turkish-cased",
                device=0 if torch.cuda.is_available() else -1,
            )

            # Load sentiment analysis for educational content
            self.models["sentiment"] = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-xlm-roberta-base-sentiment",
                device=0 if torch.cuda.is_available() else -1,
            )

            logger.info("Language models loaded successfully")

        except Exception as e:
            logger.warning(f"Could not load transformer models: {e}")
            # Fallback to simpler models
            self.models["turkish_bert"] = None
            self.models["sentiment"] = None

    async def _load_concept_database(self):
        """Load educational concept database"""
        # Educational concepts for Turkish curriculum
        concepts = {
            "matematik": {
                "algebra": ["denklem", "eşitsizlik", "fonksiyon", "grafikler"],
                "geometri": ["üçgen", "dörtgen", "çember", "alan", "hacim"],
                "analiz": ["türev", "integral", "limit", "süreklilik"],
                "istatistik": ["ortalama", "medyan", "standart sapma", "olasılık"],
            },
            "fizik": {
                "mekanik": ["kuvvet", "hareket", "enerji", "momentum"],
                "termodinamik": ["sıcaklık", "ısı", "basınç", "entropi"],
                "elektrik": ["akım", "gerilim", "direnç", "güç"],
                "optik": ["ışık", "lens", "ayna", "kırılma"],
            },
            "kimya": {
                "atomik_yapı": ["atom", "elektron", "proton", "nötron"],
                "bağlar": ["iyonik", "kovalent", "metalik", "hidrojen"],
                "reaksiyonlar": ["asit", "baz", "oksidasyon", "indirgeme"],
                "organik": ["karbon", "hidrokarbon", "fonksiyonel grup"],
            },
        }

        # Convert to ConceptEntity objects
        for subject, categories in concepts.items():
            for category, concept_list in categories.items():
                for concept in concept_list:
                    entity = ConceptEntity(
                        concept=concept,
                        category=f"{subject}_{category}",
                        difficulty_level=0.5,  # Default difficulty
                        prerequisites=[],
                        related_concepts=[],
                    )
                    self.concept_database[concept] = entity

    async def _initialize_vectorizers(self):
        """Initialize text vectorizers for similarity analysis"""
        self.vectorizers["tfidf"] = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 3),
            stop_words=self._get_turkish_stop_words(),
        )

    def _get_turkish_stop_words(self) -> List[str]:
        """Get Turkish stop words"""
        return [
            "ve",
            "bir",
            "bu",
            "da",
            "de",
            "ile",
            "için",
            "olan",
            "var",
            "ama",
            "çok",
            "daha",
            "en",
            "gibi",
            "her",
            "kadar",
            "ne",
            "olan",
            "olarak",
            "sonra",
            "şu",
            "ya",
            "yani",
            "ancak",
            "artık",
            "aslında",
            "böyle",
            "çünkü",
            "dolayısıyla",
            "hatta",
            "hem",
            "hep",
            "hiç",
            "nasıl",
            "neden",
            "sadece",
            "şimdi",
            "tüm",
            "üzere",
            "zaten",
        ]

    async def analyze_text_complexity(
        self, text: str, context: Optional[EducationalContext] = None
    ) -> TurkishTextAnalysis:
        """Comprehensive text complexity analysis"""
        if not self.ready:
            await self.initialize()

        # Basic text statistics
        words = self._tokenize_turkish(text)
        sentences = self._split_sentences(text)

        # Calculate complexity metrics
        readability_score = await self._calculate_readability(text, words, sentences)
        vocabulary_difficulty = await self._analyze_vocabulary_difficulty(words)
        syntactic_complexity = await self._analyze_syntactic_complexity(sentences)
        semantic_richness = await self._calculate_semantic_richness(text)

        # Linguistic features
        morphological_complexity = await self._analyze_morphological_complexity(words)
        compound_word_ratio = self._calculate_compound_word_ratio(words)
        foreign_word_ratio = self._calculate_foreign_word_ratio(words)
        technical_term_ratio = await self._calculate_technical_term_ratio(text, context)

        # Educational analysis
        key_concepts = await self._extract_key_concepts(text)
        prerequisite_concepts = await self._identify_prerequisites(key_concepts)
        difficulty_factors = await self._identify_difficulty_factors(text)

        # Determine overall complexity level
        complexity_level = self._determine_complexity_level(
            readability_score, vocabulary_difficulty, syntactic_complexity
        )

        # Generate suggestions
        simplification_suggestions = await self._generate_simplification_suggestions(
            text
        )
        vocabulary_alternatives = await self._suggest_vocabulary_alternatives(words)

        return TurkishTextAnalysis(
            text=text,
            complexity_level=complexity_level,
            readability_score=readability_score,
            vocabulary_difficulty=vocabulary_difficulty,
            syntactic_complexity=syntactic_complexity,
            semantic_richness=semantic_richness,
            morphological_complexity=morphological_complexity,
            compound_word_ratio=compound_word_ratio,
            foreign_word_ratio=foreign_word_ratio,
            technical_term_ratio=technical_term_ratio,
            educational_context=context,
            key_concepts=key_concepts,
            prerequisite_concepts=prerequisite_concepts,
            difficulty_factors=difficulty_factors,
            simplification_suggestions=simplification_suggestions,
            vocabulary_alternatives=vocabulary_alternatives,
        )

    def _tokenize_turkish(self, text: str) -> List[str]:
        """Tokenize Turkish text considering morphological structure"""
        # Remove punctuation and normalize
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text.strip())

        # Split into words
        words = text.lower().split()

        # Filter out very short or long words
        words = [w for w in words if 2 <= len(w) <= 25]

        return words

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Turkish sentence endings
        sentence_endings = r"[.!?…]"
        sentences = re.split(sentence_endings, text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences

    async def _calculate_readability(
        self, text: str, words: List[str], sentences: List[str]
    ) -> float:
        """Calculate readability score for Turkish text"""
        if not sentences or not words:
            return 0.0

        # Adapted Flesch Reading Ease for Turkish
        avg_sentence_length = len(words) / len(sentences)
        avg_syllables_per_word = np.mean(
            [self._count_syllables_turkish(word) for word in words]
        )

        # Turkish adapted formula
        readability = (
            206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        )

        # Normalize to 0-100
        return max(0, min(100, readability))

    def _count_syllables_turkish(self, word: str) -> int:
        """Count syllables in Turkish word"""
        vowels = "aeıioöuü"
        syllables = 0
        prev_was_vowel = False

        for char in word.lower():
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                syllables += 1
            prev_was_vowel = is_vowel

        return max(1, syllables)

    async def _analyze_vocabulary_difficulty(self, words: List[str]) -> float:
        """Analyze vocabulary difficulty"""
        if not words:
            return 0.0

        # Common Turkish words (most frequent 1000 words)
        common_words = set(
            [
                "bir",
                "bu",
                "ve",
                "ile",
                "için",
                "var",
                "olan",
                "çok",
                "daha",
                "en",
                "gibi",
                "her",
                "kadar",
                "ne",
                "olarak",
                "sonra",
                "şu",
                "ya",
                "yani",
                "artık",
                "böyle",
                "çünkü",
                "hem",
                "hiç",
                "nasıl",
            ]
        )

        # Calculate percentage of uncommon words
        uncommon_count = sum(
            1 for word in words if word not in common_words and len(word) > 3
        )
        difficulty = uncommon_count / len(words) if words else 0

        return min(1.0, difficulty)

    async def _analyze_syntactic_complexity(self, sentences: List[str]) -> float:
        """Analyze syntactic complexity"""
        if not sentences:
            return 0.0

        complexities = []
        for sentence in sentences:
            # Count complex structures
            complexity = 0

            # Subordinate clauses
            subordinates = len(
                re.findall(r"\b(ki|çünkü|eğer|ama|ancak|fakat)\b", sentence.lower())
            )
            complexity += subordinates * 0.2

            # Passive voice indicators
            passive_indicators = len(
                re.findall(r"\w+(ıl|il|ul|ül)(di|dı)", sentence.lower())
            )
            complexity += passive_indicators * 0.1

            # Complex verb forms
            complex_verbs = len(
                re.findall(r"\w+(miş|mış|muş|müş|acak|ecek)", sentence.lower())
            )
            complexity += complex_verbs * 0.1

            complexities.append(min(1.0, complexity))

        return np.mean(complexities) if complexities else 0.0

    async def _calculate_semantic_richness(self, text: str) -> float:
        """Calculate semantic richness using vocabulary diversity"""
        words = self._tokenize_turkish(text)
        if len(words) < 10:
            return 0.0

        # Type-Token Ratio
        unique_words = set(words)
        ttr = len(unique_words) / len(words)

        # Normalize TTR (higher is more diverse)
        return min(1.0, ttr * 2)

    async def _analyze_morphological_complexity(self, words: List[str]) -> float:
        """Analyze morphological complexity of Turkish words"""
        if not words:
            return 0.0

        complex_morphology_count = 0

        for word in words:
            if len(word) < 4:
                continue

            # Count potential suffixes
            suffix_count = 0
            for suffix in self.turkish_suffixes:
                if word.endswith(suffix):
                    suffix_count += 1

            # Words with multiple suffixes are more complex
            if suffix_count >= 2 or len(word) > 10:
                complex_morphology_count += 1

        return complex_morphology_count / len(words) if words else 0.0

    def _calculate_compound_word_ratio(self, words: List[str]) -> float:
        """Calculate ratio of compound words"""
        if not words:
            return 0.0

        # Simple heuristic: very long words likely compound
        compound_count = sum(1 for word in words if len(word) > 12)
        return compound_count / len(words)

    def _calculate_foreign_word_ratio(self, words: List[str]) -> float:
        """Calculate ratio of foreign words in Turkish text"""
        if not words:
            return 0.0

        # Common foreign word patterns in Turkish
        foreign_patterns = [
            r"\w*tion\w*",  # -tion suffix (English)
            r"\w*sion\w*",  # -sion suffix (English)
            r"\w*ment\w*",  # -ment suffix (English/French)
            r"\w*ismus\w*",  # -ismus suffix (Latin/Greek)
        ]

        foreign_count = 0
        for word in words:
            for pattern in foreign_patterns:
                if re.search(pattern, word.lower()):
                    foreign_count += 1
                    break

        return foreign_count / len(words)

    async def _calculate_technical_term_ratio(
        self, text: str, context: Optional[EducationalContext]
    ) -> float:
        """Calculate ratio of technical terms"""
        technical_count = 0

        for subject, pattern in self.technical_terms_patterns.items():
            matches = len(re.findall(pattern, text.lower()))
            technical_count += matches

        word_count = len(self._tokenize_turkish(text))
        return technical_count / word_count if word_count > 0 else 0.0

    async def _extract_key_concepts(self, text: str) -> List[str]:
        """Extract key educational concepts from text"""
        concepts = []
        text_lower = text.lower()

        # Find concepts in our database
        for concept, entity in self.concept_database.items():
            if concept in text_lower:
                concepts.append(concept)

        # Use TF-IDF for additional concept extraction
        if self.vectorizers.get("tfidf"):
            try:
                # Fit on current text (simple approach)
                tfidf_matrix = self.vectorizers["tfidf"].fit_transform([text])
                feature_names = self.vectorizers["tfidf"].get_feature_names_out()
                tfidf_scores = tfidf_matrix.toarray()[0]

                # Get top terms
                top_indices = np.argsort(tfidf_scores)[-10:]
                top_terms = [
                    feature_names[i] for i in top_indices if tfidf_scores[i] > 0.1
                ]
                concepts.extend(top_terms)

            except Exception as e:
                logger.warning(f"TF-IDF concept extraction failed: {e}")

        return list(set(concepts))

    async def _identify_prerequisites(self, concepts: List[str]) -> List[str]:
        """Identify prerequisite concepts"""
        prerequisites = []

        for concept in concepts:
            if concept in self.concept_database:
                entity = self.concept_database[concept]
                prerequisites.extend(entity.prerequisites)

        return list(set(prerequisites))

    async def _identify_difficulty_factors(self, text: str) -> List[str]:
        """Identify factors that make text difficult"""
        factors = []

        # Long sentences
        sentences = self._split_sentences(text)
        avg_sentence_length = np.mean([len(s.split()) for s in sentences])
        if avg_sentence_length > 20:
            factors.append("uzun_cümleler")

        # Complex vocabulary
        words = self._tokenize_turkish(text)
        long_words = [w for w in words if len(w) > 10]
        if len(long_words) / len(words) > 0.3:
            factors.append("karmaşık_kelimeler")

        # Technical terminology
        technical_ratio = await self._calculate_technical_term_ratio(text, None)
        if technical_ratio > 0.1:
            factors.append("teknik_terimler")

        # Foreign words
        foreign_ratio = self._calculate_foreign_word_ratio(words)
        if foreign_ratio > 0.05:
            factors.append("yabancı_kelimeler")

        return factors

    def _determine_complexity_level(
        self, readability: float, vocabulary: float, syntax: float
    ) -> TextComplexityLevel:
        """Determine overall complexity level"""
        # Weighted average of complexity metrics
        overall_score = (
            readability * 0.4 + (1 - vocabulary) * 0.3 + (1 - syntax) * 0.3
        ) * 100

        if overall_score >= 80:
            return TextComplexityLevel.BEGINNER
        elif overall_score >= 60:
            return TextComplexityLevel.ELEMENTARY
        elif overall_score >= 40:
            return TextComplexityLevel.INTERMEDIATE
        elif overall_score >= 20:
            return TextComplexityLevel.ADVANCED
        else:
            return TextComplexityLevel.EXPERT

    async def _generate_simplification_suggestions(self, text: str) -> List[str]:
        """Generate suggestions to simplify text"""
        suggestions = []

        # Analyze sentences
        sentences = self._split_sentences(text)
        for sentence in sentences:
            words = sentence.split()

            if len(words) > 20:
                suggestions.append(f"Uzun cümleyi böl: '{sentence[:50]}...'")

            # Check for complex words
            complex_words = [w for w in words if len(w) > 12]
            if complex_words:
                suggestions.append(
                    f"Karmaşık kelimeleri sadeleştir: {', '.join(complex_words[:3])}"
                )

        return suggestions

    async def _suggest_vocabulary_alternatives(
        self, words: List[str]
    ) -> Dict[str, List[str]]:
        """Suggest simpler vocabulary alternatives"""
        alternatives = {}

        # Common complex -> simple word mappings for Turkish
        word_alternatives = {
            "gerçekleştirmek": ["yapmak", "uygulamak"],
            "değerlendirmek": ["değerlemek", "incelemek"],
            "tanımlamak": ["belirlemek", "açıklamak"],
            "kullanılmaktadır": ["kullanılır", "kullanıyor"],
            "bulunmaktadır": ["bulunur", "vardır"],
            "oluşturmaktadır": ["oluşturur", "yapar"],
        }

        for word in words:
            if word.lower() in word_alternatives:
                alternatives[word] = word_alternatives[word.lower()]

        return alternatives


# Global instance
enhanced_turkish_nlp = EnhancedTurkishNLP()


async def get_enhanced_nlp() -> EnhancedTurkishNLP:
    """Get initialized enhanced NLP instance"""
    if not enhanced_turkish_nlp.ready:
        await enhanced_turkish_nlp.initialize()
    return enhanced_turkish_nlp
