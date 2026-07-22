import type { Meta, StoryObj } from '@storybook/react-vite';

import { OgretmenPaneliPage } from './OgretmenPaneliPage';

const meta = {
  title: 'Kiro/Ekran/OgretmenPaneli',
  component: OgretmenPaneliPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof OgretmenPaneliPage>;

export default meta;
type Story = StoryObj<typeof meta>;

// Varsayılan — 12-A Sayısal aktif (sunucu-otorite roster + KPI + dikkat).
export const Varsayilan: Story = {};
