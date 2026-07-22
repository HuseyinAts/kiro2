import type { Meta, StoryObj } from '@storybook/react-vite';

import { ProgressBar } from './ProgressBar';

// Ders renkleri (tokens.color.subject) — canon-guvenli hex, acik panelde doygun palet
const MAT = '#3B82F6'; // Matematik
const BIY = '#1FB683'; // Biyoloji
const TUR = '#F59E0B'; // Turkce (amber)
const FIZ_DUSK = '#A77BFF'; // Koyu zeminde parlak Fizik moru

const meta = {
  title: 'Kiro/ProgressBar',
  component: ProgressBar,
  args: { pct: 45, color: MAT, height: 8, ariaLabel: 'Matematik ilerlemesi' },
  argTypes: {
    pct: { control: { type: 'range', min: 0, max: 100, step: 1 } },
    color: { control: 'color' },
    height: { control: { type: 'number', min: 6, max: 9 } },
  },
} satisfies Meta<typeof ProgressBar>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Orta: Story = {};
export const Baslangic: Story = { name: 'Baslangic · %0', args: { pct: 0 } };
export const Tamamlandi: Story = { name: 'Tamamlandi · %100', args: { pct: 100, color: BIY } };
export const Ince: Story = { name: 'Ince · 6px', args: { height: 6, color: TUR } };

// Koyu (dusk) yuzey: iz rengi dusk skeleton'a doner, o yuzden story dusk temaya sabitlenir
export const DuskYuzey: Story = {
  name: 'dusk yuzey · Fizik',
  args: { pct: 68, color: FIZ_DUSK },
  globals: { kiroTheme: 'dusk' },
};
