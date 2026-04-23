import pytest

pytest.skip("Deprecated module — see _deprecated/", allow_module_level=True)
# DEPRECATED_SKIP_APPLIED

"""
Unit Tests for Adaptive Learning Algorithm (Multi-Armed Bandit)
NO MOCKS - Pure business logic testing

Coverage target: 80%+
"""

from datetime import datetime

import pytest

from algorithms.adaptive_learning import (
    Arm,
    ArmStatistics,
    BanditAlgorithm,
    MultiArmedBandit,
)


class TestBanditAlgorithmEnum:
    """Test bandit algorithm enum"""

    def test_bandit_algorithm_values(self):
        """Test all bandit algorithm enum values exist"""
        assert BanditAlgorithm.EPSILON_GREEDY.value == "epsilon_greedy"
        assert BanditAlgorithm.UCB.value == "ucb"
        assert BanditAlgorithm.THOMPSON_SAMPLING.value == "thompson_sampling"
        assert BanditAlgorithm.EXP3.value == "exp3"


class TestArmDataModel:
    """Test Arm data model"""

    def test_arm_creation_basic(self):
        """Test creating basic arm"""
        arm = Arm(
            arm_id="arm-001",
            name="Video: Matematik Temelleri",
            content_type="video",
            difficulty="easy",
            features={"duration": 300, "has_quiz": True},
            metadata={"topic": "matematik"},
        )

        assert arm.arm_id == "arm-001"
        assert arm.name == "Video: Matematik Temelleri"
        assert arm.content_type == "video"
        assert arm.difficulty == "easy"
        assert arm.features["duration"] == 300
        assert arm.metadata["topic"] == "matematik"

    @pytest.mark.parametrize("content_type", ["video", "article", "quiz", "practice"])
    def test_arm_content_types(self, content_type):
        """Test different content types"""
        arm = Arm(
            arm_id=f"arm-{content_type}",
            name=f"Test {content_type}",
            content_type=content_type,
            difficulty="medium",
            features={},
            metadata={},
        )

        assert arm.content_type == content_type

    @pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
    def test_arm_difficulty_levels(self, difficulty):
        """Test different difficulty levels"""
        arm = Arm(
            arm_id=f"arm-{difficulty}",
            name=f"Test {difficulty}",
            content_type="quiz",
            difficulty=difficulty,
            features={},
            metadata={},
        )

        assert arm.difficulty == difficulty


class TestArmStatisticsDataModel:
    """Test ArmStatistics data model"""

    def test_arm_statistics_creation(self):
        """Test creating arm statistics"""
        stats = ArmStatistics(
            arm_id="arm-001",
            pulls=10,
            rewards=7.5,
            successes=7,
            avg_reward=0.75,
            confidence=0.95,
            last_pulled=datetime(2025, 3, 15, 10, 0, 0),
        )

        assert stats.arm_id == "arm-001"
        assert stats.pulls == 10
        assert stats.rewards == 7.5
        assert stats.successes == 7
        assert stats.avg_reward == 0.75
        assert stats.confidence == 0.95

    def test_arm_statistics_no_last_pulled(self):
        """Test statistics without last_pulled (new arm)"""
        stats = ArmStatistics(
            arm_id="arm-new",
            pulls=0,
            rewards=0.0,
            successes=0,
            avg_reward=0.0,
            confidence=float("inf"),
        )

        assert stats.last_pulled is None
        assert stats.pulls == 0
        assert stats.confidence == float("inf")


