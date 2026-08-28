import type { Meta, StoryObj } from '@storybook/react-vite';

import { AlanKutuphanePage } from './AlanKutuphanePage';

const meta = {
  title: 'Kiro/Ekran/AlanKutuphane',
  component: AlanKutuphanePage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof AlanKutuphanePage>;

export default meta;
type Story = StoryObj<typeof meta>;

// Varsayılan — seninKey=Sayısal rozetli, 3 alan + 4 ders akordeonu (mat/fiz soru şeritli).
export const Varsayilan: Story = {};
