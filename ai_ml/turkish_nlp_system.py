"""
KIRO2 - Turkish NLP System for Educational Content
=================================================

Bu modül, Türkçe eğitim içeriği için özelleştirilmiş Doğal Dil İşleme (NLP) 
sistemlerini içerir. TYT, AYT ve YKS sınavlarındaki Türkçe metinleri analiz eder.

Turkish NLP Bileşenleri:
- Türkçe metin ön işleme ve temizleme
- Türkçe dilbilgisi analizi ve POS tagging
- Türkçe sentiment analizi
- Türkçe metin benzerliği ve semantic search
- Türkçe soru-cevap (Q&A) sistemi
- Türkçe metin özetleme
- Türkçe kelime embedding ve word2vec
- Türkçe dil modeli fine-tuning

Eğitim İçeriği Özelleştirmeleri:
- TYT Türkçe soru analizi
- Edebiyat metinleri analizi
- Tarih ve sosyal bilimler metin madenciliği
- Matematik problemlerinde Türkçe NLP
- Öğrenci yazılarının otomatik değerlendirmesi
"""

import asyncio
import json
import logging
import re
import string
import time
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Advanced NLP libraries
try:
    import spacy
    from spacy.lang.tr import Turkish
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logging.warning("spaCy not available - some NLP features will be limited")

try:
    import torch
    from transformers import (
        AutoModel,
        AutoModelForSequenceClassification,
        AutoTokenizer,
        pipeline,
    )
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("Transformers not available - advanced NLP features disabled")

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import sent_tokenize, word_tokenize
    NLTK_AVAILABLE = True
    # Türkçe stopwords download
    try:
        stopwords.words('turkish')
    except:
        nltk.download('stopwords')
        nltk.download('punkt')
except ImportError:
    NLTK_AVAILABLE = False
    logging.warning("NLTK not available")


class TextDifficulty(Enum):
    """Metin zorluk seviyeleri"""
    VERY_EASY = 1
    EASY = 2
    MEDIUM = 3
    HARD = 4
    VERY_HARD = 5


class ContentType(Enum):
    """İçerik türleri"""
    QUESTION = "soru"
    EXPLANATION = "aciklama"
    EXAMPLE = "ornek"
    THEORY = "teori"
    EXERCISE = "alistirma"
    TEST = "test"
    LITERATURE = "edebiyat"
    HISTORY = "tarih"
    GEOGRAPHY = "cografya"


class SentimentType(Enum):
    """Duygu türleri"""
    POSITIVE = "pozitif"
    NEGATIVE = "negatif"
    NEUTRAL = "notr"
    EDUCATIONAL = "egitimsel"
    MOTIVATIONAL = "motive_edici"


@dataclass
class TurkishTextAnalysis:
    """Türkçe metin analizi sonucu"""
    original_text: str
    
    # Temel istatistikler
    word_count: int = 0
    sentence_count: int = 0
    paragraph_count: int = 0
    character_count: int = 0
    
    # Dil özellikleri
    readability_score: float = 0.0
    difficulty_level: TextDifficulty = TextDifficulty.MEDIUM
    
    # Kelime analizi
    unique_words: int = 0
    vocabulary_richness: float = 0.0
    most_common_words: List[Tuple[str, int]] = field(default_factory=list)
    
    # Dilbilgisi analizi
    pos_tags: List[Tuple[str, str]] = field(default_factory=list)
    grammatical_features: Dict[str, int] = field(default_factory=dict)
    
    # Anlamsal analizi
    key_topics: List[str] = field(default_factory=list)
    sentiment: SentimentType = SentimentType.NEUTRAL
    sentiment_score: float = 0.0
    
    # Eğitim özellikleri
    content_type: ContentType = ContentType.THEORY
    educational_keywords: List[str] = field(default_factory=list)
    complexity_indicators: Dict[str, float] = field(default_factory=dict)


@dataclass
class QuestionAnalysis:
    """Soru analizi sonucu"""
    question_text: str
    question_type: str  # çoktan_seçmeli, açık_uçlu, doğru_yanlış
    
    # Soru yapısı
    has_context: bool = False
    context_length: int = 0
    answer_choices_count: int = 0
    
    # Zorluk analizi
    estimated_difficulty: TextDifficulty = TextDifficulty.MEDIUM
    cognitive_level: str = "bilgi"  # bilgi, kavrama, uygulama, analiz, sentez, değerlendirme
    
    # Konu analizi
    subject: str = ""
    topic: str = ""
    keywords: List[str] = field(default_factory=list)
    
    # Dil özellikleri
    language_complexity: float = 0.0
    vocabulary_level: str = "temel"  # temel, orta, ileri
    
    
class TurkishTextPreprocessor:
    """Türkçe metin ön işleme sınıfı"""
    
    def __init__(self):
        self.turkish_stopwords = self._load_turkish_stopwords()
        self.turkish_punctuation = string.punctuation + """''–—"
        
        # Türkçe karakter dönüşümleri
        self.char_corrections = {
            'â': 'a', 'î': 'i', 'û': 'u', 'ô': 'o',
            'Â': 'A', 'Î': 'I', 'Û': 'U', 'Ô': 'O'
        }
        
        # Ortak yazım hataları
        self.common_mistakes = {
            'birşey': 'bir şey',
            'herşey': 'her şey',
            'neden': 'ne den',  # Bağlama göre
            'öyleki': 'öyle ki',
            'içinki': 'için ki',
            'olacakki': 'olacak ki'
        }
    
    def _load_turkish_stopwords(self) -> Set[str]:
        """Türkçe stopword'leri yükle"""
        stopwords_set = set()
        
        if NLTK_AVAILABLE:
            try:
                stopwords_set.update(stopwords.words('turkish'))
            except:
                pass
        
        # Manuel Türkçe stopwords
        manual_stopwords = {
            've', 'ile', 'bir', 'bu', 'şu', 'o', 'ben', 'sen', 'biz', 'siz', 'onlar',
            'için', 'kadar', 'gibi', 'olan', 'olarak', 'üzere', 'göre', 'daha',
            'en', 'çok', 'az', 'büyük', 'küçük', 'iyi', 'kötü', 'da', 'de', 'ta', 'te',
            'ki', 'mi', 'mı', 'mu', 'mü', 'ama', 'fakat', 'ancak', 'lakin',
            'işte', 'şöyle', 'böyle', 'hep', 'hiç', 'her', 'bazı', 'kimi'
        }
        
        stopwords_set.update(manual_stopwords)
        return stopwords_set
    
    def clean_text(self, text: str, preserve_case: bool = False) -> str:
        """Metni temizle"""
        if not text:
            return ""
        
        # Unicode normalization
        text = unicodedata.normalize('NFKD', text)
        
        # HTML/XML temizliği
        text = re.sub(r'<[^>]+>', '', text)
        
        # URL'leri temizle
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Email adreslerini temizle
        text = re.sub(r'\S+@\S+', '', text)
        
        # Fazla boşlukları temizle
        text = re.sub(r'\s+', ' ', text)
        
        # Ortak yazım hatalarını düzelt
        for mistake, correction in self.common_mistakes.items():
            text = text.replace(mistake, correction)
        
        # Karakterleri düzelt
        for old_char, new_char in self.char_corrections.items():
            text = text.replace(old_char, new_char)
        
        if not preserve_case:
            text = text.lower()
        
        return text.strip()
    
    def tokenize_turkish(self, text: str, remove_stopwords: bool = True,
                        remove_punctuation: bool = True) -> List[str]:
        """Türkçe tokenization"""
        if not text:
            return []
        
        # Temizle
        cleaned_text = self.clean_text(text)
        
        # Tokenize
        if NLTK_AVAILABLE:
            tokens = word_tokenize(cleaned_text, language='turkish')
        else:
            # Basit tokenization
            tokens = re.findall(r'\b\w+\b', cleaned_text)
        
        # Noktalama işaretlerini kaldır
        if remove_punctuation:
            tokens = [token for token in tokens if token not in self.turkish_punctuation]
        
        # Stopword'leri kaldır
        if remove_stopwords:
            tokens = [token for token in tokens if token not in self.turkish_stopwords]
        
        # Çok kısa kelimeler kaldır
        tokens = [token for token in tokens if len(token) > 1]
        
        return tokens
    
    def extract_sentences(self, text: str) -> List[str]:
        """Cümleleri ayır"""
        if not text:
            return []
        
        if NLTK_AVAILABLE:
            sentences = sent_tokenize(text, language='turkish')
        else:
            # Basit cümle ayırma
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def extract_paragraphs(self, text: str) -> List[str]:
        """Paragrafları ayır"""
        if not text:
            return []
        
        paragraphs = text.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        return paragraphs


