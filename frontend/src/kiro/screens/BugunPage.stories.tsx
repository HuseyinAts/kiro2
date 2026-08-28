import type { Meta, StoryObj } from '@storybook/react-vite';

import { BugunPage } from './BugunPage';

const meta = {
  title: 'Kiro/Ekran/Bugun',
  component: BugunPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof BugunPage>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Varsayilan: Story = {};
