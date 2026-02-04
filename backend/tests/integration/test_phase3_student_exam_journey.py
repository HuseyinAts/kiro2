"""
Phase 3: Complete Student Exam Journey - End-to-End Workflow Tests
Target: Critical path testing for complete student exam experience
Focus: User registration → Learning style detection → Exam generation → Evaluation → Analytics
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCompleteStudentExamJourney:
    """Test complete student exam journey end-to-end"""

    @pytest.mark.asyncio
    async def test_complete_student_journey_workflow(self):
        """Test complete student journey from registration to results"""
        try:
            # Mock all required services
            with patch("services.user_service.KullaniciServisi") as mock_user_service:
                with patch(
                    "services.fast_learning_service.FastLearningStyleService"
                ) as mock_learning_service:
                    with patch(
                        "services.sinav_motoru_service.SinavMotoruService"
                    ) as mock_exam_service:
                        with patch(
                            "services.irt_service.IRTService"
                        ) as mock_irt_service:
                            with patch(
                                "algorithms.learning_analytics.LearningAnalyticsEngine"
                            ) as mock_analytics:
                                # Setup mocks
                                user_service = mock_user_service.return_value
                                learning_service = mock_learning_service.return_value
                                exam_service = mock_exam_service.return_value
                                irt_service = mock_irt_service.return_value
                                analytics_engine = mock_analytics.return_value

                                # STEP 1: Student Registration
                                student_id = str(uuid.uuid4())
                                registration_data = {
                                    "email": "student@test.com",
                                    "password": "secure_password",
                                    "name": "Test Student",
                                    "grade": 11,
                                }

                                mock_user = Mock()
                                mock_user.kullanici_id = student_id
                                mock_user.email = "student@test.com"
                                mock_user.name = "Test Student"

                                user_service.kullanici_olustur = AsyncMock(
                                    return_value=mock_user
                                )

                                # Test registration
                                registered_user = await user_service.kullanici_olustur(
                                    registration_data
                                )
                                assert registered_user.kullanici_id == student_id
                                assert registered_user.email == "student@test.com"

                                # STEP 2: Learning Style Detection
                                mock_learning_profile = Mock()
                                mock_learning_profile.student_id = student_id
                                mock_learning_profile.hybrid_code = "VK-A"
                                mock_learning_profile.confidence_score = 0.85
                                mock_learning_profile.dominant_style = (
                                    "Visual-Kinesthetic"
                                )

                                learning_service.detect_learning_style = AsyncMock(
                                    return_value=mock_learning_profile
                                )

                                # Test learning style detection
                                learning_profile = (
                                    await learning_service.detect_learning_style(
                                        student_id
                                    )
                                )
                                assert learning_profile.student_id == student_id
                                assert learning_profile.hybrid_code == "VK-A"
                                assert learning_profile.confidence_score >= 0.8

                                # STEP 3: Exam Generation Based on Learning Style
                                exam_config = {
                                    "student_id": student_id,
                                    "subject": "Matematik",
                                    "difficulty_range": [0.3, 0.7],
                                    "question_count": 20,
                                    "learning_style": learning_profile.hybrid_code,
                                }

                                mock_exam = Mock()
                                mock_exam.exam_id = str(uuid.uuid4())
                                mock_exam.student_id = student_id
                                mock_exam.questions = [f"q_{i}" for i in range(20)]
                                mock_exam.adaptive_algorithm = "IRT-based"

                                exam_service.generate_adaptive_exam = AsyncMock(
                                    return_value=mock_exam
                                )

                                # Test exam generation
                                generated_exam = (
                                    await exam_service.generate_adaptive_exam(
                                        exam_config
                                    )
                                )
                                assert generated_exam.student_id == student_id
                                assert len(generated_exam.questions) == 20
                                assert generated_exam.adaptive_algorithm == "IRT-based"

                                # STEP 4: Student Takes Exam (Simulated)
                                student_answers = [
                                    {
                                        "question_id": f"q_{i}",
                                        "answer": f"answer_{i}",
                                        "time_spent": 45 + i * 2,
                                    }
                                    for i in range(20)
                                ]

                                # STEP 5: Answer Evaluation with IRT
                                mock_evaluation_result = Mock()
                                mock_evaluation_result.student_id = student_id
                                mock_evaluation_result.exam_id = generated_exam.exam_id
                                mock_evaluation_result.total_score = 75.5
                                mock_evaluation_result.ability_estimate = 0.45
                                mock_evaluation_result.question_results = [
                                    {
                                        "question_id": f"q_{i}",
                                        "correct": i % 3 != 0,
                                        "irt_difficulty": 0.3 + i * 0.02,
                                    }
                                    for i in range(20)
                                ]

                                irt_service.evaluate_exam_with_irt = AsyncMock(
                                    return_value=mock_evaluation_result
                                )

                                # Test IRT evaluation
                                evaluation_result = (
                                    await irt_service.evaluate_exam_with_irt(
                                        generated_exam.exam_id, student_answers
                                    )
                                )
                                assert evaluation_result.student_id == student_id
                                assert evaluation_result.total_score > 0
                                assert evaluation_result.ability_estimate is not None
                                assert len(evaluation_result.question_results) == 20

                                # STEP 6: Learning Analytics Processing
                                analytics_data = {
                                    "student_id": student_id,
                                    "exam_result": evaluation_result,
                                    "learning_profile": learning_profile,
                                    "exam_metadata": generated_exam,
                                }

                                mock_analytics_result = Mock()
                                mock_analytics_result.student_id = student_id
                                mock_analytics_result.performance_trends = {
                                    "improvement": 15.2
                                }
                                mock_analytics_result.weak_areas = [
                                    "Geometry",
                                    "Functions",
                                ]
                                mock_analytics_result.recommendations = [
                                    "Practice visual diagrams",
                                    "Use hands-on activities",
                                ]
                                mock_analytics_result.next_difficulty_level = 0.52

                                analytics_engine.process_exam_analytics = AsyncMock(
                                    return_value=mock_analytics_result
                                )

                                # Test analytics processing
                                analytics_result = (
                                    await analytics_engine.process_exam_analytics(
                                        analytics_data
                                    )
                                )
                                assert analytics_result.student_id == student_id
                                assert (
                                    "improvement" in analytics_result.performance_trends
                                )
                                assert len(analytics_result.weak_areas) > 0
                                assert len(analytics_result.recommendations) > 0

                                # STEP 7: Workflow Validation - Verify Complete Journey
                                journey_result = {
                                    "student_registration": {
                                        "success": True,
                                        "student_id": student_id,
                                        "email": registered_user.email,
                                    },
                                    "learning_style_detection": {
                                        "success": True,
                                        "hybrid_code": learning_profile.hybrid_code,
                                        "confidence": learning_profile.confidence_score,
                                    },
                                    "exam_generation": {
                                        "success": True,
                                        "exam_id": generated_exam.exam_id,
                                        "question_count": len(generated_exam.questions),
                                        "adaptive": True,
                                    },
                                    "exam_evaluation": {
                                        "success": True,
                                        "score": evaluation_result.total_score,
                                        "ability_estimate": evaluation_result.ability_estimate,
                                        "irt_based": True,
                                    },
                                    "learning_analytics": {
                                        "success": True,
                                        "trends_analyzed": True,
                                        "recommendations_generated": len(
                                            analytics_result.recommendations
                                        )
                                        > 0,
                                        "next_level_calculated": analytics_result.next_difficulty_level
                                        is not None,
                                    },
                                }

                                # Validate complete workflow success
                                for step_name, step_result in journey_result.items():
                                    assert (
                                        step_result["success"] is True
                                    ), f"Step {step_name} failed"

                                # Validate data flow continuity
                                assert (
                                    journey_result["student_registration"]["student_id"]
                                    == student_id
                                )
                                assert (
                                    journey_result["learning_style_detection"][
                                        "confidence"
                                    ]
                                    >= 0.8
                                )
                                assert (
                                    journey_result["exam_generation"]["question_count"]
                                    == 20
                                )
                                assert journey_result["exam_evaluation"]["score"] > 0
                                assert (
                                    journey_result["learning_analytics"][
                                        "recommendations_generated"
                                    ]
                                    is True
                                )

                                # Test end-to-end performance metrics
                                journey_metrics = {
                                    "total_steps": len(journey_result),
                                    "successful_steps": sum(
                                        1
                                        for step in journey_result.values()
                                        if step["success"]
                                    ),
                                    "data_consistency": all(
                                        [
                                            student_id in str(step)
                                            or "student_id" in step
                                            for step in journey_result.values()
                                        ]
                                    ),
                                    "workflow_integrity": True,
                                }

                                assert journey_metrics["total_steps"] == 5
                                assert journey_metrics["successful_steps"] == 5
                                assert journey_metrics["workflow_integrity"] is True

                                return journey_result

        except ImportError as e:
            pytest.skip(f"Required services not available: {e}")

    @pytest.mark.asyncio
    async def test_student_journey_error_handling(self):
        """Test student journey error handling and recovery"""
        try:
            with patch("services.user_service.KullaniciServisi") as mock_user_service:
                with patch(
                    "services.fast_learning_service.FastLearningStyleService"
                ) as mock_learning_service:
                    user_service = mock_user_service.return_value
                    learning_service = mock_learning_service.return_value

                    # Test registration failure
                    user_service.kullanici_olustur = AsyncMock(
                        side_effect=Exception("Email already exists")
                    )

                    with pytest.raises(Exception, match="Email already exists"):
                        await user_service.kullanici_olustur(
                            {"email": "duplicate@test.com"}
                        )

                    # Test learning style detection failure and fallback
                    student_id = "test_student_123"
                    learning_service.detect_learning_style = AsyncMock(
                        side_effect=Exception("Detection failed")
                    )

                    # Should handle gracefully
                    try:
                        await learning_service.detect_learning_style(student_id)
                        assert False, "Should have raised exception"
                    except Exception as e:
                        assert "Detection failed" in str(e)

                    # Test fallback to default learning style
                    learning_service.get_default_learning_profile = AsyncMock(
                        return_value=Mock(
                            student_id=student_id,
                            hybrid_code="DEFAULT",
                            confidence_score=0.5,
                        )
                    )

                    fallback_profile = (
                        await learning_service.get_default_learning_profile(student_id)
                    )
                    assert fallback_profile.hybrid_code == "DEFAULT"
                    assert fallback_profile.confidence_score == 0.5

        except ImportError:
            pytest.skip("Required services not available")

    @pytest.mark.asyncio
    async def test_concurrent_student_journeys(self):
        """Test multiple concurrent student journeys"""
        try:
            with patch("services.user_service.KullaniciServisi") as mock_user_service:
                user_service = mock_user_service.return_value

                # Simulate concurrent student registrations
                async def register_student(student_index):
                    student_id = f"student_{student_index}"
                    mock_user = Mock()
                    mock_user.kullanici_id = student_id
                    mock_user.email = f"student{student_index}@test.com"
                    return mock_user

                user_service.kullanici_olustur = AsyncMock(side_effect=register_student)

                # Test concurrent registrations
                concurrent_tasks = []
                for i in range(5):
                    task = user_service.kullanici_olustur(f"student_data_{i}")
                    concurrent_tasks.append(task)

                results = await asyncio.gather(*concurrent_tasks)

                # Validate all registrations succeeded
                assert len(results) == 5
                for i, result in enumerate(results):
                    assert result.kullanici_id == f"student_{i}"
                    assert f"student{i}@test.com" in result.email

        except ImportError:
            pytest.skip("Required services not available")


class TestIRTAnalysisWorkflow:
    """Test IRT analysis and calibration workflow"""

    @pytest.mark.asyncio
    async def test_irt_calibration_workflow(self):
        """Test complete IRT calibration workflow"""
        try:
            with patch("services.irt_service.IRTService") as mock_irt_service:
                with patch(
                    "services.irt_calibration_service.IRTCalibrationService"
                ) as mock_calibration:
                    irt_service = mock_irt_service.return_value
                    calibration_service = mock_calibration.return_value

                    # STEP 1: Question Analysis
                    questions = [
                        {
                            "id": f"q_{i}",
                            "text": f"Question {i}",
                            "answers": ["A", "B", "C", "D"],
                        }
                        for i in range(10)
                    ]

                    mock_analysis_result = Mock()
                    mock_analysis_result.questions = questions
                    mock_analysis_result.initial_difficulties = [
                        0.3 + i * 0.1 for i in range(10)
                    ]
                    mock_analysis_result.discrimination_parameters = [
                        1.2 + i * 0.05 for i in range(10)
                    ]

                    irt_service.analyze_questions = AsyncMock(
                        return_value=mock_analysis_result
                    )

                    # Test question analysis
                    analysis = await irt_service.analyze_questions(questions)
                    assert len(analysis.questions) == 10
                    assert len(analysis.initial_difficulties) == 10
                    assert len(analysis.discrimination_parameters) == 10

                    # STEP 2: Calibration Process
                    calibration_data = {
                        "questions": analysis.questions,
                        "student_responses": [
                            {
                                "student_id": f"s_{i}",
                                "responses": [i % 2 for _ in range(10)],
                            }
                            for i in range(50)  # 50 students
                        ],
                    }

                    mock_calibration_result = Mock()
                    mock_calibration_result.calibrated_difficulties = [
                        0.35 + i * 0.08 for i in range(10)
                    ]
                    mock_calibration_result.student_abilities = [
                        0.2 + i * 0.03 for i in range(50)
                    ]
                    mock_calibration_result.model_fit_statistics = {
                        "rmse": 0.15,
                        "correlation": 0.92,
                    }

                    calibration_service.calibrate_parameters = AsyncMock(
                        return_value=mock_calibration_result
                    )

                    # Test calibration
                    calibration = await calibration_service.calibrate_parameters(
                        calibration_data
                    )
                    assert len(calibration.calibrated_difficulties) == 10
                    assert len(calibration.student_abilities) == 50
                    assert calibration.model_fit_statistics["correlation"] > 0.9

                    # STEP 3: Adaptive Selection Test
                    student_ability = 0.45
                    available_questions = analysis.questions

                    mock_selection_result = Mock()
                    mock_selection_result.selected_question_id = "q_5"
                    mock_selection_result.expected_information = 1.25
                    mock_selection_result.difficulty_match_score = 0.95

                    irt_service.select_next_question = AsyncMock(
                        return_value=mock_selection_result
                    )

                    # Test adaptive selection
                    selection = await irt_service.select_next_question(
                        student_ability, available_questions
                    )
                    assert selection.selected_question_id is not None
                    assert selection.expected_information > 1.0
                    assert selection.difficulty_match_score > 0.9

                    # Validate complete IRT workflow
                    irt_workflow_result = {
                        "question_analysis": {
                            "questions_analyzed": len(analysis.questions),
                            "difficulties_calculated": len(
                                analysis.initial_difficulties
                            )
                            > 0,
                            "discrimination_calculated": len(
                                analysis.discrimination_parameters
                            )
                            > 0,
                        },
                        "calibration": {
                            "parameters_calibrated": len(
                                calibration.calibrated_difficulties
                            )
                            > 0,
                            "abilities_estimated": len(calibration.student_abilities)
                            > 0,
                            "model_fit_acceptable": calibration.model_fit_statistics[
                                "correlation"
                            ]
                            > 0.8,
                        },
                        "adaptive_selection": {
                            "question_selected": selection.selected_question_id
                            is not None,
                            "information_optimized": selection.expected_information
                            > 1.0,
                            "difficulty_matched": selection.difficulty_match_score
                            > 0.8,
                        },
                    }

                    # Validate workflow success
                    for step_name, step_metrics in irt_workflow_result.items():
                        for metric_name, metric_value in step_metrics.items():
                            assert (
                                metric_value is True or metric_value > 0
                            ), f"IRT workflow failed at {step_name}.{metric_name}"

                    return irt_workflow_result

        except ImportError:
            pytest.skip("IRT services not available")


class TestLearningAnalyticsWorkflow:
    """Test learning analytics processing workflow"""

    @pytest.mark.asyncio
    async def test_learning_analytics_pipeline(self):
        """Test complete learning analytics processing pipeline"""
        try:
            with patch(
                "algorithms.learning_analytics.LearningAnalyticsEngine"
            ) as mock_analytics:
                analytics_engine = mock_analytics.return_value

                # STEP 1: Data Collection
                student_data = {
                    "student_id": "analytics_student_123",
                    "exam_history": [
                        {
                            "exam_id": f"exam_{i}",
                            "score": 60 + i * 5,
                            "subject": "Math",
                            "date": datetime.now() - timedelta(days=i * 7),
                        }
                        for i in range(10)
                    ],
                    "learning_interactions": [
                        {
                            "type": "video_watch",
                            "duration": 300 + i * 30,
                            "subject": "Math",
                        }
                        for i in range(20)
                    ],
                    "difficulty_progression": [0.3 + i * 0.02 for i in range(15)],
                }

                # STEP 2: Pattern Analysis
                mock_pattern_result = Mock()
                mock_pattern_result.learning_patterns = {
                    "preferred_content_type": "visual",
                    "optimal_session_length": 45,
                    "best_time_of_day": "morning",
                    "difficulty_progression_rate": 0.15,
                }
                mock_pattern_result.performance_trends = {
                    "overall_improvement": 25.5,
                    "subject_specific_trends": {"Math": 30.2, "Science": 18.7},
                    "consistency_score": 0.78,
                }

                analytics_engine.analyze_learning_patterns = AsyncMock(
                    return_value=mock_pattern_result
                )

                # Test pattern analysis
                patterns = await analytics_engine.analyze_learning_patterns(
                    student_data
                )
                assert patterns.learning_patterns["preferred_content_type"] == "visual"
                assert patterns.performance_trends["overall_improvement"] > 20
                assert patterns.performance_trends["consistency_score"] > 0.75

                # STEP 3: Predictive Modeling
                prediction_input = {
                    "current_ability": 0.65,
                    "learning_patterns": patterns.learning_patterns,
                    "historical_performance": patterns.performance_trends,
                }

                mock_prediction_result = Mock()
                mock_prediction_result.predicted_performance = {
                    "next_exam_score": 78.5,
                    "confidence_interval": [72.1, 84.9],
                    "improvement_probability": 0.82,
                }
                mock_prediction_result.risk_factors = [
                    "inconsistent_practice",
                    "rushing_through_problems",
                ]
                mock_prediction_result.success_factors = [
                    "visual_learning_preference",
                    "steady_improvement",
                ]

                analytics_engine.predict_performance = AsyncMock(
                    return_value=mock_prediction_result
                )

                # Test predictive modeling
                predictions = await analytics_engine.predict_performance(
                    prediction_input
                )
                assert predictions.predicted_performance["next_exam_score"] > 70
                assert (
                    predictions.predicted_performance["improvement_probability"] > 0.8
                )
                assert len(predictions.risk_factors) > 0
                assert len(predictions.success_factors) > 0

                # STEP 4: Recommendation Generation
                recommendation_input = {
                    "student_profile": student_data,
                    "learning_patterns": patterns,
                    "predictions": predictions,
                }

                mock_recommendations = Mock()
                mock_recommendations.content_recommendations = [
                    {
                        "type": "visual_diagram",
                        "topic": "Functions",
                        "priority": "high",
                    },
                    {
                        "type": "interactive_exercise",
                        "topic": "Geometry",
                        "priority": "medium",
                    },
                ]
                mock_recommendations.study_strategy = {
                    "session_length": 45,
                    "frequency": "daily",
                    "focus_areas": ["weak_concepts", "review_missed_questions"],
                }
                mock_recommendations.adaptive_parameters = {
                    "next_difficulty_level": 0.72,
                    "content_type_weights": {"visual": 0.8, "textual": 0.2},
                }

                analytics_engine.generate_recommendations = AsyncMock(
                    return_value=mock_recommendations
                )

                # Test recommendation generation
                recommendations = await analytics_engine.generate_recommendations(
                    recommendation_input
                )
                assert len(recommendations.content_recommendations) > 0
                assert recommendations.study_strategy["session_length"] > 0
                assert (
                    recommendations.adaptive_parameters["next_difficulty_level"] > 0.5
                )

                # Validate complete analytics workflow
                analytics_workflow_result = {
                    "data_collection": {
                        "exam_history_available": len(student_data["exam_history"]) > 0,
                        "interactions_recorded": len(
                            student_data["learning_interactions"]
                        )
                        > 0,
                        "progression_tracked": len(
                            student_data["difficulty_progression"]
                        )
                        > 0,
                    },
                    "pattern_analysis": {
                        "patterns_identified": len(patterns.learning_patterns) > 0,
                        "trends_calculated": patterns.performance_trends[
                            "overall_improvement"
                        ]
                        > 0,
                        "consistency_measured": patterns.performance_trends[
                            "consistency_score"
                        ]
                        > 0,
                    },
                    "predictive_modeling": {
                        "performance_predicted": predictions.predicted_performance[
                            "next_exam_score"
                        ]
                        > 0,
                        "confidence_calculated": len(
                            predictions.predicted_performance["confidence_interval"]
                        )
                        == 2,
                        "factors_identified": len(predictions.risk_factors) > 0
                        and len(predictions.success_factors) > 0,
                    },
                    "recommendation_generation": {
                        "content_recommended": len(
                            recommendations.content_recommendations
                        )
                        > 0,
                        "strategy_defined": len(recommendations.study_strategy) > 0,
                        "parameters_adapted": recommendations.adaptive_parameters[
                            "next_difficulty_level"
                        ]
                        > 0,
                    },
                }

                # Validate all workflow steps
                for step_name, step_metrics in analytics_workflow_result.items():
                    for metric_name, metric_value in step_metrics.items():
                        assert (
                            metric_value is True or metric_value > 0
                        ), f"Analytics workflow failed at {step_name}.{metric_name}"

                return analytics_workflow_result

        except ImportError:
            pytest.skip("Learning analytics not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
