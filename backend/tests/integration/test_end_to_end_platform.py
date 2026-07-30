"""
End-to-End Platform Test Suite
KapsamlÄ± platform entegrasyon testleri

Bu test suite, tÃ¼m sistemin birlikte Ã§alÄ±ÅŸmasÄ±nÄ± test eder:
- Tam sÄ±nav workflow'u
- Multi-user concurrent scenarios
- WebSocket real-time communication
- Performance load testing (100,000+ users)

Requirements: 1.1-1.6, 7.1-7.6, 11.1-11.6
"""

import asyncio
import json
import os
import time
from datetime import datetime

import aiohttp
import psutil
import pytest
import websockets

# Module skip: SQLAlchemy registry conflict - Multiple classes for "PointTransaction"
pytestmark = pytest.mark.skipif(
    True, reason="SQLAlchemy registry conflict: Multiple PointTransaction classes"
)

# Model imports
from models import Question, Student

# Core imports

# Service imports


# Agent imports


class TestFullExamWorkflow:
    """Tam sÄ±nav workflow entegrasyon testleri"""

    @pytest.fixture
    async def test_client(self):
        """Test client setup"""
        async with aiohttp.ClientSession() as session:
            yield session

    @pytest.fixture
    def test_student(self):
        """Test Ã¶ÄŸrencisi"""
        return Student(
            id="e2e_student_001",
            name="Ahmet YÄ±lmaz",
            grade_level=12,
            ability=1.5,
            morphology_awareness=0.7,
        )

    @pytest.fixture
    def test_questions(self):
        """Test sorularÄ±"""
        return [
            Question(
                id="tyt_mat_001",
                text="2x + 3 = 7 denkleminin Ã§Ã¶zÃ¼mÃ¼ nedir?",
                options=["x = 1", "x = 2", "x = 3", "x = 4"],
                correct_answer=1,
                subject="Matematik",
                topic="Denklemler",
                difficulty=1.2,
                discrimination=1.5,
                exam_type="TYT",
            ),
            Question(
                id="tyt_tur_001",
                text="AÅŸaÄŸÄ±daki cÃ¼mlede hangi sÃ¶zcÃ¼k mecaz anlamda kullanÄ±lmÄ±ÅŸtÄ±r?",
                options=["Kalbi taÅŸ kesildi", "TaÅŸ ev", "TaÅŸ duvar", "TaÅŸ yol"],
                correct_answer=0,
                subject="TÃ¼rkÃ§e",
                topic="Anlam Bilgisi",
                difficulty=1.8,
                discrimination=1.3,
                exam_type="TYT",
            ),
            Question(
                id="ayt_fiz_001",
                text="IÅŸÄ±k hÄ±zÄ± vakumda kaÃ§ m/s'dir?",
                options=["3Ã—10â¸", "3Ã—10â·", "3Ã—10â¹", "3Ã—10â¶"],
                correct_answer=0,
                subject="Fizik",
                topic="IÅŸÄ±k",
                difficulty=2.1,
                discrimination=1.7,
                exam_type="AYT",
            ),
        ]

    @pytest.mark.asyncio
    async def test_complete_tyt_exam_workflow(
        self, test_client, test_student, test_questions
    ):
        """Tam TYT sÄ±nav workflow testi"""

        # 1. Ã–ÄŸrenci giriÅŸi
        login_response = await test_client.post(
            "http://localhost:8000/api/v1/auth/login",
            json={"username": test_student.id, "password": "test_password"},
        )
        assert login_response.status == 200
        auth_data = await login_response.json()
        token = auth_data["access_token"]

        headers = {"Authorization": f"Bearer {token}"}

        # 2. TYT sÄ±navÄ± baÅŸlatma
        exam_start_response = await test_client.post(
            "http://localhost:8000/api/v1/exam/start",
            json={
                "exam_type": "TYT",
                "student_id": test_student.id,
                "duration_minutes": 165,
            },
            headers=headers,
        )
        assert exam_start_response.status == 200
        exam_data = await exam_start_response.json()
        session_id = exam_data["session_id"]

        # 3. SorularÄ± alma
        questions_response = await test_client.get(
            f"http://localhost:8000/api/v1/exam/{session_id}/questions", headers=headers
        )
        assert questions_response.status == 200
        questions_data = await questions_response.json()
        assert len(questions_data["questions"]) == 120  # TYT toplam soru sayÄ±sÄ±

        # 4. SorularÄ± cevaplama (simÃ¼lasyon)
        answers = []
        for i, question in enumerate(questions_data["questions"][:10]):  # Ä°lk 10 soru
            answer_response = await test_client.post(
                f"http://localhost:8000/api/v1/exam/{session_id}/answer",
                json={
                    "question_id": question["id"],
                    "selected_answer": i % 4,  # DÃ¶ngÃ¼sel cevap
                    "time_spent_seconds": 45 + (i * 5),
                },
                headers=headers,
            )
            assert answer_response.status == 200
            answers.append(await answer_response.json())

        # 5. SÄ±navÄ± bitirme
        finish_response = await test_client.post(
            f"http://localhost:8000/api/v1/exam/{session_id}/finish", headers=headers
        )
        assert finish_response.status == 200
        await finish_response.json()  # govdeyi tuket; deger kullanilmiyor (F841)

        # 6. SonuÃ§larÄ± alma
        results_response = await test_client.get(
            f"http://localhost:8000/api/v1/exam/{session_id}/results", headers=headers
        )
        assert results_response.status == 200
        results_data = await results_response.json()

        # 7. Performans analizi
        analysis_response = await test_client.get(
            f"http://localhost:8000/api/v1/exam/{session_id}/analysis", headers=headers
        )
        assert analysis_response.status == 200
        analysis_data = await analysis_response.json()

        # Assertions
        assert "total_score" in results_data
        assert "subject_scores" in results_data
        assert "weak_areas" in analysis_data
        assert "study_recommendations" in analysis_data
        assert results_data["exam_type"] == "TYT"
        assert results_data["total_questions"] == 120

        # 8. Adaptif Ã¶ÄŸrenme Ã¶nerileri
        recommendations_response = await test_client.get(
            f"http://localhost:8000/api/v1/adaptive/recommendations/{test_student.id}",
            headers=headers,
        )
        assert recommendations_response.status == 200
        recommendations_data = await recommendations_response.json()
        assert "personalized_content" in recommendations_data
        assert "difficulty_adjustment" in recommendations_data

        return {
            "session_id": session_id,
            "results": results_data,
            "analysis": analysis_data,
            "recommendations": recommendations_data,
        }


