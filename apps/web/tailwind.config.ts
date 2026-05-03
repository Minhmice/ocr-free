import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        mineru: {
          bg: "#0b1220",
          panel: "#111a2e",
          border: "#1f2a44",
          accent: "#3b82f6",
          muted: "#94a3b8",
        },
      },
    },
  },
  plugins: [],
};

export default config;
