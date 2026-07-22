import type { Meta, StoryObj } from '@storybook/react-vite';

import { HaftalikPlanPage } from './HaftalikPlanPage';

const meta = {
  title: 'Kiro/Ekran/HaftalikPlan',
  component: HaftalikPlanPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof HaftalikPlanPage>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Varsayilan: Story = {};
