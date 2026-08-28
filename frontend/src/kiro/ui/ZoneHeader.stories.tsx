import type { Meta, StoryObj } from '@storybook/react-vite';

import { ZoneHeader } from './ZoneHeader';

// Bespoke inline SVG (kanon: lucide/emoji YOK; stroke 2.1 round-cap)
const IconArrowUp = () => (
  <svg
    width="15"
    height="15"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2.1"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden
  >
    <path d="M12 19V5M6 11l6-6 6 6" />
  </svg>
);

const meta = {
  title: 'Kiro/ZoneHeader',
  component: ZoneHeader,
  args: { label: 'Bugünkü akış', tone: 'safe' },
  argTypes: {
    tone: { control: 'inline-radio', options: ['promote', 'safe', 'demote'] },
    label: { control: 'text' },
  },
} satisfies Meta<typeof ZoneHeader>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Safe: Story = {};
export const Promote: Story = { args: { tone: 'promote', label: 'Yükselen konular' } };

// demote tonu AMBER'dir (alarm-kırmızısı DEĞİL — Lig §22g)
export const Demote: Story = {
  name: 'Demote · sakin amber',
  args: { tone: 'demote', label: 'Tekrar bekleyen' },
};

export const IkonluBaslik: Story = {
  name: 'İkonlu başlık',
  args: { tone: 'promote', label: 'Yükselen konular', icon: <IconArrowUp /> },
};

// dusk = duygusal/hub yüzey → story koyu temaya sabitlenir
export const DuskYuzey: Story = {
  name: 'dusk yüzey',
  args: { label: 'Bu haftaki ritüel', tone: 'promote' },
  globals: { kiroTheme: 'dusk' },
};
