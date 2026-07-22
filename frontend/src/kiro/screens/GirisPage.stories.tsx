import type { Meta, StoryObj } from '@storybook/react-vite';

import { GirisPage } from './GirisPage';

const meta = {
  title: 'Kiro/Ekran/Giriş',
  component: GirisPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof GirisPage>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Varsayilan: Story = {};
