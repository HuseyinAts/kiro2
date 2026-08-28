import type { Meta, StoryObj } from '@storybook/react-vite';

import { SokratikPage } from './SokratikPage';

const meta = {
  title: 'Kiro/Ekran/Sokratik',
  component: SokratikPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof SokratikPage>;

export default meta;
type Story = StoryObj<typeof meta>;

// Varsayılan — Sokratik açılış: topbar + "cevabı vermez" bildirimi + AI karşılama,
// sağ ray (üzerinde çalışılan soru + İpucu merdiveni + Sokratik ilerleme).
export const Varsayilan: Story = {};
