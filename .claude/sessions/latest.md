## Session Handoff — 2026-07-29 01:30
**Branch:** feature/self-evolution-optimization
**Son commit:** `9a8860de7` test(teacher): rol kapısı parametrize — parent da reddedilmeli
**Uncommitted:** temiz · **Push: tamam, 0 bekleyen commit** (7 commit push edildi)

### Yapilanlar

**Blocker #1 — şifre kurtarma KAPANDI (kod tarafı)** `9275f84b0`, `65721e890`, `b3609bdf1`
- `backend/core/password_reset_codes.py` (YENİ): 6 haneli kod, (e-posta,kod) çiftine bağlı +
  hash'li, atomik INCR deneme sayacı (5), **hesap başına saatte 3 kod** (IP limiti yetmiyordu:
  100 IP → %72 kaba kuvvet başarısı).
- `backend/api/auth.py:1463` TODO → gerçek gönderim + yeni `POST /auth/verify-reset-code`.
  Gönderim **await EDİLMİYOR** — SMTP beklemek yanıt süresinden e-posta numaralandırması açardı.
- `frontend/src/kiro/screens/HesapKurtarmaPage.tsx` + `kiro/api/api-client.ts:540` canlıya bağlandı;
  `App.tsx:229` rota + `/forgot-password` yönlendirmesi (ikisi de ölü linkti).
- Planda olmayan 4 bulgu: `auth.py` `_get_token_store()` her çağrıda YENİ store üretiyordu →
  **Redis'siz her kurulumda sıfırlama ZATEN ölüydü**; ekran şifre kuralları sunucudan farklıydı
  (3 vs 5) ve **test bu yanlış sözleşmeyi sabitlemişti**; `/giris` ölü rota; "Panele dön" yalandı.

**Blocker #6 — roster KAPANDI (satır-silme UI hariç)** `c5e0ca323`, `9a8860de7`
- `backend/app/api/teacher_classroom.py`: `POST/DELETE /classes/{id}/students` (YENİ),
  `GET /students` artık gerçek ad/soyad/e-posta döndürüyor (satır 203'te sabit boş string'di).
- **Bu router'da HİÇ rol kapısı yoktu** (ölçüldü) → yeni uçlara `_require_staff` + sahiplik
  kontrolü **handler'da açık `if`** (WHERE'e gömülü kontrol testle doğrulanamaz).
- `frontend/src/pages/ModernTeacherStudentsPage.tsx`: 5 **uydurma öğrenci** fallback'i SİLİNDİ
  (satır 64: "Ahmet Yılmaz"…), dürüst hata bandı + sınıf seç/e-posta yaz/ekle formu.

### Fail Eden Testler
YOK. `tests/unit/test_password_reset_codes.py` + `tests/integration/test_password_recovery_flow.py`
**54/54**; `tests/integration/test_teacher_roster.py` **11/11**.
Mutasyon: `scripts/mutation_check_password_reset.py` **6/6**, `..._teacher_roster.py` **5/5**.
(`tests/fast/test_api_coverage_batch9.py` >600 s — kendi yavaşlığı, koşturulmadı.)

### Engelleyiciler
YOK — ama #1 SMTP kimlik bilgisi olmadan kullanıcıya mail göndermez (dev'de kod log'a düşer).

### Sonraki Adimlar (maks 5)
1. **#6 kalan**: satır-bazlı "sınıftan çıkar" butonu — `GET /students` yanıtına `sinif_id` eklenmeli
   (DELETE ucu VAR, UI'da düğme yok). + gerçek PG üzerinde duman testi.
2. **#1 kalan (operatör)**: `.env`'e SMTP_SERVER/PORT/USERNAME/PASSWORD/EMAIL_FROM →
   `docker compose up -d --no-deps backend` → kaydol→şifremi unuttum→gelen kutusu→giriş. (görev #441)
3. **#5**: öğretmen/admin panoları hâlâ mock (veli panosu 26 Tem'de bağlanmıştı).
4. **#433** ES reindex — `test_es_answer_leak.py:212` xfail(strict) mühürlü, reindex olunca kırmızıya döner.
5. `.pre-commit-config.yaml`'a `types-redis` → `auth.py`'deki mypy ignore'ları kaldırılabilir.

### Kararlar (gelecek session tekrar tartismasin)
- **6 haneli kod**, magic link DEĞİL · **e-posta ile roster**, davet kodu DEĞİL (ikisi de kullanıcı kararı).
- **Numaralandırma > gönderim geri bildirimi**: kullanıcı mailin gidip gitmediğini ASLA öğrenmez.
- `core.auth_dependencies.require_role` **kullanılmadı**: ham `Request`ten yeniden doğruluyor,
  aynı uca ikinci kimlik yolu sokuyor ve kapı gerçek JWT üretmeden test edilemiyordu.
- **bandit B105 hook'ta atlandı** — ruff `S105` aynı denetimi yapıyor, kontrol deneyiyle ÖLÇÜLDÜ.
- `auth.py` ve `teacher_classroom.py` bu hook zincirinden **hiç geçemiyormuş**; tüm ihlaller ÖNCEDEN
  vardı, gerekçeli işaretlendi/düzeltildi (3 `except: pass` artık loglanıyor).
- **Test altyapısı tuzakları**: `app.core.deps.get_db` ≠ `core.dependencies.get_db` (yanlışını
  override etmek sessizce gerçek sqlite'a gider) · `col.in_([...])` bağlı değeri LİSTE'dir.
