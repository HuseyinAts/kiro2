import type { Meta, StoryObj } from '@storybook/react-vite';

import { SinifKurulumuPage } from './SinifKurulumuPage';

const meta = {
  title: 'Kiro/Ekran/SinifKurulumu',
  component: SinifKurulumuPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof SinifKurulumuPage>;

export default meta;
type Story = StoryObj<typeof meta>;

// Adım 1 · Bilgi (varsayılan giriş) — sınıf adı + düzey + alan.
export const Varsayilan: Story = {};

// Adım 2 · Davet — katılım kodu SUNUCUDAN (postSinif server-sim) + paylaş/yenile.
export const DavetAdimi: Story = {
  args: { baslangicAdim: 'davet' },
};

// Adım 3 · Hazır — sınıf kuruldu, panele/ödeve yönlendirme.
export const HazirAdimi: Story = {
  args: { baslangicAdim: 'hazir' },
};
