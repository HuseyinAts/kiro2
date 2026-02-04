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
      },

      // ============================================
      // MODERN FONT FAMILY
      // ============================================
      fontFamily: {
        'sans': ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        'display': ['Poppins', 'Inter', 'system-ui', 'sans-serif'],
        'mono': ['Fira Code', 'Courier New', 'monospace'],
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
  plugins: [],
}