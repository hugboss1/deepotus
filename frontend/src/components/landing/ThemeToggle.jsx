import React from "react";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "@/theme/ThemeProvider";

export default function ThemeToggle({ className = "" }) {
  const { theme, toggle } = useTheme();
  const isDark = theme === "dark";
  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      data-testid="theme-toggle"
      title={isDark ? "Light mode" : "Dark mode"}
      className={`inline-flex items-center justify-center h-9 w-9 rounded-[var(--btn-radius)] border border-border bg-background/80 backdrop-blur hover:bg-secondary transition-colors ${className}`}
    >
      {isDark ? (
        <Sun size={16} className="text-foreground" />
      ) : (
        <Moon size={16} className="text-foreground" />
      )}
    </button>
  );
}
