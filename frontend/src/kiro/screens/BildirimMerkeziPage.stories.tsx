import type { Meta, StoryObj } from '@storybook/react-vite';

import { BildirimMerkeziPage } from './BildirimMerkeziPage';

const meta = {
  title: 'Kiro/Ekran/Bildirim Merkezi',
  component: BildirimMerkeziPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof BildirimMerkeziPage>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Varsayilan: Story = {};
