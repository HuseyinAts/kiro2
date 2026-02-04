"""
KIRO2 - Adaptive Learning Algorithms
====================================

Bu modül, öğrencilerin bireysel öğrenme stillerine ve performanslarına göre
kişiselleştirilmiş eğitim deneyimi sunan adaptif öğrenme algoritmalarını içerir.

Adaptif Öğrenme Bileşenleri:
- Knowledge Tracing (Bilgi İzleme)
- Item Response Theory (IRT) 
- Bayesian Knowledge Tracing (BKT)
- Deep Knowledge Tracing (DKT)
- Difficulty Adaptation Algorithm
- Learning Path Optimization
- Spaced Repetition Algorithm
- Zone of Proximal Development (ZPD) Targeting

TYT/AYT/YKS Sınavlarına Özelleştirilmiş:
- Türk eğitim müfredatına uygun konu hiyerarşisi
- Sınav odaklı zorluk seviyelendirmesi
- Öğrenci motivasyon algoritmaları
- Başarı tahmini ve müdahale sistemi
"""

import asyncio
import logging
import math
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
from scipy.optimize import minimize

# Advanced ML için
try:
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False
    logging.warning("PyTorch not available - some adaptive learning features disabled")


class LearningObjectiveType(Enum):
    """Öğrenme hedefi türleri"""
    CONCEPT = "concept"              # Kavram öğrenme
    SKILL = "skill"                  # Beceri geliştirme
    PROBLEM_SOLVING = "problem_solving"  # Problem çözme
    MEMORIZATION = "memorization"    # Ezber
    APPLICATION = "application"      # Uygulama
    ANALYSIS = "analysis"           # Analiz
    SYNTHESIS = "synthesis"         # Sentez


class DifficultyLevel(Enum):
    """Zorluk seviyeleri"""
    VERY_EASY = 1
    EASY = 2
    MEDIUM = 3
    HARD = 4
    VERY_HARD = 5


class LearningStyle(Enum):
    """Öğrenme stilleri"""
    VISUAL = "visual"               # Görsel öğrenme
    AUDITORY = "auditory"           # İşitsel öğrenme
    KINESTHETIC = "kinesthetic"     # Kinestetik öğrenme
    READ_WRITE = "read_write"       # Okuma-yazma
    MULTIMODAL = "multimodal"       # Çoklu modal


class MasteryLevel(Enum):
    """Ustalık seviyeleri"""
    NOT_STARTED = 0
    INTRODUCED = 1
    DEVELOPING = 2
    PROFICIENT = 3
    MASTERED = 4
    EXPERT = 5


@dataclass
class LearningObjective:
    """Öğrenme hedefi"""
    objective_id: str
    name: str
    subject: str              # TYT Matematik, AYT Fizik, vb.
    topic: str               # Alt konu
    objective_type: LearningObjectiveType
    difficulty_level: DifficultyLevel
    prerequisites: List[str] = field(default_factory=list)  # Önkoşul hedefler
    estimated_time_minutes: int = 30
    bloom_taxonomy_level: int = 1  # 1-6 arası (Bloom'un taksonomisi)
    
    def __post_init__(self):
        if not self.objective_id:
            self.objective_id = f"obj_{uuid.uuid4().hex[:8]}"


@dataclass
class StudentResponse:
    """Öğrenci yanıt verisi"""
    response_id: str
    student_id: str
    objective_id: str
    question_id: str
    is_correct: bool
    response_time_seconds: float
    difficulty_level: DifficultyLevel
    timestamp: datetime = field(default_factory=datetime.now)
    hint_used: bool = False
    attempts_count: int = 1
    confidence_level: Optional[float] = None  # 0-1 arası
    
    def __post_init__(self):
        if not self.response_id:
            self.response_id = f"resp_{int(time.time())}_{uuid.uuid4().hex[:8]}"


@dataclass
class StudentKnowledgeState:
    """Öğrenci bilgi durumu"""
    student_id: str
    objective_id: str
    mastery_probability: float  # 0-1 arası ustalık olasılığı
    mastery_level: MasteryLevel
    confidence: float          # Model güveni
    last_updated: datetime = field(default_factory=datetime.now)
    response_count: int = 0
    correct_responses: int = 0
    streak_correct: int = 0    # Ardışık doğru sayısı
    streak_incorrect: int = 0  # Ardışık yanlış sayısı
    time_spent_minutes: float = 0.0
    
    @property
    def accuracy_rate(self) -> float:
        return self.correct_responses / max(1, self.response_count)


@dataclass
class AdaptationDecision:
    """Adaptasyon kararı"""
    student_id: str
    decision_type: str        # "difficulty_up", "difficulty_down", "concept_review", etc.
    current_objective: str
    recommended_objective: str
    reasoning: str
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)


