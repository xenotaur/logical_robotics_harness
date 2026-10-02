// Renders the main window's status and recovery pages from the page's own
// query string (?state=<name>&code=<machine error code>). It makes no IPC
// calls: the main window is granted no app commands. Diagnostics live in
// Server > Details.
"use strict";

const SETTINGS_HINT = "Open LRH Console > Settings… (⌘,) to fix it.";
const DETAILS_HINT = "Server > Server Details… (⌘I) shows the error and recent output.";

const STATES = {
  setup: {
    title: "Set up LRH Console",
    detail:
      "Choose the lrh program and the LRH workspace to serve in Settings " +
      "(LRH Console > Settings…, ⌘,). The Settings window opens on first run.",
  },
  starting: { title: "Starting LRH Serve…", detail: "" },
  stopping: { title: "Stopping LRH Serve…", detail: "" },
  stopped: {
    title: "Server stopped",
    detail: "Choose Server > Start Server to start it.",
  },
  failed: {
    title: "Server failed",
    detail: "Choose Server > Start Server to try again. " + DETAILS_HINT,
  },
  incompatible: {
    title: "Incompatible backend",
    detail:
      "The configured lrh did not speak a compatible desktop protocol, or " +
      "served a different workspace than the one configured. Update lrh or " +
      "choose another program. " + SETTINGS_HINT,
  },
};

// Actionable text for specific failure codes.
const CODES = {
  invalid_workspace: "The configured workspace path cannot be used. " + SETTINGS_HINT,
  workspace_not_lrh_project:
    "The configured workspace has no LRH project/ directory. " + SETTINGS_HINT,
  spawn_failed: "The configured lrh program could not be started. " + SETTINGS_HINT,
  exited_before_ready:
    "lrh exited before it was ready, often because Python could not import " +
    "LRH. Check the interpreter and PYTHONPATH in Settings. " + DETAILS_HINT,
  startup_timeout: "lrh did not become ready in time. " + DETAILS_HINT,
  exited_unexpectedly: "LRH Serve stopped unexpectedly. " + DETAILS_HINT,
  not_configured: STATES.setup.detail,
};

const params = new URLSearchParams(window.location.search);
const requested = params.get("state");
const view = Object.hasOwn(STATES, requested) ? STATES[requested] : STATES.stopped;
const code = params.get("code");
const knownCode = code && /^[a-z_]{1,64}$/.test(code) ? code : null;
document.getElementById("state").textContent = view.title;
document.getElementById("detail").textContent =
  knownCode && Object.hasOwn(CODES, knownCode) ? CODES[knownCode] : view.detail;
if (knownCode) {
  const element = document.getElementById("code");
  element.textContent = `Error code: ${knownCode}`;
  element.hidden = false;
}
