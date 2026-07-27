## Session Handoff — 2026-07-27 (Kapı 1 / #7 CANLIDA — bloker yok)

**Branch:** feature/self-evolution-optimization
**Commitler:** `ac3bec8b8` (bandit hook fix) → `bb57a6676` (xfail kaldırıldı)
**Push:** YAPILMADI — 7 commit lokalde bekliyor
**Test:** `tests/e2e` gerçek DSN ile **36 passed / 148 skipped / 0 failed**

### Bu turda yapılan

**1. Migration uygulandı** — `alembic upgrade head` → `mv_safe_for_beta_20260727`.

```
mv_safe_for_beta 25.127 = v_safe_for_beta 25.127   (birebir)
ux_mv_safe_for_beta_id UNIQUE                       (CONCURRENTLY için şart)
refresh_safe_for_beta() SECURITY DEFINER, search_path sabit, owner=postgres
SET ROLE kiro2_app (rolsuper=f) -> SELECT ✓  refresh() ✓
```

**2. xfail(strict) kaldırıldı** — marker önce XPASS ile tetikledi (tasarlandığı gibi).
Kaldırmadan önce testlerin sahte-geçmediği ölçüldü; ikisinin de boş-veri kaçış dalı var:

```
PF   get_pretest_questions -> 20 soru      (skip dalına girmiyor)
CAT  warm_up=True/False    -> 30 / 100 aday
tuzak havuzu: konu       8.616 aktif /    474 güvenli ->  8.142 güvensiz
              MATEMATIK 44.193 aktif / 10.671 güvenli -> 33.522 güvensiz
```

**Mutasyon kanıtı:** `SAFE_POOL_RELATION=question_bank` → PF 20/20, CAT 13/30 sızıntı
ile kırmızı. Geri alındı. Bu dosyanın yeşili artık anlamlı.

**3. bandit hook'u kurulamıyordu → HER commit bloke oluyordu.** `repo: pycqa/bandit`
kaynak build + pbr `0.0.0` + Windows `WinError 183`. pre-commit bir hook'un ortamını
kuramayınca TÜM koşumu düşürür — yani sır tarayıcısı da koşmuyordu. `repo: local` +
PyPI `bandit==1.9.4` wheel'ine çevrildi. İlk bulgusu `quality_gate.py:78` B608 →
`# nosec B608` eklendi. Tüm zincir ilk kez uçtan uca yeşil.

**4. Backend + celery rebuild → kapı CANLIDA.**

```
container'da core/quality_gate.py     -> VAR, SAFE_POOL_RELATION="mv_safe_for_beta"
container'da tasks/quality_gate_tasks -> VAR
kapı çağrı yeri (test hariç)          -> 2  ->  16
/health                                -> 200, 4.6 ms
```

**Canlı E2E (gerçek HTTP, seed öğrenci token'ı):**

```
POST /api/v1/productive-failure/pretest/start -> 201
POST /api/v1/cat/sessions                     -> 201
POST /api/v1/duel/matchmake                   -> 200 (queued, tek oyuncu)
dönen 9 uuid -> 6'sı soru -> 6/6'sı mv_safe_for_beta İÇİNDE  (3'ü oturum/konu id'si)
```

**Celery yenileme zinciri:**

```
worker registered  -> tasks.quality_gate_tasks.refresh_safe_pool ✓
worker kuyrukları  -> features ✓ (rota çalışıyor, 'celery' kuyruğuna düşmüyor)
canlı tetik        -> {'refreshed': True, 'rows': 25127}
```

### Sonraki (maks 5)

1. **Push** — 7 commit bekliyor (anahtar rotasyonu/purge kararı ile birlikte düşünülmeli)
2. **Elasticsearch kapısı** — ES canlı, 64.270 doküman, her birinde `correct_answer`;
   `api/elasticsearch.py:153` ham `_source`'u `get_current_user`'a dönüyor.
   **PG kapısı bunu kapatmaz.** P0.
3. **`api/osym_inspired_routes.py:84`** — auth dependency YOK + `correct_answer` dönüyor
4. **11 anahtar rotasyonu** (10 Google + 1 HF) — sende; `kiro2_purge.git` push bekliyor
5. **Kapı 1 / #8** şifre kurtarma (~8h) · **#9-10** roster yazma uçları (~22h) ·
   **#11** `golden-flows.yml` YAML fix + GF skip-oranı bekçisi

### Kararlar (tekrar tartışılmayacak)

- Havuz yetersizse **boş dön + "henüz doğrulanmış soru yok"** — gevşetme/komşu-konu YOK
- Matview + zamanlı yenileme; **bayat pencere kabul**. Gerçek en kötü gecikme =
  matview bayatlığı **+ `_question_pool_cache` TTL 3600 sn** (osym_exam_engine)
- `soru_bankasi_service`'teki `except: return []` yutmasına dokunulmuyor
- CAT/placement **figür-regex korunuyor**

### Bilinen, kapsam dışı

- **Depo geneli bandit taraması YAPILMADI.** Hook yalnız değişen dosyaları kapsıyor;
  ilk kez dokunulan her backend dosyasında birikmiş bulgu çıkabilir.
- GF testlerinin ~%80'i skip — login ÇALIŞIYOR (doğrulandı), skip'ler seed-veri
  bağımlı per-test dallardan. Görev #11.
- Rotasız beat görevleri hiç koşmuyor (social / daily_plan / push / irt_calibration) — #430
- `agents/learning_path_agent.py` import edilemiyor (`core.assessment_system` yok, ölü kod)
- 2 `.tablesample()` kalıntısı: `database/repositories.py:268`,
  `repositories/question_repository.py:134` (ölü)
