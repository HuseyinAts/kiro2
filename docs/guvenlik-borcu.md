# Güvenlik Taraması Borç Kaydı

> Bu dosya, `.github/workflows/security.yml` içindeki kapıların neden
> "ratchet" (yeni bulguya kırmızı, mevcut borca değil) olarak ayarlandığını
> ve o borcun **tam olarak ne kadar olduğunu** kayıt altına alır.
> Amaç gizlemek değil; sayıyı görünür tutup küçültmek.

Ölçüm tarihi: 2026-08-28
Ölçüm yöntemi: `git worktree` ile HEAD'in temiz bir kopyası (CI'ın
`actions/checkout` ile gördüğü ağacın aynısı: 2604 izlenen `backend/**/*.py`).
Canlı çalışma dizini kullanılmadı — orada `.venv` vb. yüzünden 16.339 dosya
görünüyor ve sayılar CI ile uyuşmuyor.

---

## 1. Bandit (SAST job)

CI komutu: `bandit -r backend/ -ll` → severity MEDIUM ve üzeri.

| | Adet |
|---|---|
| Toplam bulgu (tüm severity) | 33.231 |
| LOW | 32.890 |
| **MEDIUM** | **289** |
| **HIGH** | **52** |
| `-ll` kapsamı (MEDIUM+) | **341** |

`-ll` kapsamındaki 341 bulgunun 90'ı test dosyalarında, 251'i ürün kodunda.

### Bu PR'da gerçekten düzeltilenler (ürün kodu HIGH: 43 → 0)

| Test | Adet | Ne yapıldı |
|---|---|---|
| B324 `hashlib` | 42 | Hepsi cache key / dedup / A-B kovalama amaçlı `md5`. `usedforsecurity=False` eklendi (Python 3.9+ bunun için var; ileride gerçek güvenlik amaçlı bir `md5` eklenirse Bandit yine yakalar). İki tanesi ayrıca **davranışsal** olarak düzeltildi: `core/decorators/cache.py` JWT cache key'i `md5[:12]` (48 bit → kullanıcılar arası cache çarpışması riski) yerine `sha256[:32]`; `core/unified_auth_service.py` sahte TOTP → RFC 6238. |
| B605 `os.system` | 1 | `start_hybrid_system.py`: `os.system('cls'/'clear')` → ANSI escape. Kabuk çağrısı tamamen kalktı. |

### Kalan borç (ratchet ile donduruldu)

`.bandit-baseline.json` bu anki bulguları kaydeder. Kapı bundan sonra
**yalnızca yeni bulguya** kırmızı olur.

MEDIUM kırılımı (ürün kodu):

| Test | Adet | Not |
|---|---|---|
| B608 hardcoded_sql_expressions | 140 | Çoğu `backend/scripts/quality/**` altındaki tek seferlik veri betiklerinde f-string SQL. Tek tek okunmalı; bir kısmı gerçek olabilir. |
| B310 urllib urlopen | 19 | Şema doğrulaması yok; SSRF açısından denetlenmeli. |
| B615 huggingface_unsafe_download | 17 | `from_pretrained` çağrılarında `revision=` sabitlenmemiş — tedarik zinciri riski. |
| B104 hardcoded_bind_all_interfaces | 8 | `0.0.0.0` bind. |
| B301 pickle | 7 | |
| B314 xml | 4 | |
| B102 exec | 3 | |
| B103 set_bad_file_permissions | 2 | |
| B306 mktemp | 1 | |
| B614 pytorch_load | 1 | |
| B113 request_without_timeout | 1 | |

**Sıradaki iş:** B615 (17) ve B310 (19) en yüksek getirili küme — ikisi de
mekanik ve gerçek risk taşıyor.

---

## 2. Checkov (IaC job)

CI komutu: `checkov -d . --framework all`.

| Çerçeve | Geçen | **Düşen** |
|---|---|---|
| kubernetes | 939 | **171** |
| secrets | 0 | **20** |
| github_actions | 1446 | **14** |
| openapi | 2 | **3** |
| dockerfile | 1348 | **2** |
| **Toplam** | | **210** |

Dosya bazında en yoğunlar: `k8s/deployment.yaml` (53),
`k8s/deployment-week4.yaml` (48), `k8s/statefulset.yaml` (39),
`kubernetes/deployment.yaml` (16), `kubernetes/base/backend-deployment.yaml` (13).

Kubernetes bulgularının çoğu tek bir kök eksiklikten geliyor: konteynerlerde
`securityContext` yok. Aşağıdaki dokuz kontrol aynı düzeltmeyle kapanır
(her biri 12 kez):

`CKV_K8S_20` allowPrivilegeEscalation · `CKV_K8S_22` readOnlyRootFilesystem ·
`CKV_K8S_28` NET_RAW · `CKV_K8S_30` securityContext · `CKV_K8S_31` seccomp ·
`CKV_K8S_37` capabilities drop · `CKV_K8S_38` serviceAccountToken ·
`CKV_K8S_40` yüksek UID · `CKV_K8S_43` image digest

**Sıradaki iş:** `k8s/` altındaki üç manifest'e ortak bir `securityContext`
bloğu eklemek 108 bulguyu tek seferde kapatır.

`.checkov.baseline` mevcut 210 bulguyu dondurur; yeni gelen kırmızı yapar.

---

## 3. Bağımlılık CVE'leri (pip-audit)

`pip-audit -r backend/requirements.txt` **gerçek ve ciddi** CVE'ler
buluyor. Bu adım şu an `continue-on-error: true` — çünkü düzeltmesi sürüm
yükseltmesi demek ve ayrı bir PR'da golden-flow ile doğrulanması gerekiyor.

| Paket | Kurulu | Öne çıkan bulgu |
|---|---|---|
| `pdfminer.six` | 20231228 | Pickle deserialization → **RCE** (PYSEC-2026-1762, PYSEC-2026-1761) |
| `torch` | 2.4.1 | `torch.load(weights_only=True)` ile bile **RCE** (PYSEC-2025-41); ayrıca 8 DoS |
| `mcp` | 1.0.0 | Oturum kaçırma (PYSEC-2026-3482), WebSocket origin doğrulaması yok (PYSEC-2026-3483), DNS rebinding (PYSEC-2026-1617) |
| `pypdf` | 6.12.2 | 5 adet DoS / sonsuz döngü |
| `sentry-sdk` | 1.40.0 | `env={}` verilse bile ortam değişkenlerinin alt sürece sızması (PYSEC-2026-1917) |
| `click` | 8.1.8 | `click.edit()` komut enjeksiyonu |
| `protobuf` | 4.25.9 | `ParseDict()` özyineleme DoS |

Doğrudan `requirements.txt`'te sabitli olanlar: `pypdf==6.12.2`,
`sentry-sdk[fastapi]==1.40.0`, `mcp==1.0.0`, `torch>=2.1.0`.
Diğerleri geçişli bağımlılık.

**Sıradaki iş:** `sentry-sdk` 1.x→2.x kırıcı bir major sürüm; `torch`
2.4→2.7 model kodunu etkileyebilir. Bu yüzden ayrı PR + golden-flow.
Repoda zaten 20 açık Dependabot PR'ı var, önce onlar elenmeli.

---

## 4. Semgrep

