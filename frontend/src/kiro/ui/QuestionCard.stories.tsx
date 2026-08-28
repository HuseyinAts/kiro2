import type { Meta, StoryObj } from '@storybook/react-vite';

import { QuestionCard } from './QuestionCard';
import type { AnswerResult } from '../api/api-client';

const meta = {
  title: 'Kiro/Composite/QuestionCard',
  component: QuestionCard,
  parameters: { layout: 'padded' },
} satisfies Meta<typeof QuestionCard>;

export default meta;
type Story = StoryObj<typeof meta>;

const BASE = {
  soruNo: 3,
  toplam: 10,
  konu: 'Türev',
  zorlukB: 0.4,
  soru: 'f(x) = x³ − 3x² + 2 fonksiyonunun x = 2 noktasındaki teğetinin eğimi kaçtır?',
  secenekler: ['−4', '0', '4', '8', '12'],
  konuHakimiyet: 58,
  konuTrend: 'down' as const,
};

const DOGRU: AnswerResult = {
  correct: true, dogru: 1,
  cozum: ['Bir noktadaki teğet eğimi = o noktadaki türev: f′(2).', 'Türevi al: f′(x) = 3x² − 6x.', 'x = 2 yaz: f′(2) = 12 − 12 = 0.'],
  neden: 'Türev, bir noktadaki anlık değişim hızıdır; grafikte teğetin eğimine eşittir.', xpKazanilan: 10,
};
const YANLIS: AnswerResult = { ...DOGRU, correct: false, xpKazanilan: 2 };

export const Varsayilan: Story = { args: { ...BASE, secilen: null, onSelect: () => {}, isaretli: false, onToggleIsaret: () => {} } };

export const Secili: Story = { args: { ...BASE, secilen: 2, onSelect: () => {}, onToggleIsaret: () => {} } };

export const Isaretli: Story = { args: { ...BASE, secilen: null, onSelect: () => {}, isaretli: true, onToggleIsaret: () => {} } };

export const CozumDogru: Story = { args: { ...BASE, secilen: 1, sonuc: DOGRU } };

export const CozumYanlis: Story = { args: { ...BASE, secilen: 3, sonuc: YANLIS } };
