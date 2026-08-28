import type { Meta, StoryObj } from '@storybook/react-vite';

import { VeliBaglamaPage } from './VeliBaglamaPage';

const meta = {
  title: 'Kiro/Ekran/VeliBaglama',
  component: VeliBaglamaPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof VeliBaglamaPage>;

export default meta;
type Story = StoryObj<typeof meta>;

// VELİ · Adım 1 (kod) — resmi SİZ, 6-hane bağlantı kodu (varsayılan giriş).
export const Veli: Story = {
  args: { taraf: 'veli' },
};

// VELİ · Adım 2 (rıza) — iki-yönlü kapsam + KVKK açık-rıza çekbox.
export const VeliRiza: Story = {
  args: { taraf: 'veli', baslangicAdim: 'riza' },
};

// VELİ · Adım 3 (bekle) — çocuk onayı beklenirken (sarı saat).
export const VeliBekle: Story = {
  args: { taraf: 'veli', baslangicAdim: 'bekle' },
};

// VELİ · Adım 4 (tamam) — bağlantı kuruldu, veli paneline geçiş.
export const VeliTamam: Story = {
  args: { taraf: 'veli', baslangicAdim: 'tamam' },
};

// ÖĞRENCİ · onay ekranı — akran SEN, bekleyen veli isteği + sınır kapsamı.
export const Ogrenci: Story = {
  args: { taraf: 'ogrenci' },
};
