import type { Meta, StoryObj } from '@storybook/react-vite';

import { StatusChip } from './StatusChip';

const meta = {
  title: 'Kiro/StatusChip',
  component: StatusChip,
  args: { durum: 'acik' },
  argTypes: {
    durum: { control: 'inline-radio', options: ['acik', 'bekliyor', 'tamam'] },
  },
} satisfies Meta<typeof StatusChip>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Acik: Story = { args: { durum: 'acik', kalan: '2 gün' } };
export const Bekliyor: Story = { name: 'Bekliyor · geciken (alarm değil, amber)', args: { durum: 'bekliyor' } };
export const Tamam: Story = { args: { durum: 'tamam' } };
