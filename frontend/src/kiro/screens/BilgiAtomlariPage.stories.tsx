import type { Meta, StoryObj } from '@storybook/react-vite';

import { BilgiAtomlariPage } from './BilgiAtomlariPage';

const meta = {
  title: 'Kiro/Ekran/BilgiAtomlari',
  component: BilgiAtomlariPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof BilgiAtomlariPage>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Varsayilan: Story = {};
