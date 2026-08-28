import type { Meta, StoryObj } from '@storybook/react-vite';

import { HesapKurtarmaPage } from './HesapKurtarmaPage';

const meta = {
  title: 'Kiro/Ekran/Hesap Kurtarma',
  component: HesapKurtarmaPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof HesapKurtarmaPage>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Varsayilan: Story = {};
