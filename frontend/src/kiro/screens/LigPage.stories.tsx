import type { Meta, StoryObj } from '@storybook/react-vite';

import { LigPage } from './LigPage';

const meta = {
  title: 'Kiro/Ekran/Lig',
  component: LigPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof LigPage>;

export default meta;
type Story = StoryObj<typeof meta>;

// Varsayılan — sakin mod AÇIK, sıralama görünür (kaygı-duyarlı kanon).
export const Varsayilan: Story = {};

// Yarışmacı çerçeve — sakin mod KAPALI: amber geri-sayım + sıralama-odaklı dil.
export const Yarismaci: Story = {
  args: { sakinMod: false },
};

// Sıralama gizli — odak-modu; standings gizlenir, XP/seri/emek işlemeye devam eder.
export const SiralamaGizli: Story = {
  args: { siralamaGizli: true },
};

// Seviye atladı — sağ rayda Kutlama CTA'sı (sunucu sinyali geldiğinde).
export const SeviyeAtladi: Story = {
  args: { leveledUp: true },
};
