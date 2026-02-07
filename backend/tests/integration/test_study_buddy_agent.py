"""
Test: Study Buddy Agent

NOTE: This test file is skipped because the study_buddy_agent module
has been archived/deprecated and is no longer available.
"""

import pytest

# Skip entire module - study_buddy_agent has been archived
pytest.skip(
    "study_buddy_agent module archived/deprecated",
    allow_module_level=True
)

import asyncio
import os
import sys
from unittest.mock import AsyncMock, patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime

from agents.study_buddy_agent import (
    DifficultyLevel,
    Flashcard,
    Question,
    QuestionType,
    Quiz,
    StudentPerformance,
    StudyBuddyAgent,
)


@pytest.fixture
def agent():
    """Study buddy agent fixture"""
    return StudyBuddyAgent()


@pytest.fixture
def sample_content():
    """Sample educational content"""
    return """
    Hücre bölünmesi, bir hücrenin iki veya daha fazla yavru hücreye bölündüğü süreçtir.
    Mitoz ve mayoz olmak üzere iki ana tip hücre bölünmesi vardır.
    Mitoz vücut hücrelerinde, mayoz ise üreme hücrelerinde gerçekleşir.
    """


@pytest.mark.asyncio
async def test_generate_flashcards(agent, sample_content):
    """Test flashcard generation"""
    with patch(
        "agents.study_buddy_agent.llm_service.generate_for_education"
    ) as mock_llm:
        mock_llm.return_value = {
            "success": True,
            "content": '{"flashcards": [{"front": "Hücre bölünmesi nedir?", "back": "Bir hücrenin yavru hücrelere bölünmesi", "category": "Biyoloji", "tags": ["hücre"]}]}',
        }

        flashcards = await agent.generate_flashcards(sample_content, count=5)

        assert len(flashcards) > 0
        assert flashcards[0].front != ""
        assert flashcards[0].back != ""
        assert flashcards[0].difficulty in [
            DifficultyLevel.EASY,
            DifficultyLevel.MEDIUM,
        ]


@pytest.mark.asyncio
async def test_generate_questions(agent, sample_content):
    """Test question generation"""
    with patch(
        "agents.study_buddy_agent.llm_service.generate_for_education"
    ) as mock_llm:
        mock_llm.return_value = {
            "success": True,
            "content": '{"questions": [{"type": "multiple_choice", "text": "Mitoz nerede gerçekleşir?", "options": ["A) Vücut hücreleri", "B) Üreme hücreleri", "C) Sinir hücreleri", "D) Kas hücreleri"], "correct": "A", "explanation": "Mitoz vücut hücrelerinde gerçekleşir"}]}',
        }

        questions = await agent.generate_questions(
            sample_content,
            [QuestionType.MULTIPLE_CHOICE],
            count=3,
            difficulty=DifficultyLevel.MEDIUM,
            subject="Biyoloji",
            topic="Hücre Bölünmesi",
        )

        assert len(questions) > 0
        assert questions[0].question_type == QuestionType.MULTIPLE_CHOICE
        assert questions[0].correct_answer != ""
        assert questions[0].points > 0


@pytest.mark.asyncio
async def test_create_quiz(agent, sample_content):
    """Test quiz creation"""
    with patch.object(agent, "generate_questions") as mock_gen:
        mock_gen.return_value = [
            Question(
                question_id="q1",
                question_type=QuestionType.MULTIPLE_CHOICE,
                question_text="Test sorusu",
                options=["A", "B", "C", "D"],
                correct_answer="A",
                explanation="Test açıklama",
                difficulty=DifficultyLevel.MEDIUM,
                subject="Test",
                topic="Test",
                points=10,
                metadata={},
            )
        ]

        quiz = await agent.create_quiz(
            title="Test Quiz",
            content=sample_content,
            question_count=5,
            adaptive=True,
            difficulty=DifficultyLevel.MEDIUM,
        )

        assert quiz is not None
        assert quiz.title == "Test Quiz"
        assert len(quiz.questions) > 0
        assert quiz.adaptive == True
        assert quiz.total_points > 0


