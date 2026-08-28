import type { Meta, StoryObj } from '@storybook/react-vite';

import { EmptyState } from './EmptyState';

// Bespoke inline SVG (kanon: lucide/emoji YOK; stroke currentColor 2.1 round-cap)
const IconCompass = () => (
  <svg
    width="30"
    height="30"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2.1"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden
  >
    <circle cx="12" cy="12" r="9" />
    <path d="M15.5 8.5l-2 5-5 2 2-5z" />
  </svg>
);

// Bespoke CTA (kanon: @mui/emotion YOK; altın accent, alarm-kırmızısı/indigo YOK)
const CtaButton = ({ label }: { label: string }) => (
  <button
    type="button"
    style={{
      fontFamily: 'inherit',
      fontSize: 13,
      fontWeight: 700,
      padding: '9px 18px',
      borderRadius: 999,
      border: 'none',
      backgroundColor: '#C9A24B',
      color: '#241F16',
      cursor: 'pointer',
    }}
  >
    {label}
  </button>
);

const meta = {
  title: 'Kiro/EmptyState',
  component: EmptyState,
  args: {
    serifTitle: 'Sıradaki çalışma seni bekliyor',
  },
  argTypes: {
    serifTitle: { control: 'text' },
    body: { control: 'text' },
    icon: { control: false },
    action: { control: false },
  },
} satisfies Meta<typeof EmptyState>;

export default meta;
type Story = StoryObj<typeof meta>;

// Sade: yalnız serif tek cümle iyi haberi verir
export const Sade: Story = {};

// Gövde: akran sesiyle sıradaki adımı açıklar
export const Govdeli: Story = {
  name: 'Gövdeli · akran sesi',
  args: {
    body: 'Buraya ilk konunu eklediğinde yol haritan belirir. Küçük bir adımla başla, gerisi kendiliğinden akar.',
  },
};

// İkon + gövde: pusula yönlendirmesi
export const Ikonlu: Story = {
  name: 'İkonlu · gövdeli',
  args: {
    icon: <IconCompass />,
    body: 'Pusulan hazır. İlk konunu seç, birlikte yön bulalım.',
  },
};

// Tam yönlendiren boşluk: ikon + serif + gövde + tek CTA
export const Yonlendiren: Story = {
  name: 'Yönlendiren boşluk · CTA',
  args: {
    icon: <IconCompass />,
    body: 'İlk adımı at, ilerledikçe burası çalışmalarınla dolacak.',
    action: <CtaButton label="Konu ekle" />,
  },
};

// dusk yüzey: duygusal ekran türü → globals ile temaya sabitlenir
export const Dusk: Story = {
  name: 'dusk · duygusal ekran',
  args: {
    icon: <IconCompass />,
    serifTitle: 'Bugünü kutlamayı hak ettin',
    body: 'Kaldığın yerden devam et; küçük anlar birikip büyük bir yolculuğa dönüşür.',
    action: <CtaButton label="Yolculuğa dön" />,
  },
  globals: { kiroTheme: 'dusk' },
};
