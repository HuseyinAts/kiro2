import type { Meta, StoryObj } from '@storybook/react-vite';

import { IconBadge } from './IconBadge';

// Bespoke inline SVG (kanon: lucide/emoji YOK; stroke 2.1 round cap/join)
const IconSpark = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <path d="M12 3l2 6 6 2-6 2-2 6-2-6-6-2 6-2z" />
  </svg>
);

const IconCheck = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <path d="M5 13l4 4L19 7" />
  </svg>
);

const IconAlert = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 8v5M12 16h.01" />
  </svg>
);

const IconRing = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <circle cx="12" cy="12" r="8" />
  </svg>
);

const meta = {
  title: 'Kiro/IconBadge',
  component: IconBadge,
  args: { icon: <IconSpark />, tone: 'dawn', size: 40 },
  argTypes: {
    tone: { control: 'inline-radio', options: ['dawn', 'success', 'attention', 'neutral'] },
    size: { control: { type: 'number' } },
    radiusPx: { control: { type: 'number' } },
  },
} satisfies Meta<typeof IconBadge>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Dawn: Story = {};
export const Success: Story = { args: { tone: 'success', icon: <IconCheck /> } };

// Risk = amber (alarm-kırmızısı YOK) — kanon
export const Attention: Story = {
  name: 'Attention · amber',
  args: { tone: 'attention', icon: <IconAlert /> },
};

export const Neutral: Story = { args: { tone: 'neutral', icon: <IconRing /> } };
export const Buyuk: Story = { name: 'Büyük · 56px', args: { size: 56 } };
export const Kucuk: Story = { name: 'Küçük · 32px', args: { size: 32 } };
export const KareYaricap: Story = { name: 'Kare-yakın · radiusPx 8', args: { radiusPx: 8 } };
