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
    name_tr: str
    parent_subject: str
    prereqs_met: bool
    dag_depth: int          // topological sort index (fog hesabi icin)
    progress: DungeonProgressData {
      attempt_count: int
      best_score: int
      last_score: int
      completed: bool
    }
    question_count: int     // question_bank'tan (direkt + root fallback)
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

**React entegrasyon:** Rough.js imperatif DOM API kullanir. Her OrganicPath ve DungeonRoom
icin `useRef<SVGGElement>` + `useEffect` pattern'i ile entegre edilir:

```typescript
const pathRef = useRef<SVGGElement>(null);

useEffect(() => {
  if (!pathRef.current) return;
  const rc = rough.svg(pathRef.current.ownerSVGElement!);
  pathRef.current.innerHTML = ''; // onceki cizimi temizle
  
  const from = g.node(edge.from_topic);
  const to = g.node(edge.to_topic);
  
  // Seeded random — edge ID'den deterministik offset (re-render'da titreme onlenir)
  const seed = hashCode(`${edge.from_topic}-${edge.to_topic}`);
  const pseudoRandom = (Math.sin(seed * 9301 + 49297) % 233280) / 233280;
  const cx = (from.x + to.x) / 2 + (pseudoRandom - 0.5) * 30;
  const cy = (from.y + to.y) / 2;

  const pathNode = rc.path(`M ${from.x} ${from.y} Q ${cx} ${cy} ${to.x} ${to.y}`, {
    roughness: 1.5,
    stroke: edge.prereq_type === 'hard' ? '#8B4513' : '#A0A0A0',
    strokeWidth: edge.prereq_type === 'hard' ? 2 : 1,
  });
  pathRef.current.appendChild(pathNode);
}, [edge, g]);

// JSX: <g ref={pathRef} />
```

Ayni pattern DungeonRoom icin de gecerli: `useRef` + `useEffect` + `rc.rectangle()`.

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
function fogOpacity(room: DungeonRoom, theta: number): number {
  // prereqs_met = false → tam sis
  if (!room.prereqs_met) return 0.9;

  // Tamamlanmis oda → sis yok
  if (room.progress.completed) return 0;

  // Theta-based: dusuk theta → daha fazla sis
  const thetaFactor = Math.max(0, Math.min(1, (theta + 3) / 6)); // [-3,3] → [0,1]
  
  // DAG depth: backend'den gelen dag_depth (topological sort index)
  // depth=0 (kok konu) → depthFactor=1.0, depth=7+ → depthFactor=0
  const depthFactor = Math.max(0, 1 - room.dag_depth * 0.15);
  
  return Math.max(0, 0.7 - thetaFactor * 0.4 - depthFactor * 0.2);
}
```

`dag_depth` backend'de hesaplanir: Kahn's topolojik siralama sirasinda her topic'in
indeksi kaydedilir ve response'a eklenir. Frontend bu degeri dogrudan kullanir.

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
    user_id       VARCHAR     NOT NULL REFERENCES users(id),
    topic_id      VARCHAR     NOT NULL REFERENCES topic_hierarchy(id),
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

**Not:** `users.id` ve `topic_hierarchy.id` ikisi de `character varying` (VARCHAR).
FK uyumlulugu icin ayni tip kullanilir.

**Onemli:** `user_id` auth'tan (current_user.id), URL/query parametresinden DEGIL.

ORM model'de `String` (VARCHAR) kullanilir (`Text` degil):
```python
class DungeonProgress(Base):
    __tablename__ = "dungeon_progress"
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    topic_id = Column(String, ForeignKey("topic_hierarchy.id"), primary_key=True)
    # ... diger kolonlar
```

### 6.2 Quiz Tamamlama UPSERT

```sql
INSERT INTO dungeon_progress (user_id, topic_id, attempt_count, best_score, last_score, completed)
VALUES (:uid, :tid, 1, :score, :score, FALSE)
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

