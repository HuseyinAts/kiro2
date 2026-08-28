import type { Meta, StoryObj } from '@storybook/react-vite';

import { Callout } from './Callout';

// Bespoke inline SVG (kanon: lucide/emoji YOK; stroke 2.1 round-cap)
const IconInfo = () => (
  <svg
    width="17"
    height="17"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2.1"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden
  >
    <circle cx="12" cy="12" r="9" />
    <path d="M12 11.5v4.5" />
    <path d="M12 7.75h.01" />
  </svg>
);

const meta = {
  title: 'Kiro/Callout',
  component: Callout,
  args: { children: 'Bugünkü tekrarların seni bekliyor.', tone: 'dawn' },
  argTypes: {
    tone: { control: 'inline-radio', options: ['success', 'attention', 'dawn'] },
  },
} satisfies Meta<typeof Callout>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Dawn: Story = {};

export const Success: Story = {
  name: 'success · tamamlandı',
  args: { tone: 'success', children: 'Tüm konular tamamlandı, tebrikler.' },
};

// attention tonu amber'dir — alarm-kırmızısı ASLA
export const Attention: Story = {
  name: 'attention · amber (risk = amber)',
  args: { tone: 'attention', children: 'Sınavına üç gün kaldı, planını gözden geçir.' },
};

export const Ikonlu: Story = {
  name: 'İkonlu (bespoke svg)',
  args: { icon: <IconInfo />, children: 'İpucu: her gün kısa tekrar, uzun aradan iyidir.' },
};

// dawn = duygusal yüzey → dusk ekran temasında sunulur
export const DawnDusk: Story = {
  name: 'dawn · dusk yüzey',
  args: { tone: 'dawn', children: 'Bugün atacağın küçük adım, seni hedefine yaklaştırır.' },
  globals: { kiroTheme: 'dusk' },
};
