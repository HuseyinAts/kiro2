/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // ============================================
      // MODERN COLOR SYSTEM
      // ============================================
      colors: {
        // KIRO2 Primary Brand Colors
        'kiro-primary': {
          50: '#F0F4FF',
          100: '#E0EAFF',
          200: '#C7D7FE',
          300: '#A5BBFC',
          400: '#8B9FF9',
          500: '#667EEA',
          600: '#5568D3',
          700: '#4453B8',
          800: '#3A4199',
          900: '#2D3282',
        },
        // KIRO2 Secondary Colors
        'kiro-secondary': {
          50: '#FAF5FF',
          100: '#F3E8FF',
          200: '#E9D5FF',
          300: '#D8B4FE',
          400: '#C084FC',
          500: '#A855F7',
          600: '#9333EA',
          700: '#7E22CE',
          800: '#6B21A8',
          900: '#581C87',
        },
        // Accent Colors
        'kiro-accent-cyan': '#06B6D4',
        'kiro-accent-teal': '#14B8A6',
        'kiro-accent-pink': '#EC4899',
        'kiro-accent-orange': '#F97316',
        'kiro-accent-emerald': '#10B981',

        // ============================================
        // GAMIFICATION — Realm / Subject Colors
        // ============================================
        'realm': {
          'fizik':    { DEFAULT: '#3B82F6', light: '#DBEAFE', dark: '#1D4ED8' }, // mavi
          'kimya':    { DEFAULT: '#10B981', light: '#D1FAE5', dark: '#047857' }, // yesil
          'biyoloji': { DEFAULT: '#22C55E', light: '#DCFCE7', dark: '#15803D' }, // acik yesil
          'matematik':{ DEFAULT: '#F59E0B', light: '#FEF3C7', dark: '#B45309' }, // amber
          'geometri': { DEFAULT: '#EF4444', light: '#FEE2E2', dark: '#B91C1C' }, // kirmizi
          'cografya': { DEFAULT: '#06B6D4', light: '#CFFAFE', dark: '#0E7490' }, // cyan
          'tarih':    { DEFAULT: '#D97706', light: '#FDE68A', dark: '#92400E' }, // turuncu-kahve
          'edebiyat': { DEFAULT: '#8B5CF6', light: '#EDE9FE', dark: '#6D28D9' }, // mor
          'turkce':   { DEFAULT: '#EC4899', light: '#FCE7F3', dark: '#BE185D' }, // pembe
          'felsefe':  { DEFAULT: '#6366F1', light: '#E0E7FF', dark: '#4338CA' }, // indigo
          'din':      { DEFAULT: '#14B8A6', light: '#CCFBF1', dark: '#0F766E' }, // teal
          'oba':      { DEFAULT: '#A855F7', light: '#F3E8FF', dark: '#7E22CE' }, // violet
        },

        // ============================================
        // GAMIFICATION — XP / Streak / League
        // ============================================
        'xp': {
          'start':  '#667EEA',
          'mid':    '#A855F7',
          'end':    '#EC4899',
          'text':   '#7C3AED',
          'bg':     '#EDE9FE',
        },
        'streak': {
          'fire':   '#F97316',
          'hot':    '#EF4444',
          'cool':   '#3B82F6',
          'bg':     '#FFF7ED',
          'text':   '#C2410C',
        },
        'league': {
          'bronz':  '#92400E',
          'silver': '#6B7280',
          'gold':   '#D97706',
          'platin': '#0E7490',
          'elmas':  '#7C3AED',
        },
        'badge': {
          'common':   '#6B7280',
          'rare':     '#3B82F6',
          'epic':     '#8B5CF6',
          'legendary':'#F59E0B',
        },
      },

      // ============================================
      // MODERN SHADOWS
      // ============================================
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
        'modern': '0 10px 40px -10px rgba(0,0,0,0.2)',
        'modern-lg': '0 20px 60px -15px rgba(0,0,0,0.3)',
        'modern-xl': '0 30px 80px -20px rgba(0,0,0,0.35)',
        'glow': '0 0 20px rgba(102, 126, 234, 0.4)',
        'glow-lg': '0 0 40px rgba(102, 126, 234, 0.5)',
      },

      // ============================================
      // MODERN BORDER RADIUS
      // ============================================
      borderRadius: {
        'xl': '1rem',
        '2xl': '1.5rem',
        '3xl': '2rem',
        '4xl': '2.5rem',
      },

      // ============================================
      // GLASSMORPHISM BACKDROP BLUR
      // ============================================
      backdropBlur: {
        'xs': '2px',
        'glass': '16px',
      },

      // ============================================
      // MODERN SPACING (extends default)
      // ============================================
      spacing: {
        '18': '4.5rem',
        '22': '5.5rem',
        '26': '6.5rem',
        '30': '7.5rem',
      },

      // ============================================
      // MODERN ANIMATIONS
      // ============================================
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'fade-in-up': 'fadeInUp 0.5s ease-out',
        'fade-in-down': 'fadeInDown 0.5s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'slide-down': 'slideDown 0.4s ease-out',
        'slide-left': 'slideLeft 0.4s ease-out',
        'slide-right': 'slideRight 0.4s ease-out',
        'scale-in': 'scaleIn 0.3s ease-out',
        'scale-out': 'scaleOut 0.3s ease-out',
        'bounce-in': 'bounceIn 0.6s ease-out',
        'float': 'float 3s ease-in-out infinite',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 3s linear infinite',
        'wiggle': 'wiggle 1s ease-in-out infinite',
        // Gamification animations
        'xp-fill': 'xpFill 0.8s cubic-bezier(0.22, 1, 0.36, 1) forwards',
        'badge-pop': 'badgePop 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55) forwards',
        'streak-burn': 'streakBurn 1.5s ease-in-out infinite',
        'level-up': 'levelUp 0.6s cubic-bezier(0.22, 1, 0.36, 1) forwards',
        'confetti-fall': 'confettiFall 1.2s ease-in forwards',
        'ping-once': 'pingOnce 0.6s ease-out forwards',
      },

      // ============================================
      // KEYFRAME ANIMATIONS
      // ============================================
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeInDown: {
          '0%': { opacity: '0', transform: 'translateY(-20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideUp: {
          '0%': { transform: 'translateY(100%)' },
          '100%': { transform: 'translateY(0)' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(0)' },
        },
        slideLeft: {
          '0%': { transform: 'translateX(100%)' },
          '100%': { transform: 'translateX(0)' },
        },
        slideRight: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.9)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        scaleOut: {
          '0%': { opacity: '1', transform: 'scale(1)' },
          '100%': { opacity: '0', transform: 'scale(0.9)' },
        },
        bounceIn: {
          '0%': { opacity: '0', transform: 'scale(0.3)' },
          '50%': { opacity: '1', transform: 'scale(1.05)' },
          '70%': { transform: 'scale(0.9)' },
          '100%': { transform: 'scale(1)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        wiggle: {
          '0%, 100%': { transform: 'rotate(-3deg)' },
          '50%': { transform: 'rotate(3deg)' },
        },
        // Gamification keyframes
        xpFill: {
          '0%': { width: '0%' },
          '100%': { width: 'var(--xp-percent)' },
        },
        badgePop: {
          '0%': { opacity: '0', transform: 'scale(0) rotate(-10deg)' },
          '70%': { opacity: '1', transform: 'scale(1.15) rotate(3deg)' },
          '100%': { opacity: '1', transform: 'scale(1) rotate(0deg)' },
        },
        streakBurn: {
          '0%, 100%': { filter: 'brightness(1) saturate(1)', transform: 'scale(1)' },
          '50%': { filter: 'brightness(1.2) saturate(1.5)', transform: 'scale(1.08)' },
        },
        levelUp: {
          '0%': { opacity: '0', transform: 'scale(0.5) translateY(20px)' },
          '60%': { opacity: '1', transform: 'scale(1.1) translateY(-5px)' },
          '100%': { opacity: '1', transform: 'scale(1) translateY(0)' },
        },
        confettiFall: {
          '0%': { opacity: '1', transform: 'translateY(-20px) rotate(0deg)' },
          '100%': { opacity: '0', transform: 'translateY(80px) rotate(360deg)' },
        },
        pingOnce: {
          '0%': { transform: 'scale(1)', opacity: '1' },
          '75%': { transform: 'scale(2)', opacity: '0' },
          '100%': { transform: 'scale(2)', opacity: '0' },
        },
      },

      // ============================================
      // MODERN GRADIENTS (via background-image)
      // ============================================
      backgroundImage: {
        'gradient-primary': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'gradient-sunset': 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
        'gradient-ocean': 'linear-gradient(135deg, #2193b0 0%, #6dd5ed 100%)',
        'gradient-forest': 'linear-gradient(135deg, #134e5e 0%, #71b280 100%)',
        'gradient-fire': 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
        'gradient-aurora': 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
        'gradient-radial': 'radial-gradient(circle, var(--tw-gradient-stops))',
        // Gamification gradients
        'gradient-xp': 'linear-gradient(90deg, #667EEA 0%, #A855F7 50%, #EC4899 100%)',
        'gradient-streak': 'linear-gradient(135deg, #F97316 0%, #EF4444 100%)',
        'gradient-league-gold': 'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)',
        'gradient-realm-fizik': 'linear-gradient(135deg, #DBEAFE 0%, #3B82F6 100%)',
        'gradient-realm-matematik': 'linear-gradient(135deg, #FEF3C7 0%, #F59E0B 100%)',
        'gradient-realm-edebiyat': 'linear-gradient(135deg, #EDE9FE 0%, #8B5CF6 100%)',
      },

      // ============================================
      // MODERN FONT FAMILY
      // ============================================
      fontFamily: {
        'sans': ['Plus Jakarta Sans', 'Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        'display': ['Plus Jakarta Sans', 'Poppins', 'Inter', 'system-ui', 'sans-serif'],
        'mono': ['JetBrains Mono', 'Fira Code', 'Courier New', 'monospace'],
        'inter': ['Inter', 'system-ui', 'sans-serif'],
      },

      // ============================================
      // MODERN Z-INDEX SCALE
      // ============================================
      zIndex: {
        '-1': '-1',
        '0': '0',
        '10': '10',
        '20': '20',
        '30': '30',
        '40': '40',
        '50': '50',
        '100': '100',
        '999': '999',
        '9999': '9999',
      },

      // ============================================
      // MODERN TRANSITION
      // ============================================
      transitionDuration: {
        '0': '0ms',
        '250': '250ms',
        '350': '350ms',
        '400': '400ms',
        '600': '600ms',
        '800': '800ms',
        '1200': '1200ms',
      },

      transitionTimingFunction: {
        'bounce': 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
        'smooth': 'cubic-bezier(0.4, 0, 0.2, 1)',
      },
    },
  },
  plugins: [
    // tailwindcss-animate for smooth enter/exit animations
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    require('tailwindcss-animate'),
  ],
}