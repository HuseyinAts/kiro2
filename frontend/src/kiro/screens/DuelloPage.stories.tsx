import type { Meta, StoryObj } from '@storybook/react-vite';

import { DuelloPage } from './DuelloPage';

const meta = {
  title: 'Kiro/Ekran/Duello',
  component: DuelloPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof DuelloPage>;

export default meta;
type Story = StoryObj<typeof meta>;

// Varsayılan — matchmake('mat') server-sim; süre halkası + VS bandı + soru kartı.
// Süre azaldıkça halka renk-shift'i (TEMPO) devreye girer; şık tıklayınca tur-sonuç
// bandı açılır, son turdan sonra bitiş overlay'i (zaferde ConfettiDawn) gelir.
export const Varsayilan: Story = {};
