"""
Meta-Learning System Service - CLAUDE.md Self-Improvement

Bu servis, agent'ın öğrenmeyi öğrenmesini sağlar:
- Learning rate optimization
- Transfer learning
- Exploration-exploitation balance
- Bayesian optimization
- Knowledge graph persistence

Spec: claude-md-self-improvement REQ-5
- REQ-5.1: Learning rate optimize
- REQ-5.2: Transfer learning
- REQ-5.3: Epsilon-greedy strategy
- REQ-5.4: Bayesian optimization
- REQ-5.5: Plateau detection
- REQ-5.6: Knowledge graph

Author: KIRO2 Team
Date: 2026-01-17
"""

import logging
import random
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

# Scientific computing
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None  # type: ignore

# Bayesian optimization
try:
    from skopt import gp_minimize
    from skopt.space import Integer, Real
    SKOPT_AVAILABLE = True
except ImportError:
    SKOPT_AVAILABLE = False
    gp_minimize = None  # type: ignore

# Knowledge graph
try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    nx = None  # type: ignore

# Database
# Models
from backend.models.claude_md_improvement_models import (
    AuditLog,
    PatternDetection,
    RuleEffectiveness,
)
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class LearningState:
    """Current learning state."""
    learning_rate: float = 0.1
    exploration_rate: float = 0.3  # Epsilon for epsilon-greedy
    iteration: int = 0
    total_reward: float = 0.0
    recent_rewards: list[float] = field(default_factory=list)
    plateau_count: int = 0
    best_score: float = 0.0


@dataclass
class TaskSimilarity:
    """Task similarity for transfer learning."""
    source_task: str
    target_task: str
    similarity_score: float
    shared_features: list[str]
    transferable_knowledge: dict[str, Any]


