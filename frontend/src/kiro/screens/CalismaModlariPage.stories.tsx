import type { Meta, StoryObj } from '@storybook/react-vite';

import { CalismaModlariPage } from './CalismaModlariPage';

const meta = {
  title: 'Kiro/Ekran/CalismaModlari',
  component: CalismaModlariPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof CalismaModlariPage>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Varsayilan: Story = {};