### 6.3 Topic Filtreleme

Endpoint subject parametresine gore topic_hierarchy'den filtreleme:

```python
# Direkt subject_area eslemesi
# Ornek: subject="MATEMATIK" → MAT.FON, MAT.SAY, MAT.TRG, ... (21 topic)
# Ornek: subject="FIZIK" → TYT-FIZ-01, TYT-FIZ-02, ... (4 topic)

# Code-prefix fallback: subject_area NULL olan ama code prefix'i uyan topic'ler
# Ornek: MAT.xxx topic'lerinin subject_area'si NULL ama MATEMATIK dungeon'unda gosterilmeli
CODE_PREFIX_MAP = {
    "MATEMATIK": "MAT.",
    "GEOMETRI": "GEO",
    "FIZIK": "FIZ",
    "KIMYA": "KIM",
    "BIYOLOJI": "BIY",
    "TURKCE": "TUR",
    "TARIH": "TAR",
    "COGRAFYA": "COG",
    "EDEBIYAT": "EDU",
}

# WHERE subject_area = :subject
#    OR (subject_area IS NULL AND code LIKE :prefix || '%')
# Root topic'ler (MAT, FIZ, TUR — code'da '.' yok) haric tutulur (bunlar oda degil, kategori)
# AND code LIKE '%__%'  -- en az 2+ karakter (root'lari disla)
```

**Not:** FEN (5 topic, karisik fen bilimleri) ve SOSYAL (5 topic) ayri dungeon olarak
gosterilebilir veya Faz 1'de scope disinda birakilabilir. 9 YKS dersi zaten yeterli.

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

## 7. Mevcut Veri + Seed Stratejisi

### 7.1 Mevcut Durum (DB Dogrulandi 2026-04-09)

| Ders | Mevcut Topic | Soru (alt konu) | Soru (root) | Prereq Edge |
|------|-------------|-----------------|-------------|-------------|
| MATEMATIK | 21 (MAT.xxx) | 8,005 | 8,453 | 21 |
| GEOMETRI | 5 (GEO0x) | 0 | 9,494 | 5 |
| FIZIK | 4 (TYT-FIZ) | 6 | 6,538 | 4 |
| KIMYA | 4 (TYT-KIM) | 6 | 6,045 | 4 |
| TURKCE | 3 (TYT-TR) | 5 | 10,846 | 2 |
| EDEBIYAT | 5 (EDU0x) | 0 | 3,688 | 5 |
| TARIH | 7 (TAR/TYT-TAR) | 1 | 2,366 | 7 |
| COGRAFYA | 7 (COG/TYT-COG) | 3 | 396 | 5 |
| BIYOLOJI | 2 (TYT-BIY) | 5 | 2,518 | 1 |
| **Toplam** | **58 (root haric)** | **8,031** | **50,344** | **54** |

**Kritik bulgu:** Matematik zengin (21 alt konu, 8K soru, 21 edge). Diger derslerin cogu
sorusu ROOT topic'te — alt konulara henuz dagitilmamis.

### 7.2 Strateji: Hibrit (Mevcut + Yeni)

**Adim 1 — subject_area UPDATE (34 NULL topic):**
MAT.xxx topic'lerinin subject_area'si NULL. Dungeon'da filtrelenebilmesi icin:
```sql
UPDATE topic_hierarchy SET subject_area = 'MATEMATIK' WHERE code LIKE 'MAT.%';
-- Ayni sekilde diger prefix'ler icin (gerekirse)
```

