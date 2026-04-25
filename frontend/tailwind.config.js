/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: '#FBFBF9',
        surface: '#FFFFFF',
        primary: '#0A3224',
        'primary-hover': '#0F4C3A',
        accent: '#D4AF37',
        'accent-hover': '#B3932E',
        'text-primary': '#1A1D1C',
        'text-secondary': '#4A5550',
        border: '#E2E6E4',
      },
      fontFamily: {
        heading: ['Cabinet Grotesk', 'sans-serif'],
        body: ['Manrope', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
