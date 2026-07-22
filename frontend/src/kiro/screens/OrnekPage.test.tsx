import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import { OrnekPage } from './OrnekPage';

// Faz 1 DoD: configureKiroApi({mode:'mock'}) ile örnek sayfa GERÇEK mock veriyi render eder.
describe('OrnekPage — Faz 1 configureKiroApi mock render kanıtı', () => {
  it('kiro-data.json persona + seviye + ders listesini render eder', async () => {
    render(<OrnekPage />);

    // async mock fetch tamamlanınca persona kartı görünür (yükleniyor → içerik)
    await waitFor(() => {
      expect(screen.getByTestId('persona-ad')).toBeInTheDocument();
    });

    // persona adı boş değil (kiro-data.json'dan geldi)
    expect((screen.getByTestId('persona-ad').textContent ?? '').length).toBeGreaterThan(0);

    // seviye sayısı ve ders listesi render edildi
    expect(screen.getByTestId('seviye')).toBeInTheDocument();
    expect(screen.getByTestId('ders-listesi').children.length).toBeGreaterThan(0);
  });
});
