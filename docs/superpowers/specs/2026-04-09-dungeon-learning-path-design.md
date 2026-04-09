# Dungeon Learning Path - Design Spec

**Tarih:** 2026-04-09
**Durum:** Draft
**Faz:** 1 (MVP Dungeon Haritasi)
**Tahmini Sure:** 4 hafta

---

## 1. Vizyon

Mevcut learning path visualizer'i (ModernLearningPathVisualizer) RPG dungeon temasina donusturuyoruz. Ogrenci YKS konularini bir zindan haritasinda "odalar" olarak gorecek, her oda bir konu (topic_hierarchy row). Sis (fog of war), el-cizimi (Rough.js) gorunum, organik yollar ve theta/ilerlemeye bagli oda evrimi ile oyunlastirilmis bir ogrenme deneyimi sunuyoruz.

### Temel Kararlar
- **Tema:** RPG Dungeon (zindan haritasi)
- **Gorunum:** Hand-drawn / Sketchy (Rough.js + parchment texture)
- **Odalar:** 4 seviye gorsel evrim (theta + ilerlemeye bagli)
- **Sis:** Theta x DAG derinligine bagli yogunluk
- **Yollar:** Organik Bezier egrileri + Rough.js sketch efekti
- **Konular:** 9 YKS dersi (matematik, fizik, kimya, biyoloji, turkce, tarih, geometri, cografya, edebiyat)
- **Yaklasim:** Top-Down — ModernLearningPathVisualizer yerinde degistirilir
- **Layout:** dagre kutuphane (Sugiyama algoritmasi)

---

## 2. Mimari

### 2.1 Frontend Bilesenleri

```
ModernLearningPathPage.tsx (MEVCUT — tab yapisini koruyor)
  |
  +-- DungeonMap (YENI — replaces ModernLearningPathVisualizer)
  |     |-- ParchmentBackground (CSS gradient + PNG noise)
  |     |-- <svg> viewport (pan/zoom: @use-gesture/react)
  |     |     |-- FogOfWar (SVG feGaussianBlur filter)
  |     |     |-- OrganicPath[] (Rough.js Bezier edges)
  |     |     +-- DungeonRoom[] (Rough.js rect/circle + ikon)
  |     +-- MiniMap (kucultulmus overview, opsiyonel Faz 1)
  |
  +-- NodeDetailsPanel (MEVCUT — oda tiklaninca acilir)
  +-- ReviewQueuePanel (MEVCUT — FSRS due kartlari)
```

### 2.2 Backend Endpoint

```
GET /api/v1/dungeon/{subject}
Authorization: Required (cookie/bearer)

Response: DungeonMapResponse {
  subject: str
  theta: float
  theta_se: float
  rooms: DungeonRoom[] {
    topic_id: str (UUID)
    code: str
    name: str
    parent_subject: str
    prereqs_met: bool
    progress: DungeonProgressData {
      attempt_count: int
      best_score: int
      last_score: int
      completed: bool
    }
    question_count: int  // question_bank'tan
  }
  edges: DungeonEdge[] {
    from_topic: str (UUID)
    to_topic: str (UUID)
    prereq_type: str ("hard" | "soft")
  }
}
```

### 2.3 Yeni Hook

```typescript
// useDungeonMap.ts
// - /dungeon/{subject} fetch
// - dagre layout hesaplama (useMemo)
// - Room tiklandiginda NodeDetailsPanel'e bildirim
// - Mevcut useLearningPath hook'u ile es zamanli (refetch pattern)
```

### 2.4 Veri Akisi

```
1. Kullanici ders secer (9 tab veya selector)
2. DungeonMap mount → useDungeonMap fetch /dungeon/{subject}
3. Backend: topic_hierarchy + topic_prerequisites + dungeon_progress + user_theta + question_bank COUNT
4. Frontend: dagre layout → SVG render → Rough.js sketch
5. Oda tik → NodeDetailsPanel (quiz baslat, video, kaynaklar)
6. Quiz tamamla → dungeon_progress UPSERT → refetch → oda evrimi
```

---

## 3. DungeonRoom Sistemi

### 3.1 Oda Seviyeleri

| Seviye | Kosul | Gorunum | Ikon |
|--------|-------|---------|------|
| 0 - Harap | attempt_count = 0 | Yikilmis duvarlar, gri ton | Kilit |
| 1 - Normal | 1+ deneme, best_score < 50 | Standart tas duvarlar | Kalkan |
| 2 - Gorkemli | best_score >= 50 | Isiltili duvarlar, altin cerceve | Yildiz |
| 3 - Efsanevi | completed = true (5+ deneme, best >= 80) | Parlayan portal, partikuller | Tac |

