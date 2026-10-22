// LRH Console interactive mode: applies a stored in-page theme before first
// paint, so pages do not flash in the wrong theme. A server-pinned theme
// (--theme light|dark) already sets data-theme and always wins. The main
// script, lrh-interactive.js, owns the switch itself.
(function () {
  "use strict";
  const root = document.documentElement;
  if (root.hasAttribute("data-theme")) return;
  try {
    const choice = window.localStorage.getItem("lrh-console-theme");
    if (choice === "light" || choice === "dark") {
      root.setAttribute("data-theme", choice);
      root.setAttribute("data-lrh-theme-source", "browser");
    }
  } catch (_error) {
    // Storage can be unavailable; the page then follows the system theme.
  }
})();
