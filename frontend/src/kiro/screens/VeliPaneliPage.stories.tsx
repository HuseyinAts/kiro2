import type { Meta, StoryObj } from '@storybook/react-vite';

import { VeliPaneliPage } from './VeliPaneliPage';

const meta = {
  title: 'Kiro/Ekran/VeliPaneli',
  component: VeliPaneliPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof VeliPaneliPage>;

export default meta;
type Story = StoryObj<typeof meta>;

// Varsayılan — aktif çocuk (Hüseyin), salt-okur çalışma metrikleri.
export const Varsayilan: Story = {};

// İkinci çocuk (Elif) — ChildSwitcher tablist ile getVeliDashboard(cocukId) yeniden çekilir.
export const IkinciCocuk: Story = {
  play: async ({ canvasElement }) => {
    const tab = canvasElement.querySelector<HTMLButtonElement>('[role="tab"]:not([aria-selected="true"])');
    tab?.click();
  },
};
