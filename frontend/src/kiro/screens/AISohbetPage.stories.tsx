import type { Meta, StoryObj } from '@storybook/react-vite';

import { AISohbetPage } from './AISohbetPage';

const meta = {
  title: 'Kiro/Ekran/AI Sohbet',
  component: AISohbetPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof AISohbetPage>;

export default meta;
type Story = StoryObj<typeof meta>;

// Açılış: sunucu-otoriter AI karşılama mesajı (boş sohbet) + composer.
// Gönderince yanıt streamSohbet'ten token token akar (istemci cevap uydurmaz).
export const Varsayilan: Story = {};