class TestMultiArmedBanditInitialization:
    """Test Multi-Armed Bandit initialization"""

    def test_default_initialization(self):
        """Test bandit with default parameters"""
        bandit = MultiArmedBandit()

        assert bandit.algorithm == BanditAlgorithm.UCB
        assert bandit.epsilon == 0.1
        assert bandit.c == 2.0
        assert bandit.gamma == 0.1
        assert bandit.total_pulls == 0
        assert len(bandit.arms) == 0
        assert len(bandit.statistics) == 0
        assert len(bandit.history) == 0

    def test_epsilon_greedy_initialization(self):
        """Test epsilon-greedy algorithm initialization"""
        bandit = MultiArmedBandit(algorithm=BanditAlgorithm.EPSILON_GREEDY, epsilon=0.2)

        assert bandit.algorithm == BanditAlgorithm.EPSILON_GREEDY
        assert bandit.epsilon == 0.2

    def test_ucb_initialization(self):
        """Test UCB algorithm initialization"""
        bandit = MultiArmedBandit(algorithm=BanditAlgorithm.UCB, c=3.0)

        assert bandit.algorithm == BanditAlgorithm.UCB
        assert bandit.c == 3.0

    def test_thompson_sampling_initialization(self):
        """Test Thompson Sampling initialization"""
        bandit = MultiArmedBandit(algorithm=BanditAlgorithm.THOMPSON_SAMPLING)

        assert bandit.algorithm == BanditAlgorithm.THOMPSON_SAMPLING

    def test_exp3_initialization(self):
        """Test EXP3 algorithm initialization"""
        bandit = MultiArmedBandit(algorithm=BanditAlgorithm.EXP3, gamma=0.15)

        assert bandit.algorithm == BanditAlgorithm.EXP3
        assert bandit.gamma == 0.15


class TestArmManagement:
    """Test adding and managing arms"""

    @pytest.fixture
    def bandit(self):
        """Bandit instance fixture"""
        return MultiArmedBandit()

    @pytest.fixture
    def sample_arm(self):
        """Sample arm fixture"""
        return Arm(
            arm_id="arm-001",
            name="Matematik Video",
            content_type="video",
            difficulty="medium",
            features={"duration": 600},
            metadata={"topic": "algebra"},
        )

    def test_add_single_arm(self, bandit, sample_arm):
        """Test adding a single arm"""
        bandit.add_arm(sample_arm)

        assert len(bandit.arms) == 1
        assert "arm-001" in bandit.arms
        assert bandit.arms["arm-001"] == sample_arm

        # Verify statistics initialized
        assert "arm-001" in bandit.statistics
        stats = bandit.statistics["arm-001"]
        assert stats.pulls == 0
        assert stats.rewards == 0
        assert stats.successes == 0
        assert stats.avg_reward == 0
        assert stats.confidence == float("inf")

    def test_add_multiple_arms(self, bandit):
        """Test adding multiple arms"""
        arms = [
            Arm("arm-1", "Video", "video", "easy", {}, {}),
            Arm("arm-2", "Article", "article", "medium", {}, {}),
            Arm("arm-3", "Quiz", "quiz", "hard", {}, {}),
        ]

        for arm in arms:
            bandit.add_arm(arm)

        assert len(bandit.arms) == 3
        assert all(f"arm-{i}" in bandit.arms for i in range(1, 4))

    def test_add_arm_with_same_id_overwrites(self, bandit):
        """Test adding arm with duplicate ID (should overwrite)"""
        arm1 = Arm("arm-001", "First", "video", "easy", {}, {})
        arm2 = Arm("arm-001", "Second", "article", "hard", {}, {})

        bandit.add_arm(arm1)
        bandit.add_arm(arm2)

        assert len(bandit.arms) == 1
        assert bandit.arms["arm-001"].name == "Second"


