import type { Meta, StoryObj } from '@storybook/react-vite';

import { StatBlock } from './StatBlock';

const meta = {
  title: 'Kiro/StatBlock',
  component: StatBlock,
  args: { value: 1284, label: 'Çözülen soru' },
  argTypes: {
    value: { control: 'text' },
    label: { control: 'text' },
    delta: { control: 'text' },
    tone: { control: 'color' },
  },
} satisfies Meta<typeof StatBlock>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Varsayilan: Story = {};

export const ArtiDelta: Story = {
  name: 'Delta · artış (+)',
  args: { value: 1284, label: 'Çözülen soru', delta: '+48' },
};

export const NegatifDelta: Story = {
  name: 'Delta · düşüş (-)',
  args: { value: 12, label: 'Bekleyen tekrar', delta: '-6' },
};

export const TonVurgu: Story = {
  name: 'Ton · vurgulu değer (amber)',
  args: { value: '%92', label: 'Başarı oranı', tone: '#9A5D0D' },
};

export const BuyukSayi: Story = {
  name: 'Büyük tabular sayı',
  args: { value: '12.480', label: 'Toplam XP', delta: '+320' },
};

export const DuskYuzey: Story = {
  name: 'dusk yüzey',
  args: { value: 7, label: 'Seri gün', delta: '+1' },
  globals: { kiroTheme: 'dusk' },
};
