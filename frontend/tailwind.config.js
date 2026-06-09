/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
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
          surface: '#0C1018',
          card:    '#0F1420',
          border:  '#1C2638',
          hover:   '#19223A',
          muted:   '#64748B',
        },
      },
      boxShadow: {
        card: '0 1px 3px rgba(0,0,0,0.4)',
        'card-hover': '0 0 0 1px rgba(41,171,226,0.3), 0 4px 24px rgba(41,171,226,0.07)',
        modal: '0 25px 60px rgba(0,0,0,0.7)',
      },
      keyframes: {
        'slide-up': { from: { transform: 'translateY(100%)' }, to: { transform: 'translateY(0)' } },
        'slide-in-left': { from: { transform: 'translateX(-100%)' }, to: { transform: 'translateX(0)' } },
        'fade-in': { from: { opacity: '0' }, to: { opacity: '1' } },
      },
      animation: {
        'slide-up': 'slide-up 0.28s cubic-bezier(0.32,0.72,0,1)',
        'slide-in-left': 'slide-in-left 0.25s cubic-bezier(0.32,0.72,0,1)',
        'fade-in': 'fade-in 0.2s ease',
      },
    },
  },
  plugins: [],
}
