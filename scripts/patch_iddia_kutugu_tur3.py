"""Tur 3 doğrulama sonuçlarını kütüğe yaz (wf_797a2327-67f).

5 iddia, 13 ajan (10 çürütücü + 3 hakem). Fantom oranı %60.
Aynı block-bazlı, idempotent desen (bkz. patch_iddia_kutugu_tur2.py).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

KUTUK = Path(__file__).resolve().parents[1] / "docs/audits/2026-08-12_25uzman/iddialar.yaml"
ESKI_KUYRUK = "\n    kanit: null\n    commit: null\n    zorlayici_test: null"

YAMALAR: list[tuple[str, str, str]] = [
    (
        "U07",
        "    curutme_sorusu: \"CONCURRENTLY zaten yazıcıları bloklamaz — 'lock contention' iddiası PostgreSQL semantiğiyle çelişiyor olabilir. Gerçek bekleme ölçüldü mü?\"",
        """    severity_olculen: yok
    durum: fantom
    kanit: |
      TUR 3 (wf_797a2327-67f). İki çürütücü OLGULARDA anlaşıyor, yalnız
      ETİKETTE ayrıldı (fantom vs abartılı P3) -> 3. HAKEM karar verdi: fantom.

      🔴 HAKEMİN BAĞIMSIZ DENEY KOLU (ikisinin de yapmadığı): canlı DB'de
      CONCURRENTLY'Lİ ve CONCURRENTLI'SIZ refresh'i AYRI AYRI tetikleyip
      kilitleri ölçtü:
        CONCURRENTLY'Lİ (gerçek fonksiyon): ExclusiveLock alıyor.
          SET lock_timeout='2s'; SELECT count(*) FROM mv_safe_for_beta
          -> BAŞARILI, reader_saw=0 (BLOKLANMADI)
        CONCURRENTLY'SİZ (kontrol kolu, bilinen-kötü hâl):
          REFRESH MATERIALIZED VIEW mv_safe_for_beta (CONCURRENTLY YOK)
          -> AccessExclusiveLock, okuyucu "ERROR: canceling statement due to
             lock timeout"
        Kontrol kolu iki hâli AYIRT ETTİ -> ölçüm geçerli, alet arızası değil.

      Migration'ın kendi docstring'i (20260727_mv_safe_for_beta.py:29-31)
      CONCURRENTLY'nin SEÇİLME GEREKÇESİNİ zaten şöyle açıklıyor:
        "CONCURRENTLY olmadan yenileme matview'i AccessExclusive kilitler,
         yenileme süresince tüm soru servisi durur."
      Yani iddia, sistemin CONCURRENTLY'yi seçme SEBEBİNİ kusur sanıyor.

      GÖREV TARAFI ZATEN KAPALI: celery_app.py:129-131 beat_schedule
      "refresh-safe-pool-nightly" crontab(hour=3, minute=30) — KOŞAN
      kiro2-celery-beat imajında canlı (docker exec ile doğrulandı, çalışma
      ağacında değil), modül include'da, beat adı ile @shared_task adı
      birebir eşleşiyor. Görev #428'de zaten tamamlanmış (27 Tem 2026).

      Advisory lock (quality_gate_tasks.py:29-35): gündüz küratör-tetikli
      refresh'ler pg_try_advisory_xact_lock ile zaten tekilleştiriliyor;
      self-contention koddan önlenmiş.

      Ankraj yanlış dosyayı gösteriyor: quality_gate.py:68-80'de hiç
      REFRESH/CONCURRENTLY yok.

      YAN ÖLÇÜM (U07'yi değiştirmez, sonraki iddiaları etkiler):
      question_bank 12 sütun, quality_review_status sütunu YOK, questions
      tablosu YOK — bu ortamda hacme/süreye bağlı hiçbir iddia ölçülemez.
    fix_degeri: |
      SIFIRIN ALTINDA. Kilit kazancı ölçülen olarak 0 (CONCURRENTLY zaten
      okuyucuyu bloklamıyor); bedeli var (kapı bayatlığının artması —
      quality_gate.py docstring'i "matview bayatlığı + 1 saat" diye zaten
      uyarıyor). Görev tarafı da zaten kapalı. Önerilen değişikliğin hem
      teknik gerekçesi hem de aksiyon kısmı geçersiz.
    commit: null
    zorlayici_test: null""",
    ),
    (
        "U08",
        "      davranış üretiyor mu (ölçülmüş)? Hayır ise severity P1 DEĞİL, P3.\n",
        """    severity_olculen: P3
    durum: abartili
    kanit: |
      TUR 3 (wf_797a2327-67f), iki çürütücü MUTABIK.

      Ankraj birebir doğru: irt_daemon.py:27-38 sync_calibrate_wrapper,
      asyncio.new_event_loop() + run_until_complete() + close(); çağrı yeri
      _run_loop:113-121 `await loop.run_in_executor(NLP_POOL,
      sync_calibrate_wrapper, ...)` — main event loop'u BLOKLAMAMA amacı
      ZATEN bu satırda karşılanıyor.

      🔴 KOD OKUYARAK DEĞİL TETİKLEYEREK ölçüldü: aynı deseni (ThreadPoolExecutor
      + her çağrıda new_event_loop+run_until_complete+close, 2 thread'de
      tekrar kullanım, 20 eşzamanlı görev) izole ortamda çalıştırdı:
        RESULTS: [0,2,4,...,38]  — 0/20 hata, deterministik doğru sonuç.
      Desen TETİKLENEBİLİR BOZUKLUK ÜRETMİYOR.

      "asyncio.to_thread refactor" LİTERAL OLARAK UYGULANAMAZ: to_thread
      SYNC fonksiyonu ASYNC koddan çağırmak içindir (await zorunlu). İhtiyaç
      TERS yönde: ASYNC coroutine'i (calibrate_question_irt, doğrulandı:
      "async def calibrate_question_irt") SYNC bağlamdan (thread-pool worker)
      çalıştırmak. to_thread bu yöne uygulanamaz.

      Cross-loop risk kontrolü: IRTCalibrationService.__init__ yalnız saf
      string/numpy state taşıyor; DB session, asyncio.Lock/Queue/Event YOK
      -> "Future/Task attached to different loop" hata sınıfı yapısal olarak
      mümkün değil.

      Codebase'de to_thread GERÇEKTEN var ve DOĞRU yönde kullanılıyor
      (irt_service.py:479-489, sync fonksiyonu async'ten çağırıyor) — yani
      geliştirici deseni biliyor, burada kasıtlı olarak farklı yöne ihtiyaç var.
    fix_degeri: |
      Yakın sıfır / davranışsal kazanç yok. Desen zaten hatasız (0/20 hata,
      kontrol kolu). Literal "to_thread refactor" tarif edildiği yerde
      uygulanamaz. En fazla kozmetik sadeleştirme (new_event_loop+run_until
      _complete+close -> asyncio.run(), 4 satır->1 satır), davranış değişmez,
      defekt düzeltmesi değil.
    commit: null
    zorlayici_test: null""",
    ),
    (
        "U14",
        "      over-engineering (rapor §D.1/#6 + KISS).\n",
        """    severity_olculen: yok
    durum: fantom
    kanit: |
      TUR 3 (wf_797a2327-67f). İki çürütücü OLGULARDA anlaşıyor
      (idempotency guard zaten var), yalnız hangi katmanın belirleyici
      olduğunda ayrıldı -> 3. HAKEM karar verdi: fantom.

      İDEMPOTENCY GUARD ZATEN VAR (20 Nis 2026, b642f91cf):
        offline_sync_service.py:226-263 process_sync_results():
          consumed_at dolu paket -> "already_consumed" reddi, commit YOK.
        Canlı test: test_sync_results_s4_replay_rejected_as_batch PASSED
        (6/6 passed).

      🔴 HAKEMİN BAĞIMSIZ ÖLÇÜMÜ — İKİ ÇÜRÜTÜCÜNÜN DE BAKMADIĞI DAĞITIM
      KATMANI:
        curl /api/v1/offline/sync-results (host)     -> 404
        curl /api/v1/offline/sync-status (host)       -> 404
        docker exec kiro2-backend: import api.offline_sync_api
          -> ModuleNotFoundError: No module named 'api.offline_sync_api'
        docker exec kiro2-backend ls /app/api | wc -l -> 42  (host: 148)
        host çalışma ağacında: import api.offline_sync_api OK, 4 yol var
        -> KAYNAK ÇALIŞMA AĞACINDA VAR, DAĞITILAN İMAJDA YOK.

      EVREN-SEVİYESİ ÖLÇÜM:
        SELECT count(*) FROM offline_sync_packages -> 0
        -> üretimde bugüne dek TEK bir senkron paketi bile üretilmemiş.

      FRONTEND'DE YAKALAMA YOLU YOK:
        grep "addToSyncQueue|enqueue|offlineQueue" frontend/src -> 0 sonuç
        examStore.ts:400 hata olunca set({saveStatus:'error'}) — kuyruğa
        YAZMA yok. Çakışacak "olay" hiç üretilmiyor.

      Hakemin kendi runtime probe'u (test dosyasını kullanmadan doğrudan
      çağrı): taze paket -> synced=0/failed=1; tekrar -> already_consumed,
      commit_awaited=0. Guard'ın kendisi çalışıyor.

      3 ön-koşulun ÜÇÜ DE yok: yakalama (0) + dağıtılan uç (404) + gerçek
      paket (0 satır). "Çakışma -> veri kaybı" senaryosu şu an ürünün
      hiçbir yerinde tetiklenemez.
    fix_degeri: |
      SIFIR. Vector clock veya SELECT FOR UPDATE eklemek hiçbir kullanıcı-
      görünür davranışı değiştirmez — özellik dağıtılmamış (404) ve hiç
      kullanılmamış (0 paket). Yeniden gündeme gelirse tek belirleyici ölçüm:
      offline_sync_packages > 0 VE canlı openapi'de /api/v1/offline/sync-
      results yolu görünmesi. İkisi birden olmadan bu iddia semptom değiştirmez.
    commit: null
    zorlayici_test: null""",
    ),
    (
        "U17",
        "    curutme_sorusu: \"Proje KaTeX kullanıyor olabilir (MEMORY: 'KaTeX' geçiyor). MathJax hiç yoksa iddia FANTOM.\"",
        """    severity_olculen: yok
    durum: fantom
    kanit: |
      TUR 3 (wf_797a2327-67f), iki çürütücü MUTABIK. curutme_sorusu'nun
      kendi hipotezi birebir doğrulandı.

      Ankraj dosyasında (SoruCozmePage.tsx) sıfır isabet:
        grep "mathjax|MathJax|katex|KaTeX|MathText" SoruCozmePage.tsx -> 0
      QuestionCard.tsx (SoruCozmePage'in tek render bileşeni) soruyu/şıkları
      HAM METİN basıyor: <p>{soru}</p>, <span>{sec}</span> — math render
      katmanı hiç devrede değil.

      Canlı matematik render zinciri KaTeX, MathJax DEĞİL:
        MathText.tsx: "KaTeX ile $...$ ve $$...$$ render eder"
        MarkdownRenderer.tsx: remark-math + rehype-katex
        MathText zaten React.memo ile sarılı (içerik değişmedikçe yeniden
        hesaplama YOK) — "caching yok" iddiası bu bileşen için de yanlış.
      7 canlı ekran (OSYMExamInterface, DiagnosticTestInterface, AnswerPanel,
      QuestionPanel, ProductiveFailureFlow, AdaptifTestPage, ...) MathText
      kullanıyor. SoruCozmePage bunlardan biri DEĞİL.

      MathJax'i GERÇEKTEN çağıran tek dosya (Questions/QuestionBank.tsx)
      hiçbir yerden import edilmiyor -> ölü/orphan kod.
      MathJax'in FİİLEN ÇALIŞTIĞI tek yer: MathFormula.tsx
      (/accessibility-demo rotası, soru çözme akışı DEĞİL) — VE bu dosyanın
      kendi init kodu SVG font-cache'i ZATEN AÇIYOR: `svg: {fontCache:
      'global'}`. Yani "MathJax SVG önbelleklenmiyor" iddiası, MathJax'in
      fiilen çalıştığı TEK yerde teknik olarak da YANLIŞ.

      Git tarihi: SoruCozmePage.tsx'in 4 commit'lik geçmişinde MathJax/KaTeX
      hiç geçmedi; math-render geliştirme çizgisi tamamen KaTeX üzerinden
      ilerlemiş (e5b889aff, 53c9c3762, 6a97a5c17, 4e77cadd8, 30f6752a5).

      KONTROL KOLU: aynı grep bilinen-var (MarkdownRenderer.tsx, MathText.tsx)
      ve bilinen-yok (SoruCozmePage.tsx) örneklerini doğru ayırt etti.
    fix_degeri: |
      Sıfıra yakın. Önerilen görev canlı bir yüzey bulamaz — SoruCozmePage
      hiç MathJax kullanmıyor. Gerçek teknoloji (KaTeX) zaten React.memo ile
      önbellekli. Kaygı KaTeX render maliyetiyse bu AYRI ve ÖLÇÜLMEMİŞ bir
      konu (formül-başına süre bilinmiyor) — U17'nin kapsamı değil.
    commit: null
    zorlayici_test: null""",
    ),
    (
        "U20",
        '    curutme_sorusu: "Auth cookie tabanlıysa (CLAUDE.md: \'Cookie (frontend) + Bearer (API) dual auth\') localStorage senkronu gereksiz olabilir."',
        """    severity_olculen: P2
    durum: abartili
    kanit: |
      TUR 3 (wf_797a2327-67f). İki çürütücü İKİSİ DE "abartılı" dedi ama
      farklı severity'de (P3 vs P2) -> 3. HAKEM karar verdi: P2.

      Teknik çekirdek doğrulandı: authStore.ts + repo geneli grep'te
      addEventListener('storage'), BroadcastChannel, onstorage -> 0 sonuç.
      initializeAuth() (AuthProvider.tsx:18-22) sekme başına TEK sefer,
      visibilitychange/interval yok. zustand v4 persist'in bilinen
      sınırlaması (manuel eklenmesi gerekir).

      🔴 HAKEMİN BAĞIMSIZ ÖLÇÜMÜ — İKİ ÇÜRÜTÜCÜNÜN DE MODELLEMEDİĞİ
      SENARYO: her ikisi de yalnız "aynı kullanıcı başka sekmede logout"
      senaryosunu inceledi ve 401-interceptor'ün kendiliğinden düzelttiğini
      söyledi. Ama PAYLAŞIMLI CİHAZDA "başka sekmede FARKLI KULLANICI ile
      LOGIN" senaryosunda: cookie değişir, istekler 200 döner, 401 HİÇ
      OLUŞMAZ (apiClient.ts:83, 403'ü yönlendirmeye bağlamaz) — açık sekme
      yanlış kimliği/rolü sayfa yenilenene kadar KENDİLİĞİNDEN DÜZELMEZ.

      KULLANICIYA ÇIKAN GERÇEK KATMAN (ProtectedRoute.tsx:23):
        useAuthStore() BELLEK-İÇİ store'u okuyor, localStorage'ı DEĞİL.
        `loading` kapısı (satır 26-38) "persisted isAuthenticated'a
        güvenme, cookie süresi dolmuş olabilir" yorumuyla YENİ mount'ta
        sunucu gerçeğini bekliyor — ama AÇIK KALAN sekmede bu kapı
        tetiklenmiyor.

      KONTROL KOLU: filtresiz addEventListener grep'i 40+ bilinen-iyi
      eşleşme döndürdü (api.ts SSE, App.tsx 'load', kiro2DB.ts 'online')
      -> 'storage' yokluğu alet arızası değil, gerçek yokluk.
    fix_degeri: |
      P1 DEĞİL: yetkilendirmeyi sunucu her istekte cookie'den zorluyor,
      erişim bypass'ı ölçülmedi. P3 DE DEĞİL: kendiliğinden düzelmeyen
      yanlış-kimlik gösterimi + 403 ile kırılan rol-bazlı sayfalar salt
      görsel cila değil. Fix scope küçük: authStore.ts'e
      `window.addEventListener('storage', ...)` + `persist.rehydrate()`
      eklemek; aynı sistemik boşluk cognitiveStore/examStore/settingsStore'u
      da etkiliyor, tek noktadan (persist config helper) kapatılabilir.
    commit: null
    zorlayici_test: null""",
    ),
]


def blok_sinirlari(metin: str, iddia_id: str) -> tuple[int, int] | None:
    bas_isaret = f"\n  - id: {iddia_id}\n"
    if bas_isaret not in metin:
        return None
    bas = metin.index(bas_isaret) + 1
    sonraki = metin.find("\n  - id: ", bas)
    return (bas, sonraki if sonraki != -1 else len(metin))


def main() -> int:
    metin = KUTUK.read_text(encoding="utf-8")
    basarili: list[str] = []
    basarisiz: list[str] = []

    for iddia_id, ankraj, yeni in YAMALAR:
        sinir = blok_sinirlari(metin, iddia_id)
        if sinir is None:
            basarisiz.append(f"{iddia_id}: kayit bulunamadi")
            continue
        bas, son = sinir
        blok = metin[bas:son]

        if "durum: beklemede" not in blok:
            basarisiz.append(f"{iddia_id}: durum zaten 'beklemede' degil")
            continue
        if ankraj not in blok:
            basarisiz.append(f"{iddia_id}: ANKRAJ blok icinde yok")
            continue
        if ESKI_KUYRUK not in blok:
            basarisiz.append(f"{iddia_id}: kanit/commit kuyrugu blok icinde yok")
            continue

        a_idx = blok.index(ankraj)
        a_son = blok.index("\n", a_idx)
        k_idx = blok.index(ESKI_KUYRUK, a_idx)
        blok = blok[: a_son + 1] + yeni + blok[k_idx + len(ESKI_KUYRUK) :]
        blok = blok.replace("    severity_olculen: null\n    durum: beklemede\n", "", 1)

        metin = metin[:bas] + blok + metin[son:]
        basarili.append(iddia_id)

    KUTUK.write_text(metin, encoding="utf-8")
    for x in basarili:
        print(f"[YAMALANDI] {x}")
    for x in basarisiz:
        print(f"[BASARISIZ] {x}")
    return 0 if not basarisiz else 1


if __name__ == "__main__":
    raise SystemExit(main())