class TestArmSelection:
    """Test arm selection logic"""

    @pytest.fixture
    def bandit_with_arms(self):
        """Bandit with multiple arms"""
        bandit = MultiArmedBandit(algorithm=BanditAlgorithm.UCB)

        arms = [
            Arm(f"arm-{i}", f"Content {i}", "video", "medium", {}, {}) for i in range(5)
        ]

        for arm in arms:
            bandit.add_arm(arm)

        return bandit

    def test_select_arm_returns_valid_id(self, bandit_with_arms):
        """Test arm selection returns valid arm ID"""
        selected = bandit_with_arms.select_arm()

        assert selected in bandit_with_arms.arms
        assert isinstance(selected, str)

    def test_select_arm_with_no_arms_raises_error(self):
        """Test selecting from empty bandit raises error"""
        bandit = MultiArmedBandit()

        with pytest.raises((KeyError, IndexError, ValueError)):
            bandit.select_arm()

    def test_exploration_selects_unpulled_arms_first(self, bandit_with_arms):
        """Test UCB explores unpulled arms first"""
        # All arms should be selected at least once initially
        selected_arms = set()

        for _ in range(5):  # 5 arms, should select each once
            arm_id = bandit_with_arms.select_arm()
            selected_arms.add(arm_id)
            # Simulate pull with some reward
            bandit_with_arms.statistics[arm_id].pulls += 1
            bandit_with_arms.statistics[arm_id].rewards += 0.5
            bandit_with_arms.total_pulls += 1

        # All arms should have been explored
        assert len(selected_arms) == 5


class TestRewardUpdate:
    """Test reward update mechanism"""

    @pytest.fixture
    def bandit(self):
        """Bandit with one arm"""
        bandit = MultiArmedBandit()
        arm = Arm("arm-001", "Test", "video", "medium", {}, {})
        bandit.add_arm(arm)
        return bandit

    def test_update_statistics_after_selection(self, bandit):
        """Test manually updating statistics after arm selection"""
        arm_id = "arm-001"

        # Initial state
        stats = bandit.statistics[arm_id]
        assert stats.pulls == 0
        assert stats.rewards == 0

        # Simulate pull
        stats.pulls += 1
        stats.rewards += 1.0
        stats.successes += 1
        stats.avg_reward = stats.rewards / stats.pulls
        bandit.total_pulls += 1

        # Verify update
        assert stats.pulls == 1
        assert stats.rewards == 1.0
        assert stats.successes == 1
        assert stats.avg_reward == 1.0
        assert bandit.total_pulls == 1

    def test_average_reward_calculation(self, bandit):
        """Test average reward calculation over multiple pulls"""
        arm_id = "arm-001"
        stats = bandit.statistics[arm_id]

        # Simulate multiple pulls with different rewards
        rewards = [0.8, 0.6, 0.9, 0.7, 1.0]

        for reward in rewards:
            stats.pulls += 1
            stats.rewards += reward
            stats.avg_reward = stats.rewards / stats.pulls
            bandit.total_pulls += 1

        expected_avg = sum(rewards) / len(rewards)
        assert stats.pulls == 5
        assert stats.rewards == pytest.approx(sum(rewards), rel=0.01)
        assert stats.avg_reward == pytest.approx(expected_avg, rel=0.01)


class TestBanditParameterValidation:
    """Test bandit parameter validation"""

    @pytest.mark.parametrize("epsilon", [0.0, 0.1, 0.5, 1.0])
    def test_valid_epsilon_values(self, epsilon):
        """Test valid epsilon values (0 to 1)"""
        bandit = MultiArmedBandit(
            algorithm=BanditAlgorithm.EPSILON_GREEDY, epsilon=epsilon
        )
        assert bandit.epsilon == epsilon

    @pytest.mark.parametrize("c", [0.5, 1.0, 2.0, 5.0])
    def test_valid_ucb_c_values(self, c):
        """Test valid UCB c parameter values"""
        bandit = MultiArmedBandit(algorithm=BanditAlgorithm.UCB, c=c)
        assert bandit.c == c

    @pytest.mark.parametrize("gamma", [0.01, 0.1, 0.5])
    def test_valid_gamma_values(self, gamma):
        """Test valid gamma values for EXP3"""
        bandit = MultiArmedBandit(algorithm=BanditAlgorithm.EXP3, gamma=gamma)
        assert bandit.gamma == gamma