### 3.2 Rough.js Render

```typescript
const rc = rough.svg(svgElement);
// Seviye 0: roughness=3, strokeWidth=1, stroke="#666"
// Seviye 1: roughness=2, strokeWidth=2, stroke="#8B7355"
// Seviye 2: roughness=1, strokeWidth=2, stroke="#DAA520", fill="rgba(255,215,0,0.1)"
// Seviye 3: roughness=0.5, strokeWidth=3, stroke="#FFD700", fill="rgba(255,215,0,0.2)"
```

### 3.3 Gecis Animasyonu

AnimatePresence ile opacity crossfade (0.3s):

```tsx
<AnimatePresence mode="wait">
  <motion.g
    key={`room-${topic.id}-${level}`}
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    exit={{ opacity: 0 }}
    transition={{ duration: 0.3 }}
  >
    {/* Rough.js room SVG */}
  </motion.g>
</AnimatePresence>
```

---

## 4. OrganicPath + Layout + Pan/Zoom

### 4.1 dagre Layout

```typescript
import dagre from 'dagre';

const g = new dagre.graphlib.Graph();
g.setGraph({ rankdir: 'TB', ranksep: 120, nodesep: 80 });

rooms.forEach(r => g.setNode(r.topic_id, { width: 100, height: 80 }));
edges.forEach(e => g.setEdge(e.from_topic, e.to_topic));

dagre.layout(g);
// Her node: g.node(id).x, g.node(id).y
```

### 4.2 Rough.js Sketch Paths

```typescript
edges.forEach(edge => {
  const from = g.node(edge.from_topic);
  const to = g.node(edge.to_topic);
  // Control points icin hafif rastgele offset
  const cx = (from.x + to.x) / 2 + (Math.random() - 0.5) * 30;
  const cy = (from.y + to.y) / 2;
  rc.path(`M ${from.x} ${from.y} Q ${cx} ${cy} ${to.x} ${to.y}`, {
    roughness: 1.5,
    stroke: edge.prereq_type === 'hard' ? '#8B4513' : '#A0A0A0',
    strokeWidth: edge.prereq_type === 'hard' ? 2 : 1,
  });
});
```

### 4.3 Pan/Zoom

```typescript
import { useGesture } from '@use-gesture/react';

const [transform, setTransform] = useState({ x: 0, y: 0, scale: 1 });

const bind = useGesture({
  onDrag: ({ delta: [dx, dy] }) => {
    setTransform(t => ({ ...t, x: t.x + dx, y: t.y + dy }));
  },
  onPinch: ({ offset: [scale] }) => {
    setTransform(t => ({ ...t, scale: Math.max(0.3, Math.min(3, scale)) }));
  },
});

// <svg {...bind()} style={{ transform: `translate(${x}px,${y}px) scale(${scale})` }}>
```

---

## 5. Fog of War

### 5.1 Fog Yogunlugu

```typescript
function fogOpacity(room: DungeonRoom, theta: number, dagDepth: number): number {
  // prereqs_met = false → tam sis
  if (!room.prereqs_met) return 0.9;

  // Theta-based: dusuk theta → daha fazla sis
  const thetaFactor = Math.max(0, Math.min(1, (theta + 3) / 6)); // [-3,3] → [0,1]
  
  // DAG depth: derin konular daha sisli
  const depthFactor = Math.max(0, 1 - dagDepth * 0.15);
  
  // Tamamlanmis oda → sis yok
  if (room.progress.completed) return 0;
  
  return Math.max(0, 0.7 - thetaFactor * 0.4 - depthFactor * 0.2);
}
```

### 5.2 SVG Filter

```xml
<defs>
  <filter id="fog">
    <feGaussianBlur stdDeviation="4" />
    <feColorMatrix type="matrix"
      values="0.3 0 0 0 0.2
              0 0.3 0 0 0.2
              0 0 0.3 0 0.25
              0 0 0 1 0" />
  </filter>
</defs>

<!-- Her oda icin: -->
<g filter={fogOpacity > 0.1 ? "url(#fog)" : undefined}
   opacity={1 - fogOpacity}>
  {/* DungeonRoom */}
</g>
```

---

## 6. Backend Detaylari

