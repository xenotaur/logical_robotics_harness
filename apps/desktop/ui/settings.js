// The Settings / Server Details window. This window shows only bundled
// pages and is the only one granted app commands; every value is validated
// again in Rust before it is saved.
"use strict";

const invoke = (cmd, args) => window.__TAURI_INTERNALS__.invoke(cmd, args);
const $ = (id) => document.getElementById(id);
const form = $("settings-form");

const SOURCES = {
  file: "Using the saved configuration.",
  environment:
    "Using the developer LRH_CONSOLE_* environment settings for this session. " +
    "Saving here only writes the configuration file; it takes effect in a " +
    "later session started without those variables.",
  none: "No configuration yet. Choose a program and workspace, then Save.",
};

function kind() {
  return form.querySelector('input[name="kind"]:checked').value;
}

function showKind() {
  for (const section of form.querySelectorAll("[data-kind]")) {
    section.hidden = section.dataset.kind !== kind();
  }
}

function clearErrors() {
  for (const element of form.querySelectorAll(".field-error")) {
    element.textContent = "";
  }
}

function fill(config) {
  if (!config) return;
  const launch = config.launch;
  form.querySelector(`input[name="kind"][value="${launch.kind}"]`).checked = true;
  $("path").value = launch.kind === "executable" ? launch.path : "";
  $("interpreter").value = launch.kind === "python" ? launch.interpreter : "";
  $("pythonpath").value = (launch.kind === "python" && launch.pythonpath) || "";
  $("workspace").value = config.workspace;
  $("browser").value = config.browser;
  $("start_on_open").checked = config.start_on_open;
  showKind();
}

function collect() {
  const launch =
    kind() === "executable"
      ? { kind: "executable", path: $("path").value.trim() }
      : {
          kind: "python",
          interpreter: $("interpreter").value.trim(),
          pythonpath: $("pythonpath").value.trim() || null,
        };
  return {
    launch,
    workspace: $("workspace").value.trim(),
    browser: $("browser").value,
    start_on_open: $("start_on_open").checked,
  };
}

async function loadSettings() {
  const view = await invoke("get_settings");
  $("source").textContent =
    (SOURCES[view.source] || "") +
    (view.config_path ? ` Configuration file: ${view.config_path}` : "");
  $("problem").hidden = !view.problem;
  $("problem").textContent = view.problem || "";
  fill(view.config);
}

function addDetail(list, name, value) {
  const term = document.createElement("dt");
  term.textContent = name;
  const description = document.createElement("dd");
  description.textContent = value === null || value === undefined || value === "" ? "—" : String(value);
  list.append(term, description);
}

async function loadDetails() {
  const details = await invoke("get_server_details");
  const list = $("details");
  list.replaceChildren();
  addDetail(list, "State", details.state);
  addDetail(list, "Owned process", details.owned_pid ? `pid ${details.owned_pid} (started by this app)` : null);
  addDetail(list, "Endpoint", details.endpoint);
  addDetail(list, "Configured workspace", details.configured_workspace);
  addDetail(list, "Served workspace", details.served_workspace && details.served_workspace.project_root);
  addDetail(list, "Protocol version", details.protocol_version);
  addDetail(list, "Backend", details.backend && `${details.backend.name || "lrh"} ${details.backend.version || ""} (Python ${details.backend.python || "?"})`);
  addDetail(list, "Last error", details.last_error_code && `${details.last_error_code}: ${details.last_error_message || ""}`);
  addDetail(list, "Last exit code", details.last_exit_code);
  addDetail(list, "Chrome", details.chrome_available ? "installed" : "not found: links open in the default browser");
  if (details.last_handoff) {
    const handoff = details.last_handoff;
    addDetail(
      list,
      "Last browser handoff",
      handoff.ok ? `${handoff.handoff.opened}${handoff.handoff.note ? ` (${handoff.handoff.note})` : ""}` : `failed: ${handoff.error}`,
    );
  }
  $("stderr").textContent = details.stderr_tail || "(no output yet)";
}

form.addEventListener("change", (event) => {
  if (event.target.name === "kind") showKind();
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearErrors();
  $("saved").textContent = "";
  try {
    const outcome = await invoke("save_settings", { config: collect() });
    $("restart").hidden = !outcome.restart_required;
    $("saved").textContent = outcome.env_override_active
      ? "Saved to the configuration file. This session keeps using the LRH_CONSOLE_* settings."
      : outcome.restart_required
        ? "Saved. Restart the server to use the new program or workspace."
        : outcome.started
          ? "Saved. Starting the server…"
          : "Saved.";
    await loadSettings();
  } catch (errors) {
    const list = Array.isArray(errors) ? errors : [{ field: "file", message: String(errors) }];
    for (const error of list) {
      const target = form.querySelector(`.field-error[data-field="${error.field}"]`) ||
        form.querySelector('.field-error[data-field="file"]');
      target.textContent = error.message;
    }
    $("saved").textContent = "Not saved. The previous settings are still in effect.";
  }
});

$("restart").addEventListener("click", async () => {
  try {
    await invoke("restart_server");
    $("restart").hidden = true;
    $("saved").textContent = "Restarting the server…";
  } catch (error) {
    $("saved").textContent = `Could not restart: ${error}`;
  }
});

$("refresh").addEventListener("click", loadDetails);

loadSettings().then(loadDetails);
setInterval(loadDetails, 3000);
