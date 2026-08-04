import { render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import { MathText } from './kiro/ui/MathText';
import { expect, test } from 'vitest';

test('geometry test', async () => {
  const { container } = render(
    <p style={{ margin: '0 0 24px', fontSize: 17, lineHeight: 1.75 }}>
      <MathText>{'$A(1, 2)$ noktası'}</MathText>
    </p>
  );
  
  await waitFor(() => {
    // wait for Suspense to load MarkdownRenderer
    if (!container.innerHTML.includes('katex')) {
      throw new Error('Not loaded yet');
    }
  }, { timeout: 2000 });
  
  const fs = await import('fs');
  fs.writeFileSync('test_geometry_out.html', container.innerHTML);
});