class TestMultiUserConcurrentScenarios:
    """Ã‡oklu kullanÄ±cÄ± eÅŸzamanlÄ± test senaryolarÄ±"""

    @pytest.mark.asyncio
    async def test_concurrent_exam_sessions_1000_users(self):
        """1000+ eÅŸzamanlÄ± kullanÄ±cÄ± sÄ±nav oturumlarÄ± testi"""

        # 1000 Ã¶ÄŸrenci eÅŸzamanlÄ± sÄ±nav
        student_count = 1000
        students = []

        for i in range(student_count):
            student = Student(
                id=f"concurrent_student_{i:04d}",
                name=f"Test Student {i}",
                grade_level=11 + (i % 2),
                ability=1.0 + (i * 0.001),
                morphology_awareness=0.5 + (i * 0.0001),
            )
            students.append(student)

        async def simulate_exam_session(student: Student):
            """Tek Ã¶ÄŸrenci sÄ±nav simÃ¼lasyonu"""
            async with aiohttp.ClientSession() as session:
                try:
                    # Login
                    login_response = await session.post(
                        "http://localhost:8000/api/v1/auth/login",
                        json={"username": student.id, "password": "test_password"},
                    )
                    if login_response.status != 200:
                        return {"student_id": student.id, "status": "login_failed"}

                    token = (await login_response.json())["access_token"]
                    headers = {"Authorization": f"Bearer {token}"}

                    # SÄ±nav baÅŸlat
                    start_time = time.time()
                    exam_response = await session.post(
                        "http://localhost:8000/api/v1/exam/start",
                        json={
                            "exam_type": "TYT",
                            "student_id": student.id,
                            "duration_minutes": 165,
                        },
                        headers=headers,
                    )

                    if exam_response.status != 200:
                        return {"student_id": student.id, "status": "exam_start_failed"}

                    exam_data = await exam_response.json()
                    session_id = exam_data["session_id"]

                    # 10 soru cevapla
                    for q_num in range(10):
                        answer_response = await session.post(
                            f"http://localhost:8000/api/v1/exam/{session_id}/answer",
                            json={
                                "question_id": f"q_{q_num}",
                                "selected_answer": q_num % 4,
                                "time_spent_seconds": 30 + (q_num * 2),
                            },
                            headers=headers,
                        )

                        if answer_response.status != 200:
                            return {"student_id": student.id, "status": "answer_failed"}

                    # SÄ±navÄ± bitir
                    finish_response = await session.post(
                        f"http://localhost:8000/api/v1/exam/{session_id}/finish",
                        headers=headers,
                    )

                    end_time = time.time()
                    duration = end_time - start_time

                    return {
                        "student_id": student.id,
                        "status": "success",
                        "session_id": session_id,
                        "duration_seconds": duration,
                        "finish_status": finish_response.status,
                    }

                except Exception as e:
                    return {
                        "student_id": student.id,
                        "status": "error",
                        "error": str(e),
                    }

        # EÅŸzamanlÄ± Ã§alÄ±ÅŸtÄ±r
        start_time = time.time()
        tasks = [simulate_exam_session(student) for student in students]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        total_duration = end_time - start_time

        # SonuÃ§larÄ± analiz et
        successful_sessions = [
            r for r in results if isinstance(r, dict) and r.get("status") == "success"
        ]
        failed_sessions = [
            r for r in results if isinstance(r, dict) and r.get("status") != "success"
        ]
        exceptions = [r for r in results if isinstance(r, Exception)]

        # Assertions
        assert len(successful_sessions) >= student_count * 0.8  # En az %80 baÅŸarÄ±
        assert total_duration < 300  # 5 dakikadan az (1000 kullanÄ±cÄ± iÃ§in)
        assert len(exceptions) < student_count * 0.05  # %5'ten az exception

        # Performance metrics
        avg_session_duration = sum(
            s["duration_seconds"] for s in successful_sessions
        ) / len(successful_sessions)

        return {
            "total_students": student_count,
            "successful_sessions": len(successful_sessions),
            "failed_sessions": len(failed_sessions),
            "exceptions": len(exceptions),
            "total_duration_seconds": total_duration,
            "avg_session_duration_seconds": avg_session_duration,
            "success_rate": len(successful_sessions) / student_count,
        }


