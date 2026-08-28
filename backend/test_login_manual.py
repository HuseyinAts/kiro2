from fastapi.testclient import TestClient

from application.bootstrap import bootstrap_cqrs
from main import app

bootstrap_cqrs()
client = TestClient(app, raise_server_exceptions=False)
res = client.post(
    "/api/auth/login", json={"email": "wrong@example.com", "sifre": "wrong"}
)
print(res.status_code)
print(res.text)