@pytest.mark.asyncio
async def test_evaluate_answer_multiple_choice(agent):
    """Test multiple choice answer evaluation"""
    question = Question(
        question_id="q1",
        question_type=QuestionType.MULTIPLE_CHOICE,
        question_text="Test",
        options=["A", "B", "C", "D"],
        correct_answer="B",
        explanation="B doğru cevaptır",
        difficulty=DifficultyLevel.MEDIUM,
        subject="Test",
        topic="Test",
        points=10,
        metadata={},
    )

    # Correct answer
    score, feedback = await agent.evaluate_answer(question, "B")
    assert score == 10
    assert "Doğru" in feedback

    # Wrong answer
    score, feedback = await agent.evaluate_answer(question, "A")
    assert score == 0
    assert "Yanlış" in feedback


@pytest.mark.asyncio
async def test_evaluate_answer_true_false(agent):
    """Test true/false answer evaluation"""
    question = Question(
        question_id="q2",
        question_type=QuestionType.TRUE_FALSE,
        question_text="Test",
        options=None,
        correct_answer="Doğru",
        explanation="Test açıklama",
        difficulty=DifficultyLevel.EASY,
        subject="Test",
        topic="Test",
        points=5,
        metadata={},
    )

    # Correct answer
    score, feedback = await agent.evaluate_answer(question, "doğru")
    assert score == 5
    assert "Doğru" in feedback

    # Wrong answer
    score, feedback = await agent.evaluate_answer(question, "yanlış")
    assert score == 0
    assert "Yanlış" in feedback


@pytest.mark.asyncio
async def test_get_adaptive_question(agent):
    """Test adaptive question selection"""
    # Create a quiz with adaptive state
    quiz_id = "adaptive_quiz_1"

    # Add questions to pool
    questions = [
        Question(
            question_id=f"q{i}",
            question_type=QuestionType.MULTIPLE_CHOICE,
            question_text=f"Soru {i}",
            options=["A", "B", "C", "D"],
            correct_answer="A",
            explanation="Test",
            difficulty=DifficultyLevel.MEDIUM,
            subject="Test",
            topic="Test",
            points=10,
            metadata={},
        )
        for i in range(5)
    ]

    agent.adaptive_state[quiz_id] = {
        "current_difficulty": DifficultyLevel.MEDIUM,
        "question_pool": questions,
        "asked_questions": [],
        "performance_history": [],
    }

    # Get first question
    question = await agent.get_adaptive_question(quiz_id)
    assert question is not None
    assert question.question_id in [q.question_id for q in questions]

    # Test with low performance
    question = await agent.get_adaptive_question(quiz_id, previous_performance=0.2)
    assert question is not None

    # Test with high performance
    question = await agent.get_adaptive_question(quiz_id, previous_performance=0.9)
    assert question is not None


@pytest.mark.asyncio
async def test_summarize_content(agent, sample_content):
    """Test content summarization"""
    with patch(
        "agents.study_buddy_agent.llm_service.generate_for_education"
    ) as mock_llm:
        mock_llm.return_value = {
            "success": True,
            "content": "Hücre bölünmesi özeti: Mitoz ve mayoz olmak üzere iki tiptir.",
        }

        summary = await agent.summarize_content(sample_content, max_length=100)

        assert len(summary) > 0
        assert len(summary) <= len(sample_content)


