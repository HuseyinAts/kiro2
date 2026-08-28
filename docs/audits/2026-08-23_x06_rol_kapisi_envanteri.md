# X06 — Rol kapısı envanteri (ölçüm; kod değişikliği YOK)

**Tarih:** 23 Ağustos 2026 (S249 / İ3) · **Plan:** `docs/superpowers/plans/2026-08-23-acik-kalemler-uygulama.md` Task 3
**Kapsam kararı:** kullanıcı onayıyla bu turda **yalnız envanter**; birleştirme yapılmadı.
**Yöntem:** salt-okunur kod ölçümü + üç canlı çalıştırma. Taranan: `backend/` altında
test-dışı **1.886** `.py` dosyası (tarayıcı kapsamı ajan tarafından ilan edildi).

---

## 0. Belirleyici soru ve cevabı

Kütük "5+ ayrı implementasyon var" diyordu. **Sayı tek başına kusur değildir** —
kusur **tutarsızlıktır**. Bu yüzden envanterin cevaplaması gereken tek soru şuydu:

> *İki kapı aynı rolü farklı mı yargılıyor?*

**Cevap: EVET — üç farklı biçimde, üçü de canlı çalıştırmayla kanıtlandı (§3).**
→ **X06 kütükte `dogrulandi` KALIR.**

---

## 1. Sayı mutabakatı — kütüğün "21 tanım / 6 dosya"sı aynı ölçümden gelmiyor

| Ölçüm | Tanım | Dosya |
|---|---|---|
| `backend/core/*.py`, tüm `def require_*` | **23** | **6** ← gerçek |
| `backend/core/**/*.py` özyinelemeli | 25 | 7 |
| `backend/core/*.py`, yalnız `indent=0` | 21 | 5 |

Yani kütüğün "21" ve "6 dosya" rakamları **aynı grep'ten üretilemez**: 21 → 5 dosya,
6 dosya → 23 tanım. Bu turda **23 / 6** kanon alındı.

**Elenen sahte çağıranlar (3):** `audit_api.py:111` (yorum satırı) ·
`teacher_classroom.py:53` (yorum) · `scripts/audit_missing_auth.py:68,73` (dize sabiti).
Ayrıca `auth_dependencies.py:474,486` dosya sonundaki `# Example usage` üçlü-tırnak
bloğunun içinde — `sed -n '455,475p'` ile doğrulandı.

---

## 2. Envanter (23 tanım · çağıran = test-dışı üretim dosyası sayısı)

| # | Ad | Dosya:satır | Çağıran | Durum | Kabul ettiği roller |
|---|---|---|---|---|---|
| 1 | `require_user_access` | `auth_dependencies.py:256` | 0 | **ÖLÜ** | rol yok; `manage_users` + `allow_self` |
| 2 | `require_content_access` | `auth_dependencies.py:265` | 0 | **ÖLÜ** | rol yok; `manage_content` |
| 3 | `require_exam_access` | `auth_dependencies.py:272` | 0 | **ÖLÜ** | rol yok; `manage_exams` |
| 4 | `require_analytics_access` | `auth_dependencies.py:279` | 0 | **ÖLÜ** | rol yok; `view_analytics` |
| 5 | `require_authentication` | `auth_dependencies.py:287` | 0 | **ÖLÜ** | **NO-OP dekoratör** |
| 6 | `require_authorization` | `auth_dependencies.py:303` | 0 | **ÖLÜ** | **NO-OP — gövde hiç kontrol yapmıyor** |
| 7 | **`require_role` [A]** | `auth_dependencies.py:322` | **6** | CANLI | `*roles → .lower()`; boşsa `[admin, super_admin]`; **"admin" varsa `+super_admin`** |
| 8 | `require_permission` | `auth_dependencies.py:336` | 0 | **ÖLÜ** | perm; boşsa `["read"]` |
| 9 | `require_roles` | `authorization.py:19` | 0 | ÖLÜ* | `list[KullaniciRolu]` = **Türkçe** değerler |
| 10 | `require_owner_or_roles` | `authorization.py:36` | 0 | ÖLÜ* | owner VEYA `list[KullaniciRolu]` |
| 11 | `require_admin` | `authorization.py:66` | 0 | **ÖLÜ** | `["admin"]` — **SUPER_ADMIN YOK** |
| 12 | `require_teacher_or_admin` | `authorization.py:79` | 0 | **ÖLÜ** | `["ogretmen","admin"]` |
| 13 | `require_student_owner_or_privileged` | `authorization.py:92` | 1 | CANLI | owner VEYA `["ogretmen","admin","veli"]` |
| 14 | `require_veli_consent` | `dependencies.py:409` | 1 | CANLI | rol değil — veli onayı |
| 15 | `require_org_role` | `dependencies.py:520` | 2 | CANLI | org_role **BÜYÜK HARF**; `SCHOOL_ADMIN` **her kapıyı geçer** |
| 16 | `require_dpa_signed` | `dependencies.py:542` | 1 | CANLI | rol değil — DPA imzası |
| 17 | `AuthenticationContext.require_permission` | `enhanced_authentication.py:348` | 0 | **ÖLÜ** | perm; **RED = TypeError (500)** |
| 18 | **`AuthenticationContext.require_role` [C]** | `enhanced_authentication.py:370` | 0 | **ÖLÜ** | `*roles: str`, **tam eşitlik, normalizasyon YOK**; **RED = TypeError (500)** |
| 19 | **`require_role` [B]** | `jwt_auth.py:860` | 0 | **ÖLÜ** | `list[UserRole]` **BÜYÜK HARF**; **super_admin genişletmesi YOK** |
| 20 | `require_permission` | `jwt_auth.py:898` | 0 | **ÖLÜ** | perm; `SUPER_ADMIN` veya `"*"` **bypass** |
| 21 | `require_admin` | `jwt_auth.py:937` | 1 | CANLI | `[ADMIN, SUPER_ADMIN]` BÜYÜK HARF |
| 22 | `require_permission` | `learning_path_auth.py:213` | 0 | **ÖLÜ** | perm; `"*"` bypass |
| 23 | **`require_role` [D]** | `learning_path_auth.py:259` | 0 | **ÖLÜ** | `*UserRole`; `ADMIN` varsa `+SUPER_ADMIN` |

