import type { Meta, StoryObj } from '@storybook/react-vite';

import { IlkHaftaPage } from './IlkHaftaPage';

const meta = {
  title: 'Kiro/Ekran/IlkHafta',
  component: IlkHaftaPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof IlkHaftaPage>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Varsayilan: Story = {};
