# DEMO RUNBOOK — 2 Ağustos 2026, 20:00 Yatırımcı Sunumu

**Hazırlık oturumu:** S203 · **Kod dondurma:** 17:35 (erken donduruldu — hedef karşılandı)
**Geri dönüş noktası:** `git tag demo-baslangic-20260802`

---

## 0. Sunumdan 15 dk önce — 4 komut

```bash
cd C:\Users\husey\kiro2

# 1) Stack ayakta mı
docker ps --format "{{.Names}}\t{{.Status}}"
#    beklenen: kiro2-backend / kiro2-frontend / kiro2-redis  hepsi (healthy)

# 2) Sağlık
curl -s -o /dev/null -w "backend %{http_code}\n" http://localhost:8000/health
curl -s -o /dev/null -w "frontend %{http_code}\n" http://localhost:3000/
#    ikisi de 200 olmalı

# 3) DEMO YOLU PROVASI — tek komut, 23 uç
python backend/scripts/demo_yolu_probu.py --kisa
#    beklenen son satır: "SONUC: 5xx YOK."
#    5xx varsa AŞAĞIDAKİ §4 KURTARMA'ya git

# 4) Tarayıcıyı GİZLİ pencerede aç (eski cookie/cache taşımasın)
#    http://localhost:3000
```

> **`demo_yolu_probu.py` 5xx bulursa demoya girme.** Betik çıkış kodu 1 verir.

---

## 1. Demo senaryosu — tıklama tıklama

Tohum hesaplar (`backend/scripts/seed_mvp_data.py`), şifre hepsinde
`Kiro2Beta2026@x`:

| Rol | E-posta |
|---|---|
| Öğrenci | `test@kiro2.com` |
| Öğretmen | `ogretmen@kiro2.com` |
| Veli | `veli@kiro2.com` |
| Admin | `admin@kiro2.com` |

### Akış (yaklaşık 8-10 dk)

| # | Adım | Ne söylenir | Kanıt (2 Ağu son prova) |
|---|---|---|---|
| 1 | Ana sayfa | Ürün konumlandırma | HTTP 200, 2 ms |
| 2 | Öğrenci girişi | Çift kimlik (cookie + Bearer) | `/auth/me` 200, 1 ms |
| 3 | Öğrenci paneli | Kişisel ilerleme, rozet, lig | `/student-dashboard/profil` 200 · `/istatistikler` 200 · `/gamification/profile` 200 |
| 4 | Öğrenme yolu | Kişiselleştirilmiş plan | `/learning-path/completion/{STU_}` 200 |
| 5 | Soru çözme | Beta havuzundan pratik | `POST /osym-exam/beta-practice` 200 |
| 6 | **Tekrar (FSRS)** | Aralıklı tekrar algoritması | `/fsrs/due` 200 · `/due-count` 200 · `/stats` 200 |
| 7 | Öğretmen paneli | Sınıf, öğrenci, sınav, rapor | 6 uç 200 |
| 8 | Sınav | Konfigürasyon + geçmiş | `/osym-exam/exam-configs` 200 · `/my-exams` 200 |
| 9 | Veli görünümü *(opsiyonel)* | Çocuk takibi | `/parent/children` 200 · `/parent/notifications` 200 |

**Ölçülen süreler:** tüm demo uçları **≤ 11 ms** (önbellekli 2. çağrı).

---

## 2. GÖSTERME — bilerek demo dışı

| Ekran / uç | Neden |
|---|---|
| `/parent/dashboard` | **656 satır sabit veri** (mock). §1'deki `/parent/children` gerçek — onu göster. |
| `/content-management/questions` | Tamamen mock |
| `/api/v1/fsrs/flashcards*` | 2 Ağu'da kaldırıldı → **410 Gone** (kanonik karşılık: `/fsrs/due`) |
| `/fsrs/recommendations`, `/fsrs/statistics` | **500** — deprecated senkron servis. Frontend tüketicisi **yok** (ölçüldü), demo yolunda değil (`FSRS-K1`) |

> ✅ **Bu ikisi 17:20'de DÜZELDİ, artık gösterilebilir:**
> `/fsrs/study-sessions/start` + `/end` (öğrenme yolu akışı) ve
> öğrenme stili "davranışsal veri" yazma (`gf82`).

