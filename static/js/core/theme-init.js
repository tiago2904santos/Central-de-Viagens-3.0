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
    if (raw === "light" || raw === "light-light") return "light";
    if (raw === "dark" || raw === "dark-dark" || raw === "dark-light" || raw === "light-dark") return "dark";
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function getInitialTheme() {
    try {
      var saved = localStorage.getItem(STORAGE_KEY);
      return normalizeTheme(saved);
    } catch (e) {}
    return normalizeTheme(null);
  }

  var theme = getInitialTheme();
  document.documentElement.setAttribute("data-theme", theme);
  try {
    localStorage.setItem(STORAGE_KEY, theme);
  } catch (e) {}
})();
