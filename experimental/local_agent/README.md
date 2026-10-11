# Local agent prototype

Temporary research code for `WI-LOCAL-AGENT-001`, part of the toy ladder in
`PROP-LOCAL-AGENT-DOGFOOD`. Each rung gets a little more authority than the one
before it. This package implements the first two rungs:

- **T0 ask:** ask the local model a question about a repository and get a cited
  answer streamed back from tracked files.
- **T1 brief:** get a structured briefing on one work item, checked against
  LRH's own readiness diagnostics.

Evidence is collected automatically, and a run takes only a one-key rating from
you.

## Quick start

```bash
# Start Ollama by hand (local only; no cloud models).
OLLAMA_NO_CLOUD=1 OLLAMA_HOST=127.0.0.1:11434 ollama serve

# Ask about the repository overview (README plus a tracked-file listing).
experimental/local_agent/run ask "What is this repository for?"

# Ask about one work item, with LRH's readiness diagnostics included.
experimental/local_agent/run ask "What blocks this?" --wi WI-LOCAL-AGENT-001

# Ask about specific tracked files.
experimental/local_agent/run ask "How are runs stored?" \
    --files experimental/local_agent/recorder.py

# Brief a work item (T1), checked against LRH's readiness diagnostics.
experimental/local_agent/run brief WI-LOCAL-AGENT-001

# See how it has been going (optionally only recent runs, or one kind).
experimental/local_agent/run log
experimental/local_agent/run log --since 2026-10-09 --kind ask --kind brief
```

Prompts put the sources before the question (`ask_v2`, `brief_v2`). Ollama can
then reuse its cached reading of the same sources across consecutive questions,
as long as the model stays loaded; it unloads after about 5 idle minutes.

`brief <WI-ID>` is `ask --wi <WI-ID>` with a fixed briefing prompt
(`prompts/brief_v2.md`). The tool itself prints a **Readiness (from LRH
diagnostics)** section first: prompt and execution readiness, with blocking
reasons, warnings, and issues. It is stored with the run as the answer's
`preamble`. The model is told not to state readiness, but its prose is not
checked, so read any readiness claim in the briefing itself with care. Only
`READINESS:` lines are checked.

The model's briefing follows in four sections: Summary, Scope and next steps,
Dependencies and risks, and Open questions. Claims cite `S<n>:L<a>-L<b>`, and
anything taken from the diagnostics cites `[diagnostics]`. The briefing must
end with exactly one line:

```text
READINESS: prompt_ready=<yes|no> execution_ready=<yes|no>
```

The tool compares that line with LRH's diagnostics. Light Markdown around the
line (bold, code, a quote or list marker, a final period) is ignored. It
records `readiness_check` with one of these statuses:

- `agrees`
- `contradicts`: any line disagrees
- `missing`: no such line
- `misplaced`: an agreeing line that is not the last line
- `duplicated`: more than one agreeing line
- `unavailable`: there are no diagnostics

The footer shows the result, and `log` flags every status except `agrees` and
`unavailable`. The line is an attention check. The readiness itself comes from
the tool's section, not the model.

`brief` takes the same options as `ask` (`--repo`, `--commit`,
`--project-dir`, `--yes`, `--no-rate`, and the backend options), except
`--wi`, `--files`, and `--allow-flagged`. Brief runs export like ask runs: the
question, answer, and rating note are included only with `--include-output`
on a rated run whose text has no sensitivity finding.

`ask` first prints the sources it will send, on stderr, and asks for
confirmation (skip it with `--yes`). It then streams the answer and prints a
footer line with the run id, latency, tokens, and citation check. It ends by
asking for a rating: `g`ood, `o`k, `b`ad, or Enter to skip. Rate later with
`rate <run-id> g --note "..."`. Pass `--no-rate` to skip the prompt.

`log` shows:

- recent runs;
- counts by outcome and rating;
- latency and token medians;
- the citation-resolution rate;
- runs flagged for unresolved citations or non-completed outcomes.

These numbers are the evidence behind each rung's go/no-go decision.

Other options:

- `--commit <rev>` reads sources at another commit (default `HEAD`).
- `--repo <path>` and `--project-dir <subdir>` point at another LRH repository.
- `--num-ctx`, `--max-output-tokens`, and `--timeout` set budgets.
- `--backend fake --fake-response <file>` exercises everything without a model.

## Boundaries

- **The model gets no tools.** It sees one prompt and returns text. The
  prototype never writes repository files or project state.
