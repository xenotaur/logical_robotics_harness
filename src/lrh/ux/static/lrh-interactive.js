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
    for (const line of lines) {
      const source = line.dataset.source;
      const item = line.dataset.item;
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
          // A filtered (invisible) trigger cannot take focus; the map can,
          // without scrolling the page to its top.
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
    // the top bar's Refresh) follow the new selection.
    function syncLinks(id) {
      const links = document.querySelectorAll(
        ".lrh-tabs a, .lrh-map-header a[href*='since='], .lrh-topbar a[href]",
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

    setupFilters(map);
  }

  // data-unmet is a JSON list of IDs, which may contain spaces.
  function readUnmet(item) {
    try {
      const value = JSON.parse(item.dataset.unmet || "[]");
      return Array.isArray(value) ? value.map(String) : [];
    } catch (_error) {
      return [];
    }
  }

  // Filters hide items by state, but never an unfinished item that a shown
  // item still needs: blockers stay visible.
  function setupFilters(map) {
    const items = [...map.querySelectorAll("[data-state]")];
    if (!items.length) return;
    const states = [...new Set(items.map((item) => item.dataset.state))];
    const header = map.querySelector(".lrh-map-header");
    if (!header) return;
    const box = document.createElement("fieldset");
    box.className = "lrh-filters";
    const legend = document.createElement("legend");
    legend.textContent = "Show";
    box.append(legend);
    const shown = new Set(states);
    for (const state of states) {
      const label = document.createElement("label");
      const input = document.createElement("input");
      input.type = "checkbox";
      input.checked = true;
      input.addEventListener("change", () => {
        if (input.checked) shown.add(state);
        else shown.delete(state);
        refresh();
      });
      const sample = items.find((item) => item.dataset.state === state);
      const pill = sample && sample.querySelector(".lrh-pill");
      label.append(input, " ", pill ? pill.textContent.trim() : state);
      box.append(label);
    }
    header.append(box);

    function refresh() {
      const byId = new Map();
      for (const item of items) byId.set(item.dataset.id, readUnmet(item));
      const visible = new Set(
        items.filter((item) => shown.has(item.dataset.state)).map((item) => item.dataset.id),
      );
      const stack = [...visible];
      while (stack.length) {
        for (const need of byId.get(stack.pop()) || []) {
          if (!visible.has(need)) {
            visible.add(need);
            stack.push(need);
          }
        }
      }
      for (const item of items) item.classList.toggle("lrh-filtered", !visible.has(item.dataset.id));
      for (const line of map.querySelectorAll("polyline[data-source]")) {
        const off = !visible.has(line.dataset.source) || !visible.has(line.dataset.item);
        line.classList.toggle("lrh-filtered", off);
      }
    }
  }

  setupThemeSwitch();
  setupMap();
})();
