import type { Meta, StoryObj } from '@storybook/react-vite';

import { OdevlerimPage } from './OdevlerimPage';

const meta = {
  title: 'Kiro/Ekran/Ödevlerim',
  component: OdevlerimPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof OdevlerimPage>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Varsayilan: Story = {};
