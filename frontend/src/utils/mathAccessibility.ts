/**
 * Math Accessibility Utilities
 * Converts LaTeX formulas to human-readable Turkish descriptions for screen readers
 */

interface MathSymbol {
  latex: string | RegExp;
  turkish: string;
}

// Common mathematical symbols and their Turkish pronunciations
const mathSymbols: MathSymbol[] = [
  // Basic operations
  { latex: '+', turkish: 'artı' },
  { latex: '-', turkish: 'eksi' },
  { latex: /\\times|\\cdot/g, turkish: 'çarpı' },
  { latex: /\\div|\//g, turkish: 'bölü' },
  { latex: '=', turkish: 'eşittir' },
  { latex: /\\neq|\\ne/g, turkish: 'eşit değildir' },
  { latex: /\\approx/g, turkish: 'yaklaşık eşittir' },
  { latex: /\\equiv/g, turkish: 'denktir' },

  // Comparison
  { latex: '<', turkish: 'küçüktür' },
  { latex: '>', turkish: 'büyüktür' },
  { latex: /\\leq|\\le/g, turkish: 'küçük eşittir' },
  { latex: /\\geq|\\ge/g, turkish: 'büyük eşittir' },

  // Greek letters
  { latex: /\\alpha/g, turkish: 'alfa' },
  { latex: /\\beta/g, turkish: 'beta' },
  { latex: /\\gamma/g, turkish: 'gama' },
  { latex: /\\delta/g, turkish: 'delta' },
  { latex: /\\epsilon/g, turkish: 'epsilon' },
  { latex: /\\theta/g, turkish: 'teta' },
  { latex: /\\lambda/g, turkish: 'lambda' },
  { latex: /\\mu/g, turkish: 'mü' },
  { latex: /\\pi/g, turkish: 'pi' },
  { latex: /\\sigma/g, turkish: 'sigma' },
  { latex: /\\phi/g, turkish: 'fi' },
  { latex: /\\omega/g, turkish: 'omega' },

  // Set theory
  { latex: /\\in/g, turkish: 'elemanıdır' },
  { latex: /\\notin/g, turkish: 'elemanı değildir' },
  { latex: /\\subset/g, turkish: 'alt kümesidir' },
  { latex: /\\supset/g, turkish: 'üst kümesidir' },
  { latex: /\\cup/g, turkish: 'birleşim' },
  { latex: /\\cap/g, turkish: 'kesişim' },
  { latex: /\\emptyset/g, turkish: 'boş küme' },

  // Logic
  { latex: /\\land|\\wedge/g, turkish: 've' },
  { latex: /\\lor|\\vee/g, turkish: 'veya' },
  { latex: /\\neg|\\lnot/g, turkish: 'değil' },
  { latex: /\\implies|\\Rightarrow/g, turkish: 'ise' },
  { latex: /\\iff|\\Leftrightarrow/g, turkish: 'ancak ve ancak' },

  // Calculus
  { latex: /\\lim/g, turkish: 'limit' },
  { latex: /\\sum/g, turkish: 'toplam' },
  { latex: /\\prod/g, turkish: 'çarpım' },
  { latex: /\\int/g, turkish: 'integral' },
  { latex: /\\partial/g, turkish: 'kısmi türev' },
  { latex: /\\nabla/g, turkish: 'nabla' },
  { latex: /\\infty/g, turkish: 'sonsuz' },
];

/**
 * Converts a LaTeX formula to Turkish description for screen readers
 */
export const generateMathDescription = (latex: string): string => {
  let description = latex;

  // Remove LaTeX whitespace commands
  description = description.replace(/\\,|\\;|\\:/g, ' ');
  description = description.replace(/\\\s/g, ' ');

  // Handle fractions: \frac{a}{b}
  description = description.replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, (_, num, den) => {
    return `${num} bölü ${den}`;
  });

  // Handle square roots: \sqrt{x}
  description = description.replace(/\\sqrt\{([^}]+)\}/g, (_, content) => {
    return `karekök ${content}`;
  });

  // Handle nth roots: \sqrt[n]{x}
  description = description.replace(/\\sqrt\[([^\]]+)\]\{([^}]+)\}/g, (_, n, content) => {
    return `${n}. dereceden kök ${content}`;
  });

  // Handle exponents: x^{2} or x^2
  description = description.replace(/([a-zA-Z0-9]+)\^\{([^}]+)\}/g, (_, base, exp) => {
    return `${base} üssü ${exp}`;
  });
  description = description.replace(/([a-zA-Z0-9]+)\^([a-zA-Z0-9])/g, (_, base, exp) => {
    return `${base} üssü ${exp}`;
  });

  // Handle subscripts: x_{1} or x_1
  description = description.replace(/([a-zA-Z0-9]+)_\{([^}]+)\}/g, (_, base, sub) => {
    return `${base} alt ${sub}`;
  });
  description = description.replace(/([a-zA-Z0-9]+)_([a-zA-Z0-9])/g, (_, base, sub) => {
    return `${base} alt ${sub}`;
  });

  // Handle integrals: \int_{a}^{b}
  description = description.replace(/\\int_\{([^}]+)\}\^\{([^}]+)\}/g, (_, lower, upper) => {
    return `${lower} den ${upper} ye integral`;
  });

  // Handle limits: \lim_{x \to a}
  description = description.replace(/\\lim_\{([^}]+)\\to([^}]+)\}/g, (_, variable, value) => {
    return `${variable} ${value} e giderken limit`;
  });

  // Handle summations: \sum_{i=1}^{n}
  description = description.replace(/\\sum_\{([^}]+)\}\^\{([^}]+)\}/g, (_, lower, upper) => {
    return `${lower} den ${upper} ye toplam`;
  });

  // Handle products: \prod_{i=1}^{n}
  description = description.replace(/\\prod_\{([^}]+)\}\^\{([^}]+)\}/g, (_, lower, upper) => {
    return `${lower} den ${upper} ye çarpım`;
  });

  // Handle matrices: \begin{matrix} ... \end{matrix}
  description = description.replace(/\\begin\{[bBpv]?matrix\}([^]*?)\\end\{[bBpv]?matrix\}/g, () => {
    return 'matris';
  });

  // Handle absolute value: |x|
  description = description.replace(/\|([^|]+)\|/g, (_, content) => {
    return `${content} nin mutlak değeri`;
  });

  // Handle parentheses
  description = description.replace(/\\left\(/g, 'aç parantez');
  description = description.replace(/\\right\)/g, 'kapat parantez');
  description = description.replace(/\\left\[/g, 'aç köşeli parantez');
  description = description.replace(/\\right\]/g, 'kapat köşeli parantez');
  description = description.replace(/\\left\{/g, 'aç süslü parantez');
  description = description.replace(/\\right\}/g, 'kapat süslü parantez');

  // Handle text in formulas
  description = description.replace(/\\text\{([^}]+)\}/g, '$1');
  description = description.replace(/\\mathrm\{([^}]+)\}/g, '$1');

  // Replace common symbols
  mathSymbols.forEach(({ latex, turkish }) => {
    if (latex instanceof RegExp) {
      description = description.replace(latex, turkish);
    } else {
      description = description.split(latex).join(turkish);
    }
  });

  // Clean up extra spaces and LaTeX commands
  description = description.replace(/\\/g, '');
  description = description.replace(/\{|\}/g, '');
  description = description.replace(/\s+/g, ' ');
  description = description.trim();

  return description;
};