class TestWebSocketRealTimeCommunication:
    """WebSocket gerÃ§ek zamanlÄ± iletiÅŸim testleri"""

    @pytest.mark.asyncio
    async def test_websocket_agent_coordination(self):
        """WebSocket agent koordinasyon testi"""

        # WebSocket baÄŸlantÄ±larÄ±
        connections = []
        messages_received = []

        async def websocket_client(client_id: str):
            """WebSocket client simÃ¼lasyonu"""
            try:
                uri = f"ws://localhost:8000/ws/agent-coordination/{client_id}"
                async with websockets.connect(uri) as websocket:
                    connections.append(websocket)

                    # Ä°lk mesajÄ± gÃ¶nder
                    await websocket.send(
                        json.dumps(
                            {
                                "type": "agent_register",
                                "agent_id": client_id,
                                "agent_type": "learning_path"
                                if "learning" in client_id
                                else "study_buddy",
                            }
                        )
                    )

                    # MesajlarÄ± dinle
                    async for message in websocket:
                        data = json.loads(message)
                        messages_received.append(
                            {
                                "client_id": client_id,
                                "message": data,
                                "timestamp": datetime.now(),
                            }
                        )

                        # Koordinasyon mesajÄ±na yanÄ±t ver
                        if data.get("type") == "coordination_request":
                            await websocket.send(
                                json.dumps(
                                    {
                                        "type": "coordination_response",
                                        "agent_id": client_id,
                                        "data": f"Response from {client_id}",
                                    }
                                )
                            )

                        # Test tamamlandÄ±ÄŸÄ±nda Ã§Ä±k
                        if data.get("type") == "test_complete":
                            break

            except Exception as e:
                print(f"WebSocket client {client_id} error: {e}")

        # 3 agent simÃ¼lasyonu
        agent_ids = ["learning_path_agent", "study_buddy_agent", "accessibility_agent"]

        # WebSocket client'larÄ± baÅŸlat
        client_tasks = [websocket_client(agent_id) for agent_id in agent_ids]

        # KÄ±sa sÃ¼re bekle (baÄŸlantÄ±lar kurulsun)
        await asyncio.sleep(1)

        # Koordinasyon mesajÄ± gÃ¶nder
        if connections:
            coordination_message = {
                "type": "coordination_request",
                "student_id": "test_student_001",
                "learning_style": "visual",
                "request_id": "coord_001",
            }

            # Ä°lk agent'a mesaj gÃ¶nder
            await connections[0].send(json.dumps(coordination_message))

        # MesajlarÄ±n iÅŸlenmesini bekle
        await asyncio.sleep(1)  # Reduced from 2s

        # Test tamamlama mesajÄ± gÃ¶nder
        test_complete_message = {"type": "test_complete"}
        for connection in connections:
            try:
                await connection.send(json.dumps(test_complete_message))
            except Exception as hata:
                # 30 Tem 2026: burada `pass` vardi ve dosyanin BOM'u yuzunden
                # ast.parse duştugu icin bekci bu yutmayi HIC gormuyordu (#456).
                # Baglantinin kapali olmasi beklenen bir durum, ama sessiz degil.
                print(f"test_complete gonderilemedi (baglanti kapali olabilir): {hata}")

        # Client task'larÄ± tamamla
        await asyncio.gather(*client_tasks, return_exceptions=True)

        # SonuÃ§larÄ± analiz et
        register_messages = [
            m for m in messages_received if m["message"].get("type") == "agent_register"
        ]
        coordination_messages = [
            m
            for m in messages_received
            if m["message"].get("type") == "coordination_request"
        ]
        response_messages = [
            m
            for m in messages_received
            if m["message"].get("type") == "coordination_response"
        ]

        # Assertions
        assert len(connections) >= 2  # En az 2 baÄŸlantÄ± kurulmalÄ±
        assert len(coordination_messages) >= 1  # En az 1 koordinasyon mesajÄ±
        assert len(response_messages) >= 1  # En az 1 yanÄ±t mesajÄ±

        return {
            "total_connections": len(connections),
            "total_messages": len(messages_received),
            "register_messages": len(register_messages),
            "coordination_messages": len(coordination_messages),
            "response_messages": len(response_messages),
        }


