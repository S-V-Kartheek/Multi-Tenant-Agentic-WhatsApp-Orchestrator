/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Design system tokens
        surface: {
          DEFAULT: '#0A0F1E',   // deep navy background
          card:    '#111827',   // card surface
          elevated: '#1A2235',  // elevated elements
          border:  '#1F2937',   // subtle borders
        },
        brand: {
          primary:   '#6366F1',  // indigo — primary accent
          secondary: '#8B5CF6',  // violet — secondary
          glow:      '#818CF8',  // lighter for glow effects
        },
        status: {
          waiting:  '#F59E0B',  // amber
          typing:   '#3B82F6',  // blue
          resolved: '#10B981',  // emerald
          human:    '#EF4444',  // red
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'fade-in':      'fadeIn 0.3s ease-in-out',
        'slide-up':     'slideUp 0.3s ease-out',
        'slide-right':  'slideRight 0.35s ease-out',
        'pulse-dot':    'pulseDot 1.4s ease-in-out infinite',
        'glow':         'glowPulse 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%':   { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideRight: {
          '0%':   { opacity: '0', transform: 'translateX(100%)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        pulseDot: {
          '0%, 80%, 100%': { transform: 'scale(0.6)', opacity: '0.3' },
          '40%':           { transform: 'scale(1)',   opacity: '1' },
        },
        glowPulse: {
          '0%, 100%': { boxShadow: '0 0 8px rgba(99, 102, 241, 0.3)' },
          '50%':      { boxShadow: '0 0 20px rgba(99, 102, 241, 0.6)' },
        },
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}
