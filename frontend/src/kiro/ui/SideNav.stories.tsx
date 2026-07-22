import type { Meta, StoryObj } from '@storybook/react-vite';

import { SideNav } from './SideNav';

// SideNav HER ZAMAN açık (paper) çalışma yüzeyi — bileşen temayı okumaz,
// bu yüzden dusk-özel varyant yok. Varyantlar rol + collapsed + router.
const meta = {
  title: 'Kiro/SideNav',
  component: SideNav,
  args: {
    role: 'ogrenci',
    activeId: 'panel',
    userName: 'Zeynep Kaya',
    userSub: 'TYT · 12. Sınıf',
    collapsed: false,
  },
  argTypes: {
    role: { control: 'inline-radio', options: ['ogrenci', 'veli', 'ogretmen'] },
    collapsed: { control: 'boolean' },
    showSettings: { control: 'boolean' },
    accent: { control: 'color' },
  },
} satisfies Meta<typeof SideNav>;

export default meta;
type Story = StoryObj<typeof meta>;

// Öğrenci navı — Ödevlerim öğesi ödev döngüsü ürün sözü gereği zorunlu
export const Ogrenci: Story = {};

// Alt köşedeki KIRO Asistan düğmesi yalnız öğrenci navında görünür
export const OgrenciAsistan: Story = {
  name: 'Öğrenci · asistan düğmeli',
  args: { activeId: 'solve', onAssistant: () => {} },
};

export const Veli: Story = {
  args: { role: 'veli', activeId: 'children', userName: 'Ali Kaya', userSub: 'Veli', showSettings: true },
};

export const Ogretmen: Story = {
  args: {
    role: 'ogretmen',
    activeId: 'classes',
    userName: 'Ayşe Demir',
    userSub: 'Matematik Öğretmeni',
    showSettings: true,
  },
};

// 64px ikon-only daralma — etiketler gizli, erişilebilir isim aria-label ile durur
export const Daraltilmis: Story = {
  name: 'Daraltılmış · 64px ikon-only',
  args: { collapsed: true, activeId: 'plan', onAssistant: () => {} },
};

// Router entegrasyonu: placeholder href yerine kendi link elemanınızı sarın
export const OzelLink: Story = {
  name: 'renderLink · router entegrasyonu',
  args: {
    renderLink: (item, children, props) => (
      <a href={item.href} {...props}>
        {children}
      </a>
    ),
  },
};