**Adim 2 — Eksik alt konu seed (az topic olan dersler):**
`backend/scripts/seed_dungeon_topics.py`:
- Turkce: +5 topic (TUR.PAR, TUR.ANL, TUR.YAZ, TUR.DIL, TUR.SOZ)
- Biyoloji: +6 topic (BIY.HUC, BIY.GEN, BIY.EKO, BIY.SIS, BIY.EVR, BIY.BIT)
- Fizik: +4 topic (FIZ.OPT, FIZ.ELE, FIZ.MAG, FIZ.MOD)
- Kimya: +4 topic (KIM.ORG, KIM.ASI, KIM.DEN, KIM.TER)
- **Toplam: ~19 yeni topic** (88 degil!)
- `ON CONFLICT (code) DO UPDATE` — idempotent
- Tum 18 kolon (10 NOT NULL + 8 nullable) doldurulacak
- subject_area = UPPERCASE

**Adim 3 — Yeni prerequisite edge'ler (yeni topic'ler icin):**
- Her yeni ders icin 3-5 hard + 1-2 soft edge
- **Toplam: ~25 yeni edge**

### 7.3 Mevcut Matematik DAG (kullanima hazir)

```
MAT.SAY (Sayilar) ──hard──> MAT.USL (Uslu Sayilar) ──hard──> MAT.LOG (Logaritma)
    |                           |                                    
    ├──hard──> MAT.MTL          ├──hard──> MAT.CRP ──hard──> MAT.POL
    ├──hard──> MAT.OLS          |                               |
    └──hard──> MAT.PRB          └──soft──> MAT.TRG              └──hard──> MAT.DNK
                                    |                               |
                                    └──hard──> MAT.LMT             ├──hard──> MAT.FON
                                        |                           └──hard──> MAT.EST
                                        └──hard──> MAT.TRV
                                            |
                                            └──hard──> MAT.INT
```

21 topic, 21 edge — dungeon haritasi icin hazir.

### 7.4 Bilinen Kisitlama: Soru Dagitimi

Matematik disindaki derslerde sorularin cogu root topic'te (FIZ=6538, TUR=10846).
Alt konulara dagitim **Faz 2** kapsaminda NLP-based topic classification ile yapilacak.

**Faz 1 fallback:** `question_count` hesaplanirken:
1. Once alt konu'ya direkt eslesen soruları say
2. 0 ise, root topic soru sayisini ders topic sayisina bol (tahmini goster)
3. Quiz baslatildiginda: root topic'ten rastgele soru cek

```python
# question_count fallback
direct_count = count(question_bank WHERE primary_topic_id = topic.id)
if direct_count > 0:
    return direct_count
# Root topic fallback: FIZ root'ta 6538 soru, 4+4=8 alt konu → ~817/topic
root_count = count(question_bank WHERE primary_topic_id = root_topic.id)
sibling_count = count(topics in same subject)
return root_count // sibling_count if sibling_count > 0 else 0
```

---

## 8. Haftalik Plan

### Hafta 1: Backend + Seed
- [ ] `dungeon_progress` migration + ORM model
- [ ] `/dungeon/{subject}` endpoint (GET + POST) — dag_depth hesaplama dahil
- [ ] `seed_dungeon_topics.py` (~19 yeni topic + subject_area UPDATE + ~25 prereq)
- [ ] question_count fallback logic (direkt + root bolme)
- [ ] Backend testleri (endpoint + seed)
- [ ] `loader.py` router kaydı

### Hafta 2: DungeonMap + dagre + Placeholder Room
- [ ] `useDungeonMap` hook (fetch + dagre layout + memo)
- [ ] `DungeonMap` component (SVG viewport)
- [ ] `ParchmentBackground` (CSS gradient)
- [ ] Pan/zoom (@use-gesture/react)
- [ ] **Placeholder DungeonRoom** (basit rect + text, Rough.js OLMADAN)
- [ ] ModernLearningPathVisualizer → DungeonMap switch
- [ ] Hafta sonu: dagre layout + pan/zoom + placeholder room calisir halde

### Hafta 3: Rough.js Room + Path + Fog
- [ ] `DungeonRoom` component (4 seviye Rough.js — useRef+useEffect pattern)
- [ ] `OrganicPath` component (seeded random Bezier + Rough.js)
- [ ] `FogOfWar` component (SVG filter)
- [ ] AnimatePresence gecis animasyonu
- [ ] NodeDetailsPanel entegrasyonu (oda tik → detay)