@pytest.mark.asyncio
async def test_provide_feedback(agent):
    """Test student performance feedback"""
    # Create a quiz
    quiz = Quiz(
        quiz_id="test_quiz",
        title="Test",
        description="Test quiz",
        questions=[
            Question(
                question_id="q1",
                question_type=QuestionType.MULTIPLE_CHOICE,
                question_text="Soru 1",
                options=["A", "B", "C", "D"],
                correct_answer="A",
                explanation="Test",
                difficulty=DifficultyLevel.MEDIUM,
                subject="Test",
                topic="Test",
                points=10,
                metadata={},
            )
        ],
        total_points=10,
        time_limit=None,
        difficulty=DifficultyLevel.MEDIUM,
        adaptive=False,
        metadata={},
    )

    agent.quizzes["test_quiz"] = quiz

    # Provide answers
    answers = {"q1": "A"}  # Correct answer

    performance = await agent.provide_feedback("student_1", "test_quiz", answers)

    assert performance is not None
    assert performance.student_id == "student_1"
    assert performance.quiz_id == "test_quiz"
    assert performance.percentage == 100.0
    assert "Harika" in performance.feedback


def test_calculate_similarity(agent):
    """Test text similarity calculation"""
    similarity1 = agent._calculate_similarity("test metin", "test metin")
    assert similarity1 == 1.0

    similarity2 = agent._calculate_similarity("test", "farklı")
    assert similarity2 < 0.5

    similarity3 = agent._calculate_similarity("", "test")
    assert similarity3 == 0


def test_get_flashcards_by_category(agent):
    """Test getting flashcards by category"""
    # Add some flashcards
    fc1 = Flashcard(
        card_id="fc1",
        front="Test 1",
        back="Cevap 1",
        category="Matematik",
        difficulty=DifficultyLevel.EASY,
        tags=["test"],
    )
    fc2 = Flashcard(
        card_id="fc2",
        front="Test 2",
        back="Cevap 2",
        category="Fizik",
        difficulty=DifficultyLevel.MEDIUM,
        tags=["test"],
    )

    agent.flashcards["fc1"] = fc1
    agent.flashcards["fc2"] = fc2

    # Get by category
    math_cards = agent.get_flashcards_by_category("Matematik")
    assert len(math_cards) == 1
    assert math_cards[0].card_id == "fc1"

    physics_cards = agent.get_flashcards_by_category("Fizik")
    assert len(physics_cards) == 1
    assert physics_cards[0].card_id == "fc2"


@pytest.mark.asyncio
async def test_error_handling_and_recovery(agent):
    """Test error handling and recovery scenarios"""
    # Test with LLM service failure
    with patch(
        "agents.study_buddy_agent.llm_service.generate_for_education",
        new_callable=AsyncMock,
    ) as mock_llm:
        mock_llm.side_effect = Exception("LLM service unavailable")

        flashcards = await agent.generate_flashcards("test content", count=5)
        assert flashcards == [] or len(flashcards) == 0

    # Test with invalid JSON response
    with patch(
        "agents.study_buddy_agent.llm_service.generate_for_education",
        new_callable=AsyncMock,
    ) as mock_llm:
        mock_llm.return_value = {"success": True, "content": "invalid json response"}

        questions = await agent.generate_questions(
            "test content", [QuestionType.MULTIPLE_CHOICE]
        )
        assert questions == [] or len(questions) == 0

    # Test with timeout
    with patch(
        "agents.study_buddy_agent.llm_service.generate_for_education",
        new_callable=AsyncMock,
    ) as mock_llm:
        mock_llm.side_effect = asyncio.TimeoutError()

        summary = await agent.summarize_content("test", max_length=50)
        assert summary == "" or "Error" in summary


@pytest.mark.asyncio
async def test_concurrent_operations(agent):
    """Test concurrent operations for multiple students"""
    with patch(
        "agents.study_buddy_agent.llm_service.generate_for_education",
        new_callable=AsyncMock,
    ) as mock_llm:
        mock_llm.return_value = {
            "success": True,
            "content": '{"flashcards": [{"front": "Q", "back": "A", "category": "Test", "tags": []}]}',
        }

        tasks = [agent.generate_flashcards(f"Content {i}", count=3) for i in range(5)]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        successful = [r for r in results if r and not isinstance(r, Exception)]
        assert len(successful) > 0


