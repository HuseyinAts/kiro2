"""
KIRO2 Learning Loop - Öz-İyileştirme ve Strateji Evrimi Sistemi

Thompson Sampling ve Bayesian optimizasyon ile sürekli öğrenme.
"""

import logging
import math
import random
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional

try:
    import numpy as np
except ImportError:
    np = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class StrategyType(Enum):
    """Strateji türleri"""
    MATCHING = "matching"  # Eşleştirme stratejileri
    ROUTING = "routing"  # Görev yönlendirme
    RESOURCE = "resource"  # Kaynak tahsisi
    RETRY = "retry"  # Yeniden deneme
    TIMEOUT = "timeout"  # Zaman aşımı


@dataclass
class Strategy:
    """Tek bir strateji"""
    id: str
    name: str
    strategy_type: StrategyType
    parameters: dict
    enabled: bool = True
    
    # Thompson Sampling için Beta dağılımı parametreleri
    alpha: float = 1.0  # Başarı sayısı + 1
    beta: float = 1.0  # Başarısızlık sayısı + 1
    
    # İstatistikler
    total_trials: int = 0
    total_successes: int = 0
    total_failures: int = 0
    avg_reward: float = 0.0
    last_used: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ParameterBound:
    """Parametre sınırları"""
    name: str
    min_value: float
    max_value: float
    current_value: float
    step_size: float = 0.1
    is_integer: bool = False


@dataclass
class LearningResult:
    """Öğrenme sonucu"""
    strategy_id: str
    success: bool
    reward: float
    context: dict
    timestamp: datetime = field(default_factory=datetime.now)


