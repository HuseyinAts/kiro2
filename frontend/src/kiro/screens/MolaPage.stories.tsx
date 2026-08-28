import type { Meta, StoryObj } from '@storybook/react-vite';

import { MolaPage } from './MolaPage';

const meta = {
  title: 'Kiro/Ekran/Mola',
  component: MolaPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof MolaPage>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Varsayilan: Story = {};