@pytest.mark.asyncio
async def test_spaced_repetition_algorithm(agent):
    """Test spaced repetition for flashcards"""
    flashcard = Flashcard(
        card_id="sr_test",
        front="Test question",
        back="Test answer",
        category="Test",
        difficulty=DifficultyLevel.MEDIUM,
        tags=["test"],
        review_count=0,
        success_rate=0.0,
        next_review=datetime.now(),
    )

    agent.flashcards["sr_test"] = flashcard

    # Simulate successful reviews
    for i in range(3):
        updated = await agent.update_flashcard_review("sr_test", success=True)
        if updated:
            assert updated.review_count == i + 1
            assert updated.success_rate > 0

    # Simulate failed review
    updated = await agent.update_flashcard_review("sr_test", success=False)
    if updated:
        assert updated.next_review <= datetime.now()


@pytest.mark.asyncio
async def test_performance_analytics(agent):
    """Test performance analytics and insights"""
    # Create performance data
    perf = StudentPerformance(
        student_id="analytics_test",
        total_questions=50,
        correct_answers=35,
        topics_covered={"Math": 20, "Physics": 15, "Chemistry": 15},
        difficulty_performance={
            DifficultyLevel.EASY: 0.9,
            DifficultyLevel.MEDIUM: 0.7,
            DifficultyLevel.HARD: 0.5,
        },
        time_spent=3600,
        last_updated=datetime.now(),
    )

    agent.student_performances["analytics_test"] = perf

    # Get analytics
    insights = await agent.get_performance_insights("analytics_test")

    if insights:
        assert "strong_topics" in insights
        assert "weak_topics" in insights
        assert "recommended_difficulty" in insights
        assert insights["overall_performance"] == 0.7


@pytest.mark.asyncio
async def test_adaptive_difficulty_adjustment(agent):
    """Test adaptive difficulty based on performance"""
    # Initial quiz with medium difficulty
    quiz_id = "adaptive_test"

    # Setup adaptive state
    agent.adaptive_state[quiz_id] = {
        "current_difficulty": DifficultyLevel.MEDIUM,
        "performance_history": [0.3, 0.4, 0.3],  # Poor performance
        "asked_questions": [],
        "question_pool": [],
    }

    # Get adjusted difficulty
    new_difficulty = agent.adjust_difficulty(quiz_id)
    assert new_difficulty == DifficultyLevel.EASY

    # Test with good performance
    agent.adaptive_state[quiz_id]["performance_history"] = [0.9, 0.95, 0.85]
    new_difficulty = agent.adjust_difficulty(quiz_id)
    assert new_difficulty == DifficultyLevel.HARD


@pytest.mark.asyncio
async def test_multilingual_support(agent):
    """Test multilingual question generation"""
    with patch(
        "agents.study_buddy_agent.llm_service.generate_for_education"
    ) as mock_llm:
        # Turkish response
        mock_llm.return_value = {
            "success": True,
            "content": '{"questions": [{"type": "multiple_choice", "text": "Soru", "options": ["A", "B"], "correct": "A", "explanation": "Açıklama"}]}',
        }

        tr_questions = await agent.generate_questions(
            "İçerik", [QuestionType.MULTIPLE_CHOICE], language="tr"
        )

        # English response
        mock_llm.return_value = {
            "success": True,
            "content": '{"questions": [{"type": "multiple_choice", "text": "Question", "options": ["A", "B"], "correct": "A", "explanation": "Explanation"}]}',
        }

        en_questions = await agent.generate_questions(
            "Content", [QuestionType.MULTIPLE_CHOICE], language="en"
        )

        assert len(tr_questions) > 0 or len(en_questions) > 0


