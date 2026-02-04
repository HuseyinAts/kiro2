# ADHD Support API - Dikkat Yönetimi Sistemi

## Genel Bakış

DEHB (Dikkat Eksikliği ve Hiperaktivite Bozukluğu) tanılı öğrenciler için kapsamlı dikkat yönetimi API'si.

**Requirements:** REQ-52.1 - REQ-52.20  
**Task:** 88. Dikkat Yönetimi

---

## Özellikler

### 1. Pomodoro Timer (Task 88.1)
- 25 dakika çalışma, 5 dakika mola
- Özelleştirilebilir süre ayarları
- Otomatik mola ve çalışma başlatma
- Oturum geçmişi ve istatistikler

### 2. Görsel Zamanlayıcı (Task 88.2)
- Gerçek zamanlı countdown
- Progress ring verileri
- Renk kodlu oturum tipleri

### 3. Dikkat Dağınıklığı Tespiti (Task 88.3)
- İnaktivite süresi tespiti
- Akıllı uyarı mesajları
- Önerilen aksiyonlar

### 4. Konsantrasyon Egzersizleri (Task 88.4)
- 5 farklı egzersiz (kolay, orta, zor)
- Adım adım talimatlar
- İlerleme takibi

---

## API Endpoints

### Pomodoro Timer

#### Oturum Başlat
```http
POST /api/adhd-support/pomodoro/start
Content-Type: application/json
Authorization: Bearer {token}

{
  "session_type": "work",
  "custom_duration_minutes": 25,
  "task_description": "Matematik çalışması"
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "user_id": 1,
  "session_type": "work",
  "status": "active",
  "duration_minutes": 25,
  "remaining_seconds": 1500,
  "started_at": "2025-10-24T19:00:00Z",
  "ends_at": "2025-10-24T19:25:00Z",
  "task_description": "Matematik çalışması",
  "sessions_completed_today": 0,
  "next_session_type": "short_break"
}
```

#### Mevcut Oturumu Getir
```http
GET /api/adhd-support/pomodoro/current
Authorization: Bearer {token}
```

#### Oturum Güncelle
```http
PUT /api/adhd-support/pomodoro/{session_id}
Content-Type: application/json
Authorization: Bearer {token}

{
  "action": "pause"  // pause, resume, complete, cancel
}
```

#### Ayarları Getir
```http
GET /api/adhd-support/pomodoro/settings
Authorization: Bearer {token}
```

**Response:**
```json
{
  "work_duration_minutes": 25,
  "short_break_minutes": 5,
  "long_break_minutes": 15,
  "sessions_until_long_break": 4,
  "auto_start_breaks": false,
  "auto_start_work": false,
  "sound_enabled": true,
  "notification_enabled": true
}
```

#### Ayarları Güncelle
```http
PUT /api/adhd-support/pomodoro/settings
Content-Type: application/json
Authorization: Bearer {token}

{
  "work_duration_minutes": 30,
  "short_break_minutes": 10,
  "auto_start_breaks": true
}
```

#### Geçmişi Getir
```http
GET /api/adhd-support/pomodoro/history?limit=20&offset=0
Authorization: Bearer {token}
```

---

### Görsel Zamanlayıcı

#### Timer Verilerini Getir
```http
GET /api/adhd-support/timer/visual/{session_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "session_id": "uuid",
  "remaining_seconds": 1500,
  "total_seconds": 1500,
  "progress_percentage": 0.0,
  "time_display": "25:00",
  "is_active": true,
  "session_type": "work",
  "color_scheme": {
    "primary": "#4CAF50",
    "secondary": "#81C784",
    "background": "#E8F5E9"
  }
}
```

---

### Dikkat Dağınıklığı Tespiti

#### İnaktivite Tespit Et
```http
POST /api/adhd-support/inactivity/detect?inactive_duration_seconds=120
Authorization: Bearer {token}
```

**Response:**
```json
{
  "alert_id": "uuid",
  "user_id": 1,
  "detected_at": "2025-10-24T19:00:00Z",
  "inactive_duration_seconds": 120,
  "alert_message": "Dikkatini toplamaya çalış. Küçük bir mola verebilirsin. ☕",
  "suggested_action": "short_break"
}
```

#### Uyarı Geçmişi
```http
GET /api/adhd-support/inactivity/alerts?limit=10
Authorization: Bearer {token}
```

---

### Konsantrasyon Egzersizleri

#### Egzersizleri Listele
```http
GET /api/adhd-support/focus-exercises?difficulty=easy
Authorization: Bearer {token}
```

**Response:**
```json
[
  {
    "exercise_id": "breathing-4-7-8",
    "title": "4-7-8 Nefes Egzersizi",
    "description": "Derin nefes alarak zihnini sakinleştir",
    "duration_minutes": 5,
    "difficulty": "easy",
    "instructions": [
      "Rahat bir pozisyonda otur",
      "4 saniye boyunca burnundan nefes al",
      "7 saniye nefesini tut",
      "8 saniye boyunca ağzından nefes ver"
    ],
    "benefits": [
      "Stresi azaltır",
      "Odaklanmayı artırır"
    ]
  }
]
```

