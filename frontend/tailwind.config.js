/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'safety-yellow': '#F9C74F',
        'safety-orange': '#DAA520',
        'safety-orange-dark': '#B8860B',
        'safety-black': '#000000',
        'safety-gray': '#1A1A1A',
        'safety-gray-light': '#2A2A2A',
      },
    },
  },
  plugins: [],
}
