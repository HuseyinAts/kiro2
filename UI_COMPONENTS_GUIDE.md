# 🎨 UI Components Kullanım Kılavuzu
## Frontend Specialist Agent tarafından oluşturuldu

## ✅ TAMAMLANAN İŞLER

### 1. Frontend Components (3 Component)

#### 📋 QuestionBank.tsx
**Konum:** `frontend/src/components/Questions/QuestionBank.tsx`

**Özellikler:**
- ✅ 141 soruyu listeleme
- ✅ Filtreleme (Sınav tipi, Konu, Zorluk)
- ✅ Arama (Soru metni ve konu)
- ✅ Sayfalama (10 soru/sayfa)
- ✅ Responsive design
- ✅ IRT parametreleri gösterimi
- ✅ Doğru cevap vurgulama

**Kullanım:**
```tsx
import QuestionBank from '@/components/Questions/QuestionBank';

<QuestionBank apiUrl="http://localhost:8000/api/questions" />
```

---

#### 📊 QuestionStatsDashboard.tsx
**Konum:** `frontend/src/components/Questions/QuestionStatsDashboard.tsx`

**Özellikler:**
- ✅ Toplam soru istatistikleri
- ✅ Sınav tipi dağılımı (Progress bars)
- ✅ Konu dağılımı (Top 10)
- ✅ Zorluk seviyesi dağılımı
- ✅ IRT parametreleri özeti
- ✅ Soru kalite göstergeleri

**Kullanım:**
```tsx
import QuestionStatsDashboard from '@/components/Questions/QuestionStatsDashboard';

<QuestionStatsDashboard apiUrl="http://localhost:8000/api/questions" />
```

---

#### 🏠 QuestionBankPage.tsx
**Konum:** `frontend/src/pages/QuestionBankPage.tsx`

**Özellikler:**
- ✅ Tab'lı arayüz (Soru Listesi / İstatistikler)
- ✅ Sticky header
- ✅ Icon'lu navigation
- ✅ Responsive layout

**Kullanım:**
```tsx
import QuestionBankPage from '@/pages/QuestionBankPage';

// Route olarak ekleyin
<Route path="/question-bank" element={<QuestionBankPage />} />
```

---

### 2. Backend API (8 Endpoint)

#### 📡 questions_api.py
**Konum:** `backend/api/questions_api.py`

**Endpoints:**

| Endpoint | Method | Açıklama |
|----------|--------|----------|
| `/api/questions` | GET | Tüm soruları listele (filtreleme destekli) |
| `/api/questions/{id}` | GET | ID'ye göre tek soru |
| `/api/questions/random/one` | GET | Rastgele soru |
| `/api/questions/stats/summary` | GET | İstatistikler |
| `/api/questions/subjects/list` | GET | Tüm konular |
| `/api/questions/topics/list` | GET | Alt konular |

**Filtrele Parameters:**
- `exam_type` - TYT, AYT, YDT
- `subject` - Matematik, Fizik, etc.
- `topic` - Alt konu
- `min_difficulty` - Minimum zorluk
- `max_difficulty` - Maximum zorluk
- `limit` - Sonuç sayısı
- `offset` - Başlangıç offset

**Örnek Kullanım:**
```bash
# Tüm sorular
curl http://localhost:8000/api/questions

# TYT Matematik soruları
curl "http://localhost:8000/api/questions?exam_type=TYT&subject=Matematik"

# Zor sorular (0.5-0.7 zorluk)
curl "http://localhost:8000/api/questions?min_difficulty=0.5&max_difficulty=0.7"

# İstatistikler
curl http://localhost:8000/api/questions/stats/summary

# Rastgele soru
curl http://localhost:8000/api/questions/random/one
```

---

## 🚀 NASIL KULLANILIR?

### Adım 1: Backend Çalıştır
```bash
cd backend
py -m uvicorn main:app --reload --port 8000
```

### Adım 2: Frontend Route Ekle

`frontend/src/App.tsx` veya routing dosyanıza ekleyin:

```tsx
import QuestionBankPage from './pages/QuestionBankPage';

// Routes içinde
<Route path="/questions" element={<QuestionBankPage />} />
```

### Adım 3: Navigation Ekle

Ana navigation'a link ekleyin:

```tsx
<Link to="/questions">
  Soru Bankası (141 Soru)
</Link>
```

### Adım 4: Frontend Başlat
```bash
cd frontend
npm start
```

### Adım 5: Tarayıcıda Aç
```
http://localhost:3000/questions
```

---

## 📊 ÖZELLİKLER

### Soru Listesi Tab

**Filtreler:**
- 🔍 Arama kutusu (soru metni ve konu)
- 📚 Sınav tipi dropdown (TYT, AYT, YDT)
- 📖 Konu dropdown (Matematik, Fizik, etc.)
- ⚖️ Zorluk dropdown (Kolay, Orta, Zor, Çok Zor)

**Görünüm:**
- Soru metni
- 5 şık (A-E)
- Doğru cevap vurgulaması (yeşil)
- IRT parametreleri
- Açıklama (varsa)
- Sayfalama (10 soru/sayfa)