class LearningLoop:
    """
    Öz-İyileştirme Döngüsü
    
    Özellikler:
    - Thompson Sampling ile strateji seçimi
    - Bayesian parametre optimizasyonu
    - Exploration/Exploitation dengesi
    - Regresyon önleme
    - Checkpoint ve rollback
    """
    
    def __init__(
        self,
        exploration_rate: float = 0.1,
        learning_rate: float = 0.01,
        min_trials_before_switch: int = 10
    ):
        self.strategies: dict[str, Strategy] = {}
        self.parameters: dict[str, ParameterBound] = {}
        self.history: list[LearningResult] = []
        
        self.exploration_rate = exploration_rate
        self.learning_rate = learning_rate
        self.min_trials = min_trials_before_switch
        
        # Checkpoint sistemi
        self._checkpoints: list[dict] = []
        self._best_checkpoint: Optional[dict] = None
        
        self._initialize_default_strategies()
        logger.info("LearningLoop initialized")
    
    def _initialize_default_strategies(self):
        """Varsayılan stratejileri oluştur"""
        
        # Eşleştirme stratejileri
        self.register_strategy(Strategy(
            id="match_exact_first",
            name="Exact Match First",
            strategy_type=StrategyType.MATCHING,
            parameters={"exact_weight": 1.0, "fuzzy_weight": 0.3, "semantic_weight": 0.2}
        ))
        
        self.register_strategy(Strategy(
            id="match_fuzzy_balanced",
            name="Fuzzy Balanced",
            strategy_type=StrategyType.MATCHING,
            parameters={"exact_weight": 0.5, "fuzzy_weight": 0.7, "semantic_weight": 0.5}
        ))
        
        self.register_strategy(Strategy(
            id="match_semantic_heavy",
            name="Semantic Heavy",
            strategy_type=StrategyType.MATCHING,
            parameters={"exact_weight": 0.3, "fuzzy_weight": 0.5, "semantic_weight": 0.9}
        ))
        
        # Yönlendirme stratejileri
        self.register_strategy(Strategy(
            id="route_by_capability",
            name="Route by Capability",
            strategy_type=StrategyType.ROUTING,
            parameters={"capability_weight": 0.8, "load_weight": 0.2}
        ))
        
        self.register_strategy(Strategy(
            id="route_by_load",
            name="Route by Load",
            strategy_type=StrategyType.ROUTING,
            parameters={"capability_weight": 0.3, "load_weight": 0.7}
        ))
        
        # Kaynak stratejileri
        self.register_strategy(Strategy(
            id="resource_conservative",
            name="Conservative Resources",
            strategy_type=StrategyType.RESOURCE,
            parameters={"cpu_limit": 0.5, "memory_limit": 0.5, "parallelism": 2}
        ))
        
        self.register_strategy(Strategy(
            id="resource_aggressive",
            name="Aggressive Resources",
            strategy_type=StrategyType.RESOURCE,
            parameters={"cpu_limit": 0.9, "memory_limit": 0.8, "parallelism": 8}
        ))
        
        # Varsayılan parametreler
        self.register_parameter(ParameterBound(
            name="fuzzy_threshold",
            min_value=0.5,
            max_value=0.99,
            current_value=0.85,
            step_size=0.05
        ))
        
        self.register_parameter(ParameterBound(
            name="batch_size",
            min_value=8,
            max_value=256,
            current_value=32,
            step_size=8,
            is_integer=True
        ))
        
        self.register_parameter(ParameterBound(
            name="timeout_seconds",
            min_value=10,
            max_value=300,
            current_value=60,
            step_size=10,
            is_integer=True
        ))
        
        self.register_parameter(ParameterBound(
            name="retry_count",
            min_value=1,
            max_value=10,
            current_value=3,
            step_size=1,
            is_integer=True
        ))
    
    def register_strategy(self, strategy: Strategy) -> None:
        """Strateji kaydet"""
        self.strategies[strategy.id] = strategy
        logger.debug(f"Registered strategy: {strategy.id}")
    
    def register_parameter(self, param: ParameterBound) -> None:
        """Parametre kaydet"""
        self.parameters[param.name] = param
        logger.debug(f"Registered parameter: {param.name}")
    
    def select_strategy(self, strategy_type: StrategyType, context: Optional[dict] = None) -> Strategy:
        """
        Thompson Sampling ile strateji seç
        
        Args:
            strategy_type: Strateji türü
            context: Bağlam bilgisi (opsiyonel)
        
        Returns:
            Seçilen strateji
        """
        candidates = [s for s in self.strategies.values() 
                     if s.strategy_type == strategy_type and s.enabled]
        
        if not candidates:
            raise ValueError(f"No strategies available for type: {strategy_type}")
        
        # Exploration: Rastgele seçim
        if random.random() < self.exploration_rate:
            selected = random.choice(candidates)
            logger.debug(f"Exploration: selected {selected.id}")
            return selected
        
        # Thompson Sampling: Beta dağılımından örnekle
        best_strategy = None
        best_sample = -1
        
        for strategy in candidates:
            # Beta dağılımından örnekle
            sample = random.betavariate(strategy.alpha, strategy.beta)
            if sample > best_sample:
                best_sample = sample
                best_strategy = strategy
        
        best_strategy.last_used = datetime.now()
        logger.debug(f"Thompson Sampling: selected {best_strategy.id} (sample={best_sample:.3f})")
        return best_strategy
    
    def record_outcome(self, strategy_id: str, success: bool, reward: float = 1.0, context: Optional[dict] = None) -> None:
        """
        Strateji sonucunu kaydet
        
        Args:
            strategy_id: Strateji ID
            success: Başarılı mı?
            reward: Ödül değeri (0-1 arası)
            context: Ek bağlam bilgisi
        """
        if strategy_id not in self.strategies:
            logger.warning(f"Unknown strategy: {strategy_id}")
            return
        
        strategy = self.strategies[strategy_id]
        strategy.total_trials += 1
        
        if success:
            strategy.total_successes += 1
            strategy.alpha += reward
        else:
            strategy.total_failures += 1
            strategy.beta += (1 - reward)
        
        # Moving average güncelle
        strategy.avg_reward = (
            strategy.avg_reward * (strategy.total_trials - 1) + reward
        ) / strategy.total_trials
        
        # Geçmişe kaydet
        result = LearningResult(
            strategy_id=strategy_id,
            success=success,
            reward=reward,
            context=context or {}
        )
        self.history.append(result)
        
        # Checkpoint kontrolü
        if strategy.total_trials % 100 == 0:
            self._maybe_checkpoint()
        
        logger.debug(f"Recorded outcome for {strategy_id}: success={success}, reward={reward:.2f}")
    
    def optimize_parameter(self, param_name: str, performance_score: float) -> float:
        """
        Bayesian-inspired parametre optimizasyonu
        
        Args:
            param_name: Parametre adı
            performance_score: Performans skoru (0-1)
        
        Returns:
            Yeni parametre değeri
        """
        if param_name not in self.parameters:
            raise ValueError(f"Unknown parameter: {param_name}")
        
        param = self.parameters[param_name]
        
        # Gradient-free optimizasyon
        # Performans düşükse değişiklik yap
        if performance_score < 0.5:
            # Rastgele yönde adım at
            direction = random.choice([-1, 1])
            step = param.step_size * self.learning_rate * (1 - performance_score)
            new_value = param.current_value + direction * step
        else:
            # Performans iyiyse küçük exploration
            noise = random.gauss(0, param.step_size * 0.1)
            new_value = param.current_value + noise
        
        # Sınırlar içinde tut
        new_value = max(param.min_value, min(param.max_value, new_value))
        
        if param.is_integer:
            new_value = round(new_value)
        
        param.current_value = new_value
        logger.debug(f"Optimized {param_name}: {new_value}")
        return new_value
    
    def get_parameter(self, param_name: str) -> float:
        """Parametre değeri al"""
        if param_name not in self.parameters:
            raise ValueError(f"Unknown parameter: {param_name}")
        return self.parameters[param_name].current_value
    
    def set_parameter(self, param_name: str, value: float) -> None:
        """Parametre değeri ayarla"""
        if param_name not in self.parameters:
            raise ValueError(f"Unknown parameter: {param_name}")
        
        param = self.parameters[param_name]
        value = max(param.min_value, min(param.max_value, value))
        if param.is_integer:
            value = round(value)
        param.current_value = value
    
    def _maybe_checkpoint(self) -> None:
        """Checkpoint al (performans iyiyse)"""
        current_state = self._create_checkpoint()
        
        # İlk checkpoint
        if self._best_checkpoint is None:
            self._best_checkpoint = current_state
            self._checkpoints.append(current_state)
            return
        
        # Performans karşılaştırma
        current_perf = self._calculate_overall_performance()
        best_perf = self._best_checkpoint.get("performance", 0)
        
        if current_perf > best_perf:
            self._best_checkpoint = current_state
            logger.info(f"New best checkpoint: performance={current_perf:.3f}")
        
        self._checkpoints.append(current_state)
        
        # En fazla 10 checkpoint tut
        if len(self._checkpoints) > 10:
            self._checkpoints.pop(0)
    
    def _create_checkpoint(self) -> dict:
        """Checkpoint oluştur"""
        return {
            "timestamp": datetime.now(),
            "strategies": {
                s.id: {"alpha": s.alpha, "beta": s.beta, "avg_reward": s.avg_reward}
                for s in self.strategies.values()
            },
            "parameters": {
                p.name: p.current_value
                for p in self.parameters.values()
            },
            "performance": self._calculate_overall_performance()
        }
    
    def rollback_to_best(self) -> bool:
        """En iyi checkpoint'e geri dön"""
        if self._best_checkpoint is None:
            logger.warning("No checkpoint available for rollback")
            return False
        
        # Stratejileri restore et
        for strategy_id, data in self._best_checkpoint["strategies"].items():
            if strategy_id in self.strategies:
                self.strategies[strategy_id].alpha = data["alpha"]
                self.strategies[strategy_id].beta = data["beta"]
        
        # Parametreleri restore et
        for param_name, value in self._best_checkpoint["parameters"].items():
            if param_name in self.parameters:
                self.parameters[param_name].current_value = value
        
        logger.info("Rolled back to best checkpoint")
        return True
    
    def _calculate_overall_performance(self) -> float:
        """Genel performans skoru hesapla"""
        if not self.history:
            return 0.0
        
        # Son 100 sonucun ortalaması
        recent = self.history[-100:]
        return sum(r.reward for r in recent) / len(recent)
    
    def get_strategy_stats(self) -> dict:
        """Strateji istatistikleri"""
        stats = {}
        for strategy in self.strategies.values():
            success_rate = strategy.total_successes / max(strategy.total_trials, 1)
            stats[strategy.id] = {
                "name": strategy.name,
                "type": strategy.strategy_type.value,
                "trials": strategy.total_trials,
                "success_rate": success_rate,
                "avg_reward": strategy.avg_reward,
                "ucb_score": self._calculate_ucb(strategy)
            }
        return stats
    
    def _calculate_ucb(self, strategy: Strategy, c: float = 2.0) -> float:
        """Upper Confidence Bound hesapla"""
        if strategy.total_trials == 0:
            return float("inf")
        
        total_trials = sum(s.total_trials for s in self.strategies.values())
        exploitation = strategy.avg_reward
        exploration = c * math.sqrt(math.log(total_trials) / strategy.total_trials)
        return exploitation + exploration
    
    def get_recommended_parameters(self) -> dict:
        """Önerilen parametre değerleri"""
        return {
            name: param.current_value
            for name, param in self.parameters.items()
        }
    
    def evolve_strategies(self) -> list[Strategy]:
        """
        Strateji evrimi - yeni stratejiler oluştur
        
        En başarılı stratejilerin parametrelerini kombine eder.
        """
        new_strategies = []
        
        for strategy_type in StrategyType:
            candidates = [s for s in self.strategies.values() 
                         if s.strategy_type == strategy_type and s.total_trials >= self.min_trials]
            
            if len(candidates) < 2:
                continue
            
            # En iyi iki stratejiyi seç
            sorted_candidates = sorted(candidates, key=lambda s: s.avg_reward, reverse=True)
            parent1 = sorted_candidates[0]
            parent2 = sorted_candidates[1]
            
            # Crossover: Parametreleri karıştır
            child_params = {}
            for key in parent1.parameters:
                if random.random() < 0.5:
                    child_params[key] = parent1.parameters[key]
                else:
                    child_params[key] = parent2.parameters.get(key, parent1.parameters[key])
            
            # Mutation: Küçük değişiklikler
            for key, value in child_params.items():
                if isinstance(value, (int, float)) and random.random() < 0.2:
                    mutation = random.gauss(0, abs(value) * 0.1)
                    child_params[key] = value + mutation
            
            # Yeni strateji oluştur
            child = Strategy(
                id=f"evolved_{strategy_type.value}_{len(self.strategies)}",
                name=f"Evolved {strategy_type.value}",
                strategy_type=strategy_type,
                parameters=child_params
            )
            
            new_strategies.append(child)
            self.register_strategy(child)
            logger.info(f"Evolved new strategy: {child.id}")
        
        return new_strategies


