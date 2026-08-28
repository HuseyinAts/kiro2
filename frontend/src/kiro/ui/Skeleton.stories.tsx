import type { Meta, StoryObj } from '@storybook/react-vite';

import { Skeleton } from './Skeleton';

const meta = {
  title: 'Kiro/Skeleton',
  component: Skeleton,
  // delayMs=0: Storybook'ta iskeleti anında göster (gerçek gecikme davranışı Gecikmeli story'de)
  args: { shape: 'bar', delayMs: 0 },
  argTypes: {
    shape: { control: 'inline-radio', options: ['bar', 'row', 'card'] },
    width: { control: 'text' },
    height: { control: { type: 'number' } },
    delayMs: { control: { type: 'number' } },
    sweep: { control: 'boolean' },
    slowAfterMs: { control: { type: 'number' } },
  },
} satisfies Meta<typeof Skeleton>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Bar: Story = {};

export const Row: Story = { args: { shape: 'row' } };

export const Card: Story = {
  name: 'Card · şafak süpürmesi',
  args: { shape: 'card', sweep: true },
};

export const SupurmesizKart: Story = {
  name: 'Card · süpürme kapalı',
  args: { shape: 'card', sweep: false, slowAfterMs: null },
};

// slowAfterMs=50: 3sn güvence satırı + gün mantrası davranışını anında sahnele
export const YavasMantra: Story = {
  name: 'Card · güvence satırı + gün mantrası',
  args: { shape: 'card', slowAfterMs: 50 },
};

export const Gecikmeli: Story = {
  name: '400ms altı yüklemede görünmez',
  args: { delayMs: 400 },
};

// dusk yalnız koyu yüzeyde → story dusk temaya sabitlenir
export const DuskKart: Story = {
  name: 'Card · dusk yüzey',
  args: { shape: 'card' },
  globals: { kiroTheme: 'dusk' },
};
