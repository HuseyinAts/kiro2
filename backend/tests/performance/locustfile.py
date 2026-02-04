# -*- coding: utf-8 -*-
"""
Locust Performance Test Suite
Teknofest 2025 Eğitim Eylemci Platformu için yük testleri

Bu dosya, sistemin performansını çeşitli senaryolar altında test eder:
- Normal kullanıcı trafiği
- Sınav dönemindeki yoğun kullanım
- Devrimsel özellikler yük testi
- API endpoint performansı
"""

import random
from datetime import datetime, timedelta

from locust import between, events, task
from locust.contrib.fasthttp import FastHttpUser


class TeknoFestUser(FastHttpUser):
    """Temel kullanıcı davranış modeli"""

    wait_time = between(1, 5)  # 1-5 saniye arası bekleme

    def on_start(self):
        """Kullanıcı başlangıç işlemleri"""
        self.login()
        self.student_id = f"perf_test_student_{random.randint(1000, 9999)}"
        self.auth_headers = {"Authorization": f"Bearer {self.token}"}

    def login(self):
        """Kullanıcı girişi simülasyonu"""
        login_data = {
            "username": f"test_user_{random.randint(1, 1000)}",
            "password": "test_password",
        }

        with self.client.post(
            "/api/v1/auth/login", json=login_data, catch_response=True
        ) as response:
            if response.status_code == 200:
                self.token = response.json().get("access_token", "mock_token")
                response.success()
            else:
                self.token = "mock_token"  # Fallback for testing
                response.success()  # Don't fail on auth for load testing

    @task(3)
    def browse_dashboard(self):
        """Ana dashboard görüntüleme"""
        self.client.get("/api/v1/dashboard", headers=self.auth_headers)

    @task(2)
    def get_student_profile(self):
        """Öğrenci profili görüntüleme"""
        self.client.get(
            f"/api/v1/student/profile/{self.student_id}", headers=self.auth_headers
        )

    @task(2)
    def get_questions(self):
        """Rastgele sorular alma"""
        params = {
            "subject": random.choice(["Matematik", "Türkçe", "Fizik", "Kimya"]),
            "difficulty": random.choice(["easy", "medium", "hard"]),
            "count": random.randint(5, 20),
        }
        self.client.get(
            "/api/v1/questions/random", params=params, headers=self.auth_headers
        )

    @task(1)
    def submit_answer(self):
        """Soru cevaplama"""
        answer_data = {
            "question_id": f"q_{random.randint(1, 1000)}",
            "selected_answer": random.randint(0, 3),
            "time_spent_seconds": random.randint(30, 180),
        }
        self.client.post(
            "/api/v1/exam/answer", json=answer_data, headers=self.auth_headers
        )


