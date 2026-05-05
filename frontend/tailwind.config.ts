import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "IBM Plex Sans",
          "ui-sans-serif",
          "system-ui",
          "sans-serif",
        ],
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
      },
      colors: {
        caly: {
          void: "#050508",
          matte: "#0c0c10",
          graphite: "#14141a",
          charcoal: "#1a1a22",
          mist: "#e8e8ec",
          dim: "#9898a4",
        },
        spectral: {
          rose: "#ff6b9d",
          amber: "#ffb84d",
          lime: "#c4f042",
          cyan: "#4dfff0",
          blue: "#6b8cff",
          violet: "#a78bfa",
        },
      },
      backgroundImage: {
        "grid-science":
          "linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)",
        "spectral-glow":
          "radial-gradient(ellipse 80% 50% at 50% -20%, rgba(167,139,250,0.12), transparent 55%), radial-gradient(ellipse 60% 40% at 100% 50%, rgba(77,255,240,0.06), transparent 50%), radial-gradient(ellipse 50% 30% at 0% 80%, rgba(255,107,157,0.05), transparent 45%)",
      },
      boxShadow: {
        spectral:
          "0 0 0 1px rgba(255,255,255,0.06), 0 0 40px -12px rgba(167,139,250,0.15)",
        "spectral-inset": "inset 0 1px 0 rgba(255,255,255,0.04)",
      },
      animation: {
        "shimmer-slow": "shimmer 8s ease-in-out infinite",
      },
      keyframes: {
        shimmer: {
          "0%, 100%": { opacity: "0.4" },
          "50%": { opacity: "0.85" },
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
