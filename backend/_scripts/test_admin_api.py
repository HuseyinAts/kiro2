"""
Admin Panel API Test
Admin API endpoint'lerinin çalışıp çalışmadığını test eder
"""
import os
import sys

# Backend dizinini Python path'ine ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient

from main import app


def test_admin_api_endpoints():
    """Admin API endpoint'lerini test et"""
    client = TestClient(app)

    print("🧪 Admin Panel API Test Başlatılıyor...")

    # Test kullanıcısı oluştur (admin rolü ile)
    test_admin = {
        "email": "admin@test.com",
        "ad_soyad": "Test Admin",
        "sifre": "admin123",
        "rol": "admin",
    }

    try:
        # 1. Admin kullanıcısı oluştur
        print("\n1️⃣ Admin kullanıcısı oluşturuluyor...")

        # Önce auth endpoint'ini test et
        auth_response = client.post("/api/v1/auth/register", json=test_admin)
        print(f"Auth register response: {auth_response.status_code}")

        if auth_response.status_code == 200:
            auth_data = auth_response.json()
            token = auth_data.get("access_token")
            print(f"[CHECK] Admin kullanıcısı oluşturuldu, token alındı")

            # 2. Admin API endpoint'lerini test et
            headers = {"Authorization": f"Bearer {token}"}

            print("\n2️⃣ Admin API endpoint'leri test ediliyor...")

            # Dashboard stats
            stats_response = client.get(
                "/api/v1/admin/dashboard/stats", headers=headers
            )
            print(f"Dashboard stats: {stats_response.status_code}")
            if stats_response.status_code == 200:
                print("[CHECK] Dashboard istatistikleri endpoint'i çalışıyor")
            else:
                print(f"[X] Dashboard stats hatası: {stats_response.text}")

            # Users list
            users_response = client.get("/api/v1/admin/users", headers=headers)
            print(f"Users list: {users_response.status_code}")
            if users_response.status_code == 200:
                print("[CHECK] Kullanıcı listesi endpoint'i çalışıyor")
            else:
                print(f"[X] Users list hatası: {users_response.text}")

            # Content questions
            questions_response = client.get(
                "/api/v1/admin/content/questions", headers=headers
            )
            print(f"Content questions: {questions_response.status_code}")
            if questions_response.status_code == 200:
                print("[CHECK] Soru bankası endpoint'i çalışıyor")
            else:
                print(f"[X] Questions hatası: {questions_response.text}")

            # Educational content
            educational_response = client.get(
                "/api/v1/admin/content/educational", headers=headers
            )
            print(f"Educational content: {educational_response.status_code}")
            if educational_response.status_code == 200:
                print("[CHECK] Eğitim materyalleri endpoint'i çalışıyor")
            else:
                print(f"[X] Educational content hatası: {educational_response.text}")

            print("\n[PARTY] Admin Panel API Test Tamamlandı!")

        else:
            print(f"[X] Admin kullanıcısı oluşturulamadı: {auth_response.text}")

    except Exception as e:
        print(f"[X] Test hatası: {str(e)}")


if __name__ == "__main__":
    test_admin_api_endpoints()