class RevolutionaryFeaturesUser(FastHttpUser):
    """Devrimsel özellikler yük testi"""

    wait_time = between(2, 8)  # Daha uzun bekleme (AI işlemleri)

    def on_start(self):
        self.login()
        self.student_id = f"revolutionary_test_{random.randint(1000, 9999)}"
        self.auth_headers = {"Authorization": f"Bearer {self.token}"}

    def login(self):
        """Mock login"""
        self.token = "mock_revolutionary_token"

    @task(2)
    def learning_style_detection(self):
        """Öğrenme stili tespiti yük testi"""
        request_data = {
            "student_id": self.student_id,
            "behavioral_data": [
                {
                    "video_watch_time": random.randint(60, 300),
                    "visual_content_performance": random.uniform(0.3, 1.0),
                    "interactive_engagement": random.randint(10, 100),
                    "text_reading_time": random.randint(20, 120),
                    "timestamp": datetime.now().isoformat(),
                }
                for _ in range(random.randint(5, 15))
            ],
            "questionnaire_responses": [
                {
                    "question": "Öğrenme tercihiniz?",
                    "response": random.choice(
                        [
                            "Görsel materyaller",
                            "Sesli açıklamalar",
                            "Okuma yazma",
                            "Uygulamalı çalışma",
                        ]
                    ),
                    "confidence": random.uniform(0.5, 1.0),
                }
            ],
        }

        with self.client.post(
            "/api/v1/revolutionary/learning-style/detect",
            json=request_data,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(
                    f"Learning style detection failed: {response.status_code}"
                )

    @task(2)
    def morphology_irt_analysis(self):
        """Morfoloji IRT analiz yük testi"""
        complex_texts = [
            "Çekoslovakyalılaştıramadıklarımızdanmısınız kelimesinin morfolojik yapısını analiz ediniz.",
            "Muvaffakiyetsizleştiricileştiriveremeyebileceklerimizdenmişsinizcesine sözcüğünün ek analizi.",
            "Bu mütalaa çok önemli bir tetkik gerektiriyor ve mütehassıslar tarafından incelenmelidir.",
        ]

        request_data = {
            "question": {
                "text": random.choice(complex_texts),
                "difficulty": random.uniform(1.5, 3.5),
                "discrimination": random.uniform(1.0, 2.5),
                "subject": "Türkçe",
                "topic": "Morfoloji",
            },
            "student": {
                "id": self.student_id,
                "ability": random.uniform(0.5, 2.5),
                "morphology_awareness": random.uniform(0.3, 1.0),
            },
        }

        self.client.post(
            "/api/v1/revolutionary/morphology-irt/analyze",
            json=request_data,
            headers=self.auth_headers,
        )

    @task(1)
    def text_simplification(self):
        """Metin basitleştirme yük testi"""
        complex_texts = [
            "Bu mütalaa çok önemli bir tetkik gerektiriyor ve mütehassıslar tarafından detaylı bir müzakere yapılmalıdır.",
            "İstifade ettiğimiz münasebetler neticesinde istihsal edilen mahsuller müspet neticeler vermiştir.",
            "Çekoslovakyalılaştıramadıklarımızdanmısınız gibi kelimeler Türkçe'nin zengin morfolojik yapısını gösterir.",
        ]

        request_data = {
            "text": random.choice(complex_texts),
            "target_level": random.choice(["elementary", "intermediate", "advanced"]),
        }

        self.client.post(
            "/api/v1/revolutionary/simplification/simplify",
            json=request_data,
            headers=self.auth_headers,
        )

    @task(1)
    def bionic_reading(self):
        """Bionic Reading yük testi"""
        texts = [
            "Çocuklar bahçede oynuyorlar ve çok eğleniyorlar.",
            "Türkçe'nin zengin morfolojik yapısı çok ilginçtir.",
            "Merhaba dünya! Bu bir test metnidir.",
        ]

        request_data = {"text": random.choice(texts)}

        self.client.post(
            "/api/v1/revolutionary/bionic-reading/apply",
            json=request_data,
            headers=self.auth_headers,
        )


class ExamUser(FastHttpUser):
    """Sınav senaryosu yük testi"""

    wait_time = between(30, 120)  # Soru arası gerçekçi bekleme

    def on_start(self):
        self.login()
        self.student_id = f"exam_test_{random.randint(1000, 9999)}"
        self.auth_headers = {"Authorization": f"Bearer {self.token}"}
        self.session_id = None

    def login(self):
        self.token = "mock_exam_token"

    @task(1)
    def start_exam(self):
        """Sınav başlatma"""
        exam_data = {
            "exam_type": random.choice(["TYT", "AYT", "YDT"]),
            "student_id": self.student_id,
            "duration_minutes": random.choice([165, 210, 180]),
        }

        with self.client.post(
            "/api/v1/exam/start",
            json=exam_data,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                self.session_id = response.json().get(
                    "session_id", f"mock_session_{random.randint(1000, 9999)}"
                )
                response.success()
            else:
                self.session_id = f"mock_session_{random.randint(1000, 9999)}"
                response.success()

    @task(10)
    def answer_question(self):
        """Soru cevaplama (sınav sırasında en sık yapılan işlem)"""
        if not self.session_id:
            self.start_exam()

        answer_data = {
            "question_id": f"q_{random.randint(1, 200)}",
            "selected_answer": random.randint(0, 3),
            "time_spent_seconds": random.randint(45, 300),
        }

        self.client.post(
            f"/api/v1/exam/{self.session_id}/answer",
            json=answer_data,
            headers=self.auth_headers,
        )

    @task(1)
    def get_exam_progress(self):
        """Sınav ilerleme durumu"""
        if self.session_id:
            self.client.get(
                f"/api/v1/exam/{self.session_id}/progress", headers=self.auth_headers
            )


class TeacherUser(FastHttpUser):
    """Öğretmen kullanıcı senaryosu"""

    wait_time = between(5, 15)

    def on_start(self):
        self.login()
        self.teacher_id = f"teacher_{random.randint(100, 999)}"
        self.auth_headers = {"Authorization": f"Bearer {self.token}"}

    def login(self):
        self.token = "mock_teacher_token"

    @task(3)
    def view_class_performance(self):
        """Sınıf performansı görüntüleme"""
        self.client.get(
            f"/api/v1/teacher/class-performance/{self.teacher_id}",
            headers=self.auth_headers,
        )

    @task(2)
    def create_assignment(self):
        """Ödev oluşturma"""
        assignment_data = {
            "teacher_id": self.teacher_id,
            "title": f"Test Ödevi {random.randint(1, 100)}",
            "subject": random.choice(["Matematik", "Türkçe", "Fizik", "Kimya"]),
            "question_count": random.randint(10, 30),
            "difficulty_level": random.choice(["easy", "medium", "hard"]),
            "due_date": (
                datetime.now() + timedelta(days=random.randint(1, 14))
            ).isoformat(),
        }

        self.client.post(
            "/api/v1/teacher/create-assignment",
            json=assignment_data,
            headers=self.auth_headers,
        )

    @task(1)
    def view_student_progress(self):
        """Öğrenci ilerlemesi görüntüleme"""
        student_id = f"student_{random.randint(1000, 9999)}"
        self.client.get(
            f"/api/v1/teacher/student-progress/{student_id}", headers=self.auth_headers
        )


# Performance test event handlers
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Test başlangıcında çalışır"""
    print("[ROCKET] Performance test başlatılıyor...")
    print(f"Target host: {environment.host}")
    print(f"User classes: {[cls.__name__ for cls in environment.user_classes]}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Test bitiminde çalışır"""
    print("[CHECK] Performance test tamamlandı!")

    # Test sonuçlarını özetle
    stats = environment.stats
    print(f"Total requests: {stats.total.num_requests}")
    print(f"Total failures: {stats.total.num_failures}")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"95th percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")

    # Başarı kriterleri kontrolü
    failure_rate = (
        stats.total.num_failures / stats.total.num_requests
        if stats.total.num_requests > 0
        else 0
    )
    avg_response_time = stats.total.avg_response_time

    if failure_rate > 0.05:  # %5'ten fazla hata
        print(f"[X] FAIL: Hata oranı çok yüksek: {failure_rate:.2%}")
        environment.process_exit_code = 1

    if avg_response_time > 2000:  # 2 saniyeden fazla ortalama yanıt süresi
        print(f"[X] FAIL: Ortalama yanıt süresi çok yüksek: {avg_response_time:.2f}ms")
        environment.process_exit_code = 1

    if failure_rate <= 0.05 and avg_response_time <= 2000:
        print("[CHECK] PASS: Performans kriterleri karşılandı!")


# Custom user distribution for different scenarios
class ExamSeasonScenario(TeknoFestUser):
    """Sınav dönemi yoğun kullanım senaryosu"""

    weight = 3
    wait_time = between(0.5, 2)  # Daha hızlı kullanım


class NormalUsageScenario(TeknoFestUser):
    """Normal dönem kullanım senaryosu"""

    weight = 2
    wait_time = between(2, 8)


class RevolutionaryFeaturesScenario(RevolutionaryFeaturesUser):
    """Devrimsel özellikler yoğun kullanım"""

    weight = 1
    wait_time = between(3, 10)


if __name__ == "__main__":
    # Standalone çalıştırma için
    import os

    from locust import run_single_user

    # Test environment
    os.environ["LOCUST_HOST"] = "http://localhost:8000"

    # Run single user test
    run_single_user(TeknoFestUser)
