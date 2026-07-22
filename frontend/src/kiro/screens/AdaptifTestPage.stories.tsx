import type { Meta, StoryObj } from '@storybook/react-vite';

import { AdaptifTestPage } from './AdaptifTestPage';

const meta = {
  title: 'Kiro/Ekran/Adaptif Test',
  component: AdaptifTestPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof AdaptifTestPage>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Varsayilan: Story = {};
