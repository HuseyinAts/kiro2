import type { Meta, StoryObj } from '@storybook/react-vite';

import { NedenPage } from './NedenPage';

const meta = {
  title: 'Kiro/Ekran/Neden Geri Bildirim',
  component: NedenPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof NedenPage>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Yanlis: Story = { args: { senaryo: 'yanlis' } };
export const Dogru: Story = { args: { senaryo: 'dogru' } };
