# KIRO2 Uçtan Uca Semantik Analiz Metodolojisi v6

**Tarih:** 2026-04-09
**Versiyon:** 6.0 (5 iterasyon sonrası final)
**Kapsam:** Backend + Frontend + Orchestrator + d-dataset + Docker/Config
**Tahmini Süre:** 9-12 saat (2-3 session)

---

## Çerçeve: Niyet ↔ Gerçekleşme Boşluk Analizi

Semantik analiz = kodun **ne yapması gerektiği** ile **gerçekte ne yaptığı** arasındaki boşlukları bulmak.

| Niyet Kaynağı | Gerçekleşme Kaynağı |
|---------------|---------------------|
| Fonksiyon/değişken adı | Fonksiyon gövdesi |
| Pydantic şema | Frontend fetch + TypeScript interface |
| CLAUDE.md mimari tanımı | Gerçek kod yapısı |
| Test assertion | Gerçek test gövdesi |
| IRT/FSRS formülü (teorik) | Algoritma implementasyonu |
| YKS kuralları (ÖSYM) | Sınav motoru kodu |
| Yorum/docstring | Altındaki kod |

---

## Ciddiyet Tanımı (KIRO2'ye Özel)

```
P0 — Kullanıcı verisini bozar veya güvenlik açığı oluşturur
  - Auth bypass / IDOR
  - Yanlış puan hesaplama (YKS kuralı ihlali)
  - Veri kaybı (silme/üzerine yazma)
  - SQL injection / XSS / SSRF
  - Yanlış tablo sorgusu (questions yerine question_bank olmalı)
  - Algoritma çıktısı matematiksel olarak imkansız değer üretir

P1 — Yanlış sonuç üretir ama veri kaybetmez
  - IRT/FSRS/ZPD parametre sınır ihlali
  - Field mismatch (backend ↔ frontend)
  - Missing is_active filtresi (devre dışı veri dönme riski)
  - Türkçe encoding bozulması (NFC/İ-I)
  - Exception yutma (hata sessizce geçiyor)
  - get_async_session yanlış kullanımı (generator ≠ context manager)

P2 — Çalışıyor ama ideal değil
  - Dead code / unused import / unused export
  - Naming tutarsızlığı
  - Eksik test coverage
  - Karmaşıklık yüksekliği
  - Config tutarsızlığı (çalışmayı bozmayan)
  - Dokümantasyon ↔ kod uyumsuzluğu
```

---

## Büyüyen Artifact: findings.md

Tüm adımların çıktısı tek dosyaya birikir. Bu dosya:
- Her adımda büyür
- Sonraki adımın agent prompt'una referans olarak verilir
- Sentez adımında ana girdi olur
- Compaction'dan etkilenmez (dosyada kalır)

**Dosya:** `docs/audits/findings.md`