class TurkishReadabilityAnalyzer:
    """Türkçe metin okunabilirlik analizi"""
    
    def __init__(self):
        self.preprocessor = TurkishTextPreprocessor()
        
        # Türkçe zorluk kelimeleri
        self.difficult_words = {
            'müteakip', 'müteakiben', 'ilhakında', 'maahaza', 'mevzubahis',
            'mahiyetinde', 'neticesinde', 'dolayısıyla', 'niteliksel', 'kavramsal',
            'felsefi', 'metodoloji', 'epistemoloji', 'paradigma'
        }
        
        # Basit kelimeler
        self.simple_words = {
            'ev', 'okul', 'kitap', 'masa', 'sandalye', 'su', 'ekmek', 'çocuk',
            'anne', 'baba', 'öğretmen', 'öğrenci', 'dün', 'bugün', 'yarın'
        }
    
    def calculate_readability_score(self, text: str) -> float:
        """Türkçe için okunabilirlik skoru hesapla"""
        if not text:
            return 0.0
        
        sentences = self.preprocessor.extract_sentences(text)
        tokens = self.preprocessor.tokenize_turkish(text, remove_stopwords=False)
        
        if not sentences or not tokens:
            return 0.0
        
        # Temel metrikler
        avg_sentence_length = len(tokens) / len(sentences)
        avg_word_length = sum(len(word) for word in tokens) / len(tokens)
        
        # Zor kelime oranı
        difficult_word_ratio = sum(1 for word in tokens if word in self.difficult_words) / len(tokens)
        
        # Basit kelime oranı
        simple_word_ratio = sum(1 for word in tokens if word in self.simple_words) / len(tokens)
        
        # Türkçe için özelleştirilmiş formül
        # (Flesch Reading Ease'in Türkçe adaptasyonu)
        readability_score = (
            100 - 
            (1.015 * avg_sentence_length) - 
            (84.6 * avg_word_length / 4.7) +  # Türkçe ortalama hece sayısı
            (50 * simple_word_ratio) - 
            (30 * difficult_word_ratio)
        )
        
        return max(0, min(100, readability_score))
    
    def determine_difficulty_level(self, readability_score: float) -> TextDifficulty:
        """Zorluk seviyesi belirle"""
        if readability_score >= 80:
            return TextDifficulty.VERY_EASY
        elif readability_score >= 65:
            return TextDifficulty.EASY
        elif readability_score >= 50:
            return TextDifficulty.MEDIUM
        elif readability_score >= 35:
            return TextDifficulty.HARD
        else:
            return TextDifficulty.VERY_HARD
    
    def analyze_vocabulary_complexity(self, text: str) -> Dict[str, float]:
        """Kelime dağarcığı karmaşıklık analizi"""
        tokens = self.preprocessor.tokenize_turkish(text)
        
        if not tokens:
            return {'complexity': 0.0, 'richness': 0.0}
        
        # Type-Token Ratio (TTR)
        unique_words = set(tokens)
        ttr = len(unique_words) / len(tokens)
        
        # Ortalama kelime uzunluğu
        avg_word_length = sum(len(word) for word in tokens) / len(tokens)
        
        # Zor kelime yoğunluğu
        difficult_density = sum(1 for word in tokens if len(word) > 8) / len(tokens)
        
        complexity = (avg_word_length / 10) + difficult_density + (1 - ttr)
        
        return {
            'complexity': min(1.0, complexity),
            'richness': ttr,
            'avg_word_length': avg_word_length,
            'difficult_density': difficult_density
        }


