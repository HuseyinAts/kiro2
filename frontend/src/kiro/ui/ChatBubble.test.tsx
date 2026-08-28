import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import * as React from 'react';
import { describe, it, expect } from 'vitest';

import { ChatBubble } from './ChatBubble';
import { KiroThemeProvider } from './theme';

expect.extend(toHaveNoViolations);

const paper = (ui: React.ReactNode) => render(<KiroThemeProvider theme="paper">{ui}</KiroThemeProvider>);

describe('ChatBubble', () => {
  it('AI rolü mesaj içeriğini render eder', () => {
    paper(<ChatBubble role="ai">Birlikte düşünelim mi?</ChatBubble>);
    expect(screen.getByText('Birlikte düşünelim mi?')).toBeInTheDocument();
  });

  it('kullanıcı (me) rolü mesajını render eder', () => {
    paper(<ChatBubble role="me">Paydaları eşitledim.</ChatBubble>);
    expect(screen.getByText('Paydaları eşitledim.')).toBeInTheDocument();
  });

  it('AI ipucu etiketini gösterir', () => {
    paper(
      <ChatBubble role="ai" tag="İpucu 2 / 4">
        Bir adım daha yaklaştık.
      </ChatBubble>
    );
    expect(screen.getByText('İpucu 2 / 4')).toBeInTheDocument();
  });

  it('KANON: pending durum "düşünüyor" dili taşır, absence-dili yok', () => {
    paper(
      <ChatBubble role="ai" pending>
        Düşünüyorum…
      </ChatBubble>
    );
    expect(screen.getByText('Düşünüyorum…')).toBeInTheDocument();
    expect(screen.queryByText(/eksik/i)).not.toBeInTheDocument();
  });

  it('uzun-token satır-kaydırma güvencesi (me + ai balon)', () => {
    const longToken =
      'https://ornek.com/cok/uzun/tek-parca-token-satiri-tasirmasin-diye-kaydirma-guvencesi-gerekli-1234567890';
    const { rerender } = paper(<ChatBubble role="me">{longToken}</ChatBubble>);
    const meText = screen.getByText(longToken);
    expect(meText.style.overflowWrap).toBe('anywhere');
    expect(meText.style.wordBreak).toBe('break-word');

    rerender(
      <KiroThemeProvider theme="paper">
        <ChatBubble role="ai">{longToken}</ChatBubble>
      </KiroThemeProvider>
    );
    const aiText = screen.getByText(longToken);
    expect(aiText.style.overflowWrap).toBe('anywhere');
    expect(aiText.style.wordBreak).toBe('break-word');
  });

  it('axe: AI + kullanıcı balonları ihlal yok', async () => {
    const { container } = paper(
      <>
        <ChatBubble role="ai" tag="İpucu 1 / 3">
          Hangi bilgiden başlayalım?
        </ChatBubble>
        <ChatBubble role="me">Grafikten başlayalım.</ChatBubble>
      </>
    );
    expect(await axe(container)).toHaveNoViolations();
  });
});
