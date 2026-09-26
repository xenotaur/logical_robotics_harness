# Local agent briefing prototype (stage 0)

Temporary research code for `WI-LOCAL-AGENT-001`. It briefs one selected LRH
work item using a single local-model call over an explicitly approved,
immutable context packet. The pre-registered evaluation lives in
`experiments/01_local_agent_briefing/`.

## Boundaries

- The model gets **no tools**. It sees one prompt and returns one JSON briefing.
  The prototype never writes repository files or project state.
- **Context** comes only from files tracked at a pinned commit, read from Git
  objects. Private paths (`project/sessions/`, `project/executions/`,
  `project/memory/`), untracked files, and binary files are excluded.
- **Readiness** diagnostics come from existing LRH code and are kept verbatim.
  An unready item is briefed as unready.
- **Inference** is local only. The service must be a loopback endpoint with
  proxies and redirects disabled, serving the pinned local model digest, and
  reporting no remote fields. There is no cloud fallback, no model download, and
  no installation.
- **Records** go to a private store outside Git. They are experimental attempt
  logs, not canonical LRH run or work-item state.
- Nothing in `src/lrh/` imports this package. It is not part of `scripts/test`
  or the package build. Promotion needs a separate reviewed work item.

## Setup

Use an environment bound to this worktree so `lrh` imports this checkout and the
pinned Black/Ruff apply:

```bash
scripts/conda-worktree-env <EnvName>
conda activate <EnvName>
scripts/version tools
```

The prototype needs Python ≥ 3.11.4, for the safe tar extraction filters. The
`run` and `test` wrappers put this checkout's `src/` and `experimental/` on
`PYTHONPATH` themselves. Live runs need Ollama started by hand, for example:

```bash
OLLAMA_NO_CLOUD=1 OLLAMA_HOST=127.0.0.1:11434 ollama serve
```

## Usage

```bash
# 1. Build and store a packet; review the printed sources and diagnostics.
experimental/local_agent/run packet --repo . --repo-label LRH \
    --commit <sha> --work-item <WI-ID> [--project-dir <subdir>] [--show]

# 2. Approve that exact packet by repeating its sha256, and brief it once.
experimental/local_agent/run run --packet <sha256> --approve <sha256> [--task-id T01]

# 3. Inspect, score, recover, and export.
experimental/local_agent/run inspect <run-id>
experimental/local_agent/run list
experimental/local_agent/run evaluate <run-id> --scores scores.json
experimental/local_agent/run recover <run-id>
experimental/local_agent/run export <run-id> --out <dir> [--include-output]
```

`run` re-hashes the stored packet and refuses it if its content changed after
approval. `export --include-output` requires a recorded evaluation, and both the
briefing and the evaluation notes must pass the sensitivity scan.

Pass `--store <dir>` (or set `LRH_LOCAL_AGENT_STORE`) to use a store other than
`~/.local/share/lrh/local-agent/`. `run --backend fake --fake-response <file>`
exercises the whole path without a model.

Every attempt ends with exactly one outcome:

- `completed`: inference finished with schema-valid output. This is not human
  acceptance.
- `missing_prerequisite`
- `budget_exhausted`
- `invalid_model_output`
- `backend_error`
- `timeout`
- `cancelled`

`recover` marks an interrupted run `incomplete` and keeps any truncated final
event as evidence.

## Tests

```bash
experimental/local_agent/test
```

The tests are opt-in `unittest.TestCase` suites that use a fake backend,
temporary directories, and local throwaway Git repositories. They make no
network or live-model calls. They cover:

- source pinning and rejection;
- preserved diagnostics;
- budgets;
- every outcome, including cancellation and truncated-log recovery;
- export exclusions;
- the local-only adapter checks.

Lint and format with the repository scripts:

```bash
scripts/format --check --diff experimental/local_agent
scripts/lint experimental/local_agent
```

## Layout

| Module | Role |
|---|---|
| `settings.py` | Versioned defaults: budgets, model pin, store location, exclusions |
| `sources.py` | Pinned, tracked-only source reads with provenance |
| `context.py` | Packet assembly from existing LRH readiness and context APIs |
| `briefing.py`, `prompts/` | Prompt template, output schema, citation resolution |
| `model.py` | Fake backend and local-only Ollama adapter |
| `runner.py` | One-call runner with explicit outcomes |
| `recorder.py` | Private single-writer store: manifests, JSONL events, recovery |
| `export.py` | Inspection, human evaluation records, sanitized export |
| `cli.py` | Command line (`python -m local_agent`) |
