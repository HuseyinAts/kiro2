## Session Handoff — 2026-08-13 (RLS P0: fantom sıfırdan gerçek RLS restore)
**Branch:** feature/self-evolution-optimization
**Son commit:** `0702567cc` fix(rls): forward-fix migration — DB'de tamamen eksik olan RLS'i geri yükle
**Önceki commit:** `68f0783a1` fix(rls): ALTER POLICY yazma yolunu da fail-closed yap (WITH CHECK)
**Uncommitted:** 3557 dosya — Gemini 7-11 Ağu devri, KASITLI commit'siz (değişmedi)

### Yapılanlar (bu oturum)
- **Kök neden ölçüldü (latest.md'nin bıraktığı P0):** Bu makinede `alembic_version`
  zaten head'de (`51b325d6ff41`) ama `pg_policies=0`, `relrowsecurity=0/241`.
  Transactional DDL kanıtı: RLS migrasyonları hata verseydi zincir orada durur,
  sonraki onlarca migration (mv_safe_for_beta matview dahil) hiç çalışmazdı —
  ama hepsi mevcut. Yani RLS büyük ihtimalle çalıştı, SONRA alembic dışında
  söküldü; `alembic_version` head'de kaldı. `alembic upgrade head` bu yüzden
  **no-op** olurdu (zaten head'de) — "mutating, önce karar" endişesi bu komut
  için geçersizdi, asıl mutasyon yeni bir forward-fix migration gerektiriyordu.
- **Migration `041a9181271c` yazıldı + uygulandı:** 79 tabloya RLS+policy
  yeniden kuruldu. `ad6ba3bbe485`'in (68f0783a1) fail-closed kapsamıyla
  (73 tablo) birebir aynı ayrım korundu: 73 fail-closed, 6 permissive-when-unset
  (billing 4 + organizations + parent_link_codes). Çalışma-zamanında introspect
  eder; bu ortamda eksik 3 tablo (`daily_plans`, `learning_progress_daily`,
  `yks_exam_goals`) + 1 kolon (`data_processing_agreements.organization_id`)
  için RLS'i atlar ve açıkça UYARI yazdırır (ayrı, önce-var-olan bir eksiklik —
  bu migration'ın kapsamı DEĞİL, ayrı bir görev olarak backlog'a düşebilir).
- **`test_rls_tenant_isolation_guard.py` güncellendi:** 3 önceden-kırmızı test
  artık geçiyor. `ORNEK_TABLO` (refresh_tokens) permissive'den fail-closed'a
  geçtiği için 2 test yeniden yazıldı (davranış kaydı + trap-detector koşulu).
  Taban/permissive sayıları artık bu ortamın GERÇEK (drift düşülmüş) durumuna
  göre hesaplanıyor, sabit 79/6 değil.
- **Doğrulama:** RED (4/8 fail) → migration apply → GREEN (8/8) → downgrade →
  RED (4/8, aynı sebep) → upgrade → GREEN (8/8). ruff check+format temiz.
  `test_rls_fail_closed_with_check.py` (önceki P0 fix) regresyonsuz.

### Yeni bulgu (ayrı görev, bu oturumda KAPATILMADI)
- **3 tablo bu DB'de hiç yok:** `daily_plans`, `learning_progress_daily`,
  `yks_exam_goals` — muhtemelen `c555a10f4b93`'ün düşürdüğü ve GF-K1/K2/
  mv_safe_for_beta/parent_link_codes restore dalgalarının kapsamadığı kalıntı.
- **1 tablo scope kolonu eksik:** `data_processing_agreements.organization_id`.
- Bu iki drift `041a9181271c`'nin migration çıktısındaki UYARI satırlarından
  görülür; başka bir ortamda restore/upgrade edilirse aynı komutla tekrar
  ölçülmeli — sabit sayı olarak (3, 1) güvenilmesin.

### Sonraki Adımlar (maks 5)
1. Yeni bulgu: 3 eksik tablo + 1 eksik kolonun kaynağını araştır (hangi
   migration/restore dalgası atlamış) — istenirse ayrı bir forward-fix.
2. Kalan 109 .py dosyasını (RLS + kvkk_compliance dışı) tek tek sınıflandır.
3. `frontend`/`scripts`/`docs`/`orchestrator` D'lerini import-referans kontrolü.
4. 22 commit'i push et (0 behind).

### Kararlar (gelecek session tekrar tartışmasın)
- Kirli ağacı topluca commit'leme **kasıtlı** ("M=kozmetik" 4 kez yanlış çıktı).
- Uygulanmış migration'ı YERİNDE değiştirme; forward-fix migration yaz —
  `041a9181271c` bu deseni ikinci kez uyguladı (`ad6ba3bbe485`'ten sonra).
- RLS predicate seçimi kullanıcıya soruldu (permissive vs fail-closed
  replay) — fail-closed + bekçi testi güncellemesi onaylandı.
- 3 eksik tablo/1 eksik kolon SESSİZCE atlanmadı: migration çalışma-zamanında
  introspect edip UYARI yazdırıyor, bekçi testi de aynı sayıyı düşüyor —
  ikisi drift edip birbirinden kopmasın diye tek kaynaktan (canlı ölçüm).
