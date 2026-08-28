import type { Meta, StoryObj } from '@storybook/react-vite';

import { SonucPage } from './SonucPage';

const meta = {
  title: 'Kiro/Ekran/Sınav Sonuç',
  component: SonucPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof SonucPage>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Varsayilan: Story = {};