> Bu kalemler `docs/audits/2026-08-01_eksiklik_master.md` içinde ankrajlı.
> "Mock" olan hiçbir şeyi **gerçek veri diye sunma** — soru gelirse
> "o yüzey henüz bağlanmadı, backend hazır" demek doğru cevap.

---

## 3. Bugün kapatılanlar (sorulursa)

| Kusur | Etki | Kanıt |
|---|---|---|
| Bilinmeyen sınav oturumu → 500 | **28 çağrı yeri** 404 yerine 500 veriyordu | `295f34d9d` |
| Koçluk sinyali → 500 | Üç seri bağlı sebep (DB DEFAULT yok · tz kayması · VARCHAR kimlik `int` tiplenmiş) | `9ea03d8c9` |
| **`/fsrs/due` → 500** | Frontend tekrar sayfası; `varchar = uuid` yüzünden **hiç çalışmamış** | `ee6d7c820` |
| Öğrenme stili tarayıcıda 401 | 7 uç yalnız Bearer kabul ediyordu, frontend cookie kullanıyor | `9035ad854` |
| **Önbellek modeli dizeye çeviriyordu** | "İlk açılışta çalışır, backend yeniden başlayınca patlar" | `9035ad854` |
| Çalışma oturumu başlat/bitir → 500 | Frontend'in öğrenme yolu akışı; servis **var olmayan 4 alana** yazıyordu | `eba3981fe` |
| Profil yaşı hesabı → 500 | Aynı sınıfın bir yarısı naive, diğeri tz-aware | `40f68ca8a` |

**Golden Flow: oturum başı 164 geçti / 12 düştü → şimdi 176 geçti / 0 düştü / 2 atlandı.**
Deponun kendi kapısı: `toplam=178 gecen=176 atlanan=2 hata=0` — GEÇİYOR.

---

## 4. KURTARMA — demo sırasında bir şey patlarsa

### A) Bir ekran 500 veriyor
```bash
docker restart kiro2-backend && timeout 30 bash -c 'until curl -sf localhost:8000/health >/dev/null; do sleep 2; done'
```
Sonra **sayfayı yenile**. (Restart havuzu ve bayat önbelleği düşürür.)

### B) Restart sonrası da 500
```bash
docker exec kiro2-redis redis-cli FLUSHDB     # önbelleği tamamen boşalt
docker restart kiro2-backend && sleep 25
python backend/scripts/demo_yolu_probu.py --kisa
```

### C) Her şey bozuldu — koda geri dön
```bash
git checkout demo-baslangic-20260802
docker compose down && docker compose up -d && sleep 40
```
> Bu, bugünün 5 düzeltmesini de geri alır — **son çare**. Geri döndüğün an
> `/fsrs/due` ve profil ekranı yeniden 500 verir; §2 listesi genişler.

### D) Konuşarak devam et
Ekran patlarsa **tıklamayı bırak**, `docs/audits/2026-08-01_eksiklik_master.md`
üzerinden mühendislik disiplinini anlat: 95 ölçülmüş kalem, her biri
`dosya:satır` ankrajlı, kapanış iddiaları bağımsız doğrulanıyor. Bu, çoğu
erken aşama ekipte olmayan bir olgunluk göstergesidir.

---

## 5. Bilinen risk — dürüst değerlendirme

- **Kimlik biçimi tuzağı:** öğrenme-yolu uçları `STU_xxx` bekler, `users.id`
  DEĞİL. Yanlışını gönderirsen 403 alırsın (IDOR kapısı doğru çalışıyor,
  kusur değil). Demo linkleri doğru kimliği taşıyor.
- **Tek kullanıcı ölçüldü.** Eşzamanlı çok kullanıcı yük testi bugün
  yapılmadı. Yatırımcı "kaç kullanıcı kaldırır" derse: ölçmedik, dürüst cevap
  bu; altyapı (PgBouncer) henüz kurulmadı.
- **CI aktif dalda tetiklenmiyor** (`#468`). Testler yerelde koşuyor.

---

*Üretim: S203, 2 Ağu 2026. Prova komutu: `python backend/scripts/demo_yolu_probu.py`*
