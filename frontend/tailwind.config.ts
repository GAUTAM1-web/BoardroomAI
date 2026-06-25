import type { Config } from "tailwindcss";
import animate from "tailwindcss-animate";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
    "./store/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        board: {
          ink: "#07090d",
          panel: "#11151b",
          line: "#27313d",
          mist: "#d7dee8",
          muted: "#8b98a9",
          teal: "#38d6c6",
          amber: "#f6c85f",
          rose: "#e66f7f",
          violet: "#9f8cff"
        }
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(255,255,255,0.08), 0 24px 80px rgba(0,0,0,0.45)"
      }
    }
  },
  plugins: [animate]
};

export default config;

