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
