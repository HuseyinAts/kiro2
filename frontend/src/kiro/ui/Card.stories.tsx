import type { Meta, StoryObj } from '@storybook/react-vite';

import { Card } from './Card';

const Demo = ({ label }: { label: string }) => (
  <div style={{ minWidth: 220 }}>
    <div style={{ fontWeight: 800, fontSize: 15 }}>{label}</div>
    <div style={{ marginTop: 6, fontSize: 13, opacity: 0.72 }}>Kart gövde metni · sakin kâğıt yüzey.</div>
  </div>
);

const meta = {
  title: 'Kiro/Card',
  component: Card,
  args: { children: <Demo label="Kart başlığı" /> },
  argTypes: {
    variant: { control: 'inline-radio', options: ['solid', 'dashed', 'dusk'] },
    radiusSize: { control: 'inline-radio', options: ['card', 'lg'] },
    padding: { control: { type: 'number' } },
  },
} satisfies Meta<typeof Card>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Solid: Story = {};
export const BosDashed: Story = {
  name: 'Dashed · boş/yönlendiren yüzey',
  args: { variant: 'dashed', children: <Demo label="Henüz içerik yok" /> },
};
export const BuyukYaricap: Story = { args: { radiusSize: 'lg' } };
export const DuskYuzey: Story = {
  name: 'dusk yüzey',
  args: { variant: 'dusk', children: <Demo label="Koyu kart" /> },
  globals: { kiroTheme: 'dusk' },
};
