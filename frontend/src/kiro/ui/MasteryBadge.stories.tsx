import type { Meta, StoryObj } from '@storybook/react-vite';

import { MasteryBadge } from './MasteryBadge';

const meta = {
  title: 'Kiro/MasteryBadge',
  component: MasteryBadge,
  args: { pct: 72, trend: 'up', size: 'md' },
  argTypes: {
    tier: { control: 'inline-radio', options: ['tanidik', 'yetkin', 'usta', 'fethedildi'] },
    trend: { control: 'inline-radio', options: ['up', 'stable', 'down'] },
    size: { control: 'inline-radio', options: ['md', 'lg'] },
    pct: { control: { type: 'range', min: 0, max: 100 } },
  },
} satisfies Meta<typeof MasteryBadge>;

export default meta;
type Story = StoryObj<typeof meta>;

// Kademe hikâyeleri (paper) — eşik kanonu: Tanıdık<40 · Yetkin<65 · Usta<85 · Fethedildi≥85
export const Tanidik: Story = { args: { tier: 'tanidik', pct: 28, trend: 'stable' } };
export const Yetkin: Story = { args: { tier: 'yetkin', pct: 52 } };
export const Usta: Story = { args: { tier: 'usta', pct: 72 } };
export const Fethedildi: Story = { args: { tier: 'fethedildi', pct: 92 } };

// Yön: up = başarılı getirim · down = FSRS yarı-ömrü doluyor (sıcak amber) · stable = sabit
export const YonYukari: Story = { name: 'Yön · yükseliyor', args: { trend: 'up' } };
export const YonSabit: Story = { name: 'Yön · sabit', args: { trend: 'stable' } };
export const YonGeriliyor: Story = { name: 'Yön · geriliyor', args: { trend: 'down', pct: 58, tier: 'yetkin' } };

// Boyut: lg canlı vurgular için
export const Buyuk: Story = { name: 'lg · canlı vurgu', args: { size: 'lg', tier: 'fethedildi', pct: 88 } };

// tier verilmez → tierFromPct ile yüzdeden türetilir
export const PcttenTuretilen: Story = { name: 'pct → tier (türetilen)', args: { pct: 66, trend: 'up' } };

// Koyu yüzey: dusk paletinde parlak kademe renkleri
export const DuskYuzey: Story = {
  name: 'dusk yüzey',
  args: { tier: 'usta', pct: 78, trend: 'up' },
  globals: { kiroTheme: 'dusk' },
};
