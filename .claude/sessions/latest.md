## Session Handoff — 2026-08-01 (S200 · 7 görev + öz-denetim + P0 regresyon)

**Branch:** feature/self-evolution-optimization
**Son commit:** `b57be1ace` · origin ile **senkron** · çalışma ağacı **temiz**

---

## ⚠️ TEK AKTİF REFERANS

**`docs/audits/2026-08-01_eksiklik_master.md`** — KIRO2'nin ölçülmüş
eksikliklerinin tek envanteri. **99 açık kalem**, 7 faza ayrılmış kontrol listesi.

Diğer denetim belgeleri **kanıt arşivi**; yeni iş için master'ı kullan.

### Sonraki oturum: FAZ 0'dan başla

> **Sıralama ilkesi: önce ÖLÇÜM BÜTÜNLÜĞÜ.** Bekçiler yalan söylüyorsa
> diğer hiçbir doğrulama anlam taşımaz.

| Faz | İçerik | Neden bu sıra |
|---|---|---|
| **0** | Ölçüm bütünlüğü (10 kalem) | Yeşil rapor veren ama hiçbir şey ölçmeyen bekçiler. **A.1 + A.1b BİRLİKTE** düzeltilmeli — iki hata birbirini maskeliyor |
| **1** | Yarım kalan fix'ler (9) | Bağlam taze, en yüksek ROI |
| **2** | Kaçan kardeşler (4) | Sınıf kapatma |
| **3** | Ürün kusurları (7) | Kullanıcıya dokunan |
| **4** | Test altyapısı (7) | |
| **5** | CI (3) | `F8-b`: kapı aktif dalda tetiklenmiyor → #462'nin değeri bugün **sıfır** |
| **6** | Doküman/hijyen | |

---

## Bu oturumda ne oldu

### Kapatılan 7 görev (#460-#466)

| Görev | Commit |
|---|---|
| #460 canlı ölçüm turu (5 komut, kontrol kollu) | — |
| #461 `user_item_fsrs` restore **P0** | `3773b3d42` |
| #462 GF merge kapısı **P0** | `c5a4f2c98` |
| #463 hızlı kazanç (9 kalem) | `962f7d4c9` |
| #464 RLS **ölçülebilir** yapıldı (kapatılmadı) | `64d6452be` |
| #465 admin PUT — **3.** bastırıcı bulundu **P0** | `b93cfcd3c`, `0d0dfd069` |
| #466 SMTP F20/F21/F21-yeni (**kısmi**, bkz. A.5b/A.5c) | `4ddd74383`, `ef6bafe47` |

### Sonra o işlere SALDIRILDI (7 skeptik + 2 hakem)

**49 teyitli kusur · 1 fantom · 13 "dayandı".**
Türler: kaçan kardeş 10 · vakum test 10 · eksik fix 10 · yanlış iddia 11 · regresyon 8.

> Kusurların **%41'i** doğrulama katmanının kendisinde. Ölçüm aletleri,
> ölçtükleri şeyden daha güvenilmez durumda.

### Kendi yarattığım P0 regresyon (düzeltildi, `b57be1ace`)

#462'nin token önbelleği, GF1x'in (`/auth/cikis`) **paylaşılan token'ı
blacklist'lemesine** yol açtı → sonraki **148 test** ölü token alıyordu →
`-x` ile koşum 13. testte duruyor → **kapı kalıcı kırmızı**.
"148 SKIP yalanı"nı "165 test hiç koşmuyor" ile değiştirmiştim.

**Neden kaçtı:** #462'nin doğrulama bölümü 6 birim testi + 2 YAML listeliyordu,
**e2e paketi hiç koşulmadı**.

**Fix:** `_login_taze()` — önbelleği atlar, önbelleğe yazmaz. Token'ı geçersiz
kılan test kendi token'ını alır → zehirlenme **yapısal olarak imkânsız**.
AST bekçisiyle çivili (mutasyon: GF1x'i `_login`e çevir → düşer).

---

## Fail Eden Testler

**YOK.** Koşulanlar: GF login kapısı 7/7 · GF e2e **178 test toplanıyor**
(NameError yok) · FSRS şema 5/5 · workflow YAML 12/12 · admin 56/56 ·
RLS bekçisi 6/6 · SMTP 6/6 · email_util tüketicileri 23/23.

**Önceden var (değişmedi):** tam backend paketi koşamıyor — FAZ 4 / `T1`.

---

## Kararlar (tekrar tartışılmasın)

- **`alembic/env.py` exclude satırı EKLENMEDİ** — `include_object()` çağrılarak
  ölçüldü, yapısal kapı zaten koruyor (+0 değer, #451).
- **`@admin_required` DÜZELTİLMEDİ** — 17 metottan 16'sının üretim çağıranı yok.
- **RLS fail-closed YAPILMADI** — 163 router'lık mimari iş; yerine tuzak dedektörü.
  *(Ama A.4: dedektör CI'da koşmuyor — iddiam yanlıştı.)*
- **`soru_guncelle` DEĞİŞTİRİLMEDİ** (`YENI-8`) — ikinci üretim çağıranı var.
- **İki paralel FSRS implementasyonu** — kanonik seçimi **ürün kararı**, yapılmadı.
- **Fantom listesi (master §5) 8 kalem — uğraşılmaz.**

---

## Alet dersleri (11)

1. **`cd` kalıcı** → geri alım bu oturumda **4 kez** sessizce başarısız oldu.
   `git checkout HEAD --` yanlış dizinden "pathspec did not match" verip hiçbir
   şey yapmıyor; `git status` da yanlış dizinden "boş" görünüyor. **Kökten ölç.**
2. **`git checkout -- X` yetmez** — index'ten yükler. `git add` yapıldıysa
   `git checkout HEAD -- X` gerekir.
3. **Commit'siz işi mutasyona sokma** — `checkout HEAD` fix'i de siler.
   (Bu oturumda `_login_taze` tanımını böyle kaybettim.)
4. **Yeşil test kırılmayı gizleyebilir** — bekçi AST adlarına bakıyordu,
   çözümleme yapmıyordu; tanımsız fonksiyona çağrı varken 7/7 yeşildi.
5. **Biçimlendirici `# pragma`/`# noqa`'yı satırdan kaydırır** — detect-secrets
   ve ruff **satır bazlı**. Pragma değerin kendi satırında olmalı.
6. **Biçimlendirici kullanılmayan import'u siler** (F401) → `NameError`.
   Kullanımı ÖNCE yaz, import'u SONRA.
7. **`pytest.fail`/`skip` = `BaseException`** — `pytest.raises(Exception)`
   yakalamaz, test kendisi "skipped" olur ve hiçbir şey ölçmez.
8. **detect-secrets sadece DEĞİŞEN dosyaları tarar** — dosyaya dokununca tamamı
   denetime girer, önceden var olan satırlar commit'i bloklar.
9. **`git check-ignore` TAKİPLİ dosyayı raporlamaz** — boş çıktı "ignore
   edilmiyor" demek değil.
10. **reward-hacking bekçisi boş gövdeli test double'ı reddeder** (exit 2).
    Susturma — gövde ver, kayıt tut; test de güçlenir.
11. **`.env*` salt-okunurdur** (CLAUDE.md) — izin sistemi haklı olarak bloklar.
