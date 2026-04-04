/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        deal: {
          good: '#22c55e',
          great: '#f59e0b',
          insane: '#ef4444',
          error: '#dc2626',
        },
        score: {
          low: '#6b7280',
          mid: '#eab308',
          high: '#22c55e',
          max: '#ef4444',
        },
      },
      animation: {
        'slide-in': 'slideIn 0.3s ease-out',
        'pulse-slow': 'pulse 3s infinite',
      },
      keyframes: {
        slideIn: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
