import type { Meta, StoryObj } from '@storybook/react-vite';

import { SegmentedControl } from './SegmentedControl';

const meta = {
  title: 'Kiro/SegmentedControl',
  component: SegmentedControl,
  args: {
    options: [
      { key: 'aylik', label: 'Aylık' },
      { key: 'yillik', label: 'Yıllık' },
    ],
    value: 'aylik',
    variant: 'pill',
    onChange: () => {},
  },
  argTypes: {
    variant: { control: 'inline-radio', options: ['pill', 'scale'] },
    ariaContext: { control: 'text' },
  },
} satisfies Meta<typeof SegmentedControl>;

export default meta;
type Story = StoryObj<typeof meta>;

// pill = abonelik fatura toggle'ı
export const Pill: Story = {};

export const PillRozetli: Story = {
  name: 'Pill · rozetli seçenek',
  args: {
    value: 'yillik',
    options: [
      { key: 'aylik', label: 'Aylık' },
      {
        key: 'yillik',
        label: 'Yıllık',
        badge: (
          <span style={{ marginLeft: 6, fontSize: 11, fontWeight: 700, opacity: 0.68 }}>2 ay bedava</span>
        ),
      },
    ],
  },
};

// scale = anket 1-4 ölçeği · ariaContext satır bağlamı verir
export const Scale: Story = {
  name: 'Scale · anket 1-4 ölçeği',
  args: {
    variant: 'scale',
    ariaContext: 'Bu konuyu ne kadar iyi biliyorsun',
    value: '2',
    options: [
      { key: '1', label: '1' },
      { key: '2', label: '2' },
      { key: '3', label: '3' },
      { key: '4', label: '4' },
    ],
  },
};

// Bileşen temayı okumaz; koyu yüzeyde nasıl durduğunu göstermek için dusk kanvas
export const ScaleDusk: Story = {
  name: 'Scale · dusk yüzey',
  args: {
    variant: 'scale',
    ariaContext: 'Bu konuyu ne kadar iyi biliyorsun',
    value: '3',
    options: [
      { key: '1', label: '1' },
      { key: '2', label: '2' },
      { key: '3', label: '3' },
      { key: '4', label: '4' },
    ],
  },
  globals: { kiroTheme: 'dusk' },
};