/**
 * Generates description for geometric figures
 */
export const generateGeometryDescription = (
  shape: string,
  properties: Record<string, string | number>,
): string => {
  const descriptions: Record<string, string> = {
    triangle: 'Üçgen',
    square: 'Kare',
    rectangle: 'Dikdörtgen',
    circle: 'Daire',
    pentagon: 'Beşgen',
    hexagon: 'Altıgen',
    parallelogram: 'Paralelkenar',
    trapezoid: 'Yamuk',
  };

  let description = descriptions[shape] || shape;

  if (properties.angle) {
    description += `, ${properties.angle} derece açı`;
  }
  if (properties.side) {
    description += `, kenar uzunluğu ${properties.side}`;
  }
  if (properties.radius) {
    description += `, yarıçap ${properties.radius}`;
  }
  if (properties.area) {
    description += `, alan ${properties.area}`;
  }

  return description;
};

/**
 * Generates description for graphs and charts
 */
export const generateGraphDescription = (
  type: 'linear' | 'quadratic' | 'exponential' | 'logarithmic' | 'sinusoidal',
  trend: 'increasing' | 'decreasing' | 'constant' | 'oscillating',
  domain?: string,
  range?: string,
): string => {
  const typeDescriptions = {
    linear: 'Doğrusal fonksiyon',
    quadratic: 'İkinci dereceden fonksiyon (parabol)',
    exponential: 'Üstel fonksiyon',
    logarithmic: 'Logaritmik fonksiyon',
    sinusoidal: 'Sinüzoidal fonksiyon',
  };

  const trendDescriptions = {
    increasing: 'artan',
    decreasing: 'azalan',
    constant: 'sabit',
    oscillating: 'salınımlı',
  };

  let description = `${typeDescriptions[type]}, ${trendDescriptions[trend]}`;

  if (domain) {
    description += `, tanım kümesi ${domain}`;
  }
  if (range) {
    description += `, değer kümesi ${range}`;
  }

  return description;
};

