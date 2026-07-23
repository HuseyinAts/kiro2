import type { Meta, StoryObj } from '@storybook/react-vite';

import { Switch } from './Switch';

const meta = {
  title: 'Kiro/Switch',
  component: Switch,
  args: {
    checked: true,
    ariaLabel: 'Bildirimleri aç',
    onChange: () => {},
  },
  argTypes: {
    checked: { control: 'boolean' },
    disabled: { control: 'boolean' },
    label: { control: 'text' },
  },
} satisfies Meta<typeof Switch>;

export default meta;
type Story = StoryObj<typeof meta>;

// Açık — coralCtaBg dolgu, thumb sağda
export const On: Story = {};

// Kapalı — nötr kâğıt grisi, thumb solda
export const Off: Story = {
  args: { checked: false, ariaLabel: 'Bildirimleri aç' },
};

// Devre dışı — opacity düşük, klavye/tık no-op
export const Disabled: Story = {
  args: { checked: false, disabled: true, ariaLabel: 'Bildirimler (kilitli)' },
};

// Görünür etiketli satır — erişilebilir ad içerikten türetilir
export const WithLabel: Story = {
  name: 'Etiketli · FSRS hatırlatması',
  args: { checked: true, label: 'FSRS hatırlatması', ariaLabel: undefined },
};
