import React from 'react';
import { render } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BionicReadingText, bionicWord } from '../BionicReadingText';

describe('BionicReadingText Algorithm', () => {
  it('correctly processes short words', () => {
    const { container } = render(<>{bionicWord('ve')}</>);
    expect(container.innerHTML).toContain('<span class="bionic-bold">v</span>e');
  });

  it('correctly processes medium words', () => {
    const { container } = render(<>{bionicWord('okul')}</>);
    expect(container.innerHTML).toContain('<span class="bionic-bold">ok</span>ul');
  });

  it('correctly processes long words', () => {
    const { container } = render(<>{bionicWord('psikoloji')}</>);
    expect(container.innerHTML).toContain('<span class="bionic-bold">psiko</span>loji');
  });

  it('preserves punctuation marks', () => {
    const { container } = render(<>{bionicWord('Geldiler.')}</>);
    // 8 letters -> G e l d i l e r
    // ceil(8/2) = 4 -> Geld
    expect(container.innerHTML).toContain('<span class="bionic-bold">Geld</span>iler.');
  });

  it('handles turkish characters', () => {
    const { container } = render(<>{bionicWord('öğrenci')}</>);
    // 7 letters -> ceil(7/2) = 4 -> öğre
    expect(container.innerHTML).toContain('<span class="bionic-bold">öğre</span>nci');
  });

  it('renders paragraph properly with enabled true', () => {
    const { container } = render(<BionicReadingText text="Merhaba dünya!" enabled={true} />);
    expect(container.innerHTML).toContain('neuro-inclusive-mode');
    expect(container.innerHTML).toContain('<span class="bionic-bold">Merh</span>aba');
    expect(container.innerHTML).toContain('<span class="bionic-bold">dün</span>ya!');
  });

  it('renders normal text when enabled is false', () => {
    const { container } = render(<BionicReadingText text="Merhaba dünya!" enabled={false} />);
    expect(container.innerHTML).not.toContain('neuro-inclusive-mode');
    expect(container.innerHTML).not.toContain('bionic-bold');
    expect(container.innerHTML).toContain('Merhaba dünya!');
  });

  it('preserves HTML tags and MathJax formulas', () => {
    const textWithEdgeCases = "İşte bir HTML <b>kalın</b> ve bir formül $x^2+y=0$ testi.";
    const { container } = render(<BionicReadingText text={textWithEdgeCases} enabled={true} />);

    // HTML should be preserved as text or fragment, not chopped up.
    // In our implementation we return the token directly if it's protected.
    // Check if the formula is intact
    expect(container.innerHTML).toContain('$x^2+y=0$');

    // Test the bionic words for 4-letter words (ceil(4/2) = 2)
    expect(container.innerHTML).toContain('<span class="bionic-bold">İş</span>te');
    expect(container.innerHTML).toContain('<span class="bionic-bold">HT</span>ML');
    expect(container.innerHTML).toContain('<span class="bionic-bold">b</span>ir');
  });
});