**Bulgu formatı (tüm agent'lar için zorunlu):**

```markdown
| ID | Dosya:Satır | Niyet | Gerçekleşme | Ciddiyet | Güven | Agent |
```

**Güven seviyeleri:**
- **KESİN** — Statik araçla kanıtlanabilir (type error, missing import)
- **YÜKSEK** — 2+ agent aynı bulguyu doğruladı
- **ORTA** — 1 agent buldu, bağlam mantıklı
- **DÜŞÜK** — Yorum gerektiren, domain bilgisi lazım

---

## ADIM 0 — Ön Koşul ve Durdurma Kontrolü

**Süre:** 15 dk
**Soru:** "Analiz yapılabilecek durumda mıyız?"

### Kontroller

```bash
# 1. Git durumu
git status                    # uncommitted changes?
git log --oneline -3          # son commit beklenen mi?

# 2. Araç envanteri
pip list 2>/dev/null | grep -iE "vulture|radon|bandit|pydeps"

# 3. Altyapı (opsiyonel — runtime analizi yapılacaksa)
pg_isready -p 5434            # PostgreSQL
redis-cli ping                # Redis
docker ps --format "table {{.Names}}\t{{.Status}}"  # Docker

# 4. Migration ↔ Model senkronizasyonu
cd backend && python -c "from alembic.config import Config; from alembic import command; command.check(Config('alembic.ini'))" 2>&1
```

### Durdurma Koşulları

```
❌ Migration ↔ DB şeması uyuşmuyor   → DURDUR, alembic upgrade head
❌ Backend import error (circular)     → DURDUR, import düzelt
❌ 50+ uncommitted değişiklik          → DURDUR, commit veya stash
❌ Yanlış branch (master değilse)      → DURDUR, branch kontrol
```

### Çıktı

```
Durum: GO / BLOCKED (sebep)
Araçlar: [mevcut olanlar listesi]
Son commit: [hash] [mesaj]
Branch: [branch adı]
```

→ `findings.md` başlığına yaz

---

## ADIM 1 — Hedef Haritası

**Süre:** 45-60 dk
**Soru:** "Nereye bakmalıyız?"

### 3 Filtre

**Filtre A — Coverage boşluğu:**
```bash
cd backend && pytest --cov=app --cov-report=json -q --no-header 2>/dev/null
# coverage.json → %0-30 arası dosyaları çıkar
python -c "
import json
data = json.load(open('coverage.json'))
for f, info in sorted(data['files'].items(), key=lambda x: x[1]['summary']['percent_covered']):
    pct = info['summary']['percent_covered']
    if pct < 30 and '/test' not in f and '/_deprecated' not in f:
        print(f'{pct:5.1f}%  {f}')
" | head -30
```

**Filtre B — Son değişiklikler (en taze = en az test edilmiş):**
```bash
git log --oneline -30 --name-only --diff-filter=M | grep -E "\.py$|\.tsx?$" | sort | uniq -c | sort -rn | head -20
```

**Filtre C — Sorun geçmişi (MEMORY.md'den):**
```
5 session: learning_path_v2.py
4 session: unified_auth_service.py, gamification.py
3 session: osym_exam_engine.py, exam router'ları
2 session: bkt_service.py, irt_service.py, fsrs_service.py
```

### Önceliklendirme Matrisi

```
ÖNCELİK 1 (derin analiz):
  Filtre A ∩ B → coverage düşük + son değişen
  Filtre A ∩ C → coverage düşük + sorun geçmişi olan
  → Beklenen: 8-15 dosya

ÖNCELİK 2 (pattern tarama):
  Filtre A veya B (tek filtre geçen)
  → Beklenen: 10-20 dosya

ÖNCELİK 3 (atla veya son bak):
  Hiçbir filtreye girmeyen + coverage >50%
  → Analiz dışı (sağlam kabul)
```

### Frontend Hedef Haritası

```bash
# Frontend coverage (varsa)
cd frontend && npx vitest run --coverage --reporter=json 2>/dev/null

# Yoksa: son değişen component/page/hook dosyaları
git log --oneline -30 --name-only --diff-filter=M | grep -E "frontend/src" | sort | uniq -c | sort -rn | head -15
```

### Orchestrator + d-dataset

```
Orchestrator: Tüm 24 modül → Öncelik 2 (policy_engine.py, routing.py → Öncelik 1)
d-dataset: READ-ONLY veri bütünlüğü → Adım 4'te DB import tutarlılığı kontrolü
```

### Çıktı

```markdown
## Adım 1: Hedef Haritası

### Öncelik 1 (derin analiz)
| # | Dosya | Coverage | Son Değişiklik | Sorun Geçmişi |
|---|-------|----------|----------------|---------------|
| 1 | backend/app/services/xxx.py | %12 | 3 gün | 4 session |
...

### Öncelik 2 (pattern tarama)
| # | Dosya | Sebep |
...
```

→ `findings.md`'ye ekle

---

## ADIM 2 — Kalibrasyon

**Süre:** 60-90 dk
**Soru:** "Analiz yöntemimiz çalışıyor mu?"

### 2 Dosyada Test

**Dosya A (çok fixlenmiş):** `learning_path_v2.py`
- Bilinen geçmiş: IDOR, async/await, is_active, verify_student_access
- Beklenti: düzeltmeler doğrulanır + yeni sorun bulunabilir

**Dosya B (bakılmamış):** Adım 1'den coverage %0 olan bir Öncelik 1 dosya
- Beklenti: en az 2-3 anlamlı bulgu çıkar

### Her Dosyaya 3 Paralel Agent

```
Agent A (feature-dev:code-reviewer):
  "[dosya] dosyasını niyet-gerçekleşme boşluğu çerçevesinde analiz et.

   Bilinen geçmiş sorunlar (Dosya A için):
   - IDOR: user_id parametre olarak alınıyordu, artık token'dan çözülmeli
   - async/await: verify_student_access çağrılarına await eklendi
   - is_active: soru sorgularında filtre eklendi

   Kontrol et:
   1. Bilinen düzeltmeler hâlâ yerinde mi?
   2. Aynı pattern'de YENİ sorunlar var mı?
   3. Fonksiyon adlarının söylediği ile yaptığı uyuşuyor mu?
   4. Hata durumları (exception) handle ediliyor mu yoksa yutuluyor mu?
   5. Return tipleri çağıranın beklediğiyle uyuşuyor mu?

   ZORUNLU ÇIKTI FORMATI — sadece bu tablo, başka metin yazma:
   | ID | Dosya:Satır | Niyet | Gerçekleşme | Ciddiyet | Güven |"

Agent B (coderabbit:code-reviewer):
  "[dosya] dosyasındaki tüm public fonksiyonları incele.

   Her fonksiyon için:
   - Adı ne vaat ediyor? Gerçekte ne yapıyor?
   - Parametre tipleri doğru mu?
   - None/null dönüş durumu var mı? Çağıran bunu handle ediyor mu?
   - SQL injection, IDOR, input validation riski var mı?

   ZORUNLU ÇIKTI FORMATI — sadece bu tablo, başka metin yazma:
   | ID | Dosya:Satır | Niyet | Gerçekleşme | Ciddiyet | Güven |"

Agent C (psychometrics-specialist VEYA domain-uygun uzman):
  "[dosya] dosyasındaki domain mantığını doğrula.

   - Algoritma çağrıları doğru sırada mı?
   - Parametre sınırları korunuyor mu? (IRT: a∈[0.1,3], b∈[-4,4], c∈[0,0.5])
   - Veri dönüşümleri (enum ↔ string, case convention) tutarlı mı?
   - question_bank mı yoksa questions mı sorgulanıyor?

   ZORUNLU ÇIKTI FORMATI — sadece bu tablo, başka metin yazma:
   | ID | Dosya:Satır | Niyet | Gerçekleşme | Ciddiyet | Güven |"
```

### Kalibrasyon Değerlendirme

```
Dosya A (fixlenmiş):
  □ Bilinen 3 düzeltmeden kaçı doğrulandı?     Hedef: ≥2/3
  □ Yeni bulgu sayısı?                           Hedef: 1-10 arası
  □ False positive? (elle 5 bulgu kontrol)       Hedef: ≤%30

Dosya B (bakılmamış):
  □ Anlamlı bulgu sayısı?                        Hedef: ≥2
  □ En az 1 P0 veya P1 bulgu var mı?             Hedef: evet

Convergence:
  □ 2+ agent aynı Dosya:Satır'ı buldu mu?       → YÜKSEK güven etiketle
```

### Karar Noktası

```
✅ Her iki dosyada hedefler karşılandı → ADIM 3'e geç
⚠️ Dosya A'da <2/3 doğrulama → agent promptlarını ayarla, tekrar kalibre
⚠️ >%50 false positive → tablo formatına "kanıt" kolonu ekle, tekrar kalibre
❌ Her iki dosyada 0 bulgu → yöntem temel sorunlu, kullanıcıya danış
```

### Çıktı

```markdown
## Adım 2: Kalibrasyon Sonucu

Dosya A: [dosya adı]
  Doğrulama: X/3 | Yeni bulgu: Y | False positive: Z%

Dosya B: [dosya adı]
  Bulgu: X adet | P0/P1: Y adet

Convergence: X bulgu 2+ agent tarafından doğrulandı
Karar: [GEÇ / AYARLA / DURDUR]
```

→ `findings.md`'ye ekle + kalibrasyon bulguları tabloya ekle

---

## ADIM 3 — Güven Katmanlı Tarama

**Süre:** 4-5 saat
**Soru:** "Öncelik 1 dosyalarda ne tür boşluklar var?"

### Katman 1: Kanıtlanabilir Boşluklar (KESİN güven)

İnsan yargısı gerektirmez. Statik araç + pattern matching.

```bash
# T1.1: Tip uyumsuzlukları (sadece Öncelik 1 dosyalar)
cd backend && mypy \
  app/services/DOSYA1.py \
  app/services/DOSYA2.py \
  app/api/DOSYA3.py \
  --disallow-untyped-defs \
  --warn-return-any \
  --ignore-missing-imports 2>&1

# T1.2: Frontend tip kontrolü (sadece Öncelik 1)
cd frontend && npx tsc --noEmit 2>&1 | grep -E "DOSYA1|DOSYA2"
```

```
# T1.3: Dual table regresyon
Grep: pattern="from.*models.*import.*\bQuestion\b" (QuestionBankItem DEĞİL)
  path=backend/app/services/ + backend/app/api/
  Hariç tut: _deprecated/, tests/, __pycache__

# T1.4: Absolute import yasağı (SQLAlchemy çift MetaData)
Grep: pattern="^from models\." path=backend/app/models/

# T1.5: Auth dekoratör eksikliği — ADAY listesi
Grep: pattern="@router\.(get|post|put|delete|patch)" path=backend/app/api/
  → Aynı fonksiyonda Depends(...get_current.*|require_admin|mevcut_kullanici) YOK
  → ADAY olarak işaretle, Katman 2'de bağlam kontrolü

# T1.6: get_async_session yanlış kullanım
Grep: pattern="async with get_async_session" path=backend/app/
  → Doğrusu: Depends(get_db) veya async with get_db_session_context()

# T1.7: is_active filtresi eksikliği — ADAY listesi
Grep: pattern="query.*QuestionBankItem|select.*QuestionBankItem" path=backend/app/
  → Aynı sorguda "is_active" YOK → ADAY
```

**Çıktı:** Kesin bulgular + Katman 2 aday listesi → `findings.md`'ye ekle

---

### Katman 2: Muhtemel Boşluklar (ORTA-YÜKSEK güven)

4 paralel agent. Katman 1 adaylarını bağlama oturturur + yeni bulgular.

```
Agent A (güvenlik) → Öncelik 1 backend dosyaları:
  "docs/audits/findings.md dosyasını oku. Katman 1'de [P0-ADAY] işaretli
   auth ve IDOR adaylarını bağlamıyla değerlendir.

   Her aday için:
   - Endpoint kasıtlı olarak public mi? (auth, health, docs)
   - user_id dışarıdan mı alınıyor yoksa token'dan mı çözülüyor?
   - Rate limiting var mı?

   Ek olarak Öncelik 1 dosyalarda:
   - SQL injection: f-string veya format() ile SQL oluşturma
   - SSRF: Kullanıcı URL'si doğrudan fetch ediliyor mu?
   - Secret exposure: Hardcoded key, password, token

   ZORUNLU ÇIKTI FORMATI:
   | ID | Dosya:Satır | Niyet | Gerçekleşme | Ciddiyet | Güven | Agent |
   Agent kolonu: 'security'"

Agent B (veri bütünlüğü) → Öncelik 1 backend dosyaları:
  "docs/audits/findings.md dosyasını oku. Katman 1'de [P1-ADAY] işaretli
   is_active ve tablo adaylarını bağlamıyla değerlendir.

   Her sorgu noktasında:
   - Doğru tablo mu? (question_bank = 77K prod, questions = BOŞ legacy)
   - is_active == True filtresi var mı?
   - Return tipi çağıranın beklediğiyle uyuşuyor mu?
   - Exception yakalanıp yutulmuyor mu (bare except)?
   - Null/None dönüş handle ediliyor mu?

   Case convention: question_bank UPPERCASE ('TYT','MATEMATIK'),
   enum lowercase ('tyt','matematik') — dönüşüm yapılıyor mu?

   ZORUNLU ÇIKTI FORMATI:
   | ID | Dosya:Satır | Niyet | Gerçekleşme | Ciddiyet | Güven | Agent |
   Agent kolonu: 'data-integrity'"

Agent C (domain) → Öncelik 1 algoritma/servis dosyaları:
  "Öncelik 1 dosyalardaki algoritma ve iş mantığını doğrula.

   IRT 3PL: a∈[0.1,3.0], b∈[-4.0,4.0], c∈[0.0,0.5], P(θ) clamp [0,1]
   BKT: p(L),p(T),p(G),p(S) ∈ [0,1], p(L) monoton artan
   FSRS: stability≥0, difficulty∈[0,1], interval≥1
   ZPD: P(correct)∈[0.15,0.85]
   YKS: TYT 4Y=1D net düşürme, AYT alan katsayısı

   Fonksiyon adı ↔ davranış uyumu: adı 'calculate_score' ama aslında
   sadece fetch yapıyorsa → niyet-gerçekleşme boşluğu.

   ZORUNLU ÇIKTI FORMATI:
   | ID | Dosya:Satır | Niyet | Gerçekleşme | Ciddiyet | Güven | Agent |
   Agent kolonu: 'domain'"

Agent D (frontend) → Öncelik 1 frontend dosyaları:
  "Öncelik 1 frontend component, hook ve service dosyalarını analiz et.

   Kontrol noktaları:
   - API çağrısı doğru endpoint'e mi gidiyor? (/api/v1/ prefix)
   - credentials: 'include' her fetch'te var mı? (cookie auth)
   - Response tipi TypeScript interface ile uyuşuyor mu?
   - Error state handle ediliyor mu? (loading/error/empty)
   - Zustand store güncellemesinde race condition riski var mı?
   - localStorage'da auth token kalıntısı var mı? (artık cookie-based olmalı)

   ZORUNLU ÇIKTI FORMATI:
   | ID | Dosya:Satır | Niyet | Gerçekleşme | Ciddiyet | Güven | Agent |
   Agent kolonu: 'frontend'"
```

### Convergence (Çapraz Doğrulama)

4 agent çıktısı toplandıktan sonra:

```
1. Tüm tabloları birleştir
2. Aynı Dosya:Satır'ı 2+ agent bulduysa → Güven'i YÜKSEK yap
3. Tek agent bulduysa → mevcut güven kalır
4. Çelişkili bulgu (biri P0, diğeri "sorun yok") → elle incele, kullanıcıya sor
```

### P0 Karar Noktası

```
Katman 1 + Katman 2 tamamlandığında:

P0 bulgu sayısı:
  0     → doğrudan Katman 3'e geç
  1-3   → kullanıcıya göster: "X P0 bulundu. Şimdi fix mi, analiz devam mı?"
  4+    → analiz DURDUR, P0'ları önce düzelt (bu kadar P0 varsa analiz güvenilmez)
```

→ Tüm bulgular `findings.md`'ye ekle

---

### Katman 3: Yorum Gerektiren Boşluklar (DÜŞÜK güven)

**Sadece Katman 1-2'de ≤3 P0 bulunduysa geçilir.**
**Kullanıcı kararı gerektirir.**

```
T3.1: Orchestrator policy tutarlılığı
  Araç: Explore agent
  "orchestrator/ altındaki 45 policy'yi analiz et.
   Birbiriyle çelişen policy var mı?
   Policy → agent routing mantıklı mı?
   State geçişlerinde kayıp/bozulma riski var mı?"

T3.2: Config/Route tutarlılığı
  Araç: general-purpose agent
  ".env.mvp ↔ docker-compose.yml ↔ backend/core/config.py
   ↔ nginx.conf ↔ vite.config.ts arasında:
   - Port numaraları uyuşuyor mu?
   - Hostname (localhost vs host.docker.internal) tutarlı mı?
   - Backend router prefix ↔ frontend API URL ↔ nginx proxy uyuşuyor mu?
   - VersionRedirectMiddleware 32 kuralı güncel mi?"

T3.3: Test semantiği
  Araç: Grep + Bash
  "- assert True / assert 1==1 / pass gibi sahte test var mı?
   - 1337 skip'in sebep dağılımı nedir?
   - Coverage %47 boşlukta P0 risk taşıyan dosya var mı?"

T3.4: Dokümantasyon ↔ gerçeklik
  "CLAUDE.md'deki sayılar (41+ endpoint, 77,336 soru, 17 kanal)
   güncel mi? Gerçek durum farklıysa → niyet-gerçekleşme boşluğu."
```

→ Bulgular `findings.md`'ye ekle

---

## ADIM 4 — Akış İzleme

**Süre:** 2-3 saat
**Soru:** "Kullanıcının en kritik 2 eylemi uçtan uca doğru mu?"
**Bağımlılık:** Adım 3'ün birikimli modeli üstüne inşa eder.

### Akış Seçimi Gerekçesi

| Akış | Kullanıcı Etkisi | Karmaşıklık | Sorun Geçmişi | Seçim |
|------|-------------------|-------------|---------------|-------|
| Sınav | Herkes, her gün | Yüksek (7+ servis) | 3 session | **SEÇİLDİ** |
| Öğrenme yolu | Herkes, her gün | Çok yüksek (4 algoritma) | 5 session | **SEÇİLDİ** |
| Auth | Herkes, giriş | Orta | 4 session (stabilize) | İzlenmiyor |
| YouTube | Aktif kullanıcı | Orta | 1 session (stabil) | İzlenmiyor |

### Akış A: Sınav Akışı (feature-dev:code-explorer)

```
"KIRO2 sınav akışını kullanıcı perspektifinden uçtan uca izle.

 ÖNCE docs/audits/findings.md dosyasını oku — önceki adımların
 bulgularını bu akışta doğrula.

 İzleme rotası (her geçiş noktasında DUR ve kontrol et):

 1. UI GİRİŞ: ExamPage/ModernExamStart component
    → Hangi API endpoint'i çağrılıyor?
    → Props doğru tipte mi?

 2. API: exam router → endpoint fonksiyonu
    → Auth kontrolü var mı? (Depends)
    → Request validation (Pydantic schema)

 3. SERVICE: sınav session oluşturma
    → Soru seçimi: hangi tablo? question_bank mi?
    → is_active filtresi var mı?
    → Soru sayısı ve süre kısıtı (TYT 120/135dk) doğru mu?

 4. SERVICE: cevap kaydetme
    → record_answer zinciri: BKT → IRT → FSRS → ZPD
    → Her geçişte parametre tipi korunuyor mu?
    → 4 yanlış 1 doğru götürme hesaplaması doğru mu?

 5. SERVICE: session kapatma + sonuç
    → Puan hesaplama formülü
    → Net hesabı: (doğru - yanlış/4) veya (doğru - yanlış/3)?

 6. DB → API: response dönüşümü
    → Field adları: snake_case → camelCase?
    → Null field'lar handle ediliyor mu?

 7. API → UI: sonuç gösterimi
    → Backend'den gelen ile frontend'in gösterdiği uyuşuyor mu?
    → Konu bazlı analiz doğru hesaplanıyor mu?

 HER GEÇİŞ NOKTASINDA:
 □ Tip dönüşümü doğru mu?
 □ Field adları uyuşuyor mu?
 □ Null/empty handle ediliyor mu?
 □ Hata durumunda ne oluyor?
 □ findings.md'deki hangi bulgu bu noktayı etkiliyor?

 ÇIKTI: Geçiş noktası tablosu
 | Geçiş | Kaynak | Hedef | Durum | Boşluk (varsa) |"
```

### Akış B: Öğrenme Yolu + Algoritma Zinciri (feature-dev:code-explorer)

```
"KIRO2 öğrenme yolu akışını uçtan uca izle.

 ÖNCE docs/audits/findings.md dosyasını oku.

 İzleme rotası:

 1. UI: DungeonMap / ModernLearningPathPage
    → Hangi API çağrıları? (/api/v1/learning-path/...)
    → Node tıklama → quiz başlatma akışı

 2. API: learning_path router
    → Auth + ownership kontrolü (verify_student_access)
    → DAG oluşturma: topic_hierarchy doğru okunuyor mu?

 3. SERVICE: DAG + node ilerleme
    → topic_hierarchy (105 row) → DAG node eşleşmesi
    → Node durumu: prereq_blocked doğru hesaplanıyor mu?

 4. SERVICE: soru seçimi (quiz)
    → IRT theta ↔ soru difficulty eşleşmesi
    → ZPD sınırları: P(correct) ∈ [0.15, 0.85]?

 5. SERVICE: cevap kaydı → algoritma zinciri
    → BKT: p_mastery güncelleme (p_L, p_T, p_G, p_S sınırları)
    → BKT → IRT: theta = p_L bridge (tip dönüşümü doğru mu?)
    → IRT: theta_se güncelleme
    → FSRS: state read → review → state write (persistent mi?)
    → FSRS: stability/difficulty clamp
    → ZPD: sonraki soru zorluk seçimi

 6. DB: state persistence
    → FSRSCard tablosu: due date doğru yazılıyor mu?
    → user_theta tablosu: theta değeri makul aralıkta mı?

 7. UI: dungeon room durumu güncelleme
    → Room ↔ topic eşleşmesi
    → Fog-of-war: mastered node'lar açılıyor mu?
    → Progress bar doğru mu?

 ÇIKTI: Geçiş noktası tablosu
 | Geçiş | Kaynak | Hedef | Durum | Boşluk (varsa) |"
```

### d-dataset Bütünlük Kontrolü (Akış izleme sırasında)

```
Akış izleme sırasında soru verisi DB'den okunduğunda:

□ question_bank'taki soru sayısı = 77,336 mi?
  → SELECT COUNT(*) FROM question_bank WHERE is_active = true

□ eslesmis_sorucevap.jsonl → question_bank import tutarlı mı?
  → Rastgele 10 soru: jsonl'deki field'lar DB'dekiyle uyuşuyor mu?

□ question_image_url: 58,523 kayıt hâlâ geçerli mi?
  → SELECT COUNT(*) FROM question_bank WHERE question_image_url IS NOT NULL
```

→ Tüm geçiş noktası bulguları `findings.md`'ye ekle

---

## ADIM 5 — Sentez ve Rapor

**Süre:** 30-45 dk
**Girdi:** `docs/audits/findings.md` (Adım 0-4 boyunca biriken)

### Rapor Yapısı

```
docs/audits/semantic-analysis-report-v1.md

## Executive Summary (1 sayfa)
- Tarih, kapsam, yöntem
- Analiz edilen: X dosya, Y endpoint, Z akış
- Toplam bulgu: N (P0: a, P1: b, P2: c)
- Güven dağılımı: KESİN: w, YÜKSEK: x, ORTA: y, DÜŞÜK: z
- Kalibrasyon: [başarılı — X/3 doğrulama, Y yeni bulgu]
- Durdurma: [tetiklenmedi / tetiklendi → aksiyon]
- Kritik karar: [varsa kullanıcı kararı özeti]

## P0 Bulgular — Hemen Aksiyon
| ID | Dosya:Satır | Boşluk Özeti | Önerilen Fix | Güven |

## P1 Bulgular — Sprint Planına Al
| ID | Dosya:Satır | Boşluk Özeti | Önerilen Fix | Güven |

## P2 Bulgular — Backlog
(sayı + kategori özeti, tablo gereksiz)

## Akış Trace Özeti
### Sınav Akışı
- İzlenen geçiş sayısı: X
- Sorun bulunan geçişler: Y (listele)

### Öğrenme Yolu Akışı
- İzlenen geçiş sayısı: X
- Sorun bulunan geçişler: Y (listele)

## Kapsam Dışı / Sonraki İterasyonda
- Öncelik 2-3 dosyalar (analiz edilmedi)
- Runtime doğrulama (Docker kapalıysa)
- Tam frontend coverage analizi

## Sonraki Adımlar
1. P0 düzeltmeleri (dosya:satır listesi)
2. P0 fix sonrası regresyon taraması
3. Öncelik 2 dosyalarla ADIM 3-4 tekrarı (opsiyonel genişletme)
```

---

## Opsiyonel: Runtime Doğrulama

**Ön koşul:** Docker servisleri healthy
**Ne zaman:** Adım 5 sonrası, P0 fix'ler tamamlandıktan sonra

```bash
# Altyapı hazır mı?
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "healthy|Up"
curl -s http://localhost:8000/api/v1/health | python -m json.tool
curl -s http://localhost:3000/healthz
```

Hazırsa:

```
1. Playwright: login → dashboard → sınav başlat → soru çöz → sonuç
   → Accessibility tree (semantik DOM)
   → Network requests (gereksiz çağrı, 404, CORS)
   → Console messages (error pattern)

2. curl ile 5 kritik endpoint:
   → Response shape findings.md'deki schema ile uyuşuyor mu?
   → Response time kabul edilebilir mi?
```

---

## Genişletme Döngüsü

İlk iterasyon (Adım 0-5) tamamlandığında:

```
□ P0 fix'ler yapıldı mı?              → regresyon taraması (mini Adım 3 Katman 1)
□ Öncelik 2 dosyalar önemli mi?        → Adım 3-4-5 tekrarı (Öncelik 2 ile)
□ Yeni commit geldi mi?                → delta analizi (sadece değişen dosyalar)
□ Runtime doğrulama gerekiyor mu?      → Opsiyonel Runtime adımı
```

Her genişletme kendi bulgularını aynı `findings.md`'ye ekler.

---

## Tam Akış Diyagramı

```
ADIM 0: Ön Koşul
  │
  ├─ BLOCKED ──→ DUR, altyapı düzelt, sonra tekrar başla
  │
  └─ GO
      ↓
ADIM 1: Hedef Haritası
  │ Çıktı: Öncelikli dosya listesi (3 bant)
  ↓
ADIM 2: Kalibrasyon (2 dosya × 3 agent)
  │
  ├─ BAŞARISIZ ──→ prompt ayarla, tekrar kalibre et (max 2 deneme)
  │
  └─ BAŞARILI
      ↓
ADIM 3: Güven Katmanlı Tarama
  │
  ├─ Katman 1 (KESİN) ──→ kesin bulgular + aday listesi
  │     ↓
  ├─ Katman 2 (4 paralel agent) ──→ convergence ──→ güven-etiketli bulgular
  │     │
  │     └─ P0 karar noktası ──→ 4+ P0: DURDUR, fix et
  │                           → 1-3 P0: kullanıcıya sor
  │                           → 0 P0: devam
  │     ↓
  └─ Katman 3 (yorumsal, kullanıcı kararı) ──→ değerlendirilmiş bulgular
      ↓
ADIM 4: Akış İzleme (2 akış, Adım 3 modeli üstüne)
  │
  ├─ Sınav akışı trace (7 geçiş noktası)
  ├─ Öğrenme yolu trace (7 geçiş noktası)
  └─ d-dataset bütünlük kontrolü
      ↓
ADIM 5: Sentez Raporu
  │ Çıktı: semantic-analysis-report-v1.md (piramit: 1 executive + P0/P1/P2 + trace)
  ↓
[OPSİYONEL] Runtime Doğrulama (Docker çalışıyorsa)
  ↓
[OPSİYONEL] Genişletme Döngüsü (Öncelik 2 dosyalar / yeni commit'ler)
```

---

## Pratik Notlar

### Session Planlaması
```
Session 1 (4-5 saat):
  Adım 0 + Adım 1 + Adım 2 + Adım 3 (Katman 1-2)
  → İlk session sonunda: kesin + muhtemel bulgular, P0 listesi

Session 2 (3-4 saat):
  Adım 3 (Katman 3) + Adım 4 + Adım 5
  → İkinci session sonunda: final rapor + aksiyon listesi

Session 3 (opsiyonel, 2-3 saat):
  P0 fix + regresyon taraması + Öncelik 2 genişletme
```

### Context Yönetimi
```
- findings.md büyüyen artifact — compaction'dan etkilenmez
- Her adım sonunda findings.md'ye yaz
- Sonraki adımın agent prompt'unda: "docs/audits/findings.md oku"
- Session arası: findings.md + bu metodoloji dokümanı yeterli
```

### Agent Çıktı Formatı Standardı
```
TÜM agent'lar bu tabloyu kullanır:
| ID | Dosya:Satır | Niyet | Gerçekleşme | Ciddiyet | Güven | Agent |

- ID: A001, A002... (Adım numarası + sıra)
- Ciddiyet: P0 / P1 / P2
- Güven: KESİN / YÜKSEK / ORTA / DÜŞÜK
- Agent: security / data-integrity / domain / frontend / explorer
- Tablo dışı açıklama YASAK (gürültü azaltma)
```

### Araç Yoksa Alternatifler
```
vulture yok → Grep: export/def tanımı olan ama import edilmeyen semboller
radon yok  → atla (karmaşıklık = P2, kritik değil)
bandit yok → Agent A (güvenlik) bunu kapsar
pydeps yok → Grep: import haritası (daha yavaş ama çalışır)
```
