# B3 — Konu kırılımı ders bazından konu bazına iner

> **Tarih:** 21 Ağustos 2026 · **Kabul kriteri:** A1 dördüncü ayağı
> ("netini ve **konu kırılımını** görür") · **Dal:** `feature/self-evolution-optimization`

## 1. Sorun (ölçüldü, iddia değil)

`core/osym_exam_engine.py:1364` konu kırılımını `question.subject_area` ile grupluyor.
`subject_area` ders düzeyinde bir alan ("MATEMATIK"), konu düzeyinde değil. Sonuç: bir
sınavın **tüm** soruları tek kovaya iniyor.

Canlı ölçüm — oturum `6e3a1832-d642-4c73-aadf-b7bea8f6c4d6` (21 Ağu 2026, 40 soru):

```sql
WITH son AS (SELECT id FROM exam_sessions ORDER BY created_at DESC LIMIT 1)
SELECT qm.subject_area AS ders, th.code AS konu_kodu, th.name_tr, count(*) AS soru
FROM exam_questions eq
JOIN question_bank qb ON qb.id = eq.question_id
JOIN question_metadata qm ON qm.id = qb.id
LEFT JOIN topic_hierarchy th ON th.id = qb.primary_topic_id
WHERE eq.exam_session_id = (SELECT id FROM son)
GROUP BY 1,2,3 ORDER BY 4 DESC;
```

| ders | konu_kodu | name_tr | soru |
|---|---|---|---|
| MATEMATIK | MAT.FON | Fonksiyonlar | 7 |
| MATEMATIK | MAT.CRP | Çarpanlara Ayırma | 5 |
| MATEMATIK | MAT.KMB | Kombinasyon | 4 |
| MATEMATIK | MAT.POL | Polinomlar | 4 |
| MATEMATIK | MAT.PRM | Permütasyon | 3 |
| MATEMATIK | MAT.PRB | Problemler | 3 |
| MATEMATIK | MAT.OLS | Olasılık | 3 |
| MATEMATIK | MAT.USL | Üslü ve Köklü Sayılar | 2 |
| MATEMATIK | MAT.DNK | Denklemler | 2 |
| MATEMATIK | MAT.EST | Eşitsizlikler | 2 |
| MATEMATIK | MAT.MTL | Mutlak Değer | 2 |
| MATEMATIK | MAT.SAY | Sayılar ve İşlemler | 2 |
| MATEMATIK | MAT.GEO | Geometri | 1 |

**13 gerçek konu kodu var. Motor 1 satır döndürüyor.** Veri kayıp değil — motor atıyor.

Yüzeydeki sonuç: `frontend/src/pages/ModernExamResultsPage.tsx:400` tablosunun başlığı
"Konu" ama içeriği ders — öğrenci **tek satır** görüyor.

### Bu bir fantom değil — kontrol kolu

| Kontrol | Sonuç |
|---|---|
| `question_bank` aktif satır / `primary_topic_id` dolu | 3.922 / **3.922** (%100) |
| Kapıdaki (`mv_safe_for_beta`) MAT dilimi | 351 soru / **14** farklı konu |
| Kapıdaki KIMYA dilimi | 3.209 soru / **12** farklı konu |
| `topic_hierarchy` level-2 (konu) satırı | 25, `code` + `name_tr` dolu |

## 2. Kapsam

Uçtan uca: motor → API sözleşmesi → frontend → **canlı kabul ölçümü**. Yalnız backend
yeterli değil: A1'in dördüncü ayağı öğrenci ekranda konuyu görene kadar kapanmaz
(CLAUDE.md E3 — oturum başına en az 1 kullanıcı-görünür çıktı).

## 3. Tasarım

### 3.1 Sözleşme: EKLEMELİ (alan silinmez)

`subject` alanı **anlamını korur** (ders). İki alan eklenir:

```python
@dataclass
class SubjectPerformance:
    subject: str
    total_questions: int
    correct_answers: int
    wrong_answers: int
    empty_answers: int
    success_rate: float
    average_response_time: float
    difficulty_level: float
    topic_code: str | None = None     # YENİ — sona, varsayılanlı
    topic_name: str | None = None     # YENİ — sona, varsayılanlı
```

**Alanlar neden SONA ve varsayılanlı:** `backend/tests/unit/test_sinav_api.py:1118-1119`
dataclass'ı **pozisyonel** çağırıyor:

```python
SubjectPerformance("MATEMATIK", 40, 28, 10, 2, 70.0, 65.5, 0.8)
```

Başa veya ortaya eklenen alan bu çağrıları **sessizce** yanlış alana bağlar — `TypeError`
bile vermez, `topic_code` konumuna `40` gider. Sona + varsayılanlı ekleme bu sınıfı
yapısal olarak imkânsız kılar.

`SubjectPerformanceResponse` (`api/sinav.py:246`) aynı iki alanı `str | None = None`
olarak alır.

### 3.2 Motor sorgusu

Gruplama anahtarı `subject` → `(subject, primary_topic_id)`.

```python
select(
    Question,
    StudentAnswer,
    TopicHierarchy.code,
    TopicHierarchy.name_tr,
)
.options(
    selectinload(Question.content),
    selectinload(Question.metadata_info),
    selectinload(Question.statistics),
)
.join(ExamQuestion, Question.id == ExamQuestion.question_id)
.outerjoin(StudentAnswer, and_(...))
.outerjoin(TopicHierarchy, TopicHierarchy.id == Question.primary_topic_id)
.where(ExamQuestion.exam_session_id == session_id)
.order_by(ExamQuestion.question_order)
```

