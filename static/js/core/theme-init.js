(function () {
  "use strict";

  var VALID_THEMES = ["dark", "light"];
  var STORAGE_KEY = "cv-theme";
  var THEME_ALIASES = {
    "dark-dark": "dark",
    "light-dark": "dark",
    "dark-light": "dark",
    "light-light": "light",
    dark: "dark",
    light: "light",
    "variant-a": "dark",
    "variant-b": "light",
  };

  function normalizeTheme(raw) {
    return THEME_ALIASES[raw] || null;
  }

  function getInitialTheme() {
    try {
      var saved = localStorage.getItem(STORAGE_KEY);
      var normalized = normalizeTheme(saved);
      if (normalized) return normalized;
    } catch (e) {}

    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function toDomTheme(theme) {
    return theme === "light" ? "light-light" : "dark-dark";
  }

  var theme = getInitialTheme();
  document.documentElement.setAttribute("data-theme", toDomTheme(theme));
  try {
    localStorage.setItem(STORAGE_KEY, theme);
  } catch (e) {}
})();
