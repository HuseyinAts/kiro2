module.exports = {
  root: true,
  env: {
    browser: true,
    es2021: true,
    node: true,
  },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react/recommended',
    // 'plugin:react-hooks/recommended', // Disabled - v7 has React 19 Compiler rules not compatible with React 18
    'plugin:jsx-a11y/recommended',
    'plugin:import/recommended',
    'plugin:import/typescript',
  ],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
    ecmaFeatures: {
      jsx: true,
    },
    project: './tsconfig.json',
  },
  plugins: [
    'react',
    'react-hooks',
    'react-refresh',
    '@typescript-eslint',
    'jsx-a11y',
    'import',
  ],
  settings: {
    react: {
      version: 'detect',
    },
    'import/resolver': {
      typescript: {
        alwaysTryTypes: true,
        project: './tsconfig.json',
      },
      node: {
        extensions: ['.js', '.jsx', '.ts', '.tsx'],
      },
    },
  },
  rules: {
    // React Rules
    'react/react-in-jsx-scope': 'off', // Not needed in React 18+
    'react/prop-types': 'off', // Using TypeScript for prop validation
    'react/jsx-uses-react': 'off',
    'react/jsx-uses-vars': 'error',
    'react-refresh/only-export-components': [
      'warn',
      { allowConstantExport: true },
    ],

    // TypeScript Rules
    '@typescript-eslint/no-explicit-any': 'warn',
    '@typescript-eslint/no-unused-vars': [
      'error',
      {
        argsIgnorePattern: '^_',
        varsIgnorePattern: '^_',
      },
    ],
    '@typescript-eslint/explicit-module-boundary-types': 'off',
    '@typescript-eslint/no-non-null-assertion': 'warn',

    // Import Rules
    'import/order': [
      'error',
      {
        groups: [
          'builtin',
          'external',
          'internal',
          'parent',
          'sibling',
          'index',
        ],
        'newlines-between': 'always',
        alphabetize: {
          order: 'asc',
          caseInsensitive: true,
        },
      },
    ],
    'import/no-unresolved': ['error', {
      ignore: ['^mermaid$', 'react-syntax-highlighter/.*']
    }],
    'import/no-cycle': 'warn',
    'import/no-duplicates': 'error',

    // S179 fix (B-P0-66): UI library hygiene.
    // KIRO2 has 3 systems: @mui/material (221 files), Tailwind (158),
    // shadcn `components/ui/*` (18). New components MUST pick ONE.
    // This rule is informational — pre-existing mix stays; CI promo
    // after audit of remaining ~25 mixed files.
    'no-restricted-imports': [
      'warn',
      {
        paths: [
          {
            name: '@mui/material',
            message:
              'B-P0-66: prefer Tailwind + shadcn for new components. '
              + 'See .claude/rules/path-naming.md style addendum.',
          },
        ],
      },
    ],

    // Accessibility Rules.
    // S179 fix (F-P1-7): promote the 3 highest-volume / highest-risk
    // rules to 'error'. Pre-fix all were 'warn' and CI's
    // --max-warnings 0 was bypassed, so 156 a11y violations were
    // silently shipping. The 3 promoted rules are also the ones a
    // screen-reader user notices first.
    'jsx-a11y/anchor-is-valid': 'warn',
    'jsx-a11y/click-events-have-key-events': 'error',  // S179 promoted
    'jsx-a11y/no-static-element-interactions': 'error',  // S179 promoted
    'jsx-a11y/alt-text': 'error',  // S179 promoted (was 100% prod, keep strict)
    'jsx-a11y/aria-props': 'warn',
    'jsx-a11y/aria-role': 'warn',
    // S179 fix (F-P0-6): promote to error. Pre-fix only 3/150 inputs
    // had `aria-invalid` and ~67 `<label>` lacked `htmlFor`. CI gate
    // forces new code to pair labels with inputs for screen readers.
    'jsx-a11y/label-has-associated-control': 'error',
    'jsx-a11y/media-has-caption': 'warn',
    'jsx-a11y/no-autofocus': 'warn',

    // React Hooks - relax for React 18 (React Compiler rules are for React 19)
    'react-hooks/rules-of-hooks': 'error',
    // S179 fix (B-P1-23): exhaustive-deps promoted from warn → error.
    // Pre-fix 82% of components lacked memo/callback, and stale-deps
    // were the primary re-render trigger. Keeping this strict catches
    // the pattern at PR-time.
    'react-hooks/exhaustive-deps': 'error',
    // Disable React Compiler rules (only needed for React 19)
    // These rules are for React 19 Compiler, not needed for React 18
    'react-hooks/purity': 'off',
    'react-hooks/ref-access': 'off',
    'react-hooks/set-state-in-effect': 'off',
    'react-hooks/immutability': 'off',
    'react-hooks/prefer-memoization': 'off',

    // Other relaxed rules
    'react/display-name': 'warn',
    '@typescript-eslint/ban-ts-comment': 'warn',
    'jsx-a11y/mouse-events-have-key-events': 'warn',
    'jsx-a11y/no-noninteractive-element-interactions': 'warn',
    'jsx-a11y/no-noninteractive-tabindex': 'warn',
    'jsx-a11y/no-redundant-roles': 'warn',
    'jsx-a11y/no-interactive-element-to-noninteractive-role': 'warn',
    'import/no-duplicates': 'warn',
    'import/order': 'warn',
    '@typescript-eslint/no-require-imports': 'warn',

    // General Rules
    'no-console': ['warn', { allow: ['warn', 'error'] }],
    'no-debugger': 'warn',
    'no-alert': 'warn',
    'prefer-const': 'error',
    'no-var': 'error',
    'eqeqeq': ['error', 'always'],
    'curly': ['error', 'all'],
    'no-multiple-empty-lines': ['error', { max: 1 }],
    'no-trailing-spaces': 'error',
    'comma-dangle': ['error', 'always-multiline'],
    'semi': ['error', 'always'],
    'quotes': ['error', 'single', { avoidEscape: true }],
    'object-curly-spacing': ['error', 'always'],
    'array-bracket-spacing': ['error', 'never'],
  },
  overrides: [
    {
      // Test files
      files: ['**/*.test.ts', '**/*.test.tsx', '**/*.spec.ts', '**/*.spec.tsx'],
      env: {
        jest: true,
      },
      extends: ['plugin:testing-library/react'],
      rules: {
        '@typescript-eslint/no-explicit-any': 'off',
        'no-console': 'off',
      },
    },
    {
      // Config files
      files: ['*.config.ts', '*.config.js', '*.config.cjs'],
      rules: {
        '@typescript-eslint/no-var-requires': 'off',
        'import/no-default-export': 'off',
      },
    },
    {
      // Generated/utility files with legacy typing or console usage
      files: [
        'src/api.ts',
        'src/utils/touchUtils.ts',
        'src/utils/webVitals.ts',
        'src/utils/wcagValidator.ts',
        'src/types/api.generated.ts',
      ],
      rules: {
        '@typescript-eslint/no-explicit-any': 'off',
        'no-console': 'off',
      },
    },
    {
      // Test setup files
      files: ['tests/setup.ts'],
      rules: {
        '@typescript-eslint/no-explicit-any': 'off',
      },
    },
  ],
  ignorePatterns: [
    'dist',
    'build',
    'node_modules',
    '*.min.js',
    'coverage',
    '.eslintrc.cjs',
    'vite.config.ts',
  ],
};
