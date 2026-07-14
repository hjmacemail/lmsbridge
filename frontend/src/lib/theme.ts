// Light/dark theme: defaults to the OS preference, remembers the user's explicit choice.
export type Theme = "light" | "dark";
const KEY = "lmsb_theme";

export function initTheme(): Theme {
  let t = localStorage.getItem(KEY) as Theme | null;
  if (t !== "light" && t !== "dark") {
    t = typeof window !== "undefined" && window.matchMedia
      && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  document.documentElement.dataset.theme = t;
  return t;
}

export function setTheme(t: Theme): void {
  localStorage.setItem(KEY, t);
  document.documentElement.dataset.theme = t;
}

export function currentTheme(): Theme {
  return (document.documentElement.dataset.theme as Theme) || "light";
}
