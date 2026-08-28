import type { Meta, StoryObj } from '@storybook/react-vite';

import { AbonelikPage } from './AbonelikPage';

const meta = {
  title: 'Kiro/Ekran/Abonelik',
  component: AbonelikPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof AbonelikPage>;

export default meta;
type Story = StoryObj<typeof meta>;

/** Veli — fiyat GÖRÜNÜR (plan ızgarası + kanıt şeridi + fatura toggle). */
export const Veli: Story = { args: { rol: 'veli' } };

/** Veli — aylık fatura varsayılanı (₺124/ay). */
export const VeliAylik: Story = { args: { rol: 'veli', varsayilanFatura: 'aylik' } };

/** Öğrenci — fiyat/plan GİZLİ (KVKK) → VeliYonlendirmeKarti. */
export const Ogrenci: Story = { args: { rol: 'ogrenci' } };
