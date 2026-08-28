import type { Meta, StoryObj } from '@storybook/react-vite';

import { BossSavasiPage } from './BossSavasiPage';

const meta = {
  title: 'Kiro/Ekran/BossSavasi',
  component: BossSavasiPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof BossSavasiPage>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Varsayilan: Story = {};
