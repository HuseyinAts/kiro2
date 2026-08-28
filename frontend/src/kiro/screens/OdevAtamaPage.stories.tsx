import type { Meta, StoryObj } from '@storybook/react-vite';

import { OdevAtamaPage } from './OdevAtamaPage';

const meta = {
  title: 'Kiro/Ekran/OdevAtama',
  component: OdevAtamaPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof OdevAtamaPage>;

export default meta;
type Story = StoryObj<typeof meta>;

// Varsayılan — tüm sınıf seçili, kişiye özel zorluk açık.
export const Varsayilan: Story = {};

// Öğrenci-özetinden gelen ön-seçim (?ogrenci=id) — yalnız o öğrenci seçili başlar.
export const OnSecili: Story = {
  args: { ogrenciId: 'o-cy' },
};
