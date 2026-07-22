import type { Meta, StoryObj } from '@storybook/react-vite';

import { OnboardingPage } from './OnboardingPage';

const meta = {
  title: 'Kiro/Ekran/Onboarding',
  component: OnboardingPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof OnboardingPage>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Varsayilan: Story = {};
