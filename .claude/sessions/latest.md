## Session Handoff — 2026-07-30 (PC kapanması sonrası kurtarma)
**Branch:** feature/self-evolution-optimization
**Son commit:** `c690854c5` fix(ci): reward-hacking bekçisi uyarıda exit 1 döndürüp push'u yine blokluyordu
**Uncommitted:** temiz · **PUSH EDİLMEDİ** — **7 commit** bekliyor (cfe3e54c4 → c690854c5)

### Bu oturum: yarım kalan #446 tamamlandı

PC kapandığında `backend/hooks/reward_hacking/` altında 3 dosya staged ama commit'siz
duruyordu (görev #446 `in_progress`). Tespit + bitirme:

**Kusur:** a278ec1c8 severity eşiğini kurdu (tavsiye → WARNING) ama push YİNE bloke
oluyordu. `hook_manager._aggregate_results`'taki `elif warning_count > 0: WARNING(1)`
dalı — pre-commit çerçevesi sıfır olmayan HER kodu başarısızlık sayar. a278ec1c8'in
kendi mesajı "exit 1 (uyarı, geçiyor)" diyerek yanlış varsayımı belgelemiş.

**Kanıt (birim test yetmez, GERÇEK KAPI ölçüldü — `pre-commit run --hook-stage pre-push`):**
- yalnız-advisory dosya → `Passed` exit 0, uyarılar yine yazdırıldı
- `assert True` → `Failed` exit 2 (bekçi körleşmedi)
- MUTASYON (elif geri konuldu) → kapı `Failed exit code 1` + birim test kırmızı
- Birim: test_severity_from_confidence.py 11 → 14 · paket 86 passed

**Kapının zorunlu kıldığı 3 önceden-var-olan düzeltme** (A/B ile HEAD'de de var
olduğu ölçüldü; `--no-verify` bu deponun belgelenmiş anti-pattern'i):
RUF012 ×2 → `ClassVar` · mypy → `isinstance(result, Exception)` → `BaseException`
(salt tip değil: `gather(return_exceptions=True)` CancelledError döndürür, Exception
alt sınıfı değil → eski kod onu `extend()` içine sokuyordu).

### Fail Eden Testler
`test_detects_bare_except` — **DEDEKTÖR DEĞİL TEST YANLIŞ** (yeni ölçüm). Gövdesi
`except Exception: handle_error()`, yani ne bare ne boş except; 0 bulgu doğru cevap.
Test adı gövdesiyle uyuşmuyor → REQ-6.4 fiilen kapsanmıyor. **2 satırlık ayrı iş.**

### KARAR BEKLEYEN (kullanıcı)
1. **Push edilsin mi — 7 commit.** (28 Tem'den beri bekliyor)
2. **`getMe()` — Persona'nın backend karşılığı HİÇ YOK.** `api-client.ts:182` `live('/me')`
   çağırıyor, `/api/v1/me` 404. `/auth/me` yalnız `{id,email,ad,soyad,rol}` dönüyor;
   `Persona` xp/seviye/seri/hedefUni/yksTarihi… istiyor. **31 dosya getMe kullanıyor**,
   `DuelloPage.tsx:155` `Promise.all` içinde → düello ekranı hata veriyor. Seçenekler:
   (a) gerçek agregasyon ucu, (b) istemcide birleştir, (c) hibrit. **Tasarım kararı.**
   (görev #447)
3. 12-oturum gözden geçirme raporu docs/audits altına yazılsın mı?

### Sonraki Adımlar (maks 5)
1. **Rebuild** — son 4 commit canlıda YOK:
   `docker compose build backend frontend celery-worker celery-beat && docker compose up -d`
2. **`user_item_fsrs`** — tablo YOK (ölçüldü), `/fsrs-review` rotası 500.
   `c555a10f4b93_sync_db_changes.py` upgrade()'i 145 DROP TABLE taşıyor. **1-2 gün**
3. **ES bypass (#433)** — mv kapısı 25.127, aktif havuz 110.858, ES 64.270 dok. **1 gün**
4. **route_contract_check.py** — mount'lu ekranların `live()` yollarını canlı openapi ile
   karşılaştıran pre-push kapısı; "backend düzeldi ama kullanıcıya ulaşmıyor" desenini
   (13 kez) kapatır. `if kontrol==0: exit 1` koy.
5. **Operatör**: SMTP env (3 compose dosyasında da yok) · 73 STUDENT triyajı (#445) ·
   anahtar penceresi faturalama (#436) · GitHub Actions (#270)

### Kararlar / Tuzaklar
- **`git stash pop` index'e DEĞİL çalışma ağacına geri koyar.** Bu oturumda `--staged`
  ile gizlenip pop'lanan iş, sonraki `git checkout -- <dosya>` ile silindi (index HEAD'i
  taşıyordu). Kurtarma: `git fsck --unreachable` → "index on <branch>" mesajlı commit →
  `git show <sha>:<yol>`. Mutasyon testinde artık dosyayı temp'e kopyala.
- Bekçi gevşetilirken **iki yönlü + mutasyon** kanıtı zorunlu: yalnız "yeşil test"
  bu depoda üç kez yanlış çıktı.
