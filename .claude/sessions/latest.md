## Session Handoff — 2026-08-07 (S205: FAZ 0 içerik kurtarma — TAMAMLANDI)

**Dal:** feature/self-evolution-optimization · **Son commit:** `b84bdc503`
**Önceki:** S204 uçtan uca denetim (`docs/audits/2026-08-06_uctan_uca_durum_tespiti.md`)

### ✅ FAZ 0 kapandı (5 commit)
| Commit | İş |
|---|---|
| `1091db7ab` | Tohum script'i mühürlendi + hacim/çeşitlilik invaryant testi |
| `6f3380072` | Celery DSN çözümlemesi + parola maskeleme |
| `eb40cb30d` | Streak bildirimi `organization_id` taşımıyordu |
| `d5bf6c339` | Takipsiz `fa067642bdfe` migration'ı sürüm kontrolüne alındı |
| `b84bdc503` | 22 scratch script `.gitignore`'a (glob değil açık liste) |

### İçerik kurtarma — canlı ölçüm
`question_bank` **2.304 satır / 21 benzersiz → 187.835 / 182.519** (oran 0,97), aktif 110.858.
Öğrenci kapısı `mv_safe_for_beta` **2.200 → 25.127**. Fizik/Biyoloji/Kimya 1'er → **11.071 /
5.251 / 13.096**. Sentetik satırlar `qb_synthetic_backup_20260806`'da. HNSW tek-thread
yeniden kuruldu (`indisvalid=t`, 695 MB); kopya ikinci HNSW geri getirilmedi (22→21 index).
İnvaryant testi **RED→GREEN** kanıtlı (2.304<150.000 ve 0,009<0,90 düşüyordu).

### Celery zinciri — üç seri bağlı kusur
1. `psycopg2.connect`'e SQLAlchemy DSN'i (`+asyncpg`) ham veriliyordu → görev **4 gündür ölü**
2. Hata metni DSN'i gömüyordu → `kiro2_app` parolası worker log'una **14 kez** düştü
   (log + Celery sonuç backend'i = iki sızıntı yüzeyi)
3. (1) düzelince ortaya çıktı: INSERT `organization_id` taşımıyordu (NOT NULL)

Canlı doğrulama: `{'sent': 4, 'status': 'sent'}` — DB'de 4 satır, 4'ünde org dolu.
Konteynerler yeniden oluşturulup sızmış log'lar imha edildi (14 → **0**).
Testler 9/9; iki kritik test **mutasyonla çivili** (`1 failed`, `error` değil).

### ⚠️ Açık kalemler
- **Rebuild YAPILMADI**: fix konteynere `docker cp` ile konuldu, imajda yok. Çalışma ağacında
  ~300 commit'siz dosya olduğu için imaja gömmek istenmedi. Sonraki gerçek deploy'da rebuild şart.
- `questions` legacy tablosu **silik kalacak** (karar verildi). Yedekte mevcut; migration'ın
  `downgrade()`'i `pass` — geri alınabilirmiş gibi görünüyor ama değil.
- `tests/db/test_indexes.py` **vakum test** — sabitleri kendine assert ediyor, DB'ye bakmıyor.
- `push_tasks.py:107` `date.today()` naive/aware karışımı (gf82 sınıfı), `noqa` ile işaretlendi.

### Sonraki adımlar
1. FAZ 1: CI'yı aktif dalda tetikle (#468) · `quality-gate.yml` no-op GF adımı · xdist çöküşü
2. FAZ 2: 4 KVKK router'ını aç + SMTP kimlik bilgisi (#441)
3. FAZ 3: PSP (iyzico/PayTR 3DS) + TLS
4. FAZ 4: 167 kırık yol için ürün kararı
5. Beklemede: 6 Cursor planı (vite code-split, pytest-xdist, socratic_guard,
   teacher_copilot, PWA sync, alembic round-trip) — 18:00–19:00 işi, commit'siz duruyor

### Çalışma şekli değişikliği
Kullanıcı: "bana iş verme, tümünü sen yapacaksın her zaman" → `psql`/`docker`/`pytest` dahil
tüm komutları Claude çalıştırır. CLAUDE.md'nin "İnsan Döngüsünde" bölümü **geçersiz**.