class TurkishSentimentAnalyzer:
    """Türkçe duygu analizi"""
    
    def __init__(self):
        self.preprocessor = TurkishTextPreprocessor()
        
        # Türkçe duygu kelimeleri
        self.positive_words = {
            'güzel', 'harika', 'mükemmel', 'başarılı', 'mutlu', 'sevindirici',
            'olumlu', 'yararlı', 'faydalı', 'etkili', 'başarı', 'kazanım',
            'gelişim', 'ilerleme', 'iyileşme', 'artış', 'büyüme', 'kalite'
        }
        
        self.negative_words = {
            'kötü', 'başarısız', 'üzücü', 'olumsuz', 'zararlı', 'etkisiz',
            'problem', 'sorun', 'hata', 'eksik', 'yetersiz', 'düşük',
            'azalma', 'gerileme', 'bozulma', 'yanlış', 'kusur'
        }
        
        self.educational_words = {
            'öğrenme', 'öğretim', 'eğitim', 'bilgi', 'bilim', 'araştırma',
            'inceleme', 'çalışma', 'analiz', 'sentez', 'kavram', 'teori',
            'uygulama', 'pratik', 'deneyim', 'beceri', 'yetenek', 'gelişim'
        }
        
        self.motivational_words = {
            'hedef', 'amaç', 'başarı', 'çaba', 'çalışma', 'gayret',
            'azim', 'kararlılık', 'motivasyon', 'ilham', 'teşvik',
            'cesaret', 'güven', 'umut', 'gelecek', 'fırsat', 'şans'
        }
    
    def analyze_sentiment(self, text: str) -> Tuple[SentimentType, float]:
        """Duygu analizi yap"""
        if not text:
            return SentimentType.NEUTRAL, 0.0
        
        tokens = self.preprocessor.tokenize_turkish(text.lower())
        
        if not tokens:
            return SentimentType.NEUTRAL, 0.0
        
        # Kelime sayıları
        positive_count = sum(1 for token in tokens if token in self.positive_words)
        negative_count = sum(1 for token in tokens if token in self.negative_words)
        educational_count = sum(1 for token in tokens if token in self.educational_words)
        motivational_count = sum(1 for token in tokens if token in self.motivational_words)
        
        total_sentiment_words = positive_count + negative_count + educational_count + motivational_count
        
        if total_sentiment_words == 0:
            return SentimentType.NEUTRAL, 0.0
        
        # Duygu skorları
        positive_score = positive_count / len(tokens)
        negative_score = negative_count / len(tokens)
        educational_score = educational_count / len(tokens)
        motivational_score = motivational_count / len(tokens)
        
        # En yüksek skora sahip duygu türünü belirle
        scores = {
            SentimentType.POSITIVE: positive_score,
            SentimentType.NEGATIVE: negative_score,
            SentimentType.EDUCATIONAL: educational_score,
            SentimentType.MOTIVATIONAL: motivational_score
        }
        
        dominant_sentiment = max(scores, key=scores.get)
        sentiment_strength = scores[dominant_sentiment]
        
        # Eşik değerler
        if sentiment_strength < 0.02:  # %2'den az
            return SentimentType.NEUTRAL, sentiment_strength
        
        return dominant_sentiment, sentiment_strength


