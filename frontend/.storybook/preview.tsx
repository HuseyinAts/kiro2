import type { Preview, Decorator } from '@storybook/react-vite';

import { KiroThemeProvider } from '../src/kiro/ui/theme';
import type { KiroTheme } from '../src/kiro/ui/theme';
import '../src/kiro/tokens/tokens.css';

// KANON: tema kullanıcı toggle'ı DEĞİL, ekran türüdür. Buradaki toolbar yalnız
// story-demo amacıyla bir bileşeni iki kanonik yüzeyde (paper/dusk) göstermek içindir.
const withKiroTheme: Decorator = (Story, context) => {
  const theme = (context.globals.kiroTheme ?? 'paper') as KiroTheme;
  return (
    <KiroThemeProvider theme={theme}>
      <div
        className={theme === 'dusk' ? 'k-dusk' : 'k-paper'}
        style={{
          background: theme === 'dusk' ? '#110C18' : '#F7F4EF',
          padding: 28,
          minHeight: 96,
        }}
      >
        <Story />
      </div>
    </KiroThemeProvider>
  );
};

const preview: Preview = {
  parameters: {
    layout: 'centered',
    controls: { expanded: true },
  },
  globalTypes: {
    kiroTheme: {
      description: 'Kiro tema (ekran türü — demo)',
      defaultValue: 'paper',
      toolbar: {
        title: 'Tema',
        items: [
          { value: 'paper', title: 'paper · çalışma/analitik' },
          { value: 'dusk', title: 'dusk · duygusal/hub' },
        ],
      },
    },
  },
  decorators: [withKiroTheme],
};

export default preview;
