import type { Meta, StoryObj } from '@storybook/react-vite';

import { configureKiroApi } from '../api/api-client';
import kiroData from '../api/kiro-data.json';

import { AdaptifTestPage } from './AdaptifTestPage';

const meta = {
  title: 'Kiro/Ekran/Adaptif Test',
  component: AdaptifTestPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof AdaptifTestPage>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Varsayilan: Story = {};

// ---------------------------------------------------------------------------
// Formüllü — üretim gerçeği. CAT-uygun MATEMATIK havuzunun %60.7'si LaTeX
// içeriyor; LaTeX'li şık satırlarının %97'si tam-dize "$...$" biçiminde.
// Dizeler question_bank'tan alındı (27 Tem 2026). String.raw kullanılır:
// tek ters bölü JS'te "\f"i FORM-FEED yapar ve KaTeX'e bozuk girdi gider.
// ---------------------------------------------------------------------------

const UZUN_FORMUL = String.raw`$\theta \in \left( \frac{\pi}{24}, \frac{\pi}{12} \right)$`;

/** Şıkların en uzunu kasten taşma sınırında — 390px'te yatay taşma kontrolü. */
const FORMULLU_BANK = [
  {
    b: -0.4,
    konu: 'Trigonometri',
    soru: `${UZUN_FORMUL} olmak üzere, ${String.raw`$a = \sin(6\theta)$`}, ${String.raw`$b = \tan(6\theta)$`} ve ${String.raw`$c = \cos(6\theta)$`} olduğuna göre, aşağıdaki sıralamalardan hangisi doğrudur?`,
    secenekler: [
      String.raw`$c < a < b$`,
      String.raw`$c < b < a$`,
      String.raw`$\frac{2}{7} < \sqrt{5} < \pi$`,
      UZUN_FORMUL,
    ],
    dogru: 0,
  },
  {
    b: 0.2,
    konu: 'Polinomlar',
    soru: String.raw`$P(x) = x^3 + 3x^2 - 10$ polinomunun $x+2$ ile bölümünden kalan kaçtır?`,
    secenekler: [String.raw`$-6$`, String.raw`$\frac{26}{33}$`, String.raw`$\sqrt[3]{8}$`, '14'],
    dogru: 0,
  },
];

export const Formullu: Story = {
  decorators: [
    (Story) => {
      const veri = structuredClone(kiroData) as unknown as { catBankMat: unknown[] };
      veri.catBankMat = FORMULLU_BANK;
      configureKiroApi({ mode: 'mock', mockData: veri as never });
      return <Story />;
    },
  ],
};
