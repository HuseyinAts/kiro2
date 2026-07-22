import type { Meta, StoryObj } from '@storybook/react-vite';

import { OgrenciOzetiPage } from './OgrenciOzetiPage';

const meta = {
  title: 'Kiro/Ekran/OgrenciOzeti',
  component: OgrenciOzetiPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof OgrenciOzetiPage>;

export default meta;
type Story = StoryObj<typeof meta>;

// Varsayılan — sağlıklı ritim (durum: saglikli).
export const Varsayilan: Story = {
  args: { ogrenciId: 'o-ha' },
};

// Dikkat — amber risk şeridi (durum: dikkat; riskMetni sunucudan).
export const Dikkat: Story = {
  args: { ogrenciId: 'emre-sahin' },
};