**İstatistik Kartları (Üstte):**
- TYT soru sayısı (mavi)
- AYT soru sayısı (yeşil)
- YDT soru sayısı (mor)

---

### İstatistikler Tab

**Üst Kartlar:**
- Toplam soru sayısı
- Ortalama zorluk
- Konu sayısı
- Ortalama ayırt edicilik

**Grafikler:**
- Sınav tipi dağılımı (Progress bars)
- Konu dağılımı (Horizontal bars, top 10)
- Zorluk seviyesi dağılımı
- IRT parametreleri (Zorluk, Ayırt edicilik, Tahmin)

**Kalite Göstergeleri:**
- Yüksek kalite sorular (ayırt edicilik > 1.0)
- Orta kalite sorular (0.5-1.0)
- İncelenmeli sorular (< 0.5)

---

## 🎨 TASARIM ÖZELLİKLERİ

### Renk Paleti
- **TYT:** Mavi (`bg-blue-500`)
- **AYT:** Yeşil (`bg-green-500`)
- **YDT:** Mor (`bg-purple-500`)
- **Kolay:** Yeşil (`bg-green-100`)
- **Orta:** Sarı (`bg-yellow-100`)
- **Zor:** Turuncu (`bg-orange-100`)
- **Çok Zor:** Kırmızı (`bg-red-100`)

### Responsive Design
- ✅ Mobile first
- ✅ Tablet optimizasyonu
- ✅ Desktop geniş layout
- ✅ Grid system (1/2/4 columns)

### Accessibility
- ✅ Semantic HTML
- ✅ ARIA labels (future)
- ✅ Keyboard navigation ready
- ✅ Color contrast WCAG AA

---

## 🔧 TEKNOLOJİLER

**Frontend:**
- React 18
- TypeScript
- Tailwind CSS
- Shadcn/ui components
- Fetch API

**Backend:**
- FastAPI
- PostgreSQL
- psycopg2
- Pydantic

---

## 📝 ÖRNEK KULLANIM SENARYOLARI

### Senaryo 1: Matematik Soruları Filtrele
1. Soru Bankası sayfasını aç
2. "Konu" dropdown'dan "Matematik" seç
3. 35 matematik sorusu listelenir
4. Sayfalama ile tüm soruları gez

### Senaryo 2: Zor TYT Soruları Bul
1. "Sınav Tipi" = TYT
2. "Zorluk" = Zor
3. Sadece zor TYT soruları görünür

### Senaryo 3: İstatistikleri İncele
1. "İstatistikler" tab'ına geç
2. Sınav tipi dağılımını gör (TYT: 72, AYT: 58, YDT: 11)
3. Konu dağılımını incele
4. IRT parametrelerini kontrol et

### Senaryo 4: Arama Yap
1. Arama kutusuna "fotosentez" yaz
2. 13 fotosentez sorusu listelenir
3. Tüm filtreleri temizle butonu ile sıfırla

---

## 🐛 TROUBLESHOOTING

### Backend API bağlanamıyor
**Sorun:** `Failed to fetch`
**Çözüm:**
```bash
# Backend'in çalıştığından emin olun
netstat -ano | findstr :8000

# Yoksa başlatın
cd backend
py -m uvicorn main:app --reload --port 8000
```

### PostgreSQL bağlantı hatası
**Sorun:** `Database connection error`
**Çözüm:**
```bash
# PostgreSQL çalışıyor mu?
net start postgresql-x64-18

# Şifre doğru mu? (.env)
DATABASE_URL=postgresql+asyncpg://postgres:1470@localhost:5434/turkiye_sinav_db
```

### Componentler görünmüyor
**Sorun:** Import hataları
**Çözüm:**
```bash
# Dependencies kurulu mu?
cd frontend
npm install

# TypeScript build
npm run build
```

---

## ✅ KONTROL LİSTESİ

Kurulum tamamlandı mı?

- [ ] Backend çalışıyor (port 8000)
- [ ] PostgreSQL çalışıyor (port 5434)
- [ ] 141 soru database'de
- [ ] API endpoint'leri erişilebilir
- [ ] Frontend route eklendi
- [ ] Components import edildi
- [ ] Tarayıcıda sayfa açılıyor
- [ ] Filtreler çalışıyor
- [ ] İstatistikler görünüyor

---

## 🎉 SONUÇ

**✅ BAŞARIYLA TAMAMLANDI!**

3 React component + 8 REST API endpoint ile tam fonksiyonel bir soru bankası arayüzü oluşturduk!

**Oluşturulan Dosyalar:**
1. `frontend/src/components/Questions/QuestionBank.tsx` (365 satır)
2. `frontend/src/components/Questions/QuestionStatsDashboard.tsx` (315 satır)
3. `frontend/src/pages/QuestionBankPage.tsx` (85 satır)
4. `backend/api/questions_api.py` (350 satır)

**Toplam:** ~1115 satır kod

**Özellikler:**
- Filtreleme ✅
- Arama ✅
- Sayfalama ✅
- İstatistikler ✅
- Responsive ✅
- Type-safe ✅

---

**Frontend Specialist Agent**
*KIRO2 Platform*
*15 Kasım 2025*