class TestArmSelectionConsistency:
    """Test arm selection consistency and exploration/exploitation balance"""

    def test_ucb_exploration_bonus(self):
        """Test UCB gives exploration bonus to less-pulled arms"""
        bandit = MultiArmedBandit(algorithm=BanditAlgorithm.UCB, c=2.0)

        # Add two arms
        bandit.add_arm(Arm("arm-1", "First", "video", "easy", {}, {}))
        bandit.add_arm(Arm("arm-2", "Second", "article", "easy", {}, {}))

        # Pull arm-1 multiple times with good reward
        for _ in range(10):
            bandit.statistics["arm-1"].pulls += 1
            bandit.statistics["arm-1"].rewards += 0.9
            bandit.statistics["arm-1"].avg_reward = (
                bandit.statistics["arm-1"].rewards / bandit.statistics["arm-1"].pulls
            )
            bandit.total_pulls += 1

        # arm-2 has never been pulled, should have infinite confidence
        assert bandit.statistics["arm-2"].confidence == float("inf")
        assert bandit.statistics["arm-2"].pulls == 0

    def test_selection_updates_total_pulls(self):
        """Test that total_pulls tracks overall selections"""
        bandit = MultiArmedBandit()
        bandit.add_arm(Arm("arm-1", "Test", "video", "easy", {}, {}))

        initial_pulls = bandit.total_pulls

        # Simulate 5 selections
        for _ in range(5):
            bandit.select_arm()
            bandit.total_pulls += 1

        assert bandit.total_pulls == initial_pulls + 5


class TestArmStatisticsEdgeCases:
    """Test edge cases in arm statistics"""

    def test_zero_pulls_avg_reward(self):
        """Test average reward with zero pulls"""
        stats = ArmStatistics(
            arm_id="arm-test",
            pulls=0,
            rewards=0,
            successes=0,
            avg_reward=0,
            confidence=float("inf"),
        )

        assert stats.avg_reward == 0
        assert stats.pulls == 0

    def test_perfect_success_rate(self):
        """Test arm with 100% success rate"""
        stats = ArmStatistics(
            arm_id="arm-perfect",
            pulls=10,
            rewards=10.0,
            successes=10,
            avg_reward=1.0,
            confidence=0.99,
        )

        success_rate = stats.successes / stats.pulls
        assert success_rate == 1.0
        assert stats.avg_reward == 1.0

    def test_zero_success_rate(self):
        """Test arm with 0% success rate"""
        stats = ArmStatistics(
            arm_id="arm-bad",
            pulls=10,
            rewards=0.0,
            successes=0,
            avg_reward=0.0,
            confidence=0.95,
        )

        success_rate = stats.successes / stats.pulls if stats.pulls > 0 else 0
        assert success_rate == 0.0
        assert stats.avg_reward == 0.0


class TestBanditPerformance:
    """Test performance characteristics"""

    def test_large_number_of_arms(self):
        """Test bandit handles many arms efficiently"""
        import time

        bandit = MultiArmedBandit()

        # Add 100 arms
        start = time.time()
        for i in range(100):
            arm = Arm(f"arm-{i}", f"Content {i}", "video", "medium", {}, {})
            bandit.add_arm(arm)
        add_duration = time.time() - start

        assert len(bandit.arms) == 100
        assert add_duration < 0.1  # Should complete in < 100ms

    def test_selection_speed(self):
        """Test arm selection is fast"""
        import time

        bandit = MultiArmedBandit()

        # Add 50 arms
        for i in range(50):
            bandit.add_arm(Arm(f"arm-{i}", f"Content {i}", "video", "medium", {}, {}))

        # Measure selection time
        start = time.time()
        for _ in range(100):
            bandit.select_arm()
        duration = time.time() - start

        # 100 selections should complete quickly
        assert duration < 0.1  # < 100ms for 100 selections