### 6.1 Yeni Tablo: dungeon_progress

```sql
CREATE TABLE dungeon_progress (
    user_id       TEXT        NOT NULL REFERENCES users(id),
    topic_id      TEXT        NOT NULL REFERENCES topic_hierarchy(id),
    attempt_count INTEGER     NOT NULL DEFAULT 0,
    best_score    INTEGER     NOT NULL DEFAULT 0,
    last_score    INTEGER     NOT NULL DEFAULT 0,
    completed     BOOLEAN     NOT NULL DEFAULT FALSE,
    first_attempt TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_attempt  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, topic_id)
);

CREATE INDEX idx_dungeon_progress_user ON dungeon_progress (user_id);
```

**Onemli:** `user_id` auth'tan (current_user.id), URL/query parametresinden DEGIL.

### 6.2 Quiz Tamamlama UPSERT

```sql
INSERT INTO dungeon_progress (user_id, topic_id, attempt_count, best_score, last_score, completed)
VALUES (:uid, :tid, 1, :score, :score,
        CASE WHEN 1 >= 5 AND :score >= 80 THEN TRUE ELSE FALSE END)
ON CONFLICT (user_id, topic_id) DO UPDATE SET
    attempt_count = dungeon_progress.attempt_count + 1,
    best_score = GREATEST(dungeon_progress.best_score, EXCLUDED.best_score),
    last_score = EXCLUDED.last_score,
    completed = CASE
        WHEN dungeon_progress.attempt_count + 1 >= 5
             AND GREATEST(dungeon_progress.best_score, EXCLUDED.best_score) >= 80
        THEN TRUE ELSE dungeon_progress.completed END,
    last_attempt = NOW();
```

### 6.3 SUBJECT_ALIASES

```python
SUBJECT_ALIASES = {
    "FEN": "FIZIK",
    "SOSYAL": "TARIH",
    "GENEL": "TURKCE",
}

# Endpoint'te: subject_area IN (:subject, *aliases_for(subject))
```

### 6.4 Endpoint Dosyasi

`backend/app/api/learning_path_dungeon.py`:
- `GET /dungeon/{subject}` — harita + progress + edges
- `POST /dungeon/{subject}/complete` — quiz tamamlama (score UPSERT)
- Her ikisinde `Depends(get_current_user)` + `Depends(get_db)` zorunlu

### 6.5 Migration

`backend/alembic/versions/20260410_create_dungeon_progress.py`:
- revision: `dungeon_progress_001`
- down_revision: `user_item_fsrs_001`
- `CREATE TABLE IF NOT EXISTS dungeon_progress (...)`
- downgrade: `DROP TABLE IF EXISTS dungeon_progress`

---

## 7. Seed Data

### 7.1 Topic Hierarchy Seed

`backend/scripts/seed_dungeon_topics.py`:
- 88 yeni topic (her derste 8-12 alt konu)
- `ON CONFLICT (code) DO UPDATE` — idempotent (UNIQUE constraint dogrulandi)
- Tum 10 NOT NULL kolon doldurulacak
- parent_id = NULL (DAG-only, tree hierarchy yok)
- subject_area = UPPERCASE

### 7.2 Ornek Konu Yapisi (Matematik)

```
MATEMATIK (ust konu)
  ├── MAT-SAYI-BASAMAK (Sayi Basamak Degeri)
  ├── MAT-BOLUNEBILME (Bolunebilme Kurallari)
  ├── MAT-ASAL-SAYI (Asal Sayilar)
  ├── MAT-OBEB-OKEK (OBEB-OKEK)
  ├── MAT-MUTLAK-DEGER (Mutlak Deger)
  ├── MAT-USLU-SAYILAR (Uslu Sayilar)
  ├── MAT-KOKLU-SAYILAR (Koklu Sayilar)
  ├── MAT-CARPANLARA-AYIRMA (Carpanlara Ayirma)
  ├── MAT-ESITSIZLIK (Esitsizlik)
  └── MAT-FONKSIYON (Fonksiyonlar)
```

### 7.3 Prerequisite Ornek

```
MAT-ASAL-SAYI → MAT-BOLUNEBILME (hard)
MAT-OBEB-OKEK → MAT-ASAL-SAYI (hard)
MAT-KOKLU-SAYILAR → MAT-USLU-SAYILAR (hard)
MAT-CARPANLARA-AYIRMA → MAT-OBEB-OKEK (soft)
```

---

