# KIRO2 — Mimari Karar Kayıtları (ADR)

Format: tek dosya, karar başına bölüm. Durum: `öneri` → kullanıcı onayıyla `kabul`.
**2026-07-04: Tüm ADR'ler kullanıcı tarafından onaylandı.** ADR-002 revize edildi: kullanıcı kararıyla Stripe birincil, iyzico yedek.
Bağlam ölçüleri URETIM_YOL_HARITASI.md'den; kanon CLAUDE.md'den.

---

## ADR-000 · Hedef repo: mevcut `kiro2`'ye retrofit (greenfield DEĞİL)
**Durum:** kabul · 2026-07-04
**Bağlam:** Yol haritası Faz 0 "boş pnpm+Turborepo + Next.js" varsayıyordu. Keşif:
`HuseyinAts/kiro2` reposunda olgun bir `frontend/` var (Vite + React 18 + TS,
Vitest + Playwright + MSW + axe + BackstopJS + PWA/workbox altyapısı kurulu) ve
backend aynı repoda.
**Karar:** Yeni monorepo AÇILMAZ. KIRO2 tasarım sistemi mevcut `frontend/` içine
taşınır; Vite kalır, Next.js'e geçilmez. Mobil (Expo) ihtiyacı doğduğunda
`packages/` çıkarımı o gün değerlendirilir.
**Sonuç:** Faz 0.1 "monorepo kur" → "mevcut repoda `src/kiro/` alanı aç" olarak
değişir. MUI + lucide-react + emotion, kanonla çelişir (bespoke SVG, ikon
kütüphanesi YOK) → ekran portu ilerledikçe kademeli sökülür; yeni KIRO ekranları
bu bağımlılıkları HİÇ kullanmaz.

## ADR-001 · Auth: kendi JWT'miz (mevcut backend `/auth/*`)
**Durum:** kabul · 2026-07-04
**Karar:** Yönetilen sağlayıcı (Supabase/Auth0) alınmaz; sözleşmenin varsaydığı
`/auth/login · register · refresh · recover(3 adım)` mevcut backend'de
uygulanır. Web: httpOnly cookie; (ileride mobil: SecureStore). 401 → refresh →
tek tekrar. Misafir→hesap migrasyonu: yerleştirme θ'sı kayıt gövdesinde taşınır.
**Gerekçe:** Backend + auth modülleri repoda zaten var; sözleşme şekli birebir.

## ADR-002 · Ödeme: Stripe (tokenizasyon), iyzico yedek
**Durum:** kabul · 2026-07-04 (kullanıcı kararı: Stripe birincil — önerideki iyzico’nun yerini aldı)
**Karar:** Stripe birincil ödeme sağlayıcısı; kart YALNIZ sağlayıcıda tokenize
edilir, bizde tutulmaz (PCI kapsam dışı). TRY tahsilat + yerel kart/taksit
ihtiyacı doğarsa iyzico yedek olarak eklenir (soyutlama: `kartToken` alanı
sağlayıcı-bağımsız).
Ürün sözleri backend gereksinimi: bugün ödeme alınmaz · deneme bitmeden e-posta
hatırlatması ZORUNLU · iptal tek adım (`DELETE /billing/subscription`) ·
öğrenci rolüne fiyat gösterilmez.

## ADR-003 · Gerçek zamanlı: MVP'de 15 sn polling
**Durum:** kabul · 2026-07-04
**Karar:** Düello/Lig için WebSocket KURULMAZ; TanStack Query
`refetchInterval: 15000` yeter. Sözleşme değişmez — ileride aynı uçların
üstüne WS katmanı eklenebilir.

## ADR-004 · Push: FCM + APNs; web fazında ertelenir
**Durum:** kabul · 2026-07-04
**Karar:** Web-öncelikli ilk sürümde push YOK; Bildirim Merkezi `GET
/notifications` polling ile çalışır. `POST /notifications/token` ucu sözleşmede
hazır (openapi.yaml) — mobil (Expo) geldiğinde FCM+APNs bağlanır. "Deneme
bitmeden hatırlat" sözü push'a değil E-POSTAYA bağlıdır (ADR-002) — web fazında
da tutulur.

## ADR-005 · Analitik + hata izleme: Sentry + opt-in PostHog (EU)
**Durum:** kabul · 2026-07-04
**Karar:** Sentry (PII maskeleme AÇIK) + ürün analitiği opt-in PostHog EU
barındırma. KVKK: 17-19 yaş kullanıcı → veli aydınlatma metni kayıt akışında;
analitik varsayılan KAPALI, açık rıza ile açılır. Anksiyete-ilgili hiçbir metin
içeriği loglanmaz.

## ADR-006 · State: TanStack Query v5 + Zustand (karar teyidi)
**Durum:** kabul · 2026-07-04
**Karar:** Sunucu verisi TanStack Query v5; yerel state Zustand/useState.
Mevcut `react-query` v3 bağımlılığı v5'e yükseltilir (`@tanstack/react-query`).
Redux eklenmez — prototipteki tüm state ekran-yereldi.

## ADR-007 · Faz 2 bileşen kalite kapısı: Storybook 10 + BackstopJS (lokal) + a11y
**Durum:** kabul · 2026-07-22 (uygulama kararı)
**Bağlam:** 20 ui-starter bileşeni "test edilmemiş başlangıç"tı; Faz 2 DoD = story + RTL + axe +
görsel-diff. Storybook depoda kurulu değildi.
**Kararlar:**
- **Storybook 10.5.3** (`@storybook/react-vite`, Vite 7 destekli) + `addon-a11y`. SB10'un optional
  `vite-plus`→vitest-4 peer'i repo vitest 3 ile çakıştı → `--legacy-peer-deps` + `frontend/.npmrc`
  (`legacy-peer-deps=true`, CI `npm ci` paritesi). Repo vitest **3.2.4 korundu**.
- **BackstopJS = LOKAL dev gate.** Senaryolar `storybook-static/index.json`'dan türetilir;
  `misMatchThreshold=1` (≤%1); referans = BİZİM bileşenimiz (regresyon guard). Cross-OS
  font-render farkı nedeniyle CI'da koşmaz; `.dc.html` insan PX referansı; bitmaps gitignore.
  **CI gate'i = kanon-lint + tsc + vitest + axe.**
- **ProgressBar sapma:** `ariaLabel` prop eklendi (role=progressbar erişilebilir ad — WCAG 1.1.1).
  ui-starter'a a11y fix; test kural-dışlaması kaldırıldı.
- **Story renk literalleri:** stories `../tokens` import yerine token-eşdeğer hex literal kullanır
  (agent whitelist'i sınırlıydı); kanon-güvenli, ileride token-import'a refactor edilebilir (P3).
**Açık a11y bulgusu (design kararı):** white-on-coral `#FF6F5C` ~2.75:1 < AA — Button primary /
ChatBubble(me) / SideNav-aktif. Sistemik coral-CTA seçimi; koyulaştırma (≥3:1) veya metin-taşıyan
yüzeyde daha koyu coral önerilir. jsdom-axe kontrastı ölçemediği için otomatik yakalanmaz.
