import type { Meta, StoryObj } from '@storybook/react-vite';

import type { HaftaGun } from '../types';
import { WeeklyActivityBars } from './WeeklyActivityBars';

// Haftalık aktivite — Veli / Öğretmen / Öğrenci-Özeti panellerinin paylaştığı çubuk seti.
const DOLU: HaftaGun[] = [
  { label: 'Pzt', dk: 45, aktif: true },
  { label: 'Sal', dk: 60, aktif: true },
  { label: 'Çar', dk: 30, aktif: true },
  { label: 'Per', dk: 75, aktif: true },
  { label: 'Cum', dk: 50, aktif: true },
  { label: 'Cmt', dk: 90, aktif: true },
  { label: 'Paz', dk: 40, aktif: true },
];

// Molalı hafta — çalışma olmayan günler pasif (şeftali) renkte.
const MOLALI: HaftaGun[] = [
  { label: 'Pzt', dk: 25, aktif: true },
  { label: 'Sal', dk: 0, aktif: false },
  { label: 'Çar', dk: 0, aktif: false },
  { label: 'Per', dk: 0, aktif: false },
  { label: 'Cum', dk: 40, aktif: true },
  { label: 'Cmt', dk: 0, aktif: false },
  { label: 'Paz', dk: 0, aktif: false },
];

const meta = {
  title: 'Kiro/WeeklyActivityBars',
  component: WeeklyActivityBars,
  args: { gunler: DOLU, ariaLabel: 'Haftalık aktivite' },
} satisfies Meta<typeof WeeklyActivityBars>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Dolu: Story = {};

export const BaslikliTrend: Story = {
  name: 'Başlıklı · toplam + trend',
  args: { toplamSa: 6.5, trend: '+1,1 sa' },
};

export const Molali: Story = {
  name: 'Molalı · pasif günler',
  args: { gunler: MOLALI, ariaLabel: 'Emre Şahin haftalık aktivite' },
};
