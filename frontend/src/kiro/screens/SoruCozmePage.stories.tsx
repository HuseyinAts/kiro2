import type { Meta, StoryObj } from '@storybook/react-vite';

import { SoruCozmePage } from './SoruCozmePage';

const meta = {
  title: 'Kiro/Ekran/Soru Çözme',
  component: SoruCozmePage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof SoruCozmePage>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Varsayilan: Story = {};
