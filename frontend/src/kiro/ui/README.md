# ui-starter — KIRO2 çekirdek bileşen iskeletleri (web/React)

⚠️ **Test edilmemiş başlangıç kodu.** Bu klasör, `BILESEN_ENVANTER.md` §B'deki 15 P0 yapı taşının
React (web) iskeletidir — tasarım aracında üretildi, derleyiciden geçmedi. Hedef repoya taşıyıp
tip hatalarını/ince ayarı orada yapın. React Native portu aynı props imzalarıyla `ui-native`'e yazılır.

- Piksel referansı: `KIRO Bilesenler.dc.html` (tek sayfa) + ilgili ekran `.dc.html`'leri.
- Tüm renk/tipografi/radius `../tokens`'tan gelir — bileşen içinde ham hex YOK.
- Tema ekran TÜRÜNE bağlıdır (çalışma=paper, duygusal=dusk): ekran kökünü `<KiroThemeProvider theme="paper">` ile sar; kullanıcı toggle'ı değildir.
- Kurallar bileşenlere gömülü: hedef ≥44px (`hit.minTarget`), sayılar tabular-nums, risk=amber, ikon düğmede ariaLabel zorunlu.

```tsx
import { KiroThemeProvider, Button, Card, StatBlock } from './ui-starter';

<KiroThemeProvider theme="paper">
  <Card><StatBlock value="312" label="Çözülen soru" delta="+48" /></Card>
  <Button variant="primary" size="lg" onClick={start}>Çalışmaya başla</Button>
</KiroThemeProvider>
```
