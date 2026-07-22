import type { Meta, StoryObj } from '@storybook/react-vite';

import { ErrorState } from './ErrorState';

const meta = {
  title: 'Kiro/ErrorState',
  component: ErrorState,
  args: { onRetry: () => {} },
  argTypes: {
    serifTitle: { control: 'text' },
    body: { control: 'text' },
    retryLabel: { control: 'text' },
  },
} satisfies Meta<typeof ErrorState>;

export default meta;
type Story = StoryObj<typeof meta>;

export const VarsayilanKurtarma: Story = {};

export const KurtarmaYok: Story = {
  name: 'Kurtarma eylemi olmadan',
  args: { onRetry: undefined },
};

export const OzelMesaj: Story = {
  name: 'Özel başlık · gövde',
  args: {
    serifTitle: 'Bağlantı şu an kurulamadı.',
    body: 'Sorun sende değil. İlerlemen güvende — birazdan yeniden deneyebilirsin.',
    retryLabel: 'Yeniden bağlan',
  },
};

export const DuskYuzey: Story = {
  name: 'dusk yüzey',
  globals: { kiroTheme: 'dusk' },
};
