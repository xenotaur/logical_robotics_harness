// LRH Console interactive mode: loaded only by `lrh serve --interactive`.
//
// Progressive enhancement over the static pages. Every behavior here also
// exists without scripts (links, ?item= selection, server-rendered drawers),
// so nothing breaks when this file is absent or blocked. It never fetches,
// never evaluates strings, and writes only one localStorage key.
(function () {
  "use strict";

  const root = document.documentElement;
  const THEME_KEY = "lrh-console-theme";
  // A server-pinned theme (--theme light|dark) arrives as data-theme on the
  // root element. lrh-theme-early.js may also have set it from storage, and
  // marks that with data-lrh-theme-source="browser".
  const pinned =
    root.hasAttribute("data-theme") &&
    root.getAttribute("data-lrh-theme-source") !== "browser";

  // ----- In-page theme switch (hidden when the server pins a theme) -----

  function readTheme() {
    try {
      return window.localStorage.getItem(THEME_KEY) || "system";
    } catch (_error) {
      return "system";
    }
  }

  function applyTheme(choice) {
    if (choice === "light" || choice === "dark") {
      root.setAttribute("data-theme", choice);
      root.setAttribute("data-lrh-theme-source", "browser");
    } else {
      root.removeAttribute("data-theme");
      root.removeAttribute("data-lrh-theme-source");
    }
  }

  function setupThemeSwitch() {
    const slot = document.querySelector("[data-lrh-theme-slot]");
    if (!slot || pinned) return;
    applyTheme(readTheme());
    const group = document.createElement("div");
    group.className = "lrh-theme-switch";
    group.setAttribute("role", "group");
    group.setAttribute("aria-label", "Theme");
    for (const [value, label] of [
      ["light", "Light"],
      ["dark", "Dark"],
      ["system", "System"],
    ]) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = label;
      button.dataset.theme = value;
      button.setAttribute("aria-pressed", String(readTheme() === value));
      button.addEventListener("click", () => {
        try {
          window.localStorage.setItem(THEME_KEY, value);
        } catch (_error) {
          // Storage can be unavailable; the choice still applies to this page.
        }
        applyTheme(value);
        for (const other of group.querySelectorAll("button")) {
          other.setAttribute("aria-pressed", String(other === button));
        }
      });
      group.append(button);
    }
    slot.append(group);
  }

  // ----- Dependency map: tracing, selection, filters -----

  function setupMap() {
    const map = document.querySelector(".lrh-dependency-map");
    if (!map) return;
    const lines = [...map.querySelectorAll("polyline[data-source]")];
    const needs = new Map();
    const neededBy = new Map();
    // Trace over every edge the server sends, not only the drawn lines: a
    // filter can hide an item in the middle of a chain.
    for (const [source, item] of readEdges(map, lines)) {
      if (!needs.has(item)) needs.set(item, new Set());
      if (!neededBy.has(source)) neededBy.set(source, new Set());
      needs.get(item).add(source);
      neededBy.get(source).add(item);
    }

    function walk(start, graph) {
      const seen = new Set();
      const stack = [start];
      while (stack.length) {
        for (const other of graph.get(stack.pop()) || []) {
          if (!seen.has(other) && other !== start) {
            seen.add(other);
            stack.push(other);
          }
        }
      }
      return seen;
    }

    function mark(selected, preview) {
      const up = selected ? walk(selected, needs) : new Set();
      const down = selected ? walk(selected, neededBy) : new Set();
      const related = new Set([...up, ...down]);
      if (selected) related.add(selected);
      for (const card of map.querySelectorAll(".lrh-card[data-id]")) {
        const id = card.dataset.id;
        // A hover or focus preview highlights, but never looks like a selection.
        const isSelected = !preview && id === selected;
        card.classList.toggle("lrh-card--selected", isSelected);
        card.classList.toggle("lrh-card--related", !preview && id !== selected && related.has(id));
        card.classList.toggle("lrh-card--preview", Boolean(preview && related.has(id)));
        const role = card.querySelector(".lrh-role");
        const text = isSelected
          ? "Selected"
          : up.has(id)
            ? "Upstream"
            : down.has(id)
              ? "Downstream"
              : "";
        if (role && !text) role.remove();
        if (text) {
          const label = role || document.createElement("span");
          label.className = "lrh-role";
          label.textContent = text;
          if (!role) card.querySelector(".lrh-card-top").append(label);
        }
      }
      for (const line of lines) {
        const on =
          Boolean(selected) && related.has(line.dataset.source) && related.has(line.dataset.item);
        line.classList.toggle("lrh-line--selected", on);
        line.setAttribute("marker-end", on ? "url(#lrh-arrow-selected)" : "url(#lrh-arrow)");
      }
    }

    // The card, table row, or list link that opens a drawer, for returning
    // focus when that drawer closes.
    function triggerFor(id) {
      for (const link of map.querySelectorAll("[data-id] a[href], a.lrh-card[data-id]")) {
        const owner = link.closest("[data-id]");
        if (owner && owner.dataset.id === id && link.offsetParent !== null) return link;
      }
      return null;
    }

    // True while focus returns to a card after its drawer closes, so that
    // focus does not count as a hover-or-focus preview.
    let restoringFocus = false;

    function showDrawer(id) {
      for (const drawer of document.querySelectorAll("[data-drawer-for]")) {
        const hide = drawer.dataset.drawerFor !== id;
        // Hiding the element that has focus would strand keyboard and
        // screen-reader users, so focus returns to what opened the drawer.
        if (hide && !drawer.hidden && drawer.contains(document.activeElement)) {
          const trigger = triggerFor(drawer.dataset.drawerFor);
          restoringFocus = true;
          if (trigger) trigger.focus();
          // A trigger that is filtered out or not displayed cannot take
          // focus; the map can, without scrolling the page to its top.
          if (!trigger || document.activeElement !== trigger) {
            map.setAttribute("tabindex", "-1");
            map.focus({ preventScroll: true });
          }
          restoringFocus = false;
        }
        drawer.hidden = hide;
      }
    }

    // Same-page links rendered with the old ?item= (tabs, Check for changes,
    // the top bar's Refresh, the filters) follow the new selection.
    function syncLinks(id) {
      const links = document.querySelectorAll(
        ".lrh-tabs a, .lrh-map-header a[href*='since='], .lrh-topbar a[href], " +
          ".lrh-filters a, .lrh-filter-note a",
      );
      for (const link of links) {
        const url = new URL(link.href, window.location.href);
        if (url.origin !== window.location.origin) continue;
        if (url.pathname !== window.location.pathname) continue;
        if (id) url.searchParams.set("item", id);
        else url.searchParams.delete("item");
        link.setAttribute("href", url.pathname + url.search);
      }
    }

    function currentSelection() {
      return new URLSearchParams(window.location.search).get("item");
    }

    function select(id) {
      const params = new URLSearchParams(window.location.search);
      if (id) params.set("item", id);
      else params.delete("item");
      const query = params.toString();
      window.history.replaceState(null, "", query ? `?${query}` : window.location.pathname);
      syncLinks(id);
      mark(id, false);
      showDrawer(id);
      const notice = map.querySelector("[data-lrh-unknown-item]");
      if (notice) notice.remove();
    }

    for (const card of map.querySelectorAll(".lrh-card[data-id]")) {
      const id = card.dataset.id;
      card.addEventListener("click", (event) => {
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        select(id);
      });
      const preview = () => {
        if (!currentSelection() && !restoringFocus) mark(id, true);
      };
      const clear = () => {
        if (!currentSelection()) mark(null, false);
      };
      card.addEventListener("mouseenter", preview);
      card.addEventListener("focus", preview);
      card.addEventListener("mouseleave", clear);
      card.addEventListener("blur", clear);
    }
    for (const close of document.querySelectorAll("[data-drawer-for] .lrh-iconbtn")) {
      close.addEventListener("click", (event) => {
        event.preventDefault();
        select(null);
      });
    }
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && currentSelection()) select(null);
    });

    // Filters reload the page (the server lays the map out again without the
    // hidden cards), so bring the selection back into view after a reload:
    // its card on the map, or its entry in the list on a narrow screen.
    const chosen = currentSelection();
    if (chosen) {
      for (const item of map.querySelectorAll(".lrh-card[data-id], .lrh-map-list [data-id]")) {
        if (item.dataset.id === chosen && item.offsetParent !== null) {
          item.scrollIntoView({ block: "center", inline: "center" });
          break;
        }
      }
    }
  }

  // data-edges is a JSON list of [prerequisite, item] pairs; IDs may contain
  // spaces. Without it, fall back to the drawn lines.
  function readEdges(map, lines) {
    const holder = map.querySelector("[data-edges]");
    if (holder) {
      try {
        const value = JSON.parse(holder.dataset.edges);
        if (Array.isArray(value)) {
          return value
            .filter((pair) => Array.isArray(pair) && pair.length === 2)
            .map(([source, item]) => [String(source), String(item)]);
        }
      } catch (_error) {
        // Fall through to the lines.
      }
    }
    return lines.map((line) => [line.dataset.source, line.dataset.item]);
  }

  // ----- Loading indication for slow navigations -----

  // Same-origin page loads can take a moment while the server reads project
  // files. After a short delay, dim the page and say it is loading, so a slow
  // click never looks like a stalled app. Links that open elsewhere,
  // downloads, and in-page selections never trigger it.
  const LOADING_DELAY_MS = 300;

  function setupLoading() {
    const overlay = document.createElement("div");
    overlay.className = "lrh-loading-overlay";
    overlay.setAttribute("role", "status");
    overlay.setAttribute("aria-live", "polite");
    document.body.append(overlay);
    let timer = null;

    function clear() {
      if (timer !== null) window.clearTimeout(timer);
      timer = null;
      root.classList.remove("lrh-loading");
      overlay.textContent = "";
    }

    function start() {
      clear();
      timer = window.setTimeout(() => {
        root.classList.add("lrh-loading");
        overlay.textContent = "Loading…";
      }, LOADING_DELAY_MS);
    }

    document.addEventListener("click", (event) => {
      if (event.defaultPrevented || event.button !== 0) return;
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      const link = event.target instanceof Element ? event.target.closest("a[href]") : null;
      if (!link || link.hasAttribute("download")) return;
      if (link.target && link.target !== "_self") return;
      const url = new URL(link.href, window.location.href);
      if (url.origin !== window.location.origin) return;
      if (url.searchParams.has("download")) return;
      const here = new URL(window.location.href);
      if (url.pathname === here.pathname && url.search === here.search && url.hash) return;
      start();
    });
    // Coming back through the history cache must not leave the page dimmed.
    window.addEventListener("pageshow", clear);
  }

  setupThemeSwitch();
  setupMap();
  setupLoading();
})();
