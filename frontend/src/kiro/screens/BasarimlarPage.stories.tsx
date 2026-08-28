import type { Meta, StoryObj } from '@storybook/react-vite';

import { BasarimlarPage } from './BasarimlarPage';

const meta = {
  title: 'Kiro/Ekran/Basarimlar',
  component: BasarimlarPage,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof BasarimlarPage>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Varsayilan: Story = {};
