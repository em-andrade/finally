import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}', './lib/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        base: {
          900: '#0d1117',
          800: '#1a1a2e',
          700: '#20233a',
          600: '#2a2e47',
        },
        border: {
          DEFAULT: '#30364a',
        },
        accent: {
          yellow: '#ecad0a',
          blue: '#209dd7',
          purple: '#753991',
        },
        up: '#22c55e',
        down: '#ef4444',
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace'],
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      keyframes: {
        'flash-up': {
          '0%': { backgroundColor: 'rgba(34, 197, 94, 0.45)' },
          '100%': { backgroundColor: 'transparent' },
        },
        'flash-down': {
          '0%': { backgroundColor: 'rgba(239, 68, 68, 0.45)' },
          '100%': { backgroundColor: 'transparent' },
        },
      },
      animation: {
        'flash-up': 'flash-up 500ms ease-out',
        'flash-down': 'flash-down 500ms ease-out',
      },
    },
  },
  plugins: [],
};

export default config;