- **Context comes only from committed, tracked files**, read from Git objects at
  the pinned commit. Uncommitted edits are never sent. These are excluded and
  listed as exclusions:
  - private paths (`project/sessions/`, `project/executions/`, `project/memory/`);
  - untracked and binary files;
  - credential-like file names (`.env*`, `*.pem`, `*.key`, `id_rsa*`,
    `*secret*`, `*credential*`, and similar);
  - any file with a high-severity finding from LRH's sensitivity scanner
    (secret, token, private key, URL credentials, payment card, government
    ID).

  Medium-severity findings (email, IP address, phone) do not exclude a file.
  The source summary marks such a file `WARN: <categories>`, by category,
  never by value, before the model is called. That text does reach the model,
  which is acceptable only because inference stays on this machine.

  The scanner misfires on some code. A parameter named `token` annotated with
  a `Callable` type reads as a secret, so `recorder.py` is excluded. You can
  send such a file anyway with an explicit, per-run override that names the
  categories:

  ```bash
  experimental/local_agent/run ask "How are runs stored?" \
      --files experimental/local_agent/recorder.py \
      --allow-flagged experimental/local_agent/recorder.py=secret
  ```

  The summary lists every finding it would let through, by rule and line
  (`ALLOWED DESPITE <category>: <rule> at L<n>`, shown in the terminal only;
  for `recorder.py` it names the `secret` category and L103), and only a
  typed `yes` sends; Enter declines. It is refused:
  - with `--yes`, or without a terminal;
  - for a file with another high-severity category, or none;
  - for a file you didn't request, or one excluded by path;
  - for `--wi` and overview questions.

  The run records each override as structured fields, never the value.
- **Readiness diagnostics come from existing LRH code** and are kept verbatim.
  An unready item is described as unready.
- **Inference is local only.** The service must be a loopback endpoint, with
  proxies and redirects disabled. It must serve the pinned `gemma4:12b` manifest
  digest and report no remote fields. There is no cloud fallback, no model
  download, and no installation. Hidden reasoning is turned off (`think:
  false`).
- **Records go to a private store outside Git**, by default
  `~/.local/share/lrh/local-agent/`. Override it with `--store` or
  `LRH_LOCAL_AGENT_STORE`. These are experimental attempt logs, not canonical
  LRH state. They are kept until the workstream closes, plus 90 days.
  - `delete <run-id>` removes one run.
  - `prune --before YYYY-MM-DD [--dry-run]` removes older runs.
- **Nothing in `src/lrh/` imports this package.** It is not part of
  `scripts/test` or the package build. Promotion needs a separate reviewed work
  item.

## Outcomes

Every attempt ends with exactly one outcome. This includes attempts that stop
before the model is called: a missing work item, a refused endpoint or model,
or declining at the confirmation prompt. If an answer fails partway through,
the streamed part is kept, marked `partial`.

- `completed`: the model finished. This is not acceptance; that is what your
  rating is for.
- `budget_exhausted`: the input was over budget, so nothing was sent, or the
  output hit its limit, in which case the partial answer is kept.
- `invalid_model_output`: the answer was empty. The detail notes any hidden
  reasoning that used up the budget.
- `missing_prerequisite`: for example, Ollama is not running or the model is not
  pulled.
- `backend_error`
- `timeout`
- `cancelled`

`inspect <run-id>` summarizes a run. `recover <run-id>` marks an interrupted run
`incomplete`, and keeps any truncated final event as evidence.

`export <run-id> --out <dir>` writes a sanitized record. By default it leaves
out the question, the answer, and your rating note. `--include-output` adds them
only for a rated run whose text has no sensitivity finding at all, medium
included.

## Setup and tests

Use an environment bound to this worktree, so that `lrh` imports this checkout
and the pinned Black and Ruff apply:

```bash
scripts/conda-worktree-env <EnvName>
conda activate <EnvName>
experimental/local_agent/test
scripts/format --check --diff experimental/local_agent
scripts/lint experimental/local_agent
```

The prototype needs Python 3.11.4 or later, for the safe tar extraction filters.
The `run` and `test` wrappers put `src/` and `experimental/` on `PYTHONPATH`
themselves.

The tests are opt-in `unittest` suites that use:

- a fake backend;
- a fake streaming transport;
- temporary directories;
- throwaway Git repositories.

They make no network or live-model calls.

## Legacy pilot commands

`packet`, `task`, `b0`, `run`, and `evaluate` belong to the superseded stage-0
pilot (`experiments/01_local_agent_briefing/`, now marked superseded). They are
not part of the current procedure; T1 `brief` replaces their briefing, and they
can be removed in a later cleanup. `log` counts their runs as kind `pilot`.

## Layout

| Module | Role |
|---|---|
| `ask.py`, `prompts/ask_v2.md` | T0: context modes, one streamed call, rating, `log` summary |
| `brief.py`, `prompts/brief_v2.md` | T1: briefing preset on `ask --wi`, with the readiness check |
| `settings.py` | Versioned defaults: budgets, model pin, store location, exclusions |
| `sources.py` | Pinned, tracked-only source reads with provenance and exclusions |
| `context.py` | Work-item packet assembly from existing LRH readiness and context APIs |
| `briefing.py`, `prompts/` | Briefing prompt and schema; citation resolution |
| `model.py` | Fake backend and local-only, streaming Ollama adapter |
| `recorder.py` | Private single-writer store: manifests, JSONL events, recovery, pruning |
| `export.py` | Inspection, evaluation records, sanitized export |
| `runner.py`, `tasks.py` | Legacy pilot runner and task lookup |
| `cli.py` | Command line (`python -m local_agent`) |