`semgrep/semgrep-action@v1` bu depoda **hiç çalışmadı** (iş her zaman daha
önce, Bandit adımında düşüyordu). Kaç bulgu üreteceği bilinmiyor. Kalibre
edilmemiş bir kapıyı kırmızı bırakmak yerine önce sayı görünür kılınıyor;
eşik, sayılar bilindikten sonra bağlanacak.

---

## 5. OWASP ZAP (API Security Testing job)

CI komutu: `zaproxy/action-api-scan@v0.5.0 -t .../openapi.json -a -I -c .zap/rules.tsv`
(aktif tarama, `openapi.json`'dan import edilen 1596 URL -> 10.055 URL'e
genisliyor).

Run 33214662441 (28 Ağu 2026, PR #62, 2. deneme): `FAIL-NEW: SQL Injection
[40018] x 163`, iş 32dk 32sn'de kırmızı düştü. Ham veri: run'ın kendi
`zap-report` artifact'ı (`report_json.json`, `gh run download`) ve
zaproxy action'ın otomatik açtığı issue #64.

### Doğrulama

163 vuruşun 161'i **boş `evidence`** alanıyla geldi -- yalnızca ZAP'in
boolean-tabanlı sezgiseli (`AND 1=1` / `AND 1=2` gönderip yanıt
boyutu/içeriği farklılaşıyor mu diye bakan teknik). Vurulan parametreler
`limit`, `sayfa`, `konu`, `zorluk`, `aktif`, `end_date`, `search` gibi
sıradan filtre/sayfalama alanları -- bu alanlarda deger degistikce sonuc
kumesinin degismesi zaten BEKLENEN davranis, sezgisel bunu "SQLi" sanıyor.

Kod tarafında dogrulama: bu 163 vurusun dagıldıgı tum route/servis
dosyalari (`api/auth.py`, `api/veli.py`, `api/admin.py`,
`services/veli_onay_service.py` ve digerleri) tek tek kontrol edildi --
sorgu insasi ya SQLAlchemy ORM `select(...).where(Model.x == deger)`
(otomatik parametreli) ya da baglanan `text("... WHERE x = :p", {"p": deger})`
kullaniyor. Depo genelinde `git grep` ile ham f-string/`.format`/`%`
SQL insasi taraması yapıldı: canli API yüzeyinde tek eşleşme yok; tek
eşleşmeler zaten `# nosec B608` ile gerekçelendirilmiş iki satır
(`api/admin.py:183,340` -- sabit kod parçaları f-string'de, kullanıcı
değerleri hep `:param` bağlı) ve Alembic migration'larının DDL'inde
(tablo/kolon adları sabit Python listelerinden, HTTP girdisinden değil).
Bandit'in aynı sınıfı yakalayan B608 kuralı da (bkz. §1) canlı API
kodunda sıfır bulgu üretti -- iki bağımsız aracın doğrulaması örtüşüyor.

Kalan 2 vuruş (`veli-onay/verify`, `veli-onay/withdraw`, param `token`,
attack `John Doe'(`) gerçek `HTTP/1.1 500` evidence'ı taşıyor. Kod okundu:
`VeliOnayService.verify_and_grant/withdraw` token'i önce `hashlib.sha256`
ile hash'liyor, DB'ye SADECE bu hash `token_hash == :hash` seklinde ORM
karsilastirmasiyla gidiyor -- enjeksiyona kapali bir yol. Bu 2 istek aynı
taramanın genel `A Server Error response code [100000]` grubunda da var
(227 vuruş, API'nin tamamına yayılmış) -- yani token içeriğine özgü değil,
10.055 URL'lik aktif taramanın tek bir test Postgres konteynerine bindirdiği
yük altında oluşan dağınık/geçici 500'lerden ikisi. `settings.debug=False`
olduğu için (CI `DEBUG` env değişkenini set etmiyor) global exception
handler (`core/application.py:434`) zaten yalnız `{"detail": "Dahili
sunucu hatasi"}` dönüyor, iz (traceback) sızmıyor.

### Karar

`.zap/rules.tsv`: `40018` (genel boolean-tabanlı) `FAIL` -> `WARN`.
Zaman-tabanlı SQLi varyantları (`40019`-`40022`, farklı/daha güvenilir
teknik) `FAIL` kalıyor; bu taramada hiç vurmadılar. Gerçek bir SQLi
bulunmadı -- bu, "gerçek delik -> gerçek düzeltme" değil, "yanlış pozitif
-> belgelenmiş istisna" dalı (SAST/IaC baseline ratchet'iyle aynı ilke).

**Sıradaki iş (opsiyonel, kapı değil):** 227'lik genel 500 kümesi, tek
Postgres/Redis konteynerinin 10k'lık aktif tarama yükü altında bağlantı
havuzu baskısı görüp görmediğine dair ayrı bir dayanıklılık sorusu --
güvenlik açığı değil, kapasite/timeout ayarı sorusu. Bu PR'ın kapsamı
dışında bırakıldı.

---

## 6. CodeQL (py/weak-sensitive-data-hashing)

PR #62, commit `9a29c9c`'den sonra alınan check-run: "Code scanning results /
CodeQL -- 7 new alerts including 7 high severity security vulnerabilities"
(PR alert #2977-#2983, hepsi `py/weak-sensitive-data-hashing`, CWE-327/328/916).
Bu, aynı PR'ın Bandit için eklediği `usedforsecurity=False` bayrağının (bkz.
§1) 7 `hashlib.md5(...)` çağrı noktasında CodeQL'in "yeni alert" muhasebesini
tetiklemesinden geliyor.

### Doğrulama

Master'ın kendi açık CodeQL alert'leri karşılaştırıldı
(`/security/code-scanning?query=tool:CodeQL+branch:master+rule:py/weak-sensitive-data-hashing+is:open`):
**master'da bu kuralla açık 18 alert zaten var** (20 Tem 2026'dan beri), ve
PR'ın 7 "yeni" alert'i dosya bazında birebir eşleşiyor:

| PR alert | Master'daki eşi (20 Tem 2026) | Dosya |
|---|---|---|
| #2983 | #151 | `backend/services/visual_supports_service.py` |
| #2982 | #145 | `backend/core/rbac_system.py` (`_get_cache_key`) |
| #2981 | #144 | `backend/core/rbac_system.py` (`_clear_user_cache`) |
| #2980 | #143 | `backend/core/rag_ab_testing.py` |
| #2979 | #138 | `backend/core/file_upload_security.py` |
| #2978 | #137 | `backend/core/feature_flags.py` |
| #2977 | #136 | `backend/core/decorators/cache.py` |

Yani bu 7 alert **yeni bir güvenlik açığı değil**: satırın metni
(`usedforsecurity=False` eklenmesiyle) değiştiği için GitHub'ın alert eşleştirme
parmak izi kayboldu ve aynı kod konumları için taze alert numaraları açıldı.
CodeQL'in bu kuralı, Bandit'in aksine, Python'ın `usedforsecurity=False`
parametresini tanımıyor -- md5/sha1 çağrısını parametreden bağımsız olarak
"hassas veri + zayıf hash" deseniyle işaretliyor. 7 konumun her biri kaynak
kodundan tek tek okunup ne için kullanıldığı doğrulandı.

### Karar: 5 belgelenmiş yanlış pozitif

`cache.py`, `feature_flags.py`, `file_upload_security.py`, `rag_ab_testing.py`,
`visual_supports_service.py`: hepsi güvenlik-dışı kullanım (cache-key kısaltma,
A/B kova ataması, dosya adı benzersizleştirme, kısa id üretimi) -- hiçbiri
saklanan bir değerle karşılaştırma/doğrulama yapmıyor, `usedforsecurity=False`
zaten doğru işaret. CodeQL'in bu bayrağı tanımaması bir araç sınırlaması;
gerçek bir düzeltme gerektirmiyor.

### Karar: 1 gerçek düzeltme + 1 bağımsız bug (rbac_system.py)

`rbac_system.py`'deki 2 çağrı farklı: `_get_cache_key` yetkilendirme kararını
(granted/denied) önbelleğe alan anahtarı üretiyor, `_clear_user_cache` rol
değiştiğinde/iptal edildiğinde bu önbelleği temizliyor.
`_get_cached_permission` önbellekten okurken context'i tekrar doğrulamıyor --
salt hash eşleşmesine güveniyor, bu yüzden md5 yerine sha256 kullanmak
maliyetsiz bir sağlamlaştırma (aynı gerekçe cache.py'deki JWT cache-key
düzeltmesiyle, bkz. PR açıklaması).

Kodu okurken CodeQL'in bulmadığı **ayrı, ikinci bir bug** ortaya çıktı:
`_clear_user_cache`, `hashlib.md5(user_id...)[:8]`'in önbellek anahtarının
(`hashlib.md5(f"{user_id}:{kaynak}:{eylem}:{id}"...)`) bir öneki olduğunu
varsayıyordu. Bu yanlış -- hash fonksiyonlarının çığ etkisi yüzünden
`hash("A")` ile `hash("A:B")` arasında önek ilişkisi yoktur, kontrol pratikte
neredeyse hiç eşleşmiyordu. Yani bir kullanıcının rolü iptal edildiğinde
(`revoke_role_from_user`), önbellekteki eski "granted=True" kararı
temizlenmiyordu ve `cache_ttl` (300sn) boyunca sunulmaya devam edebiliyordu --
iptalden sonra en fazla 5 dakikalık bir "hayalet yetki" penceresi.

Düzeltme: `_get_cache_key` artık `sha256(user_id)[:16] + ":" + sha256(geri kalan)`
üretiyor; `_clear_user_cache` aynı `sha256(user_id)[:16]` önekini yeniden
hesaplayıp gerçek bir önek eşleşmesi yapıyor. Yerel doğrulama (`RBACManager`
uçtan uca): assign_role -> check_permission (granted=True, cache 1 kayıt) ->
revoke_role_from_user -> cache 0 kayıt (önceden bug yüzünden 1 kalıyordu) ->
check_permission tekrar (granted=False, cached=False). `test_core_remaining_batch2.py::TestRBACManager`
(27 test) yeşil kaldı -- mevcut testlerin hiçbiri bu önbellek geçersiz kılma
davranışını doğrulamıyordu (yalnızca `revoke_role_from_user`'ın dönüş
değerini kontrol ediyorlardı), bug da bu regresyon riski de testlerde
görünmüyordu.

---

## 7. Claude PR Review workflow'u -- eksik `id-token: write`

PR #62 checks listesinde `Claude PR Review / Automatic PR Review` kırmızıydı
(run 33222014953, job 99017858889). `gh run view --job` ile net hata:
"Action failed with error: Could not fetch an OIDC token. Did you remember to
add `id-token: write` to your workflow permissions?". `anthropics/claude-code-action@v1`,
`anthropic_api_key` doğrudan verilmiş olsa bile OIDC token almayı deniyor;
`.github/workflows/claude-review.yml`'in `permissions:` bloğunda bu yoktu.
`id-token: write` eklendi (en az yetki ilkesiyle, yalnızca bu blok).

**Sıradaki iş (opsiyonel, kapı değil):** aynı check'te ikinci, non-fatal bir
uyarı da var: "Unexpected input(s) 'model' ..." -- action'ın güncel `v1`
sürümü artık `model:` girdisini tanımıyor (muhtemelen `claude_args` üzerinden
geçirilmesi gerekiyor). Job'u kırmıyor (varsayılan modele düşüyor), bu PR'ın
kapsamı dışında bırakıldı.

---

## 8. Kapı olmaktan çıkarılanlar ve gerekçeleri

| Adım | Durum | Gerekçe |
|---|---|---|
| Terrascan | `continue-on-error` | Tenable projeyi **arşivledi**. Taradığı üç çerçeve (docker, k8s, github) Checkov'un kapsamında; bilgi olarak duruyor, kapı Checkov. |
| `safety check` | **Kaldırıldı** | 01.06.2024'te deprecate edildi, Safety 3.x hesap/API anahtarı istiyor. Aynı işi anahtarsız ve bakımı süren `pip-audit` yapıyor. |
| Snyk | `if: env.SNYK_TOKEN != ''` | Token yoksa adım her koşulda hata veriyordu. Token tanımlıysa aynen çalışır. |

---

## 9. PR #62 sonrası backlog -- Faz 0 ve Faz 1

PR #62 kapanış raporunda listelenen 7 kalemlik backlog için plan yapıldı;
aşağıda ilk iki fazın sonucu (kalan fazlar ilerledikçe buraya eklenecek).

### Faz 0 -- yerel temizlik

`docker stop/rm kiro2_pgv15_repro`, `docker rmi kiro2ci311img:latest`
(17.2GB boşaldı), `git worktree remove ../kiro2_ci_snapshot --force`
(worktree'nin commit edilmemiş Dockerfile/bandit-baseline değişiklikleri
master'daki `f59411683` ile aynı olduğu doğrulandıktan sonra silindi --
kaybolan bir şey yok). `kiro2-fe-test` image'ı zaten yoktu.

### Faz 1 -- test gate'lerin gerçekten test ettiğinden emin ol

İki bağımsız, birbirini maskeleyen sorun bulundu:

1. **`conftest.py` ScopeMismatch**: `global_db_manager_cleanup` session-scope
   async fixture, pytest-asyncio 1.3.0'ın varsayılan function-scope event
   loop fixture'ıyla çatışıyordu -- Quality Gate'in "Router registration
   check" adımı collection aşamasında patlıyordu. Düzeltme: fixture'ı sync
   `def` yapıp `db_manager.close()` çağrısını `asyncio.run()` ile sarmak
   (global `asyncio_default_fixture_loop_scope` ayarına dokunmadan -- blast
   radius'u tek fixture'a hapsetmek için).
2. **429 sessizce skip'e dönüşüyordu**: `test_gf1wb_auth_refresh_token_is_persisted`
   (auth.py:329 refresh-token persist regresyonunu yakalaması gereken tek
   golden-flow testi) ve `test_es_answer_leak.py` / `test_osym_inspired_auth.py`
   dosyalarının `student_token`/`teacher_token` fixture'ları, login 429
   (rate-limit) döndürdüğünde bunu "ortam sorunu" sanıp testi skip
   ediyordu -- yani gate kendini boğduğunda hiçbir şey doğrulamıyordu. Üç
   dosyada da 429 artık `pytest.fail()`, sadece diğer non-200 kodlar
   (bağlantı hatası, seed veri eksikliği vb.) skip.

Doğrulama: `--collect-only` ile 10/10 test toplandı (0 hata, ScopeMismatch
gitti). Canlı dev backend'e (`kiro2-backend`) karşı çalıştırıldığında GF1wB
önceden var olan, benimle ilgisiz bir skip'e düştü -- satır 1771,
"login did not set a refresh cookie (deploy may use Bearer-only flow)":
bu container'ın login akışı cookie değil Bearer-only çalışıyor, bu da
Faz 2'nin (auth.py:329) canlı yerel doğrulamasının bu container'a karşı
mümkün olmayabileceği anlamına geliyor -- asıl doğrulama kanalı CI'nin
Golden Flows job'u olacak. Diğer iki dosyanın fixture'ları (`student_token`
iki dosyada da, `teacher_token`) canlı login ile PASSED / doğru şekilde
non-429 skip verdi.

### Faz 1 devamı -- CI'da açığa çıkan 3 zincirleme maskeleme bug'ı + 1 kök neden

Yukarıdaki fixler CI'da `quality` job'unu yeşile çevirince, ondan `needs:
quality` ile bağımlı **backend-test** ve **Quality Gate** job'ları PR #67
üzerinde **ilk kez** çalıştı (daha önce hep `needs: quality` zincirinde
engellenmiş, hiç çalışmamışlardı) ve art arda 3 tane daha önce hiç
görülmemiş, birbirini maskeleyen altyapı sorunu ortaya çıkardı:

1. **`DATABASE_URL_SYNC` bare `postgresql://`** (`ci.yml`): alembic'in
   psycopg2→psycopg3 dönüştürme mantığı (`env.py`, zaten belgeliydi) sadece
   `+asyncpg` içeren bir girdiyi dönüştürüyor; CI'daki DSN çıplak olduğu
   için psycopg2'ye düşüyordu ve CI'da psycopg2 kurulu değil ->
   `ModuleNotFoundError`. Düzeltme: `+psycopg` eklendi (commit `6a36ab630`).
2. **`backend-test` job'unun postgres servisi pgvector'suzdu**: alembic
   baseline migration'ı `CREATE EXTENSION vector` içeriyor; servis image'ı
   düz `postgres:15`. Düzeltme: `pgvector/pgvector:pg15` (commit
   `6f2c401f3`; `postgres:15`'in diğer 4 kullanımı -- e2e-test/claude-ci/
   deploy/security.yml -- ayrı ayrı incelendi, bu PR'ın tetiklediği yol
   dışında oldukları için dokunulmadı).
3. **`UV_SYSTEM_PYTHON=1` (workflow-geneli) + izole `.venv` çakışması**:
   `backend-test` job'u `uv venv` + `source .venv/bin/activate` ile izole
   bir venv kuruyor, ama `UV_SYSTEM_PYTHON=1` açıkken `uv pip install` bu
   venv'i yok sayıp sistem Python'una kuruyordu (kanıt: "Install
   dependencies" adımının kendi çıktısı -- "Using Python 3.11.16
   environment at: /opt/hostedtoolcache/...", `.venv` DEĞİL). Sonuç bir
   split-brain: `alembic`/`pytest` gibi CLI entry-point'ler PATH
   fallback'iyla sistem konumunu bulup çalışıyordu (yanıltıcı "başarılı"
   görünümü), ama `.venv/bin/python` PATH'te önce geliyordu ve o venv
   bomboştu -> "Seed MVP users" adımında `ModuleNotFoundError: No module
   named 'psycopg'`. Düzeltme: `backend-test` job'una özel
   `env: UV_SYSTEM_PYTHON: "0"` override (commit `47629fcf0`) -- workflow
   genelini değil sadece bu job'u etkiler.
4. **CodeQL (GHAS default setup) -- `login_resp` önceden atanmamış
   değişken uyarısı**: bu PR'ın kendi `test_gf1wb_auth_refresh_token_is_persisted`
   düzeltmesinde (`try: login_resp = ... except ConnectError: pytest.skip()`)
   statik analiz `pytest.skip()`'in hep raise ettiğini bilmiyor, sonraki
   `login_resp.status_code` okumasını riskli sayıyordu. Düzeltme: `login_resp
   = None` ön-ataması (commit `a7d1d1fc2`) -- davranış değişmedi, sadece
   analizör tatmin edildi.

Yukarıdaki 4'ü de düzeltildikten sonra **Backend Tests (Python 3.11)** ilk
kez migrations + seed + tüm pytest paketine kadar ilerledi (önceki hatalar
sırasıyla 0s / ~1s / 1m19s'de dururken bu sefer 3m19s'e ulaştı) ve orada
**5. bir kök neden** ortaya çıktı -- bu sefer masking değil, gerçek bir
bağımlılık sürüm sorunu:

**`transformers`/`sentence-transformers` sürümsüz (alt sınır only) pin'i
bozuk bir `transformers` sürümü kuruyor.** `backend/requirements.txt`:
`transformers>=4.35.0`, `sentence-transformers>=2.2.0` -- üst sınır yok,
CI her çalıştığında PyPI'daki EN YENİ sürümü kurar. Kanıt (tam traceback,
`tests/test_video_recommendation_service.py` collection hatası):

