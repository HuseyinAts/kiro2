import type { Meta, StoryObj } from '@storybook/react-vite';

import { ArkadasSerisiPage } from './ArkadasSerisiPage';

const meta = {
  title: 'Kiro/Ekran/ArkadasSerisi',
  component: ArkadasSerisiPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof ArkadasSerisiPage>;

export default meta;
type Story = StoryObj<typeof meta>;

// Varsayılan — mock getMe + getFriends (kiro-data.json). Sıralama Seri (en uzun seri altın satır).
export const Varsayilan: Story = {};
