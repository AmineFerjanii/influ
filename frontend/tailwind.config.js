/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#e8f7fd',
          100: '#c4eaf8',
          300: '#6dcbee',
          500: '#29ABE2',
          600: '#1a95cc',
          700: '#0f7aaa',
        },
        ealan: {
          bg:      '#07090F',
          surface: '#0D1117',
          card:    '#101620',
          border:  '#1A2035',
          hover:   '#1E2640',
        },
      },
    },
  },
  plugins: [],
}
