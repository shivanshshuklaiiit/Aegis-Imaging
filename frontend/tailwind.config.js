/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        aegis: {
          ink: "#0B1F33", // deepest, for high-contrast headings
          navy: "#0F2A47", // primary brand
          blue: "#2E5C8A", // secondary
          signal: "#06B6D4", // cyan accent — "scanning / active / verified"
          slate: "#475569",
          muted: "#64748B",
          bg: "#F5F7FB",
          card: "#FFFFFF",
          approve: "#16A34A",
          reject: "#DC2626",
          escalate: "#D97706",
          border: "#E6EBF1",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      maxWidth: {
        content: "1240px",
      },
      letterSpacing: {
        tightest: "-0.04em",
      },
      boxShadow: {
        card: "0 1px 2px rgba(15,42,71,0.04), 0 6px 20px -8px rgba(15,42,71,0.10)",
        lift: "0 16px 40px -12px rgba(15,42,71,0.22)",
        glow: "0 0 0 1px rgba(6,182,212,0.4), 0 0 24px -2px rgba(6,182,212,0.35)",
        innerline: "inset 0 1px 0 0 rgba(255,255,255,0.6)",
      },
      backgroundImage: {
        "grid-fade":
          "linear-gradient(to right, rgba(15,42,71,0.04) 1px, transparent 1px), linear-gradient(to bottom, rgba(15,42,71,0.04) 1px, transparent 1px)",
        "navy-sheen":
          "radial-gradient(120% 120% at 0% 0%, #143456 0%, #0F2A47 45%, #0B1F33 100%)",
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "pulse-ring": {
          "0%, 100%": { opacity: "1", transform: "scale(1)" },
          "50%": { opacity: "0.45", transform: "scale(1.015)" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
        "scan-y": {
          "0%": { top: "0%", opacity: "0" },
          "10%": { opacity: "1" },
          "90%": { opacity: "1" },
          "100%": { top: "100%", opacity: "0" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-6px)" },
        },
        "spin-slow": {
          to: { transform: "rotate(360deg)" },
        },
        "dash": {
          to: { "stroke-dashoffset": "0" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.5s cubic-bezier(0.22,1,0.36,1) both",
        "pulse-ring": "pulse-ring 1.6s ease-in-out infinite",
        shimmer: "shimmer 1.8s infinite",
        "scan-y": "scan-y 2.4s cubic-bezier(0.45,0,0.55,1) infinite",
        float: "float 6s ease-in-out infinite",
        "spin-slow": "spin-slow 14s linear infinite",
      },
    },
  },
  plugins: [],
};