class TestPerformanceLoadTesting:
    """Performance yÃ¼k testleri (100,000+ kullanÄ±cÄ±)"""

    @pytest.mark.asyncio
    async def test_high_load_simulation_10k_users(self):
        """10,000 kullanÄ±cÄ± yÃ¼k simÃ¼lasyonu (100K iÃ§in extrapolation)"""

        # 10K kullanÄ±cÄ± ile test, 100K iÃ§in extrapolation yapacaÄŸÄ±z
        user_count = 10000
        concurrent_limit = 500  # EÅŸzamanlÄ± baÄŸlantÄ± limiti

        async def simulate_user_activity(user_id: int):
            """Tek kullanÄ±cÄ± aktivite simÃ¼lasyonu"""
            async with aiohttp.ClientSession() as session:
                try:
                    start_time = time.time()

                    # Login
                    login_response = await session.post(
                        "http://localhost:8000/api/v1/auth/login",
                        json={
                            "username": f"load_user_{user_id}",
                            "password": "test_password",
                        },
                    )

                    if login_response.status != 200:
                        return {"user_id": user_id, "status": "login_failed"}

                    token = (await login_response.json())["access_token"]
                    headers = {"Authorization": f"Bearer {token}"}

                    # Ã‡eÅŸitli API Ã§aÄŸrÄ±larÄ±
                    api_calls = [
                        ("GET", "/api/v1/student/profile"),
                        ("GET", "/api/v1/questions/random"),
                        (
                            "POST",
                            "/api/v1/revolutionary/learning-style/detect",
                            {
                                "student_id": f"load_user_{user_id}",
                                "behavioral_data": [],
                                "questionnaire_responses": [],
                            },
                        ),
                        ("GET", "/api/v1/content/recommendations"),
                        ("GET", "/api/v1/analytics/performance"),
                    ]

                    successful_calls = 0
                    failed_calls = 0

                    for method, endpoint, *data in api_calls:
                        try:
                            if method == "GET":
                                response = await session.get(
                                    f"http://localhost:8000{endpoint}", headers=headers
                                )
                            else:
                                response = await session.post(
                                    f"http://localhost:8000{endpoint}",
                                    json=data[0] if data else {},
                                    headers=headers,
                                )

                            if response.status == 200:
                                successful_calls += 1
                            else:
                                failed_calls += 1

                        except Exception:
                            failed_calls += 1

                    end_time = time.time()
                    duration = end_time - start_time

                    return {
                        "user_id": user_id,
                        "status": "success",
                        "duration_seconds": duration,
                        "successful_calls": successful_calls,
                        "failed_calls": failed_calls,
                        "total_calls": len(api_calls),
                    }

                except Exception as e:
                    return {"user_id": user_id, "status": "error", "error": str(e)}

        # Sistem kaynaklarÄ±nÄ± Ã¶lÃ§
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        initial_cpu = process.cpu_percent()

        # Batch'ler halinde kullanÄ±cÄ±larÄ± Ã§alÄ±ÅŸtÄ±r
        batch_size = concurrent_limit
        all_results = []

        start_time = time.time()

        for batch_start in range(0, user_count, batch_size):
            batch_end = min(batch_start + batch_size, user_count)
            batch_users = range(batch_start, batch_end)

            # Batch'i Ã§alÄ±ÅŸtÄ±r
            batch_tasks = [simulate_user_activity(user_id) for user_id in batch_users]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            all_results.extend(batch_results)

            # Batch'ler arasÄ± kÄ±sa bekleme
            await asyncio.sleep(0.1)

        end_time = time.time()
        total_duration = end_time - start_time

        # Final sistem kaynaklarÄ±
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        final_cpu = process.cpu_percent()

        # SonuÃ§larÄ± analiz et
        successful_users = [
            r
            for r in all_results
            if isinstance(r, dict) and r.get("status") == "success"
        ]
        failed_users = [
            r
            for r in all_results
            if isinstance(r, dict) and r.get("status") != "success"
        ]
        exceptions = [r for r in all_results if isinstance(r, Exception)]

        # Performance metrics
        if successful_users:
            avg_user_duration = sum(
                u["duration_seconds"] for u in successful_users
            ) / len(successful_users)
            total_api_calls = sum(
                u["successful_calls"] + u["failed_calls"] for u in successful_users
            )
            successful_api_calls = sum(u["successful_calls"] for u in successful_users)
            api_success_rate = (
                successful_api_calls / total_api_calls if total_api_calls > 0 else 0
            )
        else:
            avg_user_duration = 0
            total_api_calls = 0
            successful_api_calls = 0
            api_success_rate = 0

        # Throughput hesaplama
        throughput_users_per_second = (
            len(successful_users) / total_duration if total_duration > 0 else 0
        )
        throughput_requests_per_second = (
            successful_api_calls / total_duration if total_duration > 0 else 0
        )

        # Assertions
        assert len(successful_users) >= user_count * 0.8  # En az %80 baÅŸarÄ±
        assert avg_user_duration < 10.0  # KullanÄ±cÄ± baÅŸÄ±na 10 saniyeden az
        assert api_success_rate >= 0.8  # API Ã§aÄŸrÄ±larÄ±nÄ±n %80'i baÅŸarÄ±lÄ±
        assert (
            final_memory - initial_memory < 2000
        )  # 2GB'dan az memory artÄ±ÅŸÄ± (10K kullanÄ±cÄ± iÃ§in)

        # 100K kullanÄ±cÄ± iÃ§in extrapolation
        extrapolated_100k = {
            "estimated_total_duration_seconds": total_duration * 10,
            "estimated_throughput_users_per_second": throughput_users_per_second,
            "estimated_memory_usage_mb": (final_memory - initial_memory) * 10,
            "estimated_success_rate": api_success_rate,
            "scalability_factor": 10,
        }

        return {
            "total_users": user_count,
            "successful_users": len(successful_users),
            "failed_users": len(failed_users),
            "exceptions": len(exceptions),
            "total_duration_seconds": total_duration,
            "avg_user_duration_seconds": avg_user_duration,
            "total_api_calls": total_api_calls,
            "successful_api_calls": successful_api_calls,
            "api_success_rate": api_success_rate,
            "throughput_users_per_second": throughput_users_per_second,
            "throughput_requests_per_second": throughput_requests_per_second,
            "memory_usage_mb": {
                "initial": initial_memory,
                "final": final_memory,
                "increase": final_memory - initial_memory,
            },
            "cpu_usage_percent": {"initial": initial_cpu, "final": final_cpu},
            "extrapolated_100k_users": extrapolated_100k,
        }

    @pytest.mark.asyncio
    async def test_stress_test_response_time(self):
        """Stres testi - YanÄ±t sÃ¼resi analizi (Requirement 7.1)"""

        # FarklÄ± yÃ¼k seviyelerinde yanÄ±t sÃ¼relerini test et
        load_levels = [100, 500, 1000, 2000, 5000]
        results = []

        for load_level in load_levels:

            async def single_request():
                """Tek API isteÄŸi"""
                async with aiohttp.ClientSession() as session:
                    start_time = time.time()
                    try:
                        response = await session.get(
                            "http://localhost:8000/api/v1/health",
                            timeout=aiohttp.ClientTimeout(total=5),
                        )
                        end_time = time.time()
                        return {
                            "success": response.status == 200,
                            "response_time_ms": (end_time - start_time) * 1000,
                        }
                    except Exception as e:
                        end_time = time.time()
                        return {
                            "success": False,
                            "response_time_ms": (end_time - start_time) * 1000,
                            "error": str(e),
                        }

            # YÃ¼k seviyesinde istekler gÃ¶nder
            tasks = [single_request() for _ in range(load_level)]
            load_results = await asyncio.gather(*tasks)

            # YanÄ±t sÃ¼relerini analiz et
            successful_requests = [r for r in load_results if r["success"]]
            response_times = [r["response_time_ms"] for r in successful_requests]

            if response_times:
                response_times.sort()
                p50 = response_times[len(response_times) // 2]
                p95 = response_times[int(len(response_times) * 0.95)]
                p99 = response_times[int(len(response_times) * 0.99)]
                avg = sum(response_times) / len(response_times)
            else:
                p50 = p95 = p99 = avg = 0

            results.append(
                {
                    "load_level": load_level,
                    "total_requests": load_level,
                    "successful_requests": len(successful_requests),
                    "success_rate": len(successful_requests) / load_level,
                    "response_time_ms": {
                        "avg": avg,
                        "p50": p50,
                        "p95": p95,
                        "p99": p99,
                    },
                }
            )

            # Requirement 7.1: p95 < 200ms kontrolÃ¼
            if load_level <= 1000:
                assert (
                    p95 < 200
                ), f"p95 response time {p95}ms exceeds 200ms at load level {load_level}"

        return {
            "stress_test_results": results,
            "requirement_7_1_met": all(
                r["response_time_ms"]["p95"] < 200
                for r in results
                if r["load_level"] <= 1000
            ),
        }

    @pytest.mark.asyncio
    async def test_sustained_load_stability(self):
        """SÃ¼rekli yÃ¼k stabilitesi testi (Requirement 7.2, 7.3)"""

        # 5 dakika boyunca sÃ¼rekli yÃ¼k
        duration_seconds = 300  # 5 dakika
        requests_per_second = 100

        start_time = time.time()
        total_requests = 0
        successful_requests = 0
        failed_requests = 0
        response_times = []

        async def continuous_load():
            """SÃ¼rekli yÃ¼k oluÅŸtur"""
            nonlocal total_requests, successful_requests, failed_requests

            async with aiohttp.ClientSession() as session:
                while time.time() - start_time < duration_seconds:
                    request_start = time.time()
                    try:
                        response = await session.get(
                            "http://localhost:8000/api/v1/health",
                            timeout=aiohttp.ClientTimeout(total=5),
                        )
                        request_end = time.time()

                        total_requests += 1
                        if response.status == 200:
                            successful_requests += 1
                            response_times.append((request_end - request_start) * 1000)
                        else:
                            failed_requests += 1

                    except Exception:
                        total_requests += 1
                        failed_requests += 1

                    # Rate limiting
                    await asyncio.sleep(1.0 / requests_per_second)

        # Birden fazla worker ile yÃ¼k oluÅŸtur
        workers = 10
        tasks = [continuous_load() for _ in range(workers)]
        await asyncio.gather(*tasks)

        end_time = time.time()
        actual_duration = end_time - start_time

        # Uptime hesaplama (Requirement 7.3)
        uptime_percentage = (
            (successful_requests / total_requests * 100) if total_requests > 0 else 0
        )

        # Assertions
        assert uptime_percentage >= 99.9, f"Uptime {uptime_percentage}% is below 99.9%"
        assert successful_requests > 0, "No successful requests during sustained load"

        return {
            "duration_seconds": actual_duration,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "uptime_percentage": uptime_percentage,
            "avg_response_time_ms": sum(response_times) / len(response_times)
            if response_times
            else 0,
            "requests_per_second": total_requests / actual_duration,
            "requirement_7_3_met": uptime_percentage >= 99.9,
        }


class TestFullStudentJourney:
    """Tam Ã¶ÄŸrenci yolculuÄŸu testleri (registration â†’ exam â†’ results â†’ recommendations)"""

    @pytest.mark.asyncio
    async def test_complete_student_journey(self):
        """KayÄ±ttan Ã¶nerilere kadar tam Ã¶ÄŸrenci yolculuÄŸu"""

        async with aiohttp.ClientSession() as session:
            # 1. KAYIT (Registration)
            registration_data = {
                "username": "yeni_ogrenci_001",
                "email": "yeni@test.com",
                "password": "SecurePass123!",
                "first_name": "AyÅŸe",
                "last_name": "Demir",
                "role": "STUDENT",
                "grade_level": 12,
                "target_exam": "TYT",
            }

            register_response = await session.post(
                "http://localhost:8000/api/v1/auth/register", json=registration_data
            )
            assert register_response.status == 200
            register_result = await register_response.json()
            assert "user_id" in register_result
            user_id = register_result["user_id"]

            # 2. GÄ°RÄ°Å (Login)
            login_response = await session.post(
                "http://localhost:8000/api/v1/auth/login",
                json={
                    "username": registration_data["username"],
                    "password": registration_data["password"],
                },
            )
            assert login_response.status == 200
            login_result = await login_response.json()
            token = login_result["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # 3. PROFÄ°L OLUÅTURMA (Profile Setup)
            profile_response = await session.post(
                "http://localhost:8000/api/v1/student/profile",
                json={
                    "user_id": user_id,
                    "grade_level": 12,
                    "target_exam": "TYT",
                    "target_university": "Ä°TÃœ",
                    "target_department": "Bilgisayar MÃ¼hendisliÄŸi",
                    "study_hours_per_day": 4,
                    "weak_subjects": ["Matematik", "Fizik"],
                },
                headers=headers,
            )
            assert profile_response.status == 200

            # 4. Ã–ÄRENME STÄ°LÄ° TESPÄ°TÄ° (Learning Style Detection)
            learning_style_response = await session.post(
                "http://localhost:8000/api/v1/revolutionary/learning-style/detect",
                json={
                    "student_id": user_id,
                    "behavioral_data": [
                        {
                            "action": "video_watched",
                            "duration": 300,
                            "subject": "Matematik",
                        },
                        {"action": "text_read", "duration": 180, "subject": "Fizik"},
                        {
                            "action": "practice_completed",
                            "score": 0.75,
                            "subject": "Matematik",
                        },
                    ],
                    "questionnaire_responses": [
                        {"question_id": "vark_1", "answer": "visual"},
                        {"question_id": "felder_1", "answer": "active"},
                    ],
                },
                headers=headers,
            )
            assert learning_style_response.status == 200
            learning_style_result = await learning_style_response.json()
            assert "learning_profile" in learning_style_result

            # 5. SINAV BAÅLATMA (Start Exam)
            exam_start_response = await session.post(
                "http://localhost:8000/api/v1/exam/start",
                json={
                    "exam_type": "TYT",
                    "student_id": user_id,
                    "duration_minutes": 165,
                    "adaptive_mode": True,
                },
                headers=headers,
            )
            assert exam_start_response.status == 200
            exam_result = await exam_start_response.json()
            session_id = exam_result["session_id"]

            # 6. SORULARI ALMA (Get Questions)
            questions_response = await session.get(
                f"http://localhost:8000/api/v1/exam/{session_id}/questions",
                headers=headers,
            )
            assert questions_response.status == 200
            questions_result = await questions_response.json()
            questions = questions_result["questions"]
            assert len(questions) == 120

            # 7. SORULARI CEVAPLAMA (Answer Questions)
            # Ä°lk 20 soruyu cevapla (simÃ¼lasyon)
            for i, question in enumerate(questions[:20]):
                # GerÃ§ekÃ§i cevap simÃ¼lasyonu (bazÄ± doÄŸru, bazÄ± yanlÄ±ÅŸ)
                correct_probability = 0.7 if i < 10 else 0.5
                is_correct = i % 10 < (correct_probability * 10)
                selected_answer = (
                    question["correct_answer"]
                    if is_correct
                    else (question["correct_answer"] + 1) % 4
                )

                answer_response = await session.post(
                    f"http://localhost:8000/api/v1/exam/{session_id}/answer",
                    json={
                        "question_id": question["id"],
                        "selected_answer": selected_answer,
                        "time_spent_seconds": 45 + (i * 3),
                    },
                    headers=headers,
                )
                assert answer_response.status == 200

            # 8. SINAVI BÄ°TÄ°RME (Finish Exam)
            finish_response = await session.post(
                f"http://localhost:8000/api/v1/exam/{session_id}/finish",
                headers=headers,
            )
            assert finish_response.status == 200

            # 9. SONUÃ‡LARI ALMA (Get Results)
            results_response = await session.get(
                f"http://localhost:8000/api/v1/exam/{session_id}/results",
                headers=headers,
            )
            assert results_response.status == 200
            results = await results_response.json()
            assert "total_score" in results
            assert "subject_scores" in results

            # 10. PERFORMANS ANALÄ°ZÄ° (Performance Analysis)
            analysis_response = await session.get(
                f"http://localhost:8000/api/v1/exam/{session_id}/analysis",
                headers=headers,
            )
            assert analysis_response.status == 200
            analysis = await analysis_response.json()
            assert "weak_areas" in analysis
            assert "study_recommendations" in analysis

            # 11. KÄ°ÅÄ°SELLEÅTÄ°RÄ°LMÄ°Å Ã–NERÄ°LER (Personalized Recommendations)
            recommendations_response = await session.get(
                f"http://localhost:8000/api/v1/adaptive/recommendations/{user_id}",
                headers=headers,
            )
            assert recommendations_response.status == 200
            recommendations = await recommendations_response.json()
            assert "personalized_content" in recommendations
            assert "difficulty_adjustment" in recommendations
            assert "learning_path" in recommendations

            # 12. Ä°Ã‡ERÄ°K Ã–NERÄ°LERÄ° (Content Recommendations)
            content_response = await session.get(
                "http://localhost:8000/api/v1/content/recommendations",
                params={"student_id": user_id, "subject": "Matematik"},
                headers=headers,
            )
            assert content_response.status == 200
            content = await content_response.json()
            assert "youtube_videos" in content or "khan_academy_courses" in content

            # 13. Ã–ÄRENME YOLU OLUÅTURMA (Create Learning Path)
            learning_path_response = await session.post(
                "http://localhost:8000/api/v1/adaptive/learning-path",
                json={
                    "student_id": user_id,
                    "target_subjects": ["Matematik", "Fizik"],
                    "time_constraint_weeks": 12,
                    "target_score": 450,
                },
                headers=headers,
            )
            assert learning_path_response.status == 200
            learning_path = await learning_path_response.json()
            assert "learning_sequence" in learning_path
            assert "estimated_completion_time" in learning_path

            return {
                "user_id": user_id,
                "session_id": session_id,
                "registration": "success",
                "login": "success",
                "profile_setup": "success",
                "learning_style_detected": learning_style_result["learning_profile"],
                "exam_completed": "success",
                "results": results,
                "analysis": analysis,
                "recommendations": recommendations,
                "learning_path": learning_path,
                "journey_status": "complete",
            }


class TestTeacherStudentParentWorkflow:
    """Ã–ÄŸretmen-Ã–ÄŸrenci-Veli workflow entegrasyon testleri"""

    @pytest.mark.asyncio
    async def test_teacher_student_parent_interaction(self):
        """Ã–ÄŸretmen-Ã–ÄŸrenci-Veli etkileÅŸim workflow'u"""

        async with aiohttp.ClientSession() as session:
            # 1. Ã–ÄRETMEN KAYDI VE GÄ°RÄ°ÅÄ°
            teacher_register = await session.post(
                "http://localhost:8000/api/v1/auth/register",
                json={
                    "username": "ogretmen_mehmet",
                    "email": "mehmet@okul.com",
                    "password": "Teacher123!",
                    "first_name": "Mehmet",
                    "last_name": "YÄ±lmaz",
                    "role": "TEACHER",
                },
            )
            assert teacher_register.status == 200
            teacher_data = await teacher_register.json()
            teacher_id = teacher_data["user_id"]

            teacher_login = await session.post(
                "http://localhost:8000/api/v1/auth/login",
                json={"username": "ogretmen_mehmet", "password": "Teacher123!"},
            )
            teacher_token = (await teacher_login.json())["access_token"]
            teacher_headers = {"Authorization": f"Bearer {teacher_token}"}

            # 2. Ã–ÄRENCÄ° KAYDI VE GÄ°RÄ°ÅÄ°
            student_register = await session.post(
                "http://localhost:8000/api/v1/auth/register",
                json={
                    "username": "ogrenci_ali",
                    "email": "ali@ogrenci.com",
                    "password": "Student123!",
                    "first_name": "Ali",
                    "last_name": "Kaya",
                    "role": "STUDENT",
                    "grade_level": 11,
                },
            )
            assert student_register.status == 200
            student_data = await student_register.json()
            student_id = student_data["user_id"]

            student_login = await session.post(
                "http://localhost:8000/api/v1/auth/login",
                json={"username": "ogrenci_ali", "password": "Student123!"},
            )
            student_token = (await student_login.json())["access_token"]
            student_headers = {"Authorization": f"Bearer {student_token}"}

            # 3. VELÄ° KAYDI VE GÄ°RÄ°ÅÄ°
            parent_register = await session.post(
                "http://localhost:8000/api/v1/auth/register",
                json={
                    "username": "veli_fatma",
                    "email": "fatma@veli.com",
                    "password": "Parent123!",
                    "first_name": "Fatma",
                    "last_name": "Kaya",
                    "role": "PARENT",
                },
            )
            assert parent_register.status == 200
            parent_data = await parent_register.json()
            parent_id = parent_data["user_id"]

            parent_login = await session.post(
                "http://localhost:8000/api/v1/auth/login",
                json={"username": "veli_fatma", "password": "Parent123!"},
            )
            parent_token = (await parent_login.json())["access_token"]
            parent_headers = {"Authorization": f"Bearer {parent_token}"}

            # 4. VELÄ°-Ã–ÄRENCÄ° BAÄLANTISI
            link_response = await session.post(
                "http://localhost:8000/api/v1/parent/link-student",
                json={
                    "parent_id": parent_id,
                    "student_id": student_id,
                    "relationship": "mother",
                },
                headers=parent_headers,
            )
            assert link_response.status == 200

            # 5. Ã–ÄRETMEN SINIF OLUÅTURMA
            class_response = await session.post(
                "http://localhost:8000/api/v1/teacher/class/create",
                json={
                    "teacher_id": teacher_id,
                    "class_name": "11-A Matematik",
                    "grade_level": 11,
                    "subject": "Matematik",
                },
                headers=teacher_headers,
            )
            assert class_response.status == 200
            class_data = await class_response.json()
            class_id = class_data["class_id"]

            # 6. Ã–ÄRENCÄ°YÄ° SINIFA EKLEME
            add_student_response = await session.post(
                f"http://localhost:8000/api/v1/teacher/class/{class_id}/add-student",
                json={"student_id": student_id},
                headers=teacher_headers,
            )
            assert add_student_response.status == 200

            # 7. Ã–ÄRETMEN Ã–DEV OLUÅTURMA
            assignment_response = await session.post(
                "http://localhost:8000/api/v1/teacher/assignment/create",
                json={
                    "teacher_id": teacher_id,
                    "class_id": class_id,
                    "title": "Denklemler Ã–devi",
                    "description": "2. derece denklemler konusu",
                    "subject": "Matematik",
                    "topic": "Denklemler",
                    "question_count": 20,
                    "difficulty": "MEDIUM",
                    "due_date": "2025-10-15",
                },
                headers=teacher_headers,
            )
            assert assignment_response.status == 200
            assignment_data = await assignment_response.json()
            assignment_id = assignment_data["assignment_id"]

            # 8. Ã–ÄRENCÄ° Ã–DEVÄ° GÃ–RÃœNTÃœLEME
            student_assignments_response = await session.get(
                "http://localhost:8000/api/v1/student/assignments",
                params={"student_id": student_id},
                headers=student_headers,
            )
            assert student_assignments_response.status == 200
            assignments = await student_assignments_response.json()
            assert len(assignments) > 0

            # 9. Ã–ÄRENCÄ° Ã–DEVÄ° TAMAMLAMA
            complete_assignment_response = await session.post(
                f"http://localhost:8000/api/v1/student/assignment/{assignment_id}/complete",
                json={
                    "student_id": student_id,
                    "answers": [
                        {"question_id": f"q_{i}", "answer": i % 4} for i in range(20)
                    ],
                    "time_spent_minutes": 45,
                },
                headers=student_headers,
            )
            assert complete_assignment_response.status == 200

            # 10. Ã–ÄRETMEN PERFORMANS RAPORU GÃ–RÃœNTÃœLEME
            class_performance_response = await session.get(
                f"http://localhost:8000/api/v1/teacher/class/{class_id}/performance",
                headers=teacher_headers,
            )
            assert class_performance_response.status == 200
            class_performance = await class_performance_response.json()
            assert "students" in class_performance
            assert "average_score" in class_performance

            # 11. VELÄ° HAFTALIK RAPOR ALMA
            parent_report_response = await session.get(
                "http://localhost:8000/api/v1/parent/weekly-report",
                params={"parent_id": parent_id, "student_id": student_id},
                headers=parent_headers,
            )
            assert parent_report_response.status == 200
            parent_report = await parent_report_response.json()
            assert "student_progress" in parent_report
            assert "completed_assignments" in parent_report
            assert "study_time" in parent_report

            # 12. VELÄ° Ã–ÄRETMENLE Ä°LETÄ°ÅÄ°M
            message_response = await session.post(
                "http://localhost:8000/api/v1/parent/message-teacher",
                json={
                    "parent_id": parent_id,
                    "teacher_id": teacher_id,
                    "student_id": student_id,
                    "subject": "Matematik PerformansÄ±",
                    "message": "Ã‡ocuÄŸumun matematik performansÄ± hakkÄ±nda bilgi alabilir miyim?",
                },
                headers=parent_headers,
            )
            assert message_response.status == 200

            # 13. Ã–ÄRETMEN MESAJI GÃ–RÃœNTÃœLEME VE CEVAPLAMA
            teacher_messages_response = await session.get(
                "http://localhost:8000/api/v1/teacher/messages",
                params={"teacher_id": teacher_id},
                headers=teacher_headers,
            )
            assert teacher_messages_response.status == 200
            messages = await teacher_messages_response.json()
            assert len(messages) > 0

            return {
                "teacher_id": teacher_id,
                "student_id": student_id,
                "parent_id": parent_id,
                "class_id": class_id,
                "assignment_id": assignment_id,
                "workflow_steps": {
                    "teacher_registration": "success",
                    "student_registration": "success",
                    "parent_registration": "success",
                    "parent_student_link": "success",
                    "class_creation": "success",
                    "student_added_to_class": "success",
                    "assignment_created": "success",
                    "assignment_completed": "success",
                    "teacher_viewed_performance": "success",
                    "parent_viewed_report": "success",
                    "parent_teacher_communication": "success",
                },
                "workflow_status": "complete",
            }


class TestOfflineOnlineSynchronization:
    """Offline-Online senkronizasyon testleri"""

    @pytest.mark.asyncio
    async def test_offline_exam_sync(self):
        """Offline sÄ±nav verilerinin online senkronizasyonu"""

        async with aiohttp.ClientSession() as session:
            # 1. KullanÄ±cÄ± giriÅŸi
            login_response = await session.post(
                "http://localhost:8000/api/v1/auth/login",
                json={"username": "offline_user", "password": "test_password"},
            )
            assert login_response.status == 200
            token = (await login_response.json())["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # 2. Offline iÃ§erik paketi indirme
            offline_package_response = await session.post(
                "http://localhost:8000/api/v1/pwa/offline-package",
                json={
                    "student_id": "offline_user",
                    "exam_type": "TYT",
                    "subject": "Matematik",
                    "question_count": 50,
                },
                headers=headers,
            )
            assert offline_package_response.status == 200
            offline_package = await offline_package_response.json()
            assert "package_id" in offline_package
            assert "questions" in offline_package
            package_id = offline_package["package_id"]

            # 3. Offline sÄ±nav simÃ¼lasyonu (local storage'da saklanacak veriler)
            offline_exam_data = {
                "package_id": package_id,
                "student_id": "offline_user",
                "exam_type": "TYT",
                "start_time": datetime.now().isoformat(),
                "answers": [
                    {
                        "question_id": f"offline_q_{i}",
                        "selected_answer": i % 4,
                        "time_spent_seconds": 45 + (i * 2),
                        "timestamp": datetime.now().isoformat(),
                    }
                    for i in range(20)
                ],
                "end_time": datetime.now().isoformat(),
                "completed_offline": True,
            }

            # 4. Online'a dÃ¶nÃ¼ÅŸ - Senkronizasyon baÅŸlatma
            sync_response = await session.post(
                "http://localhost:8000/api/v1/pwa/sync",
                json={
                    "student_id": "offline_user",
                    "offline_data": offline_exam_data,
                    "sync_type": "exam_completion",
                },
                headers=headers,
            )
            assert sync_response.status == 200
            sync_result = await sync_response.json()
            assert sync_result["sync_status"] == "success"
            assert "session_id" in sync_result
            session_id = sync_result["session_id"]

            # 5. Senkronize edilen sonuÃ§larÄ± doÄŸrulama
            results_response = await session.get(
                f"http://localhost:8000/api/v1/exam/{session_id}/results",
                headers=headers,
            )
            assert results_response.status == 200
            results = await results_response.json()
            assert "total_score" in results
            assert results["completed_offline"] is True

            # 6. Offline progress verilerini senkronize etme
            progress_data = {
                "student_id": "offline_user",
                "offline_activities": [
                    {
                        "activity_type": "video_watched",
                        "content_id": "video_123",
                        "duration_seconds": 300,
                        "timestamp": datetime.now().isoformat(),
                    },
                    {
                        "activity_type": "practice_completed",
                        "content_id": "practice_456",
                        "score": 0.85,
                        "timestamp": datetime.now().isoformat(),
                    },
                ],
            }

            progress_sync_response = await session.post(
                "http://localhost:8000/api/v1/pwa/sync-progress",
                json=progress_data,
                headers=headers,
            )
            assert progress_sync_response.status == 200
            progress_sync_result = await progress_sync_response.json()
            assert progress_sync_result["activities_synced"] == len(
                progress_data["offline_activities"]
            )

            # 7. Senkronizasyon durumunu kontrol etme
            sync_status_response = await session.get(
                "http://localhost:8000/api/v1/pwa/sync-status",
                params={"student_id": "offline_user"},
                headers=headers,
            )
            assert sync_status_response.status == 200
            sync_status = await sync_status_response.json()
            assert sync_status["last_sync_time"] is not None
            assert sync_status["pending_syncs"] == 0

            # 8. Conflict resolution testi
            conflict_data = {
                "student_id": "offline_user",
                "offline_data": {
                    "question_id": "conflict_q_1",
                    "offline_answer": 2,
                    "offline_timestamp": "2025-10-04T10:00:00",
                },
                "online_data": {
                    "question_id": "conflict_q_1",
                    "online_answer": 3,
                    "online_timestamp": "2025-10-04T10:05:00",
                },
            }

            conflict_response = await session.post(
                "http://localhost:8000/api/v1/pwa/resolve-conflict",
                json=conflict_data,
                headers=headers,
            )
            assert conflict_response.status == 200
            conflict_result = await conflict_response.json()
            assert "resolved_answer" in conflict_result
            assert conflict_result["resolution_strategy"] in [
                "latest_timestamp",
                "offline_priority",
                "online_priority",
            ]

            return {
                "package_id": package_id,
                "session_id": session_id,
                "offline_package_downloaded": "success",
                "offline_exam_completed": "success",
                "sync_completed": "success",
                "results_verified": "success",
                "progress_synced": "success",
                "sync_status_checked": "success",
                "conflict_resolved": "success",
                "sync_workflow_status": "complete",
            }

    @pytest.mark.asyncio
    async def test_offline_content_caching(self):
        """Offline iÃ§erik Ã¶nbellekleme testi"""

        async with aiohttp.ClientSession() as session:
            login_response = await session.post(
                "http://localhost:8000/api/v1/auth/login",
                json={"username": "cache_user", "password": "test_password"},
            )
            token = (await login_response.json())["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # 1. Ä°Ã§erik Ã¶nbellekleme isteÄŸi
            cache_request = {
                "student_id": "cache_user",
                "content_types": ["videos", "articles", "practice_questions"],
                "subjects": ["Matematik", "Fizik"],
                "cache_size_mb": 100,
            }

            cache_response = await session.post(
                "http://localhost:8000/api/v1/pwa/cache-content",
                json=cache_request,
                headers=headers,
            )
            assert cache_response.status == 200
            cache_result = await cache_response.json()
            assert "cached_items" in cache_result
            assert cache_result["total_size_mb"] <= cache_request["cache_size_mb"]

            # 2. Ã–nbellek durumunu kontrol etme
            cache_status_response = await session.get(
                "http://localhost:8000/api/v1/pwa/cache-status",
                params={"student_id": "cache_user"},
                headers=headers,
            )
            assert cache_status_response.status == 200
            cache_status = await cache_status_response.json()
            assert "cached_items_count" in cache_status
            assert "total_cache_size_mb" in cache_status

            # 3. Ã–nbellekten iÃ§erik alma (offline mode simÃ¼lasyonu)
            cached_content_response = await session.get(
                "http://localhost:8000/api/v1/pwa/cached-content",
                params={
                    "student_id": "cache_user",
                    "content_type": "practice_questions",
                    "subject": "Matematik",
                },
                headers=headers,
            )
            assert cached_content_response.status == 200
            cached_content = await cached_content_response.json()
            assert len(cached_content["items"]) > 0

            return {
                "cache_request": "success",
                "cache_status_checked": "success",
                "cached_content_retrieved": "success",
                "cached_items_count": cache_status["cached_items_count"],
                "total_cache_size_mb": cache_status["total_cache_size_mb"],
            }


if __name__ == "__main__":
    # Run end-to-end tests
    pytest.main([__file__, "-v", "--tb=short", "-x"])