class BayesianKnowledgeTracing:
    """Bayesian Bilgi İzleme Algoritması"""
    
    def __init__(self, 
                 p_learn: float = 0.3,      # Öğrenme oranı
                 p_guess: float = 0.25,     # Tahmin oranı
                 p_slip: float = 0.1,       # Sürçme oranı
                 p_transit: float = 0.1):   # Geçiş oranı
        self.p_learn = p_learn
        self.p_guess = p_guess
        self.p_slip = p_slip
        self.p_transit = p_transit
        
        # Öğrenci bilgi durumları
        self.knowledge_states: Dict[str, Dict[str, StudentKnowledgeState]] = defaultdict(dict)
        
    def update_knowledge_state(self, response: StudentResponse) -> StudentKnowledgeState:
        """Öğrenci yanıtına göre bilgi durumunu güncelle"""
        key = f"{response.student_id}_{response.objective_id}"
        
        if key not in self.knowledge_states:
            # İlk durum
            self.knowledge_states[key] = StudentKnowledgeState(
                student_id=response.student_id,
                objective_id=response.objective_id,
                mastery_probability=0.5,  # Başlangıç olasılığı
                mastery_level=MasteryLevel.NOT_STARTED,
                confidence=0.5
            )
        
        state = self.knowledge_states[key]
        
        # BKT güncellemesi
        prior_knowledge = state.mastery_probability
        
        if response.is_correct:
            # Doğru yanıt durumunda
            likelihood = prior_knowledge * (1 - self.p_slip) + (1 - prior_knowledge) * self.p_guess
            posterior = (prior_knowledge * (1 - self.p_slip)) / likelihood
            state.streak_correct += 1
            state.streak_incorrect = 0
            state.correct_responses += 1
        else:
            # Yanlış yanıt durumunda
            likelihood = prior_knowledge * self.p_slip + (1 - prior_knowledge) * (1 - self.p_guess)
            posterior = (prior_knowledge * self.p_slip) / likelihood
            state.streak_incorrect += 1
            state.streak_correct = 0
        
        # Öğrenme geçişi
        state.mastery_probability = posterior + (1 - posterior) * self.p_learn
        
        # İstatistikleri güncelle
        state.response_count += 1
        state.time_spent_minutes += response.response_time_seconds / 60.0
        state.last_updated = datetime.now()
        
        # Ustalık seviyesini güncelle
        state.mastery_level = self._determine_mastery_level(state.mastery_probability)
        
        # Model güvenini hesapla
        state.confidence = self._calculate_confidence(state)
        
        self.knowledge_states[key] = state
        return state
    
    def _determine_mastery_level(self, mastery_prob: float) -> MasteryLevel:
        """Ustalık olasılığından seviye belirle"""
        if mastery_prob >= 0.9:
            return MasteryLevel.EXPERT
        elif mastery_prob >= 0.8:
            return MasteryLevel.MASTERED
        elif mastery_prob >= 0.65:
            return MasteryLevel.PROFICIENT
        elif mastery_prob >= 0.4:
            return MasteryLevel.DEVELOPING
        elif mastery_prob >= 0.1:
            return MasteryLevel.INTRODUCED
        else:
            return MasteryLevel.NOT_STARTED
    
    def _calculate_confidence(self, state: StudentKnowledgeState) -> float:
        """Model güvenini hesapla"""
        # Yanıt sayısı ve tutarlılık üzerinden güven hesapla
        response_factor = min(1.0, state.response_count / 10.0)  # 10 yanıtta maksimum güven
        
        # Tutarlılık faktörü
        if state.response_count > 1:
            consistency_factor = abs(state.accuracy_rate - 0.5) * 2  # 0.5'ten uzaklık
        else:
            consistency_factor = 0.0
        
        return min(1.0, response_factor * 0.7 + consistency_factor * 0.3)
    
    def get_mastery_probability(self, student_id: str, objective_id: str) -> float:
        """Ustalık olasılığını al"""
        key = f"{student_id}_{objective_id}"
        if key in self.knowledge_states:
            return self.knowledge_states[key].mastery_probability
        return 0.0  # Bilinmeyen durumda


class ItemResponseTheory:
    """Madde Tepki Kuramı (IRT) Algoritması"""
    
    def __init__(self):
        # Sorular için parametreler
        self.item_parameters: Dict[str, Dict[str, float]] = {}
        # Öğrenciler için yetenek parametreleri  
        self.student_abilities: Dict[str, float] = {}
        
    def estimate_item_parameters(self, responses: List[StudentResponse]) -> Dict[str, Dict[str, float]]:
        """Soru parametrelerini tahmin et (2PL Model)"""
        
        # Sorular ve öğrencileri topla
        items = set(r.question_id for r in responses)
        students = set(r.student_id for r in responses)
        
        # Yanıt matrisi oluştur
        response_matrix = {}
        for response in responses:
            key = (response.student_id, response.question_id)
            response_matrix[key] = 1 if response.is_correct else 0
        
        # Her soru için parametreleri hesapla
        for item_id in items:
            item_responses = [(r.student_id, r.is_correct) for r in responses if r.question_id == item_id]
            
            if len(item_responses) < 5:  # Minimum yanıt sayısı
                # Varsayılan parametreler
                self.item_parameters[item_id] = {
                    'difficulty': 0.0,    # b parametresi
                    'discrimination': 1.0  # a parametresi
                }
                continue
            
            # Basit yaklaşım: doğruluk oranından zorluk hesapla
            correct_rate = sum(resp[1] for resp in item_responses) / len(item_responses)
            
            # Logit dönüşümü ile zorluk parametresi
            if correct_rate == 0:
                difficulty = 3.0
            elif correct_rate == 1:
                difficulty = -3.0
            else:
                difficulty = -math.log(correct_rate / (1 - correct_rate))
            
            # Ayırıcılık gücü (basit yaklaşım)
            discrimination = max(0.5, min(2.0, 1.0 + (0.5 - abs(correct_rate - 0.5))))
            
            self.item_parameters[item_id] = {
                'difficulty': difficulty,
                'discrimination': discrimination
            }
        
        return self.item_parameters
    
    def estimate_student_ability(self, student_id: str, responses: List[StudentResponse]) -> float:
        """Öğrenci yeteneğini tahmin et"""
        student_responses = [r for r in responses if r.student_id == student_id]
        
        if not student_responses:
            return 0.0
        
        # Maximum Likelihood Estimation yaklaşımı
        def likelihood_function(ability):
            log_likelihood = 0
            for response in student_responses:
                if response.question_id not in self.item_parameters:
                    continue
                    
                params = self.item_parameters[response.question_id]
                a = params['discrimination']
                b = params['difficulty']
                
                # 2PL model probability
                prob = 1 / (1 + math.exp(-a * (ability - b)))
                
                if response.is_correct:
                    log_likelihood += math.log(max(1e-10, prob))
                else:
                    log_likelihood += math.log(max(1e-10, 1 - prob))
            
            return -log_likelihood  # Minimize etmek için negatif
        
        # Optimizasyon
        result = minimize(likelihood_function, x0=[0.0], method='BFGS', 
                         options={'maxiter': 100})
        
        ability = result.x[0]
        self.student_abilities[student_id] = ability
        return ability
    
    def predict_response_probability(self, student_id: str, question_id: str) -> float:
        """Öğrenci yanıt olasılığını tahmin et"""
        if student_id not in self.student_abilities:
            return 0.5  # Bilinmeyen durum
        
        if question_id not in self.item_parameters:
            return 0.5  # Bilinmeyen soru
        
        ability = self.student_abilities[student_id]
        params = self.item_parameters[question_id]
        
        # 2PL model
        a = params['discrimination']
        b = params['difficulty']
        prob = 1 / (1 + math.exp(-a * (ability - b)))
        
        return prob


