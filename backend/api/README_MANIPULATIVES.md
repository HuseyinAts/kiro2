# Manipülatifler API - Task 87

## Genel Bakış

Manipülatifler API, diskalkuli (matematik öğrenme güçlüğü) olan öğrenciler için interaktif matematik araçları sağlar. Bu API, 4 ana manipülatif aracı destekler:

1. **Sanal Bloklar** (Virtual Blocks)
2. **GeoGebra Entegrasyonu**
3. **İnteraktif Geometri**
4. **Dijital Tangram**

## Requirements

- **REQ-51.81-51.85**: Sanal bloklar, drag-and-drop, miktar işlemleri
- **REQ-51.86-51.90**: GeoGebra embed, interaktif geometri, dinamik matematik
- **REQ-51.91-51.95**: İnşa araçları, ölçüm araçları, dönüşüm araçları
- **REQ-51.96-51.100**: Tangram puzzle arayüzü, şekil tanıma, uzamsal akıl yürütme

## API Endpoints

### Sanal Bloklar

#### POST `/api/manipulatives/virtual-blocks/operation`
Sanal blok işlemini kaydet.

**Request Body:**
```json
{
  "operation_type": "add",
  "blocks_used": [
    {"type": "unit", "count": 5},
    {"type": "ten", "count": 2}
  ],
  "result": 25,
  "duration_seconds": 120
}
```

**Response:**
```json
{
  "success": true,
  "message": "Sanal blok işlemi kaydedildi",
  "data": {
    "operation_type": "add",
    "result": 25,
    "blocks_used": [...],
    "duration": 120
  }
}
```

#### GET `/api/manipulatives/virtual-blocks/progress`
Kullanıcının sanal blok ilerlemesini getir.

**Response:**
```json
{
  "success": true,
  "data": {
    "total_operations": 45,
    "operations_by_type": {
      "add": 20,
      "subtract": 15,
      "multiply": 7,
      "divide": 3
    },
    "average_duration": 95,
    "accuracy_rate": 0.87
  }
}
```

### GeoGebra

#### POST `/api/manipulatives/geogebra/activity`
GeoGebra aktivitesini kaydet.

**Request Body:**
```json
{
  "user_id": 123,
  "applet_id": "geometry-basic",
  "activity_type": "geometry",
  "duration_seconds": 300,
  "completed": true
}
```

#### GET `/api/manipulatives/geogebra/applets`
GeoGebra applet listesini getir.

**Query Parameters:**
- `activity_type` (optional): geometry, algebra, calculus

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "geometry-basic",
      "name": "Temel Geometri",
      "type": "geometry",
      "url": "https://www.geogebra.org/geometry",
      "description": "Temel geometrik şekiller ve ölçümler"
    }
  ]
}
```

### İnteraktif Geometri

#### POST `/api/manipulatives/geometry/tool-usage`
Geometri aracı kullanımını kaydet.

**Request Body:**
```json
{
  "user_id": 123,
  "tool_type": "ruler",
  "shapes_created": [
    {"type": "line", "points": 2},
    {"type": "circle", "points": 2}
  ],
  "measurements": [
    {"type": "length", "value": 150.5}
  ],
  "duration_seconds": 180
}
```

#### GET `/api/manipulatives/geometry/tools`
Mevcut geometri araçlarını listele.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "ruler",
      "name": "Cetvel",
      "type": "measurement",
      "description": "Uzunluk ölçümü",
      "icon": "📏"
    },
    {
      "id": "compass",
      "name": "Pergel",
      "type": "construction",
      "description": "Daire çizimi",
      "icon": "📐"
    }
  ]
}
```

### Dijital Tangram

#### POST `/api/manipulatives/tangram/puzzle`
Tangram puzzle kaydını kaydet.

**Request Body:**
```json
{
  "user_id": 123,
  "puzzle_id": "tangram-square",
  "pieces_used": [
    {"id": "large-1", "type": "large-triangle", "x": 100, "y": 200, "rotation": 45}
  ],
  "completed": true,
  "attempts": 3,
  "duration_seconds": 240
}
```

#### GET `/api/manipulatives/tangram/puzzles`
Tangram puzzle listesini getir.

