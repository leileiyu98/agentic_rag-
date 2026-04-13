/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Apple Design System Colors
        'apple-bg': '#F5F5F7',
        'apple-surface': '#FFFFFF',
        'apple-text': '#1D1D1F',
        'apple-text-secondary': '#86868B',
        'apple-blue': '#007AFF',
        'apple-blue-light': '#E8F4FF',
        'apple-border': '#E5E5E7',
        'apple-gray': '#F2F2F7',
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'SF Pro Display', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      borderRadius: {
        'apple': '10px',
        'apple-lg': '16px',
        'apple-xl': '20px',
      },
      boxShadow: {
        'apple': '0 2px 12px rgba(0, 0, 0, 0.08)',
        'apple-lg': '0 4px 24px rgba(0, 0, 0, 0.12)',
      },
    },
  },
  plugins: [],
}
