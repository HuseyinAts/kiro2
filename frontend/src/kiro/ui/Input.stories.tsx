import type { Meta, StoryObj } from '@storybook/react-vite';

import { Input } from './Input';

const meta = {
  title: 'Kiro/Input',
  component: Input,
  args: {
    value: '',
    onChange: () => undefined,
    ariaLabel: 'Ad Soyad',
    placeholder: 'Adınızı yazın',
  },
  argTypes: {
    type: { control: 'inline-radio', options: ['text', 'email', 'password', 'number'] },
    width: { control: 'number' },
  },
} satisfies Meta<typeof Input>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Bos: Story = { name: 'Boş · placeholder yönlendirir' };
export const Dolu: Story = { args: { value: 'Ayşe Yılmaz' } };
export const Eposta: Story = {
  name: 'E-posta',
  args: { type: 'email', ariaLabel: 'E-posta', placeholder: 'ornek@site.com' },
};
export const Parola: Story = {
  name: 'Parola',
  args: { type: 'password', value: 'gizli-parola', ariaLabel: 'Parola', placeholder: 'Parolanız' },
};
export const GenisAlan: Story = {
  name: 'Geniş alan',
  args: { width: 320, placeholder: 'Daha uzun bir metin alanı' },
};

// dusk yalnız KOYU yüzeyde → story dusk temaya sabitlenir
export const DuskYuzey: Story = {
  name: 'dusk yüzey',
  args: { value: 'Koyu yüzey' },
  globals: { kiroTheme: 'dusk' },
};
