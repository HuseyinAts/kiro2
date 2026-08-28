import type { Meta, StoryObj } from '@storybook/react-vite';

import { configureKiroApi } from '../api/api-client';
import type { MockData } from '../api/api-client';
import kiroData from '../api/kiro-data.json';
import type { AbonelikYonetim } from '../types';
import { PlanYonetimiPage } from './PlanYonetimiPage';

// Varyant matrisi: durum{aktif/deneme/iptal} × fatura{yıllık/aylık} × rol.
// Fiyat/durum/fatura SUNUCU-otoriter → mock'un abonelikYonetim'ini yamalayıp
// ekran mount'tan ÖNCE configureKiroApi ile kurarız (getAbonelikYonetim onu okur).
function mockWith(patch: Partial<AbonelikYonetim>): MockData {
  return {
    ...kiroData,
    abonelikYonetim: { ...kiroData.abonelikYonetim, ...patch },
  } as unknown as MockData;
}

const meta = {
  title: 'Kiro/Ekran/PlanYonetimi',
  component: PlanYonetimiPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof PlanYonetimiPage>;

export default meta;
type Story = StoryObj<typeof meta>;

// Veli · Deneme · Aylık (mock varsayılanı) — durum pili amber, ilk-ödeme satırı.
export const VeliDenemeAylik: Story = {
  render: () => {
    configureKiroApi({ mode: 'mock', mockData: mockWith({ durum: 'deneme', fatura: 'aylik' }) });
    return <PlanYonetimiPage rol="veli" />;
  },
};

// Veli · Aktif · Yıllık — durum pili yeşil, "Sonraki yenileme" + yıllık fiyat/indirim.
export const VeliAktifYillik: Story = {
  render: () => {
    configureKiroApi({ mode: 'mock', mockData: mockWith({ durum: 'aktif', fatura: 'yillik' }) });
    return <PlanYonetimiPage rol="veli" />;
  },
};

// Veli · İptal (deneme kökenli) — amber iptal bandı + "Geri aç"; iptal kartı gizli.
export const VeliIptal: Story = {
  render: () => {
    configureKiroApi({ mode: 'mock', mockData: mockWith({ durum: 'iptal', fatura: 'aylik' }) });
    return <PlanYonetimiPage rol="veli" />;
  },
};

// Veli · Fatura yok — kanonik soft-empty ("Henüz fatura yok — deneme sürüyor…").
export const VeliFaturaYok: Story = {
  render: () => {
    configureKiroApi({ mode: 'mock', mockData: mockWith({ durum: 'deneme', fatura: 'aylik', faturalar: [] }) });
    return <PlanYonetimiPage rol="veli" />;
  },
};

// ÖĞRENCİ — FİYAT GİZLİ (KVKK): plan/fiyat/iptal yerine VeliYonlendirmeKarti.
export const Ogrenci: Story = {
  render: () => {
    configureKiroApi({ mode: 'mock', mockData: kiroData as unknown as MockData });
    return <PlanYonetimiPage rol="ogrenci" />;
  },
};
