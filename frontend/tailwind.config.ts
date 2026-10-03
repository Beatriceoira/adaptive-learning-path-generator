import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#16302A",
        "ink-muted": "#55655C",
        paper: "#F4F6F1",
        panel: "#FFFFFF",
        line: "#DCE3D6",
        accent: "#D9A441",
        "accent-deep": "#B9832C",
        sage: "#4C7A63",
        "sage-deep": "#3B6650",
        rust: "#A5432E",
      },
      fontFamily: {
        display: ["var(--font-display)", "Georgia", "serif"],
        body: ["var(--font-body)", "system-ui", "sans-serif"],
      },
      borderRadius: {
        sm: "4px",
        md: "6px",
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};

export default config;
