# KIRO2 BugBot Kuralları

Bu dosya Cursor BugBot'un PR review'larında kullandığı proje-özel kurallardır.
Detaylı geliştirme talimatları için CLAUDE.md ve .cursor/rules/00-core.mdc'ye bak.

## Learned Rules (8 Nisan 2026 itibariyle)

BugBot PR yorumlarından otomatik öğreniyor. Davranış:
- **Reactions ve replies**'dan candidate rule üretir
- **Faydalıysa** otomatik promote eder
- **Fayda sağlamayan** rule'ları auto-disable eder
- Resolution rate şu an **%78**

**Benim için ne anlama geliyor?** Her PR yorumunda:
- BugBot bulgusu HATALI ise 👎 (thumbs down) bas + sebep yaz
- BugBot bulgusu DOĞRU + useful ise 👍 bas
- Bu feedback ile BugBot KIRO2'ye zamanla uyum sağlar

Manual rule tanımı için Bugbot Dashboard → Repository Rules:
https://cursor.com/dashboard/bugbot/repository-rules

## Backend Güvenlik

Eğer PR `backend/app/api/v1/` altında yeni endpoint ekliyor ve handler'ında
`Depends(get_current_user)` yoksa:
- Blocking Bug aç, başlık: "Eksik auth dependency"
- Body: "Endpoint authenticated kullanıcı olmadan erişilebilir. FastAPI
  Depends(get_current_user) ekle. Bkz: backend/app/core/security.py template"
- Label: "security"

Eğer endpoint kullanıcıya özel bir resource döndürüyor veya değiştiriyor
(soru, attempt, progress, study_plan gibi) ve ownership check yoksa
(örn. `resource.user_id == current_user.id`):
- Blocking Bug aç: "Eksik IDOR ownership check"
- Body: "Kullanıcı başka birinin kaynağına erişebilir. Resource'u döndürmeden
  önce user_id doğrulaması ekle."
- Label: "security"

## Dual Table Trap (KIRO2-özel)

Eğer PR `from models.database import Question` import ediyorsa:
- Blocking Bug aç: "Yanlış Question tablosu"
- Body: "`models.database.Question` BOŞ legacy tablo. Production'da
  `models.question_bank.QuestionBankItem` (77K soru) kullanılmalı.
  is_active == True filtresi de zorunlu."
- Label: "kiro2-critical"

## Alembic Migration

Eğer PR `backend/alembic/versions/` altında yeni revision ekliyorsa:
- `CREATE INDEX` var mı kontrol et — varsa `CONCURRENTLY` kullanılmalı
  (prod tablolarda lock downtime önler)
- `downgrade()` fonksiyonu boş bırakılmış mı? Boşsa non-blocking Bug:
  "Migration reversible değil, downgrade implementasyonu eksik"
- Data migration (INSERT/UPDATE) ile schema migration (ALTER) aynı revision'da mı?
  Öyleyse warning: "Data ve schema migration ayrı revision'lara bölünmeli"
- revision ID zincirinde boşluk/çakışma var mı (down_revision doğru mu)?

## Test Zorunluluğu

Eğer PR `backend/app/services/`, `backend/app/api/`, `backend/app/core/`
altında değişiklik yapıyor ve `backend/tests/` veya `tests/` altında
yeni/değişen test dosyası yoksa:
- Blocking Bug aç: "Backend değişikliği için eksik test"
- Body: "916 passing test baseline korunmalı. Değiştirilen modül için
  pytest test dosyası ekle veya güncelle."
- Label: "quality"

Eğer test dosyasında `assert True`, `assert 1 == 1`, `expect(true).toBe(true)`,
veya `@pytest.mark.skip` (reason olmadan) varsa:
- Blocking Bug: "Reward hacking test"
- Body: "Gerçek assertion yerine trivial true/skip. Testin amacını gerçekten
  doğrulayan assertion yaz."
- Label: "quality"

## FSRS / IRT / BKT Algoritma Koruması

Eğer PR `backend/app/services/fsrs/`, `backend/app/services/irt/`,
`backend/app/services/bkt/` altında parametre/formül değiştiriyorsa:
- PR description'da değişiklik gerekçesi var mı kontrol et
- Golden dataset testleri (`tests/irt/`, `tests/fsrs/`) hâlâ geçiyor mu?
- Parametre değişikliği varsa rollback planı belirtilmiş mi?
- Label: "algorithm-critical"

IRT parametre sınırı ihlali:
- difficulty < -5.0 veya > 4.0 → Blocking Bug
- discrimination < 0.1 veya > 4.0 → Blocking Bug
- guessing < 0 veya > 0.4 → Blocking Bug

## Middleware HTTPException (Session 148)

Eğer `BaseHTTPMiddleware.dispatch()` içinde `raise HTTPException` varsa:
- Blocking Bug: "Middleware'de HTTPException yasak"
- Body: "Session 148 GF99: BaseHTTPMiddleware.dispatch()'te HTTPException
  500 olarak çıkar. JSONResponse kullan."
- Label: "kiro2-critical"

## Turkish NLP / Tokenizer

Eğer PR `backend/mcp_servers/zemberek_nlp/` veya tokenizer ile ilgili
kod değiştiriyorsa:
- Türkçe agglutinative morfoloji testleri geçiyor mu?
- BPE dışında tokenization varsa edge case'ler dokümante edilmiş mi?
- `.toUpperCase()` / `.toLowerCase()` Türkçe string üzerinde kullanılmış mı?
  (yanlış — `.toLocaleUpperCase('tr-TR')` kullanılmalı)
- Label: "nlp"

## Frontend

Eğer PR `frontend/src/` altında değişiklik yapıyorsa:
- TypeScript strict mode ihlali var mı (`any` kullanımı)?
- React component'te hook kuralları (rules of hooks) ihlal edilmiş mi?
- MSW test kurulumu olan modüllerde yeni endpoint için mock eklenmiş mi?
- `stores/` (çoğul) veya `useAuth.ts` import'u var mı?
  - Varsa Blocking Bug: "Yanlış store path. `store/authStore` (tekil) kullan"
- Label: "frontend"

## Secrets / Env

Eğer PR'da `.env*`, `secrets.baseline`, yapılandırma dosyalarında
plaintext token/password pattern varsa (regex: `/(api_key|token|password|secret)\s*=\s*["'][^"']{8,}/i`):
- Blocking Bug aç: "Olası secret sızıntısı"
- Body: "Commit'lenmeden önce secret'ı çıkar, `.env.example`'da placeholder kullan"
- Label: "security"

## Dosya Boyutu / Performance

Eğer yeni eklenen tek bir dosya 1000 satırdan fazlaysa:
- Non-blocking Bug: "Büyük dosya — modüler bölünmesi düşünülmeli"

Eğer loop içinde `await` + DB query pattern tespit edilirse (N+1 problem):
- Warning: "N+1 query pattern — selectinload/joinedload ile eager load yap"

## MCP Tool Kullanımı (Teams/Enterprise Plan)

Eğer BugBot MCP tool'larına erişimi varsa (Teams plan), review sırasında
ek context almak için:
- GitHub MCP: related issues, PR history
- Filesystem MCP: cross-file reference check
- Sequential-thinking MCP: karmaşık security analiz

Individual plan'da MCP yok — yalnızca bu markdown rule'lara güveniyor.
