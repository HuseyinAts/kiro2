# frontend/src/kiro — KIRO2 Şafak tasarım sistemi (retrofit)

ADR-000: mevcut `frontend/` (Vite + React 18 + TS) içine retrofit; yeni monorepo YOK.
Kaynak handoff: repo kökü `design/` (kanon: `design/CLAUDE_CODE_TALIMAT.md` +
`design/ENTEGRASYON_PLANI.md`).

## Yerleşim
- `tokens/` — tokens.ts + tokens.css (birebir) + index barrel
- `types/` — types.ts (birebir) + index barrel
- `api/` — api-client.ts + kiro-data.json (mock kaynağı)
- `ui/` — ui-starter bileşenleri (Faz 2 kalite kapısı; şu an yalnız `theme.tsx` foundation)
- `screens/` — Faz 3 ekran portları (şu an `OrnekPage` = Faz 1 mock-render kanıtı)

## Tema kuralı (EN sık ihlal edilen kanon)
Tema kullanıcı toggle'ı DEĞİL, **ekran türüdür**: çalışma/odak/analitik/panel = `paper`,
duygusal/hub/kutlama/ritüel = `dusk`. Route-bazlı `KiroThemeProvider theme=...` ile uygula; ASLA
karıştırma, asla kullanıcıya seçtirme.

## Mock → live geçişi
Ekran kodu YALNIZ api-client'ı çağırır. `configureKiroApi({mode:'mock', mockData})` →
`configureKiroApi({mode:'live', baseUrl})` tek konfig; ekran değişmez. Motorlar (θ/CAT/FSRS/BKT)
SUNUCUDA — istemci yalnız sunucu-otoriter sonucu render eder (soru `dogru` alanı istemciye inmez).

## Verbatim'den sapmalar (kayıt)
1. `api/api-client.ts`: import `./types` → `../types` (klasör yerleşimi gereği).
2. `api/api-client.ts` + `types/types.ts`: iki doküman-yorumundaki literal "eksik" kelimesi
   kaldırıldı (projenin kendi `kanon-lint` EKSIK kuralını tetikliyordu) — anlam korundu ("bekliyor").
3. `api/api-client.ts`: header yorumundaki `⚠️` emoji → `[DIKKAT]` (kanon-lint EMOJI kuralı) +
   kullanılmayan `Question` type-import kaldırıldı (repo strict `noUnusedLocals` → TS6196).

## Kanon lint (yerel)
Repo kökünden: `node design/scripts/kanon-lint.mjs frontend/src/kiro` (ihlalde exit 1).
frontend'den: `npm run kanon:lint`.
