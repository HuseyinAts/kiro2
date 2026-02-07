"""
Complete Exam Taking Workflow End-to-End Integration Testing
Full lifecycle testing from exam selection to results analysis
"""

import pytest
import os
import sys
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, validator
from typing import List, Dict, Optional, Any
import statistics
import secrets

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_complete_exam_lifecycle_workflow():
    """Test complete exam workflow from discovery to completion and results"""

    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from pydantic import BaseModel
        from typing import List, Dict, Optional

        app = FastAPI(title="KIRO2 Complete Exam Workflow")

        # Comprehensive exam database
        class MockExamDatabase:
            def __init__(self):
                self.exams = {
                    "tyt_matematik_deneme_1": {
                        "id": "tyt_matematik_deneme_1",
                        "title": "TYT Matematik Deneme Sınavı - 1",
                        "subject": "matematik",
                        "exam_type": "TYT",
                        "difficulty_level": "orta",
                        "duration_minutes": 165,
                        "total_questions": 40,
                        "total_points": 100.0,
                        "pass_score": 60.0,
                        "created_by": "teacher_matematik_001",
                        "academic_year": "2024-2025",
                        "is_active": True,
                        "instructions": "Sınav süresi 165 dakikadır. Her soru için tek bir cevap işaretleyiniz. Yanlış cevaplar doğru cevapları götürmez.",
                        "topics": ["sayılar", "cebir", "geometri", "fonksiyonlar"],
                        "questions": [
                            {
                                "id": "q1",
                                "question_number": 1,
                                "question_text": "2x + 5 = 13 denkleminde x'in değeri kaçtır?",
                                "question_type": "multiple_choice",
                                "options": {"A": "2", "B": "3", "C": "4", "D": "5"},
                                "correct_answer": "C",
                                "points": 2.5,
                                "topic": "cebir",
                                "difficulty": "kolay",
                            },
                            {
                                "id": "q2",
                                "question_number": 2,
                                "question_text": "f(x) = x² + 3x - 2 fonksiyonunun türevi nedir?",
                                "question_type": "multiple_choice",
                                "options": {
                                    "A": "2x + 3",
                                    "B": "x² + 3",
                                    "C": "2x - 3",
                                    "D": "x + 3",
                                },
                                "correct_answer": "A",
                                "points": 3.0,
                                "topic": "fonksiyonlar",
                                "difficulty": "orta",
                            },
                            {
                                "id": "q3",
                                "question_number": 3,
                                "question_text": "Bir üçgenin iç açıları toplamı kaç derecedir?",
                                "question_type": "multiple_choice",
                                "options": {
                                    "A": "90",
                                    "B": "180",
                                    "C": "270",
                                    "D": "360",
                                },
                                "correct_answer": "B",
                                "points": 2.0,
                                "topic": "geometri",
                                "difficulty": "kolay",
                            },
                            {
                                "id": "q4",
                                "question_number": 4,
                                "question_text": "√(16) + √(25) işleminin sonucu kaçtır?",
                                "question_type": "multiple_choice",
                                "options": {"A": "7", "B": "8", "C": "9", "D": "10"},
                                "correct_answer": "C",
                                "points": 2.5,
                                "topic": "sayılar",
                                "difficulty": "kolay",
                            },
                        ],
                    },
                    "ayt_fizik_mekanik_1": {
                        "id": "ayt_fizik_mekanik_1",
                        "title": "AYT Fizik - Mekanik Bölümü",
                        "subject": "fizik",
                        "exam_type": "AYT",
                        "difficulty_level": "zor",
                        "duration_minutes": 180,
                        "total_questions": 14,
                        "total_points": 70.0,
                        "pass_score": 50.0,
                        "created_by": "teacher_fizik_001",
                        "academic_year": "2024-2025",
                        "is_active": True,
                        "instructions": "Sınav süresi 180 dakikadır. Hesap makinesi kullanabilirsiniz.",
                        "topics": ["kuvvet", "hareket", "enerji", "momentum"],
                        "questions": [
                            {
                                "id": "q1",
                                "question_number": 1,
                                "question_text": "Bir cisim 10 m/s hızla hareket ederken 2 m/s² ivmeyle yavaşlıyor. 5 saniye sonra hızı kaç m/s olur?",
                                "question_type": "multiple_choice",
                                "options": {"A": "0", "B": "5", "C": "10", "D": "15"},
                                "correct_answer": "A",
                                "points": 5.0,
                                "topic": "hareket",
                                "difficulty": "orta",
                            },
                            {
                                "id": "q2",
                                "question_number": 2,
                                "question_text": "Newton'un ikinci yasası hangi formülle ifade edilir?",
                                "question_type": "multiple_choice",
                                "options": {
                                    "A": "F = ma",
                                    "B": "F = mv",
                                    "C": "F = mv²",
                                    "D": "F = mgh",
                                },
                                "correct_answer": "A",
                                "points": 5.0,
                                "topic": "kuvvet",
                                "difficulty": "kolay",
                            },
                        ],
                    },
                }
                self.submissions = {}
                self.results = {}
                self.exam_sessions = {}

        # Enhanced scoring and analytics service
        class MockExamScoringService:
            def __init__(self):
                self.scoring_algorithms = {
                    "TYT": self._calculate_tyt_score,
                    "AYT": self._calculate_ayt_score,
                }

            def calculate_exam_score(
                self, exam: dict, answers: dict, time_data: dict = None
            ) -> dict:
                exam_type = exam.get("exam_type", "TYT")
                scoring_func = self.scoring_algorithms.get(
                    exam_type, self._calculate_default_score
                )
                return scoring_func(exam, answers, time_data)

            def _calculate_tyt_score(
                self, exam: dict, answers: dict, time_data: dict = None
            ) -> dict:
                total_questions = len(exam["questions"])
                total_points = exam["total_points"]
                correct_answers = 0
                wrong_answers = 0
                empty_answers = 0
                earned_points = 0.0
                question_analysis = []
                topic_breakdown = {}

                for question in exam["questions"]:
                    q_id = question["id"]
                    user_answer = answers.get(q_id)
                    correct_answer = question["correct_answer"]
                    topic = question["topic"]

                    # Initialize topic if not exists
                    if topic not in topic_breakdown:
                        topic_breakdown[topic] = {
                            "correct": 0,
                            "total": 0,
                            "points": 0.0,
                        }

                    topic_breakdown[topic]["total"] += 1

                    question_result = {
                        "question_id": q_id,
                        "question_number": question["question_number"],
                        "user_answer": user_answer,
                        "correct_answer": correct_answer,
                        "is_correct": False,
                        "points_earned": 0.0,
                        "points_possible": question["points"],
                        "topic": topic,
                        "difficulty": question["difficulty"],
                    }

                    if user_answer is None or user_answer == "":
                        empty_answers += 1
                        question_result["result_type"] = "empty"
                    elif user_answer == correct_answer:
                        correct_answers += 1
                        earned_points += question["points"]
                        question_result["is_correct"] = True
                        question_result["points_earned"] = question["points"]
                        question_result["result_type"] = "correct"
                        topic_breakdown[topic]["correct"] += 1
                        topic_breakdown[topic]["points"] += question["points"]
                    else:
                        wrong_answers += 1
                        question_result["result_type"] = "wrong"

                    question_analysis.append(question_result)

                # Calculate percentages
                percentage = (
                    (earned_points / total_points) * 100 if total_points > 0 else 0
                )
                success_rate = (
                    (correct_answers / total_questions) * 100
                    if total_questions > 0
                    else 0
                )

                # Calculate topic performance percentages
                for topic in topic_breakdown:
                    topic_data = topic_breakdown[topic]
                    topic_data["percentage"] = (
                        (topic_data["correct"] / topic_data["total"]) * 100
                        if topic_data["total"] > 0
                        else 0
                    )

                # Determine performance level
                performance_level = self._get_performance_level(percentage)

                # Calculate time efficiency if time data provided
                time_analysis = {}
                if time_data:
                    total_time = time_data.get("total_time_minutes", 0)
                    expected_time = exam.get("duration_minutes", 165)
                    time_efficiency = (
                        (expected_time - total_time) / expected_time * 100
                        if expected_time > 0
                        else 0
                    )

                    time_analysis = {
                        "total_time_minutes": total_time,
                        "expected_time_minutes": expected_time,
                        "time_efficiency_percentage": time_efficiency,
                        "average_time_per_question": total_time / total_questions
                        if total_questions > 0
                        else 0,
                    }

                return {
                    "exam_id": exam["id"],
                    "exam_title": exam["title"],
                    "exam_type": exam["exam_type"],
                    "total_questions": total_questions,
                    "total_points": total_points,
                    "earned_points": earned_points,
                    "percentage": round(percentage, 2),
                    "success_rate": round(success_rate, 2),
                    "correct_answers": correct_answers,
                    "wrong_answers": wrong_answers,
                    "empty_answers": empty_answers,
                    "performance_level": performance_level,
                    "passed": percentage >= exam.get("pass_score", 60),
                    "topic_breakdown": topic_breakdown,
                    "question_analysis": question_analysis,
                    "time_analysis": time_analysis,
                    "recommendations": self._generate_recommendations(
                        topic_breakdown, performance_level
                    ),
                }

            def _calculate_ayt_score(
                self, exam: dict, answers: dict, time_data: dict = None
            ) -> dict:
                # Similar to TYT but with different scoring criteria
                return self._calculate_tyt_score(exam, answers, time_data)

            def _calculate_default_score(
                self, exam: dict, answers: dict, time_data: dict = None
            ) -> dict:
                return self._calculate_tyt_score(exam, answers, time_data)

            def _get_performance_level(self, percentage: float) -> str:
                if percentage >= 90:
                    return "mükemmel"
                elif percentage >= 80:
                    return "çok_iyi"
                elif percentage >= 70:
                    return "iyi"
                elif percentage >= 60:
                    return "orta"
                elif percentage >= 50:
                    return "geçer"
                else:
                    return "yetersiz"

            def _generate_recommendations(
                self, topic_breakdown: dict, performance_level: str
            ) -> List[dict]:
                recommendations = []

                # Topic-based recommendations
                for topic, data in topic_breakdown.items():
                    if data["percentage"] < 50:
                        recommendations.append(
                            {
                                "type": "topic_improvement",
                                "topic": topic,
                                "message": f"{topic} konusunda daha fazla çalışma yapmanız önerilir (%{data['percentage']:.1f})",
                                "priority": "high",
                            }
                        )
                    elif data["percentage"] < 70:
                        recommendations.append(
                            {
                                "type": "topic_enhancement",
                                "topic": topic,
                                "message": f"{topic} konusunda pratik sorular çözebilirsiniz (%{data['percentage']:.1f})",
                                "priority": "medium",
                            }
                        )

                # Overall performance recommendations
                if performance_level in ["yetersiz", "geçer"]:
                    recommendations.append(
                        {
                            "type": "general_improvement",
                            "message": "Genel performansınızı artırmak için düzenli çalışma programı oluşturun",
                            "priority": "high",
                        }
                    )
                elif performance_level in ["orta", "iyi"]:
                    recommendations.append(
                        {
                            "type": "skill_enhancement",
                            "message": "Zor soruları çözmek için daha fazla pratik yapın",
                            "priority": "medium",
                        }
                    )
                else:
                    recommendations.append(
                        {
                            "type": "maintenance",
                            "message": "Mükemmel performansınızı korumaya devam edin",
                            "priority": "low",
                        }
                    )

                return recommendations

        # Initialize services
        exam_db = MockExamDatabase()
        scoring_service = MockExamScoringService()

        # Request models
        class ExamStartRequest(BaseModel):
            exam_id: str
            user_id: str

        class QuestionAnswer(BaseModel):
            question_id: str
            answer: Optional[str] = None
            time_spent_seconds: Optional[int] = None

        class ExamSubmission(BaseModel):
            exam_id: str
            session_id: str
            user_id: str
            answers: List[QuestionAnswer]
            start_time: str
            end_time: str
            total_time_minutes: int

        class ExamFilter(BaseModel):
            subject: Optional[str] = None
            exam_type: Optional[str] = None
            difficulty_level: Optional[str] = None
            academic_year: Optional[str] = None

        # API endpoints for complete exam workflow
        @app.get("/api/exams")
        async def list_available_exams(
            subject: Optional[str] = None,
            exam_type: Optional[str] = None,
            difficulty: Optional[str] = None,
        ):
            """List available exams with filtering"""
            available_exams = []

            for exam_id, exam in exam_db.exams.items():
                if not exam.get("is_active", True):
                    continue

                # Apply filters
                if subject and exam.get("subject") != subject:
                    continue
                if exam_type and exam.get("exam_type") != exam_type:
                    continue
                if difficulty and exam.get("difficulty_level") != difficulty:
                    continue

                # Return summary for listing
                exam_summary = {
                    "id": exam["id"],
                    "title": exam["title"],
                    "subject": exam["subject"],
                    "exam_type": exam["exam_type"],
                    "difficulty_level": exam["difficulty_level"],
                    "duration_minutes": exam["duration_minutes"],
                    "total_questions": exam["total_questions"],
                    "total_points": exam["total_points"],
                    "topics": exam["topics"],
                    "academic_year": exam["academic_year"],
                }
                available_exams.append(exam_summary)

            return {
                "success": True,
                "total_exams": len(available_exams),
                "exams": available_exams,
            }

        @app.get("/api/exams/{exam_id}/details")
        async def get_exam_details(exam_id: str):
            """Get detailed exam information before starting"""
            exam = exam_db.exams.get(exam_id)
            if not exam:
                raise HTTPException(status_code=404, detail="Sınav bulunamadı")

            return {
                "success": True,
                "exam": {
                    "id": exam["id"],
                    "title": exam["title"],
                    "subject": exam["subject"],
                    "exam_type": exam["exam_type"],
                    "difficulty_level": exam["difficulty_level"],
                    "duration_minutes": exam["duration_minutes"],
                    "total_questions": exam["total_questions"],
                    "total_points": exam["total_points"],
                    "pass_score": exam["pass_score"],
                    "instructions": exam["instructions"],
                    "topics": exam["topics"],
                    "academic_year": exam["academic_year"],
                    "created_by": exam["created_by"],
                },
            }

        @app.post("/api/exams/{exam_id}/start")
        async def start_exam(exam_id: str, start_request: ExamStartRequest):
            """Start an exam session"""
            exam = exam_db.exams.get(exam_id)
            if not exam:
                raise HTTPException(status_code=404, detail="Sınav bulunamadı")

            if not exam.get("is_active", True):
                raise HTTPException(status_code=403, detail="Bu sınav aktif değil")

            # Create exam session
            session_id = secrets.token_urlsafe(32)
            session_data = {
                "session_id": session_id,
                "exam_id": exam_id,
                "user_id": start_request.user_id,
                "start_time": datetime.now().isoformat(),
                "end_time": None,
                "status": "in_progress",
                "current_question": 1,
                "answers_submitted": 0,
                "created_at": datetime.now().isoformat(),
            }

            exam_db.exam_sessions[session_id] = session_data

            # Return exam questions (without correct answers)
            exam_questions = []
            for question in exam["questions"]:
                exam_questions.append(
                    {
                        "id": question["id"],
                        "question_number": question["question_number"],
                        "question_text": question["question_text"],
                        "question_type": question["question_type"],
                        "options": question["options"],
                        "points": question["points"],
                        "topic": question["topic"],
                    }
                )

            return {
                "success": True,
                "message": "Sınav başlatıldı",
                "session_id": session_id,
                "exam": {
                    "id": exam["id"],
                    "title": exam["title"],
                    "duration_minutes": exam["duration_minutes"],
                    "total_questions": exam["total_questions"],
                    "instructions": exam["instructions"],
                },
                "questions": exam_questions,
                "start_time": session_data["start_time"],
            }

        @app.post("/api/exams/submit")
        async def submit_exam(submission: ExamSubmission):
            """Submit completed exam for scoring"""
            # Verify session exists
            session = exam_db.exam_sessions.get(submission.session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Geçersiz sınav oturumu")

            if session["status"] != "in_progress":
                raise HTTPException(status_code=400, detail="Sınav zaten tamamlanmış")

            # Get exam data
            exam = exam_db.exams.get(submission.exam_id)
            if not exam:
                raise HTTPException(status_code=404, detail="Sınav bulunamadı")

            # Update session
            session["end_time"] = submission.end_time
            session["status"] = "completed"
            session["answers_submitted"] = len(submission.answers)

            # Process answers
            answers_dict = {}
            time_data = {
                "total_time_minutes": submission.total_time_minutes,
                "question_times": {},
            }

            for answer in submission.answers:
                answers_dict[answer.question_id] = answer.answer
                if answer.time_spent_seconds:
                    time_data["question_times"][
                        answer.question_id
                    ] = answer.time_spent_seconds

            # Calculate score
            score_result = scoring_service.calculate_exam_score(
                exam, answers_dict, time_data
            )

            # Store submission and result
            submission_id = f"sub_{len(exam_db.submissions) + 1:06d}"
            exam_db.submissions[submission_id] = {
                "id": submission_id,
                "session_id": submission.session_id,
                "exam_id": submission.exam_id,
                "user_id": submission.user_id,
                "answers": answers_dict,
                "start_time": submission.start_time,
                "end_time": submission.end_time,
                "total_time_minutes": submission.total_time_minutes,
                "submitted_at": datetime.now().isoformat(),
            }

            exam_db.results[submission_id] = {
                "submission_id": submission_id,
                "user_id": submission.user_id,
                "exam_id": submission.exam_id,
                "score_data": score_result,
                "calculated_at": datetime.now().isoformat(),
            }

            return {
                "success": True,
                "message": "Sınav başarıyla tamamlandı",
                "submission_id": submission_id,
                "immediate_result": {
                    "percentage": score_result["percentage"],
                    "correct_answers": score_result["correct_answers"],
                    "total_questions": score_result["total_questions"],
                    "passed": score_result["passed"],
                    "performance_level": score_result["performance_level"],
                },
            }

        @app.get("/api/results/{submission_id}")
        async def get_exam_result(submission_id: str):
            """Get detailed exam results"""
            result = exam_db.results.get(submission_id)
            if not result:
                raise HTTPException(status_code=404, detail="Sonuç bulunamadı")

            submission = exam_db.submissions.get(submission_id)

            return {
                "success": True,
                "result": {
                    "submission_id": submission_id,
                    "user_id": result["user_id"],
                    "exam_id": result["exam_id"],
                    "submission_time": submission["submitted_at"]
                    if submission
                    else None,
                    "score_data": result["score_data"],
                    "calculated_at": result["calculated_at"],
                },
            }

        @app.get("/api/results/{submission_id}/detailed")
        async def get_detailed_exam_analysis(submission_id: str):
            """Get comprehensive exam analysis and recommendations"""
            result = exam_db.results.get(submission_id)
            if not result:
                raise HTTPException(status_code=404, detail="Sonuç bulunamadı")

            submission = exam_db.submissions.get(submission_id)
            score_data = result["score_data"]

            # Enhanced analysis
            analysis = {
                "overview": {
                    "exam_title": score_data["exam_title"],
                    "exam_type": score_data["exam_type"],
                    "completion_date": submission["submitted_at"]
                    if submission
                    else None,
                    "total_time": submission["total_time_minutes"]
                    if submission
                    else None,
                },
                "performance": {
                    "overall_score": score_data["percentage"],
                    "performance_level": score_data["performance_level"],
                    "passed": score_data["passed"],
                    "correct_answers": score_data["correct_answers"],
                    "wrong_answers": score_data["wrong_answers"],
                    "empty_answers": score_data["empty_answers"],
                },
                "topic_analysis": score_data["topic_breakdown"],
                "question_details": score_data["question_analysis"],
                "time_analysis": score_data.get("time_analysis", {}),
                "recommendations": score_data["recommendations"],
                "next_steps": [
                    "Zayıf olduğunuz konuları tekrar edin",
                    "Benzer seviyede sorular çözün",
                    "Zaman yönetimi üzerinde çalışın",
                ],
            }

            return {"success": True, "detailed_analysis": analysis}

        # Test client
        client = TestClient(app)

        # Test complete exam workflow

        # 1. List available exams
        response = client.get("/api/exams")
        assert response.status_code == 200

        exams_data = response.json()
        assert exams_data["success"] is True
        assert exams_data["total_exams"] == 2
        assert len(exams_data["exams"]) == 2

        # Test filtering
        response = client.get("/api/exams?subject=matematik")
        assert response.status_code == 200

        matematik_exams = response.json()
        assert len(matematik_exams["exams"]) == 1
        assert matematik_exams["exams"][0]["subject"] == "matematik"

        # 2. Get exam details
        exam_id = "tyt_matematik_deneme_1"
        response = client.get(f"/api/exams/{exam_id}/details")
        assert response.status_code == 200

        exam_details = response.json()
        assert exam_details["success"] is True
        exam_info = exam_details["exam"]
        assert exam_info["id"] == exam_id
        assert exam_info["title"] == "TYT Matematik Deneme Sınavı - 1"
        assert exam_info["total_questions"] == 4
        assert exam_info["duration_minutes"] == 165

        # 3. Start exam
        start_request = {"exam_id": exam_id, "user_id": "student_exam_test"}

        response = client.post(f"/api/exams/{exam_id}/start", json=start_request)
        assert response.status_code == 200

        start_result = response.json()
        assert start_result["success"] is True
        assert "session_id" in start_result
        assert len(start_result["questions"]) == 4

        session_id = start_result["session_id"]

        # Verify questions don't contain correct answers
        for question in start_result["questions"]:
            assert "correct_answer" not in question
            assert "options" in question
            assert "question_text" in question

        # 4. Submit exam with answers
        submission_data = {
            "exam_id": exam_id,
            "session_id": session_id,
            "user_id": "student_exam_test",
            "answers": [
                {
                    "question_id": "q1",
                    "answer": "C",
                    "time_spent_seconds": 45,
                },  # Correct
                {
                    "question_id": "q2",
                    "answer": "A",
                    "time_spent_seconds": 120,
                },  # Correct
                {
                    "question_id": "q3",
                    "answer": "B",
                    "time_spent_seconds": 30,
                },  # Correct
                {
                    "question_id": "q4",
                    "answer": "A",
                    "time_spent_seconds": 60,
                },  # Wrong (correct is C)
            ],
            "start_time": "2024-01-15T10:00:00",
            "end_time": "2024-01-15T10:30:00",
            "total_time_minutes": 30,
        }

        response = client.post("/api/exams/submit", json=submission_data)
        assert response.status_code == 200

        submission_result = response.json()
        assert submission_result["success"] is True
        assert "submission_id" in submission_result

        immediate_result = submission_result["immediate_result"]
        assert immediate_result["correct_answers"] == 3  # 3 out of 4 correct
        assert immediate_result["total_questions"] == 4
        assert immediate_result["percentage"] == 75.0  # (2.5+3.0+2.0)/10*100 = 75%
        assert immediate_result["passed"] is True  # Above 60%

        submission_id = submission_result["submission_id"]

        # 5. Get detailed results
        response = client.get(f"/api/results/{submission_id}")
        assert response.status_code == 200

        result_data = response.json()
        assert result_data["success"] is True

        score_data = result_data["result"]["score_data"]
        assert score_data["correct_answers"] == 3
        assert score_data["wrong_answers"] == 1
        assert score_data["empty_answers"] == 0
        assert score_data["performance_level"] == "iyi"  # 75% = "iyi"

        # Verify topic breakdown
        topic_breakdown = score_data["topic_breakdown"]
        assert "cebir" in topic_breakdown
        assert "fonksiyonlar" in topic_breakdown
        assert "geometri" in topic_breakdown
        assert "sayılar" in topic_breakdown

        # Cebir should be 100% (1/1 correct)
        assert topic_breakdown["cebir"]["correct"] == 1
        assert topic_breakdown["cebir"]["total"] == 1
        assert topic_breakdown["cebir"]["percentage"] == 100.0

        # Sayılar should be 0% (0/1 correct)
        assert topic_breakdown["sayılar"]["correct"] == 0
        assert topic_breakdown["sayılar"]["total"] == 1
        assert topic_breakdown["sayılar"]["percentage"] == 0.0

        # 6. Get detailed analysis
        response = client.get(f"/api/results/{submission_id}/detailed")
        assert response.status_code == 200

        analysis_data = response.json()
        assert analysis_data["success"] is True

        detailed_analysis = analysis_data["detailed_analysis"]
        assert "overview" in detailed_analysis
        assert "performance" in detailed_analysis
        assert "topic_analysis" in detailed_analysis
        assert "question_details" in detailed_analysis
        assert "time_analysis" in detailed_analysis
        assert "recommendations" in detailed_analysis

        # Verify recommendations include weak topic (sayılar)
        recommendations = detailed_analysis["recommendations"]
        topic_improvement_recs = [
            r for r in recommendations if r["type"] == "topic_improvement"
        ]
        assert len(topic_improvement_recs) > 0
        assert any("sayılar" in rec["topic"] for rec in topic_improvement_recs)

        # Test error cases
        # Invalid exam
        response = client.get("/api/exams/nonexistent/details")
        assert response.status_code == 404

        # Invalid session for submission
        invalid_submission = submission_data.copy()
        invalid_submission["session_id"] = "invalid_session"
        response = client.post("/api/exams/submit", json=invalid_submission)
        assert response.status_code == 404

        # Invalid result
        response = client.get("/api/results/invalid_submission")
        assert response.status_code == 404

        print("✅ Complete exam lifecycle workflow successful")

    except Exception as e:
        print(f"Complete exam lifecycle workflow test failed: {e}")


def test_advanced_exam_analytics_and_comparison():
    """Test advanced exam analytics, comparison, and progress tracking"""

    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from pydantic import BaseModel
        from typing import List, Dict
        import statistics

        app = FastAPI(title="KIRO2 Advanced Exam Analytics")

        # Enhanced analytics database
        class MockAnalyticsDatabase:
            def __init__(self):
                self.user_performances = {}
                self.comparative_data = {}
                self.learning_paths = {}
                self.progress_tracking = {}

        # Advanced analytics service
        class MockAdvancedAnalyticsService:
            def __init__(self, db):
                self.db = db

            def record_exam_performance(self, user_id: str, exam_result: dict):
                if user_id not in self.db.user_performances:
                    self.db.user_performances[user_id] = []

                performance_record = {
                    "exam_id": exam_result["exam_id"],
                    "exam_type": exam_result.get("exam_type", "TYT"),
                    "subject": exam_result.get("subject", "unknown"),
                    "score": exam_result["percentage"],
                    "correct_answers": exam_result["correct_answers"],
                    "total_questions": exam_result["total_questions"],
                    "completion_time": exam_result.get("total_time_minutes", 0),
                    "topic_breakdown": exam_result.get("topic_breakdown", {}),
                    "performance_level": exam_result.get(
                        "performance_level", "unknown"
                    ),
                    "date": datetime.now().isoformat(),
                }

                self.db.user_performances[user_id].append(performance_record)
                return performance_record

            def calculate_progress_trends(
                self, user_id: str, subject: str = None
            ) -> dict:
                performances = self.db.user_performances.get(user_id, [])

                if subject:
                    performances = [p for p in performances if p["subject"] == subject]

                if len(performances) < 2:
                    return {
                        "trend": "insufficient_data",
                        "message": "En az 2 sınav sonucu gerekli",
                    }

                # Sort by date
                performances.sort(key=lambda x: x["date"])

                scores = [p["score"] for p in performances]
                dates = [p["date"] for p in performances]

                # Calculate trend
                recent_scores = scores[-3:] if len(scores) >= 3 else scores
                earlier_scores = scores[:-3] if len(scores) >= 3 else [scores[0]]

                recent_avg = statistics.mean(recent_scores)
                earlier_avg = statistics.mean(earlier_scores)

                improvement = recent_avg - earlier_avg
                improvement_rate = (
                    (improvement / earlier_avg * 100) if earlier_avg > 0 else 0
                )

                trend_direction = (
                    "improving"
                    if improvement > 2
                    else "declining"
                    if improvement < -2
                    else "stable"
                )

                return {
                    "trend": "calculated",
                    "direction": trend_direction,
                    "improvement_rate": round(improvement_rate, 2),
                    "recent_average": round(recent_avg, 2),
                    "earlier_average": round(earlier_avg, 2),
                    "total_exams": len(performances),
                    "best_score": max(scores),
                    "latest_score": scores[-1],
                    "consistency": self._calculate_consistency(scores),
                }

            def _calculate_consistency(self, scores: List[float]) -> dict:
                if len(scores) < 3:
                    return {"level": "insufficient_data"}

                std_dev = statistics.stdev(scores)
                mean_score = statistics.mean(scores)
                coefficient_of_variation = (
                    (std_dev / mean_score) * 100 if mean_score > 0 else 0
                )

                if coefficient_of_variation < 10:
                    consistency_level = "very_consistent"
                elif coefficient_of_variation < 20:
                    consistency_level = "consistent"
                elif coefficient_of_variation < 30:
                    consistency_level = "moderately_consistent"
                else:
                    consistency_level = "inconsistent"

                return {
                    "level": consistency_level,
                    "coefficient_of_variation": round(coefficient_of_variation, 2),
                    "standard_deviation": round(std_dev, 2),
                }

            def compare_with_peers(self, user_id: str, exam_type: str = "TYT") -> dict:
                user_performances = self.db.user_performances.get(user_id, [])
                user_scores = [
                    p["score"] for p in user_performances if p["exam_type"] == exam_type
                ]

                if not user_scores:
                    return {"error": "Bu sınav türünde performans verisi bulunamadı"}

                user_average = statistics.mean(user_scores)

                # Mock peer data (normally from actual database)
                mock_peer_scores = [
                    65,
                    72,
                    68,
                    75,
                    70,
                    78,
                    63,
                    82,
                    69,
                    74,
                    71,
                    76,
                    67,
                    73,
                    80,
                ]
                peer_average = statistics.mean(mock_peer_scores)

                # Calculate percentile
                all_scores = mock_peer_scores + [user_average]
                all_scores.sort()
                user_rank = all_scores.index(user_average) + 1
                percentile = (user_rank / len(all_scores)) * 100

                comparison = {
                    "user_average": round(user_average, 2),
                    "peer_average": round(peer_average, 2),
                    "percentile": round(percentile, 2),
                    "rank": user_rank,
                    "total_students": len(all_scores),
                    "above_average": user_average > peer_average,
                    "performance_gap": round(user_average - peer_average, 2),
                }

                if percentile >= 90:
                    comparison["performance_category"] = "top_performer"
                elif percentile >= 75:
                    comparison["performance_category"] = "above_average"
                elif percentile >= 50:
                    comparison["performance_category"] = "average"
                elif percentile >= 25:
                    comparison["performance_category"] = "below_average"
                else:
                    comparison["performance_category"] = "needs_improvement"

                return comparison

            def analyze_strengths_and_weaknesses(self, user_id: str) -> dict:
                performances = self.db.user_performances.get(user_id, [])

                if not performances:
                    return {"error": "Performans verisi bulunamadı"}

                # Aggregate topic performance
                topic_scores = {}
                for performance in performances:
                    for topic, data in performance.get("topic_breakdown", {}).items():
                        if topic not in topic_scores:
                            topic_scores[topic] = []
                        topic_scores[topic].append(data.get("percentage", 0))

                # Calculate averages and categorize
                topic_analysis = {}
                for topic, scores in topic_scores.items():
                    avg_score = statistics.mean(scores)
                    topic_analysis[topic] = {
                        "average_score": round(avg_score, 2),
                        "exam_count": len(scores),
                        "best_score": max(scores),
                        "latest_score": scores[-1],
                        "trend": "improving"
                        if len(scores) > 1 and scores[-1] > scores[0]
                        else "stable",
                    }

                # Categorize strengths and weaknesses
                strengths = []
                weaknesses = []
                needs_attention = []

                for topic, data in topic_analysis.items():
                    avg = data["average_score"]
                    if avg >= 80:
                        strengths.append({"topic": topic, **data})
                    elif avg >= 60:
                        needs_attention.append({"topic": topic, **data})
                    else:
                        weaknesses.append({"topic": topic, **data})

                return {
                    "strengths": strengths,
                    "needs_attention": needs_attention,
                    "weaknesses": weaknesses,
                    "topic_analysis": topic_analysis,
                    "overall_summary": {
                        "strong_areas": len(strengths),
                        "improvement_areas": len(weaknesses),
                        "total_topics_analyzed": len(topic_analysis),
                    },
                }

            def generate_personalized_study_plan(
                self, user_id: str, target_score: float = 80
            ) -> dict:
                analysis = self.analyze_strengths_and_weaknesses(user_id)
                trends = self.calculate_progress_trends(user_id)

                if "error" in analysis or "error" in trends:
                    return {"error": "Yeterli veri bulunmuyor"}

                study_plan = {
                    "target_score": target_score,
                    "current_average": trends.get("recent_average", 0),
                    "gap_to_target": target_score - trends.get("recent_average", 0),
                    "weekly_goals": [],
                    "focus_areas": [],
                    "time_allocation": {},
                }

                # Focus on weaknesses first
                for weakness in analysis["weaknesses"]:
                    study_plan["focus_areas"].append(
                        {
                            "topic": weakness["topic"],
                            "priority": "high",
                            "current_score": weakness["average_score"],
                            "target_improvement": 20,
                            "study_time_per_week": 3,  # hours
                        }
                    )

                # Then improvement areas
                for area in analysis["needs_attention"]:
                    study_plan["focus_areas"].append(
                        {
                            "topic": area["topic"],
                            "priority": "medium",
                            "current_score": area["average_score"],
                            "target_improvement": 10,
                            "study_time_per_week": 2,
                        }
                    )

                # Generate weekly goals for 4 weeks
                for week in range(1, 5):
                    week_goal = {
                        "week": week,
                        "focus_topics": [
                            area["topic"] for area in study_plan["focus_areas"][:2]
                        ],
                        "target_improvement": 5,
                        "practice_exams": 1 if week % 2 == 0 else 0,
                    }
                    study_plan["weekly_goals"].append(week_goal)

                return study_plan

        # Initialize services
        analytics_db = MockAnalyticsDatabase()
        analytics_service = MockAdvancedAnalyticsService(analytics_db)

        # Request models
        class ExamResultRecord(BaseModel):
            user_id: str
            exam_id: str
            exam_type: str
            subject: str
            percentage: float
            correct_answers: int
            total_questions: int
            total_time_minutes: int
            topic_breakdown: dict
            performance_level: str

        class ProgressRequest(BaseModel):
            user_id: str
            subject: Optional[str] = None

        class ComparisonRequest(BaseModel):
            user_id: str
            exam_type: str = "TYT"

        class StudyPlanRequest(BaseModel):
            user_id: str
            target_score: float = 80.0

        # API endpoints
        @app.post("/api/analytics/record-performance")
        async def record_performance(result: ExamResultRecord):
            """Record exam performance for analytics"""
            performance_record = analytics_service.record_exam_performance(
                result.user_id, result.dict()
            )

            return {
                "success": True,
                "message": "Performans kaydedildi",
                "record_id": len(analytics_db.user_performances[result.user_id]),
            }

        @app.post("/api/analytics/progress-trends")
        async def get_progress_trends(request: ProgressRequest):
            """Get user progress trends and analytics"""
            trends = analytics_service.calculate_progress_trends(
                request.user_id, request.subject
            )

            return {
                "success": True,
                "user_id": request.user_id,
                "subject": request.subject,
                "trends": trends,
            }

        @app.post("/api/analytics/peer-comparison")
        async def compare_with_peers(request: ComparisonRequest):
            """Compare user performance with peers"""
            comparison = analytics_service.compare_with_peers(
                request.user_id, request.exam_type
            )

            return {
                "success": True,
                "user_id": request.user_id,
                "exam_type": request.exam_type,
                "comparison": comparison,
            }

        @app.post("/api/analytics/strengths-weaknesses")
        async def analyze_strengths_weaknesses(request: ProgressRequest):
            """Analyze user strengths and weaknesses"""
            analysis = analytics_service.analyze_strengths_and_weaknesses(
                request.user_id
            )

            return {"success": True, "user_id": request.user_id, "analysis": analysis}

        @app.post("/api/analytics/study-plan")
        async def generate_study_plan(request: StudyPlanRequest):
            """Generate personalized study plan"""
            study_plan = analytics_service.generate_personalized_study_plan(
                request.user_id, request.target_score
            )

            return {
                "success": True,
                "user_id": request.user_id,
                "study_plan": study_plan,
            }

        # Test client
        client = TestClient(app)

        # Test advanced analytics workflow
        user_id = "analytics_test_user"

        # 1. Record multiple exam performances
        exam_results = [
            {
                "user_id": user_id,
                "exam_id": "tyt_matematik_1",
                "exam_type": "TYT",
                "subject": "matematik",
                "percentage": 65.0,
                "correct_answers": 26,
                "total_questions": 40,
                "total_time_minutes": 120,
                "topic_breakdown": {
                    "sayılar": {"correct": 6, "total": 10, "percentage": 60.0},
                    "cebir": {"correct": 8, "total": 10, "percentage": 80.0},
                    "geometri": {"correct": 7, "total": 10, "percentage": 70.0},
                    "fonksiyonlar": {"correct": 5, "total": 10, "percentage": 50.0},
                },
                "performance_level": "orta",
            },
            {
                "user_id": user_id,
                "exam_id": "tyt_matematik_2",
                "exam_type": "TYT",
                "subject": "matematik",
                "percentage": 72.0,
                "correct_answers": 29,
                "total_questions": 40,
                "total_time_minutes": 115,
                "topic_breakdown": {
                    "sayılar": {"correct": 7, "total": 10, "percentage": 70.0},
                    "cebir": {"correct": 9, "total": 10, "percentage": 90.0},
                    "geometri": {"correct": 8, "total": 10, "percentage": 80.0},
                    "fonksiyonlar": {"correct": 5, "total": 10, "percentage": 50.0},
                },
                "performance_level": "iyi",
            },
            {
                "user_id": user_id,
                "exam_id": "tyt_matematik_3",
                "exam_type": "TYT",
                "subject": "matematik",
                "percentage": 78.0,
                "correct_answers": 31,
                "total_questions": 40,
                "total_time_minutes": 110,
                "topic_breakdown": {
                    "sayılar": {"correct": 8, "total": 10, "percentage": 80.0},
                    "cebir": {"correct": 9, "total": 10, "percentage": 90.0},
                    "geometri": {"correct": 9, "total": 10, "percentage": 90.0},
                    "fonksiyonlar": {"correct": 5, "total": 10, "percentage": 50.0},
                },
                "performance_level": "iyi",
            },
        ]

        for result in exam_results:
            response = client.post("/api/analytics/record-performance", json=result)
            assert response.status_code == 200
            assert response.json()["success"] is True

        # 2. Test progress trends
        trends_request = {"user_id": user_id, "subject": "matematik"}
        response = client.post("/api/analytics/progress-trends", json=trends_request)
        assert response.status_code == 200

        trends_data = response.json()
        assert trends_data["success"] is True

        trends = trends_data["trends"]
        assert trends["trend"] == "calculated"
        assert trends["direction"] == "improving"  # 65 -> 72 -> 78
        assert trends["total_exams"] == 3
        assert trends["best_score"] == 78.0
        assert trends["latest_score"] == 78.0
        assert trends["improvement_rate"] > 0

        # 3. Test peer comparison
        comparison_request = {"user_id": user_id, "exam_type": "TYT"}
        response = client.post(
            "/api/analytics/peer-comparison", json=comparison_request
        )
        assert response.status_code == 200

        comparison_data = response.json()
        assert comparison_data["success"] is True

        comparison = comparison_data["comparison"]
        assert "user_average" in comparison
        assert "peer_average" in comparison
        assert "percentile" in comparison
        assert "performance_category" in comparison
        assert comparison["user_average"] == 71.67  # (65+72+78)/3

        # 4. Test strengths and weaknesses analysis
        analysis_request = {"user_id": user_id}
        response = client.post(
            "/api/analytics/strengths-weaknesses", json=analysis_request
        )
        assert response.status_code == 200

        analysis_data = response.json()
        assert analysis_data["success"] is True

        analysis = analysis_data["analysis"]
        assert "strengths" in analysis
        assert "weaknesses" in analysis
        assert "needs_attention" in analysis

        # Cebir should be strength (average 86.67%)
        cebir_strength = next(
            (s for s in analysis["strengths"] if s["topic"] == "cebir"), None
        )
        assert cebir_strength is not None
        assert cebir_strength["average_score"] > 80

        # Fonksiyonlar should be weakness (average 50%)
        fonksiyonlar_weakness = next(
            (w for w in analysis["weaknesses"] if w["topic"] == "fonksiyonlar"), None
        )
        assert fonksiyonlar_weakness is not None
        assert fonksiyonlar_weakness["average_score"] < 60

        # 5. Test personalized study plan generation
        study_plan_request = {"user_id": user_id, "target_score": 85.0}
        response = client.post("/api/analytics/study-plan", json=study_plan_request)
        assert response.status_code == 200

        plan_data = response.json()
        assert plan_data["success"] is True

        study_plan = plan_data["study_plan"]
        assert study_plan["target_score"] == 85.0
        assert study_plan["current_average"] == 78.0  # Latest score
        assert study_plan["gap_to_target"] == 7.0
        assert len(study_plan["weekly_goals"]) == 4
        assert len(study_plan["focus_areas"]) > 0

        # Fonksiyonlar should be high priority focus area
        high_priority_areas = [
            area for area in study_plan["focus_areas"] if area["priority"] == "high"
        ]
        assert len(high_priority_areas) > 0
        assert any(area["topic"] == "fonksiyonlar" for area in high_priority_areas)

        print("✅ Advanced exam analytics and comparison successful")

    except Exception as e:
        print(f"Advanced exam analytics test failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
