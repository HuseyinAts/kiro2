import type { Meta, StoryObj } from '@storybook/react-vite';

import { Chip } from './Chip';

// Bespoke inline SVG (kanon: lucide/emoji YOK; stroke 2.1 round-cap)
const IconFlame = () => (
  <svg
    width="14"
    height="14"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2.1"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden
  >
    <path d="M12 3c.7 2.4 3.5 3.6 3.5 6.8a3.5 3.5 0 0 1-7 0c0-1.4.6-2.4 1.4-3.2.2 1.3 1.1 1.8 2.1 1.2-1-1.6-.6-3.6 0-4.8z" />
  </svg>
);

const IconTag = () => (
  <svg
    width="13"
    height="13"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2.1"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden
  >
    <path d="M4 4h7l9 9-7 7-9-9V4z" />
    <path d="M8 8h.01" />
  </svg>
);

const meta = {
  title: 'Kiro/Chip',
  component: Chip,
  args: { kind: 'status', label: 'Sözcük anlamı' },
  argTypes: {
    kind: { control: 'inline-radio', options: ['streak', 'tag', 'status'] },
    tone: { control: 'inline-radio', options: ['tyt', 'ayt'] },
    label: { control: 'text' },
  },
} satisfies Meta<typeof Chip>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Status: Story = {};

export const StatusIkonlu: Story = {
  name: 'Durum · ikonlu',
  args: { icon: <IconTag /> },
};

// Seri çipi: sayı → tabular-nums (numText)
export const Streak: Story = {
  name: 'Seri · alev + sayı',
  args: { kind: 'streak', label: 7, icon: <IconFlame /> },
};

export const TagTyt: Story = {
  name: 'Etiket · TYT',
  args: { kind: 'tag', tone: 'tyt', label: 'TYT' },
};

export const TagAyt: Story = {
  name: 'Etiket · AYT',
  args: { kind: 'tag', tone: 'ayt', label: 'AYT' },
};

// status kind surf(theme) okur → dusk yüzeyde ayrı görünür
export const StatusDusk: Story = {
  name: 'Durum · dusk yüzey',
  args: { kind: 'status', label: 'Gece modu', icon: <IconTag /> },
  globals: { kiroTheme: 'dusk' },
};