class DifficultyAdaptationEngine:
    """Zorluk Seviyesi Adaptasyon Motoru"""
    
    def __init__(self):
        self.target_success_rate = 0.75  # Hedef başarı oranı
        self.adaptation_threshold = 0.15  # Adaptasyon eşiği
        self.window_size = 5  # Değerlendirme penceresi
        
    def should_adapt_difficulty(self, recent_responses: List[StudentResponse]) -> Optional[AdaptationDecision]:
        """Zorluk seviyesi adaptasyonu gerekli mi?"""
        if len(recent_responses) < self.window_size:
            return None
        
        # Son yanıtları değerlendir
        recent_responses = sorted(recent_responses, key=lambda x: x.timestamp)[-self.window_size:]
        success_rate = sum(1 for r in recent_responses if r.is_correct) / len(recent_responses)
        avg_response_time = sum(r.response_time_seconds for r in recent_responses) / len(recent_responses)
        
        student_id = recent_responses[0].student_id
        current_difficulty = recent_responses[-1].difficulty_level
        
        # Karar verme mantığı
        if success_rate > self.target_success_rate + self.adaptation_threshold:
            # Çok kolay - zorlaştır
            if current_difficulty != DifficultyLevel.VERY_HARD:
                new_difficulty = DifficultyLevel(min(5, current_difficulty.value + 1))
                return AdaptationDecision(
                    student_id=student_id,
                    decision_type="difficulty_up",
                    current_objective=recent_responses[-1].objective_id,
                    recommended_objective=recent_responses[-1].objective_id,
                    reasoning=f"Başarı oranı çok yüksek ({success_rate:.2f}), zorluk artırılmalı",
                    confidence=min(1.0, (success_rate - self.target_success_rate) * 2)
                )
        
        elif success_rate < self.target_success_rate - self.adaptation_threshold:
            # Çok zor - kolaylaştır  
            if current_difficulty != DifficultyLevel.VERY_EASY:
                new_difficulty = DifficultyLevel(max(1, current_difficulty.value - 1))
                return AdaptationDecision(
                    student_id=student_id,
                    decision_type="difficulty_down",
                    current_objective=recent_responses[-1].objective_id,
                    recommended_objective=recent_responses[-1].objective_id,
                    reasoning=f"Başarı oranı çok düşük ({success_rate:.2f}), zorluk azaltılmalı",
                    confidence=min(1.0, (self.target_success_rate - success_rate) * 2)
                )
        
        # Yanıt süresi faktörü
        if avg_response_time > 120 and success_rate < 0.6:  # 2 dakikadan fazla ve düşük başarı
            return AdaptationDecision(
                student_id=student_id,
                decision_type="concept_review",
                current_objective=recent_responses[-1].objective_id,
                recommended_objective=recent_responses[-1].objective_id,
                reasoning="Uzun yanıt süresi ve düşük başarı - kavram tekrarı öneriliyor",
                confidence=0.8
            )
        
        return None


class SpacedRepetitionAlgorithm:
    """Aralıklı Tekrar Algoritması (SM-2 algoritması benzeri)"""
    
    def __init__(self):
        # Öğrenci-konu çiftleri için tekrar programı
        self.repetition_schedule: Dict[str, Dict[str, Any]] = {}
        
    def calculate_next_review(self, student_id: str, objective_id: str, 
                            performance_quality: float) -> datetime:
        """Sonraki tekrar zamanını hesapla"""
        key = f"{student_id}_{objective_id}"
        
        if key not in self.repetition_schedule:
            # İlk tekrar
            self.repetition_schedule[key] = {
                'interval': 1,        # Gün cinsinden
                'repetition': 0,      # Tekrar sayısı
                'easiness': 2.5,      # Kolaylık faktörü (1.3-2.5 arası)
                'last_review': datetime.now()
            }
        
        schedule = self.repetition_schedule[key]
        
        # SM-2 algoritması
        if performance_quality >= 3:  # Başarılı yanıt (0-5 arası skala)
            if schedule['repetition'] == 0:
                schedule['interval'] = 1
            elif schedule['repetition'] == 1:
                schedule['interval'] = 6
            else:
                schedule['interval'] = int(schedule['interval'] * schedule['easiness'])
            
            schedule['repetition'] += 1
        else:
            # Başarısız yanıt - baştan başla
            schedule['repetition'] = 0
            schedule['interval'] = 1
        
        # Kolaylık faktörünü güncelle
        schedule['easiness'] = max(1.3, 
            schedule['easiness'] + (0.1 - (5 - performance_quality) * (0.08 + (5 - performance_quality) * 0.02))
        )
        
        # Sonraki tekrar tarihi
        next_review = datetime.now() + timedelta(days=schedule['interval'])
        schedule['last_review'] = datetime.now()
        
        return next_review
    
    def get_due_reviews(self, student_id: str) -> List[str]:
        """Süresi gelen tekrarları al"""
        now = datetime.now()
        due_objectives = []
        
        for key, schedule in self.repetition_schedule.items():
            if key.startswith(f"{student_id}_"):
                next_review = schedule['last_review'] + timedelta(days=schedule['interval'])
                if next_review <= now:
                    objective_id = key.split('_', 1)[1]
                    due_objectives.append(objective_id)
        
        return due_objectives


