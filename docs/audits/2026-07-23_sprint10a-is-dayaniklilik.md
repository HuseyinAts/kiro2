# KIRO2 — Faz 3 · SPRINT10-A (Grup 8 · İş & Dayanıklılık kısmi 3/7)

**2026-07-23** — 3 ekran ✅: **Bildirim Merkezi · Alan Kütüphanesi · Çevrimdışı** (hepsi öğrenci, PAPER). Keşif: `2026-07-23_sprint10-grup8-kesif.md`. Dilimleme kararı: 3 alt-tur (S10-A basit 3 → S10-B billing zinciri → S10-C Ayarlar).

## Kararlar (kullanıcı, keşif sonrası)
- Ödeme/PSP Faz 3 saf-mock · Öğrenci fiyat GÖSTERİLMEZ (→ "veli hesabından yönet") · Sakin-mod+Sıralamayı-gizle **tek `KullaniciAyar` kaynağı + tam davranış** (Faz3 localStorage mock) — bunlar S10-B/S10-C'de uygulanacak.

## Süreç
Keşif workflow (11 ajan) → build workflow (infra 1 + 3 ekran paralel) → **otoriter gate** → adversarial review (22 ajan, 4 boyut + skeptik doğrulama) → fix (3 paralel) → breakpoint gate.

## Infra (additive, üretime sızmaz)
- **types.ts (+11 tip):** `BildirimTon/Bildirim/BildirimGrup/BildirimYanit` · `ConnectivityState/CachedPack/SyncQueueItem/SyncStatus` · `AlanKutuphaneDers/AlanKutuphaneAlan/AlanKutuphaneData` (mevcut `Alan/AlanKey/DersKatalogEntry/KatalogUnite` REUSE).
- **api-client.ts (+6 metod):** getBildirimler · markBildirimOkundu · markTumBildirimOkundu · clearBildirimler · getAlanKutuphane · getCevrimdisiDurum (mutation'lar server-sim, ekran optimistik). Plan* çakışması önlendi (abonelik "Plan"ı S10-B'de ayrı ad).
- **mswHandlers.ts:** notifications(+read/read-all/clear) · alan-kutuphane · offline/durum (çift-kayıt yok).
- **kiro-data.json + MockData Pick (İKİ yer):** `bildirimler` · `alanKutuphane` · `cevrimdisi`.

## Ekranlar
- **Bildirim Merkezi:** SideNav + tek-sütun gruplu liste (Bugün/Bu hafta); pil "{n} yeni" coralCtaBg; okundu/tümü-okundu/temizle optimistik; EmptyState "Her şey sakin."; zayıf-konu ton **amber** (kanon>DC, coral değil).
- **Alan Kütüphanesi:** geri-oku + 3-alan ızgarası + tek-açılır akordeon katalog; sunucu-otorite sayaç; "örnek soru havuzda" şeridi koşullu (soruSayisi>0).
- **Çevrimdışı:** SideNav + durum bandı (amber/dawn/success, kırmızı yok) + iki-sütun (hazır paketler / eşitleme kuyruğu); `navigator.onLine` + online/offline event; manuel toggle yok (DC meta-notu atlandı).

## Adversarial (22 ajan) — 12 doğrulandı / 6 phantom
- **1 major (AA):** Alan kapanış paragrafı + konu sıra-no `ink.faded2 #B0A9B8` (2.08:1 AA FAIL) → `ink.muted` (5.15:1). **FIX.**
- **Minör/nit fix:** Alan DC statik dipnot "TYT ortak…" geri eklendi + akordeon etiketi DC-sadık `{konuToplam} konunun tamamını gör` (sunucu sayacı) + yanıltıcı yorum düzeltildi; Bildirim "Bildirimler" `<div>`→`<h1>`; Çevrimdışı hardcoded 'bugün' kaldırıldı (mock `sonEsitleme`="bugün 14:32", sunucu-otorite) + `getMe().catch` tolere + sol `<section> minWidth:0`; 3 dosyaya error/loading/empty(+yeniden_baglaniyor) test kapsamı.
- **Phantom (doğru elendi):** SideNav ≤1023 rail = yerleşik sistem kararı (BREAKPOINT_SPEC §3); violet=başarım DC-amaçlı; zayıf-konu 'biz' koç sesi DC-sadık; iki-sütun overflow yok (minWidth defensive eklendi yine de).
- **Breakpoint:** ilk turda 5 FAIL (Alan akordeon buton `minHeight:36 < 44` hit-target, 5 genişlik) → `minHeight:44`+padding → **0 FAIL**.

## Kapı (otoriter, bağımsız çalıştırıldı)
kanon **0 ihlal** (14 uyarı pre-existing, dokunulmayan dosyalar) · scoped strict tsc **0** · vitest **57 dosya / 340 test PASS** (308→340: +32 yeni) · **breakpoint 0 FAIL / 364** · axe temiz.

**İlerleme: 34/42 ekran + 1 composite (QuestionCard) + `ui/WeeklyActivityBars`. Grup 8 kısmi (3/7).**
Sonraki: **S10-B billing zinciri** — Abonelik · Ödeme(+3DS mock) · Plan Yönetimi (öğrenci fiyat gizli → veli yönlendirme; PSP saf-mock; AbonelikPlan ayrı ad).
