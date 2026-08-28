import type { Meta, StoryObj } from '@storybook/react-vite';

import { ConfettiDawn } from './ConfettiDawn';
import { surf, type KiroTheme } from './theme';

// prefers-reduced-motion Storybook'ta arg degil sistem tercihi -> parametreyle taklit et.
// (Kanon: transform-only konfeti; azaltılmış harekette TAMAMEN kapalı.)
function applyReducedMotion(reduce: boolean): void {
  window.matchMedia = (query: string) =>
    ({
      matches: reduce && query.includes('prefers-reduced-motion'),
      media: query,
      onchange: null,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      addListener: () => undefined,
      removeListener: () => undefined,
      dispatchEvent: () => false,
    }) as unknown as MediaQueryList;
}

const meta = {
  title: 'Kiro/ConfettiDawn',
  component: ConfettiDawn,
  args: { count: 20, zIndex: 2 },
  argTypes: {
    count: { control: { type: 'number' } },
    zIndex: { control: { type: 'number' } },
  },
  decorators: [
    (Story, context) => {
      applyReducedMotion(Boolean(context.parameters.reducedMotion));
      const theme: KiroTheme = context.globals.kiroTheme === 'dusk' ? 'dusk' : 'paper';
      const s = surf(theme);
      return (
        <div
          style={{
            position: 'relative',
            width: 420,
            height: 300,
            overflow: 'hidden',
            borderRadius: 14,
            background: s.bg,
            border: `1px solid ${s.border}`,
          }}
        >
          <Story />
        </div>
      );
    },
  ],
} satisfies Meta<typeof ConfettiDawn>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const Seyrek: Story = {
  name: 'Seyrek · az parça',
  args: { count: 8 },
};

export const Yogun: Story = {
  name: 'Yoğun · çok parça',
  args: { count: 40 },
};

// Kutlama duygusal (koyu) ekranlarda gosterilir; dusk yuzeyde goster.
export const DuskYuzeyde: Story = {
  name: 'dusk yüzeyde kutlama',
  globals: { kiroTheme: 'dusk' },
};

// Azaltılmış hareket tercihinde konfeti hiç render edilmez (boş yüzey).
export const AzaltilmisHareket: Story = {
  name: 'azaltılmış hareket · konfeti kapalı',
  parameters: { reducedMotion: true },
};
