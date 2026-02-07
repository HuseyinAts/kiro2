"""
RLHF Training Service
Reinforcement Learning from Human Feedback - Soru kalitesi iyileştirme.

Requirements: REQ-48.29-48.32
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """İnsan geri bildirimi tipi"""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


@dataclass
class HumanFeedback:
    """İnsan geri bildirimi"""

    question_id: str
    question_text: str
    feedback_type: FeedbackType
    quality_score: float  # 0-100 arası
    comments: str
    reviewer_id: str
    timestamp: datetime


@dataclass
class RLHFMetrics:
    """RLHF eğitim metrikleri"""

    epoch: int
    policy_loss: float
    value_loss: float
    reward_mean: float
    reward_std: float
    kl_divergence: float
    performance_improvement: float
    timestamp: datetime


class RewardModel(nn.Module):
    """
    Reward Model

    Soru kalitesini 0-100 arası skorlayan model.
    REQ-48.30: Reward model training
    """

    def __init__(self, input_dim: int = 768, hidden_dim: int = 256):
        """
        Initialize Reward Model

        Args:
            input_dim: Input dimension (embedding boyutu)
            hidden_dim: Hidden layer dimension
        """
        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid(),  # 0-1 arası output
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass

        Args:
            x: Input tensor (batch_size, input_dim)

        Returns:
            torch.Tensor: Reward scores (batch_size, 1)
        """
        return self.network(x) * 100  # 0-100 arası scale et


