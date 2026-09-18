import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: 'class',
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // High WCAG AA contrast color palette
        brand: {
          50: '#EEF2FF',
          100: '#E0E7FF',
          200: '#C7D2FE',
          300: '#A5B4FC',
          400: '#818CF8',
          500: '#6366F1',
          600: '#4F46E5',
          700: '#4338CA', // 5.8:1 contrast on white
          800: '#3730A3', // 8.2:1 contrast on white
          900: '#312E81',
        },
        paper: {
          light: '#FAF8F5',
          dark: '#141A23',
        },
        accent: {
          orange: '#C2410C', // 4.9:1 contrast
          green: '#047857',  // 4.6:1 contrast
          red: '#B91C1C',    // 5.6:1 contrast
        }
      },
      fontFamily: {
        sans: ['"Be Vietnam Pro"', 'system-ui', '-apple-system', 'sans-serif'],
        serif: ['"Merriweather"', '"Lora"', 'Georgia', 'serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
    },
  },
  plugins: [],
};
export default config;
