/**
 * MathJax Configuration for Accessibility
 * Configures MathJax 3.x with full accessibility features including:
 * - Screen reader support (ARIA, MathML)
 * - Keyboard navigation
 * - Turkish language support
 * - Collapsible expressions
 * - Interactive exploration
 */

export const mathJaxConfig = {
  // LaTeX input configuration
  tex: {
    inlineMath: [
      ['$', '$'],
      ['\\(', '\\)'],
    ],
    displayMath: [
      ['$$', '$$'],
      ['\\[', '\\]'],
    ],
    packages: {
      '[+]': ['ams', 'newcommand', 'configmacros', 'action', 'require'],
    },
    // Macros for common Turkish math terms
    macros: {
      ve: '\\text{ ve }',
      veya: '\\text{ veya }',
      ise: '\\Rightarrow',
      ancakveancak: '\\Leftrightarrow',
      ic: '\\in',
      icdegildir: '\\notin',
      altkumesi: '\\subseteq',
      ustkumesi: '\\supseteq',
      birlesim: '\\cup',
      kesisim: '\\cap',
      boskume: '\\emptyset',
    },
  },

  // SVG output configuration
  svg: {
    fontCache: 'global',
    displayAlign: 'left',
    displayIndent: '0',
    scale: 1,
  },

  // Accessibility configuration
  options: {
    // Enable accessibility features
    enableMenu: true,
    enableAssistiveMml: true,
    enableExplorer: true,

    // Menu options for accessibility
    menuOptions: {
      settings: {
        // Assistive MathML for screen readers
        assistiveMml: true,

        // Allow collapsible expressions
        collapsible: true,

        // Enable interactive explorer
        explorer: true,

        // Make math navigable via keyboard
        inTabOrder: false, // Set to true to add math to tab order

        // Zoom options
        zoom: 'Click',
        zscale: '200%',

        // Context menu
        context: 'MathJax',
      },
    },

    // Rendering options
    renderActions: {
      addMenu: [],
      assistiveMml: [],
      complexity: [],
    },
  },

  // Accessibility-specific configuration
  a11y: {
    // Speech output configuration
    speech: {
      enabled: true,
      locale: 'tr', // Turkish language

      // Speech rules for Turkish
      rules: {
        default: 'default',
        brief: 'brief',
        sbrief: 'superbrief',
      },

      // Braille output
      braille: true,

      // Speech generation
      speechRules: 'mathspeak', // Options: 'mathspeak', 'clearspeak'
      speechStyle: 'default', // Options: 'default', 'brief', 'superbrief'
    },

    // Semantic enrichment
    semantic: true,

    // Complexity metrics
    complexity: {
      disabled: false,
      // Collapse complex expressions
      collapse: {
        identifier: 3,
        number: 3,
        text: 10,
        infixop: 15,
        relseq: 15,
        multirel: 15,
        fenced: 18,
        bigop: 20,
        integral: 20,
        fraction: 12,
        sqrt: 9,
        tensor: 10,
        general: 25,
      },
    },

    // Explorer configuration (keyboard navigation)
    explorer: {
      walker: 'syntactic', // Options: 'syntactic', 'semantic'
      highlight: 'hover',
      background: 'blue',
      foreground: 'white',
      speech: true,
      generation: 'lazy',
      subtitle: true,
      keyMagnifier: true,
      speechModifier: 'alt',
    },
  },

  // Startup configuration
  startup: {
    pageReady: async () => {
      console.log('MathJax starting...');

      // Default page ready
      await window.MathJax.startup.defaultPageReady();

      console.log('MathJax loaded with accessibility features');

      // Dispatch custom event
      const event = new CustomEvent('mathjax-loaded', {
        detail: { version: window.MathJax.version },
      });
      window.dispatchEvent(event);

      return Promise.resolve();
    },

    ready: () => {
      console.log('MathJax ready');
      window.MathJax.startup.defaultReady();
    },
  },

  // Loader configuration
  loader: {
    load: [
      'input/tex',
      'output/svg',
      '[tex]/ams',
      '[tex]/newcommand',
      '[tex]/configmacros',
      '[tex]/action',
      '[tex]/require',
      'ui/menu',
      'a11y/assistive-mml',
      'a11y/semantic-enrich',
      'a11y/complexity',
      'a11y/explorer',
    ],
    paths: {
      mathjax: 'https://cdn.jsdelivr.net/npm/mathjax@3/es5',
    },
  },
};

/**
 * Initialize MathJax with accessibility configuration
 */
export const initMathJax = (): void => {
  if (typeof window !== 'undefined') {
    // Set configuration before MathJax loads
    (window as any).MathJax = mathJaxConfig;

    // Load MathJax script
    if (!document.querySelector('script[src*="mathjax"]')) {
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg-full.js';
      script.async = true;
      script.id = 'MathJax-script';
      document.head.appendChild(script);
    }
  }
};

/**
 * Typeset a specific element or the entire document
 */
export const typesetMath = async (elements?: HTMLElement[]): Promise<void> => {
  if (window.MathJax && window.MathJax.typesetPromise) {
    try {
      await window.MathJax.typesetPromise(elements);
      console.log('Math typeset completed');
    } catch (error) {
      console.error('MathJax typeset error:', error);
    }
  }
};

/**
 * Convert LaTeX to accessible SVG with MathML
 */
export const convertToSvg = async (latex: string, display: boolean = false): Promise<string> => {
  if (!window.MathJax || !window.MathJax.tex2svg) {
    throw new Error('MathJax not loaded');
  }

  try {
    const node = window.MathJax.tex2svg(latex, { display });
    return node.outerHTML;
  } catch (error) {
    console.error('LaTeX to SVG conversion error:', error);
    throw error;
  }
};

/**
 * Convert LaTeX to MathML
 */
export const convertToMathML = async (latex: string): Promise<string> => {
  if (!window.MathJax || !window.MathJax.tex2mml) {
    throw new Error('MathJax not loaded');
  }

  try {
    return window.MathJax.tex2mml(latex);
  } catch (error) {
    console.error('LaTeX to MathML conversion error:', error);
    throw error;
  }
};

/**
 * Check if MathJax is loaded
 */
export const isMathJaxLoaded = (): boolean => {
  return !!(window.MathJax && window.MathJax.startup && window.MathJax.startup.promise);
};

/**
 * Wait for MathJax to be ready
 */
export const waitForMathJax = (): Promise<void> => {
  return new Promise((resolve) => {
    if (isMathJaxLoaded()) {
      window.MathJax.startup.promise.then(resolve);
    } else {
      window.addEventListener('mathjax-loaded', () => resolve(), { once: true });
    }
  });
};

export default mathJaxConfig;
