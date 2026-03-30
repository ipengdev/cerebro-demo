import frappeUIPreset from 'frappe-ui/tailwind'

export default {
  darkMode: ['selector', '[data-theme="dark"]'],
  presets: [frappeUIPreset],
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
    './node_modules/frappe-ui/src/**/*.{vue,js,ts,jsx,tsx}',
    '../node_modules/frappe-ui/src/**/*.{vue,js,ts,jsx,tsx}',
    './node_modules/frappe-ui/frappe/**/*.{vue,js,ts,jsx,tsx}',
    '../node_modules/frappe-ui/frappe/**/*.{vue,js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        brand: {
          50: '#fdf2f4',
          100: '#fce7ec',
          200: '#f9d0da',
          300: '#f4a9bc',
          400: '#ec7596',
          500: '#d94a72',
          600: '#a62952',
          700: '#8b2346',
          800: '#6e1d39',
          900: '#5a1a31',
        },
      },
    },
  },
  plugins: [],
}
