import type { Meta, StoryObj } from '@storybook/react-vite';

import { HarmanPage } from './HarmanPage';

const meta = {
  title: 'Kiro/Ekran/Harmanlanmış Deneme',
  component: HarmanPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof HarmanPage>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Varsayilan: Story = {};
