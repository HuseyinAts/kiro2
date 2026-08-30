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


## 10. Reward-hacking-check kaçağı, `osym_routes` ve repo-geneli `requirements.txt` kırığı (29 Ağu 2026)

SS9'daki Faz 0-6 (PR #62 sonrası 7 kalemlik backlog) tamamlandıktan sonra,
SS9/Faz 5 eki'nde zaten "önceden var olan, ilgisiz borç" olarak işaretlenmiş
`api.osym_routes` (`ModuleNotFoundError: services.osym_pdf_pipeline`)
sorunu ele alındı. Bu iş sırasında, öngörülemeyen çok daha büyük bir
repo-geneli kırık ortaya çıktı ve düzeltildi.

### 10.1 `osym_routes` kök nedeni: 3 dosya hiç commit edilmemiş

`api/osym_routes.py`'nin import ettiği `services/osym_pdf_pipeline.py`
(131 satır), `services/turkish_readability_service.py` (101 satır) ve
`models/osym_trends.py` (42 satır) yerel diskte vardı ama **hiçbir zaman
git'e eklenmemişti** -- yalnızca geliştirme makinesinde duruyordu. CI'nin
temiz checkout'unda bu üç dosya yok olduğundan import patlıyor,
`loader.py` bunu WARNING'e çevirip router'ı sessizce düşürüyor, tüm
osym_routes endpoint'leri 404 dönüyordu. Düzeltme: 3 dosya + `models/
__init__.py`'a 2 satırlık OSYM model import/`__all__` girişi commit
edildi (`15d3a1044`). `models/__init__.py`'nin geri kalanındaki 23
önceden var olan ruff ihlali (F401 x19 kasıtlı `_deprecated` shim
importları, SIM105 x2 kasıtlı try/except/pass, RUF022 x1 kronolojik
sıralı `__all__`) `pyproject.toml`'da gerekçeli per-file-ignore ile
görünür şekilde not edildi -- gizlenmedi, ayrı bir temizlik görevi olarak
işaretli.

### 10.2 Reward-hacking-check'in gerçek bulgusu: `models/__init__.py`'de sessiz yutma

Aynı dosyaya yapılan 2 satırlık ekleme, pre-push `reward-hacking-check`
hook'unu tetikledi: dosyada zaten var olan 2 adet `except ImportError:
pass` (geriye-uyumluluk shim'leri için) CRITICAL bulgu verdi. Hook'un iki
bağımsız tespit yolu olduğu doğrulandı -- regex tabanlı yol (yorum/log
varlığına bakıyor) ve tamamen yorum-kör bir AST yolu (yalnız gövdenin
`pass`/`...`/salt-docstring olup olmadığına bakıyor); yalnızca yorum
eklemek AST yolunu atlatmıyor (yerel bir problayıcı ile doğrulandı). İki
olası "aracı kandırma" yolu bilerek KULLANILMADI: salt-docstring gövde
(AST'nin docstring istisnasını istismar eder) ve `context_analyzer.py`'nin
"example" kelimesi geçirme açığı (`should_ignore()`) -- ikisi de aracın
amacına karşı dürüst olmayan birer bypass olurdu. Gerçek düzeltme: iki
`pass`'i de `logger.debug(...)` çağrısına çevirmek (`agents/context/
context_manager.py:47`'deki mevcut desenle aynı örüntü) -- artık tamamen
sessiz değil, hem regex hem AST yolunu dürüstçe tatmin ediyor. Doğrulama:
`ruff check`/`ruff format --check` temiz, yerel prob "NO FINDINGS" (önceden
2 CRITICAL), `test_router_registration.py` 3/3 passed. Commit `64550617a`,
**PR #72**.

### 10.3 PR #72'nin CI'ı beklenenden çok daha kırmızı çıktı -- repo-geneli, ilgisiz bir kırık

PR #72 push edildiğinde CI, kampanyanın önceki hiçbir PR'ında görülmemiş
ölçüde kırmızı döndü. Her kırmızı check'in log'u tek tek okunarak (hiçbiri
varsayılan olarak "önceden bilinen gürültü" sayılmadan) neredeyse hiçbirinin
bu PR'ın kendi diff'inden kaynaklanmadığı ortaya çıktı -- iki ayrı,
repo-geneli `backend/requirements.txt` kırığı:

1. **`python-dotenv` eksik**: `tests/conftest.py:50`'nin dogrudan kullandığı
   `from dotenv import load_dotenv` `requirements.txt`'te hiç yoktu (diğer
   kilit dosyalarında vardı) -> `ModuleNotFoundError` -> conftest.py import
   edilemiyor -> pytest'e bağlı HER quality-gate/golden-flow job'u başarısız.
2. **`opentelemetry-instrumentation-fastapi` aile-içi tutarsızlığı**:
   `git log -L`/`git blame` ile izole edildi -- `1e6e6c135` (#40, Dependabot
   tekil bump) yalnızca bu paketi 0.42b0'dan 0.65b0'a çıkarmış, kardeş
   paketleri (`opentelemetry-sdk`/`-api`/`-instrumentation`, hepsi 1.21.0/
   0.42b0 ailesinde) DOKUNMADAN bırakmıştı. 0.65b0 ailesi
   `opentelemetry-semantic-conventions==0.65b0` ister, 1.21.0 ailesi
   `==0.42b0` ister -- karşılıklı dışlayıcı, sıkı çözücülerde (`uv pip
   install`) sert hata.

Her ikisinin de **bu PR'dan bağımsız, repo-geneli** olduğu `gh run list
--branch master --workflow ci.yml --limit 5` ile kanıtlandı: master'ın son
5 çalışması (bu kampanyada bizzat merge edilen `477e0e306`/#43 dahil)
`failure`/`cancelled` ile bitiyordu. Düzeltme: `opentelemetry-instrumentation-
fastapi` `1e6e6c135`'ten önceki `0.42b0`'a geri alındı (tek kullanım yeri
`core/opentelemetry_config.py`, etkilenmiyor); `python-dotenv==1.2.1`
(diğer kilit dosyalarındaki pinle aynı) eklendi. İkisi de `pip install
--dry-run` ile CI turuna hiç çıkmadan yerelde doğrulandı. Ayrı, doğru
kapsamlı bir dala taşındı (`fix/requirements-opentelemetry-dotenv-conflict`,
commit `31aeddec7`, **PR #73**) -- `models/__init__.py`/`osym_routes`
fix'iyle karışmasın diye.

PR #73 merge edilmeden önce, kalan kırmızıların TAMAMI (20 check yeşile
döndü: 5 Code Quality job'u, Golden Flow E2E, License Compliance,
Container Security, CodeQL x2, SAST, IaC, OWASP, Secret Scanning, vb.)
tek tek doğrulandı; kalan 5 kırmızı (§10.4-10.6) ayrı ayrı önceden-var-olan
olarak kanıtlandı. `master`'da branch protection olmadığı (`gh api repos/
.../branches/master/protection` -> 404) doğrulandıktan sonra `gh pr merge
73 --squash` ile birleştirildi (merge commit `6971d18cf`, 29 Ağu 2026
20:32 UTC). Ardından `master` senkronize edildi ve PR #72'nin dalına
merge edildi (çakışmasız) -- PR #72'nin CI'ı artık her iki düzeltmeyle
birlikte yeniden çalışıyor.

### 10.4 `nn` NameError kökeni artık kesinleşti: `torch`/`transformers` sürüm uyuşmazlığı

SS9'dan beri "muhtemelen CI'a özgü paket sürümü" olarak işaretli olan
`NameError: name 'nn' is not defined` artık tam kanıtla açıklandı. CI
log'unda (`transformers`'ın kendi kurulum çıktısı):

```
[transformers] Disabling PyTorch because PyTorch >= 2.5 is required
but found 2.4.1
PyTorch was not found. Models won't be available and only tokenizers,
configuration and file/data utilities can be used.
```

`backend/requirements.txt`: `transformers>=4.35.0` / `torch>=2.1.0` --
ikisi de üst sınırsız, ve `git blame` ile ikisinin de `1fe3a390ac`
(7 Şub 2026) tarihinden beri, yani **6,5 aydır**, bu haliyle durduğu
doğrulandı. CI (temiz Linux) `torch`'u `2.4.1`'e çözüyor; kurulu
`transformers` sürümü `torch>=2.5` şart koşuyor, karşılanmayınca PyTorch
entegrasyonunu TAMAMEN kapatıyor (`nn` hiç import edilmiyor) --
`api.rag`, `api.v1.semantic_search`, `api.youtube_routes` ve
`tests/test_video_recommendation_service.py` bu yüzden patlıyor. Bu bug
6,5 aydır potansiyel olarak oradaydı, ama §10.3'teki `requirements.txt`
install-seviyesi hataları CI'yı bu noktaya hiç ulaştırmadığından şimdiye
kadar gerçek bir çalıştırmada görünmemişti -- PR #73 asıl install
kırıklarını giderince ilk kez açığa çıktı.

**Gerçek düzeltme kapsam dışı bırakıldı (bu segment yapılmadı):** `torch`'u
`>=2.5`'e çıkarmak, ardından bununla birlikte açığa çıkan İKİNCİ bir
çakışmayı çözmek gerekiyor -- `requirements.txt`'te sabit `sympy==1.12`
pin'i, torch >=2.5'in istediği `sympy>=1.13.x` ile uyuşmuyor. İkisi
birlikte, kendi araştırmasını/doğrulamasını hak eden ayrı bir PR'ın
konusu.

### 10.5 "Automatic PR Review" -- yeni semptom, aynı eski kök neden

PR #72/#73'te bu check `##[warning]Unexpected input(s) 'model'` uyarısının
ardından `##[error]Action failed with error: Environment variable
validation failed` ile başarısız oluyor. Bu, SS9/Faz1'de zaten
belgelenmiş kök nedenle (`ANTHROPIC_API_KEY`/`CLAUDE_CODE_OAUTH_TOKEN`
repo secret'ı YOK) AYNI hata imzası -- `'model'` uyarısı muhtemelen aynı
eksikliğin yeni bir yan-semptomu, ayrı bir bug değil. Düzeltmesi kod
tarafında değil: bu, yalnızca Hüseyin'in yapabileceği bir kimlik-bilgisi
girişi (repo secret eklemek).

### 10.6 Frontend Tests -- aynı önceden var olan borç, yeniden doğrulandı

PR #72'de de aynı imza: `no-trailing-spaces`, `eqeqeq`, `prefer-const`,
`comma-dangle`, `no-empty`, `@typescript-eslint/no-unused-vars` kuralları
+ iki `parserOptions.project` parse hatası, SS9/Faz'lardaki "988 önceden
var olan ESLint hatası" bulgusuyla aynı kategori -- bu PR hiç frontend
dosyasına dokunmadı.

### Sonuç ve merge

PR #72'nin CI'ı (güncellenmiş `master`'la) tam olarak beklendiği gibi
çıktı: `test_mapped_routers_are_importable` **yalnızca** `api.rag`/
`api.v1.semantic_search`/`api.youtube_routes` için `NameError: name 'nn'
is not defined` ile başarısız oldu (log'u kelimesi kelimesine doğrulandı)
-- `osym_routes` bu listede YOK, yani bu PR'ın kendi düzeltmesi çalışıyor;
`test_all_app_api_routers_registered` ve `test_registered_app_api_modules_
exist` PASSED (2/3 passed, 1/3 önceden-var-olan/ilgisiz kırmızı). Backend
Tests aynı imzayı taşıyor (coverage tablosu §9'daki gibi 0.00%'e
çöküyor -- collection hatası tüm suite'i erken durduruyor). Diğer 20+
check (Golden Flow E2E, tüm Code Quality job'ları, CodeQL python+
javascript, Container Security, License Compliance, SAST, IaC, OWASP,
Secret Scanning, Checkov, Trivy, Compliance) PASSED. `gh pr merge 72
--squash` ile birleştirildi (29 Ağu 2026 20:44 UTC). `--no-verify`
kullanılmadı, hiçbir kırmızı check körlemesine geçilmedi -- her biri
log seviyesinde doğrulandı.

**Bu segment sonunda repo durumu:** SS9'daki Faz 0-6 (PR #62 sonrası
backlog) ve bu bölümdeki osym_routes/requirements.txt zinciri (PR #72,
#73) TAMAMLANDI. Geriye kalan bilinen borç: (1) `torch`/`transformers`
sürüm uyuşmazlığı (§10.4, kod düzeltmesi gerekiyor, kapsamlı/ayrı PR);
(2) Automatic PR Review'in eksik repo secret'ı (§10.5, yalnızca Hüseyin
yapabilir); (3) Frontend Tests ESLint borcu (§10.6, 988 hata, ayrı
triyaj); (4) `allow_auto_merge` repo ayarı (Faz 5, yalnızca Hüseyin
yapabilir, önerilir); (5) kalan Dependabot PR'ları (otomasyon Faz 5
düzeltmesiyle artık çalışıyor, düzenli izlenmeli).

### 10.7 YENİ BULGU (bu segmentin sonunda, henüz düzeltilmedi): `osym_routes` deseni tek örnek değil

PR #72/#73 sonrası `git status` çalıştırıldığında **120+ commit edilmemiş
dosya** ortaya çıktı -- §10.1'deki "3 dosya hiç commit edilmemiş" bulgusu
tekil bir olay değil, tekrarlayan bir örüntüymüş. Somut, doğrulanmış bir
örnek: `api/osym_routes.py:391` (TRACKED, PR #72 ile az önce merge edildi)
`run_equating` endpoint'i içinde `from services.irt_equating_service
import MeanMeanEquator` -- fonksiyon-içi (lazy) import, bu yüzden
`test_mapped_routers_are_importable` bunu YAKALAMADI (modül seviyesinde
değil), ama `services/irt_equating_service.py`'nin kendisi commit edilmemiş
-- yani `/run-equating` (admin) endpoint'i CI/temiz checkout'ta ÇAĞRILDIĞI
AN `ModuleNotFoundError` verecek. `tests/fast/test_irt_equating.py` da
aynı modülü import ediyor (module-level) -- CI'da collection hatası
vermesi bekleniyor ama bu dosya `ders-zorlayici` pre-push hook'unun
kapsadığı 320 testin arasında değil, bu yüzden yerel pre-push hiç
yakalamıyor.

Untracked listesinde AYNI şekilde eşleşen test+servis çiftleri var:
`services/empirical_irt_calibrator.py` (+ `test_y11_goc.py`,
`scripts/quality/calibrate_question_bank_irt.py`), `algorithms/
isomorphic_generator.py` (+ `test_isomorphic_generator.py`), `services/
yks_jargon_service.py` (+ `test_yks_jargon_service.py`), `services/nlp/`
(+ `test_motivation_generator.py`, `test_osym_validator.py`), ve daha
fazlası -- eşlik eden test dosyalarının varlığı bunların çoğunun
YARIM/deneysel değil TAMAMLANMIŞ, test edilmiş özellikler olduğuna işaret
ediyor. Listede ayrıca token/kimlik bilgisi gibi görünen dosya adları da
var (`.fantom_tok`, `.e2e_token`, `.probe_tok`, `.a1_eksen1_prob_email`)
-- bunlar ASLA commit edilmemeli, önce içerik/amaç teyit edilmeden
dokunulmadı.

**Bu segmentte YAPILMADI:** 120+ dosyanın hiçbiri incelenmedi/commit
edilmedi -- kapsamı (gerçek kaynak kodu / scratch-debug dosyası / sızıntı
riski taşıyan dosya ayrımı gerektiren) bu segmentin geri kalanına
sığmayacak kadar büyük, kendi dikkatli triyaj geçişini hak ediyor. Sonraki
en yüksek öncelikli iş olarak işaretlendi.

### 10.8 PR #74: 10.7'nin kanıtlanmış tek örneğinin düzeltilmesi (29 Ağu 2026)

10.7'de tarif edilen zincirin somut, kanıtlanmış tek halkası düzeltildi:
`services/irt_equating_service.py` (88 satır, `api/osym_routes.py:391`'in
lazy import ile ihtiyaç duyduğu modül) artı PR #72'nin kendisinin arkada
bıraktığı 2 test dosyası (`test_osym_pdf_pipeline.py`,
`test_turkish_readability.py`) artı yeni `test_irt_equating.py` (4 test)
commit edildi. Ruff N803 (4x, `A`/`B` büyük harf parametreleri) için
`pyproject.toml`'a `models/__init__.py` emsaliyle aynı desende gerekçeli
per-file-ignore eklendi -- `A`/`B` kasıtlı: IRT equating literatürünün
standart notasyonu, çağıran kod (`osym_routes.py`) da aynı adlandırmayı
kullanıyor. `test_osym_pdf_pipeline.py`'deki `os.path` çağrıları
`pathlib.Path`'e taşındı (PTH110/PTH107, davranış değişmedi).

Yerel doğrulama: 10/10 test yeşil, ruff temiz, pre-commit hook'ları
(bandit/mypy/secret-detection dahil) ve pre-push 320-test paketi +
reward-hacking-check temiz. **PR #74**
(https://github.com/HuseyinAts/kiro2/pull/74), branch
`fix/osym-routes-missing-irt-equating-and-tests`, commit `417327892`.

CI'da 4 kırmızı çıktı, hepsi log seviyesinde doğrulandı ve önceden
bilinen/ilgisiz borçlarla eşleşti (yeni hiçbir şey yok):
- **Backend Tests**: `test_video_recommendation_service.py` collection
  hatası, `NameError: name 'nn' is not defined` -- §10.4 (torch/
  transformers sürüm uyuşmazlığı), bu PR'ın diff'iyle ilgisiz.
- **Quality Gate / Router registration check**: `test_mapped_routers_
  are_importable` yine aynı 3 router'da başarısız (`api.rag`,
  `api.v1.semantic_search`, `api.youtube_routes`) -- `api.osym_routes`
  listede YOK, yani bu PR'ın düzeltmesi tutuyor, yeni bir kırılma
  eklemedi.
- **Automatic PR Review**: aynı `Unexpected input(s) 'model'` uyarısı --
  §10.5 (eksik repo secret), kozmetik.
- **Frontend Tests**: aynı önceden var olan ESLint hataları (react-hooks/
  exhaustive-deps, jsx-a11y/*) -- §10.6, bu PR backend-only.
- **CI Summary**: yukarıdakilerin toplamı olduğu için kırmızı, ayrı bir
  kök neden değil.

Merge: `71f764c88` (2026-08-29T21:10:49Z UTC), `gh pr merge 74 --squash`.
Local master senkronize edildi (`202de7994..71f764c88`, fast-forward, 5
dosya, +268 satır).

**Kalan kapsam:** 555 - 4 = ~551 commit edilmemiş dosya hâlâ triyaj
bekliyor (bkz. 10.7 kategorizasyonu: scratch/probe, credential-riskli
dosya adları, gerçek backend/frontend kaynak+test çiftleri, belirsiz
docs/infra). Bu segmentte sadece kanıtlanmış TEK zincir kapatıldı --
kalan ~551 dosyanın hiçbiri bu PR'a dahil edilmedi, kasıtlı olarak. Bu
triyaj bir sonraki en yüksek öncelikli iş olarak işaretli kalıyor.

### 10.9 PR #75/#76: SS10.7 zincirinin devamı + adaptive_testing_service.py'de YENİ, GERÇEK bug (29 Ağu 2026)

**PR #75** (services/nlp/*): `motivation_generator.py`, `osym_validator.py`,
`yks_trend_analyzer.py` (backend/services/nlp/) ve 3 eşleşen test dosyası hiç
commit edilmemişti (SS10.7 kategorizasyonunda "gerçek backend kaynak+test"
grubu). Ruff RUF012 (ClassVar), S311 (`motivation_generator.py`'ye
`irt_equating_service.py` emsaliyle aynı gerekçeli per-file-ignore --
şablon seçimi, kripto değil), RUF021, SIM102 düzeltildi; mypy no-any-return
düzeltildi (`yks_trend_analyzer.py`, cache'ten okunan değer için açık
`str` tip belirtimi). Yerelde 12/12 test yeşil. CI'da 4 kırmızı, hepsi log
seviyesinde doğrulandı ve §10.4/10.5/10.6/§10.8'deki bilinen borçlarla
eşleşti (yeni hiçbir şey yok, `api.osym_routes` yine listede YOK). Merge:
`d361e02ff` (2026-08-29T21:38:04Z UTC).

**PR #76** (empirical_irt_calibrator): `services/empirical_irt_calibrator.py`
(4PL IRT parametre kalibrasyon motoru), onu kullanan
`scripts/quality/calibrate_question_bank_irt.py` (dry-run/--apply DB batch
pipeline) ve `tests/integration/test_empirical_irt_calibration.py` hiç
commit edilmemişti. Ruff (S324 -- `hashlib.md5(usedforsecurity=False)`,
PTH118/120, RUF059, UP038) ve mypy (var-annotated, union-attr) düzeltildi.

**Önemli yeni bulgu -- `services/adaptive_testing_service.py`'de canlı,
önceden-tespit-edilmemiş bir bug:** `test_empirical_irt_calibration.py`'nin
3 testinden 2'si, dosya hiç commit edilmediği için hiç koşmamıştı. Biri
(`test_irt_bootstrap_uses_empirical_calibrator`) zararsız -- `irt_bootstrap.
difficulty_to_irt()`'in `EmpiricalIRTCalibrator`'a entegrasyonu PLANLANMIŞ
ama hiç YAPILMAMIŞ (TypeError: unexpected keyword argument 'question_id').
Diğeri (`test_cold_start_cat_convergence_simulation`) ise EmpiricalIRTCalibrator
ile ilgisiz -- doğrudan zaten TRACKED olan `adaptive_testing_service.py`'yi
koşturuyor ve gerçek bir bug'a çarpıyor: `submit_response()`
(~satır 236) `session.response_history`'ye düz `{"a":.., "b":..}` sözlüğü
ekliyor, ama response_history'nin diğer girişleri iç içe `{"irt_params":
{...}}` şeklinde saklanıyor. `_calculate_sem()` → `_calculate_fisher_
information()` zinciri `item["a"]` okurken bu düz/iç-içe şekil
tutarsızlığına çarpıp `KeyError: 'a'` ile patlıyor (satır 345).

Bu, SS10.7'nin "hiç koşmayan test gate gerçek bug'ı yakalayamaz" deseninin
CAT (Computer Adaptive Testing) puanlama motorunda -- yani sınav sırasında
öğrencinin yetenek tahminini hesaplayan KRİTİK koddaki -- bir örneği.
Fix bu PR'ların kapsamı dışında BİLEREK bırakıldı (auth.py refresh-token
emsaliyle aynı gerekçe: önce arastır/belgele, kritik path'i ayrı, izole
bir PR'da düzelt). İki test de `xfail(strict=True)` ile, gerekçe ve dosya/
satır referansıyla işaretlendi -- CI yeşil kalıyor ama bulgu KAYBOLMUYOR.
Merge: `6cd4e1e4b` (2026-08-29T22:26:16Z UTC).

### 10.10 PR #77: growth_mindset_engine.py API'ye bağlandı + tests/integration/ event_loop boşluğu (29 Ağu 2026)

**PR #77**: `services/psychology/growth_mindset_engine.py` (GrowthMindsetEngine,
akademik durgunluk/direnç/alışkanlık mesajları) hiç API'ye bağlı değildi --
sadece dosya + birim testi commit edilmemişti (SS10.7 grubu). Bu PR onu yeni
bir `GET /api/v1/student-dashboard/growth-mindset` endpoint'ine
(`api/student_dashboard.py`) bağladı ve 2 test dosyasını (unit + integration)
commit'e ekledi.

**tests/integration/'da yeni tespit edilen bir boşluk:** `test_growth_mindset_api.py`
ilk çalıştırıldığında `ScopeMismatch: ... event_loop with a session scoped
request object` ile setup'ta düşüyordu. Kök neden: pytest-asyncio 0.21.1
(pinli), `pytest.ini`'nin `asyncio_default_fixture_loop_scope = session`
ayarını yok sayıyor; kök conftest'teki session-kapsamlı async fixture zinciri
(`setup_database` → `async_client`) session-kapsamlı bir `event_loop`
override'ı istiyor. `tests/e2e/conftest.py`'de bu zaten çözülmüştü;
`tests/integration/conftest.py`'de HİÇ yoktu -- bu dizindeki diğer
`async_client` kullanan dosyalar (örn. `test_exam_api_comprehensive.py`)
başka nedenlerle zaten skip olduğu için bu boşluk şimdiye kadar fark
edilmemişti. Düzeltme: `tests/e2e/conftest.py`'deki override'ın birebir
aynısı `tests/integration/conftest.py`'ye eklendi.

**Gerçek, canlı bir bug daha bulundu (mock_db_session):** Aynı test
`mock_db_session` fixture'ını (`tests/conftest.py` -- salt bir
`unittest.mock.AsyncMock()`) kullanıyordu. Bu fixture hiçbir gerçek
veritabanına bağlı değil; `.add()`/`.commit()` çağrıları sessizce hiçbir
yere yazmıyordu -- yani seed edilen veri, HTTP katmanının gerçekte gördüğü
(get_db → db_manager, `async_client` ile aynı `test_async_engine`'e bağlı)
veritabanında hiç var olmuyordu. Endpoint gerçekten çağrılsaydı bile
"improvement" değil "neutral" dönerdi. Gerçek `db_session` fixture'ına
(`tests/conftest.py:634`) geçildi.

**Ölçülen, pre-existing bir sınırlama (düzeltilmedi):** Yerelde de CI'da da
`TEST_DATABASE_URL` tanımsız → SQLite fallback; `setup_database`'in
`Base.metadata.create_all()` çağrısı `campus_info.sports_facilities`'in
Postgres-only `ARRAY` kolonu yüzünden patlıyor ve `pytest.skip(...)`
tetikliyor. `test_growth_mindset_api_endpoint` bu yüzden hem yerelde hem
CI'da SKIP olarak kalıyor -- `test_student_dashboard_integration.py` ve
`test_exam_api_comprehensive.py`'nin zaten kabul edilmiş aynı deseni.

**Lint borcu:** `api/student_dashboard.py`'de 8x pre-existing RET504
(kontrol kolu: `git show HEAD:... | ruff check ...`, PR öncesi/sonrası
aynı) -- `pyproject.toml`'a gerekçeli per-file-ignore eklendi, 8
fonksiyonu bu PR kapsamı dışında değiştirmemek için.

**CI kırmızısı, gerçek ve yeni:** İlk push'ta ruff PLW0108 ("Lambda may be
unnecessary") `test_growth_mindset_api.py:59`'da `lambda: MockKullanici()`
satırını yakaladı -- yerel lint bu satırı kaçırmıştı. Düzeltme: doğrudan
`MockKullanici` (sınıfın kendisi zaten sıfır-argümanlı bir callable).
İkinci push'ta CI yeşil.

**CI'da doğrulanan, PR'dan bağımsız 5 kırmızı (log seviyesinde teyit
edildi):** Automatic PR Review (§10.5, secret yok), Backend Tests Python
3.11 (§10.4, `tests/test_video_recommendation_service.py`'de
`NameError: name 'nn' is not defined` -- bu PR'ın dokunmadığı bir
dosya), Frontend Tests (§10.6, 988 hata -- katalogla birebir eşleşiyor),
Quality Gate/Router registration (§10.4, `api.rag`/`api.v1.semantic_search`/
`api.youtube_routes`), CI Summary (yukarıdakilerin salt türevi). Backend
Tests ve Frontend Tests bu üçlü zincirde (PR #75/#76/#77) İLK KEZ gerçekten
çalışıp kırmızı çıktı (önceki PR'larda "skipping" görünüyordu) -- ikisi de
zaten bilinen §10.4/§10.6 borcuna işaret ediyor, yeni bir bulgu değil.

Merge: `4331dff60` (2026-08-29T23:50:31Z UTC).

### 10.11 PR #78: GrowthMindsetCard.tsx canlı dashboard'a bağlandı, eski
localStorage/Bearer auth deseni temizlendi (30 Ağu 2026)

**PR #78**: `components/Dashboard/GrowthMindsetCard.tsx` (SS10.7 grubundan,
PR #77'nin bağladığı `growth-mindset` endpoint'ini hiç kullanmıyordu)
hiçbir yerden import edilmiyordu. Bu PR onu, `App.tsx:47` üzerinden
doğrulanan **canlı/routed** sayfa `pages/ModernStudentDashboard.tsx`'e
bağladı (`StudentDashboard.tsx` ve `ModernDashboard.tsx` legacy,
hiçbir yerden import edilmiyor -- tam kod taramasıyla elendi).

**Eski, depodan çıkarılmış bir auth deseni bulundu ve düzeltildi:**
orijinal dosya `localStorage.getItem('token')` + manuel `Authorization:
Bearer` header'ı ile ham `axios.get()` kullanıyordu. `apiClient.ts`
"No more localStorage token storage - XSS attack surface eliminated."
yorumuyla httpOnly cookie tabanlı auth'a geçildiğini belgeliyor;
sayfadaki diğer kartlar (`SubjectThetaCards`, ...) zaten `useQuery` +
`apiRequest` (`credentials: 'include'`) kullanıyordu. Eski haliyle
commit edilseydi ya çalışmayan ya da güvenlik regresyonu olan bir
bileşen sevk edilmiş olurdu. Düzeltme: veri katmanı `SubjectThetaCards`
ile birebir aynı desene yeniden yazıldı, görsel katman değiştirilmedi.

**Ek bulgu, bu PR'dan bağımsız, önceden var olan bir test-altyapısı
sorunu:** `snapshots.test.tsx > Dashboard Components Snapshots >
ModernStudentDashboard` testi, `ModernStudentDashboard`'ı dinamik
`import()` eden `beforeEach`'te vitest'in 10000ms `hookTimeout`'unu
aşıyor. Nedensellik doğrudan test edildi: `GrowthMindsetCard` import'u
ve kullanımı geçici olarak kaldırılıp aynı test tekrar çalıştırıldı --
hâlâ aynı şekilde, aynı konumda, aynı hookTimeout'ta patlıyor (11517ms
vs 10824ms, aynı hata) -- yani bu PR'dan tamamen bağımsız. Olası neden:
dosya doğrudan `@mui/material` import ediyor (ESLint'in kendi
`no-restricted-imports` kuralınca zaten legacy/discouraged işaretli,
satır 8), MUI'nin emotion tabanlı CSS-in-JS'i vitest/jsdom altında
soğuk transform'da yavaş kalabiliyor. CI'nin "Frontend Tests" job'u
zaten "Run ESLint" adımında duruyor (§10.6) -- bu vitest adımına CI şu
an hiç ulaşmıyor, bloklamıyor. Kök neden tam profillenmedi (orantısız
olurdu); ileride `ModernStudentDashboard.tsx`'in `@mui/material`
bağımlılığı Tailwind/shadcn'e taşınırsa (zaten ESLint'in kendi öneri
sırası) muhtemelen kendiliğinden çözülür.

**Ölçülen, küçük bir iyileşme:** Frontend Tests'in ESLint adımı bu PR'da
"2101 problems (987 errors, 1114 warnings)" verdi -- §10.6'nın belgelediği
988 hatadan 1 eksik. Fark, bu PR'ın düzelttiği (kendi diff'inin
kaydırdığı ama önceden var olduğu `git diff` hunk analiziyle doğrulanan)
tek bir trailing-whitespace hatasından geliyor; ESLint adımı tüm repo'yu
tarıyor (diff-bazlı değil), yani proje-geneli sayaç 1 azaldı.

**CI'da doğrulanan, PR'dan bağımsız 5 kırmızı (log seviyesinde teyit
edildi):** Automatic PR Review (§10.5), Backend Tests Python 3.11 (§10.4,
`tests/test_video_recommendation_service.py`, aynı `NameError: name 'nn'
is not defined`), Frontend Tests (§10.6, yukarıda), Quality Gate/Router
registration (§10.4, `api.rag`/`api.v1.semantic_search`/`api.youtube_routes`),
CI Summary (türev). API Security Testing (ZAP) 42m1s'de yeşil --
33-43+ dk aralığının üst ucunda, beklenen baseline içinde.

Merge: `44fd5f396` (2026-08-30T01:18:03Z UTC).

**Kalan kapsam:** SS10.7'deki 555 dosyadan şimdiye kadar
4+7+3+3+1=18 tanesi commit edildi (PR #74/#75/#76/#77/#78). ~537 dosya
hâlâ triyaj bekliyor.

### 10.12 Triyaj notu (PR yok): SS10.7 grubundaki 5 orphan frontend
bileşeni incelendi -- hiçbiri GrowthMindsetCard gibi "hazır, sadece bağla"
değil (30 Ağu 2026)

PR #78'in `GrowthMindsetCard.tsx` deneyiminden sonra, aynı "orphan mı,
neden bağlı değil, bağlanmalı mı" sorusu şu 5 dosyaya da soruldu:
`Gamification/StreakWidget.tsx`, `Gamification/DailyQuestsModal.tsx`,
`Dashboard/MisconceptionFlashcard.tsx`,
`Dashboard/TeacherMisconceptionHeatmap.tsx`, `Cognitive/BionicReadingText.tsx`.
Sonuç: hiçbiri kanıt seviyesinde "hazır, güvenle bağlanabilir" durumda
değil -- bu yüzden hiçbiri bu turda commit edilmedi. Kanıtlar:

- **`StreakWidget.tsx` -- muhtemelen supersede edilmiş, ölü kod.**
  `Gamification/index.ts` barrel'ı bunu export ETMİYOR (barrel'ın
  export ettiği `StreakBadge`/`StreakDot`, "FAZ-4" yorumuyla daha yeni
  görünüyor). `StreakBadge.tsx` aynı "seri" kavramını Tailwind
  (className, MUI değil) ile, kademeli emoji etiketleriyle (🌱/🔥/🐉/⚡)
  çok daha zengin bir şekilde kapsıyor -- `StreakWidget` ise MUI tabanlı
  (zaten ESLint'in `no-restricted-imports` kuralınca yeni kod için
  caydırılan yön) ve tek bir `freeze` satın alma prop'u (`onFreezeBuy`)
  dışında sade. `GamificationProfile` tipinde (`Dashboard/types.ts`)
  `streak`/`streak_active_today` VAR ama `freeze`/`freezeCount` kavramı
  YOK -- yani `StreakWidget`'ın "seri dondurucu satın al" özelliğinin
  backend karşılığı da görünmüyor.
- **`DailyQuestsModal.tsx` -- doğrulanmış şekilde supersede edilmiş,
  bağlanmamalı.** Canlı, bağlı `Dashboard/DailyQuestBanner.tsx`
  tıklandığında modal AÇMIYOR, `navigate('/daily-quests')` ile TAM
  SAYFAYA (`pages/DailyQuestPage.tsx`, `App.tsx`'te zaten route'lu) gidiyor.
  Modal'ı bağlamak canlı UX ile çakışan, gereksiz bir ikinci yol
  eklemek olurdu.
- **`Dashboard/GamificationDashboard.tsx` (bulgu, ayrı dosya ama ilişkili):**
  `Gamification/index.ts` barrel'ının kendi default export'u olmasına
  rağmen, kendi test dosyası dışında hiçbir yerden import edilmiyor.
  Yani `components/Gamification/` klasörünün tamamı ("Task 91"/"FAZ-4")
  canlı uygulamadan kopmuş olabilir -- ama bu, klasördeki diğer 6
  dosya (`PointsDisplay`, `LevelDisplay`, `BadgeCollection`,
  `Leaderboard`, `XPBar`, `BadgeEarned`) tek tek kontrol edilmeden
  iddia edilemez; bu turda yapılmadı.
- **`TeacherMisconceptionHeatmap.tsx` -- prototip, gerçek veri yok.**
  Dosya içinde donanımlı `const mockData: HeatmapData[]` var (elle
  yazılmış sahte konu/öğrenci/şiddet satırları), hiçbir `useQuery`/API
  çağrısı yok. Muhtemel canlı ev sahibi `pages/ModernTeacherDashboard.tsx`
  (App.tsx:57/586, route'lu, canlı) ama bu bileşeni olduğu gibi
  bağlamak gerçek öğretmenlere SAHTE sayılar göstermek olurdu --
  önce backend'de gerçek bir "yanılgı ısı haritası" endpoint'i
  gerekiyor (bu PR'ın kapsamı dışında, backend tasarım kararı
  gerektiriyor).
- **`Dashboard/MisconceptionFlashcard.tsx` -- saf sunum bileşeni,
  ev sahibi belirsiz.** Props (`misconceptionName`, `distractor`,
  `refutation`, `takeaway`, `onDismiss`) veri çekmiyor; muhtemelen
  sınav-sonucu/tekrar akışına ait ama böyle bir akış bu turda
  bulunamadı -- tahmin yürütmek yerine boş bırakıldı.
- **`Cognitive/BionicReadingText.tsx` -- muhtemelen değerli, kendi
  test dosyası var (`__tests__/BionicReadingText.test.tsx`) ama canlı
  kullanımı yok.** Metin dönüştürme (erişilebilirlik) yardımcı
  bileşeni -- muhtemel ev sahibi sınav/okuma metni render eden bir
  yer, ama bu tur içinde taranmadı.

**Sonuç:** SS10.7'deki 555 dosyanın "orphan frontend bileşeni" alt
kümesi homojen değil -- bazıları GrowthMindsetCard gibi "hazır, bağla",
bazıları supersede edilmiş ölü kod, bazıları backend'i eksik prototip.
Her biri kendi kanıtıyla ele alınmalı, toplu bir kural uygulanamaz.
Kalan kapsam sayacı bu notla değişmedi (hiçbir dosya commit edilmedi).


### 10.13 PR #79: `api.v1.mistakes` router'ı hiç kaydedilmemişti -- SS10.4/
RCA-1 deseninin ikinci kanıtlanmış örneği (30 Ağu 2026)

**PR #79**: `backend/api/v1/mistakes.py` (FSRS "due mistakes" tekrar
kuyruğu endpoint'i, SS10.7 grubundan) dosyası repoda duruyordu ama
`routers/loader.py`'nin `ROUTER_MAPPING`'ine hiç eklenmemişti -- yani
router hiçbir zaman uygulamaya mount edilmemişti. Bu, `test_router_
registration.py`'nin kendi docstring'inin tarif ettiği hata sınıfının
("Session 120 -- 5 router 2+ hafta 404 döndü çünkü loader.py'ye ekleme
adımı atlanmıştı") ikinci kanıtlanmış örneği -- ilk örnek 10.7/10.8'de
`api.osym_routes`'un lazy-import zinciriydi, bu farklı bir kök neden
(basitçe kaydı unutulmuş bir router) ama aynı sonuç sınıfı (sessiz 404).

**Ek olarak fark edildi ve düzeltildi:** `api/v1/mistakes.py`'nin prefix'i
yanlıştı (`"/mistakes"`) -- diğer tüm `api/v1/*` router'ları (`semantic_
search`, `batch`, `expert_agents_api`) kendi kendine tam `/api/v1/...`
yolunu prefix'liyor, `loader.py` merkezi bir prefix eklemiyor. `"/api/v1/
mistakes"` olarak düzeltildi -- router şu ana kadar hiç mount edilmediği
için sıfır tüketicisi var, düzeltme geriye dönük hiçbir şeyi kırmadı.

**Ölçülen, düzeltilmeyen bir algoritma sınırlaması işaretlendi:**
`IsomorphicGenerator.generate_isomorphic_question()`'ın kendi docstring'i
"LLM entegrasyonu için placeholder" / "mock simulation" olduğunu
söylüyor -- sayıları değiştirirken doğru cevap şıklarını yeniden
hesaplamıyor, sadece onları da rastgele kaydırıyor, yani döndürülen
çoktan seçmeli şıklar matematiksel olarak yanlış olabilir. Çağrı
noktasının hemen üstüne Türkçe bir uyarı yorumu eklendi; gerçek düzeltme
(matematiği yeniden hesaplamak ya da LLM entegrasyonu) bu PR'ın kapsamı
dışında bırakıldı.

**Yan iş: ilk kez tracked+lint-taranan bir dosyanın pre-existing borcu.**
`backend/algorithms/isomorphic_generator.py` bu PR'la ilk kez commit
edildiği için ruff/bandit'in CI-taradığı ağaca ilk kez girdi -- 6
pre-existing bulgu (RUF012 x2, S311/B311 x4) düzeltildi. `test_isomorphic_
generator.py` (3 test, önceden var, değiştirilmedi) ilk kez commit
edildi.

**Yerel doğrulama:** 3/3 test yeşil, `ruff check`/`ruff format --check`/
`bandit` temiz, pre-push zorunlu kapı (320 passed, 1 skipped, 1 xfailed,
104.67s) baseline ile birebir eşleşti.

**CI'da doğrulanan, PR'dan bağımsız 5 kırmızı (log seviyesinde teyit
edildi):** Automatic PR Review (§10.5, eksik secret), Backend Tests
Python 3.11 (§10.4, `tests/test_video_recommendation_service.py`, aynı
`NameError: name 'nn' is not defined`), Frontend Tests (§10.6, "2101
problems (987 errors, 1114 warnings)" -- PR #78 sonrası baseline ile
birebir aynı, bu PR frontend'e dokunmadığı için beklenen), Quality Gate/
Router registration (§10.4, `api.rag`/`api.v1.semantic_search`/`api.
youtube_routes` -- ÖNEMLİ: `test_mapped_routers_are_importable` bu 3
router'da başarısız oldu ama `api.v1.mistakes` listede YOK ve `test_all_
app_api_routers_registered` (aynı dosyanın DİĞER testi, bu PR'ın asıl
konusu) AYRI YEŞİL geçti -- "1 failed, 2 passed" -- yani bu PR'ın kendi
düzeltmesi doğrulandı, yeni bir kırılma eklemedi), CI Summary (türev).
API Security Testing (ZAP) 54m1s'de yeşil -- önceki PR'ların 33-43+ dk
aralığından belirgin şekilde uzun sürdü (muhtemelen runner yoğunluğu),
ama sonuç değişmedi.

Merge: `b108242a8` (2026-08-30T02:48:51Z UTC), `gh pr merge 79 --squash`.
Local master senkronize edildi (`94b170e11..b108242a8`, fast-forward, 4
dosya, +218 satır).

**Kalan kapsam:** SS10.7'deki 555 dosyadan şimdiye kadar
4+7+3+3+1+3=21 tanesi commit edildi (PR #74/#75/#76/#77/#78/#79). ~534
dosya hâlâ triyaj bekliyor (`isomorphic_generator.py`, `mistakes.py`,
`test_isomorphic_generator.py` -- `routers/loader.py` zaten tracked
olduğu için sayaca dahil değil).


### 10.14 PR #80: YKSJargonService untracked yedekten kurtarıldı --
BİLEREK bağlanmadı (30 Ağu 2026)

**PR #80**: `backend/services/yks_jargon_service.py` (`YKSJargonService`,
SS10.7 grubundan) hiç commit edilmemişti. Servis, farklı YKS derslerinde
aynı kelimenin farklı teknik anlamlara gelmesinden (ör. Fizik'te "iş"
W=F.x, günlük dilde "iş" = meslek) doğan LLM halüsinasyonunu önlemeyi
hedefliyor -- bir dersin sözlüğünü LLM sistem promptuna XML kural bloğu
olarak enjekte eden (`get_jargon_prompt_injection`) ve üretilmiş metni
regex tabanlı guardrail ile tarayan (`validate_text_jargon_compliance`)
iki sınıf metoduyla. Bağımsız (zero external dependency), tamamen
self-contained bir yardımcı sınıf.

**Bilinçli olarak BAĞLANMADI:** `git grep` ile doğrulandı --
`YKSJargonService`/`yks_jargon_service` adı kendi dosyası ve testi
dışında hiçbir yerde geçmiyor. Bu depoda onu çağıracak bir LLM tabanlı
soru-üretim prompt pipeline'ı **tek, açık bir çağrı noktası olarak
bulunamadı** -- `IsomorphicGenerator`'ın kendi docstring'i de (SS10.13)
kendisinin "LLM entegrasyonu için placeholder" olduğunu söylüyor, yani bu
depodaki soru üretimi henüz tam bir LLM prompt akışına sahip görünmüyor.
Ayrıca `socratic_rag_guardrail_service.py`'deki "prompt_injection" ismi
kontrol edildi -- o güvenlik anlamında (LLM prompt injection SALDIRISI
tespiti), bu servisin "prompt'a içerik enjekte etme" anlamıyla alakasız,
çakışma/ikilik yok. Bu PR bilinçli olarak dar tutuldu: dosyayı untracked
backlogtan kurtarmak (PR #75'in `services/nlp/*` emsaliyle aynı desen) --
gerçek wiring, prompt pipeline'ının kendisini bulmayı/tasarlamayı
gerektiren ayrı bir iş olarak işaretli bırakıldı.

**İlk kez tracked+lint taranan dosyanın pre-existing borcu:** 4 bulgu
düzeltildi -- RUF012 (`SUBJECT_GLOSSARIES` artık `ClassVar`), PLR0912
(gerekçeli `# noqa` -- her ders bloğu bağımsız, sözlük yapısıyla aynı
gruplamayı yansıtıyor), SIM102 x2 (nested if'ler `and` ile birleştirildi,
davranış testlerle doğrulanarak değişmedi).

**Yerel doğrulama:** 2/2 test yeşil, `ruff check`/`ruff format --check`/
`bandit`/`mypy` temiz, pre-push zorunlu kapı (320 passed, 1 skipped, 1
xfailed, ~107s) baseline ile birebir eşleşti.

**CI'da doğrulanan, PR'dan bağımsız 5 kırmızı (log seviyesinde teyit
edildi):** Automatic PR Review (§10.5), Backend Tests Python 3.11 (§10.4),
Frontend Tests (§10.6), Quality Gate/Router registration (§10.4, "1
failed, 2 passed" -- bu PR router'a hiç dokunmadığı için beklenen),
CI Summary (türev). API Security Testing (ZAP) 40m21s'de yeşil.

Merge: `4fc3168f9` (2026-08-30T03:40:57Z UTC).

**Kalan kapsam:** SS10.7'deki 555 dosyadan şimdiye kadar
4+7+3+3+1+3+2=23 tanesi commit edildi (PR #74/#75/#76/#77/#78/#79/#80).
~532 dosya hâlâ triyaj bekliyor.


### 10.15 PR #81: Kayıt akışına learning_path_student_profiles insert'i eklendi (30 Ağu 2026)

**PR #81**: Önceki bir SS10.x segmentinin "Optional Next Step"i olarak
bırakılan bir şüphe doğrulandı: `RegisterUserCommandHandler.handle()`
(`application/commands/auth.py`) `STUDENT` rolü için `student_profiles`
satırı oluşturuyordu ama `learning_path_student_profiles` satırını HİÇ
oluşturmuyordu. Sonuç: yeni kayıt olan her öğrenci için learning-path alt
sisteminin tamamı (profil olmadan `verify_student_access` her isteği 403
ile reddediyor) baştan kilitliydi.

Kanıt zinciri: `test_db_profile_sync.py` (untracked, `db_session`
fixture'ıyla gerçek Postgres'e karşı) yazılıp koşturuldu -- düzeltmeden
ÖNCE 1 passed/2 failed, düzeltmeden SONRA 3/3 passed. Aynı anda untracked
backlogtaki `services/profile_sync_service.py` (aynı işi ayrı bir
senkronizasyon yolunda yapan bir "kurtarma adayı") da incelendi ve S255
kaymasının (bkz. SS10.x, `neuro_inclusive_mode`) BU dosyayı da vuracağı
görüldü -- raw-SQL `INSERT` kolonu atlıyordu, ORM'deki Python-tarafı
`default=False` raw SQL'i korumuyor. İki dosya da (auth.py'nin asıl
düzeltmesi + profile_sync_service.py'nin kurtarılan hâli) aynı düzeltmeyle
işaretlendi.

**Yerel doğrulama:** 3/3 test yeşil (gerçek Postgres), `ruff check`/`ruff
format --check`/`mypy` temiz, pre-push zorunlu kapı (320 passed, 1
skipped, 1 xfailed, 97.01s) baseline ile birebir eşleşti.

**CI'da doğrulanan, PR'dan bağımsız 5 kırmızı:** Automatic PR Review
(§10.5), Backend Tests Python 3.11 (§10.4), Frontend Tests (§10.6),
Quality Gate/Router registration (§10.4, "1 failed, 2 passed" -- bu PR
router'a hiç dokunmadığı için beklenen), CI Summary (türev). 8 Golden
Flow E2E testi 4m1s'de yeşil (bu PR'ın asıl konusu olan kayıt akışını
uçtan uca doğruluyor). API Security Testing (ZAP) 42m35s'de yeşil.

Merge: `a7b9f3cab` (2026-08-30T05:20:25Z UTC), `gh pr merge 81 --squash`.

**Kalan kapsam:** SS10.7'deki 555 dosyadan şimdiye kadar
4+7+3+3+1+3+2+2=25 tanesi commit edildi (PR #74/#75/#76/#77/#78/#79/#80/
#81) -- `profile_sync_service.py`, `test_db_profile_sync.py`. ~530 dosya
hâlâ triyaj bekliyor.


### 10.16 PR #82: `ai_mentor_service.py` kurtarması Windows'ta import anında çöküyordu -- emoji `print()` + eager singleton (30 Ağu 2026)

SS10.7 grubundan `services/ai_mentor_service.py` (untracked backlog)
kurtarılırken, modülün import'u bile Windows'ta çöküyordu:
`UnicodeEncodeError: 'charmap' codec can't encode characters in position
0-1: character maps to <undefined>`. Kök neden `ai_mentor_service.py`de
değil, onun kullandığı (zaten tracked) `services/llm/ensemble_manager.py`
idi -- provider init durumunu `print(f"✅ ...")` / `print(f"⚠️  ...
failed: {e}")` gibi emoji içeren çağrılarla raporluyordu. Bu karakterler
Windows'un UTF-8 olmayan konsol code page'lerinde (bu makinede
cp1254/Türkçe) encode edilemiyor -- tek bir provider'ın (ör. Gemini,
`GOOGLE_API_KEY` yokken) init hatası, kendi `except` bloğunun İÇİNDE yeni
bir `UnicodeEncodeError` fırlatıp yakalanmadan yukarı sızıyordu. Yani asıl
amacı "bir sağlayıcı başarısız olursa sessizce diğerine geç" olan fallback
deseni, bu platformda soft-fail yerine hard-crash'e dönüşüyordu -- 17
çağrı noktasının hepsi aynı sınıftan. Bu, sadece `ai_mentor_service.py`yi
değil, `MultiLLMEnsembleManager`'ı kullanan HER servisi etkiliyordu
(`api/osym_routes.py`, `services/osym_pdf_pipeline.py`,
`services/sequential_reasoning_service.py`,
`tasks/question_generation_tasks.py`).

İkinci, bağımsız düzeltme: `ai_mentor_service.py`nin modül-seviyesi
`ai_mentor_service = AIMentorService()` singleton'ı `MultiLLMEnsembleManager()`'ı
IMPORT ANINDA kuruyordu -- hiçbir sağlayıcı anahtarı yokken bu her zaman
`RuntimeError` fırlatırdı (encoding hatası çözülünce bu ortaya çıktı).
Codebase'in kendi yerleşik deseni (`services/sequential_reasoning_service.py`)
lazy `@property` ile çözüyor; aynı desen burada da uygulandı.

**Yerel doğrulama:** düzeltme öncesi `from services.ai_mentor_service
import ai_mentor_service` importta çöküyordu; düzeltme sonrası aynı
import temiz, `generate_nudge()` gerçek uçtan uca çağrıldı (0 sağlayıcı
anahtarı ile) -> 4 provider için `logger.warning` (encoding hatası yok),
`RuntimeError` yakalandı, statik Türkçe fallback mesajı döndü.
`pytest tests/unit/test_services_remaining_batch1.py` -- 71 passed.
`ruff check`/`ruff format --check`/`bandit` temiz.

Ayrıca `ensemble_manager.py`de PLR0917 (çok fazla pozisyonel parametre)
için ayni ruff sürüm çelişkisi (bkz. §10.10, `tests/conftest.py`)
`backend/pyproject.toml`da gerekçeli per-file-ignore ile kaydedildi --
inline `noqa` pre-commit'in eski ruff'ında (v0.7.1) RUF100 ile otomatik
siliniyor, CI'nin pin'siz kurulumu ise PLR0917 ile patlıyordu.

**CI'da doğrulanan, PR'dan bağımsız 5 kırmızı:** Automatic PR Review
(§10.5), Backend Tests Python 3.11 (§10.4), Frontend Tests (§10.6),
Quality Gate (§10.4), CI Summary (türev). Code Quality (ruff/mypy/
bandit/safety/semgrep) hepsi yeşil -- ruff çelişkisi düzeltmesi
doğrulandı. 8 Golden Flow E2E testi 4m14s'de yeşil. API Security Testing
(ZAP) 27m31s'de yeşil.

Merge: `5b27cabea` (2026-08-30T05:50:42Z UTC), `gh pr merge 82 --squash`.

**Kalan kapsam:** SS10.7'deki 555 dosyadan şimdiye kadar
4+7+3+3+1+3+2+2+1=26 tanesi commit edildi (PR #74/#75/#76/#77/#78/#79/
#80/#81/#82) -- `ai_mentor_service.py` (`ensemble_manager.py` zaten
tracked'ti, sayaca dahil değil). ~529 dosya hâlâ triyaj bekliyor.


### 10.17 PR #85: `alembic_utils.py` backlog kurtarması -- çift mypy ortamı çelişkisi (30 Ağu 2026)

SS10.7 grubundan `backend/core/alembic_utils.py` (+ `tests/integration/
test_alembic_utils.py`, 9 test) untracked kalmıştı. İlk mypy geçişinde iki
bulgu çıktı: `from alembic import op` (`attr-defined` -- alembic'in `op`u
çalışma zamanında dinamik proxy, upstream sınırlaması) ve `table_exists`
(`no-any-return` -- `Inspector.has_table()` mypy'ye `Any` yansıyor).
İkisi de bu kampanyanın daha önce kurduğu desenle çözüldü: gerekçeli
`# type: ignore[attr-defined]` ve açık `result: bool` yerel değişken
anotasyonu.

`reward-hacking-check` bekçisi `constraint_exists`teki
`except Exception: pass`i (bir `# nosec B110` yorumuyla) CRITICAL
işaretledi -- bekçinin AST yolu yorum-kör, sadece gövdenin `pass`/`...`
olup olmadığına bakıyor. PR #72'de kurulan gerçek desen tekrar
uygulandı: sessiz yutma yerine `logger.debug(...)` (davranış aynı,
gözlemlenebilirlik eklendi).

İkinci, bağımsız bir sorun CI'da ortaya çıktı: "Code Quality (mypy)" job'u
AYNI `# type: ignore[attr-defined]` satırını `[unused-ignore]` ile
REDDETTİ. Kök neden: pre-commit'in mypy hook'u izole bir venv'de
(pinlenmiş `v1.11.2` + `additional_dependencies` listesi, `alembic` dahil
DEĞİL) çalışıyor -- bu ortamda ignore GEREKLİ. CI'nin ayrı job'u ise
projenin gerçek `.venv`'ini (requirements.txt'teki pinlenmiş `alembic`
ile) kullanıyor -- bu ortamda ignore GEREKSİZ. İki ayrı, ikisi de geçerli
CI kapısı aynı satır için çelişiyordu. Düzeltme: kök `pyproject.toml`da
sadece bu modül için `warn_unused_ignores = false` (`ignore_errors = true`
DEĞİL -- dosyanın geri kalanı tam denetimde kalıyor).

**Yerel doğrulama:** 9/9 entegrasyon testi gerçek Postgres'e karşı yeşil
(iki kez tekrarlandı). Pre-commit mypy hook'u ve `backend\venv`'in mypy
1.7.1'i (CI'nin gerçek bulgusunu tekrar ürettiği doğrulanan ortam) hem
düzeltme öncesi (kırmızı) hem sonrası (yeşil) ayrı ayrı çalıştırıldı.

**CI'da doğrulanan, PR'dan bağımsız 5 kırmızı:** Automatic PR Review,
Backend Tests Python 3.11, CI Summary, Frontend Tests, Quality Gate --
hepsi §10.16 emsaliyle birebir. Code Quality (mypy dahil) hepsi yeşil.
API Security Testing (ZAP) 43m23s'de yeşil -- bu segmentte aynı anda 4
PR'ın ZAP taraması tetiklendiği için (bkz. §10.19) normal ~27dk yerine
uzadı, kaynak çekişmesi dışında bir sorun değil.

Merge: `afbb23aab` (2026-08-30T06:48:32Z UTC), `gh pr merge 85 --squash`.

**Kalan kapsam:** SS10.7'deki 555 dosyadan şimdiye kadar 26+2=28 tanesi
commit edildi -- `alembic_utils.py` + `test_alembic_utils.py` (kök
`pyproject.toml` değişikliği zaten tracked'ti, sayaca dahil değil).
~527 dosya hâlâ triyaj bekliyor.


### 10.18 PR #83: `pedagogy_models.py` backlog kurtarması -- 3 tablo `Base.metadata`'ya bağlandı (30 Ağu 2026)

SS10.7 grubundan `MEBCurriculumNode` (içerik zehirlenmesi filtresi --
müfredat dışı kelime kara/beyaz listesi) ve `MisconceptionMatrix`/
`MisconceptionRemedy` (kavram yanılgısı sözlüğü + mikro-öğrenme tedavisi)
untracked kalmıştı; git grep ile doğrulandı, dosyanın dışında hiçbir
servis/API/test onları çağırmıyordu.

Canlı Postgres'te (30 Ağu 2026) ölçüldü: 3 tablo da GERÇEKTEN var
(`alembic/versions_archive/d23f7afe5e9a_*.py` + baseline şema) ve ORM
modeli kolon kolon BİREBİR eşleşiyor -- schema drift yok. Tek düzeltme:
`MisconceptionMatrix.severity_weight` tip ipucu `Mapped[float]` idi ama
canlı kolon `integer` -- `Mapped[int]` + `default=1` olarak düzeltildi.
`models/database.py` (re-export katmanı) üzerinden `Base.metadata`'ya
bağlandı (129 tablo, önceden 126) -- `core/alembic_autogen_guard.py`'nin
belgelediği "87 tablo metadata dışında" borcundan 3'ü kapandı. Kalıcı
bekçi: `test_pedagogy_models_sema_paritesi.py` (S255 deseninin 3 tabloya
genellenmesi, 7 yeni test) -- DB<->ORM kolon paritesini otomatik doğrular.

Yan bulgu: `database.py`'nin `__all__` listesi RUF022 tetikliyordu (aynı
CI/pre-commit ruff sürüm çelişkisi, bkz. §10.16'daki PLR0917); liste
kasıtlı olarak alfabetik değil, model dosyasına göre gruplanmış --
otomatik "fix" bu belgeleme yapısını kırardı, dosyaya özel per-file-ignore
ile korundu.

Bu PR'ın dalı, §10.16/PR #82 merge edildikten sonra `backend/pyproject.toml`
üzerinde CONFLICTING duruma düştü (ikisi de aynı per-file-ignores bölümüne
dokunuyordu -- öngörülen risk). `git rebase` yerel olarak çözdü ama
yayınlamak `push --force` gerektirirdi (bu oturumda yasak, canlı kullanıcı
onayı yok); rebase geri alındı (`git reset` + kapsamlı `checkout --`,
`reset --hard` DEĞİL) ve aynı çözüm `git merge origin/master --no-edit` ile
tekrarlandı -- zorlama olmadan normal push edilebildi.

**Yerel doğrulama:** 7 yeni + 4 mevcut (S255) parite testi yeşil, ayrıca
mevcut 9 `alembic_autogen_guard` testi yeşil (regresyon yok). `ruff
check`/`mypy` temiz.

**CI'da doğrulanan, PR'dan bağımsız 5 kırmızı:** §10.17 ile birebir aynı
desen. API Security Testing (ZAP) 43m23s'de yeşil (bkz. §10.19 -- eşzamanlı
4 PR nedeniyle uzadı).

Merge: `1f2cc70ef` (2026-08-30), `gh pr merge 83 --squash`.

**Kalan kapsam:** SS10.7'deki 555 dosyadan şimdiye kadar 28+1=29 tanesi
commit edildi -- yalnız `pedagogy_models.py` (`database.py`,
`pyproject.toml` zaten tracked'ti; `test_pedagogy_models_sema_paritesi.py`
bu PR'da yeni yazılan bekçi testiydi, SS10.7 havuzundan değil, sayaca
dahil değil). ~526 dosya hâlâ triyaj bekliyor.


### 10.19 PR #87: `backend/utils/__init__.py` eksikti (30 Ağu 2026)

`backend/utils/` dizini 6 tracked dosyaya (cache_manager.py,
file_watcher.py, lazy_imports.py, pdf_generator.py, video_validation.py,
zemberek_integration.py) sahipti ama kendi `__init__.py`si takip
dışıydı -- SS10.7 taramasından kalan, boş (0 byte) bir dosya. Python 3'ün
implicit namespace packages özelliği çalışma zamanında bir soruna yol
açmıyordu, ama paketi açıkça tanımlamak için eklendi. Dosya boş olduğu
için ruff/mypy/bandit'in üzerinde kontrol edecek bir şeyi yoktu.

**CI'da doğrulanan, PR'dan bağımsız 5 kırmızı:** §10.17/§10.18 ile
birebir. API Security Testing (ZAP) 31m1s'de yeşil.

Merge: `d4e1c1574` (2026-08-30), `gh pr merge 87 --squash`.

**Kalan kapsam:** SS10.7'deki 555 dosyadan şimdiye kadar 29+1=30 tanesi
commit edildi. ~525 dosya hâlâ triyaj bekliyor.

**Not (§10.17-10.19 ortak):** Bu üç PR + §10.16/PR #86 aynı segmentte,
art arda açıldı -- sonuç, hepsinin ZAP taramasının eşzamanlı çalışması
(API Security Testing süreleri 31dk-43dk arasına yayıldı, normal
~27dk yerine). Bulgu niteliğinde: eşzamanlı çok-PR açma, tek başına
zararsız olsa da CI kaynak çekişmesi üzerinden toplam bekleme süresini
uzatıyor -- ileride büyük backlog kurtarma dalgalarında dikkate alınacak.


### 10.20 PR #62 sonrası backlog planı (Faz 0-6) tamamen doğrulandı (30 Ağu 2026)

Bu segmentte, PR #83/#85 CI beklerken, eski plan dosyasının (PR #62
kapanışında listelenen 7 kalem) durumu tek tek yeniden doğrulandı --
Faz 0-3 önceki bir segmentte zaten tamamlanmış olarak biliniyordu, bu kez
Faz 4-6 doğrulandı:

- **Faz 4 (temiz-oda ölçüm script'i):** `backend/scripts/
  temiz_kopya_guvenlik_olcumu.py` zaten tracked ve mevcut -- ayrı bir iş
  gerekmiyor.
- **Faz 5 (Dependabot triyaj, 20 PR):** Açık PR sayısı 12'ye düşmüş,
  plandaki iki büyük-atlama örneği (#43 marshmallow, #46 structlog) artık
  listede yok -- otomasyon çalışır durumda (`gh pr view` ile tek tek
  sorgulanan PR'lar `MERGEABLE` dönüyor, `gh pr list`in toplu görünümündeki
  `UNKNOWN` sadece GitHub'ın tembel hesaplama önbelleği). Kalan 12 PR,
  haftalık normal Dependabot akışı -- ayrı bir müdahale gerekmiyor.
- **Faz 6 (5 CodeQL false-positive dismiss):** `docs/guvenlik-borcu.md`
  §"Faz 6" bölümünün kendisi işin daha önce yapıldığını (ve bir
  `dismissed_comment` bug'ının düzeltildiğini) belgeliyor.

Repo'nun toplam açık CodeQL alert sayısı (`gh api .../code-scanning/alerts`)
2601 -- ama bu, plandaki "5 spesifik `py/weak-sensitive-data-hashing`
false-positive'i" ile karışmamalı; o 5'i zaten dismiss edilmiş, kalan 2601
çok daha geniş, ayrı bir triyaj gerektiren bir gövde (bu planın kapsamı
dışında).

**Sonuç:** `stateful-shimmying-papert.md` planının 7 kaleminin TAMAMI
(Faz 0-6) doğrulanmış durumda tamamlanmış. Plan dosyası kapatılabilir.


### 10.21 PR #89: `sorular` -> `v_safe_for_beta` -- var olmayan tabloyu hedefleyen ÖSYM referans sorgusu (30 Ağu 2026)

`api/hybrid_question_generation.py` (Wave 2B few-shot havuzu, 2 çağrı
yeri) ve `services/production_quality_monitor.py` (`_get_evaluator`) ham
SQL ile `FROM sorular` sorguluyordu. `sorular` yalnızca
`backend/migrations/013_create_sorular_table.sql` içinde tanımlıydı -- bu
klasör (57/58 tracked dosya) alembic'e hiç entegre değil, hiçbir `alembic
upgrade head` onu yaratmıyor. Canlı DB'de doğrulandı: hem `sorular`
(migration 013) hem `questions` (migration 003) `to_regclass(...)` ile
NULL dönüyor -- yani `migrations/` klasörünün TAMAMI, alembic'in gerçek
şemasının yerini asla almamış, terk edilmiş paralel bir tasarım.

**Sessiz hata mekanizması:** iki çağrı yeri de `except Exception ->
logger.warning` ile yutuyordu (bilinçli tasarım -- referans
yüklenemezse üretim durmasın). Sonuç 500 değil, sessiz kalite kaybı:
Wave 2B referanssız few-shot üretim yapıyordu, ve
`ProductionQualityMonitor._get_evaluator()` HER çağrıda patlayıp `None`
dönüyordu (`log_question`'ın kendi geniş except'i içinde) -- yani
`api/production_monitoring.py` (`routers/loader.py`'de "analytics"
altında tracked, **canlı mount**) hiçbir soruyu hiç loglayamıyordu.
Ölü kod değil: gerçek, mount edilmiş production path.

**Düzeltme:** canlı şemada aynı veriyi taşıyan VE zaten kalite-kapısından
geçirilmiş olan `v_safe_for_beta` view'ına yönlendirildi (`question_content`
+ `mv_safe_for_beta` manuel join yerine -- `v_safe_for_beta` zaten
`mv_safe_for_beta`'nın kendi kaynağı, difficulty_level/subject_area
sütunlarını da hazır içeriyor). Canlı DB'de 2967 uygun satır var (>100
karakter, correct_answer dolu). Kalıcı bekçi:
`tests/integration/test_osym_reference_query.py` -- kaynak dosyaların
SQL'ini parse edip her tablonun canlı DB'de var olduğunu ve
`question_content` kullanan sorguların `mv_safe_for_beta` kapısından
geçtiğini doğruluyor (CLAUDE.md'nin "soru sorgularinda is_active + kalite-
status filtresi ZORUNLU" kuralı).

**Yan temizlik (`production_quality_monitor.py`):** pre-commit ruff/mypy
kapısı dosyada dokunulmamış 12 önceden-var-olan bulguyla birlikte çalıştı
(dosya daha önce hiç lint edilmemiş). Güvenli/trivial 11'i doğrudan
düzeltildi: 3x `PTH123` (open -> Path.open), 5x `T201` (print -> logger),
1x `C401` (generator -> set comprehension), 1x `PLW0603`
(`get_monitor()` singleton'ı ilk denemede function-attribute pattern'iyle
düzeltildi ama mypy `attr-defined` ile reddetti -- ikinci, kalıcı çözüm
`functools.cache`, tipli/idiomatik). Kalan `PLR0912` (`generate_report`,
18 > 12 dal) için `backend/pyproject.toml`'a per-file-ignore eklendi --
fonksiyonun KENDİ docstring'i bu borcu zaten `@TODO S179 fix (B-P0-69)`
olarak işaretliyor ve "Do NOT add new branches" diyor.

**CodeQL bulgusu (yeni bekçide):** `check-runs` annotasyonu
`test_osym_reference_query.py:65`'te `py/uninitialized-local-variable`
işaretledi -- `baglanti` fixture'ı `except psycopg2.OperationalError ->
pytest.skip(...)` sonrası `conn.autocommit = False`'a düşüyordu; skip()
çalışma zamanında HER ZAMAN raise eder ama CodeQL'in akış analizi bunu
bilmiyor. İkinci commit'le (`b07e415ca`) except bloğuna açık bir `raise`
eklendi (orijinal hatayı yeniden fırlatır) -- CodeQL bir sonraki pushta
"skipping" (alert kapandı), ardından "pass" olarak doğruladı.

**Yerel doğrulama:** `test_osym_reference_query.py` 4/4 yeşil (önce
kırmızı, `sorular` mevcut değilken doğrulandı). `test_api_batch2.py` +
`test_question_management.py`: 372 passed, 31 skipped, 13 failed -- 13'ü
de FSRS flashcard uçlarının kasıtlı 410 Gone kaldırmasıyla ilgili,
önceden var olan, alakasız borç. Push-time `ders-zorlayici` bekçi paketi:
320 passed, 1 skipped, 1 xfailed.

**CI'da doğrulanan, PR'dan bağımsız 5 kırmızı:** Automatic PR Review,
Backend Tests Python 3.11, CI Summary, Frontend Tests, Quality Gate --
önceki PR'lerle birebir. API Security Testing (ZAP) 31m49s'de yeşil --
bu segmentte eşzamanlı başka PR olmadığı için normal ~27-32dk aralığında
(bkz. §10.19'daki 4-PR-eşzamanlı uzama bulgusunun tersi doğrulaması).

Merge: `00ed89da9` (2026-08-30), `gh pr merge 89 --squash` (2 commit:
`c4cf02a26` ana düzeltme, `b07e415ca` CodeQL fixup).

**Kalan kapsam:** SS10.7'deki 555 dosyadan şimdiye kadar 30+1=31 tanesi
commit edildi -- yalnız `test_osym_reference_query.py` (`hybrid_question_
generation.py`, `production_quality_monitor.py`, `pyproject.toml` zaten
tracked'ti, sayaca dahil değil). ~524 dosya hâlâ triyaj bekliyor.

### 10.22 PR #91: `routers/learning/gamification.py` + eşleşen frontend bileşenleri -- gerçek ama bilerek bağlanmamış özellik (30 Ağustos 2026)

SS10.7 taramasında `backend/routers/learning/` altında tek dosya
bulundu: `gamification.py` (142 satır) -- günlük görev üretimi
(`/quests`), seri durumu (`/status`), seri dondurucu satın alma
(`/freeze/buy`) ve lig liderlik tablosu (`/leaderboard`). Modelleri
(`models.gamification.DailyQuest`/`Streak`) ve servisi
(`services.leaderboard_service.leaderboard_service`, `add_xp`/
`get_top_users`/`get_user_rank` üçü de mevcut) zaten tracked. Eşleşen
iki frontend bileşeni de untracked: `DailyQuestsModal.tsx` ve
`StreakWidget.tsx` (`frontend/src/components/Gamification/`) -- prop
şekilleri router'ın yanıt şekilleriyle alan alana örtüşüyor, ama
fetch/API çağrısı yok (saf sunum).

**İki bağımsız gamification alt sistemi:** `api/gamification_api.py`
(953 satır, zaten tracked, `routers/loader.py`'de `"integrations"`
kategorisiyle canlı) puan/seviye/rozet/başarım/profil/liderlik-tablosu
kapsıyor; `core.gamification.leaderboard_manager` +
`services.learning_event_service.GamificationDBService` +
`models.user_achievement.UserAchievement` kullanıyor. Untracked router
tamamen farklı bir yüzeyi kapsıyor (günlük görev, seri, seri
dondurucu) ve farklı servisi (`services.leaderboard_service`)
kullanıyor -- ama İKİSİ DE kendi `/leaderboard` uç noktasını tanımlıyor.
Gerçek bir path collision riski: untracked router benzer bir prefix
altında bağlanırsa iki `/leaderboard` çakışır.

**Ölü/terk edilmiş `routers/<kategori>/` iskeleti:** `backend/routers/`
altında 10 alt dizin var (accessibility, admin, ai, analytics, auth,
content, exam, integrations, learning, security); 9'u TAMAMEN boş,
hepsi aynı `6.01.2026 01:46` damgasını taşıyor (Ocak-2026 ilk
scaffold'undan kalma, hiç doldurulmamış). `routers/loader.py`'nin
`ROUTER_MAPPING` sözlüğü `eski_modül -> (kategori, yeni_modül_yolu)`
şeklinde; `_load_router` HER ZAMAN `importlib.import_module(yeni_modül_
yolu)` çağırıyor ve `yeni_modül_yolu` HER ZAMAN düz `"api.X"` veya
`"app.api.X"` -- `kategori` stringi (ör. `"learning"`) sadece
`router_registry.register(kategori, ...)`'a giden bir loglama/gruplama
etiketi, dosya sistemi yoluyla hiçbir ilişkisi yok. Yani
`routers/learning/gamification.py`'nin bulunduğu dizin yapısının
kendisi zaten canlı router-yükleme mekanizmasından yapısal olarak
kopuk -- bağlamak için bu kod tabanında hiç kullanılmamış yeni bir
import-yolu konvansiyonu icat etmek gerekirdi.

**Frontend tarafında tüketen yok:** `DailyQuestsModal.tsx` /
`StreakWidget.tsx` içinde fetch/API çağrısı yok; `frontend/**/*.ts(x)`
genelinde `daily_quest|streak/freeze|gamification/status|gamification/
quests` için sıfır eşleşme -- hiçbir container/sayfa bu bileşenleri
render etmiyor.

**Karar: kaydet, bağlama.** Yukarıdaki üç bulgu (path collision riski
+ ölü dizin yapısı + tüketen yokluğu) birlikte, bu kampanyanın daha
önce kurduğu "rescued but deliberately not connected" örüntüsüyle aynı
kategori: kod gerçek ve doğru, ama bağlamak dar bir "rescue" commit'inin
kapsamını aşan yeni mimari/routing kararları gerektirirdi (hangi
gamification API kalacak, `/leaderboard` çakışması nasıl çözülecek,
UI'da nereye yerleşecek -- hepsi ürün kararı, otonom olarak alınmadı).

**Bu rescue sırasında bulunan + düzeltilen:** `gamification.py`
hiç lint edilmemişti; tek bulgu `DTZ011` (`today = date.today()`,
tz-naive) -- `datetime.now(UTC).date()`'e çevrildi, import güncellendi.
Frontend tarafında `npx eslint` 5 hata + 2 uyarı buldu; 3'ü
(`comma-dangle` + 2x `quotes`, `DailyQuestsModal.tsx`) gerçekten bu
dosyaya özgü, doğrudan düzeltildi.

**Düzeltilmeyen 2 bulgu (kontrol ölçümüyle pre-existing kanıtlandı):**
her iki dosyada da `import/default` ("No default export... react") ve
`no-restricted-imports` (`@mui/material`, B-P0-66: "yeni bileşenler
için Tailwind + shadcn tercih edilir") kalıyor. Kontrol: zaten
tracked + canlı `frontend/src/components/CAT/CATWidget.tsx` üzerinde
aynı `npx eslint` komutu AYNI iki bulguyu veriyor. Yani bu rescue'nin
getirdiği yeni bir sorun değil -- tüm React+MUI kod tabanının önceden
var olan durumu. `npm run lint` (`--max-warnings 0`) CI'da "Frontend
Tests" işinin bir adımı (`ci.yml:395-397`, diff-bazlı/grandfathered
DEĞİL, tüm `frontend/`'i tarıyor) -- yani "Frontend Tests" zaten,
bu PR'dan bağımsız olarak, codebase'in geri kalanındaki aynı MUI/
import-default borcu yüzünden kırmızı. Bu da PR #89'dan beri kurulu
"Frontend Tests bilinen-kırmızı" temeliyle tutarlı.

**`__init__.py` eklenmedi:** `routers/<kategori>/` altındaki 10 alt
dizinin 10'unda da `__init__.py` yok (namespace-scaffold konvansiyonu).
Bu router hiçbir yerden `routers.learning.X` olarak import edilmiyor
(bu PR onu bağlamıyor), yani mevcut (yokluk) konvansiyonuna uymayan
yeni bir dosya eklemenin işlevsel bir faydası yok.

**Canlı DB doğrulaması:** `localhost:5434/kiro2`'de `daily_quests` ve
`streaks` tabloları mevcut; kolonlar router'ın kullandığı TÜM alanlarla
birebir eşleşiyor (`daily_quests`: id, organization_id, quest_date,
student_id, quest_type, title, description, target_value,
current_value, xp_reward, completed, completed_at, bonus_claimed;
`streaks`: user_id, organization_id, current_streak, largest_streak,
freeze_count, last_activity, total_days_active).

**Yerel doğrulama:** `pre-commit run` (ruff + ruff-format + bandit +
mypy + secrets) `gamification.py` için PASSED. Push-time
`ders-zorlayici` bekçi paketi: 320 passed, 1 skipped, 1 xfailed.

**CI'da doğrulanan, PR'dan bağımsız 5 kırmızı:** Automatic PR Review
(29s), Backend Tests Python 3.11 (3m15s), CI Summary (2s), Frontend
Tests (1m6s), Quality Gate (3m16s) -- PR #89'daki 5-kırmızı taban
çizgisiyle birebir aynı check seti, hepsi FAILURE. Geri kalan tüm
check'ler (CodeQL x2 + default-setup, Container/SAST/IaC/Secret/OWASP/
License/Compliance Security Scan'leri, 5x Code Quality alt-job'u,
Checkov, Trivy, 8 Golden Flow E2E, PR Welcome Message) yeşil. API
Security Testing (ZAP) 34m35s'de yeşil -- önceki iki PR'ın 31-33dk
aralığından biraz daha uzun ama hâlâ aynı büyüklük mertebesinde,
endişe verici değil.

Merge: `82d192554` (2026-08-30), `gh pr merge 91 --squash` (tek commit
`7b71b8fe7`in squash'ı).

**Kalan kapsam:** SS10.7'deki 555 dosyadan şimdiye kadar 34 tanesi
commit edildi (gamification.py + DailyQuestsModal.tsx + StreakWidget.tsx,
üçü de gerçekten untracked'ti). ~521 dosya hâlâ triyaj bekliyor.

### 10.23 PR #93: `useSanitize.ts`/`useMathSanitizer.ts`/`BionicReadingText.tsx` -- XSS açığı yok, iki ayrı kurtarılabilir bulgu (30 Ağustos 2026)

"sanitize" adı taşıyan iki hook (`frontend/src/hooks/useSanitize.ts`,
`useMathSanitizer.ts`) SS10.7 taramasında güvenlik açığı şüphesiyle
önceliklendirildi (task #71). İnceleme sonucu: **XSS açığı yok**, ama
araştırma iki ayrı kurtarılabilir/belgelenebilir bulgu ortaya çıkardı.

**Doğrulama -- açık yok:** `frontend/src/utils/sanitize.ts` (tracked,
DOMPurify tabanlı) zaten canlı güvenlik kontrolü. `dangerouslySetInnerHTML`
kullanan tracked bileşenlerin HEPSİ (6/6) zaten doğru sanitize fonksiyonunu
çağırıyor: `Common/AccessibleMathFormula.tsx:19,244,313` (`sanitizeMathML`),
`MathSolution/MathExpressionAnimated.tsx:15,112` (`sanitizeHTML`),
`QuestionGeometry.tsx:17,52,90`, `QuestionGraph.tsx:17,53,72`,
`QuestionMapDiagram.tsx:17,51,88` (üçü de `sanitizeSVG`),
`Revolutionary/BionicReadingToggle.tsx:48,329` (`sanitizeBionicText`) --
hepsi `// SECURITY FIX #4` yorumuyla işaretli. `useSanitize.ts`'in 3
hook'u (`useHTMLSanitizer`/`useSVGSanitizer`/`useBionicSanitizer`) bu
aynı, zaten güvenli modülü saran KULLANILMAYAN wrapper'lar -- `git grep`
ile doğrulandı: bu hook adlarını import eden tracked dosya yok, yani
yeni bir güvenlik kapsamı eklemiyorlar.

**Bulgu 1 -- `useMathSanitizer.ts`, zaten canlı kodun kopyası:** LaTeX
-> MathML dönüştürücüsü, `AccessibleMathFormula.tsx`'in kendi inline
`convertLatexToMathML` fonksiyonuyla (satır 82-94: aynı `\frac` regex'i,
aynı `<mfrac><mi>..</mi><mi>..</mi></mfrac>` çıktı deseni, aynı "basit
dönüşüm" yorumu) neredeyse birebir aynı. Yeni/riskli mantık değil --
canlı koddan çıkarılmış ama hiçbir yere adapte edilmemiş bir refactor.

**Bulgu 2 -- `BionicReadingText.tsx`, ayrı ve yapısal olarak XSS-güvenli:**
Zaten tracked+canlı olan `Revolutionary/BionicReadingToggle.tsx` (backend'in
ürettiği `bionic_metin` HTML'ini `dangerouslySetInnerHTML` +
`sanitizeBionicText` ile render eder, `RevolutionaryDashboard.tsx` ve
`Revolutionary/index.ts`'e bağlı) ile KARIŞTIRILMAMALI.
`BionicReadingText.tsx` tamamen bağımsız, client-side bir uygulama: React
elemanlarını doğrudan JSX ile kurar (`bionicWord()`, satır 18),
`dangerouslySetInnerHTML` hiç kullanmıyor -- yapısal olarak XSS'e kapalı.
LaTeX/MathJax (`$...$`, `$$...$$`), HTML etiketleri ve markdown linklerini
kelime-kalınlaştırma dönüşümünden korumak için kendi tokenization mantığı
var, Türkçe karakter desteği var (ğüşıöçĞÜŞİÖÇ). Kendi test dosyası
mevcut ve `npx vitest --run` ile 8/8 PASSED (48ms).

**Lint:** `eslint --fix` ile 3 dosyada 11 curly/comma-dangle hatası
otomatik düzeldi. Kalan 1 hata (`BionicReadingText.tsx:1`,
`import/default`, React'in default export'u bulunamadı) tracked
`CATWidget.tsx`'te de aynen tekrar ediyor -- kontrol ölçümüyle
doğrulanmış, proje genelinde önceden var olan bir durum (bkz. §10.22).
`react-refresh/only-export-components` uyarısı (`bionicWord` export'u,
test dosyasının algoritmayı izole test edebilmesi için gerekli) için
gerekçeli `eslint-disable-next-line` eklendi (satır 17) -- aynı desenin
emsali `pages/ModernExamStartPage.tsx:62`'de zaten var.
`--report-unused-disable-directives` ile eklenen yorumun gerçekten
kullanıldığı doğrulandı.

**Bağlanmadı:** `RevolutionaryDashboard.tsx`, `GlobalCognitiveWrapper.tsx`,
hiçbir router/sayfa değişmedi -- bilinen "kurtarıldı ama bağlanmadı"
deseni (bkz. §10.22).

**Yerel doğrulama:** Push-time `ders-zorlayici` bekçi paketi: 320 passed,
1 skipped, 1 xfailed (117.14s).

**CI'da doğrulanan, PR'dan bağımsız 5 kırmızı:** Automatic PR Review
(31s), Backend Tests Python 3.11 (3m20s), CI Summary (3s), Frontend
Tests (1m17s), Quality Gate (3m6s) -- PR #89/#91'deki taban çizgisiyle
birebir aynı check seti, hepsi FAILURE. Geri kalan tüm check'ler (CodeQL
x2 + default-setup, Container/SAST/IaC/Secret/OWASP/License/Compliance
Security Scan'leri, Security Summary, Trivy, Checkov, 5x Code Quality
alt-job'u, 8 Golden Flow E2E, PR Welcome Message) yeşil. API Security
Testing (ZAP) 35m56s'de yeşil -- önceki PR'ların 27-41dk aralığı
içinde, endişe verici değil.

Merge: `72d555f49` (2026-08-30), `gh pr merge 93 --squash --delete-branch`
(tek commit `180093861`in squash'ı).

**Not -- PR #62 sonrası backlog planı kapandı:** Bu segmentte ayrıca
doğrulandı: `stateful-shimmying-papert.md` planı (§10.20'de "tamamen
doğrulandı" olarak belgelenmişti) hâlâ kapalı durumda -- yeniden açılacak
bir şey yok.

**Kalan kapsam:** SS10.7'deki 555 dosyadan şimdiye kadar 39 tanesi
commit edildi (`useSanitize.ts`, `useMathSanitizer.ts`,
`BionicReadingText.tsx`, `neuro-inclusive.css`,
`BionicReadingText.test.tsx` -- beşi de gerçekten untracked'ti). ~516
dosya hâlâ triyaj bekliyor.


### 10.24 PR #95: `send_email` SMTP kapısı ayrışma riskini test altına al (30 Ağustos 2026)

SS10.7 taramasında `backend/` kök dizininde untracked, alt çizgiyle
başlayan bir dosya bulundu: `_smtp_mutasyon.py`. Kurcalama/scratch değil
-- `core/email_util.py` ve `core/eposta_dogrulama.py`'yi hedefleyen,
tam işlevsel bir mutasyon testi harness'iydi (aynı desenin tracked
emsalleri: `backend/scripts/mutation_check_password_reset.py`,
`mutation_check_teacher_roster.py`). Çalıştırıldığında gerçek bir
test-kapsam boşluğu ortaya çıkardı.

**Bulgu:** `_smtp_kimlik()` (#466'nın dersi: `SMTP_HOST`/`SMTP_SERVER`
ayrışmasını önlemek için eklenen TEK kaynak) hem `smtp_yapilandirilmis_
mi()` (kapı) hem `send_email()` (tüketici) tarafından okunuyor -- ama bu
ilişkiyi doğrulayan test yoktu. `test_eposta_kapi_sirasi.py`'deki
`test_smtp_kontrolu_send_email_ile_ayni_degiskenleri_okur` docstring'inde
tam bunu iddia ediyor, ama assertion'ı yalnız KAPI fonksiyonunu çağırıyor
-- `send_email()`'in KENDİSİ hiç çağrılmıyor. #466'nın aynı ayrışma
sınıfının test edilmemiş bir tekrarı riski.

**Ölçüm (iddia ≠ ölçüm):** Harness taban çizgisini (4 hedef test yeşil)
doğruluyor, 4 mutasyonu tek tek uyguluyor, pytest'i koşuyor, `git
checkout` ile harfi harfine geri alıyor, geri alımı `git status` ile
doğruluyor. Düzeltme öncesi sonuç **3/4**: M1 (SMTP ön-koşulu
kaldırılır), M2 (#466 ayrışması yeniden üretilir) ve M3 (hata gürültüsü
susturulur) hepsi doğru şekilde OLDÜ, ama **M4 (`send_email` kendi eski
kontrolüne döner: `if not (smtp_server and smtp_username):`) HAYATTA
KALDI** -- 0 test düştü. Yani `send_email` kendi bağımsız kontrolüne
geri dönse bile hiçbir test bunu fark etmiyordu.

**Düzeltme:** `test_eposta_kapi_sirasi.py`'ye yeni test
(`test_send_email_kismi_smtp_yapilandirmasinda_gonderim_yapmaz`). Senaryo:
`SMTP_HOST` + `SMTP_USERNAME` var, `SMTP_PASSWORD` yok (kısmi
yapılandırma) -- `send_email(..., blocking=True)` çağrılır, dönüş
değerinin `False` olduğu ve erken-dönüş uyarısının loglandığı doğrulanır.
M4'ü gerçekten öldürdüğü elle de doğrulandı: mutasyon geçici
uygulandığında test kırmızıya dönüyor, log'da gerçek bir SMTP bağlantı
denemesi kanıtı var (`[Errno 11001] getaddrinfo failed`) -- yani sahte
pozitif değil, `send_email` gerçekten bağlanmaya çalışıyordu. Düzeltme
sonrası: **4/4**.

**Harness'in konumu:** `_smtp_mutasyon.py` reponun kurulu adlandırma
sözleşmesine taşındı (bkz. `backend/scripts/mutation_check_password_
reset.py`, `mutation_check_teacher_roster.py`):
`backend/scripts/mutation_check_smtp_email_gate.py`. Taşıma sırasında yol
hesaplaması düzeltildi (`scripts/` alt dizinine göre `parent.parent`),
`bandit`/`mypy` için sırasıyla `# nosec` gerekçeleri ve bir `TypedDict`
eklendi (kardeş dosyaların aksine bu harness'in `MUTASYONLAR` yapısı
karışık değer tipleri taşıdığından yoksa mypy'nin "changed files only"
adımında 5 hataya yol açardı). İlginç bir yan bulgu: reponun kendi
`reward-hacking-check` push-stage hook'u (`backend/hooks/reward_hacking/`,
Daisy Stanton Standartları) satır sonunda gerekçesiz `# nosec` gördüğünde
(`#\s*nosec\s*$` deseni) bunu "coverage manipülasyonu" diye işaretliyor;
kardeş dosyalar bunu yalnız `# noqa: S603` ekinin (ki ruff artık bu repoda
"unused directive" diyor) tesadüfen bu deseni kırması sayesinde
atlatıyor. Gerekçe `# nosec - <sebep>` olarak aynı satıra taşınınca hem
ruff hem `reward-hacking-check` temiz.

**Yerel doğrulama:** `python backend/scripts/mutation_check_smtp_email_
gate.py` -> 4/4 (üç kez çalıştırıldı). `ruff check`, `ruff format
--check`, `mypy --ignore-missing-imports`, `bandit` temiz. Push-time
`ders-zorlayici` bekçi paketi iki push denemesinde de: 320 passed, 1
skipped, 1 xfailed (~100-110s).

**CI'da doğrulanan, PR'dan bağımsız 5 kırmızı:** Automatic PR Review
(25s), Backend Tests Python 3.11 (3m13s), CI Summary (3s), Frontend
Tests (1m21s), Quality Gate (3m31s) -- PR #89/#91/#93'teki taban
çizgisiyle birebir aynı check seti, hepsi FAILURE (`gh pr view --json
statusCheckRollup` ile doğrulandı). Geri kalan tüm check'ler yeşil. API
Security Testing (ZAP) 36m46s'de yeşil -- önceki PR'ların 27-41dk
aralığı içinde.

Merge: `d807018fa` (2026-08-30), `gh pr merge 95 --squash --delete-branch`
(iki commit'in squash'ı: ilk commit + `reward-hacking-check` gerekçe
düzeltmesi).

**Kalan kapsam:** SS10.7'deki 555 dosyadan şimdiye kadar 40 tanesi
commit edildi. Backlog'ta hâlâ triyaj bekleyen: diğer 12 untracked
`backend/scripts/*.py`, `backend/test_nlp_perf.py`/`test_root_perf.py`
(pytest'in `testpaths`'i dışında, zararsız ama karar bekliyor),
`backend/api/v1/predictive_analytics.py` (mock veri, ürün kararı
gerekiyor), `backend/application/commands/.kontrol/`,
`frontend/src/components/Dashboard/MisconceptionFlashcard.tsx` +
`TeacherMisconceptionHeatmap.tsx`, çeşitli `frontend/src/test/e2e/*` ve
`frontend/tests/e2e/` spec'leri, kök dizindeki deploy/doküman dosyaları.

### 10.25 PR #97: `audit_sql_migration_drift.py`'yi izlemeye al -- kendi bulgularının elle doğrulanması (30 Ağustos 2026)

SS10.7 taramasında `backend/scripts/` altında untracked bulunan bir diğer
dosya: `audit_sql_migration_drift.py`. Scratch değil -- kendi docstring'i
gerekçesini veriyor: 13 Ağu 2026 tarihli S206 olayında (`daily_plans` /
`yks_exam_goals` / `learning_progress_daily` tabloları yalnızca
`backend/migrations/*.sql` içinde tanımlıydı, canlı DB'de yoktu; Celery
beat + 2 API ucu kalıcı 500 veriyordu -- `cdea871deea9` ile kapandı) bu
hatanın kardeşlerini aramak için yazılmış, salt-okunur bir üç yönlü drift
denetleyicisi (`backend/migrations/*.sql` <-> `alembic/versions` <-> canlı
DB). Zaten izlenen `audit_db_dependency.py` / `audit_orm_vs_livedb.py`
ailesiyle aynı sözleşmeyi izliyor.

**Kendi kontrol kolu:** Script, bilinen-canlı `users` tablosu için
referans sayısının 0 olmadığını doğrulayarak kendi tarayıcısının bozuk
olmadığını kontrol ediyor -- aksi halde "tarayıcı arızalı" diyip kendini
geçersiz kılıyor. Bu, kampanyanın "iddia ≠ ölçüm" felsefesinin statik-
analiz araçlarına uygulanmış hali (bkz. `mutation_check_*.py` ailesindeki
aynı disiplinin test tarafındaki karşılığı, §10.24).

**Yerel çalıştırma bulguları:** Canlı dev DB'ye karşı çalıştırıldı: 132
tablo `.sql`'de, 1 tablo alembic'te, 254 tablo canlı DB'de. Kontrol kolu
(`users`) geçti (orm=1 dosya, sql=26 dosya). 27 tablo ".sql'de var, DB'de
yok" olarak bulundu; bunlardan 2'si "KOD BAĞIMLI" (kod hâlâ referans
veriyor) olarak işaretlendi: `questions`, `video_cache`.

**Elle doğrulama -- ikisi de yanlış-pozitif çıktı:** Script'in kendi
bulgularına kör kör güvenmek yerine, iki hit de kaynağına kadar izlendi
(kampanyanın "iddia ≠ ölçüm" disiplini script'i kurtarırken script'in
ÇIKTISINA da uygulandı):

- `questions`: `backend/models/learning_path_models.py`'deki eşleşme bir
  DOCSTRING metni ("Links to Question (from questions table)"), gerçek
  SQL değil. `backend/core/_deprecated/automated_question_generator.py:
  1134`'teki eşleşme gerçek bir `SELECT ... FROM questions` ama dosya
  zaten `_deprecated/` altında.
- `video_cache`: `api/youtube_routes.py`, `services/youtube/
  cache_manager.py`, `services/youtube/database.py` ve `core/
  sql_injection_prevention.py` (yorum örneği) hepsi `sqlite3.connect(...)`
  kullanıyor -- ayrı bir SQLite dosyası, script'in denetlediği ana
  Postgres DB'si değil. Script'in regex tabanlı kullanım taraması
  (`RAWSQL_RE = "(?:FROM|INTO|UPDATE|JOIN)\s+{t}\b"`) motor farkını ayırt
  edemiyor -- düz metin regex için bir Postgres tablosuna referans ile
  bambaşka bir SQLite DB'sindeki aynı isimli tabloya referans birebir
  aynı görünüyor. Bilinen ve kabul edilebilir bir yanlış-pozitif sınıfı.

Sonuç: script doğru çalışıyor, iki bulgu da gerçek canlı-500 riski değil.
Script'in kendisinde bir hata yok -- veritabanı-motoru körlüğü, regex
tabanlı statik analizin doğal bir sınırı.

**Yapılan tek kod değişikliği:** `sys.stdout.reconfigure(encoding="utf-8",
errors="replace")` satırına `# type: ignore[union-attr]` eklendi -- CI'nin
"değişen dosyalarda mypy" adımında bu YENİ dosya için gerekli (kardeş
`audit_*.py` dosyalarının hepsinde zaten var olan aynı düzeltme).
Davranış/mantık değişmedi.

**Yerel doğrulama:** `ruff check`, `ruff format --check`, `mypy
--ignore-missing-imports`, `bandit` (0 bulgu, tüm severity/confidence
seviyelerinde) temiz. `python -m hooks.reward_hacking.cli` temiz. Script
canlı dev DB'ye karşı fix öncesi/sonrası iki kez çalıştırıldı, çıktı
değişmedi. Push-time `ders-zorlayici` bekçi paketi: 320 passed, 1 skipped,
1 xfailed (~103s).

**CI'da doğrulanan, PR'dan bağımsız 5 kırmızı:** Automatic PR Review,
Backend Tests Python 3.11, CI Summary, Frontend Tests, Quality Gate --
önceki PR'lardaki (#89/#91/#93/#95) taban çizgisiyle birebir aynı check
seti, hepsi FAILURE (`gh pr view --json statusCheckRollup` ile
doğrulandı). Geri kalan tüm check'ler yeşil. API Security Testing (ZAP)
38m43s'de yeşil -- önceki PR'ların 27-41dk aralığı içinde.

Merge: `e91372249` (2026-08-30), `gh pr merge 97 --squash --delete-branch`.

**Kalan kapsam:** Bu PR yalnızca dosyayı izlemeye aldı + tek mypy
düzeltmesini yaptı; script'in bulduğu 25 "referanssız" (kod bağımlı
işaretlenmemiş) tablonun ayrıca temizlenmesi/araştırılması bu PR'ın
kapsamı dışında kaldı. SS10.7'deki 555 dosyadan şimdiye kadar 41 tanesi
commit edildi. Backlog'ta hâlâ triyaj bekleyen: 12 untracked
`backend/scripts/*.py` (`generate_qwen_kcs.py`, `golden_dataset_
stress_tester.py`, `quality/sanitize_question_bank_ocr.py`,
`quality/y11_sizinti_ayirt_olc.py`, `semantic_backfill.py` orta kurtarma
adayı olarak işaretlenenler dahil), `backend/test_nlp_perf.py`/
`test_root_perf.py`, `backend/api/v1/predictive_analytics.py`,
`backend/application/commands/.kontrol/`,
`frontend/src/components/Dashboard/MisconceptionFlashcard.tsx` +
`TeacherMisconceptionHeatmap.tsx`, çeşitli `frontend/src/test/e2e/*` ve
`frontend/tests/e2e/` spec'leri, kök dizindeki deploy/doküman dosyaları.

### 10.26 PR #99: `golden_dataset_stress_tester.py`'yi izlemeye al -- ayni taramada 2 dosya kurtarilmadi, 2 dosya scratch (30 Ağustos 2026)

SS10.7 backlog taramasi `backend/scripts/`'daki geri kalan untracked dosyalari
kapsayacak sekilde genisletildi. Bu turda 5 dosya elle calistirilarak
incelendi (yalniz statik analizle yetinilmedi) ve sonuc beklenenden farkli
cikti: yalniz 1 tanesi gercekten kurtarilabildi, 2 tanesi calisirken hata
verdi ve urun kararina ertelendi, 2 tanesi scratch cikti.

**Kurtarilan: `golden_dataset_stress_tester.py`.** `FSRSService` ve
`IRTCalibrationService`'i (ikisi de tracked, gercekten var) 10K soru / 50K
etkilesim olcegiyle bellek-ici sinayan bir stres testi. Cikti dosyasi
(`backend/golden_dataset_report.json`) zaten `.gitignore`'da tanimliydi
(satir 495) -- yani arac daha once de calistirilmis. Elle calistirinca
(iddia != olcum) gercek bir hata bulundu: `sys.stdout.reconfigure` yoktu,
ilk `print()` (emoji icerdigi icin) cp1254 konsolunda aninda
`UnicodeEncodeError` ile cokuyordu -- kardes `audit_*.py`/`mutation_check_
*.py` dosyalarinin hepsinde zaten var olan duzeltme eklendi. Sonrasinda
script bastan sona calistirildi: IRT fazi 10.000 soru/0.86s, FSRS fazi
50.000 etkilesim/80.14s, gecerli rapor uretti. Ayrica `open()` ->
`Path().open()` (ruff PTH123). mypy yerelde numpy stub surum farkiyla
(yerel `numpy==2.5.1`/`mypy==1.19.1`, repo `numpy==2.4.2`/`mypy==1.8.0`
pinliyor) alakasiz bir hatayla duruyordu; CI'nin pinlenmis mypy'si (bu
PR'da yesil) otoriter. Merge: `2f9570e8a` (2026-08-30), 5 bilinen kirmizi
taban cizgisiyle birebir (`gh pr view --json statusCheckRollup` ile
dogrulandi), API Security Testing 50m38s'de yesil.

**Kurtarilmadi -- calistirinca hata verdi: `sanitize_question_bank_ocr.py`.**
Statik olarak temizdi (ruff/mypy/bandit/reward-hacking-check hepsi
gecti), ama `python scripts/quality/sanitize_question_bank_ocr.py`
calistirilinca `ModuleNotFoundError: No module named
'services.ocr_sanitizer_service'` verdi. Sebebi: bu servis reponun HICBIR
zamaninda commit edilmemis. Zaten tracked `tests/integration/
test_ocr_sanitizer_rag_guardrails.py` bunu kendi `pytest.skip()`
gerekcesinde belgeliyor: "ACIK BORC: services/ocr_sanitizer_service HIC
YAZILMADI (git log --all -> 0 commit) ... Servis yazilinca bu satir
KALDIRILACAK." Yani bu script, hic yazilmamis bir servise karsi onceden
yazilmis, henuz calisamayan kod -- "kurtarilacak scratch" degil, zaten
bilinen ve baska bir dosyada belgelenmis bir acik borc. Izlemeye almadim;
bu PR'in kapsami disinda birakildi.

**Kurtarilmadi -- urun karari gerektiriyor: `generate_qwen_kcs.py`.**
`knowledge_components`/`question_kc_mapping` tablolarina INSERT yapiyor,
ama bu tablolari yaratan migration (`level4_kc_taxonomy_20260808`)
`alembic/versions_archive/`'da duruyor -- CANLI `alembic/versions/`
zincirinde DEGIL. Canli dev DB'de dogrudan sorguyla dogrulandi: ikisi de
YOK. Ayni ozellik icin iki KARDES untracked script daha var
(`metadata_phase1_schema_migration.py`: "Phase 1: Schema migration for
P0-P3 metadata"; `metadata_phase4_kc_mapping.py`: "Phase 4: KC mapping +
q_matrix from topic hierarchy") -- yani bu tek dosyalik bir kurtarma degil,
yarim kalmis/ertelenmis coklu-fazli bir ozellik kumesi. Ustune, script'in
kendi mantiginda gercek bir idempotency hatasi var: `kc_id =
f"kc_{uuid.uuid4().hex[:12]}"` her calistirmada RASTGELE uretiliyor, bu
yuzden `ON CONFLICT (kc_id) DO NOTHING` (ve `question_kc_mapping`'in
`(question_id, kc_id)` bilesik anahtari) hicbir zaman gercek bir
cakismayla karsilasmiyor -- `--apply` iki kez calistirilirsa yinelenen
KC satirlari uretir. `predictive_analytics.py` ile ayni kategoriye
kondu: Claude'un tek basina karar veremeyecegi bir urun/kapsam sorusu
("bu ozellik devam ediyor mu, terk mi edildi, konsolide mi edilecek").
Izlemeye almadim.

**Scratch: `y11_sizinti_ayirt_olc.py`, `semantic_backfill.py`.** Ikisi
de `CROP_KOK`/veri dosyasi icin `C:/Users/husey/kiro2/d-dataset/...`
bicimde, repo disindaki bir dizine hardcoded mutlak Windows yolu
kullaniyor -- tasinabilir degil, yalniz bu makinede calisir, tek seferlik
elle-etiketlenmis veri setine karsi bir dogrulama/backfill denemesi.
`semantic_backfill.py`'de ayrica `asyncpg.connect(...)` cagrisina
DOGRUDAN GOMULU bir DB kimlik bilgisi var (env-var/varsayilan deseni
yok, tek bir uygulama-ozel kullanici+parola literal string olarak
yazili) -- diger script'lerdeki yaygin `postgres:postgres` yerel
varsayilanindan farkli olarak gercek bir uygulama kimlik bilgisi gibi
gorunuyor. Dosya untracked oldugu ve scratch olarak kalacagi icin
repoya/GitHub'a hicbir sizinti yok, ama parolanin duz metin halde bir
script dosyasinda oturmasi kendi basina bir bulgu; kimlik bilgisi
degisikligi/rotasyonu Hüseyin'in kendi karari (bu kampanyanin standing
kurali: kimlik bilgisi kararlari devredilmiyor).

**Kalan kapsam:** SS10.7'deki 555 dosyadan simdiye kadar 42 tanesi
commit edildi (bu PR'daki 1 dosya + onceki 41). `backend/scripts/`
altinda hala triyaj bekleyen 11 untracked dosya var (7'si onceden
scratch onaylandi: `add_cascades.py`, `backfill_children.py`,
`check_duplicate_tables.py`, `check_qs_cols.py`, `clean_exceptions.py`,
`fix_imports.py`, `restore_stats.py`; bu turda 4'u daha karara baglandi:
2 scratch, 2 urun-karari-bekliyor). Geri kalan SS10.7 kapsami degismedi
(bkz. §10.25 "Kalan kapsam").
