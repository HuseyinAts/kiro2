## Session Handoff — 2026-07-29 (akşam)
**Branch:** feature/self-evolution-optimization
**Son commit:** `d7f80175b` fix(teacher): 7 yazma ucu kapısızdı
**Uncommitted:** temiz · **PUSH EDİLMEDİ** — 3 commit bekliyor (`cfe3e54c4`, `25784449d`, `d7f80175b`)

### Yapilanlar (3 commit, hepsi TDD + mutasyon)

**`cfe3e54c4` celery rotasız görevler** — Redis `celery` kuyruğunda 3.369 tüketilmemiş mesaj.
`task_default_queue` set edilmemişti (celery varsayılanı "celery"), worker onu dinlemiyordu.
Hiç koşmayanlar: expire_duel_voting 3047/0 · refresh_daily_plans 92/0 · send_streak_reminders
37/0 · irt_calibration 14/0. Fix: `task_default_queue="default"` + Queue("default"). RED 7 →
GREEN 16/16. **Canlıda kanıtlandı**: rotasız sahte görev gönderildi, worker "Received
unregistered task" logladı. Kuyruk yedeklendi (`C:/Users/husey/celery_queue_backup_20260729.jsonl`)
ve silindi. NOT: görev #416 "retention push canlıya alındı" completed'dı ama hiç koşmamıştı.

**`25784449d` kayıt rol eşleştirmesi** — `str(kullanici_data.rol).lower()`; Python 3.11+ `str,Enum`
için `str()` "KullaniciRolu.OGRETMEN" üretiyor. ROL_MAP hiçbir anahtarı tutturmuyordu →
**öğretmen ve veli kaydolamıyordu**, herkes sessizce STUDENT oluyordu. Denetimin "herkes admin
olabilir" P0'ı FANTOMDU (admin da STUDENT'e düşüyordu). TUZAK: bariz fix (`rol.value`)
öğretmen/veli'yi onarıp admin yükseltmesini AÇACAKTI — ikisi tek testte çivilendi.
`_map_registration_role` çıkarıldı; ADMIN/SUPER_ADMIN 403. RED 6 → GREEN 11/11, mutasyon 3/3.

**`d7f80175b` öğretmen rol kapıları + kayıt formu** — 15 uçtan 2'sinde kapı vardı (29 Tem'de
eklenen roster uçları). 7 yazma ucu kapısızdı: POST /classes, POST+DELETE /exams,
/assignments, /contents. Öğrenci token'ı 422 alıyordu = kapıya takılmıyordu. RED 7 fail/14 pass
→ GREEN 21/21 + kapsam bekçisi (router dekoratör sayısı testle eşleşmezse kırmızı).
Ayrıca kayıt formundan Admin kartı kaldırıldı (25784449d ile ölü seçeneğe dönmüştü).

**Stack yeniden derlendi** (29 Tem 13:30 UTC) — o güne kadar imajlar 26-28 Tem'de takılıydı ve
blocker #1/#6 "kapandı" denmesine rağmen canlıda YOKTU. Bu oturumun en büyük bulgusu.
**UYARI: son 3 commit henüz imajda YOK, tekrar build gerekiyor.**

### Fail Eden Testler
YOK. test_teacher_roster 21/21 · test_celery_routing_contract 16/16 ·
test_auth_registration_role 11/11 · auth paketi 34/34 · celery yan etki 821/821.

### 12-oturum gözden geçirmesi (21-29 Tem, 141 commit) — SONUÇ
95 iddia ölçüldü: **27 sağlam · 9 "sağlam" denip çürüdü · 39 eksik · 6 fantom · 12 yeni risk**.
Sağlamlık %28. Baskın desen: **"backend düzeldi ama kullanıcıya ulaşmıyor" (13 kez)**.
Rapor: bu oturumda üretildi, docs/audits'e YAZILMADI (kullanıcı kararı bekliyor).

### KARAR BEKLEYEN (kullanıcı)
1. **`getMe()` — Persona'nın backend karşılığı HİÇ YOK.** `api-client.ts:182` `live('/me')`
   çağırıyor, `/api/v1/me` 404. Sentez "tek satır, `/auth/me` yap" dedi ama `/auth/me`
   `{user:{id,email,ad,soyad,rol}}` dönüyor; `Persona` ise ad/adKisa/bas/sinif/seri/seriRekor/
   xp/seviye/hedefBolum/hedefUni/hedefSiralama/guncelSiralama/yksTarihi/gunlukHedefDk istiyor.
   Alanların çoğu hiçbir uçta yok. **31 dosya getMe kullanıyor**, `DuelloPage.tsx:155`
   `Promise.all` içinde → düello ekranı şu an hata veriyor. Seçenekler: (a) gerçek
   `/api/v1/me` agregasyon ucu yaz, (b) birkaç uçtan istemcide birleştir, (c) kimlik
   `/auth/me`'den + kalan alanlar mock (hibrit). **Bu bir fix değil, tasarım kararı.**
2. Push edilsin mi (3 commit)?
3. Gözden geçirme raporu docs/audits altına yazılsın mı?

### Sonraki Adimlar (maks 5)
1. **Rebuild** — son 3 commit canlıda yok: `docker compose build backend frontend celery-worker celery-beat && docker compose up -d`
2. **`user_item_fsrs`** — tablo YOK (ölçüldü), `/fsrs-review` mount'lu rota 500.
   `c555a10f4b93_sync_db_changes.py` upgrade()'inde DROP edilmiş; dosya hâlâ 145 DROP TABLE
   taşıyor, taze DB'de her koşumda tekrar oynuyor. **1-2 gün**
3. **ES bypass (#433)** — mv kapısı 25.127, aktif havuz 110.858, ES indeksi 64.270 doküman.
   ES kapıyı hiç tanımıyor. **1 gün**
4. **route_contract_check.py** — mount'lu ekranların `live()` yollarını canlı openapi ile
   karşılaştıran pre-push kapısı. 13 kez tekrarlayan deseni kapatır. Uyarı: `if kontrol==0: exit 1`
   koy (push_secret_guard bu hatayı yapmıştı).
5. **Operatör**: SMTP env (3 compose dosyasında da yok) · 73 STUDENT hesap triyajı (#445) ·
   anahtar penceresi faturalama kontrolü (#436)

### Kararlar
- `send_email` SMTP yokken zaten `False` dönüyor — ajanın "koşulsuz True" iddiası YANLIŞ.
  Gerçek dar sorun: SMTP yapılandırılmış ama kimlik hatalıysa thread hatayı yutup `True` dönüyor.
- `str(enum)` tuzağı **sistemik değil**: depoda `getattr(x,"value",x)` deyimi 6 dosyada +
  4 `isinstance` şubesi var; kayıt ucu onu kullanmayan tek yerdi. Tekrarlarsa doğru hamle
  enum'ları `StrEnum`'a çevirmek (geniş değişiklik, şimdi yapılmadı).
- Rol reddi **sessiz düşürme değil 403**: bu bug'ı aylarca gizleyen şey sessiz düşürmeydi.