# ---------------------------------------------------------------------------
# LinUCB Contextual Bandit (M3)
# ---------------------------------------------------------------------------


class LinUCBBandit:
    """LinUCB contextual bandit for automatic strategy selection (M3).

    Replaces manual A/B testing with automatic exploration/exploitation.
    Shadow testing + progressive rollout + auto-rollback.

    Multi-objective reward:
    score = 0.4*success + 0.3*quality_gate + 0.15*(1-cost) + 0.15*(1-safety)
    """

    def __init__(self, n_features: int = 8, alpha: float = 1.0) -> None:
        self.n_features = n_features
        self.alpha = alpha  # Exploration parameter

        # Per-arm parameters: arm_id -> (A_inv, b)
        self._arms: dict[str, dict] = {}
        self._shadow_results: list[dict] = []
        self._canary_arm: Optional[str] = None
        self._canary_wins: int = 0
        self._baseline_score: float = 0.5

    def _to_column(self, context: list[float]) -> Any:
        """Convert context to numpy column vector, padded to n_features."""
        x = np.array(context[: self.n_features], dtype=float).reshape(-1, 1)
        if x.shape[0] < self.n_features:
            x = np.pad(x.flatten(), (0, self.n_features - x.shape[0])).reshape(-1, 1)
        return x

    def add_arm(self, arm_id: str) -> None:
        """Register a strategy arm."""
        self._arms[arm_id] = {
            "A": np.eye(self.n_features),
            "b": np.zeros(self.n_features),
            "trials": 0,
            "total_reward": 0.0,
        }

    def select_arm(self, context: list[float]) -> str:
        """Select best arm given context features.

        Args:
            context: Feature vector [task_type_enc, agent_enc, difficulty, ...].

        Returns:
            Selected arm_id.
        """
        if not self._arms:
            return ""

        x = self._to_column(context)

        best_arm = ""
        best_ucb = -float("inf")

        for arm_id, arm in self._arms.items():
            A = arm["A"]
            b = arm["b"]
            try:
                A_inv = np.linalg.solve(A, np.eye(self.n_features))
            except np.linalg.LinAlgError:
                A_inv = np.eye(self.n_features)
            theta = A_inv @ b
            ucb = float(theta.T @ x + self.alpha * math.sqrt(float(x.T @ A_inv @ x)))

            if ucb > best_ucb:
                best_ucb = ucb
                best_arm = arm_id

        return best_arm

    def update(self, arm_id: str, context: list[float], reward: float) -> None:
        """Update arm parameters after observing reward.

        Args:
            arm_id: Arm that was pulled.
            context: Feature vector.
            reward: Multi-objective score (0-1).
        """
        if arm_id not in self._arms:
            return

        x = self._to_column(context)

        arm = self._arms[arm_id]
        arm["A"] = arm["A"] + x @ x.T
        arm["b"] = arm["b"] + (reward * x).flatten()
        arm["trials"] += 1
        arm["total_reward"] += reward

    def shadow_test(
        self,
        current_arm: str,
        bandit_arm: str,
        context: list[float],
        current_reward: float,
    ) -> dict[str, Any]:
        """Shadow test: compare bandit suggestion vs current strategy.

        The bandit arm is NOT executed, only its predicted reward is compared.
        """
        x = self._to_column(context)

        # Predict bandit arm reward
        if bandit_arm in self._arms:
            arm = self._arms[bandit_arm]
            try:
                theta = np.linalg.solve(arm["A"], arm["b"])
            except np.linalg.LinAlgError:
                theta = arm["b"]
            predicted = float(theta.T @ x)
        else:
            predicted = 0.0

        result: dict[str, Any] = {
            "current_arm": current_arm,
            "bandit_arm": bandit_arm,
            "current_reward": current_reward,
            "predicted_reward": predicted,
            "bandit_wins": predicted > current_reward,
        }
        self._shadow_results.append(result)
        return result

    def check_progressive_rollout(self, bandit_arm: str) -> bool:
        """Check if bandit arm should be promoted to canary (3 consecutive shadow wins).

        Returns:
            True if ready for canary deployment.
        """
        recent = [
            r for r in self._shadow_results[-3:]
            if r.get("bandit_arm") == bandit_arm
        ]
        if len(recent) >= 3 and all(r.get("bandit_wins") for r in recent):
            self._canary_arm = bandit_arm
            self._canary_wins = 0
            return True
        return False

    def should_rollback(self, score: float) -> bool:
        """Auto-rollback: canary score < baseline.

        Rollback trigger: score < 0.5 OR safety_incidents > 0 OR quality_gate < 0.6
        """
        if score < self._baseline_score:
            self._canary_arm = None
            self._canary_wins = 0
            return True
        return False

    @staticmethod
    def compute_multi_objective_score(
        success_rate: float,
        quality_gate_pass_rate: float,
        cost_ratio: float,
        safety_incidents: int,
    ) -> float:
        """Multi-objective experiment scoring.

        score = 0.4*success + 0.3*quality_gate + 0.15*(1-cost) + 0.15*(1-safety)
        """
        safety = min(1.0, safety_incidents)
        return (
            0.4 * success_rate
            + 0.3 * quality_gate_pass_rate
            + 0.15 * (1.0 - cost_ratio)
            + 0.15 * (1.0 - safety)
        )


