export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        wonder: {
          lime: '#d9ff00',
          black: '#000000',
          accent: '#00f2ff',
          gray: {
            900: '#0a0a0a',
            800: '#121212',
            700: '#1a1a1a',
            600: '#222222',
          }
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Outfit', 'Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'orb-float': 'float 10s ease-in-out infinite',
        'fade-in': 'fadeIn 0.5s ease-out forwards',
        'shimmer': 'shimmer 2s linear infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0) scale(1)' },
          '50%': { transform: 'translateY(-20px) scale(1.05)' },
        },
        fadeIn: {
          from: { opacity: '0', transform: 'translateY(10px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        }
      }
    },
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: [
      {
        wonder: {
          "primary": "#d9ff00",
          "secondary": "#ffffff",
          "accent": "#00f2ff",
          "neutral": "#1a1a1a",
          "base-100": "#000000",
          "info": "#3abff8",
          "success": "#36d399",
          "warning": "#fbbd23",
          "error": "#f87272",
          "--rounded-btn": "0.5rem",
          "--rounded-box": "1rem",
        },
      },
      "dark",
    ],
  },
}