`ÖLÜ*` = harici çağıran 0, yalnız kendi dosyası içinden çağrılıyor.
Ek (özyinelemeli tarama): `unified/auth_system.py:581/:600` — üretim çağıranı **0**.

> **23'ün 16'sı ÖLÜ.** Canlı olan 7'nin 3'ü rol kapısı bile değil
> (`veli_consent`, `dpa_signed`, `org_role`).

---

## 3. Tutarsızlık kanıtı — üç canlı çalıştırma

### 3.1 Aynı girdi, iki implementasyon, ZIT karar

```
AYNI GIRDI: kullanici rolu SUPER_ADMIN, kapi "admin" istiyor
  A) auth_dependencies : required=['admin','super_admin'] user='super_admin' -> KABUL
  B) jwt_auth          : RED -> HTTPException 403
                         "Insufficient permissions. Required roles: ['ADMIN']"
```

Fark tek satırlık: `auth_dependencies.py:331` "admin" istenince listeye
`super_admin`'i **otomatik ekliyor**; `jwt_auth.py:886` eklemiyor.

### 3.2 Türkçe rol değeri — iki kapı zıt

```
AYNI GIRDI: KullaniciRolu.OGRETMEN = "ogretmen", kapi "teacher" istiyor
  auth_dependencies                      -> 'ogretmen' in ['teacher'] -> RED
  teacher_classroom.py:58 _STAFF_ROLLERI -> KABUL
```

### 3.3 🔴 Bir rol kapısı 403 değil **500** üretiyor

```
ctx = AuthenticationContext(user_id='u1'); ctx.role='student'; ctx.require_role('admin')
  -> firlatilan tip : builtins.TypeError
  -> mesaj          : AuthorizationError.__init__() got an unexpected keyword
                      argument 'severity'
  -> HTTPException mi? : False
```

Kaynak: `enhanced_authentication.py:381` →
`raise AuthorizationError(msg, severity=…, context={…})`
İmza: `core/exceptions.py:61` → `def __init__(self, message: str = "…")`.

Bugün üretim çağıranı **0** (ÖLÜ), yani **canlı etkisi yok**. Ama bu kapı
birleştirme sırasında canlandırılırsa **yetki reddi yerine sessiz 500** üretir.
Bu yüzden birleştirmeden **önce** kapatılması gereken ayrı bir kalemdir.

### 3.4 Rol sözlüğü 5 çatallı

| Kaynak | Değer |
|---|---|
| `models/enums_db.py:18` (kanonik, *"Do NOT redefine"*) | `STUDENT = "STUDENT"` |
| 3 kopya enum | `STUDENT = "student"` |
| `models/enums.py:104` | `OGRENCI = "ogrenci"` |

---

## 4. Sonuç ve öneri (uygulanmadı — kapsam kararı)

**X06 `dogrulandi` kalır.** Tutarsızlık arandı ve **bulundu**; 21/23 sayısı değil,
§3'teki üç zıt yargı kusurdur.

Birleştirme yapılırken **sırayla**:

1. **Önce kanon rol yazımını ÖLÇ** — tek `psql` sorgusu:
   `SELECT role, count(*) FROM users GROUP BY 1`. Beş aday yazımdan hangisinin
   canlı olduğu ölçülmeden enum birleştirilemez; yanlış kanon **tüm kullanıcıları
   kapı dışında bırakır**.
2. **`enhanced_authentication.py:381` TypeError→500 kusurunu ayrı ve önce kapat.**
3. Sonra 7 canlı kapıyı tek kanonik kapıya göçür.
4. **16 ölü tanımın silinmesi AYRI KALEM** — Cerrahi Müdahale kuralı: X06 bir
   tutarsızlık kalemidir, ölü kod temizliğini kapsamaz.

---

## 5. Ölçüm aleti arızaları (bulgu diye raporlanmadan yakalandı)

| # | Arıza | Nasıl kapatıldı |
|---|---|---|
| A2 | `rg` PATH'te **yok** → `exit 127`. Ham koşulsa **"çağıran yok" yanlış-pozitifi** üretirdi | Dahili Grep aracı + Git Bash `grep`; ikinci aletle teyit |
| A3 | `grep -rn … backend/` **120 sn timeout** (NTFS + 15 GB). Kısmi çıktı "çağıran yok" sanılabilirdi | Dizin daraltma + kendi `os.walk` tarayıcısı; **kapsam ilan edildi** (1.886 dosya) |
| A6 | "Çağıran var" **yanlış-pozitifi** — 3 sahte çağıran (2 yorum, 1 dize sabiti) | Elle ayıklandı, tabloda ELENEN olarak işaretlendi |

**Ölçülemeyenler (dürüstlük kaydı):** 6 canlı çağıranın HTTP'de gerçekten
erişilebilir olduğu **ölçülmedi** (`/openapi.json` sorgulanmadı) — "6 çağıran"
**kod** düzeyinde doğrudur, uç erişilebilirliği ayrı bir ölçümdür.
`learning_path_auth.py:259` ve `unified/auth_system.py:581` **çalıştırılmadı**.
