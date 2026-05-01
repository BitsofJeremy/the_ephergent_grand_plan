export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        'bg-deep': '#08080d',
        'bg-surface': '#121219',
        'bg-elevated': '#1c1c28',
        'text-primary': '#e8e8f0',
        'text-secondary': '#9090b0',
        'border-subtle': '#2a2a3a',
        'accent-cyan': '#00d4ff',
        'accent-amber': '#ffb020',
        'accent-magenta': '#e040fb',
        'accent-pink': '#F12CA5',
        'accent-green': '#00e676',
      },
      fontFamily: {
        display: ['Space Grotesk', 'Inter', 'system-ui', 'sans-serif'],
        body: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
};