# Singleton instance
_learning_loop: Optional[LearningLoop] = None


def get_learning_loop() -> LearningLoop:
    """Singleton LearningLoop erişimi"""
    global _learning_loop
    if _learning_loop is None:
        _learning_loop = LearningLoop()
    return _learning_loop


if __name__ == "__main__":
    # Test
    loop = get_learning_loop()
    
    # Strateji seçimi test
    for _ in range(20):
        strategy = loop.select_strategy(StrategyType.MATCHING)
        success = random.random() > 0.3  # %70 başarı
        loop.record_outcome(strategy.id, success, reward=random.uniform(0.5, 1.0) if success else 0.2)
    
    # İstatistikler
    print("Strategy Stats:")
    for sid, stats in loop.get_strategy_stats().items():
        print(f"  {sid}: trials={stats['trials']}, success_rate={stats['success_rate']:.2f}")
    
    # Parametre optimizasyonu
    print(f"\nCurrent fuzzy_threshold: {loop.get_parameter('fuzzy_threshold')}")
    loop.optimize_parameter("fuzzy_threshold", 0.7)
    print(f"Optimized fuzzy_threshold: {loop.get_parameter('fuzzy_threshold')}")
    
    # Strateji evrimi
    print("\nEvolving strategies...")
    new_strategies = loop.evolve_strategies()
    print(f"Created {len(new_strategies)} new strategies")
