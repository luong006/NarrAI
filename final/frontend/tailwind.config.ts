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
        // Warm, editorial palette with high contrast for interactive controls.
        brand: {
          50: '#F7F2EC',
          100: '#EEE4D7',
          200: '#DDC9B5',
          300: '#C9AA8F',
          400: '#B78969',
          500: '#9F684A',
          600: '#89553D',
          700: '#704331',
          800: '#573528',
          900: '#3F281F',
        },
        paper: {
          light: '#FAF8F5',
          dark: '#211D19',
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