### Hafta 4: Polish + Test
- [ ] Quiz complete → dungeon_progress update → refetch → oda evrimi
- [ ] MiniMap (opsiyonel)
- [ ] Responsive (mobile pan/zoom test)
- [ ] Performance profiling (~77 node render < 100ms)
- [ ] Frontend testleri (vitest — seeded random = deterministic snapshot)
- [ ] E2E test (login → ders sec → oda tik → quiz → evrim)

---

## 9. Test Stratejisi

### Backend
- `test_dungeon_endpoint.py`: GET harita, POST complete, auth zorunlulugu, CODE_PREFIX_MAP
- `test_dungeon_progress_model.py`: UPSERT, completed threshold, FK constraint
- `test_seed_dungeon_topics.py`: idempotent seed, ~19 yeni topic, ~25 prereq, subject_area UPDATE
- `test_question_count_fallback.py`: direkt count, root fallback, 0 case

### Frontend
- `DungeonMap.test.tsx`: render, room count, edge count
- `DungeonRoom.test.tsx`: 4 seviye gorsel (snapshot — seeded random ile deterministik)
- `useDungeonMap.test.ts`: fetch mock, dagre layout ciktisi
- `FogOfWar.test.tsx`: opacity hesaplama (completed=0, prereqs_met=false, derin konu)

### E2E
- Login → Matematik sec → DungeonMap render → Oda tik → Quiz baslat → Tamamla → Oda evrimi

---

## 10. Performans Hedefleri

| Metrik | Hedef | Yontem |
|--------|-------|--------|
| Endpoint response | < 200ms | Single query + JOIN |
| dagre layout (~77 node max) | < 50ms | useMemo, yeniden hesaplama yok |
| Rough.js render (~77 room max) | < 100ms | Lazy render (viewport icindekiler) |
| SVG pan/zoom | 60fps | CSS transform, SVG reflow yok |
| Bundle artisi | < 60KB gzip | Rough.js 40KB + gesture 15KB |

---

## 11. Risk ve Azaltma

| Risk | Etki | Azaltma |
|------|------|---------|
| Rough.js ilk render yavas | Gorsel gecikme | Lazy load, viewport culling |
| Rough.js + React entegrasyon | Imperatif/declaratif cakisma | useRef+useEffect pattern, clear on update |
| dagre layout buyuk graf | Layout suresi | useMemo, sadece degisince |
| Sorular root topic'te yigilmis | Alt konuda soru yok | Root fallback: count / sibling sayisi |
| Az topic olan dersler (TUR=3, BIY=2) | Bos dungeon | Seed ~19 yeni topic |
| Mobile pinch/zoom | Kotu UX | @use-gesture test, min/max scale |
| dagre TypeScript types eksik | Build hatasi | @types/dagre veya manual .d.ts |

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

### DB Dogrulamalari (2026-04-09)
- topic_hierarchy: 72 mevcut topic (34 NULL subject_area, 38 set)
- topic_hierarchy kolonlari: 18 kolon, id=VARCHAR, name_tr (name degil!)
- topic_prerequisites: 90 satir, 68 hard + 22 soft
- MAT.xxx: 21 alt konu, 8,005 soru, 21 prereq edge — dungeon'a hazir
- Diger dersler: Sorularin cogu root topic'te (FIZ=6538, TUR=10846 root'ta)
- user_theta: UPPERCASE subject_area
- question_bank: 77,336 soru, primary_topic_id VARCHAR (UUID format)
- code: UNIQUE constraint
- parent_id: tumu NULL
- users.id: VARCHAR (character varying)

### Kutuphaneler
- dagre: https://github.com/dagrejs/dagre
- Rough.js: https://roughjs.com/
- @use-gesture/react: https://use-gesture.netlify.app/
