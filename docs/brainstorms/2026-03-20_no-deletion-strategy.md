# Brainstorm: Hicbir Seyi Silmeden Nasil Devam Ederim
Tarih: 2026-03-20 | Domain: architecture | Perspektifler: Performans, Bakim, Maliyet
Kisitlama: HICBIR dosya silinmeyecek, hicbir ozellik devre disi birakilmayacak

## TL;DR
~9 saatte 3 kritik sorun cozulebilir: IRT bootstrap scripti ZATEN HAZIR (assign_difficulty_heuristic.py), record_answer()'a 6 satir ekleyerek 4 algortimayi bagla, App.tsx'e 1 route ekleyerek Revolutionary 10+ ozelligi gorunur yap. FSRS state persistence Sprint 2'de (~12 saat).

## Top 5 Aksiyon

| # | Aksiyon | Etki | Zorluk | Sure | Yeni Kod? |
|---|---------|------|--------|------|-----------|
| 1 | **IRT bootstrap** — assign_difficulty_heuristic.py calistir (dry-run + apply) | 5/5 | Kolay | ~3 saat | Hayir, script hazir |
| 2 | **Algoritma baglama** — record_answer() icine BKT->IRT->FSRS veri gecisi (6 satir) | 5/5 | Kolay | ~4 saat | 6 satir ekleme |
| 3 | **Revolutionary aktivasyonu** — App.tsx'e /admin/labs route + RevolutionaryDashboard | 4/5 | Kolay | ~2 saat | 1 route + 1 import |
| 4 | **FSRS state persistence** — Yeni fsrs_card_state tablosu + migration | 4/5 | Orta | ~12 saat | Yeni model + migration |
| 5 | **Bloom batch etiketleme** — 77K soruya Bloom etiketi, IRT'yi guclendirir | 3/5 | Kolay | ~4 saat | Script calistir |

Sprint 1: ~9 saat (aksiyon 1-3)
Sprint 2: ~16 saat (aksiyon 4-5)

## Konsensus

1. **IRT bootstrap script HAZIR** — assign_difficulty_heuristic.py IRT_MAP tanimli (VERY_EASY=-2.0 ... VERY_HARD=2.0). Calistirilmasi yeterli.
2. **Algoritma baglama minimal efor** — record_answer() zaten 4 algortimayi seri cagiriyor. BKT new_p_L -> IRT initial_theta = (new_p_L - 0.5) * 4.0.
3. **Silmek yerine aktive etmek daha degerli** — Revolutionary 18 component yazilmis. 1 route = 10+ ozellik gorunur.

## Catismalar

| Konu | Taraf A | Taraf B | Karar |
|------|---------|---------|-------|
| FSRS zamanlama | Performans: Sprint 1 | Maliyet: Sprint 2 | Maliyet hakli — once 3 kolay is |
| Revolutionary backend | Bakim: smoke test sart | Maliyet: demo bozulur sadece | Bakim hakli — /admin/labs + "Deneysel" etiketi |
| Wrapper bypass | Bakim: yorum ekle zorunlu | Performans: dokunma | Her ikisi — Sprint 3'e birak |

## Perspektif Detaylari

### 1. Performans Muhendisi

**IRT Heuristik Bootstrap:** student_success_rate ve times_asked field'lari mevcut. irt_difficulty = -logit(success_rate) * 1.7. times_asked >= 30 olanlara is_calibrated=True. Mevcut IRT kodu DEGISMEZ.

**BKT->IRT Koprusu:** record_answer() satirlari 239-248. initial_theta = (new_p_L - 0.5) * 4.0. FSRS'ye BKT attempt_count aktarilabilir. 6 satir ekleme.

**FSRS State:** Yeni fsrs_card_state tablosu (student_id, topic_id, stability, difficulty, reps, lapses, due_date). Mevcut FSRS kodu degismez, sadece state okuma/yazma eklenir.

**Kor nokta:** record_answer() senkron seri — 1000+ concurrent'ta bottleneck.
**Uyari:** student_success_rate=0 ise logit patlar, clamp(0.05, 0.95) zorunlu.

### 2. Bakim/Organizasyon Muhendisi

**App.tsx Bypass:** Wrapper'lari silmeden, lazy import'lari dogrudan Modern* dosyalarina yonlendir. 27 wrapper kalir ama kullanilmaz.

**Revolutionary /admin/labs:** 18 component tek route ile gorunur. RevolutionaryDashboard container. Admin-only.

**Backend Feature Config:** features.json veya FEATURE_* env var ile orphan router'lari kontrol altina al.

**Kor nokta:** Revolutionary backend servisleri calisir mi bilinmiyor, smoke test sart.
**Uyari:** Bypass edilen wrapper'lara // INACTIVE yorumu zorunlu.

### 3. Maliyet/Strateji Analisti

**Kritik kesif:** assign_difficulty_heuristic.py ZATEN YAZILMIS. IRT_MAP tanimli. Sadece calistirilmasi lazim.

**ROI sirasi:** Algoritma baglama (4 saat, en yuksek) > IRT bootstrap (3 saat) > Revolutionary route (2 saat)

**Bloom bonus:** Bloom taxonomy classifier batch calistirilabilir, IRT'yi guclendirir.

**Kor nokta:** Bloom classifier IRT'yi guclendirir — onceki raporlarda gozden kacinmis.
**Uyari:** YOLO detector'a dokunmayin — zaten calisiyor.

## Kor Noktalar & Uyarilar

### Kor Noktalar
1. assign_difficulty_heuristic.py ZATEN VAR (pozitif kesif)
2. Bloom classifier IRT'yi guclendirir (difficulty_level + bloom_level)
3. record_answer() senkron seri — gelecekte bottleneck
4. FSRS state = ogrenci x konu bazli, ayri tablo gerekli
5. Revolutionary backend servisleri test edilmemis

### Uyarilar
1. YOLO detector'a dokunmayin — zaten aktif
2. Wrapper bypass'i simdi yapmayin — Sprint 3
3. success_rate=0 ise logit patlar — clamp zorunlu
4. Revolutionary backend smoke test ONCE

## Uygulama Plani

```
Sprint 1 (~9 saat, 1-2 gun):
  1. IRT bootstrap: python assign_difficulty_heuristic.py --dry-run && --apply (~3 saat)
  2. Algoritma baglama: record_answer() icine 6 satir ekleme (~4 saat)
  3. Revolutionary route: App.tsx + /admin/labs (~2 saat)

Sprint 2 (~16 saat, 2-3 gun):
  4. FSRS state persistence: model + migration + record_answer guncelleme (~12 saat)
  5. Bloom batch: bloom_taxonomy_classifier.py batch calistirma (~4 saat)

Sprint 3 (opsiyonel):
  6. App.tsx wrapper bypass (Modern* direkt import)
  7. Backend feature flag sistemi (features.json)
  8. record_answer() async parallelization
```

---
*3 paralel perspektif (Performans, Bakim, Maliyet), "silmeden baglama" stratejisi, 2026-03-20*