@pytest.mark.asyncio
async def test_question_bank_management(agent):
    """Test question bank storage and retrieval"""
    # Add questions to bank
    questions = [
        Question(
            question_id=f"bank_q{i}",
            question_type=QuestionType.MULTIPLE_CHOICE,
            question_text=f"Question {i}",
            options=["A", "B", "C", "D"],
            correct_answer="A",
            explanation="Test",
            difficulty=DifficultyLevel.MEDIUM,
            subject="Math",
            topic=f"Topic {i % 3}",
            points=10,
            metadata={"usage_count": 0},
        )
        for i in range(10)
    ]

    for q in questions:
        agent.question_bank[q.question_id] = q

    # Get questions by topic
    topic_questions = agent.get_questions_by_topic("Topic 0")
    assert len(topic_questions) >= 3

    # Get questions by subject and difficulty
    math_medium = agent.get_questions_by_criteria(
        subject="Math", difficulty=DifficultyLevel.MEDIUM
    )
    assert len(math_medium) == 10


@pytest.mark.asyncio
async def test_quiz_time_management(agent):
    """Test quiz timing and time limit enforcement"""
    quiz = Quiz(
        quiz_id="timed_quiz",
        title="Timed Test",
        description="Test with time limit",
        questions=[],
        total_points=100,
        time_limit=300,  # 5 minutes
        difficulty=DifficultyLevel.MEDIUM,
        adaptive=False,
        metadata={"start_time": datetime.now().isoformat()},
    )

    agent.quizzes["timed_quiz"] = quiz

    # Check time remaining
    remaining = agent.get_time_remaining("timed_quiz")
    assert remaining is not None
    assert remaining <= 300

    # Simulate timeout
    quiz.metadata["start_time"] = datetime.now().timestamp() - 400
    is_expired = agent.is_quiz_expired("timed_quiz")
    assert is_expired is True


@pytest.mark.asyncio
async def test_hint_generation_levels(agent):
    """Test progressive hint generation"""
    question = Question(
        question_id="hint_test",
        question_type=QuestionType.OPEN_ENDED,
        question_text="What is photosynthesis?",
        correct_answer="Process by which plants convert light to energy",
        explanation="Detailed explanation",
        difficulty=DifficultyLevel.MEDIUM,
        subject="Biology",
        topic="Photosynthesis",
        points=10,
        metadata={},
    )

    with patch(
        "agents.study_buddy_agent.llm_service.generate_for_education"
    ) as mock_llm:
        # Different hint levels
        hints = [
            "Think about plants and sunlight",
            "Plants use chlorophyll to capture light",
            "The process involves converting CO2 and water",
        ]

        for level, expected_hint in enumerate(hints, 1):
            mock_llm.return_value = {"success": True, "content": expected_hint}

            hint = await agent.get_hint(question, hint_level=level)
            assert hint == expected_hint


@pytest.mark.asyncio
async def test_quiz_review_and_corrections(agent):
    """Test quiz review and correction functionality"""
    # Create completed quiz
    quiz = Quiz(
        quiz_id="review_quiz",
        title="Completed Quiz",
        description="Test",
        questions=[
            Question(
                question_id="rq1",
                question_type=QuestionType.MULTIPLE_CHOICE,
                question_text="Question 1",
                options=["A", "B", "C", "D"],
                correct_answer="B",
                explanation="B is correct because...",
                difficulty=DifficultyLevel.MEDIUM,
                subject="Test",
                topic="Test",
                points=10,
                metadata={},
            )
        ],
        total_points=10,
        time_limit=None,
        difficulty=DifficultyLevel.MEDIUM,
        adaptive=False,
        metadata={"completed": True},
    )

    agent.quizzes["review_quiz"] = quiz

    # Student answers
    student_answers = {"rq1": "A"}  # Wrong answer

    # Get review
    review = await agent.generate_quiz_review("review_quiz", student_answers)

    if review:
        assert "corrections" in review
        assert len(review["corrections"]) > 0
        assert review["corrections"][0]["question_id"] == "rq1"
        assert review["corrections"][0]["student_answer"] == "A"
        assert review["corrections"][0]["correct_answer"] == "B"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