#### Egzersiz Başlat
```http
POST /api/adhd-support/focus-exercises/{exercise_id}/start
Authorization: Bearer {token}
```

#### Egzersiz Tamamla
```http
PUT /api/adhd-support/focus-exercises/progress/{exercise_id}/complete
  ?duration_seconds=300
  &success_rate=0.85
  &notes=Çok rahatlatıcıydı
Authorization: Bearer {token}
```

#### İlerleme Geçmişi
```http
GET /api/adhd-support/focus-exercises/progress?limit=20
Authorization: Bearer {token}
```

---

### İstatistikler ve Öneriler

#### Günlük İstatistikler
```http
GET /api/adhd-support/stats/daily
Authorization: Bearer {token}
```

**Response:**
```json
{
  "date": "2025-10-24",
  "pomodoro_sessions": {
    "total": 8,
    "completed": 6,
    "work_minutes": 150,
    "break_minutes": 30
  },
  "focus_exercises": {
    "total": 3,
    "completed": 2,
    "total_minutes": 20
  },
  "inactivity_alerts": {
    "total": 2,
    "average_duration_seconds": 180
  },
  "focus_score": 85.0,
  "productivity_trend": "improving"
}
```

#### Kişiselleştirilmiş Öneriler
```http
GET /api/adhd-support/recommendations
Authorization: Bearer {token}
```

**Response:**
```json
{
  "recommendations": [
    {
      "type": "pomodoro",
      "title": "Pomodoro Tekniğini Dene",
      "description": "25 dakikalık odaklanma oturumları ile verimliliğini artır",
      "priority": "high",
      "estimated_benefit": "Odaklanma süresini %40 artırabilir"
    }
  ],
  "personalized_message": "Bugün harika gidiyorsun! 🎯"
}
```

---

## Veri Modelleri

### PomodoroSessionType (Enum)
- `work` - Çalışma oturumu (25dk)
- `short_break` - Kısa mola (5dk)
- `long_break` - Uzun mola (15dk)

### PomodoroSessionStatus (Enum)
- `active` - Aktif çalışıyor
- `paused` - Duraklatıldı
- `completed` - Tamamlandı
- `cancelled` - İptal edildi

### Suggested Actions
- `continue` - Devam et
- `short_break` - Kısa mola ver
- `walk_break` - Yürüyüş yap
- `restart_session` - Yeni oturum başlat

---

## Kullanım Örnekleri

### Python (requests)
```python
import requests

# Pomodoro oturumu başlat
response = requests.post(
    "http://localhost:8000/api/adhd-support/pomodoro/start",
    json={
        "session_type": "work",
        "task_description": "Fizik çalışması"
    },
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

session = response.json()
print(f"Oturum başlatıldı: {session['session_id']}")
print(f"Bitiş zamanı: {session['ends_at']}")
```

### JavaScript (fetch)
```javascript
// Konsantrasyon egzersizlerini getir
const response = await fetch(
  'http://localhost:8000/api/adhd-support/focus-exercises?difficulty=easy',
  {
    headers: {
      'Authorization': 'Bearer YOUR_TOKEN'
    }
  }
);

const exercises = await response.json();
console.log(`${exercises.length} egzersiz bulundu`);
```

### cURL
```bash
# Dikkat dağınıklığı tespit et
curl -X POST \
  "http://localhost:8000/api/adhd-support/inactivity/detect?inactive_duration_seconds=180" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Hata Kodları

| Kod | Açıklama |
|-----|----------|
| 200 | Başarılı |
| 401 | Yetkisiz (token geçersiz) |
| 404 | Oturum bulunamadı |
| 422 | Geçersiz input (validation hatası) |
| 500 | Sunucu hatası |

---

## Notlar

### Türkçe Dil Desteği
- Tüm mesajlar Türkçe
- Emoji kullanımı (motivasyon için)
- Kültürel uygunluk

### DEHB Özel Tasarım
- Nazik hatırlatmalar
- Pozitif pekiştirme
- Küçük adımlar
- Görsel destekler

### Güvenlik
- JWT authentication required
- User data isolation
- Input validation (Pydantic)

---

## Frontend Entegrasyon

### React Örneği
```typescript
import { useState, useEffect } from 'react';

function PomodoroTimer() {
  const [session, setSession] = useState(null);
  
  const startSession = async () => {
    const response = await fetch('/api/adhd-support/pomodoro/start', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        session_type: 'work',
        task_description: 'Matematik çalışması'
      })
    });
    
    const data = await response.json();
    setSession(data);
  };
  
  return (
    <div>
      <button onClick={startSession}>Pomodoro Başlat</button>
      {session && (
        <div>
          <h3>{session.task_description}</h3>
          <p>Kalan süre: {Math.floor(session.remaining_seconds / 60)}:{session.remaining_seconds % 60}</p>
        </div>
      )}
    </div>
  );
}
```

---

## Test

```bash
# Backend testlerini çalıştır
cd backend
pytest tests/test_adhd_support_api.py -v
```

---

## Lisans

Bu API, Türkiye Üniversite Sınavları Hazırlık Platformu'nun bir parçasıdır.

**Geliştirici:** Kiro AI  
**Tarih:** 24 Ekim 2025  
**Versiyon:** 1.0.0
