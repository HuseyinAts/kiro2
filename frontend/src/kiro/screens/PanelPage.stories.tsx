import type { Meta, StoryObj } from '@storybook/react-vite';

import { PanelPage } from './PanelPage';

const meta = {
  title: 'Kiro/Ekran/Panel',
  component: PanelPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof PanelPage>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Varsayilan: Story = {};
