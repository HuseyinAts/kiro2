import type { Meta, StoryObj } from '@storybook/react-vite';

import { OgrenmeYoluPage } from './OgrenmeYoluPage';

const meta = {
  title: 'Kiro/Ekran/OgrenmeYolu',
  component: OgrenmeYoluPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof OgrenmeYoluPage>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Varsayilan: Story = {};
