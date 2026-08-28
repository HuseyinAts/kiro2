import type { Meta, StoryObj } from '@storybook/react-vite';

import { CevrimdisiPage } from './CevrimdisiPage';

const meta = {
  title: 'Kiro/Ekran/Cevrimdisi',
  component: CevrimdisiPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof CevrimdisiPage>;

export default meta;
type Story = StoryObj<typeof meta>;

// Çevrimdışı — sakin amber bant, çalışman cihazında sürüyor.
export const Cevrimdisi: Story = {
  args: { durumBaslangic: 'cevrimdisi' },
};

// Yeniden bağlanıyor — dawn bant, eşitleme fazı.
export const YenidenBaglaniyor: Story = {
  args: { durumBaslangic: 'yeniden_baglaniyor' },
};

// Bağlandı — success bant, kuyruk boşaldı, hoş geldin başlığı.
export const Baglandi: Story = {
  args: { durumBaslangic: 'baglandi' },
};
