import type { Meta, StoryObj, Decorator } from '@storybook/react-vite';

import { KutlamaPage } from './KutlamaPage';

// KutlamaPage türü URL paramından okur (mount'ta tek okuma). Story türü seçmek için
// dekoratör, story render'ından ÖNCE senkron olarak location'ı ayarlar.
const urlTuru = (type?: string): Decorator => (Story) => {
  if (typeof window !== 'undefined') {
    window.history.replaceState({}, '', type ? `/kutlama?type=${type}` : '/kutlama');
  }
  return <Story />;
};

const meta = {
  title: 'Kiro/Ekran/Kutlama',
  component: KutlamaPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof KutlamaPage>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Varsayilan: Story = { decorators: [urlTuru('gunluk')] };
export const Boss: Story = { decorators: [urlTuru('boss')] };
