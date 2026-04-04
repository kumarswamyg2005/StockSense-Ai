/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          500: '#22d3ee',
          600: '#0891b2'
        }
      },
      keyframes: {
        fadeInY: {
          '0%': { opacity: '0', transform: 'translateY(40px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        }
      },
      animation: {
        'fadeInY': 'fadeInY 0.5s ease-out forwards'
      }
    }
  },
  plugins: []
};