Neden bu şekil güvenli:

- `primary_topic_id` **`question_bank`'ın kendi kolonu** (`models/question_bank.py:166`),
  `_install_compat_delegates` devredicisi DEĞİL → sınıf düzeyinde JOIN yazılabilir,
  `AttributeError` riski yok.
- `TopicHierarchy.code` / `.name_tr` **kolon seçimi** → `Row` döner, ek eager-load
  gerekmez. S220'de ölçülen 361→4 SELECT kazancı bozulmaz (`MissingGreenlet` yolu açılmaz).
- `outerjoin`: `primary_topic_id` NULL olan satır **düşmez**.

### 3.3 Sıralama ve az-örneklem politikası

**Tüm kovalar gösterilir.** Sıra: `total_questions` azalan, eşitlikte `topic_name`
alfabetik (deterministik — testin kararlı olması için gerekli).

Az soruluk kova (1-2 soru) gizlenmez ve birleştirilmez: öğrencinin hangi konuda eksik
olduğunu görmesi, yüzdenin istatistiksel gürültüsünden daha değerli. `%0` gibi tek-soruluk
değerler tabloda kalır.

### 3.4 Konu atanmamış soru

`primary_topic_id` NULL veya `topic_hierarchy` satırı yoksa:

- `topic_code = None`
- `topic_name = "Konu atanmamış"`

Sessiz varsayılan (ders adına düşme) **yapılmaz** — o davranış borcu ölçülemez kılar
(`audit-methodology.md`, uyumluluk katmanı kör noktası kuralı). Bugün bu kova 0 satır
üretir; sızarsa **görünür** olur.

### 3.5 Frontend

`ModernExamResultsPage.tsx`:

- `subject_breakdown` öğesine `topic: string` eklenir (`:123` mapping).
- Tablo `Konu` tek sütunundan **`Ders | Konu`** iki sütuna çıkar (`:400`, `:413`).

`frontend/src/types/api.generated.ts` OpenAPI'den yeniden üretilir (elle düzenlenmez).

### 3.6 İkincil kazanç (kapsam dışı ama bedava)

`application/commands/sinav.py:830` ikinci tüketici. `zayif_konular` / `guclu_konular`
bugün `["matematik"]` üretiyor; konu bazına inince kendiliğinden
`["Fonksiyonlar", "Olasılık"]` olur. Ek kod gerekmez.

## 4. Kabul kriteri — ÖLÇÜM, beyan değil

Bu spec, aşağıdaki komut **≥5** döndürene kadar kapanmış sayılmaz:

```bash
# yeni oturum aç → 40 soru → cevapla → tamamla → kırılımı çek
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/osym-exam/$SID/subject-performance \
| python -c "import sys,json; d=json.load(sys.stdin); \
print(len({r['topic_code'] for r in d if r.get('topic_code')}))"
```

Bugünkü değer: **1**. Hedef: **≥5** (aynı oturumda DB'de 13 var).

Karşı-ölçüm (yanlış-sıfır tuzağına karşı): aynı oturum için DB'den doğrudan sayılan
farklı `topic_code` adedi, API'nin döndürdüğü adede **eşit** olmalı.

## 5. Dokunulan dosyalar

| # | Dosya | Değişiklik | Risk |
|---|---|---|---|
| 1 | `backend/core/osym_exam_engine.py` | dataclass +2 alan, sorguya `TopicHierarchy` outerjoin, gruplama anahtarı, sıralama | MED |
| 2 | `backend/api/sinav.py` | `SubjectPerformanceResponse` +2 alan, `:892` mapping | LOW |
| 3 | `frontend/src/pages/ModernExamResultsPage.tsx` | `topic` alanı + `Ders \| Konu` sütunları | LOW |
| 4 | `frontend/src/types/api.generated.ts` | OpenAPI'den yeniden üretim | LOW |
| 5 | `backend/tests/**` (3 dosya, 9 çağrı noktası) | yeni alanlar için uyumlama | LOW |
| 6 | `backend/tests/integration/test_osym_exam_engine.py` | **YENİ** konu-kırılımı testi (RED önce) | — |

## 6. Deploy döngüsü (imaj pişmiş — reload YOK)

`docker-compose.yml:43` backend'e kaynak volume mount'u **yok**. Canlı doğrulama için
CLAUDE.md kanonik döngüsü zorunlu:

```bash
docker cp backend/core/osym_exam_engine.py kiro2-backend:/app/core/osym_exam_engine.py
docker cp backend/api/sinav.py kiro2-backend:/app/api/sinav.py
docker exec kiro2-backend find /app -name "*.pyc" -delete
docker restart kiro2-backend
sleep 90          # 22 DEĞİL — 150 router, açılış 60-85 sn
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health   # 200 bekle
```

## 7. Bu spec'in kapsamadıkları

- **L2 (e-posta doğrulama)** — A1'in ikinci ayağı, ayrı iş.
- `mv_safe_for_beta` içerik kalitesi (S231 dersi) — bu spec kırılımı düzeltir, havuzu değil.
- `analytics.py` / `exam_results_reporting.py` içindeki **ayrı** `_get_subject_performance_*`
  fonksiyonları — farklı uç, farklı sözleşme, bu turda dokunulmaz.