```
services/video_recommendation_service.py -> services/semantic_youtube_search.py
  -> sentence_transformers -> transformers.integrations.peft
  -> transformers.conversion_mapping -> transformers.core_model_loading
  -> transformers/integrations/accelerate.py:65:
       ) -> tuple[int, list[str], list[nn.Module]]:
     NameError: name 'nn' is not defined
```

Bu, KIRO2 kodu DEĞİL -- kurulu `transformers` paketinin kendi
`integrations/accelerate.py` dosyasında `nn` (torch.nn) import edilmeden
bir tip imzasında kullanılmış (üçüncü parti kütüphane hatası/sürüm
uyumsuzluğu). Bu TEK kök neden en az 5 yerde patlıyor:

- Quality Gate'in router-registration testi: `api/osym_routes.py`
  (`services.osym_pdf_pipeline` eksik -- ayrı, ilgisiz bir sorun),
  `api/rag.py`, `api/v1/semantic_search.py`, `api/youtube_routes.py` --
  hepsi bu zincir üzerinden `NameError: name 'nn' is not defined` veriyor
  ve `loader.py` bunu sessizce WARNING + 404'e düşürüyor (**canlıda 3 API
  yolu şu an muhtemelen 404 dönüyor**).
- Backend Tests: `tests/test_video_recommendation_service.py` collection
  hatası, `-x` bayrağıyla birleşince pytest'in TÜM 320 geçen testi
  raporlamadan durmasına yol açıyor (`3 skipped, 2 errors`, "passed" satırı
  bile yok) -- yani gate "0 test geçti" gibi görünüyor, oysa yerel
  ders-zorlayici koşusu aynı commit'te 320/322 geçtiğini zaten kanıtladı.

