/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./pages/**/*.{js,jsx}", "./components/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink:   { DEFAULT: "#12151C", soft: "#3A4152", mute: "#767E92" },
        paper: { DEFAULT: "#F4F5F7", raised: "#FFFFFF", sunk: "#EBEDF1" },
        line:  { DEFAULT: "#E1E4EA", strong: "#C9CED8" },
        // One hue per agent. Agent identity is the core concept of this system,
        // so colour encodes it rather than decorating with it.
        billing:   "#B45309",
        technical: "#0E7490",
        product:   "#6D28D9",
        complaint: "#BE123C",
        faq:       "#475569",
      },
      fontFamily: {
        display: ["'Bricolage Grotesque'", "system-ui", "sans-serif"],
        sans: ["'IBM Plex Sans'", "system-ui", "sans-serif"],
        mono: ["'IBM Plex Mono'", "ui-monospace", "monospace"],
      },
      keyframes: {
        rise: { "0%": { opacity: 0, transform: "translateY(6px)" },
                "100%": { opacity: 1, transform: "translateY(0)" } },
        blink: { "0%,80%,100%": { opacity: 0.25 }, "40%": { opacity: 1 } },
      },
      animation: {
        rise: "rise 220ms ease-out both",
        blink: "blink 1.2s infinite",
      },
    },
  },
  plugins: [],
};
