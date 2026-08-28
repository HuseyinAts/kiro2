import type { Meta, StoryObj } from '@storybook/react-vite';

import { ChatBubble } from './ChatBubble';

const meta = {
  title: 'Kiro/ChatBubble',
  component: ChatBubble,
  args: {
    role: 'ai',
    children: 'Bu soruda ilk hangi bilgiyi fark ettin? Birlikte oradan ilerleyelim.',
  },
  argTypes: {
    role: { control: 'inline-radio', options: ['ai', 'me'] },
    tag: { control: 'text' },
    pending: { control: 'boolean' },
  },
} satisfies Meta<typeof ChatBubble>;

export default meta;
type Story = StoryObj<typeof meta>;

// AI koç: gradyan avatar + beyaz sol balon (Sokratik ton — cevabı vermez, birlikte düşünür)
export const AiKoc: Story = { name: 'AI koç · sol balon' };

// Kullanıcı: coral balon, sağa yaslı
export const Kullanici: Story = {
  name: 'Kullanıcı · sağ balon',
  args: { role: 'me', children: 'Sanırım önce paydaları eşitlemem gerekiyor.' },
};

// AI + ipucu etiketi (İpucu N / M)
export const AiIpucuEtiketi: Story = {
  name: 'AI · ipucu etiketi',
  args: { tag: 'İpucu 2 / 4' },
};

// AI düşünüyor: soluk (pending) balon
export const AiDusunuyor: Story = {
  name: 'AI · düşünüyor (pending)',
  args: { pending: true, children: 'Düşünüyorum…' },
};
