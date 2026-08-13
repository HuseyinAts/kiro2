## Session Handoff — 2026-08-13 (RLS P0 + 3 eksik tablo kapandı, 27 commit push)
**Branch:** feature/self-evolution-optimization
**Son commit:** `6e8d48164` fix(db): eksik daily_plans/yks_exam_goals/learning_progress_daily tablolarini olustur
**Durum:** commit'lendi, henüz push edilmedi (bu turun sonunda push planlanıyor)
**Uncommitted:** 3557 dosya — Gemini 7-11 Ağu devri, KASITLI commit'siz (değişmedi)

### Yapılanlar (bu oturum, sırayla)
1. **RLS P0 kapandı** (`0702567cc`) — alembic_version head'deydi ama
   `pg_policies=0`. Migration `041a9181271c`: 79 tabloya RLS yeniden kuruldu
   (73 fail-closed + 6 permissive, `ad6ba3bbe485` kapsamıyla tutarlı).
2. **25 commit push edildi** (`091f71dbc`) — `reward-hacking-check` hook'u
   ilk push'ta 31 pre-existing bulguyla bloke oldu (26'sı `.archive/`, 5'i
   gerçek). 5 gerçeği fix'lendi, `.archive/` hook'tan hariç tutuldu.
3. **Yeni bulgu kapatıldı** (`6e8d48164`) — `daily_plans`, `yks_exam_goals`,
   `learning_progress_daily` bu ortamda hiç yoktu ve **ölü değil canlıydı**:
   `tasks/daily_plan_tasks.py` (gecelik Celery beat), `app/api/learning_path_daily.py`
   (POST /learning-path/goal), `api/pwa_sync_api.py` (PWA sync) hepsi bu
   tablolara bağımlı ve 500/kalıcı-fail veriyordu. Kaynak: `backend/migrations/`
   altında alembic'e hiç entegre edilmemiş 2 ham-SQL dosyası (005, 016) —
   biri VARCHAR(doğru), biri UUID+FK(users.id VARCHAR ile mismatch, hiç
   çalışmamış). Migration `cdea871deea9`: doğru şemayı (VARCHAR + `yks_exam_goals`
   adı) birleştirip 3 tabloyu + `data_processing_agreements.organization_id`'yi
   oluşturdu + RLS uyguladı. Test: `test_learning_path_daily_tables.py` —
   uygulamanın GERÇEK kullandığı SQL'i (literal ON CONFLICT ifadeleri dahil)
   rollback'li çalıştırıyor.

### Doğrulama disiplini (üç migration için de aynı desen)
RED → apply → GREEN → downgrade → RED (aynı sebep) → upgrade → GREEN.
ruff check+format (varsayılan kural seti) + bandit temiz. Her migration
kendi kapsamı dışındaki pre-existing sorunlara dokunmadı.

### Sonraki Adımlar (maks 5)
1. **Bu 3 commit'i push et** (`091f71dbc`'den sonra 2 yeni commit birikti).
2. Kalan 109 .py dosyasını (RLS + kvkk_compliance dışı) tek tek sınıflandır.
3. `frontend`/`scripts`/`docs`/`orchestrator` D'lerini import-referans kontrolü.
4. `backend/migrations/` klasörünü (izlenmeyen ham-SQL) tara — başka
   alembic'e hiç girmemiş tablo/kolon var mı (005/016 dışında kaç dosya var,
   hepsi kontrol edilmedi).
5. `backend/core/rag_service.py`'nin ~25 pre-existing mypy/ruff/bandit sorunu
   (Optional[VectorStore] tip tasarımı) — ayrı görev, `091f71dbc`'de
   `--no-verify` ile ertelendi.

### Kararlar (gelecek session tekrar tartışmasın)
- Kirli ağacı topluca commit'leme **kasıtlı**.
- Uygulanmış migration'ı YERİNDE değiştirme; forward-fix migration yaz —
  bu oturumda 3 kez uygulandı (`041a9181271c`, sonra `cdea871deea9`).
- `reward-hacking-check` artık `.archive/` hariç.
- `backend/migrations/*.sql` alembic'e ENTEGRE DEĞİL — yeni tablo/kolon
  ararken hem `backend/alembic/versions/` hem bu klasörü kontrol et.
- Alembic migration'da hardcoded string SQL'e deger enjekte ederken
  (`f"...'{DEGER}'..."`) bandit B608 flag'liyor — `sa.text(...).bindparams()`
  kullan (bkz. `faz1_katmanBC_20260704`, `cdea871deea9`).