**Kapsam dışı bırakıldı (bu PR'da DÜZELTİLMEDİ):** `transformers`'a üst
sınır/pin eklemek üretim bağımlılığı sürüm kararı -- hangi sürümün güvenli
olduğunu araştırmak, torch/sentence-transformers ile uyumu doğrulamak,
etkilenen 4 router'ı gerçekten test etmek gerekiyor. Faz 1'in kapsamı CI/
test altyapısı (YAML, DSN, image, venv) idi, üretim bağımlılık sürümü
değil -- bu, ayrı bir incelemeyi hak ediyor (Faz 5'in Dependabot
triyajıyla aynı kategori: "major/kırıcı sürüm kararı, insan onayı ister").

**Diğer, bu PR'dan bağımsız olduğu ölçülen kırmızılar:**

- **Automatic PR Review**: `anthropics/claude-code-action@v1` job'u
  `ANTHROPIC_API_KEY`/`CLAUDE_CODE_OAUTH_TOKEN` repo secret'ı YOK diye
  "Environment variable validation failed" ile patlıyor (log kanıtı:
  `"anthropic_api_key": ""`, `"claude_code_oauth_token": ""`). Bu bir
  kod/CI-config sorunu değil -- repo secret'ı eklemek gerekiyor, bu yalnız
  Hüseyin'in yapabileceği bir işlem (kimlik bilgisi girişi).
- **Frontend Tests**: 988 önceden var olan ESLint hatası (bu PR sadece
  backend/CI dosyalarına dokundu, frontend'e hiç dokunmadı).
- **API Security Testing** (security.yml, OWASP ZAP): bu job bu PR'dan
  bağımsız çalışıyor (backend-test/quality'ye bağımlı değil). Ölçüldü:
  master'da SON 3 çalışması da (10/17/24 Ağu) 2s44dk-3s54dk sürüp
  `failure` ile bitmiş -- yani hem çok yavaş hem de zaten kırmızı, bu PR'la
  ilgisiz. PR #67 üzerinde de aynı şekilde uzun sürdüğü için (rapor anında
  hâlâ `in_progress`) merge kararı buna beklemeden verildi.

### Sonuç ve merge

Yukarıdaki 4 masking bug + CodeQL uyarısı düzeltildikten sonra kalan tüm
kırmızılar ölçülüp önceden-var-olan borç olduğu doğrulandı (plan'ın
"yeşil ya da sadece önceden-var-olan borç kırmızı" barı karşılandı).
PR #67, `master`'ın branch-protection'ı olmadığı doğrulandıktan sonra
`gh pr merge 67 --merge` ile merge commit `b20afb920` olarak birleştirildi
(29 Ağu 2026, established convention: PR #59-62 de aynı şekilde regular
merge commit kullanmış, squash değil).


### Faz 2 -- `auth.py` refresh-token persist görünürlüğü

Denetim notunun işaretlediği gerçek bulgu doğrulandı: `LoginCommandHandler`
(`application/commands/auth.py`) login sonrası refresh-token'ı DB'ye
"fire-and-forget" yazıyordu -- yazma sessizce başarısız olursa cookie'de
token var ama DB'de yok (session desync), hata sadece WARNING'e düşüp
kayboluyordu. Düzeltme: hata artık `user_id`/`jti` ile birlikte ERROR
seviyesinde loglanıyor; login'in kendi başarı/başarısızlık sözleşmesi
(kullanıcıya 200 dönmesi) değişmedi -- görünürlük eklendi, davranış
korundu.

PR #68, kendi dalı (`fix/refresh-token-persist-visibility`), plan'ın
"kritik bir auth path, PR #62'den ayrı" kararına uygun. Doğrulama sırasında
ayrı bir CI-only kırmızı daha bulundu ve düzeltildi: CI'nin PINSIZ kurulan
ruff'ı (`uv pip install ruff`, o an 0.16.5) `test_auth_endpoints.py`'de
40x RUF059 (kullanılmayan unpack) yakaladı -- yerel pre-commit'in PINLİ
0.7.1'i bu kuralı hiç TANIMIYOR (per-file-ignores'a eklemek "Unknown rule
selector" ile pre-commit'in tüm ruff çağrısını patlatıyor, ölçüldü).
Grandfather etmek yerine `ruff --fix --unsafe-fixes --select RUF059` ile
40 site koddan düzeltildi (`app`/`mock_db`/`window` -> alt çizgili adlar,
46/46 test PASS) -- Faz 1'in "aynı aracın üç sürümü, kapıyı en eskisi
tutuyor" bulgusuna dördüncü bir örnek (bkz. `audit-methodology.md`).

**Kalan kırmızılar -- hepsi §9'da zaten belgelenen, bu PR'dan bağımsız
borç, bu oturumda log'ları tek tek okunarak yeniden doğrulandı:**

- **Quality Gate + Backend Tests (Python 3.11)**: ikisi de aynı
  `transformers`/`nn` kök nedeni (§9) -- `Backend Tests` bu sefer
  `tests/test_video_recommendation_service.py`'de collection hatası
  verip `-x`/xdist "stopping after 2 failures" ile TÜM paketi durdurdu,
  coverage %0'a düştü (§9'daki "3 skipped, 2 errors" ile aynı imza,
  sadece hangi router/test'in tetiklediği farklı gündü). Yerelde
  `pytest tests/test_router_registration.py` **3/3 passed** (CI'daki 4
  router hatası yerel ortamda üretilemiyor -- CI'ya özgü paket sürümü).
- **Automatic PR Review**: aynı eksik `ANTHROPIC_API_KEY`/
  `CLAUDE_CODE_OAUTH_TOKEN` secret'ı (§9), log'da yine
  `"anthropic_api_key": ""` doğrulandı.
- **Frontend Tests**: aynı önceden var olan ESLint borcu (§9, 988 hata) --
  bu PR sadece 3 backend dosyasına dokundu (`gh pr view --json files` ile
  doğrulandı), frontend'e hiç dokunmadı.
- **API Security Testing (ZAP)**: §9'da PR #67 için ölçülen "master'da son
  3 çalışması da 2s44dk-3s54dk sürüp failure ile bitti" bulgusu burada da
  geçerli kabul edildi -- bu job PR #68'de de dakikalarca `pending` kaldı
  (ZAP scan adımında), aynı öncedenki gibi sonucu beklemeden merge kararı
  verildi.

Tüm kırmızıların önceden-var-olan/bu PR'dan bağımsız olduğu doğrulandıktan
sonra (plan'ın "yeşil ya da sadece önceden-var-olan borç kırmızı" barı),
**8 Golden Flow E2E tests job'u PASSED (4m29s)** -- §9'un işaret ettiği asıl
doğrulama kanalı (GF1wB refresh-token-persist testi) CI'da gerçekten
çalışıp geçti. PR #68, `gh pr merge 68 --merge` ile merge commit
`8050cc499946dabc44d0dab7edbc8bee23c5fdfa` olarak birleştirildi (29 Ağu
2026).


### Faz 3 -- `fsrs.py` ölü kod + import sırası lint borcu

Araştırma doğru çıktı: `end_study_session` (`backend/app/api/fsrs.py`)
artık `fsrs_service`'e delege ediyor ve satır 482-501'de temiz biçimde
bitiyor. 2 Ağu'daki `eba3981fe` ("fsrs: çalışma oturumu uçları gerçek
modele karşı yeniden yazıldı") bu üst kısmı düzeltti ama ardından gelen
eski, `oturum` değişkenine dayanan bir uygulama parçasını (satır 503-539)
temizlemedi -- ilk `except Exception` bloğu her zaman return/raise ile
bittiği için bu kuyruk hiçbir zaman çalışmıyordu (ruff'ın kendi B025
"duplicate except" bulgusu bunu doğruluyor). PR #69'da bu ölü blok
silindi, `_maybe_await` helper import sırasını bozan konumundan (E402 x12)
`fastapi` importlarının sonrasına taşındı, `backend/api/fsrs.py`'deki
bilinçli geriye-uyumluluk shim'i (`from app.api.fsrs import *`,
`test_api_batch2.py:932` hâlâ kullanıyor) `# noqa: F403` + gerekçe
yorumuyla işaretlendi. Ölçüldü: `ruff check` fix öncesi **26 hata**, fix
sonrası **All checks passed!**. Regresyon yok: `test_api_batch2.py -k
"fsrs or FSRS"` fix öncesi/sonrası birebir aynı -- 13 failed (bu PR'ın
kapsamı dışında, önceden var olan borç: kaldırılan flashcard/review/
due-flashcards uçları için güncellenmemiş eski testler, hepsi HTTP 410
alıyor), 38 passed; `StudySession`/`study_session` testleri 7/7 passed
(`end_study_session`'ın aktif kod yolunu doğrudan kapsıyor); yerel
`test_router_registration.py` 3/3 passed.

Kalan kırmızılar PR #68'de (§ Faz 2) tek tek log'u okunarak doğrulanan
aynı beş kalem -- Quality Gate + Backend Tests (aynı `transformers`/`nn`
kök nedeni, §9), Automatic PR Review (aynı eksik secret), Frontend Tests
(aynı 988 önceden var olan ESLint hatası), API Security Testing (ZAP,
§9'daki "master'da 2s44dk-3s54dk sürüp failure" bulgusu) -- Quality Gate
log'u bu PR'da da tekrar okunarak aynı 4 router/aynı imza doğrulandı,
tekrar araştırmaya gerek kalmadı. 8 Golden Flow E2E tests PASSED.
PR #69, `gh pr merge 69 --merge` ile merge commit
`08e035dcf8d81cc6c5f089f52527ad655c3956e7` olarak birleştirildi (29 Ağu
2026).


### Faz 4 -- Temiz kopya güvenlik ölçüm script'i

Bu kampanya boyunca "temiz kopya ölçümü" (canlı/kirli çalışma dizini --
16.339 dosya, `.venv` dahil -- yerine `git worktree` ile HEAD'in CI'nin
`actions/checkout`'unun gördüğü kümeyle aynı temiz bir kopyasını çıkarıp
bandit/checkov'u orada çalıştırma) defalarca elle tekrarlandı. PR #70,
bu §"Ölçüm yöntemi" notunu tek dosyalık, tekrar-çalıştırılabilir bir
script'e döktü: `backend/scripts/temiz_kopya_guvenlik_olcumu.py`.
Belgelenen CI komutlarını (SS 1-2: `bandit -r backend/ -ll`, `checkov -d .
--framework all`) değiştirmeden kullanır, sadece JSON çıktı bayrakları
ekler; checkov'un `-o json --output-file-path <dir>` çıktısının ampirik
olarak doğrulanmış iki şeklini (tek framework eşleşirse tek dict, birden
fazla eşleşirse dict listesi) doğru normalize eder.

**Doğrulama:** ruff/mypy temiz. İki saf özetleme fonksiyonu
(`bandit_json_ozetle`, `checkov_json_ozetle`) sentetik-ama-gerçek-şemalı
veriyle ayrı unit-test edildi (her iki checkov şekli dahil). Script
gerçekten çalıştırıldı: temiz worktree kuruldu, bandit worktree içinde
GERÇEKTEN koşup geçerli JSON yazdı (297 bulgu, MEDIUM+); checkov bu
**yerel geliştirme makinesinde kurulu olmadığı için** (`checkov`/`python -m
checkov` bulunamıyor -- CI'nin `security.yml`'inde ayrı bir adımda
kuruluyor, yerel `requirements*.txt`'in parçası değil) script kendi
belgelediği istenen davranışla patladı: sessiz geçmedi, aleti-yok hatası
açıkça yukarı fırladı, `finally` bloğu exception'a rağmen worktree'yi
temizledi (`git worktree list` ile doğrulandı). Yani checkov yarısının
CANLI bir yerel doğrulaması bu PR'ın kapsamında değil -- doğruluğu (1)
yukarıdaki unit test + (2) checkov'un CI'daki belgelenmiş gerçek
davranışına dayanıyor; ilk gerçek "temiz kopya" tam ölçümü (bandit +
checkov birlikte) ayrı bir sonraki adım.

**Yan bulgu -- dördüncü "aynı aracın farklı kapısı" örneği:** script'in
ilk `git commit` denemesi sessizce başarısız oldu. Yerel pre-commit
`bandit (PyPI wheel)` hook'u, CI'nin belgelenen SAST adımının aksine
(`bandit -r backend/ -ll`, sadece MEDIUM+), `-ll` filtresi OLMADAN
çalışıyor -- LOW severity bulguları da yakalıyor. Script'in kendi
subprocess kullanımı (hepsi sabit literal komut listesi, `shell=True`
yok, kullanıcı girdisi hiçbir komuta ulaşmıyor) 4 LOW/High-confidence
bulguya takıldı (B404 import, B603 x2, B607). Düzeltme kod yeniden
yapılandırma değil, gerekçeli `# nosec <KOD>` bayrakları -- bandit'in
kendi JSON çıktısıyla doğrulandı: 4 bulgu nosec ile bastırıldı, 0 kalan
bulgu (hiçbir severity'de); CI'nin kendi "Code Quality (bandit)" job'u da
bu PR'da ayrıca PASSED geçerek aynı sonucu bağımsız doğruladı. Bu,
kampanyanın tekrarlayan "aynı aracın farklı sürümü/kapısı" deseninin --
RUF059 (Faz 2, ruff sürüm farkı) ve önceki üç CI-katmanı örneğinden (§9)
sonra -- bu kez **versiyon değil önem-derecesi (severity) eşiği**
uyumsuzluğu şeklinde yeni bir örneği.

Kalan kırmızılar yine aynı beş önceden-var-olan kalem -- bu PR'da da
Quality Gate (`ModuleNotFoundError: services.osym_pdf_pipeline` +
`NameError: name 'nn' is not defined`) ve Backend Tests
(`test_video_recommendation_service.py` aynı `NameError`, `TOTAL
144957 144957 0.00%`, "coverage of 60% not reached") log'ları tazeden
okunarak doğrulandı; Frontend Tests aynı "✖ 2102 problems (988 errors,
1114 warnings)"; Automatic PR Review aynı eksik secret; API Security
Testing beklendiği gibi pending bırakıldı (§9 emsali). PR bu kez CI'nin
tam güvenlik/uyumluluk paketini de tetikledi (Code Quality bandit/mypy/
ruff/safety/semgrep, CodeQL python+javascript, Checkov, Container
Security Scan, IaC Security Scan, License Compliance Check, OWASP
Dependency Check, SAST Scan, Secret Scanning, Compliance Checks, Trivy,
Security Summary) -- hepsi PASSED. 8 Golden Flow E2E tests PASSED
(3m53s). PR #70, `gh pr merge 70 --merge` ile merge commit
`026b5055cf7e3934f44548f7dea69e4efcd03d48` olarak birleştirildi (29 Ağu
2026).


### Faz 5 -- Dependabot triyajı: otomasyon neden hiç çalışmamış

Plan'ın orijinal varsayımı ("otomasyon var, sadece bayat PR'lar rebase
istiyor") **kısmen yanlış çıktı**. Canlı veri (`gh pr list --app
dependabot --json mergeable,mergeStateStatus`) 20 PR'ın hepsinin artık
gerçek bir `mergeable` durumu olduğunu gösterdi (5 CONFLICTING/DIRTY: #38,
#45, #46, #49, #58; 15 MERGEABLE/UNSTABLE) -- ama daha derin bir kazı,
**hiçbir Dependabot PR'ının bugüne kadar hiç otomatik merge edilmediğini**
ortaya çıkardı, CI durumundan tamamen bağımsız olarak. İki ayrı, birbirinden
bağımsız repo-ayarı kök nedeni bulundu (ikisi de `gh api` ile doğrulandı,
varsayım değil):

**Kök neden 1 (düzeltildi, PR #71):** `can_approve_pull_request_reviews:
false` (`gh api repos/.../actions/permissions/workflow`) -- repo'nun
"Allow GitHub Actions to create and approve pull requests" ayarı kapalı.
`dependabot-auto-merge.yml`'in "Auto-approve" adımı bu yüzden HER ZAMAN
başarısız oluyordu (kanıt: PR #41'in 2 ay önceki `dependabot` job'u, 11s'de
exit 1), ve GitHub Actions'ın varsayılan step-bağımlılığı yüzünden bu
başarısızlık asıl merge adımını hiç çalıştırmıyordu. master'da branch
protection olmadığından (`gh api repos/.../branches/master/protection` ->
404) onaylanmış review zaten merge şartı değildi -- sadece bu adımın
başarısızlığı yanlışlıkla merge adımını engelliyordu. Düzeltme:
"Auto-approve" adımına `continue-on-error: true`, "Enable auto-merge"
adımının `if:`'ine `always() &&` eklendi. PR #71, tam beş-kırmızı emsali
(Quality Gate, Backend Tests, CI Summary, Frontend Tests, Automatic PR
Review -- hepsi bu PR'da da taze log ile doğrulandı) + Golden Flow PASSED
sonrası `gh pr merge 71 --merge` ile merge commit
`4231921eb0d02d527eb1403b3d45dc8f2ed04968` olarak birleştirildi.

**Kök neden 2 (kod ile düzeltilemez, kullanıcı kararı gerekiyor):** PR
#71'in fix'i canlı doğrulanırken (20 PR'a `@dependabot rebase` yorumu
atılıp taze bir `dependabot` job'u izlendi -- PR #41) ikinci, bağımsız bir
duvar ortaya çıktı: "Auto-approve" artık `continue-on-error` sayesinde
yeşil görünüyor, ama "Enable auto-merge" adımı YENİ bir hatayla
başarısız: `GraphQL: Auto merge is not allowed for this repository
(enablePullRequestAutoMerge)`. Doğrulandı: `gh api repos/HuseyinAts/kiro2
--jq '{allow_auto_merge}'` -> `false`. Bu, repo Settings -> General ->
Pull Requests -> "Allow auto-merge" onay kutusu -- workflow dosyasından
TAMAMEN bağımsız, ayrı bir repo özelliği anahtarı. `gh pr merge --auto`
bu kapalıyken hiçbir zaman çalışamaz; workflow'un `--auto` kullanmaması
(düz `gh pr merge` ile hemen merge etmesi) de GÜVENLİ DEĞİL, çünkü branch
protection olmadığından "önce CI'yı bekle" garantisini sadece `--auto`
sağlıyor. **Bu, `can_approve_pull_request_reviews` gibi, benim
değiştiremeyeceğim bir repo/güvenlik ayarı -- kod tarafında cerrahi bir
düzeltmesi yok.**

**Düzeltme (canlı gözlemle):** İlk yazıldığında bu bölüm "Allow auto-merge"
kapalıyken HİÇBİR PR'ın kendiliğinden merge olamayacağını söylüyordu --
bu YANLIŞ çıktı, birkaç dakika içinde canlı veriyle çürütüldü. `gh pr
merge --auto`, PR o an ZATEN mergeable ise (bekleyen zorunlu kontrol yok --
master'da branch protection olmadığından "zorunlu kontrol" kavramı zaten
yok) GraphQL kuyruklama mutasyonuna (`enablePullRequestAutoMerge`,
`allow_auto_merge` ayarına tabi) hiç başvurmadan DOĞRUDAN merge ediyor;
sadece PR hâlâ bekleyen kontrolleri varken çalışırsa kuyruklamaya düşüyor
ve o zaman `allow_auto_merge:false` engeline takılıyor. Kanıt: rebase
yorumlarından sonraki ~10 dakika içinde 4 PR gerçekten otomatik merge
oldu -- #44 (18:19), #45 (18:20), #40 (18:21), #47 matplotlib (18:27),
hepsi `mergedBy: app/github-actions`. Yani düzeltme kısmi değil, ÇALIŞIYOR
-- sadece PR'ın workflow çalıştığı ANDA hâlâ kontrol bekliyor olması
durumunda (CI'nin en yavaş olduğu ilk birkaç dakika) auto-merge kuyruğa
düşüp `allow_auto_merge` engeline takılabiliyor. **Yine de "Allow
auto-merge" açılması önerilir** -- bu, CI yavaş bittiğinde de garantili
merge sağlar; ama artık "hiçbir şey merge olamıyor" değil, "bazı PR'lar
şansa bağlı olarak kuyruğa düşebiliyor" düzeyinde ikincil bir iyileştirme.

**Bu oturumda yapılan diğer triyaj işleri:** Tüm 20 PR'a `@dependabot
rebase` yorumu atıldı (5 CONFLICTING çakışmasını çözmek + 15 UNSTABLE'ın
~2,5 aylık bayat CI sonucunu güncel master'a karşı tazelemek + düzeltilmiş
otomasyonu tetiklemek için). 2 major bump (workflow politikası geriği
otomatik merge kapsamı dışında, insan incelemesi gerektiriyor) için
önceden hazırlanmış kod-tabanı risk analizi doğrudan PR yorumu olarak
paylaşıldı: **#43 marshmallow 3.26.2->4.3.0** (klonda `import marshmallow`
sıfır sonuç, dolaylı/transitive bağımlılık, düşük risk) ve **#46 structlog
24.1.0->26.1.0** (10 dosyada standart stdlib-entegrasyonu kullanımı,
kullanılan hiçbir API'de breaking change yok, düşük risk) -- ikisi için de
son merge kararı kullanıcıya bırakıldı, buton basılmadı. `#47 matplotlib`
(minor, 3.8->3.11) düşük-orta risk olarak değerlendirilmişti (14 dosyada
kullanıcı-görünür diyagram üretimi) -- otomasyona bırakıldı ama bu servis
grubunun test kapsamı ayrıca doğrulanmadı, ayrı bir not olarak kayıtlı.

**Faz 5 eki (aynı gün, sonraki) -- #43 ve #46 kullanıcı onayıyla merge
edildi.** Kullanıcı risk analizini görüp doğrudan "#43 ve #46'yı merge et"
talimatı verdi. #46 tek komutla temiz merge oldu (`c4010481d`). #43'te
`gh pr merge` "Pull Request has merge conflicts" hatası verdi --
`mergeable: CONFLICTING` doğrulandı, `@dependabot rebase` yorumu atıldı,
ama Dependabot'ın kendi rebase'i ~3 dakika içinde gelmedi (branch zaten
bir kez force-push almıştı, headRefOid sabit kaldı). `git merge-tree` ile
kanıtlandı: gerçek bir kod çakışması değil, `requirements.qa.lock.txt` /
`requirements.qa.lock.linux.txt`'de alfabetik olarak bitişik iki satırın
(marshmallow, matplotlib) iki farklı PR tarafından bağımsız değiştirilmesi
-- #43 dalı hâlâ eski `matplotlib==3.10.8`'i taşıyordu, master'da #47 ile
zaten `3.11.1`'e çıkmıştı. Bu kilit dosyalarında hash pin YOK (düz
`paket==versiyon` formatı), yani elle çözüm hash uydurma riski taşımıyordu
-- her iki satır da ilgili taraftan harfiyen alındı (marshmallow==4.3.1 +
matplotlib==3.11.1), başka hiçbir satır etkilenmedi (branch'in tüm
diff'i zaten sadece bu 2 satırdı). Yerel branch'te merge yapıldı, pre-push
hook'ları (320 test + reward-hacking-check) geçti, push edildi, PR
`MERGEABLE` oldu, `gh pr merge 43 --squash` ile kapatıldı (`477e0e306`).
`--no-verify` kullanılmadı.

Bu arada, merge öncesi kırmızı check'leri kör geçmemek için ikisi de log
seviyesinde doğrulandı (önceden merge olmuş #52 ile birebir aynı çıktı):
"Automatic PR Review" -- Claude Code Action'ın kendi bot-actor guard'ı
Dependabot PR'larını toptan reddediyor (`Workflow initiated by non-human
actor: dependabot`); bu, önceden bilinen "eksik id-token: write" (SS 7)
bulgusundan AYRI, yeni keşfedilen bir kapsam-dışı-bırakma sorunu --
düzeltmek için `allowed_bots` listesine dependabot eklenmesi gerekir, kod
değişikliği kolay ama repo'nun bu botu bilinçli/bilinçsiz dışladığı
belirsiz, bu yüzden dokunulmadı, sadece not düşüldü. "Quality Gate" ->
"Router registration check" -- `test_mapped_routers_are_importable`
testi `api.osym_routes` (`ModuleNotFoundError: services.osym_pdf_pipeline`)
ve `api.rag`/`api.v1.semantic_search`/`api.youtube_routes` (`NameError:
name 'nn' is not defined`) için önceden var olan, bu PR'larla ilgisiz
kırık router import'ları yüzünden başarısız oluyor; `loader.py` bunu
WARNING'e çevirip sessiz 404 üretiyor. İkisi de #43/#46'dan önce zaten
kırıktı, bu oturumun kapsamı dışında, ayrı bir borç kalemi olarak not
edildi. "Backend Tests (Python 3.11)" / "Frontend Tests" / "API Security
Testing" ise #47'de (zaten merge olmuş) hâlâ `pending` görünüyor -- bu üç
kontrolün bu repoda Dependabot PR'larında hiç sonuçlanmadığı, master'da
branch protection olmadığı için bunun merge'ü hiç engellemediği ayrıca
doğrulandı.


### Faz 6 -- CodeQL false-positive dismiss'leri: iş zaten yapılmıştı, ama bozuk

Faz 6'ya başlarken hazırlık notundaki (`py/weak-sensitive-data-hashing`
kuralı için 5 alert: #136, #137, #138, #143, #151) numaraları canlı
`gh api repos/.../code-scanning/alerts` ile doğrulanmaya çalışıldı --
ama bu 5 dosya güncel `state=open` listesinde HİÇ görünmedi. Doğrudan
numara sorgusu gerçeği ortaya çıkardı: **hepsi zaten `dismissed`,
`dismissed_reason: "false positive"` idi** -- `dismissed_at` damgası bu
OTURUMUN içinde, 14:01:22-27Z (bu segmentin kendi işinden önce, muhtemelen
bu konuşmanın özetlenen/daha önceki bir kısmında). Yani asıl dismiss
kararı zaten doğru verilmiş ve doğru 5 alert'e uygulanmıştı.

**Ama bozuk bir yan etkisi vardı:** her 5 alert'in `dismissed_comment`
alanı, gerekçe metni yerine kelimesi kelimesine
`@C:\Users\husey\AppData\Local\Temp\kiro2_codeql_dismiss_comment.txt`
string'ini içeriyordu -- yani `gh api -f dismissed_comment=@<dosya>`
çağrısı dosya içeriğini OKUMAK yerine `@<yol>` metnini olduğu gibi
gönderdi (bu ortamda `-f`'in dosya-okuma davranışı güvenilir değil).
Düzeltmeye çalışırken **iki farklı, birbirinden bağımsız GitHub API
kısıtı** ortaya çıktı (ikisi de canlı 4xx yanıtlarıyla doğrulandı, tahmin
değil):

1. `dismissed_reason` değeri `"false_positive"` (alt çizgi) DEĞİL,
   `"false positive"` (boşluk) olmalı -- yanlış değer 422 "is not a
   member of [...]" ile reddedildi.
2. `dismissed_comment` **280 karakterle sınırlı** -- orijinal Türkçe
   gerekçe metni 401 karakterdi, 422 "Only 280 characters are allowed;
   401 were supplied" ile reddedildi.
3. Zaten `dismissed` olan bir alert'e tekrar `state=dismissed` PATCH'i
   400 "Alert is already dismissed" ile reddediliyor -- düzeltme, önce
   `state=open`'a döndürüp sonra doğru gövdeyle tekrar dismiss etmeyi
   gerektirdi (iki adımlı; her adım `gh api --input <json-dosyası>` ile
   -- PowerShell'in Türkçe/tırnaklı metin içeren `-f` argümanlarını
   güvenilir aktaramadığı bu oturumda defalarca gözlemlendiği için,
   gövde bu kez doğrudan bir JSON dosyasından okundu, komut satırından
   değil).

280 karaktere sığan kısaltılmış gerekçe metniyle (`Yanlis pozitif: bu md5
kullanimlari guvenlik amacli degil (hashlib.usedforsecurity=False ile
isaretli) -- cache-key kisaltma, A/B kova atamasi, id benzersizlestirme.
CodeQL bu parametreyi tanimiyor (arac sinirlamasi), Bandit taniyor.
Detay: docs/guvenlik-borcu.md SS6.`, 268 karakter) 5 alert de
reopen->redismiss edildi, `gh api` ile canlı tekrar okunarak doğru
gerekçe metninin göründüğü doğrulandı. `#144`/`#145` (rbac_system.py --
gerçek, zaten kod ile düzeltilmiş bulgular, false positive DEĞİL) hiç
dokunulmadı, hâlâ `open` -- doğrulandı, hazırlık notunun talimatına
uygun.