class LearningPathOptimizer:
    """Öğrenme Yolu Optimizasyon Algoritması"""
    
    def __init__(self):
        self.knowledge_graph: Dict[str, List[str]] = {}  # Önkoşul graf
        self.learning_objectives: Dict[str, LearningObjective] = {}
        
    def add_learning_objective(self, objective: LearningObjective):
        """Öğrenme hedefi ekle"""
        self.learning_objectives[objective.objective_id] = objective
        
        # Graf güncellemesi
        if objective.objective_id not in self.knowledge_graph:
            self.knowledge_graph[objective.objective_id] = []
        
        # Önkoşulları ekle
        for prereq in objective.prerequisites:
            if prereq not in self.knowledge_graph:
                self.knowledge_graph[prereq] = []
            self.knowledge_graph[prereq].append(objective.objective_id)
    
    def generate_learning_path(self, student_id: str, target_objectives: List[str],
                             knowledge_tracer: BayesianKnowledgeTracing) -> List[str]:
        """Kişiselleştirilmiş öğrenme yolu oluştur"""
        
        # Mevcut bilgi durumunu al
        mastery_levels = {}
        for obj_id in self.learning_objectives:
            mastery_prob = knowledge_tracer.get_mastery_probability(student_id, obj_id)
            mastery_levels[obj_id] = mastery_prob
        
        # Topological sort ile önkoşul sıralaması
        path = []
        visited = set()
        temp_visited = set()
        
        def dfs_visit(obj_id):
            if obj_id in temp_visited:
                return  # Döngü var - atla
            if obj_id in visited:
                return
                
            temp_visited.add(obj_id)
            
            # Önkoşulları önce ziyaret et
            if obj_id in self.learning_objectives:
                for prereq in self.learning_objectives[obj_id].prerequisites:
                    if mastery_levels.get(prereq, 0) < 0.8:  # Henüz ustalık yok
                        dfs_visit(prereq)
            
            temp_visited.remove(obj_id)
            visited.add(obj_id)
            
            # Ustalık seviyesi düşükse yola ekle
            if mastery_levels.get(obj_id, 0) < 0.8:
                path.append(obj_id)
        
        # Hedef öğrenme hedeflerini ziyaret et
        for target in target_objectives:
            dfs_visit(target)
        
        return path
    
    def optimize_learning_sequence(self, path: List[str], student_preferences: Dict[str, Any]) -> List[str]:
        """Öğrenme sırasını optimize et"""
        if not path:
            return path
            
        # Öğrenci tercihlerini al
        preferred_difficulty = student_preferences.get('difficulty_preference', 'medium')
        learning_style = student_preferences.get('learning_style', 'multimodal')
        time_available_minutes = student_preferences.get('daily_time_minutes', 120)
        
        # Her hedef için skor hesapla
        objective_scores = []
        for obj_id in path:
            if obj_id not in self.learning_objectives:
                continue
                
            obj = self.learning_objectives[obj_id]
            score = 0
            
            # Zorluk tercihi skoru
            difficulty_map = {
                'easy': {1: 3, 2: 2, 3: 1, 4: 0, 5: -1},
                'medium': {1: 1, 2: 2, 3: 3, 4: 2, 5: 1},
                'hard': {1: -1, 2: 0, 3: 1, 4: 2, 5: 3}
            }
            score += difficulty_map.get(preferred_difficulty, {}).get(obj.difficulty_level.value, 0)
            
            # Süre uygunluğu skoru
            if obj.estimated_time_minutes <= time_available_minutes / 3:  # Günlük zamanın 1/3'ü
                score += 2
            elif obj.estimated_time_minutes <= time_available_minutes / 2:
                score += 1
            
            # Bloom taksonomisi tercihi (basit -> karmaşık)
            score += (3 - obj.bloom_taxonomy_level) * 0.5
            
            objective_scores.append((obj_id, score))
        
        # Skora göre sırala (yüksek skor önce)
        objective_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Önkoşul kısıtlarını koruyarak yeniden sırala
        optimized_path = []
        available_objectives = [obj_id for obj_id, _ in objective_scores]
        
        while available_objectives:
            # Önkoşulları tamamlanmış en yüksek skorlu hedefi seç
            for obj_id in available_objectives:
                if obj_id in self.learning_objectives:
                    prereqs = self.learning_objectives[obj_id].prerequisites
                    if all(prereq in optimized_path or prereq not in path for prereq in prereqs):
                        optimized_path.append(obj_id)
                        available_objectives.remove(obj_id)
                        break
            else:
                # Hiçbiri uygun değilse ilkini al (deadlock'u önlemek için)
                if available_objectives:
                    optimized_path.append(available_objectives.pop(0))
        
        return optimized_path