class TurkishQuestionAnalyzer:
    """Türkçe soru analizi sistemi"""
    
    def __init__(self):
        self.preprocessor = TurkishTextPreprocessor()
        self.readability_analyzer = TurkishReadabilityAnalyzer()
        self.sentiment_analyzer = TurkishSentimentAnalyzer()
        
        # Soru türü belirleyicileri
        self.question_indicators = {
            'çoktan_seçmeli': ['A)', 'B)', 'C)', 'D)', 'E)', 'a)', 'b)', 'c)', 'd)', 'e)'],
            'doğru_yanlış': ['Doğru', 'Yanlış', 'doğru', 'yanlış', 'D-Y'],
            'açık_uçlu': ['açıklayınız', 'yorumlayınız', 'değerlendiriniz', 'tartışınız']
        }
        
        # Bilişsel seviye kelimeleri (Bloom's Taxonomy)
        self.cognitive_levels = {
            'bilgi': ['nedir', 'kimdir', 'hangi', 'ne zaman', 'nerede', 'kaç', 'sayınız', 'listele'],
            'kavrama': ['açıkla', 'özetle', 'tanımla', 'karşılaştır', 'sınıflandır', 'grupla'],
            'uygulama': ['hesapla', 'çöz', 'kullan', 'uygula', 'göster', 'bul', 'hesapla'],
            'analiz': ['analiz et', 'incele', 'ayır', 'karşılaştır', 'sınıfla', 'kategorize et'],
            'sentez': ['oluştur', 'tasarla', 'yaz', 'planla', 'birleştir', 'geliştir'],
            'değerlendirme': ['değerlendir', 'eleştir', 'yargıla', 'savun', 'karar ver', 'öncelikle']
        }
        
        # Konu anahtar kelimeleri
        self.subject_keywords = {
            'matematik': ['sayı', 'işlem', 'denklem', 'geometri', 'alan', 'çevre', 'fonksiyon'],
            'türkçe': ['anlam', 'sözcük', 'cümle', 'metin', 'şiir', 'roman', 'dil bilgisi'],
            'tarih': ['dönem', 'savaş', 'devlet', 'medeniyet', 'sultan', 'antlaşma', 'reform'],
            'coğrafya': ['iklim', 'nüfus', 'şehir', 'bölge', 'yer şekli', 'ekonomi', 'kıta'],
            'fizik': ['kuvvet', 'enerji', 'hareket', 'ışık', 'elektrik', 'manyetik', 'dalga'],
            'kimya': ['atom', 'molekül', 'reaksiyon', 'asit', 'baz', 'element', 'bileşik'],
            'biyoloji': ['hücre', 'canlı', 'organ', 'sistem', 'gen', 'protein', 'evrim']
        }
    
    def analyze_question(self, question_text: str) -> QuestionAnalysis:
        """Soruyu kapsamlı analiz et"""
        analysis = QuestionAnalysis(question_text=question_text)
        
        if not question_text:
            return analysis
        
        # Temel özellikler
        analysis = self._extract_basic_features(analysis)
        
        # Soru türünü belirle
        analysis.question_type = self._determine_question_type(question_text)
        
        # Bilişsel seviyeyi belirle
        analysis.cognitive_level = self._determine_cognitive_level(question_text)
        
        # Konu/ders belirleme
        analysis.subject = self._determine_subject(question_text)
        
        # Zorluk seviyesi
        readability_score = self.readability_analyzer.calculate_readability_score(question_text)
        analysis.estimated_difficulty = self.readability_analyzer.determine_difficulty_level(readability_score)
        
        # Dil karmaşıklığı
        complexity = self.readability_analyzer.analyze_vocabulary_complexity(question_text)
        analysis.language_complexity = complexity['complexity']
        
        # Kelime seviyesi
        if complexity['avg_word_length'] > 7:
            analysis.vocabulary_level = "ileri"
        elif complexity['avg_word_length'] > 5:
            analysis.vocabulary_level = "orta"
        else:
            analysis.vocabulary_level = "temel"
        
        # Anahtar kelimeler
        analysis.keywords = self._extract_keywords(question_text)
        
        return analysis
    
    def _extract_basic_features(self, analysis: QuestionAnalysis) -> QuestionAnalysis:
        """Temel özellikleri çıkar"""
        text = analysis.question_text
        
        # Context kontrolü
        if len(text) > 200:  # Uzun sorular genellikle context içerir
            analysis.has_context = True
            analysis.context_length = len(text)
        
        # Seçenek sayısı
        for indicator_type, indicators in self.question_indicators.items():
            if indicator_type == 'çoktan_seçmeli':
                count = sum(1 for ind in indicators if ind in text)
                if count > 0:
                    analysis.answer_choices_count = count
                    break
        
        return analysis
    
    def _determine_question_type(self, text: str) -> str:
        """Soru türünü belirle"""
        text_lower = text.lower()
        
        # Çoktan seçmeli kontrol
        choice_count = 0
        for indicator in self.question_indicators['çoktan_seçmeli']:
            if indicator in text:
                choice_count += 1
        
        if choice_count >= 4:  # En az 4 seçenek
            return 'çoktan_seçmeli'
        
        # Doğru-yanlış kontrol
        for indicator in self.question_indicators['doğru_yanlış']:
            if indicator in text_lower:
                return 'doğru_yanlış'
        
        # Açık uçlu kontrol
        for indicator in self.question_indicators['açık_uçlu']:
            if indicator in text_lower:
                return 'açık_uçlu'
        
        # Varsayılan
        if '?' in text:
            return 'açık_uçlu'
        else:
            return 'çoktan_seçmeli'
    
    def _determine_cognitive_level(self, text: str) -> str:
        """Bilişsel seviyeyi belirle (Bloom's Taxonomy)"""
        text_lower = text.lower()
        
        level_scores = {}
        for level, keywords in self.cognitive_levels.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            level_scores[level] = score
        
        if max(level_scores.values()) > 0:
            return max(level_scores, key=level_scores.get)
        
        return 'bilgi'  # Varsayılan
    
    def _determine_subject(self, text: str) -> str:
        """Ders/konu alanını belirle"""
        text_lower = text.lower()
        
        subject_scores = {}
        for subject, keywords in self.subject_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            subject_scores[subject] = score
        
        if max(subject_scores.values()) > 0:
            return max(subject_scores, key=subject_scores.get)
        
        return 'genel'  # Varsayılan
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Anahtar kelimeleri çıkar"""
        tokens = self.preprocessor.tokenize_turkish(text)
        
        # Frekans analizi
        token_freq = Counter(tokens)
        
        # En sık geçen ve önemli kelimeleri seç
        keywords = []
        for word, freq in token_freq.most_common(10):
            if (len(word) > 3 and  # Çok kısa kelimeler değil
                freq > 1 and      # En az 2 kez geçiyor
                word not in self.preprocessor.turkish_stopwords):
                keywords.append(word)
        
        return keywords[:5]  # En fazla 5 anahtar kelime


class TurkishSemanticSearch:
    """Türkçe anlamsal arama sistemi"""
    
    def __init__(self):
        self.preprocessor = TurkishTextPreprocessor()
        self.vectorizer = None
        self.document_vectors = None
        self.documents = []
        
    def index_documents(self, documents: List[str]):
        """Dokümanları indeksle"""
        self.documents = documents
        
        # Metinleri ön işle
        processed_docs = [
            ' '.join(self.preprocessor.tokenize_turkish(doc))
            for doc in documents
        ]
        
        # TF-IDF vektörizasyon
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),  # Unigram ve bigram
            min_df=2,
            max_df=0.8
        )
        
        self.document_vectors = self.vectorizer.fit_transform(processed_docs)
        
        logging.info(f"Indexed {len(documents)} documents")
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[int, str, float]]:
        """Anlamsal arama yap"""
        if not self.vectorizer or not self.document_vectors:
            return []
        
        # Sorguyu işle
        processed_query = ' '.join(self.preprocessor.tokenize_turkish(query))
        query_vector = self.vectorizer.transform([processed_query])
        
        # Benzerlik hesapla
        similarities = cosine_similarity(query_vector, self.document_vectors).flatten()
        
        # En benzer dokümanları döndür
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.1:  # Minimum benzerlik eşiği
                results.append((idx, self.documents[idx], similarities[idx]))
        
        return results
    
    def find_similar_documents(self, document_idx: int, top_k: int = 5) -> List[Tuple[int, str, float]]:
        """Benzer dokümanları bul"""
        if not self.document_vectors or document_idx >= len(self.documents):
            return []
        
        # Seçilen dokümanın vektörü
        doc_vector = self.document_vectors[document_idx]
        
        # Tüm dokümanlarla benzerlik hesapla
        similarities = cosine_similarity(doc_vector, self.document_vectors).flatten()
        
        # Kendisini hariç tut
        similarities[document_idx] = -1
        
        # En benzer dokümanları döndür
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.2:  # Minimum benzerlik eşiği
                results.append((idx, self.documents[idx], similarities[idx]))
        
        return results


class TurkishTextSummarizer:
    """Türkçe metin özetleme sistemi"""
    
    def __init__(self):
        self.preprocessor = TurkishTextPreprocessor()
    
    def extractive_summarization(self, text: str, num_sentences: int = 3) -> str:
        """Çıkarımsal özetleme"""
        if not text:
            return ""
        
        sentences = self.preprocessor.extract_sentences(text)
        
        if len(sentences) <= num_sentences:
            return text
        
        # Cümle skorlama
        sentence_scores = self._score_sentences(sentences)
        
        # En yüksek skorlu cümleleri seç
        top_sentences = sorted(
            sentence_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:num_sentences]
        
        # Orijinal sıralamayı koru
        selected_indices = sorted([sentences.index(sent) for sent, _ in top_sentences])
        summary_sentences = [sentences[i] for i in selected_indices]
        
        return ' '.join(summary_sentences)
    
    def _score_sentences(self, sentences: List[str]) -> Dict[str, float]:
        """Cümleleri skorla"""
        # Tüm cümleleri birleştirip kelime frekansı hesapla
        all_words = []
        for sentence in sentences:
            words = self.preprocessor.tokenize_turkish(sentence)
            all_words.extend(words)
        
        word_freq = Counter(all_words)
        max_freq = max(word_freq.values()) if word_freq else 1
        
        # Kelimeleri normalize et
        for word in word_freq:
            word_freq[word] = word_freq[word] / max_freq
        
        # Cümle skorları
        sentence_scores = {}
        for sentence in sentences:
            words = self.preprocessor.tokenize_turkish(sentence)
            score = sum(word_freq.get(word, 0) for word in words)
            
            if len(words) > 0:
                sentence_scores[sentence] = score / len(words)
            else:
                sentence_scores[sentence] = 0
        
        return sentence_scores
    
    def keyword_based_summary(self, text: str, keywords: List[str], num_sentences: int = 3) -> str:
        """Anahtar kelime bazlı özet"""
        sentences = self.preprocessor.extract_sentences(text)
        
        if len(sentences) <= num_sentences:
            return text
        
        # Anahtar kelime içeren cümleleri skorla
        sentence_scores = {}
        for sentence in sentences:
            score = 0
            sentence_words = self.preprocessor.tokenize_turkish(sentence.lower())
            
            for keyword in keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in sentence_words:
                    score += 2  # Tam eşleşme
                else:
                    # Kısmi eşleşme kontrolü
                    for word in sentence_words:
                        if keyword_lower in word or word in keyword_lower:
                            score += 1
            
            sentence_scores[sentence] = score
        
        # En yüksek skorlu cümleleri seç
        top_sentences = sorted(
            sentence_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:num_sentences]
        
        if not top_sentences:
            return self.extractive_summarization(text, num_sentences)
        
        # Orijinal sıralamayı koru
        selected_indices = sorted([sentences.index(sent) for sent, _ in top_sentences])
        summary_sentences = [sentences[i] for i in selected_indices]
        
        return ' '.join(summary_sentences)


class TurkishNLPPipeline:
    """Türkçe NLP ana pipeline'ı"""
    
    def __init__(self):
        self.preprocessor = TurkishTextPreprocessor()
        self.readability_analyzer = TurkishReadabilityAnalyzer()
        self.sentiment_analyzer = TurkishSentimentAnalyzer()
        self.question_analyzer = TurkishQuestionAnalyzer()
        self.semantic_search = TurkishSemanticSearch()
        self.summarizer = TurkishTextSummarizer()
        
        # Pipeline istatistikleri
        self.processed_texts = 0
        self.processing_times = []
        
    def comprehensive_text_analysis(self, text: str) -> TurkishTextAnalysis:
        """Kapsamlı metin analizi"""
        start_time = time.time()
        
        analysis = TurkishTextAnalysis(original_text=text)
        
        if not text:
            return analysis
        
        # Temel istatistikler
        sentences = self.preprocessor.extract_sentences(text)
        paragraphs = self.preprocessor.extract_paragraphs(text)
        tokens = self.preprocessor.tokenize_turkish(text, remove_stopwords=False)
        
        analysis.word_count = len(tokens)
        analysis.sentence_count = len(sentences)
        analysis.paragraph_count = len(paragraphs)
        analysis.character_count = len(text)
        
        # Kelime analizi
        unique_tokens = set(tokens)
        analysis.unique_words = len(unique_tokens)
        analysis.vocabulary_richness = len(unique_tokens) / max(1, len(tokens))
        
        token_freq = Counter(tokens)
        analysis.most_common_words = token_freq.most_common(10)
        
        # Okunabilirlik
        analysis.readability_score = self.readability_analyzer.calculate_readability_score(text)
        analysis.difficulty_level = self.readability_analyzer.determine_difficulty_level(
            analysis.readability_score
        )
        
        # Karmaşıklık indikatörleri
        complexity = self.readability_analyzer.analyze_vocabulary_complexity(text)
        analysis.complexity_indicators = complexity
        
        # Duygu analizi
        sentiment, score = self.sentiment_analyzer.analyze_sentiment(text)
        analysis.sentiment = sentiment
        analysis.sentiment_score = score
        
        # İçerik türü tahmini
        analysis.content_type = self._estimate_content_type(text)
        
        # Eğitim anahtar kelimeleri
        analysis.educational_keywords = self._extract_educational_keywords(text)
        
        # Konu tespiti (basit)
        analysis.key_topics = self._extract_key_topics(text)
        
        # İşlem süresini kaydet
        processing_time = time.time() - start_time
        self.processing_times.append(processing_time)
        self.processed_texts += 1
        
        return analysis
    
    def _estimate_content_type(self, text: str) -> ContentType:
        """İçerik türünü tahmin et"""
        text_lower = text.lower()
        
        # Soru indikatörleri
        if '?' in text or any(indicator in text_lower for indicator in ['hangi', 'ne', 'kim', 'nerede']):
            return ContentType.QUESTION
        
        # Açıklama indikatörleri
        if any(indicator in text_lower for indicator in ['açıklama', 'tanım', 'nedir', 'nasıl']):
            return ContentType.EXPLANATION
        
        # Örnek indikatörleri
        if any(indicator in text_lower for indicator in ['örnek', 'örneğin', 'mesela']):
            return ContentType.EXAMPLE
        
        # Test indikatörleri
        if any(indicator in text_lower for indicator in ['test', 'sınav', 'deneme', 'a)', 'b)', 'c)']):
            return ContentType.TEST
        
        return ContentType.THEORY  # Varsayılan
    
    def _extract_educational_keywords(self, text: str) -> List[str]:
        """Eğitim anahtar kelimelerini çıkar"""
        educational_terms = {
            'öğrenme', 'öğretim', 'eğitim', 'konu', 'ders', 'sınıf', 'okul',
            'öğrenci', 'öğretmen', 'bilgi', 'beceri', 'kavram', 'teori',
            'uygulama', 'örnek', 'problem', 'çözüm', 'analiz', 'sentez'
        }
        
        tokens = self.preprocessor.tokenize_turkish(text.lower())
        found_keywords = [token for token in tokens if token in educational_terms]
        
        return list(set(found_keywords))
    
    def _extract_key_topics(self, text: str) -> List[str]:
        """Ana konuları çıkar (basit yaklaşım)"""
        tokens = self.preprocessor.tokenize_turkish(text)
        
        # Frekans bazlı anahtar kelime çıkarımı
        token_freq = Counter(tokens)
        
        # En sık geçen ve anlamlı kelimeleri seç
        key_topics = []
        for word, freq in token_freq.most_common(5):
            if len(word) > 3 and freq > 1:
                key_topics.append(word)
        
        return key_topics
    
    def analyze_educational_content(self, content: str, content_metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Eğitim içeriği için özelleştirilmiş analiz"""
        
        # Temel analiz
        text_analysis = self.comprehensive_text_analysis(content)
        
        # Soru analizi (eğer içerik soru ise)
        question_analysis = None
        if text_analysis.content_type == ContentType.QUESTION or '?' in content:
            question_analysis = self.question_analyzer.analyze_question(content)
        
        # Özetleme
        summary = self.summarizer.extractive_summarization(content, num_sentences=2)
        
        # Sonuçları derle
        result = {
            'text_analysis': text_analysis,
            'question_analysis': question_analysis,
            'summary': summary,
            'processing_metadata': {
                'processed_at': datetime.now().isoformat(),
                'processing_time_ms': self.processing_times[-1] * 1000 if self.processing_times else 0,
                'total_processed_texts': self.processed_texts
            }
        }
        
        # Metadata varsa ekle
        if content_metadata:
            result['content_metadata'] = content_metadata
        
        return result
    
    def batch_process_educational_content(self, content_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Toplu eğitim içeriği işleme"""
        results = []
        
        for content_item in content_list:
            content_text = content_item.get('text', '')
            metadata = content_item.get('metadata', {})
            
            if content_text:
                analysis = self.analyze_educational_content(content_text, metadata)
                analysis['original_item'] = content_item
                results.append(analysis)
        
        return results
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """İşleme istatistiklerini al"""
        avg_processing_time = (
            sum(self.processing_times) / len(self.processing_times)
            if self.processing_times else 0
        )
        
        return {
            'total_processed_texts': self.processed_texts,
            'average_processing_time_ms': avg_processing_time * 1000,
            'total_processing_time_seconds': sum(self.processing_times),
            'fastest_processing_ms': min(self.processing_times) * 1000 if self.processing_times else 0,
            'slowest_processing_ms': max(self.processing_times) * 1000 if self.processing_times else 0
        }


# === KIRO2 İçin Özelleştirilmiş NLP Sistemi ===

class KIRO2TurkishNLPSystem:
    """KIRO2 için özelleştirilmiş Türkçe NLP sistemi"""
    
    def __init__(self):
        self.nlp_pipeline = TurkishNLPPipeline()
        self.content_database = []  # İçerik veritabanı simülasyonu
        
        # KIRO2 özel konfigürasyon
        self.kiro2_subjects = [
            'TYT Türkçe', 'TYT Matematik', 'TYT Fen Bilimleri', 'TYT Sosyal Bilimler',
            'AYT Matematik', 'AYT Fizik', 'AYT Kimya', 'AYT Biyoloji',
            'AYT Edebiyat', 'AYT Tarih', 'AYT Coğrafya'
        ]
        
        self.difficulty_mapping = {
            TextDifficulty.VERY_EASY: "Çok Kolay",
            TextDifficulty.EASY: "Kolay", 
            TextDifficulty.MEDIUM: "Orta",
            TextDifficulty.HARD: "Zor",
            TextDifficulty.VERY_HARD: "Çok Zor"
        }
    
    async def initialize_content_database(self, content_data: List[Dict[str, Any]]):
        """İçerik veritabanını başlat"""
        self.content_database = content_data
        
        # Semantic search için içerikleri indeksle
        content_texts = [item.get('text', '') for item in content_data]
        self.nlp_pipeline.semantic_search.index_documents(content_texts)
        
        logging.info(f"KIRO2 content database initialized with {len(content_data)} items")
    
    async def analyze_question_for_kiro2(self, question_text: str, 
                                       subject: str, expected_difficulty: str = None) -> Dict[str, Any]:
        """KIRO2 için soru analizi"""
        
        # Kapsamlı analiz
        analysis_result = self.nlp_pipeline.analyze_educational_content(question_text)
        
        # KIRO2 özel değerlendirmeler
        kiro2_insights = {
            'subject_match': self._verify_subject_alignment(question_text, subject),
            'difficulty_assessment': self._assess_difficulty_for_kiro2(analysis_result['text_analysis']),
            'educational_quality': self._evaluate_educational_quality(analysis_result),
            'student_engagement': self._predict_student_engagement(analysis_result),
            'content_suggestions': self._generate_content_suggestions(analysis_result)
        }
        
        # Zorluk uyumu kontrolü
        if expected_difficulty:
            kiro2_insights['difficulty_alignment'] = self._check_difficulty_alignment(
                analysis_result['text_analysis'], expected_difficulty
            )
        
        return {
            'question_text': question_text,
            'subject': subject,
            'nlp_analysis': analysis_result,
            'kiro2_insights': kiro2_insights,
            'recommendations': self._generate_kiro2_recommendations(analysis_result, kiro2_insights)
        }
    
    def _verify_subject_alignment(self, text: str, expected_subject: str) -> Dict[str, Any]:
        """Konu uyumunu doğrula"""
        question_analysis = self.nlp_pipeline.question_analyzer.analyze_question(text)
        detected_subject = question_analysis.subject
        
        # Konu eşleştirme
        subject_mapping = {
            'matematik': ['TYT Matematik', 'AYT Matematik'],
            'türkçe': ['TYT Türkçe', 'AYT Edebiyat'],
            'fizik': ['TYT Fen Bilimleri', 'AYT Fizik'],
            'tarih': ['TYT Sosyal Bilimler', 'AYT Tarih'],
            'coğrafya': ['TYT Sosyal Bilimler', 'AYT Coğrafya'],
            'kimya': ['TYT Fen Bilimleri', 'AYT Kimya'],
            'biyoloji': ['TYT Fen Bilimleri', 'AYT Biyoloji']
        }
        
        expected_subjects = subject_mapping.get(detected_subject, [])
        is_aligned = expected_subject in expected_subjects or detected_subject == 'genel'
        
        return {
            'detected_subject': detected_subject,
            'expected_subject': expected_subject,
            'is_aligned': is_aligned,
            'confidence': 0.8 if is_aligned else 0.3,
            'suggested_subjects': expected_subjects
        }
    
    def _assess_difficulty_for_kiro2(self, text_analysis: TurkishTextAnalysis) -> Dict[str, Any]:
        """KIRO2 için zorluk değerlendirmesi"""
        base_difficulty = text_analysis.difficulty_level
        
        # KIRO2 kriterlerine göre ayarlama
        adjustments = []
        final_difficulty = base_difficulty
        
        # Kelime sayısı faktörü
        if text_analysis.word_count > 100:
            adjustments.append("Uzun metin - zorluk artırıldı")
            if base_difficulty.value < 5:
                final_difficulty = TextDifficulty(base_difficulty.value + 1)
        
        # Kelime dağarcığı zenginliği
        if text_analysis.vocabulary_richness > 0.8:
            adjustments.append("Zengin kelime dağarcığı - zorluk artırıldı")
            if base_difficulty.value < 5:
                final_difficulty = TextDifficulty(min(5, base_difficulty.value + 1))
        
        # Karmaşıklık göstergeleri
        if text_analysis.complexity_indicators.get('complexity', 0) > 0.7:
            adjustments.append("Yüksek dil karmaşıklığı tespit edildi")
        
        return {
            'base_difficulty': self.difficulty_mapping[base_difficulty],
            'final_difficulty': self.difficulty_mapping[final_difficulty],
            'adjustments': adjustments,
            'readability_score': text_analysis.readability_score,
            'complexity_score': text_analysis.complexity_indicators.get('complexity', 0)
        }
    
    def _evaluate_educational_quality(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Eğitsel kalite değerlendirmesi"""
        text_analysis = analysis_result['text_analysis']
        
        quality_score = 0.0
        quality_factors = []
        
        # Metin uzunluğu uygunluğu
        if 50 <= text_analysis.word_count <= 200:
            quality_score += 0.2
            quality_factors.append("Uygun metin uzunluğu")
        
        # Kelime dağarcığı zenginliği
        if 0.4 <= text_analysis.vocabulary_richness <= 0.8:
            quality_score += 0.2
            quality_factors.append("Dengeli kelime dağarcığı")
        
        # Eğitim anahtar kelimeleri varlığı
        if text_analysis.educational_keywords:
            quality_score += 0.2
            quality_factors.append("Eğitim terminolojisi kullanımı")
        
        # Duygu analizi - eğitsel uygunluk
        if text_analysis.sentiment in [SentimentType.EDUCATIONAL, SentimentType.NEUTRAL]:
            quality_score += 0.2
            quality_factors.append("Eğitim için uygun duygu tonu")
        
        # Okunabilirlik skoru
        if text_analysis.readability_score >= 40:
            quality_score += 0.2
            quality_factors.append("Kabul edilebilir okunabilirlik")
        
        quality_level = "Yüksek" if quality_score >= 0.8 else "Orta" if quality_score >= 0.6 else "Düşük"
        
        return {
            'quality_score': quality_score,
            'quality_level': quality_level,
            'quality_factors': quality_factors,
            'improvement_needed': quality_score < 0.6
        }
    
    def _predict_student_engagement(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Öğrenci katılım tahmini"""
        text_analysis = analysis_result['text_analysis']
        
        engagement_score = 0.0
        engagement_factors = []
        
        # Motivasyonel içerik
        if text_analysis.sentiment == SentimentType.MOTIVATIONAL:
            engagement_score += 0.3
            engagement_factors.append("Motivasyonel dil kullanımı")
        
        # Uygun zorluk seviyesi
        if text_analysis.difficulty_level in [TextDifficulty.EASY, TextDifficulty.MEDIUM]:
            engagement_score += 0.2
            engagement_factors.append("Öğrenci seviyesine uygun zorluk")
        
        # Pratik örnekler varlığı
        if text_analysis.content_type == ContentType.EXAMPLE:
            engagement_score += 0.2
            engagement_factors.append("Pratik örnek içeriği")
        
        # Metin uzunluğu - çok uzun metinler sıkıcı olabilir
        if text_analysis.word_count <= 150:
            engagement_score += 0.15
            engagement_factors.append("Optimal metin uzunluğu")
        
        # Soru formatı - interaktif içerik
        if text_analysis.content_type == ContentType.QUESTION:
            engagement_score += 0.15
            engagement_factors.append("İnteraktif soru formatı")
        
        engagement_level = (
            "Yüksek" if engagement_score >= 0.7 else 
            "Orta" if engagement_score >= 0.5 else 
            "Düşük"
        )
        
        return {
            'engagement_score': engagement_score,
            'engagement_level': engagement_level,
            'engagement_factors': engagement_factors,
            'predicted_attention_duration': f"{min(300, max(60, text_analysis.word_count * 2))} saniye"
        }
    
    def _check_difficulty_alignment(self, text_analysis: TurkishTextAnalysis, 
                                  expected_difficulty: str) -> Dict[str, Any]:
        """Zorluk seviyesi uyumunu kontrol et"""
        actual_difficulty = text_analysis.difficulty_level
        
        difficulty_values = {
            "Çok Kolay": 1, "Kolay": 2, "Orta": 3, "Zor": 4, "Çok Zor": 5
        }
        
        expected_value = difficulty_values.get(expected_difficulty, 3)
        actual_value = actual_difficulty.value
        
        difference = abs(expected_value - actual_value)
        
        if difference == 0:
            alignment = "Mükemmel"
        elif difference == 1:
            alignment = "İyi"
        elif difference == 2:
            alignment = "Kabul Edilebilir"
        else:
            alignment = "Uyumsuz"
        
        return {
            'expected_difficulty': expected_difficulty,
            'actual_difficulty': self.difficulty_mapping[actual_difficulty],
            'alignment': alignment,
            'difference': difference,
            'needs_adjustment': difference > 1
        }
    
    def _generate_content_suggestions(self, analysis_result: Dict[str, Any]) -> List[str]:
        """İçerik geliştirme önerileri"""
        text_analysis = analysis_result['text_analysis']
        suggestions = []
        
        # Okunabilirlik önerileri
        if text_analysis.readability_score < 40:
            suggestions.append("Daha basit kelimeler kullanarak okunabilirliği artırın")
            suggestions.append("Cümle uzunluklarını kısaltmayı düşünün")
        
        # Kelime dağarcığı önerileri
        if text_analysis.vocabulary_richness < 0.3:
            suggestions.append("Daha zengin kelime dağarcığı kullanın")
        elif text_analysis.vocabulary_richness > 0.8:
            suggestions.append("Aynı kelimelerin tekrarını azaltın")
        
        # İçerik türü önerileri
        if text_analysis.content_type == ContentType.THEORY:
            suggestions.append("Pratik örnekler ekleyerek içeriği zenginleştirin")
        
        # Duygu tonu önerileri
        if text_analysis.sentiment == SentimentType.NEGATIVE:
            suggestions.append("Daha pozitif ve motive edici dil kullanın")
        
        # Uzunluk önerileri
        if text_analysis.word_count > 250:
            suggestions.append("Metni daha kısa ve öz hale getirin")
        elif text_analysis.word_count < 30:
            suggestions.append("İçeriği daha detaylı açıklamalarla genişletin")
        
        return suggestions
    
    def _generate_kiro2_recommendations(self, analysis_result: Dict[str, Any], 
                                      kiro2_insights: Dict[str, Any]) -> List[str]:
        """KIRO2 önerileri oluştur"""
        recommendations = []
        
        # Konu uyumu
        subject_alignment = kiro2_insights['subject_match']
        if not subject_alignment['is_aligned']:
            recommendations.append(
                f"⚠️ Konu uyumsuzluğu: {subject_alignment['suggested_subjects'][0] if subject_alignment['suggested_subjects'] else 'İlgili konuyu'} kontrol edin"
            )
        
        # Zorluk seviyesi
        difficulty = kiro2_insights['difficulty_assessment']
        if 'adjustment' in difficulty and difficulty['adjustments']:
            recommendations.append(f"[CHART] Zorluk seviyesi: {difficulty['final_difficulty']}")
        
        # Eğitsel kalite
        quality = kiro2_insights['educational_quality']
        if quality['improvement_needed']:
            recommendations.append("[BOOKS] Eğitsel kaliteyi artırmak için iyileştirmeler gerekli")
        
        # Öğrenci katılımı
        engagement = kiro2_insights['student_engagement']
        if engagement['engagement_level'] == 'Düşük':
            recommendations.append("[TARGET] Öğrenci katılımını artıracak unsurlar ekleyin")
        
        # İçerik önerileri
        content_suggestions = kiro2_insights['content_suggestions']
        if content_suggestions:
            recommendations.extend([f"[BULB] {suggestion}" for suggestion in content_suggestions[:2]])
        
        return recommendations[:5]  # En fazla 5 öneri
    
    async def find_similar_content(self, query_text: str, subject: str = None,
                                 top_k: int = 5) -> List[Dict[str, Any]]:
        """Benzer içerik arama"""
        if not self.content_database:
            return []
        
        # Semantic search
        search_results = self.nlp_pipeline.semantic_search.search(query_text, top_k * 2)
        
        # Sonuçları filtrele ve zenginleştir
        filtered_results = []
        for idx, content_text, similarity in search_results:
            if idx < len(self.content_database):
                content_item = self.content_database[idx]
                
                # Konu filtresi
                if subject and content_item.get('subject') != subject:
                    continue
                
                # Analiz ekle
                analysis = self.nlp_pipeline.comprehensive_text_analysis(content_text)
                
                filtered_results.append({
                    'content_item': content_item,
                    'similarity_score': similarity,
                    'text_analysis': analysis,
                    'content_text': content_text
                })
                
                if len(filtered_results) >= top_k:
                    break
        
        return filtered_results
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Sistem istatistikleri"""
        nlp_stats = self.nlp_pipeline.get_processing_statistics()
        
        return {
            'content_database_size': len(self.content_database),
            'supported_subjects': self.kiro2_subjects,
            'nlp_processing_stats': nlp_stats,
            'system_features': [
                'Türkçe metin analizi',
                'Soru analizi ve kategorilendirme',
                'Zorluk seviyesi tespiti',
                'Duygu analizi',
                'Anlamsal arama',
                'Metin özetleme',
                'Eğitsel kalite değerlendirmesi'
            ]
        }


# === Örnek Kullanım ===

async def example_kiro2_turkish_nlp():
    """KIRO2 Türkçe NLP sistemi örneği"""
    
    # NLP sistemini başlat
    kiro2_nlp = KIRO2TurkishNLPSystem()
    
    print("🇹🇷 KIRO2 Türkçe NLP Sistemi Başlatılıyor...")
    
    # Örnek içerik veritabanı
    sample_content = [
        {
            'id': 1,
            'subject': 'TYT Matematik',
            'text': 'Bir sayının %20\'si 40 ise, bu sayının %30\'u kaçtır? A) 50 B) 60 C) 70 D) 80',
            'difficulty': 'Orta',
            'type': 'soru'
        },
        {
            'id': 2,
            'subject': 'TYT Türkçe',
            'text': 'Aşağıdaki cümlede altı çizili sözcük hangi anlamda kullanılmıştır? "Onun yüzü asıktı." A) Üzgün B) Ciddi C) Kızgın D) Sessiz',
            'difficulty': 'Kolay',
            'type': 'soru'
        },
        {
            'id': 3,
            'subject': 'AYT Tarih',
            'text': 'Osmanlı İmparatorluğu\'nda Tanzimat Fermanı\'nın ilan edilme sebepleri nelerdir? Bu reform hareketinin toplumsal ve ekonomik sonuçlarını değerlendiriniz.',
            'difficulty': 'Zor',
            'type': 'soru'
        }
    ]
    
    # İçerik veritabanını başlat
    await kiro2_nlp.initialize_content_database(sample_content)
    
    print("[CHECK] İçerik veritabanı yüklendi!")
    
    # Örnek soru analizi
    test_question = """
    Aşağıdaki metni okuyarak soruları cevaplayınız:
    
    "Teknolojinin hızla gelişmesi, eğitim sistemlerinde de köklü değişikliklere yol açmıştır. 
    Geleneksel öğretim yöntemleri yerini dijital platformlara bırakmaya başlamıştır. 
    Bu değişim, öğrencilerin öğrenme alışkanlıklarını da etkilemektedir."
    
    Bu metne göre, teknolojinin eğitime etkisi ile ilgili aşağıdakilerden hangisi söylenemez?
    A) Eğitim sistemlerinde değişiklikler yaratmıştır
    B) Geleneksel yöntemler hâlâ dominant durumda kalmaya devam etmektedir  
    C) Dijital platformlar önem kazanmıştır
    D) Öğrenci davranışları değişmektedir
    """
    
    # Soru analizi yap
    print("\n[MEMO] Soru Analizi Başlatılıyor...")
    
    analysis_result = await kiro2_nlp.analyze_question_for_kiro2(
        question_text=test_question,
        subject='TYT Türkçe',
        expected_difficulty='Orta'
    )
    
    print(f"\n[MAG] Analiz Sonuçları:")
    print(f"Konu: {analysis_result['subject']}")
    
    # NLP analizi
    nlp_analysis = analysis_result['nlp_analysis']['text_analysis']
    print(f"\n[CHART] Metin İstatistikleri:")
    print(f"  Kelime sayısı: {nlp_analysis.word_count}")
    print(f"  Cümle sayısı: {nlp_analysis.sentence_count}")
    print(f"  Okunabilirlik skoru: {nlp_analysis.readability_score:.1f}")
    print(f"  Zorluk seviyesi: {kiro2_nlp.difficulty_mapping[nlp_analysis.difficulty_level]}")
    print(f"  Duygu tonu: {nlp_analysis.sentiment.value}")
    
    # Soru analizi
    question_analysis = analysis_result['nlp_analysis']['question_analysis']
    if question_analysis:
        print(f"\n❓ Soru Özellikleri:")
        print(f"  Soru türü: {question_analysis.question_type}")
        print(f"  Bilişsel seviye: {question_analysis.cognitive_level}")
        print(f"  Tespit edilen konu: {question_analysis.subject}")
        print(f"  Seçenek sayısı: {question_analysis.answer_choices_count}")
    
    # KIRO2 içgörüleri
    kiro2_insights = analysis_result['kiro2_insights']
    print(f"\n[TARGET] KIRO2 Değerlendirmesi:")
    
    subject_match = kiro2_insights['subject_match']
    print(f"  Konu uyumu: {'[CHECK]' if subject_match['is_aligned'] else '[X]'}")
    
    difficulty = kiro2_insights['difficulty_assessment']
    print(f"  Final zorluk: {difficulty['final_difficulty']}")
    
    quality = kiro2_insights['educational_quality']
    print(f"  Eğitsel kalite: {quality['quality_level']} ({quality['quality_score']:.2f})")
    
    engagement = kiro2_insights['student_engagement']
    print(f"  Öğrenci katılım tahmini: {engagement['engagement_level']}")
    print(f"  Tahmin edilen dikkat süresi: {engagement['predicted_attention_duration']}")
    
    # Öneriler
    print(f"\n[BULB] KIRO2 Önerileri:")
    for i, rec in enumerate(analysis_result['recommendations'], 1):
        print(f"  {i}. {rec}")
    
    # Özet
    summary = analysis_result['nlp_analysis']['summary']
    print(f"\n[CLIPBOARD] Metin Özeti:")
    print(f"  {summary}")
    
    # Benzer içerik arama
    print(f"\n[MAG] Benzer İçerik Arama:")
    similar_content = await kiro2_nlp.find_similar_content(
        "matematik yüzde hesaplama", 
        subject='TYT Matematik', 
        top_k=2
    )
    
    for i, content in enumerate(similar_content, 1):
        print(f"  {i}. Benzerlik: {content['similarity_score']:.3f}")
        print(f"     İçerik: {content['content_text'][:100]}...")
    
    # Sistem istatistikleri
    stats = kiro2_nlp.get_system_statistics()
    print(f"\n[TRENDING_UP] Sistem İstatistikleri:")
    print(f"  İçerik veritabanı: {stats['content_database_size']} öğe")
    print(f"  Desteklenen dersler: {len(stats['supported_subjects'])}")
    print(f"  İşlenen metin sayısı: {stats['nlp_processing_stats']['total_processed_texts']}")
    print(f"  Ortalama işlem süresi: {stats['nlp_processing_stats']['average_processing_time_ms']:.1f}ms")
    
    print(f"\n✨ KIRO2 Türkçe NLP sistemi analizi tamamlandı!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(example_kiro2_turkish_nlp())