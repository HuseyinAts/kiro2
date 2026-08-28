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

## 5. Kapı olmaktan çıkarılanlar ve gerekçeleri

| Adım | Durum | Gerekçe |
|---|---|---|
| Terrascan | `continue-on-error` | Tenable projeyi **arşivledi**. Taradığı üç çerçeve (docker, k8s, github) Checkov'un kapsamında; bilgi olarak duruyor, kapı Checkov. |
| `safety check` | **Kaldırıldı** | 01.06.2024'te deprecate edildi, Safety 3.x hesap/API anahtarı istiyor. Aynı işi anahtarsız ve bakımı süren `pip-audit` yapıyor. |
| Snyk | `if: env.SNYK_TOKEN != ''` | Token yoksa adım her koşulda hata veriyordu. Token tanımlıysa aynen çalışır. |
