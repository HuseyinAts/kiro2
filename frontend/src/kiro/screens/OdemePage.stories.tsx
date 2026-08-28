import type { Meta, StoryObj } from '@storybook/react-vite';

import type { ThreeDSDurum } from '../types';
import { OdemePage } from './OdemePage';

const meta = {
  title: 'Kiro/Ekran/Odeme',
  component: OdemePage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof OdemePage>;

export default meta;
type Story = StoryObj<typeof meta>;

// 3DS preview seam'leri — üretimde GEÇİLMEZ (varsayılan getOdeme3dsSonuc, sunucu-otorite).
// Never: çözülmeyen Promise → statik spinner (screenshot). Ret: banka-red dalı.
const NEVER = (): Promise<ThreeDSDurum> => new Promise<ThreeDSDurum>(() => undefined);
const RET = (): Promise<ThreeDSDurum> => Promise.resolve('reddedildi');

// FORM · Aylık — 2 sütun (kart formu + özet). Veli-bağlamı (SİZ).
export const Form: Story = {
  args: { baslangicFazi: 'form', fatura: 'aylik' },
};

// FORM · Yıllık — indirimli fatura özeti (₺924/yıl).
export const FormYillik: Story = {
  args: { baslangicFazi: 'form', fatura: 'yillik' },
};

// 3DS · bekleme — spinner (kiroSpin, RM-guard) + bespoke 3-adım stepper (statik).
export const ThreeDS: Story = {
  args: { baslangicFazi: '3ds', resolve3ds: NEVER },
};

// 3DS · banka-red → forma dön (amber decline; alarm-kırmızı YOK).
export const Reddedildi: Story = {
  args: { baslangicFazi: '3ds', resolve3ds: RET },
};

// TAMAM · deneme başladı → Plan Yönetimi CTA.
export const Tamam: Story = {
  args: { baslangicFazi: 'tamam' },
};