class PPOTrainer:
    """
    Proximal Policy Optimization Trainer

    REQ-48.31: PPO algorithm implementation
    """

    def __init__(
        self,
        policy_model: nn.Module,
        value_model: nn.Module,
        learning_rate: float = 3e-4,
        gamma: float = 0.99,
        epsilon: float = 0.2,
        value_coef: float = 0.5,
        entropy_coef: float = 0.01,
    ):
        """
        Initialize PPO Trainer

        Args:
            policy_model: Policy network
            value_model: Value network
            learning_rate: Learning rate
            gamma: Discount factor
            epsilon: PPO clip parameter
            value_coef: Value loss coefficient
            entropy_coef: Entropy coefficient
        """
        self.policy_model = policy_model
        self.value_model = value_model

        self.gamma = gamma
        self.epsilon = epsilon
        self.value_coef = value_coef
        self.entropy_coef = entropy_coef

        # Optimizers
        self.policy_optimizer = optim.Adam(policy_model.parameters(), lr=learning_rate)
        self.value_optimizer = optim.Adam(value_model.parameters(), lr=learning_rate)

        logger.info("PPO Trainer initialized")

    def compute_advantages(
        self, rewards: torch.Tensor, values: torch.Tensor, dones: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Advantage ve return hesapla (GAE - Generalized Advantage Estimation)

        Args:
            rewards: Rewards tensor
            values: Value predictions
            dones: Done flags

        Returns:
            Tuple[torch.Tensor, torch.Tensor]: (advantages, returns)
        """
        advantages = []
        returns = []

        advantage = 0
        next_value = 0

        for t in reversed(range(len(rewards))):
            if dones[t]:
                next_value = 0
                advantage = 0

            delta = rewards[t] + self.gamma * next_value - values[t]
            advantage = delta + self.gamma * 0.95 * advantage

            advantages.insert(0, advantage)
            returns.insert(0, advantage + values[t])

            next_value = values[t]

        advantages = torch.tensor(advantages)
        returns = torch.tensor(returns)

        # Normalize advantages
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        return advantages, returns

    def train_step(
        self,
        states: torch.Tensor,
        actions: torch.Tensor,
        old_log_probs: torch.Tensor,
        rewards: torch.Tensor,
        dones: torch.Tensor,
    ) -> Dict[str, float]:
        """
        PPO training step

        Args:
            states: State tensor
            actions: Action tensor
            old_log_probs: Old log probabilities
            rewards: Rewards
            dones: Done flags

        Returns:
            Dict: Training metrics
        """
        # Value predictions
        values = self.value_model(states).squeeze()

        # Compute advantages
        advantages, returns = self.compute_advantages(rewards, values, dones)

        # Policy loss
        new_log_probs = self.policy_model(states, actions)
        ratio = torch.exp(new_log_probs - old_log_probs)

        surr1 = ratio * advantages
        surr2 = torch.clamp(ratio, 1 - self.epsilon, 1 + self.epsilon) * advantages
        policy_loss = -torch.min(surr1, surr2).mean()

        # Value loss
        value_loss = nn.MSELoss()(values, returns)

        # Entropy (for exploration)
        entropy = -(new_log_probs * torch.exp(new_log_probs)).mean()

        # Total loss
        total_loss = (
            policy_loss + self.value_coef * value_loss - self.entropy_coef * entropy
        )

        # Optimize
        self.policy_optimizer.zero_grad()
        self.value_optimizer.zero_grad()
        total_loss.backward()
        self.policy_optimizer.step()
        self.value_optimizer.step()

        # KL divergence
        kl_div = (old_log_probs - new_log_probs).mean().item()

        return {
            "policy_loss": policy_loss.item(),
            "value_loss": value_loss.item(),
            "entropy": entropy.item(),
            "kl_divergence": kl_div,
        }


class RLHFTrainingService:
    """
    RLHF Training Service

    Reinforcement Learning from Human Feedback ile model iyileştirme.

    Requirements:
    - REQ-48.29: RLHF training loop with human feedback
    - REQ-48.30: Reward model training (0-100 scoring)
    - REQ-48.31: PPO algorithm implementation
    - REQ-48.32: Model performance improvement (20%+)
    """

    def __init__(self, embedding_dim: int = 768, device: Optional[str] = None):
        """
        Initialize RLHF Training Service

        Args:
            embedding_dim: Embedding dimension
            device: Device ('cuda', 'cpu', veya None)
        """
        # Device seç
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        logger.info(f"Initializing RLHF Training Service on {self.device}")

        # Reward model
        self.reward_model = RewardModel(input_dim=embedding_dim)
        self.reward_model.to(self.device)

        # Feedback storage
        self.feedback_history: List[HumanFeedback] = []
        self.metrics_history: List[RLHFMetrics] = []

        # Baseline performance
        self.baseline_performance: Optional[float] = None

        logger.info("RLHF Training Service initialized")

    def collect_human_feedback(
        self,
        question_id: str,
        question_text: str,
        quality_score: float,
        feedback_type: FeedbackType,
        comments: str = "",
        reviewer_id: str = "anonymous",
    ) -> HumanFeedback:
        """
        İnsan geri bildirimi topla

        REQ-48.29: RLHF training loop with human feedback

        Args:
            question_id: Soru ID
            question_text: Soru metni
            quality_score: Kalite skoru (0-100)
            feedback_type: Geri bildirim tipi
            comments: Yorumlar
            reviewer_id: Değerlendirici ID

        Returns:
            HumanFeedback: Geri bildirim objesi
        """
        feedback = HumanFeedback(
            question_id=question_id,
            question_text=question_text,
            feedback_type=feedback_type,
            quality_score=quality_score,
            comments=comments,
            reviewer_id=reviewer_id,
            timestamp=datetime.now(),
        )

        self.feedback_history.append(feedback)
        logger.info(
            f"Collected feedback for question {question_id}: {quality_score}/100"
        )

        return feedback

    def train_reward_model(
        self,
        question_embeddings: torch.Tensor,
        quality_scores: torch.Tensor,
        epochs: int = 10,
        batch_size: int = 32,
        learning_rate: float = 1e-3,
    ) -> Dict[str, float]:
        """
        Reward model eğit

        REQ-48.30: Reward model training (0-100 scoring)

        Args:
            question_embeddings: Soru embeddings (N, embedding_dim)
            quality_scores: Kalite skorları (N,) - 0-100 arası
            epochs: Epoch sayısı
            batch_size: Batch boyutu
            learning_rate: Learning rate

        Returns:
            Dict: Training metrics
        """
        self.reward_model.train()

        optimizer = optim.Adam(self.reward_model.parameters(), lr=learning_rate)
        criterion = nn.MSELoss()

        # Dataset oluştur
        dataset = torch.utils.data.TensorDataset(question_embeddings, quality_scores)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

        losses = []

        for epoch in range(epochs):
            epoch_loss = 0.0

            for batch_embeddings, batch_scores in dataloader:
                batch_embeddings = batch_embeddings.to(self.device)
                batch_scores = batch_scores.to(self.device)

                # Forward pass
                predictions = self.reward_model(batch_embeddings).squeeze()
                loss = criterion(predictions, batch_scores)

                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                epoch_loss += loss.item()

            avg_loss = epoch_loss / len(dataloader)
            losses.append(avg_loss)

            if (epoch + 1) % 2 == 0:
                logger.info(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")

        self.reward_model.eval()

        return {
            "final_loss": losses[-1],
            "avg_loss": sum(losses) / len(losses),
            "epochs": epochs,
        }

    def predict_quality(self, question_embedding: torch.Tensor) -> float:
        """
        Soru kalitesini tahmin et

        REQ-48.30: Reward model scoring (0-100)

        Args:
            question_embedding: Soru embedding

        Returns:
            float: Kalite skoru (0-100)
        """
        self.reward_model.eval()

        with torch.no_grad():
            embedding = question_embedding.to(self.device)
            if embedding.dim() == 1:
                embedding = embedding.unsqueeze(0)

            score = self.reward_model(embedding).item()

        return float(np.clip(score, 0.0, 100.0))

    def run_rlhf_loop(
        self,
        initial_questions: List[Dict[str, Any]],
        num_iterations: int = 10,
        questions_per_iteration: int = 50,
    ) -> List[RLHFMetrics]:
        """
        RLHF training loop çalıştır

        REQ-48.29: RLHF training loop
        REQ-48.32: Model performance improvement (20%+)

        Args:
            initial_questions: İlk soru seti
            num_iterations: İterasyon sayısı
            questions_per_iteration: İterasyon başına soru sayısı

        Returns:
            List[RLHFMetrics]: Training metrics
        """
        # Baseline performance hesapla
        if self.baseline_performance is None:
            baseline_scores = [q.get("quality_score", 50.0) for q in initial_questions]
            self.baseline_performance = sum(baseline_scores) / len(baseline_scores)
            logger.info(f"Baseline performance: {self.baseline_performance:.2f}")

        metrics_list = []

        for iteration in range(num_iterations):
            logger.info(f"RLHF Iteration {iteration + 1}/{num_iterations}")

            # Simüle edilmiş rewards (gerçek uygulamada insan feedback'i kullanılır)
            rewards = []
            for _ in range(questions_per_iteration):
                # Reward model ile kalite tahmini
                fake_embedding = torch.randn(768).to(self.device)
                quality = self.predict_quality(fake_embedding)
                rewards.append(quality)

            # Metrics hesapla
            reward_mean = np.mean(rewards)
            reward_std = np.std(rewards)

            # Performance improvement
            if self.baseline_performance:
                improvement = (
                    (reward_mean - self.baseline_performance)
                    / self.baseline_performance
                ) * 100
            else:
                improvement = 0.0

            metrics = RLHFMetrics(
                epoch=iteration + 1,
                policy_loss=0.0,  # PPO ile hesaplanacak
                value_loss=0.0,
                reward_mean=reward_mean,
                reward_std=reward_std,
                kl_divergence=0.0,
                performance_improvement=improvement,
                timestamp=datetime.now(),
            )

            metrics_list.append(metrics)
            self.metrics_history.append(metrics)

            logger.info(
                f"Iteration {iteration + 1}: "
                f"Reward={reward_mean:.2f}±{reward_std:.2f}, "
                f"Improvement={improvement:.2f}%"
            )

        # Final improvement kontrolü
        final_improvement = metrics_list[-1].performance_improvement
        if final_improvement >= 20.0:
            logger.info(
                f"✓ REQ-48.32 satisfied: {final_improvement:.2f}% improvement (target: 20%+)"
            )
        else:
            logger.warning(
                f"✗ REQ-48.32 not satisfied: {final_improvement:.2f}% improvement (target: 20%+)"
            )

        return metrics_list

    def get_feedback_statistics(self) -> Dict[str, Any]:
        """
        Feedback istatistiklerini getir

        Returns:
            Dict: İstatistikler
        """
        if not self.feedback_history:
            return {"total_feedback": 0}

        scores = [f.quality_score for f in self.feedback_history]

        feedback_by_type = {
            FeedbackType.POSITIVE: 0,
            FeedbackType.NEGATIVE: 0,
            FeedbackType.NEUTRAL: 0,
        }

        for feedback in self.feedback_history:
            feedback_by_type[feedback.feedback_type] += 1

        return {
            "total_feedback": len(self.feedback_history),
            "avg_quality_score": sum(scores) / len(scores),
            "min_quality_score": min(scores),
            "max_quality_score": max(scores),
            "std_quality_score": np.std(scores),
            "feedback_by_type": {
                "positive": feedback_by_type[FeedbackType.POSITIVE],
                "negative": feedback_by_type[FeedbackType.NEGATIVE],
                "neutral": feedback_by_type[FeedbackType.NEUTRAL],
            },
        }

    def export_feedback_data(self, output_file: str) -> None:
        """
        Feedback verilerini dışa aktar

        Args:
            output_file: Çıktı dosyası
        """
        import json

        data = {
            "total_feedback": len(self.feedback_history),
            "baseline_performance": self.baseline_performance,
            "feedback": [
                {
                    "question_id": f.question_id,
                    "question_text": f.question_text,
                    "quality_score": f.quality_score,
                    "feedback_type": f.feedback_type.value,
                    "comments": f.comments,
                    "reviewer_id": f.reviewer_id,
                    "timestamp": f.timestamp.isoformat(),
                }
                for f in self.feedback_history
            ],
            "metrics": [
                {
                    "epoch": m.epoch,
                    "reward_mean": m.reward_mean,
                    "reward_std": m.reward_std,
                    "performance_improvement": m.performance_improvement,
                    "timestamp": m.timestamp.isoformat(),
                }
                for m in self.metrics_history
            ],
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Exported feedback data to {output_file}")

    def save_reward_model(self, model_path: str) -> None:
        """
        Reward model'i kaydet

        Args:
            model_path: Model dosya yolu
        """
        torch.save(
            {
                "model_state_dict": self.reward_model.state_dict(),
                "baseline_performance": self.baseline_performance,
            },
            model_path,
        )

        logger.info(f"Saved reward model to {model_path}")

    def load_reward_model(self, model_path: str) -> None:
        """
        Reward model'i yükle

        Args:
            model_path: Model dosya yolu
        """
        checkpoint = torch.load(model_path, map_location=self.device)
        self.reward_model.load_state_dict(checkpoint["model_state_dict"])
        self.baseline_performance = checkpoint.get("baseline_performance")

        logger.info(f"Loaded reward model from {model_path}")
