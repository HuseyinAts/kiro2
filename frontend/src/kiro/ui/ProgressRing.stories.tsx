import type { Meta, StoryObj } from '@storybook/react-vite';

import { ProgressRing } from './ProgressRing';

const meta = {
  title: 'Kiro/ProgressRing',
  component: ProgressRing,
  args: { pct: 72 },
  argTypes: {
    pct: { control: { type: 'range', min: 0, max: 100, step: 1 } },
    size: { control: { type: 'number' } },
    strokeWidth: { control: { type: 'number' } },
    ringColor: { control: 'color' },
    label: { control: 'text' },
    sublabel: { control: 'text' },
  },
} satisfies Meta<typeof ProgressRing>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Varsayilan: Story = {};

// pct alt sınır: başlangıç/boş yüzey (kanon: pozitif dil, absence-dili yok)
export const Baslangic: Story = {
  name: 'Başlangıç · %0',
  args: { pct: 0, sublabel: 'Başlıyor' },
};

export const Tamamlandi: Story = {
  name: 'Tamamlandı · %100',
  args: { pct: 100, sublabel: 'Konu bitti' },
};

export const EtiketVeAltEtiket: Story = {
  args: { pct: 64, label: 'Orta', sublabel: 'Matematik' },
};

export const Buyuk: Story = {
  args: { pct: 48, size: 148, strokeWidth: 12, sublabel: '12 soru' },
};

// Risk = amber halka (kanon: alarm-kırmızısı YASAK)
export const RiskAmber: Story = {
  name: 'Risk · amber halka',
  args: { pct: 28, ringColor: '#C77A1E', sublabel: 'Zayıf konu' },
};

// dusk yalnız koyu yüzeyde → story dusk temaya sabitlenir
export const DuskYuzey: Story = {
  name: 'dusk yüzey',
  args: { pct: 82, sublabel: 'Bu hafta' },
  globals: { kiroTheme: 'dusk' },
};
