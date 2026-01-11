/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'safety-yellow': '#DC3C8C', // Muted magenta
        'safety-orange': '#DC3C8C', // Muted magenta (main brand color)
        'safety-orange-dark': '#B0307A', // Darker muted magenta
        'safety-black': '#000000',
        'safety-gray': '#1A1A1A',
        'safety-gray-light': '#2A2A2A',
      },
    },
  },
  plugins: [],
}
