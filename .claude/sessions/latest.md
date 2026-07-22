## Session Handoff — 2026-07-23 (SPRINT9-A · GRUP 7 kısmi 4/6)
**Branch:** feature/self-evolution-optimization (origin'in önünde — push YOK)
**Son commit:** (SPRINT9-A commit — bkz. git log; öncesi 05e6cf04a = SPRINT8 E2E docs)

### Yapılanlar (Faz 3 tasarım-portu — Grup 7 Roller A → frontend/src/kiro/)
- **Grup 7 kısmi (4/6).** Veli Paneli · Öğretmen Paneli · Öğrenci Özeti · Sınıf Kurulumu (hepsi **paper**). İlerleme **29/42 ekran + 1 composite (QuestionCard) + `ui/WeeklyActivityBars`**.
- **Ayrı tur (kullanıcı "ağırları ayır"):** Veli Bağlama (KVKK) + Ödev Atama.
- Rol/gizlilik: Veli **SİZ-dili** + çocuk **salt-okur** (sohbet/AI/mood gizli); Öğretmen SİZ + roster salt-okur; Öğrenci Özeti salt-okur (tek yazma=ödev-ata link); Sınıf Kurulumu **DC SEN korundu** (DC>spec).
- **Kullanıcı kararı:** Veli Bağlama → **DC 6-haneli kod-akışı + mock** (Faz 4 gerçek /parent email-onay).
- Backend: `/teacher`+`/parent` MEVCUT (Faz 4 wiring); katılım-kodu/rotate/join + öğrenci Ödevlerim + zengin-atama = **mock**.
- Süreç: keşif (7) → build (infra + WeeklyActivityBars + 4 ekran + gate) → adversarial (11) → fix → breakpoint gate.
- Rapor: `docs/audits/2026-07-23_sprint9a-roller.md`; durum: `design/PORT_DURUM.md`.

### Fail Eden Testler
- YOK. vitest **52 dosya / 294 test PASS** · kanon 0 · tsc 0 · axe temiz · **breakpoint 0 FAIL / 280**.

### Adversarial + breakpoint (bu session)
- Adversarial (11 ajan): P0 **0** · major **2** · minor **2** · phantom **0** → hepsi fix (VeliPaneli yeşil-token AA+rozet; OgrenciOzeti h1→h2→h3; OgretmenPaneli negatif-delta amber).
- Breakpoint: SinifKurulumu kök-div `content-box` 12px taşma → **deterministik Playwright teşhisi** → `box-sizing` fix → 0/280. (Build+adversarial kaçırdı — mekanik kapı yakaladı; SPRINT8 dersi tekrar.)

### Engelleyiciler / Operatör (sende)
- **Push YAPILMADI** (kullanıcı "push yok").
- Backend healthy (PG18 Automatic fix'i önceki turda kalıcı çözdü — RestartCount 0).
- Kalan (opsiyonel): SegmentedControl BackstopJS pixel-ref regen; rota wiring (App router).

### Sonraki Adımlar (maks 5)
1. **Grup 7 kalanı (ayrı tur):** Veli Bağlama (KVKK kod-akışı, en hassas) + Ödev Atama (Ödevlerim döngüsü). Aynı pipeline.
2. Sonra Grup 8 (İş: Abonelik/Ödeme/Plan/Ayarlar/Bildirim/Alan Kütüphanesi/Çevrimdışı) + Grup 9 (AI).
3. Faz 4 backend wiring: /teacher+/parent gerçek; katılım-kodu/Ödevlerim/zengin-atama backend YOK.
4. Premium (Veli Paneli) → Grup 8 Abonelik ekranı (CTA link ertelendi).
5. KVKK (Veli): çocuk günlük-durum/XP görünürlüğü karşılıklı-onay + opt-in.

### Kararlar (gelecek session tekrar tartışmasın)
- 4 rol-paneli **paper**; Veli/Öğretmen **SİZ-dili**; çocuk/öğrenci verisi **salt-okur** (sohbet/AI/mood gizli).
- Sınıf Kurulumu **DC SEN** (DC>spec tiebreaker); Veli Bağlama = **DC kod-akışı + mock**.
- **Overflow teşhisi deterministik:** breakpoint fail'de tahmin YOK → Playwright parent-zincir ile taşan öğeyi bul. Kök div de box-sizing:border-box olmalı (SPRINT8 pitfall).
- `ui/WeeklyActivityBars` paylaşımlı (3 ekran); transform:scaleY (layout-anim değil) + RM-guard + per-bar SR metni.