class MetaLearningService:
    """
    Meta-learning service for CLAUDE.md self-improvement.

    Implements learning-to-learn with:
    - Adaptive learning rate
    - Transfer learning across similar tasks
    - Exploration-exploitation balancing
    - Bayesian hyperparameter optimization
    """

    # Configuration
    MIN_LEARNING_RATE = 0.01
    MAX_LEARNING_RATE = 0.5
    INITIAL_EPSILON = 0.3
    EPSILON_DECAY = 0.99
    MIN_EPSILON = 0.05
    PLATEAU_THRESHOLD = 0.01
    PLATEAU_PATIENCE = 5
    RECENT_WINDOW = 10

    def __init__(self, db: AsyncSession):
        """Initialize meta-learning service."""
        self.db = db
        self._learning_state = LearningState()
        self._knowledge_graph: nx.DiGraph | None = None

        if NETWORKX_AVAILABLE:
            self._knowledge_graph = nx.DiGraph()

        if not NUMPY_AVAILABLE:
            logger.warning("numpy not available. Meta-learning limited.")

    # =========================================================================
    # REQ-5.1: Learning Rate Optimization
    # =========================================================================

    async def optimize_learning_rate(
        self,
        recent_performance: list[float],
    ) -> float:
        """
        Optimize learning rate based on recent performance.

        Uses adaptive learning rate scheduling:
        - Increase if improving
        - Decrease if oscillating or stuck
        - Maintain if stable

        Args:
            recent_performance: Recent performance scores

        Returns:
            Optimized learning rate
        """
        if len(recent_performance) < 2:
            return self._learning_state.learning_rate

        current_lr = self._learning_state.learning_rate

        # Calculate trend
        if NUMPY_AVAILABLE:
            trend = np.polyfit(
                range(len(recent_performance)),
                recent_performance,
                1,
            )[0]  # Slope
        else:
            # Simple trend calculation
            n = len(recent_performance)
            mean_x = (n - 1) / 2
            mean_y = sum(recent_performance) / n

            numerator = sum(
                (i - mean_x) * (y - mean_y)
                for i, y in enumerate(recent_performance)
            )
            denominator = sum((i - mean_x) ** 2 for i in range(n))

            trend = numerator / max(denominator, 0.001)

        # Calculate variance
        mean_perf = sum(recent_performance) / len(recent_performance)
        variance = sum((p - mean_perf) ** 2 for p in recent_performance) / len(recent_performance)

        # Adjust learning rate
        if trend > 0.05:  # Improving
            # Increase learning rate
            new_lr = min(current_lr * 1.1, self.MAX_LEARNING_RATE)
            logger.info(f"Increasing learning rate: {current_lr:.4f} -> {new_lr:.4f}")

        elif trend < -0.05:  # Declining
            # Decrease learning rate
            new_lr = max(current_lr * 0.8, self.MIN_LEARNING_RATE)
            logger.info(f"Decreasing learning rate: {current_lr:.4f} -> {new_lr:.4f}")

        elif variance > 0.1:  # Oscillating
            # Decrease learning rate significantly
            new_lr = max(current_lr * 0.5, self.MIN_LEARNING_RATE)
            logger.info(f"Reducing LR due to oscillation: {current_lr:.4f} -> {new_lr:.4f}")

        else:  # Stable
            new_lr = current_lr

        self._learning_state.learning_rate = new_lr

        # Log audit
        await self._log_audit(
            action="optimize_learning_rate",
            entity_type="meta_learning",
            details={
                "previous_lr": current_lr,
                "new_lr": new_lr,
                "trend": trend,
                "variance": variance,
            },
        )

        return new_lr

    # =========================================================================
    # REQ-5.2: Transfer Learning
    # =========================================================================

    async def find_similar_tasks(
        self,
        target_task: str,
        threshold: float = 0.5,
    ) -> list[TaskSimilarity]:
        """
        Find similar tasks for transfer learning.

        Args:
            target_task: Target task description
            threshold: Minimum similarity threshold

        Returns:
            List of similar tasks with transferable knowledge
        """
        # Get all rules and their contexts
        result = await self.db.execute(
            select(RuleEffectiveness)
            .where(RuleEffectiveness.effectiveness_score > 0.5)  # Good performers
        )
        rules = result.scalars().all()

        similarities = []

        for rule in rules:
            # Calculate text similarity
            similarity = self._calculate_text_similarity(
                target_task, rule.rule_text or ""
            )

            if similarity >= threshold:
                # Identify shared features
                shared_features = self._extract_shared_features(
                    target_task, rule.rule_text or ""
                )

                # Get transferable knowledge
                transferable = {
                    "rule_id": rule.rule_id,
                    "effectiveness_score": rule.effectiveness_score,
                    "success_patterns": await self._get_success_patterns(rule.rule_id),
                }

                similarities.append(TaskSimilarity(
                    source_task=rule.rule_id,
                    target_task=target_task,
                    similarity_score=similarity,
                    shared_features=shared_features,
                    transferable_knowledge=transferable,
                ))

        # Sort by similarity
        similarities.sort(key=lambda x: x.similarity_score, reverse=True)

        return similarities[:5]  # Top 5

    async def apply_transfer_learning(
        self,
        target_task: str,
        source_knowledge: TaskSimilarity,
    ) -> dict[str, Any]:
        """
        Apply transfer learning from similar task.

        Args:
            target_task: Target task
            source_knowledge: Knowledge from similar task

        Returns:
            Applied knowledge and recommendations
        """
        knowledge = source_knowledge.transferable_knowledge
        shared = source_knowledge.shared_features

        # Calculate transfer weight based on similarity
        weight = source_knowledge.similarity_score ** 2  # Square for emphasis

        # Generate recommendations
        recommendations = []

        if knowledge.get("success_patterns"):
            for pattern in knowledge["success_patterns"]:
                recommendations.append({
                    "type": "pattern",
                    "description": pattern.get("description", ""),
                    "weight": weight,
                    "source": source_knowledge.source_task,
                })

        # Update knowledge graph
        if self._knowledge_graph is not None:
            self._knowledge_graph.add_edge(
                source_knowledge.source_task,
                target_task,
                weight=weight,
                transfer_time=datetime.now(UTC).isoformat(),
            )

        await self._log_audit(
            action="apply_transfer_learning",
            entity_type="meta_learning",
            details={
                "source": source_knowledge.source_task,
                "target": target_task,
                "similarity": source_knowledge.similarity_score,
                "recommendations_count": len(recommendations),
            },
        )

        return {
            "applied": True,
            "source_task": source_knowledge.source_task,
            "similarity": source_knowledge.similarity_score,
            "weight": weight,
            "shared_features": shared,
            "recommendations": recommendations,
        }

    # =========================================================================
    # REQ-5.3: Epsilon-Greedy Strategy
    # =========================================================================

    def should_explore(self) -> bool:
        """
        Determine whether to explore (random action) or exploit (best known).

        Uses epsilon-greedy with decay.

        Returns:
            True if should explore, False if should exploit
        """
        explore = random.random() < self._learning_state.exploration_rate
        return explore

    async def get_action(
        self,
        available_actions: list[str],
        action_values: dict[str, float],
    ) -> tuple[str, bool]:
        """
        Select action using epsilon-greedy strategy.

        Args:
            available_actions: List of possible actions
            action_values: Estimated value of each action

        Returns:
            Tuple of (selected_action, is_exploration)
        """
        if not available_actions:
            return "", False

        if self.should_explore():
            # Explore: random action
            action = random.choice(available_actions)
            return action, True
        # Exploit: best known action
        best_action = max(
            available_actions,
            key=lambda a: action_values.get(a, 0.0),
        )
        return best_action, False

    async def update_exploration_rate(self) -> float:
        """
        Update exploration rate with decay.

        Returns:
            New exploration rate
        """
        current = self._learning_state.exploration_rate
        new_rate = max(
            current * self.EPSILON_DECAY,
            self.MIN_EPSILON,
        )

        self._learning_state.exploration_rate = new_rate
        self._learning_state.iteration += 1

        return new_rate

    # =========================================================================
    # REQ-5.4: Bayesian Optimization
    # =========================================================================

    async def bayesian_optimize(
        self,
        objective_fn,
        parameter_space: dict[str, tuple[float, float]],
        n_calls: int = 20,
    ) -> dict[str, Any]:
        """
        Perform Bayesian optimization for hyperparameters.

        Args:
            objective_fn: Function to minimize
            parameter_space: Dict of {param_name: (min, max)}
            n_calls: Number of optimization iterations

        Returns:
            Optimization results
        """
        if not SKOPT_AVAILABLE:
            # Fallback: random search
            logger.warning("skopt not available, using random search")
            return await self._random_search(
                objective_fn, parameter_space, n_calls
            )

        # Create search space
        space = [
            Real(low, high, name=name)
            for name, (low, high) in parameter_space.items()
        ]
        param_names = list(parameter_space.keys())

        # Run Bayesian optimization
        try:
            result = gp_minimize(
                objective_fn,
                space,
                n_calls=n_calls,
                random_state=42,
            )

            best_params = dict(zip(param_names, result.x))

            await self._log_audit(
                action="bayesian_optimize",
                entity_type="meta_learning",
                details={
                    "best_params": best_params,
                    "best_value": float(result.fun),
                    "n_calls": n_calls,
                },
            )

            return {
                "success": True,
                "best_params": best_params,
                "best_value": result.fun,
                "all_values": list(result.func_vals),
            }

        except Exception as e:
            logger.error(f"Bayesian optimization failed: {e}")
            return await self._random_search(
                objective_fn, parameter_space, n_calls
            )

    async def _random_search(
        self,
        objective_fn,
        parameter_space: dict[str, tuple[float, float]],
        n_calls: int,
    ) -> dict[str, Any]:
        """Fallback random search optimization."""
        best_params = {}
        best_value = float("inf")

        for _ in range(n_calls):
            # Random sample
            params = {
                name: random.uniform(low, high)
                for name, (low, high) in parameter_space.items()
            }

            try:
                value = objective_fn(list(params.values()))

                if value < best_value:
                    best_value = value
                    best_params = params

            except Exception as e:
                logger.warning(f"Objective function error: {e}")

        return {
            "success": True,
            "best_params": best_params,
            "best_value": best_value,
            "method": "random_search",
        }

    # =========================================================================
    # REQ-5.5: Plateau Detection
    # =========================================================================

    async def detect_plateau(
        self,
        recent_scores: list[float],
    ) -> tuple[bool, str]:
        """
        Detect if learning has plateaued.

        Uses moving average comparison to detect stagnation.

        Args:
            recent_scores: Recent performance scores

        Returns:
            Tuple of (is_plateau, reason)
        """
        if len(recent_scores) < self.RECENT_WINDOW:
            return False, "Not enough data"

        # Calculate moving averages
        first_half = recent_scores[:len(recent_scores) // 2]
        second_half = recent_scores[len(recent_scores) // 2:]

        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)

        # Check for plateau
        improvement = abs(avg_second - avg_first)

        if improvement < self.PLATEAU_THRESHOLD:
            self._learning_state.plateau_count += 1

            if self._learning_state.plateau_count >= self.PLATEAU_PATIENCE:
                reason = (
                    f"Plateau detected: {self._learning_state.plateau_count} consecutive "
                    f"iterations with improvement < {self.PLATEAU_THRESHOLD}"
                )

                await self._log_audit(
                    action="detect_plateau",
                    entity_type="meta_learning",
                    details={
                        "plateau_count": self._learning_state.plateau_count,
                        "avg_first": avg_first,
                        "avg_second": avg_second,
                        "improvement": improvement,
                    },
                )

                return True, reason
        else:
            # Reset plateau count
            self._learning_state.plateau_count = 0

        return False, "Learning progressing"

    async def escape_plateau(self) -> dict[str, Any]:
        """
        Apply strategies to escape plateau.

        Returns:
            Applied strategies and new parameters
        """
        strategies = []

        # Strategy 1: Increase exploration
        old_epsilon = self._learning_state.exploration_rate
        self._learning_state.exploration_rate = min(0.5, old_epsilon * 2)
        strategies.append({
            "name": "increase_exploration",
            "old_value": old_epsilon,
            "new_value": self._learning_state.exploration_rate,
        })

        # Strategy 2: Adjust learning rate
        old_lr = self._learning_state.learning_rate
        self._learning_state.learning_rate = min(
            self.MAX_LEARNING_RATE,
            old_lr * 1.5,
        )
        strategies.append({
            "name": "increase_learning_rate",
            "old_value": old_lr,
            "new_value": self._learning_state.learning_rate,
        })

        # Reset plateau count
        self._learning_state.plateau_count = 0

        await self._log_audit(
            action="escape_plateau",
            entity_type="meta_learning",
            details={"strategies": strategies},
        )

        return {
            "plateau_escaped": True,
            "strategies_applied": strategies,
        }

    # =========================================================================
    # REQ-5.6: Knowledge Graph
    # =========================================================================

    async def persist_knowledge_graph(self) -> dict[str, Any]:
        """
        Persist knowledge graph to storage.

        Returns:
            Persistence result
        """
        if not self._knowledge_graph or not NETWORKX_AVAILABLE:
            return {"success": False, "error": "Knowledge graph not available"}

        try:
            # Convert to JSON-serializable format
            graph_data = nx.node_link_data(self._knowledge_graph)

            # Add metadata
            graph_data["meta"] = {
                "persisted_at": datetime.now(UTC).isoformat(),
                "node_count": self._knowledge_graph.number_of_nodes(),
                "edge_count": self._knowledge_graph.number_of_edges(),
                "learning_state": {
                    "learning_rate": self._learning_state.learning_rate,
                    "exploration_rate": self._learning_state.exploration_rate,
                    "iteration": self._learning_state.iteration,
                    "best_score": self._learning_state.best_score,
                },
            }

            await self._log_audit(
                action="persist_knowledge_graph",
                entity_type="knowledge_graph",
                details=graph_data["meta"],
            )

            return {
                "success": True,
                "nodes": graph_data["meta"]["node_count"],
                "edges": graph_data["meta"]["edge_count"],
            }

        except Exception as e:
            logger.error(f"Failed to persist knowledge graph: {e}")
            return {"success": False, "error": str(e)}

    async def load_knowledge_graph(
        self,
        graph_data: dict[str, Any],
    ) -> bool:
        """
        Load knowledge graph from storage.

        Args:
            graph_data: Serialized graph data

        Returns:
            Success status
        """
        if not NETWORKX_AVAILABLE:
            return False

        try:
            self._knowledge_graph = nx.node_link_graph(graph_data)

            # Restore learning state if available
            if "meta" in graph_data and "learning_state" in graph_data["meta"]:
                state = graph_data["meta"]["learning_state"]
                self._learning_state.learning_rate = state.get("learning_rate", 0.1)
                self._learning_state.exploration_rate = state.get("exploration_rate", 0.3)
                self._learning_state.iteration = state.get("iteration", 0)
                self._learning_state.best_score = state.get("best_score", 0.0)

            return True

        except Exception as e:
            logger.error(f"Failed to load knowledge graph: {e}")
            return False

    def query_knowledge_graph(
        self,
        node: str,
        depth: int = 2,
    ) -> dict[str, Any]:
        """
        Query knowledge graph for related nodes.

        Args:
            node: Starting node
            depth: Maximum depth to traverse

        Returns:
            Related nodes and edges
        """
        if not self._knowledge_graph or not NETWORKX_AVAILABLE:
            return {"related": [], "edges": []}

        if node not in self._knowledge_graph:
            return {"related": [], "edges": []}

        # BFS to find related nodes
        related: set[str] = set()
        edges = []

        current_level = {node}
        for d in range(depth):
            next_level: set[str] = set()

            for n in current_level:
                # Successors (outgoing edges)
                for succ in self._knowledge_graph.successors(n):
                    if succ not in related:
                        next_level.add(succ)
                        edge_data = self._knowledge_graph.get_edge_data(n, succ, {})
                        edges.append({
                            "source": n,
                            "target": succ,
                            "weight": edge_data.get("weight", 1.0),
                        })

                # Predecessors (incoming edges)
                for pred in self._knowledge_graph.predecessors(n):
                    if pred not in related:
                        next_level.add(pred)
                        edge_data = self._knowledge_graph.get_edge_data(pred, n, {})
                        edges.append({
                            "source": pred,
                            "target": n,
                            "weight": edge_data.get("weight", 1.0),
                        })

            related.update(next_level)
            current_level = next_level

        return {
            "start_node": node,
            "related": list(related),
            "edges": edges,
            "depth": depth,
        }

    # =========================================================================
    # Learning Loop
    # =========================================================================

    async def record_reward(
        self,
        reward: float,
    ) -> None:
        """
        Record reward and update learning state.

        Args:
            reward: Reward value
        """
        self._learning_state.total_reward += reward
        self._learning_state.recent_rewards.append(reward)

        # Keep recent window
        if len(self._learning_state.recent_rewards) > self.RECENT_WINDOW:
            self._learning_state.recent_rewards.pop(0)

        # Update best score
        self._learning_state.best_score = max(self._learning_state.best_score, reward)

    async def get_learning_status(self) -> dict[str, Any]:
        """Get current learning status."""
        return {
            "learning_rate": self._learning_state.learning_rate,
            "exploration_rate": self._learning_state.exploration_rate,
            "iteration": self._learning_state.iteration,
            "total_reward": self._learning_state.total_reward,
            "best_score": self._learning_state.best_score,
            "recent_avg": (
                sum(self._learning_state.recent_rewards) /
                max(len(self._learning_state.recent_rewards), 1)
            ),
            "plateau_count": self._learning_state.plateau_count,
        }

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _calculate_text_similarity(
        self,
        text1: str,
        text2: str,
    ) -> float:
        """Calculate simple text similarity using Jaccard index."""
        if not text1 or not text2:
            return 0.0

        # Tokenize
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        # Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / max(union, 1)

    def _extract_shared_features(
        self,
        text1: str,
        text2: str,
    ) -> list[str]:
        """Extract shared features (words) between texts."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        # Filter common words
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been"}
        shared = words1 & words2 - stop_words

        return list(shared)[:10]  # Top 10

    async def _get_success_patterns(
        self,
        rule_id: str,
    ) -> list[dict[str, Any]]:
        """Get success patterns for a rule."""
        result = await self.db.execute(
            select(PatternDetection)
            .where(
                and_(
                    PatternDetection.pattern_type == "success",
                    PatternDetection.active == True,
                )
            )
            .limit(5)
        )
        patterns = result.scalars().all()

        return [
            {
                "id": str(p.id),
                "description": p.description,
                "confidence": p.confidence,
            }
            for p in patterns
            if rule_id in (p.related_rules or [])
        ]

    async def _log_audit(
        self,
        action: str,
        entity_type: str,
        entity_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Log audit entry."""
        try:
            audit = AuditLog(
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                actor="meta_learning_service",
                details=details or {},
            )
            self.db.add(audit)
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log audit: {e}")


# Factory function
async def get_meta_learning_service(db: AsyncSession) -> MetaLearningService:
    """Get meta-learning service instance."""
    return MetaLearningService(db)
