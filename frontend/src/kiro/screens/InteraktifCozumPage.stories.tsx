import type { Meta, StoryObj } from '@storybook/react-vite';

import { InteraktifCozumPage } from './InteraktifCozumPage';

const meta = {
  title: 'Kiro/Ekran/İnteraktif Çözüm',
  component: InteraktifCozumPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof InteraktifCozumPage>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Sayfa: Story = {};
