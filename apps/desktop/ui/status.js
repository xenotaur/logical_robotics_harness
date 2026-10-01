// Renders the shell's status page from its own query string
// (?state=<name>&code=<error code>). It makes no IPC calls: the main window
// is granted no app commands.
"use strict";

const STATES = {
  unconfigured: {
    title: "Backend not configured",
    detail:
      "Set LRH_CONSOLE_LRH_EXECUTABLE (or LRH_CONSOLE_PYTHON) and " +
      "LRH_CONSOLE_WORKSPACE to absolute paths, then relaunch. These " +
      "developer settings are documented in docs/how-to/project-setup/" +
      "desktop-toolchain.md.",
  },
  starting: { title: "Starting LRH Serve…", detail: "" },
  stopping: { title: "Stopping LRH Serve…", detail: "" },
  stopped: {
    title: "Server stopped",
    detail: "Choose Server > Start Server to start it.",
  },
  failed: {
    title: "Server failed",
    detail:
      "Choose Server > Start Server to try again. Diagnostics and recovery " +
      "pages arrive with the Settings work.",
  },
};

const params = new URLSearchParams(window.location.search);
const view = STATES[params.get("state")] || STATES.stopped;
document.getElementById("state").textContent = view.title;
document.getElementById("detail").textContent = view.detail;
const code = params.get("code");
if (code && /^[a-z_]{1,64}$/.test(code)) {
  const element = document.getElementById("code");
  element.textContent = `Error code: ${code}`;
  element.hidden = false;
}
