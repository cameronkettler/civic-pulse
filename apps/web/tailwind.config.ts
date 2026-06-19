import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#172026",
        panel: "#f7f8fa",
        line: "#d7dde3",
        signal: "#0f766e",
        civic: "#235789",
        alert: "#b45309"
      }
    }
  },
  plugins: []
};

export default config;
