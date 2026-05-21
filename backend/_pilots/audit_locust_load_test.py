"""
Locust API Load Test — İleri Düzey Audit

Real concurrent student behavior under sustained load.
50 student × 5dk → throughput + p95 latency per endpoint + error rate.

Web UI: http://localhost:8089
Headless run:
    locust -f backend/_pilots/audit_locust_load_test.py --headless \
        -u 50 -r 5 --run-time 60s --host http://localhost:8000 \
        --csv=/tmp/locust_kiro2 --html=/tmp/locust_kiro2.html

NOT: Rate limit 10/60s yüzünden -r 5 (5 user/sec ramp) ile dağıt.
30 USER MAX (rate limit 30/60 önerilen post-fix).
"""

from __future__ import annotations

import random

from locust import HttpUser, between, task


class KIRO2Student(HttpUser):
    """Real-ish KIRO2 student session simulation."""

    wait_time = between(2, 5)  # 2-5 saniye think time

    def on_start(self):
        """Login on session start."""
        email = f"student{random.randint(1, 9)}@kiro2.com"
        # MVP seed test user
        r = self.client.post(
            "/api/v1/auth/login",
            json={"email": "test@kiro2.com", "password": "Kiro2Beta2026@x"},
        )
        if r.status_code == 200:
            data = r.json()
            token = data.get("access_token") or data.get("token")
            if token:
                self.client.headers["Authorization"] = f"Bearer {token}"
            self.environment.events.user_count_changed.fire(user_count=1)
        else:
            self.environment.runner.quit()

    @task(weight=10)
    def get_me(self):
        with self.client.get(
            "/api/v1/auth/me", catch_response=True, name="/auth/me"
        ) as r:
            if r.status_code >= 500:
                r.failure(f"crash {r.status_code}")

    @task(weight=8)
    def learning_path_today(self):
        with self.client.get(
            "/api/v1/learning-path/today",
            catch_response=True,
            name="/learning-path/today",
        ) as r:
            if r.status_code >= 500:
                r.failure(f"crash {r.status_code}")

    @task(weight=6)
    def fsrs_due(self):
        with self.client.get(
            "/api/v1/fsrs/due", catch_response=True, name="/fsrs/due"
        ) as r:
            if r.status_code >= 500:
                r.failure(f"crash {r.status_code}")

    @task(weight=4)
    def osym_configs(self):
        with self.client.get(
            "/api/v1/osym-exam/exam-configs",
            catch_response=True,
            name="/osym-exam/exam-configs",
        ) as r:
            if r.status_code >= 500:
                r.failure(f"crash {r.status_code}")

    @task(weight=3)
    def youtube_search(self):
        with self.client.post(
            "/api/v1/youtube/search",
            json={"query": "matematik konu anlatımı", "limit": 5},
            catch_response=True,
            name="/youtube/search",
        ) as r:
            if r.status_code >= 500:
                r.failure(f"crash {r.status_code}")
