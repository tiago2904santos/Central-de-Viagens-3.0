(function () {
  "use strict";

  var STORAGE_KEY = "cv-theme";
  var VALID_THEMES = ["dark", "light"];
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

  function getStoredTheme() {
    try {
      var saved = localStorage.getItem(STORAGE_KEY);
      return normalizeTheme(saved);
    } catch (e) {}
    return normalizeTheme(null);
  }

  function applyTheme(theme) {
    if (VALID_THEMES.indexOf(theme) < 0) {
      theme = "dark";
    }
    document.documentElement.setAttribute("data-theme", theme);
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch (e) {}

    document.querySelectorAll("[data-theme-mode]").forEach(function (btn) {
      var mode = btn.getAttribute("data-theme-mode");
      var pressed = mode === theme;
      btn.setAttribute("aria-pressed", pressed ? "true" : "false");
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    var initial = getStoredTheme();
    applyTheme(initial);
    try {
      if (localStorage.getItem(STORAGE_KEY) === null) {
        localStorage.setItem(STORAGE_KEY, initial);
      } else {
        var raw = localStorage.getItem(STORAGE_KEY);
        if (normalizeTheme(raw) !== raw) {
          localStorage.setItem(STORAGE_KEY, initial);
        }
      }
    } catch (e) {}

    document.querySelectorAll("[data-theme-mode]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var mode = btn.getAttribute("data-theme-mode");
        if (VALID_THEMES.indexOf(mode) >= 0) {
          applyTheme(mode);
        }
      });
    });
  });
})();
