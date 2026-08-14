# Session S210 — Gemini turu devralma + question_bank model split

**Branch:** feature/self-evolution-optimization
**Commit'ler:** `dbf06794c` (frontend) · `99cda20a4` (backend modüller) · `0fd9b8413` (model split, P0-B)
**Önceki:** `015e11123` (S209)
**📄 Detaylı handoff:** `docs/audits/2026-08-15_s210_gemini_devir_model_split.md`

## ✅ Yapılanlar

1. **Gemini turu ölçüldü.** 3522 kirli dosya → 2020 `M`'nin **1345'i yalnız CRLF**;
   142 silinen `.py`'nin **75'i `script_mezarligi/`'na taşınmış** (60'ı gerçek silme,
   hiçbiri import edilmiyor). `git status`'ta `D` = silme DEĞİL, taşıma da olabilir.
2. **Frontend kurtarıldı** (`dbf06794c`). `package.json`/`index.html`/`vite.config.ts`
   dahil 334 dosya diskte yoktu; **120'si geri yüklendi** (115 `tsc` + 5 CSS `vite`
   istedi), 219'u ölü kod. `mockExamService.ts` yeni `/api/v1/exams` sözleşmesine
   bağlandı — `examService.ts`'e dokunulmadı (ad çatışması vardı).
   **tsc 17→0, `npm run build` exit 0.**
3. **Backend modüller** (`99cda20a4`). `leaderboard_service` `dict[str, any]` yüzünden
   hiç import edilemiyordu.
4. **P0-B KAPANDI** (`0fd9b8413`). HEAD modeli 84 kolon, canlı DB 12 — **HEAD zaten
   çalışmıyordu**. 69 alan taşınmış (AST farkı). 2542 erişim/340 dosya göründü ama
   **sert çekirdek 108/17** → strangler uygulanabilir oldu. Devrediciler alan listesini
   kolonlardan **türetiyor**; sınıf düzeyi **kasıtlı açık hata** (sessiz `None` 108 JOIN
   yerini gizlerdi). `exams.py` de indi + 3 gizli kusur (`avg_time` UnboundLocalError,
   `SubjectArea["MAT"]` KeyError, `and_(..., True)`).

**Doğrulama:** 27/27 PASS · pre-commit 0 fail (import smoke 154 modül) · uygulama
1224 yol · **mutasyon 4/4 öldürdü** (M1/M2 exams, M3/M4 compat).

## ⏳ Sıradaki

- **#485** — 108 sınıf-düzeyi `QuestionBankItem.<alan>` sorgusunu JOIN'e çevir (17 dosya).
  Bloke etmiyor, açık hata veriyor. Yoğun: `question_crud_service.py` (42),
  `question_bank_service.py` (13), `duel_api.py` (12), `curator.py` (10).
- **#444** — Öğretmen Öğrenciler sayfası UI (roster backend hazır)
- `core/rag_service.py:682` `search_with_mmr` O(k²) embed kusuru
- Kirli ağaç ~3280 dosya (Gemini'nin kasıtlı commit'siz işi) — ayrı triyaj

## ⚠️ Ortam
- Bu makine **taze**: `question_bank` **0 satır**, 246 tablo, DB 32 MB.
  DB ölçümünden önce satır sayısına bak.
- `DISABLED_ROUTERS` artık **boş** — 154 router yükleniyor. MEMORY.md'deki
  "110 router kapalı / 167 yol 404" tablosu bu ağaçta **geçersiz** (düzeltildi).

## 🧰 Alet dersleri (defterde 9 satır, `aktif`)
- Tip grafiği ≠ paketleyici grafiği — `tsc` "temiz" dedikten sonra `vite` 5 dosya
  daha istedi; ambient `.d.ts` hiçbir import grafiğinde görünmez
- mypy iki sebeple 0 verir: bail-out (`errors prevented`) ve anotasyonsuz kod (`Any`)
- Göçün boyutu **toplam kullanım değil, karşılanamayan alt küme**
- Uyumluluk katmanı kör noktasında **açık hata** vermeli, sessiz varsayılan değil