**Query Parameters:**
- `difficulty` (optional): easy, medium, hard

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "tangram-square",
      "name": "Kare Oluştur",
      "difficulty": "easy",
      "pieces": 7,
      "target_shape": "square",
      "description": "7 parça ile kare oluştur"
    }
  ]
}
```

#### GET `/api/manipulatives/tangram/progress`
Kullanıcının tangram ilerlemesini getir.

**Response:**
```json
{
  "success": true,
  "data": {
    "total_puzzles_attempted": 12,
    "total_puzzles_completed": 8,
    "completion_rate": 0.67,
    "average_attempts": 2.5,
    "average_duration": 180,
    "puzzles_by_difficulty": {
      "easy": {"attempted": 5, "completed": 5},
      "medium": {"attempted": 5, "completed": 3},
      "hard": {"attempted": 2, "completed": 0}
    }
  }
}
```

## Frontend Bileşenleri

### VirtualBlocks.tsx
Sanal bloklar bileşeni. Drag-and-drop ile sayı blokları kullanarak toplama, çıkarma, çarpma ve bölme işlemleri yapılabilir.

**Özellikler:**
- Base-10 blok sistemi (birler, onlar, yüzler)
- Drag-and-drop arayüzü
- Gerçek zamanlı sonuç hesaplama
- İşlem kaydetme

### GeoGebraEmbed.tsx
GeoGebra iframe entegrasyonu. Hazır GeoGebra applet'lerini kullanarak dinamik matematik çalışmaları yapılabilir.

**Özellikler:**
- Hazır applet listesi
- Iframe embed
- Aktivite takibi
- Tamamlama kaydı

### InteractiveGeometry.tsx
İnteraktif geometri çizim araçları. Canvas tabanlı geometrik şekil çizimi ve ölçüm araçları.

**Özellikler:**
- Çizim araçları (doğru, daire, dikdörtgen)
- Ölçüm araçları (cetvel, açıölçer)
- Dönüşüm araçları (döndürme, yansıma, öteleme)
- Grid sistemi

### DigitalTangram.tsx
Dijital tangram puzzle oyunu. 7 geometrik parça ile çeşitli şekiller oluşturma.

**Özellikler:**
- 7 tangram parçası (2 büyük üçgen, 1 orta üçgen, 2 küçük üçgen, 1 kare, 1 paralelkenar)
- Drag-and-drop parça yerleştirme
- Parça döndürme (45° artışlarla)
- Puzzle kontrol sistemi
- İlerleme takibi

### index.tsx
Ana manipülatifler sayfası. Tüm manipülatif araçları tab menüsü ile erişilebilir.

## Kullanım

### Backend
```python
# main.py'de router eklendi
from api.manipulatives_api import router as manipulatives_router
app.include_router(manipulatives_router)
```

### Frontend
```tsx
import Manipulatives from './components/Manipulatives';

function App() {
  return <Manipulatives />;
}
```

## Diskalkuli Desteği

Bu araçlar, matematik öğrenme güçlüğü (diskalkuli) olan öğrenciler için özel olarak tasarlanmıştır:

1. **Görsel Temsil**: Sayılar ve işlemler görsel bloklar ile temsil edilir
2. **İnteraktif Öğrenme**: Dokunarak ve sürükleyerek öğrenme
3. **Adım Adım İlerleme**: Basit işlemlerden karmaşık işlemlere geçiş
4. **Anında Geri Bildirim**: Her işlem sonrası görsel geri bildirim
5. **Uzamsal Akıl Yürütme**: Tangram ile şekil tanıma ve uzamsal düşünme geliştirme

## Test

```bash
# Backend test
pytest backend/tests/test_manipulatives_api.py

# Frontend test
npm test -- Manipulatives
```

## Geliştirme Notları

- Tüm API endpoint'leri authentication gerektirir
- İlerleme verileri şu an in-memory, veritabanı entegrasyonu eklenecek
- GeoGebra applet'leri resmi GeoGebra URL'lerini kullanır
- Canvas çizim performansı için requestAnimationFrame kullanılabilir
- Tangram puzzle kontrol algoritması geliştirilebilir (şu an basit bounding box kontrolü)

## İlgili Dosyalar

- `backend/api/manipulatives_api.py` - API endpoint'leri
- `frontend/src/components/Manipulatives/VirtualBlocks.tsx` - Sanal bloklar
- `frontend/src/components/Manipulatives/GeoGebraEmbed.tsx` - GeoGebra
- `frontend/src/components/Manipulatives/InteractiveGeometry.tsx` - Geometri
- `frontend/src/components/Manipulatives/DigitalTangram.tsx` - Tangram
- `frontend/src/components/Manipulatives/index.tsx` - Ana sayfa
