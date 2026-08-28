# Plan: Teacher Co-Pilot Dashboard (2026 Q3-Q4 ZPD & Unutma Eğrisi Takip Ekranları)

## Kapsam ve Amaç
Öğretmenlerin sınıflarındaki öğrencilerin ZPD (Yakınsal Gelişim Alanı) seviyelerini, FSRS unutma eğrilerini ve yapay zeka tarafından tespit edilen kavram yanılgılarını (Misconception Risks) anlık takip edebileceği modern Teacher Co-Pilot Paneli geliştirilmesi.

## Bileşenler ve Değiştirilecek Dosyalar

1. **`backend/api/teacher_copilot_api.py` (Yeni Backend API):**
   - GET `/api/v1/teacher-copilot/dashboard-analytics` -> Sınıf bazlı ZPD dağılımı, FSRS ortalama hatırlanabilirlik (% Retention), 7 günlük unutma riski taşıyan konular, AI kavram yanılgısı uyarıları.
   - GET `/api/v1/teacher-copilot/misconception-alerts` -> Detaylı kavrama hatası risk listesi ve Sokratik müdahale önerileri.
   - GET `/api/v1/teacher-copilot/zpd-student-breakdown` -> Öğrenci ZPD matrisi.

2. **`backend/main.py`:**
   - `teacher_copilot_api.router` kaydı.

3. **`frontend/src/components/Teacher/TeacherCoPilotDashboard.tsx` (Yeni Frontend Bileşeni):**
   - Premium Glassmorphism & HSL renk paletli zengin UI.
   - Sınıf ZPD seviyesi ilerleme çubukları, FSRS hafıza kaybı çarkı, AI Kavram Yanılgısı kartları ve hızlı eylem butonları ("Sokratik Ödev Gönder", "Kavram Özetini Paylaş").

4. **`frontend/src/pages/ModernTeacherCoPilotPage.tsx` (Yeni Frontend Sayfası):**
   - RoleBasedLayout ile korunan öğretmen co-pilot sayfası.

5. **`frontend/src/App.tsx`:**
   - `/teacher/copilot` lazy route tanımı.

6. **Test Suite:**
   - `backend/tests/unit/test_teacher_copilot.py`
   - `frontend/src/components/Teacher/__tests__/TeacherCoPilotDashboard.test.tsx`
