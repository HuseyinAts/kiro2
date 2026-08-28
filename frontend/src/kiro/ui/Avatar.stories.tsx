import type { Meta, StoryObj } from '@storybook/react-vite';

import { Avatar, AVATAR_PAL } from './Avatar';

// Tüm-palet showcase için baş harf etiketleri (11 renk ile birebir)
const PALET_ADLARI = ['AK', 'BÇ', 'CD', 'EF', 'GH', 'İZ', 'KL', 'MN', 'OP', 'RS', 'TU'];

const meta = {
  title: 'Kiro/Avatar',
  component: Avatar,
  args: { initials: 'AK', size: 40, bg: AVATAR_PAL[0] },
  argTypes: {
    initials: { control: 'text' },
    size: { control: { type: 'number', min: 24, max: 70, step: 2 } },
    bg: { control: 'color' },
    ring: { control: 'color' },
  },
} satisfies Meta<typeof Avatar>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Varsayilan: Story = {};

export const Kucuk: Story = { name: 'Küçük · 24', args: { size: 24 } };

export const Buyuk: Story = { name: 'Büyük · 70', args: { size: 70 } };

// Podyum vurgusu: altın (amber) halka — kutlama/lig bağlamı
export const PodyumRing: Story = {
  name: 'Podyum · altın halka',
  args: { size: 70, bg: AVATAR_PAL[1], ring: AVATAR_PAL[5] },
};

// bg palet varyasyonu — AVATAR_PAL export'unun tümü
export const TumPalet: Story = {
  name: 'Tüm palet',
  render: () => (
    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', maxWidth: 360 }}>
      {AVATAR_PAL.map((renk, i) => (
        <Avatar key={renk} initials={PALET_ADLARI[i] ?? 'AK'} bg={renk} />
      ))}
    </div>
  ),
};

// Koyu (dusk) yüzeyde podyum ringli avatar
export const PodyumDusk: Story = {
  name: 'Podyum · dusk yüzey',
  args: { size: 70, bg: AVATAR_PAL[3], ring: AVATAR_PAL[5] },
  globals: { kiroTheme: 'dusk' },
};