## 8. Haftalik Plan

### Hafta 1: Backend + Seed
- [ ] `dungeon_progress` migration + ORM model
- [ ] `/dungeon/{subject}` endpoint (GET + POST)
- [ ] `seed_dungeon_topics.py` (88 topic + 60 prereq)
- [ ] Backend testleri (endpoint + seed)
- [ ] `loader.py` router kaydı

### Hafta 2: DungeonMap + dagre
- [ ] `useDungeonMap` hook (fetch + dagre layout + memo)
- [ ] `DungeonMap` component (SVG viewport)
- [ ] `ParchmentBackground` (CSS gradient)
- [ ] Pan/zoom (@use-gesture/react)
- [ ] ModernLearningPathVisualizer → DungeonMap switch

### Hafta 3: Room + Path + Fog
- [ ] `DungeonRoom` component (4 seviye Rough.js)
- [ ] `OrganicPath` component (Bezier + Rough.js)
- [ ] `FogOfWar` component (SVG filter)
- [ ] AnimatePresence geçiş animasyonu
- [ ] NodeDetailsPanel entegrasyonu (oda tik → detay)

### Hafta 4: Polish + Test
- [ ] Quiz complete → dungeon_progress update → refetch → oda evrimi
- [ ] MiniMap (opsiyonel)
- [ ] Responsive (mobile pan/zoom test)
- [ ] Performance profiling (88 node render < 100ms)
- [ ] Frontend testleri (vitest)
- [ ] E2E test (login → ders sec → oda tik → quiz → evrim)

---

## 9. Test Stratejisi

### Backend
- `test_dungeon_endpoint.py`: GET harita, POST complete, auth zorunlulugu, SUBJECT_ALIASES
- `test_dungeon_progress_model.py`: UPSERT, completed threshold, FK constraint
- `test_seed_dungeon_topics.py`: idempotent seed, 88 topic, 60 prereq

### Frontend
- `DungeonMap.test.tsx`: render, room count, edge count
- `DungeonRoom.test.tsx`: 4 seviye gorsel (snapshot)
- `useDungeonMap.test.ts`: fetch mock, dagre layout ciktisi
- `FogOfWar.test.tsx`: opacity hesaplama (completed=0, prereqs_met=false, derin konu)

### E2E
- Login → Matematik sec → DungeonMap render → Oda tik → Quiz baslat → Tamamla → Oda evrimi

---

## 10. Performans Hedefleri

| Metrik | Hedef | Yontem |
|--------|-------|--------|
| Endpoint response | < 200ms | Single query + JOIN |
| dagre layout (88 node) | < 50ms | useMemo, yeniden hesaplama yok |
| Rough.js render (88 room) | < 100ms | Lazy render (viewport icindekiler) |
| SVG pan/zoom | 60fps | CSS transform, SVG reflow yok |
| Bundle artisi | < 60KB gzip | Rough.js 40KB + gesture 15KB |

---

## 11. Risk ve Azaltma

| Risk | Etki | Azaltma |
|------|------|---------|
| Rough.js ilk render yavas | Gorsel gecikme | Lazy load, viewport culling |
| dagre layout buyuk graf | Layout suresi | useMemo, sadece degisince |
| topic_hierarchy'de az konu | Bos harita | Seed 88 topic, fallback mesaj |
| question_bank topic eslesmesi dusuk | Odada soru yok | question_count goster, 0 ise uyari |
| Mobile pinch/zoom | Kotu UX | @use-gesture test, min/max scale |

---

## 12. Kapsam Disi (Faz 2+)

- Boss fight mekanigi
- Loot/odül sistemi
- Multiplayer dungeon
- 3D gorunum
- Ses efektleri
- Dungeon tema secimi (buz, volkan vb.)
- Achievement/rozet entegrasyonu
- Leaderboard dungeon siralaması

---

## Referanslar

- topic_hierarchy: 72 mevcut topic (DB dogrulandi)
- topic_prerequisites: 90 satir, 68 hard + 22 soft (DB dogrulandi)
- user_theta: UPPERCASE subject_area (DB dogrulandi)
- question_bank: 77,336 soru, primary_topic_id UUID (DB dogrulandi)
- code: UNIQUE constraint (DB dogrulandi)
- parent_id: tumu NULL (DB dogrulandi)
- dagre: https://github.com/dagrejs/dagre
- Rough.js: https://roughjs.com/
- @use-gesture/react: https://use-gesture.netlify.app/