class AdaptiveLearningEngine:
    """Ana Adaptif Öğrenme Motoru"""
    
    def __init__(self):
        self.knowledge_tracer = BayesianKnowledgeTracing()
        self.irt_model = ItemResponseTheory()
        self.difficulty_adapter = DifficultyAdaptationEngine()
        self.spaced_repetition = SpacedRepetitionAlgorithm()
        self.path_optimizer = LearningPathOptimizer()
        
        # Öğrenci profilleri
        self.student_profiles: Dict[str, Dict[str, Any]] = {}
        
        # Yanıt geçmişi (her öğrenci için son 50 yanıt)
        self.response_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
        
        # Adaptasyon kararları geçmişi
        self.adaptation_history: List[AdaptationDecision] = []
        
    def process_student_response(self, response: StudentResponse) -> Dict[str, Any]:
        """Öğrenci yanıtını işle ve adaptasyon kararları al"""
        
        # Yanıtı geçmişe ekle
        self.response_history[response.student_id].append(response)
        
        # Bilgi durumunu güncelle
        knowledge_state = self.knowledge_tracer.update_knowledge_state(response)
        
        # IRT modelini güncelle (toplu yanıtlarla)
        all_responses = list(self.response_history[response.student_id])
        if len(all_responses) >= 10:  # Minimum veri gereksinimi
            self.irt_model.estimate_item_parameters(all_responses)
            self.irt_model.estimate_student_ability(response.student_id, all_responses)
        
        # Zorluk adaptasyonu kontrol et
        recent_responses = list(self.response_history[response.student_id])[-5:]
        adaptation_decision = self.difficulty_adapter.should_adapt_difficulty(recent_responses)
        
        # Aralıklı tekrar hesapla
        performance_quality = self._calculate_performance_quality(response)
        next_review = self.spaced_repetition.calculate_next_review(
            response.student_id, response.objective_id, performance_quality
        )
        
        # Yanıt özeti
        result = {
            'knowledge_state': knowledge_state,
            'adaptation_decision': adaptation_decision,
            'next_review_date': next_review,
            'performance_summary': self._generate_performance_summary(response.student_id),
            'recommendations': self._generate_recommendations(response.student_id, knowledge_state)
        }
        
        # Adaptasyon kararını kaydet
        if adaptation_decision:
            self.adaptation_history.append(adaptation_decision)
        
        return result
    
    def _calculate_performance_quality(self, response: StudentResponse) -> float:
        """Performans kalitesini hesapla (0-5 arası)"""
        base_score = 3.0 if response.is_correct else 1.0
        
        # Yanıt süresi faktörü
        if response.response_time_seconds < 30:  # Çok hızlı
            time_factor = 0.8
        elif response.response_time_seconds < 60:  # Normal
            time_factor = 1.0
        elif response.response_time_seconds < 120:  # Yavaş
            time_factor = 0.9
        else:  # Çok yavaş
            time_factor = 0.7
        
        # İpucu kullanımı faktörü
        hint_factor = 0.8 if response.hint_used else 1.0
        
        # Deneme sayısı faktörü
        attempt_factor = max(0.6, 1.0 - (response.attempts_count - 1) * 0.1)
        
        quality = base_score * time_factor * hint_factor * attempt_factor
        return max(0, min(5, quality))
    
    def _generate_performance_summary(self, student_id: str) -> Dict[str, Any]:
        """Öğrenci performans özeti"""
        responses = list(self.response_history[student_id])
        
        if not responses:
            return {
                'total_responses': 0,
                'overall_accuracy': 0.0,
                'avg_response_time': 0.0,
                'strong_subjects': [],
                'weak_subjects': []
            }
        
        # Genel istatistikler
        total_responses = len(responses)
        overall_accuracy = sum(1 for r in responses if r.is_correct) / total_responses
        avg_response_time = sum(r.response_time_seconds for r in responses) / total_responses
        
        # Konu bazlı performans analizi
        subject_performance = defaultdict(lambda: {'correct': 0, 'total': 0})
        
        for response in responses:
            obj_id = response.objective_id
            if obj_id in self.path_optimizer.learning_objectives:
                subject = self.path_optimizer.learning_objectives[obj_id].subject
                subject_performance[subject]['total'] += 1
                if response.is_correct:
                    subject_performance[subject]['correct'] += 1
        
        # Güçlü ve zayıf konular
        subject_scores = {}
        for subject, perf in subject_performance.items():
            if perf['total'] >= 3:  # Minimum yanıt sayısı
                subject_scores[subject] = perf['correct'] / perf['total']
        
        sorted_subjects = sorted(subject_scores.items(), key=lambda x: x[1], reverse=True)
        strong_subjects = [s[0] for s in sorted_subjects[:3] if s[1] > 0.7]
        weak_subjects = [s[0] for s in sorted_subjects[-3:] if s[1] < 0.5]
        
        return {
            'total_responses': total_responses,
            'overall_accuracy': overall_accuracy,
            'avg_response_time': avg_response_time,
            'strong_subjects': strong_subjects,
            'weak_subjects': weak_subjects,
            'subject_scores': subject_scores
        }
    
    def _generate_recommendations(self, student_id: str, knowledge_state: StudentKnowledgeState) -> List[str]:
        """Kişiselleştirilmiş öneriler oluştur"""
        recommendations = []
        
        # Ustalık seviyesine göre öneriler
        if knowledge_state.mastery_level == MasteryLevel.EXPERT:
            recommendations.append("Harika! Bu konuda uzman seviyesiniz. Daha karmaşık problemlere geçebilirsiniz.")
        elif knowledge_state.mastery_level == MasteryLevel.MASTERED:
            recommendations.append("Bu konuyu başarıyla öğrendiniz. Bilginizi pekiştirmek için farklı soru tipleri deneyin.")
        elif knowledge_state.mastery_level == MasteryLevel.PROFICIENT:
            recommendations.append("İyi gidiyorsunuz! Birkaç pratik daha yaparak konuyu pekiştirebilirsiniz.")
        elif knowledge_state.mastery_level == MasteryLevel.DEVELOPING:
            recommendations.append("Gelişim gösteriyorsunuz. Bu konudaki temel kavramları tekrar gözden geçirin.")
        else:
            recommendations.append("Bu konu için daha fazla zaman ayırmalısınız. Temel kavramlardan başlayın.")
        
        # Streak analizi
        if knowledge_state.streak_correct >= 5:
            recommendations.append("[FIRE] 5 doğru yanıt serisi! Zorluk seviyesini artırabilirsiniz.")
        elif knowledge_state.streak_incorrect >= 3:
            recommendations.append("⚠️ Son sorularda zorlanıyorsunuz. Konuyu tekrar etmenizi öneririz.")
        
        # Zaman analizi
        perf_summary = self._generate_performance_summary(student_id)
        if perf_summary['avg_response_time'] > 90:
            recommendations.append("[BULB] Yanıt verme sürenizi kısaltmak için hız çalışmaları yapabilirsiniz.")
        
        # Spaced repetition önerileri
        due_reviews = self.spaced_repetition.get_due_reviews(student_id)
        if due_reviews:
            recommendations.append(f"📅 {len(due_reviews)} konu tekrar edilmeyi bekliyor.")
        
        return recommendations[:4]  # En fazla 4 öneri
    
    def generate_personalized_learning_path(self, student_id: str, 
                                          target_exam: str = "YKS",
                                          time_limit_days: int = 180) -> Dict[str, Any]:
        """Kişiselleştirilmiş öğrenme yolu oluştur"""
        
        # Hedef sınav için hedefleri belirle
        target_objectives = self._get_exam_objectives(target_exam)
        
        # Öğrenci tercihlerini al
        student_prefs = self.student_profiles.get(student_id, {
            'difficulty_preference': 'medium',
            'learning_style': 'multimodal',
            'daily_time_minutes': 120
        })
        
        # Öğrenme yolu oluştur
        learning_path = self.path_optimizer.generate_learning_path(
            student_id, target_objectives, self.knowledge_tracer
        )
        
        # Sırayı optimize et
        optimized_path = self.path_optimizer.optimize_learning_sequence(
            learning_path, student_prefs
        )
        
        # Zaman planlaması
        total_estimated_time = sum(
            self.path_optimizer.learning_objectives[obj_id].estimated_time_minutes
            for obj_id in optimized_path
            if obj_id in self.path_optimizer.learning_objectives
        )
        
        daily_time = student_prefs['daily_time_minutes']
        estimated_completion_days = math.ceil(total_estimated_time / daily_time)
        
        # Yol detayları
        path_details = []
        for i, obj_id in enumerate(optimized_path):
            if obj_id in self.path_optimizer.learning_objectives:
                obj = self.path_optimizer.learning_objectives[obj_id]
                mastery_prob = self.knowledge_tracer.get_mastery_probability(student_id, obj_id)
                
                path_details.append({
                    'sequence': i + 1,
                    'objective_id': obj_id,
                    'name': obj.name,
                    'subject': obj.subject,
                    'difficulty_level': obj.difficulty_level.name,
                    'estimated_time_minutes': obj.estimated_time_minutes,
                    'current_mastery': mastery_prob,
                    'mastery_level': self.knowledge_tracer._determine_mastery_level(mastery_prob).name
                })
        
        return {
            'student_id': student_id,
            'target_exam': target_exam,
            'learning_path': optimized_path,
            'path_details': path_details,
            'estimated_completion_days': estimated_completion_days,
            'total_estimated_hours': total_estimated_time / 60,
            'daily_study_minutes': daily_time,
            'completion_probability': self._calculate_completion_probability(student_id, optimized_path),
            'milestones': self._create_milestones(optimized_path, time_limit_days)
        }
    
    def _get_exam_objectives(self, exam_type: str) -> List[str]:
        """Sınav türüne göre hedefleri al"""
        # Bu normalde veritabanından gelecek
        exam_objectives = {
            'TYT': [
                'tyt_turkce_sozcuk', 'tyt_turkce_anlam', 'tyt_matematik_algebra',
                'tyt_matematik_geometri', 'tyt_fen_fizik', 'tyt_fen_biyoloji',
                'tyt_sosyal_tarih', 'tyt_sosyal_cografya'
            ],
            'AYT': [
                'ayt_matematik_fonksiyon', 'ayt_matematik_integral', 'ayt_fizik_mekanik',
                'ayt_fizik_elektrik', 'ayt_kimya_organik', 'ayt_biyoloji_genetik'
            ],
            'YKS': [
                # TYT + AYT hedeflerinin birleşimi
                'tyt_turkce_sozcuk', 'tyt_matematik_algebra', 'ayt_matematik_fonksiyon',
                'ayt_fizik_mekanik', 'ayt_kimya_organik'
            ]
        }
        
        return exam_objectives.get(exam_type, [])
    
    def _calculate_completion_probability(self, student_id: str, learning_path: List[str]) -> float:
        """Yolu tamamlama olasılığını hesapla"""
        if not learning_path:
            return 1.0
        
        # Geçmiş performansa dayalı hesaplama
        perf_summary = self._generate_performance_summary(student_id)
        base_prob = min(0.9, perf_summary['overall_accuracy'] + 0.1)
        
        # Yol uzunluğu faktörü
        length_factor = max(0.3, 1.0 - len(learning_path) * 0.02)
        
        # Zaman faktörü (günlük çalışma süresi)
        time_factor = min(1.0, self.student_profiles.get(student_id, {}).get('daily_time_minutes', 60) / 120)
        
        return base_prob * length_factor * time_factor
    
    def _create_milestones(self, learning_path: List[str], time_limit_days: int) -> List[Dict[str, Any]]:
        """Öğrenme yolu için kilometre taşları oluştur"""
        if not learning_path:
            return []
        
        milestones = []
        path_length = len(learning_path)
        
        # 4 milestone oluştur
        milestone_points = [0.25, 0.5, 0.75, 1.0]
        
        for i, point in enumerate(milestone_points):
            objective_index = int(path_length * point) - 1
            if objective_index >= 0 and objective_index < len(learning_path):
                obj_id = learning_path[objective_index]
                days_target = int(time_limit_days * point)
                
                milestones.append({
                    'milestone_number': i + 1,
                    'target_objective': obj_id,
                    'target_day': days_target,
                    'completion_percentage': point * 100,
                    'description': f"Milestone {i + 1}: {point*100:.0f}% tamamlama hedefi"
                })
        
        return milestones


