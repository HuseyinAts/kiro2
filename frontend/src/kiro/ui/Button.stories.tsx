import type { Meta, StoryObj } from '@storybook/react-vite';

import { Button } from './Button';

// Bespoke inline SVG (kanon: lucide/emoji YOK; stroke 2.1 round-cap)
const IconX = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" aria-hidden>
    <path d="M6 6l12 12M18 6L6 18" />
  </svg>
);

const meta = {
  title: 'Kiro/Button',
  component: Button,
  args: { children: 'Devam et', variant: 'primary', size: 'md' },
  argTypes: {
    variant: { control: 'inline-radio', options: ['primary', 'ghost', 'goldDark'] },
    size: { control: 'inline-radio', options: ['md', 'lg'] },
    disabled: { control: 'boolean' },
  },
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {};
export const Ghost: Story = { args: { variant: 'ghost' } };
export const Large: Story = { args: { size: 'lg', children: 'XP kazan' } };
export const Disabled: Story = { args: { disabled: true } };

export const IkonYalniz: Story = {
  name: 'İkon-yalnız (aria-label zorunlu)',
  args: { variant: 'ghost', children: undefined, icon: <IconX />, ariaLabel: 'Kapat' },
};

// goldDark yalnız KOYU yüzeyde kullanılır → story dusk temaya sabitlenir
export const GoldDarkDusk: Story = {
  name: 'goldDark · yalnız dusk',
  args: { variant: 'goldDark', children: 'Kutlamayı gör' },
  globals: { kiroTheme: 'dusk' },
};