/**
 * Creates accessible data table from graph data
 */
export const generateDataTable = (
  xValues: number[],
  yValues: number[],
  xLabel: string = 'x',
  yLabel: string = 'y',
): string => {
  let table = '<table role="table" aria-label="Grafik veri tablosu">\n';
  table += `  <thead>\n    <tr>\n      <th>${xLabel}</th>\n      <th>${yLabel}</th>\n    </tr>\n  </thead>\n`;
  table += '  <tbody>\n';

  for (let i = 0; i < Math.min(xValues.length, yValues.length); i++) {
    table += `    <tr>\n      <td>${xValues[i]}</td>\n      <td>${yValues[i]}</td>\n    </tr>\n`;
  }

  table += '  </tbody>\n</table>';
  return table;
};

/**
 * Common formulas and their Turkish descriptions
 */
export const commonFormulas: Record<string, string> = {
  // Algebra
  'x^2 + bx + c = 0': 'İkinci dereceden denklem: x kare artı b çarpı x artı c eşittir sıfır',
  'a^2 + b^2 = c^2': 'Pisagor teoremi: a kare artı b kare eşittir c kare',
  '(a + b)^2 = a^2 + 2ab + b^2': 'Tam kare açılımı: a artı b parantez kare eşittir a kare artı 2 a b artı b kare',

  // Geometry
  'A = \\pi r^2': 'Dairenin alanı: A eşittir pi çarpı r kare',
  'C = 2\\pi r': 'Dairenin çevresi: C eşittir 2 çarpı pi çarpı r',
  'V = \\frac{4}{3}\\pi r^3': 'Kürenin hacmi: V eşittir 4 bölü 3 çarpı pi çarpı r küp',

  // Trigonometry
  '\\sin^2\\theta + \\cos^2\\theta = 1': 'Trigonometrik özdeşlik: sinüs kare teta artı kosinüs kare teta eşittir bir',
  '\\tan\\theta = \\frac{\\sin\\theta}{\\cos\\theta}': 'Tanjant tanımı: tanjant teta eşittir sinüs teta bölü kosinüs teta',

  // Calculus
  '\\frac{d}{dx}x^n = nx^{n-1}': 'Üstel türev kuralı: x üssü n nin türevi eşittir n çarpı x üssü n eksi bir',
  '\\int x^n dx = \\frac{x^{n+1}}{n+1} + C': 'Üstel integral kuralı: x üssü n nin integrali eşittir x üssü n artı bir bölü n artı bir artı C',
};

/**
 * Gets a pre-defined description for common formulas
 */
export const getCommonFormulaDescription = (latex: string): string | null => {
  // Normalize the latex string
  const normalized = latex.replace(/\s+/g, ' ').trim();
  return commonFormulas[normalized] || null;
};

export default generateMathDescription;
