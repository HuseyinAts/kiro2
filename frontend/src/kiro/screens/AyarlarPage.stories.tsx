import type { Meta, StoryObj } from '@storybook/react-vite';

import { AyarlarPage } from './AyarlarPage';

const meta = {
  title: 'Kiro/Ekran/Ayarlar',
  component: AyarlarPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof AyarlarPage>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Varsayilan: Story = {};
