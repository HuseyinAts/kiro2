import type { Meta, StoryObj } from '@storybook/react-vite';

import { GeriSayimPage } from './GeriSayimPage';

const meta = {
  title: 'Kiro/Ekran/GeriSayim',
  component: GeriSayimPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof GeriSayimPage>;

export default meta;
type Story = StoryObj<typeof meta>;

// Varsayılan = B (kaygı-nötr) — kaygı-duyarlı kanon.
export const Varsayilan: Story = {};

// A varyant (geri sayım) — Ayarlar'dan açılabilir (S8 PostHog A/B).
export const GeriSayimVaryant: Story = {
  args: { varyant: 'geri-sayim' },
};