# === KIRO2 İçin TYT/AYT Özelleştirilmiş Adaptif Sistem ===

class KIRO2AdaptiveLearningSystem:
    """KIRO2 için TYT/AYT özelleştirilmiş adaptif öğrenme sistemi"""
    
    def __init__(self):
        self.adaptive_engine = AdaptiveLearningEngine()
        self._initialize_turkish_curriculum()
        
    def _initialize_turkish_curriculum(self):
        """Türk eğitim müfredatına göre öğrenme hedeflerini başlat"""
        
        # TYT Türkçe hedefleri
        tyt_turkish_objectives = [
            LearningObjective("tyt_turkce_sozcuk", "Sözcük Bilgisi", "TYT Türkçe", "Sözcük", 
                            LearningObjectiveType.MEMORIZATION, DifficultyLevel.EASY, [], 20, 1),
            LearningObjective("tyt_turkce_anlam", "Anlam Bilgisi", "TYT Türkçe", "Anlam", 
                            LearningObjectiveType.CONCEPT, DifficultyLevel.MEDIUM, ["tyt_turkce_sozcuk"], 30, 2),
            LearningObjective("tyt_turkce_okudugunuanlama", "Okuduğunu Anlama", "TYT Türkçe", "Metin", 
                            LearningObjectiveType.ANALYSIS, DifficultyLevel.HARD, ["tyt_turkce_anlam"], 40, 4)
        ]
        
        # TYT Matematik hedefleri
        tyt_math_objectives = [
            LearningObjective("tyt_matematik_temelislemler", "Temel İşlemler", "TYT Matematik", "Sayılar", 
                            LearningObjectiveType.SKILL, DifficultyLevel.EASY, [], 15, 1),
            LearningObjective("tyt_matematik_algebra", "Cebir", "TYT Matematik", "Denklem", 
                            LearningObjectiveType.PROBLEM_SOLVING, DifficultyLevel.MEDIUM, ["tyt_matematik_temelislemler"], 35, 3),
            LearningObjective("tyt_matematik_geometri", "Geometri", "TYT Matematik", "Şekil", 
                            LearningObjectiveType.APPLICATION, DifficultyLevel.HARD, ["tyt_matematik_algebra"], 45, 4)
        ]
        
        # AYT Matematik hedefleri
        ayt_math_objectives = [
            LearningObjective("ayt_matematik_fonksiyon", "Fonksiyonlar", "AYT Matematik", "Fonksiyon", 
                            LearningObjectiveType.CONCEPT, DifficultyLevel.MEDIUM, ["tyt_matematik_algebra"], 50, 3),
            LearningObjective("ayt_matematik_turev", "Türev", "AYT Matematik", "Analiz", 
                            LearningObjectiveType.APPLICATION, DifficultyLevel.HARD, ["ayt_matematik_fonksiyon"], 60, 5),
            LearningObjective("ayt_matematik_integral", "İntegral", "AYT Matematik", "Analiz", 
                            LearningObjectiveType.SYNTHESIS, DifficultyLevel.VERY_HARD, ["ayt_matematik_turev"], 70, 6)
        ]
        
        # Tüm hedefleri sisteme ekle
        all_objectives = tyt_turkish_objectives + tyt_math_objectives + ayt_math_objectives
        for obj in all_objectives:
            self.adaptive_engine.path_optimizer.add_learning_objective(obj)
    
    async def start_student_session(self, student_id: str, 
                                  student_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Öğrenci oturumu başlat"""
        
        # Profili kaydet
        self.adaptive_engine.student_profiles[student_id] = {
            'difficulty_preference': student_profile.get('difficulty_preference', 'medium'),
            'learning_style': student_profile.get('learning_style', 'visual'),
            'daily_time_minutes': student_profile.get('daily_study_hours', 2) * 60,
            'target_exam': student_profile.get('target_exam', 'YKS'),
            'target_score': student_profile.get('target_score', 350),
            'exam_date': student_profile.get('exam_date', '2024-06-15')
        }
        
        # Kişiselleştirilmiş öğrenme yolu oluştur
        learning_path = self.adaptive_engine.generate_personalized_learning_path(
            student_id=student_id,
            target_exam=student_profile.get('target_exam', 'YKS'),
            time_limit_days=180
        )
        
        # İlk öneriler
        initial_recommendations = [
            "KIRO2'ye hoş geldiniz! Size özel hazırlanmış öğrenme yolunuz hazır.",
            f"Toplam {len(learning_path['learning_path'])} hedef tamamlamanız gerekiyor.",
            f"Tahmini tamamlama süresi: {learning_path['estimated_completion_days']} gün",
            "Günlük çalışma programınıza uygun sorularla başlayalım!"
        ]
        
        return {
            'student_id': student_id,
            'session_started': datetime.now().isoformat(),
            'learning_path': learning_path,
            'initial_recommendations': initial_recommendations,
            'next_objective': learning_path['learning_path'][0] if learning_path['learning_path'] else None
        }
    
    async def process_answer(self, student_id: str, question_id: str, 
                           objective_id: str, is_correct: bool, 
                           response_time_seconds: float, **kwargs) -> Dict[str, Any]:
        """Öğrenci yanıtını işle ve adaptif öneriler sun"""
        
        # Yanıt objesi oluştur
        response = StudentResponse(
            response_id="",
            student_id=student_id,
            objective_id=objective_id,
            question_id=question_id,
            is_correct=is_correct,
            response_time_seconds=response_time_seconds,
            difficulty_level=DifficultyLevel(kwargs.get('difficulty', 3)),
            hint_used=kwargs.get('hint_used', False),
            attempts_count=kwargs.get('attempts', 1),
            confidence_level=kwargs.get('confidence', None)
        )
        
        # Adaptif motor ile işle
        result = self.adaptive_engine.process_student_response(response)
        
        # KIRO2'ye özel yorumlar ekle
        kiro2_insights = self._generate_kiro2_insights(student_id, result)
        
        return {
            'response_processed': True,
            'knowledge_state': {
                'mastery_probability': result['knowledge_state'].mastery_probability,
                'mastery_level': result['knowledge_state'].mastery_level.name,
                'accuracy_rate': result['knowledge_state'].accuracy_rate,
                'confidence': result['knowledge_state'].confidence
            },
            'adaptation_decision': result['adaptation_decision'].__dict__ if result['adaptation_decision'] else None,
            'next_review_date': result['next_review_date'].isoformat(),
            'performance_summary': result['performance_summary'],
            'recommendations': result['recommendations'],
            'kiro2_insights': kiro2_insights,
            'motivation_message': self._get_motivation_message(result['knowledge_state'])
        }
    
    def _generate_kiro2_insights(self, student_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """KIRO2'ye özel içgörüler oluştur"""
        knowledge_state = result['knowledge_state']
        perf_summary = result['performance_summary']
        
        insights = {
            'yks_readiness_score': self._calculate_yks_readiness(student_id),
            'study_efficiency': self._calculate_study_efficiency(perf_summary),
            'weak_topic_alert': None,
            'strength_boost': None,
            'exam_strategy_tip': None
        }
        
        # Zayıf konu uyarısı
        if perf_summary['weak_subjects']:
            insights['weak_topic_alert'] = {
                'subjects': perf_summary['weak_subjects'],
                'message': f"⚠️ {', '.join(perf_summary['weak_subjects'])} konularında daha fazla çalışma gerekiyor!"
            }
        
        # Güçlü konu teşviki
        if perf_summary['strong_subjects']:
            insights['strength_boost'] = {
                'subjects': perf_summary['strong_subjects'],
                'message': f"[PARTY] {', '.join(perf_summary['strong_subjects'])} konularında harika gidiyorsunuz!"
            }
        
        # Sınav stratejisi önerisi
        if knowledge_state.mastery_level.value >= 3:  # Proficient ve üzeri
            insights['exam_strategy_tip'] = "[BULB] Bu konuda yeterli seviyesiniz. Hız odaklı pratik yapmaya odaklanın!"
        elif knowledge_state.mastery_level.value <= 2:  # Developing ve altı
            insights['exam_strategy_tip'] = "[BOOKS] Bu konuyu temelden tekrar etmenizi öneririz. Acele etmeyin!"
        
        return insights
    
    def _calculate_yks_readiness(self, student_id: str) -> float:
        """YKS hazırlık skoru hesapla (0-100)"""
        # Tüm TYT/AYT hedefleri için ustalık seviyelerini al
        objectives = ['tyt_turkce_sozcuk', 'tyt_matematik_algebra', 'ayt_matematik_fonksiyon']
        
        total_mastery = 0
        count = 0
        
        for obj_id in objectives:
            mastery = self.adaptive_engine.knowledge_tracer.get_mastery_probability(student_id, obj_id)
            total_mastery += mastery
            count += 1
        
        if count == 0:
            return 0.0
            
        readiness = (total_mastery / count) * 100
        return min(100, readiness)
    
    def _calculate_study_efficiency(self, perf_summary: Dict[str, Any]) -> str:
        """Çalışma verimlilik değerlendirmesi"""
        accuracy = perf_summary['overall_accuracy']
        avg_time = perf_summary['avg_response_time']
        
        if accuracy > 0.8 and avg_time < 60:
            return "[ROCKET] Mükemmel! Hızlı ve doğru yanıtlıyorsunuz."
        elif accuracy > 0.7 and avg_time < 90:
            return "👍 İyi gidiyorsunuz! Biraz daha hız kazanabilirsiniz."
        elif accuracy > 0.6:
            return "[LIGHTNING] Doğruluk iyi ama yanıt sürenizi kısaltmaya odaklanın."
        else:
            return "[TARGET] Doğruluğu artırmaya odaklanın, hız ikinci planda."
    
    def _get_motivation_message(self, knowledge_state: StudentKnowledgeState) -> str:
        """Motivasyon mesajı al"""
        messages = {
            MasteryLevel.EXPERT: [
                "[GLOWING_STAR] Uzman seviyesindesiniz! Diğer öğrencilere örnek oluyorsunuz!",
                "[FIRE] Harika bir performans! Bu konuda artık öğretebilecek düzeydesiniz!",
                "[DIAMOND] Mükemmel! YKS'de bu konudan tam puan alacaksınız!"
            ],
            MasteryLevel.MASTERED: [
                "[TARGET] Tebrikler! Bu konuyu başarıyla öğrendiniz!",
                "✨ Harika! YKS'de bu konular için endişelenmeyebilirsiniz!",
                "[TROPHY] Bu konuda ustalık seviyesine ulaştınız!"
            ],
            MasteryLevel.PROFICIENT: [
                "👏 İyi gidiyorsunuz! Biraz daha pratik yapın!",
                "[TRENDING_UP] Gelişiminiz çok iyi! Devam edin!",
                "💪 Bu konuda yeterli seviyeye yaklaşıyorsunız!"
            ],
            MasteryLevel.DEVELOPING: [
                "🌱 Gelişmeye devam ediyorsunuz, pes etmeyin!",
                "[BOOKS] Temelleri güçlendirmeye odaklanın!",
                "[STAR] Her doğru yanıt sizi hedefinize yaklaştırıyor!"
            ],
            MasteryLevel.INTRODUCED: [
                "[ROCKET] Yeni başlangıçlar her zaman heyecanlı!",
                "[GLOWING_STAR] Bu konuyla tanışıyorsunuz, sabırla devam edin!",
                "[DIZZY] Her başlangıç bir umuttur!"
            ],
            MasteryLevel.NOT_STARTED: [
                "[TARGET] Yeni bir konuya başlamak için hazır mısınız?",
                "📖 Bu konu size yeni fırsatlar sunacak!",
                "[RAINBOW] Her öğrenme bir maceradır!"
            ]
        }
        
        level_messages = messages.get(knowledge_state.mastery_level, ["Devam edin!"])
        return np.random.choice(level_messages)


# === Örnek Kullanım ===

async def example_kiro2_adaptive_learning():
    """KIRO2 Adaptif Öğrenme Sistemi örneği"""
    
    # Sistemi başlat
    adaptive_system = KIRO2AdaptiveLearningSystem()
    
    print("[GRADUATION_CAP] KIRO2 Adaptif Öğrenme Sistemi Başlatılıyor...")
    
    # Öğrenci profili
    student_profile = {
        'difficulty_preference': 'medium',
        'learning_style': 'visual',
        'daily_study_hours': 3,
        'target_exam': 'YKS',
        'target_score': 400,
        'exam_date': '2024-06-15'
    }
    
    # Öğrenci oturumunu başlat
    session_result = await adaptive_system.start_student_session("student_12345", student_profile)
    
    print(f"[BOOKS] Öğrenme yolu hazırlandı:")
    print(f"  - Toplam hedef: {len(session_result['learning_path']['learning_path'])}")
    print(f"  - Tahmini süre: {session_result['learning_path']['estimated_completion_days']} gün")
    print(f"  - İlk hedef: {session_result['next_objective']}")
    
    print(f"\n[BULB] İlk öneriler:")
    for rec in session_result['initial_recommendations']:
        print(f"  • {rec}")
    
    # Örnek yanıtlar simülasyonu
    sample_responses = [
        {'question_id': 'q1', 'objective_id': 'tyt_turkce_sozcuk', 'is_correct': True, 'time': 25.5, 'difficulty': 2},
        {'question_id': 'q2', 'objective_id': 'tyt_turkce_sozcuk', 'is_correct': True, 'time': 30.2, 'difficulty': 2},
        {'question_id': 'q3', 'objective_id': 'tyt_turkce_sozcuk', 'is_correct': False, 'time': 45.1, 'difficulty': 3},
        {'question_id': 'q4', 'objective_id': 'tyt_turkce_anlam', 'is_correct': True, 'time': 52.3, 'difficulty': 3},
        {'question_id': 'q5', 'objective_id': 'tyt_turkce_anlam', 'is_correct': True, 'time': 38.7, 'difficulty': 3}
    ]
    
    print(f"\n[CHART] Yanıt İşleme Simülasyonu:")
    
    for i, resp in enumerate(sample_responses, 1):
        result = await adaptive_system.process_answer(
            student_id="student_12345",
            question_id=resp['question_id'],
            objective_id=resp['objective_id'],
            is_correct=resp['is_correct'],
            response_time_seconds=resp['time'],
            difficulty=resp['difficulty']
        )
        
        print(f"\n{i}. Yanıt ({resp['question_id']}):")
        print(f"  ✓ Doğru: {'Evet' if resp['is_correct'] else 'Hayır'}")
        print(f"  ⏱️ Süre: {resp['time']:.1f}s")
        print(f"  [TRENDING_UP] Ustalık: {result['knowledge_state']['mastery_probability']:.2f} ({result['knowledge_state']['mastery_level']})")
        print(f"  [TARGET] Doğruluk: {result['knowledge_state']['accuracy_rate']:.2f}")
        print(f"  💬 Motivasyon: {result['motivation_message']}")
        
        if result['adaptation_decision']:
            print(f"  🔄 Adaptasyon: {result['adaptation_decision']['decision_type']}")
            print(f"     Açıklama: {result['adaptation_decision']['reasoning']}")
        
        # KIRO2 içgörüleri
        insights = result['kiro2_insights']
        print(f"  [CHART] YKS Hazırlık: {insights['yks_readiness_score']:.1f}%")
        print(f"  [LIGHTNING] Verimlilik: {insights['study_efficiency']}")
    
    print(f"\n🏁 Örnek adaptif öğrenme oturumu tamamlandı!")
    
    # Performans özeti
    final_summary = result['performance_summary']
    print(f"\n[TRENDING_UP] Genel Performans:")
    print(f"  • Toplam yanıt: {final_summary['total_responses']}")
    print(f"  • Başarı oranı: %{final_summary['overall_accuracy']*100:.1f}")
    print(f"  • Ortalama süre: {final_summary['avg_response_time']:.1f}s")
    
    if final_summary['strong_subjects']:
        print(f"  • Güçlü konular: {', '.join(final_summary['strong_subjects'])}")
    if final_summary['weak_subjects']:
        print(f"  • Geliştirilmesi gereken: {', '.join(final_summary['weak_subjects'])}")
    
    print(f"\n[TARGET] Son öneriler:")
    for rec in result['recommendations']:
        print(f"  • {rec}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(example_kiro2_adaptive_learning())