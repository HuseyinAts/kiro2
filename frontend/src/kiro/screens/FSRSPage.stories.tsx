import type { Meta, StoryObj } from '@storybook/react-vite';

import { FSRSPage } from './FSRSPage';

const meta = {
  title: 'Kiro/Ekran/FSRS Tekrar',
  component: FSRSPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof FSRSPage>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Sayfa: Story = {};
export const Oturum: Story = { args: { demoOverlay: true } };
