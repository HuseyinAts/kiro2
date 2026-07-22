import type { Meta, StoryObj } from '@storybook/react-vite';

import { SeriDondurmaPage } from './SeriDondurmaPage';

const meta = {
  title: 'Kiro/Ekran/SeriDondurma',
  component: SeriDondurmaPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof SeriDondurmaPage>;

export default meta;
type Story = StoryObj<typeof meta>;

// Varsayılan — mock seri=12 · rekor=21 · dondurmaHak=2 · Per günü freeze.
// (Harness 7 genişlikte gezer; grid ≤760 tek sütun + kilometre taşı bağlayıcıları gizlenir.)
export const Varsayilan: Story = {};
