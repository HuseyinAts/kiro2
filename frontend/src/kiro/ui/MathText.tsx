// ============================================================================
// KIRO2 — MathText (kiro sarmalayıcı)
// Soru metni ve şıklardaki LaTeX'i okunur kılar. CAT-uygun MATEMATIK havuzunun
// %60.7'si (6,129/10,102 soru, 27 Tem 2026 ölçümü) `$...$` / `\frac` içeriyor;
// sarmalanmadan basılırsa öğrenci ham "$\frac{2}{7}$" görür.
//
// NEDEN AYRI DOSYA: kiro ekranları kiro DIŞINA import ETMEZ (mock/Storybook
// izolasyonu). Paylaşılan MathText'i kopyalamak yerine dış bağımlılığı TEK
// dosyada topluyoruz — kiro/routes adaptörlerindeki desenin ui katmanı karşılığı.
//
// NEDEN `inline` PROP'U YOK: paylaşılan bileşen block modda <div>/<p> üretir;
// soru gövdesi zaten <p> içinde (AdaptifTestPage) → iç içe <p> = geçersiz HTML.
// Üstelik src/test/setup.ts console.error'ı susturduğu için React'in
// validateDOMNesting uyarısı sessizce yutulur, testler yeşil kalır. Bu yüzden
// inline BURADA zorlanır; çağıran yanlış kullanamaz.
// ============================================================================
import * as React from 'react';

import { MathText as PaylasilanMathText } from '@/components/ui/MathText';


export interface MathTextProps {
  /** Ham metin — LaTeX içerebilir de içermeyebilir de. */
  children: string;
}

/**
 * LaTeX-farkındalıklı metin. Formül yoksa düz metin gibi davranır (ek DOM yok).
 *
 * KaTeX'in kendi fontu (KaTeX_Main) EZİLMEZ: matematik glifleri (∫, √ uzantıları,
 * büyük parantezler) o fonta bağlıdır, `font-family: inherit` dayatmak sembolleri
 * bozar. Tipografi farkı kasıtlı olarak KaTeX'in optik ölçeğine bırakılmıştır.
 */
export const MathText: React.FC<MathTextProps> = ({ children }) => (
  <span className="k-math">
    <PaylasilanMathText inline>{children}</PaylasilanMathText>
  </span>
);

export default MathText;
