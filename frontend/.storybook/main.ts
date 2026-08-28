import type { StorybookConfig } from '@storybook/react-vite';

// KIRO2 Şafak tasarım sistemi — Storybook 10 (Vite 7 builder).
// Yalnız kiro/ bileşenlerini kapsar; ana uygulama ekranları Storybook'a girmez.
const config: StorybookConfig = {
  framework: { name: '@storybook/react-vite', options: {} },
  stories: ['../src/kiro/**/*.stories.@(ts|tsx)'],
  addons: ['@storybook/addon-a11y'],
  core: { disableTelemetry: true },
};

export default config;
