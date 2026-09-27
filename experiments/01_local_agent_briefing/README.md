# 01 — Local Agent Briefing (stage 0)

- **Work item:** `WI-LOCAL-AGENT-001`
- **Workstream:** `WS-LOCAL-AGENT-DOGFOOD`
- **Design:** `PROP-LOCAL-AGENT-DOGFOOD` (Stage-0 Lane Approval section)
- **Status:** pre-registered. The pilot has not run. Results and the human
  decision are pending and will be added in a later PR.

## Question

Does a single call to a modest local model, briefing one work item from a fixed
context packet, reduce human effort compared with briefing it by hand from the
same deterministic LRH output, without fabricating project status?

The milestone this serves: *"I can ask my local assistant to brief me on an LRH
work item, inspect its sources, and retain the complete run."*

Stage 0 gives the model no tools. Repository search, shell, patches, MCP, UI,
fine-tuning, and project-state writes belong to later, separately authorized
stages. A negative result is a valid outcome, and resolving `WI-LOCAL-AGENT-001`
does not activate `WI-LOCAL-AGENT-002`.

## Pre-registered setup

Everything in this section was fixed and committed before any live run.

### Hardware and runtime

| Item | Value |
|---|---|
| Machine | MacBookPro18,4, Apple M1 Max (10-core CPU: 8P + 2E; 32-core GPU), 32 GB unified memory |
| OS | macOS 26.6.2 (25G83), arm64 |
| Inference service | Ollama 0.32.5 (Homebrew), started by hand in the foreground for pilot runs |
| Model | `gemma4:12b`: Gemma 4, 11.9B dense, Q4_K_M, native context 262,144 |
| Model manifest digest | `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c` |
| Model weight layer | `sha256:1278394b693672ac2799eadc9a83fd98259a6a88a40acfb1dcaa6c6fc895a606` |
| Fallback | `qwen3:8b` with thinking off, only after a recorded "revise" decision and with a fresh held-out set |

The pilot uses one model only. It is not a model benchmark.

### Local-only inference

A loopback endpoint alone does not prove local inference. Before sending any
prompt, the adapter (`experimental/local_agent/model.py`) checks that:

- the endpoint is plain `http` on a loopback host;
- HTTP proxies and redirects are disabled;
- `/api/tags` reports the pinned manifest digest for the model;
- neither `/api/tags` nor `/api/show` reports `remote_host` or `remote_model`;
- the model name is not cloud-tagged.

Each run's manifest records these checks. Starting Ollama with `OLLAMA_NO_CLOUD=1`
is optional defense in depth. The inference service itself remains trusted.

### Budgets (per run)

| Budget | Value |
|---|---|
| Packet source content | ≤ 80,000 bytes of source text. Each related source ≤ 16,000 bytes; the target work item may use the remainder. The rendered packet adds diagnostics, headers, and line prefixes; its size is recorded as `rendered_bytes`, and the input-token limit below bounds the total. |
| Estimated input | ≤ 24,000 tokens (chars / 4). Above this, the run ends as `budget_exhausted` without calling the model. |
| Context window (`num_ctx`) | 32,768 |
| Output (`num_predict`) | 2,048 tokens. Hitting the limit ends the run as `budget_exhausted`. |
| Wall time | 300 s per call. Exceeding it ends the run as `timeout`. |
| Sampling | temperature 0.2, seed 7 |
| Repairs | none at stage 0 |

### Context packet

- **Source content.** Only files tracked at the task's pinned commit are
  included, read from Git objects, never the working tree. Excluded:
  - `project/sessions/`, `project/executions/`, and `project/memory/`;
  - untracked, binary, and non-UTF-8 content.
- **Readiness diagnostics.** Readiness is computed with existing LRH code
  against the tracked `project/` tree extracted at that commit:
  - `evaluate_readiness` for prompt readiness;
  - `render_run_packet_from_work_item` for execution readiness;
  - `render_ready_work_item_request` for related-context resolution.

  All diagnostics are kept verbatim. An unready item can be briefed, but it is
  never presented as ready.
- **Related sources.** Admitted in priority order: dependency, workstream,
  design, focus, roadmap. Truncation happens on line boundaries and is marked.
  Omissions are listed.
- **Prefix fallback.** A reference written with the project subdirectory prefix
  (for example `lcats/project/...`) stays an unresolved LRH diagnostic, but is
  included through a labelled `prefix_fallback`.
- **Provenance.** Each source records its commit, path, Git blob id, sha256,
  and line range.
- **Approval.** You must pass the packet's sha256 back (`--approve`) before a
  model call. The runner re-hashes the stored packet and refuses to run if its
  content no longer matches. Each packet records the LRH commit and whether the
  prototype code had uncommitted changes (`lrh_code_dirty`).

### Private storage, retention, export

- **Store:** `~/.local/share/lrh/local-agent/` (override with
  `LRH_LOCAL_AGENT_STORE`). Directories are 0700 and files 0600. The store
  refuses to live inside a Git worktree.
- **Retention:** until `WS-LOCAL-AGENT-DOGFOOD` closes, plus 90 days. Deletion
  is manual.
- **Always private:** context packets, rendered prompts, raw model responses,
  and the text of tuning-iteration outputs.
- **Committed to `results/`:** sanitized exports (provenance, config, budgets,
  outcomes, timings, token counts, citation checks, scores). For every
  frozen-prompt run, the parsed briefing is included (`export --include-output`,
  which requires a recorded evaluation) after a clean sensitivity scan and PR
  review. It is labelled as a model output record rather than project state.
  Evaluation notes are scanned too, and citation statistics never copy
  free-form model text.
- Your B0 answers are committed at your discretion; otherwise only B0 times and
  scores are committed.

## Task corpus

`tasks.yaml` pins 12 tasks, 7 from LRH and 5 from LCATS:

- **Split:** 8 tuning and 4 held out.
- **Task types:** readiness, evidence gaps, dependency, find sources/code, and
  narrow change. One held-out task is a readiness trap: WI-EVENT-0079 is
  prompt-ready, but its dependency is still proposed.
- **Pins:** resolved items are pinned before their implementing PR, and the
  merged PR is their ground truth.

**Known limitations of the corpus:**

- Three items are very thin (T02, T06, T09).
- Only one task (T11) is a readiness trap.
- The owner is familiar with the resolved items, so B0 on those will look faster
  than it would on new work.
- "Held-out" means held out from prompt tuning, not hidden from the owner.

## Baselines and protocol

- **B0 (deterministic/manual):** the owner reads the same packet
  (`packet --show`: identical sources and diagnostics) and writes a briefing by
  hand. Time is recorded.
- **B1 (single local call):** one model call on the same packet. The owner
  reviews and corrects the briefing. Time is recorded.
- **Order:** counterbalanced per task in ID order, repeating the pattern
  B0-first, B1-first, B1-first, B0-first.
- **Denominator:** every attempt is recorded, including failures. None leave
  the denominator.

**Procedure:**

1. Start Ollama by hand. Run a separate 3-task smoke check (T01, T06, T11). It
   does not count toward the decision.
2. Tuning: run the 8 tuning tasks. Allow at most 3 prompt iterations
   (`briefing_v1` → `v2` → `v3`). Each iteration gets a new prompt version, and
   the old versions are kept.
3. Freeze the prompt version and record it here before any held-out run.
4. Held-out: run the 4 held-out tasks once with the frozen prompt.
5. Score every run (B0 and B1) with the rubric, then export sanitized records to
   `results/`.

**Abort the live pilot on:** 3 consecutive backend errors or timeouts, memory
pressure that makes the Mac unusable, or any sign of non-local routing. Record
the abort as a result.

## Rubric (per task and condition)

| Field | Definition |
|---|---|
| `usefulness` | 0 = not useful. 1 = useful after material correction. 2 = useful as-is or with minor edits. |
| `correction_minutes`, `review_minutes`, `total_human_minutes` | Active human time. Total includes reading the packet for B0, and review plus correction for B1. |
| `cited_claims_checked`, `cited_claims_supported` | How many cited claims were checked, and how many the cited lines actually support. |
| Citations resolving | Checked automatically: `citations_resolved / citations_total` in each run manifest |
| `unsupported_assertions` | Count of claims with no support in the packet |
| `critical_fabricated_status` | Count of false claims about readiness, status, or dependencies |
| `diagnostics_surfaced` | Whether the briefing reports the LRH readiness diagnostics accurately |
| `miss_cause` | For a miss: `context` (the fact was not in the packet), `model` (it was there and the model got it wrong), or `task` (poor fit) |
| Latency | From the run manifest: client elapsed time, plus prompt and output token counts |

A B1 briefing is "useful" if it scores 2, or scores 1 with ≤ 5 minutes of
correction.

## Decision rule

Only the **floor** is binding. Failing it means stop or revise. The floor fails
if any of these hold:

- fewer than 6 of 12 B1 briefings are useful;
- any critical fabricated status survives the owner's review;
- more than 2 of 12 runs end in a non-`completed` outcome;
- there is any sign of non-local routing.

**Advisory targets.** These are reported as met or unmet. They inform the
owner's stop/revise/proceed choice but do not decide it:

- at least 8 of 12 useful, including at least 3 of 4 held-out;
- median B1 human effort below median B0;
- p50 latency ≤ 90 s;
- most cited claims supported;
- diagnostics surfaced in at least 10 of 12 briefings.

**Interpreting misses.** Misses are classified by cause. Mostly context-limited
misses are the evidence that would justify *evaluating* stage 1
(`WI-LOCAL-AGENT-002`, bounded read/search). Model-limited misses point to
revising the prompt or model instead. Proceeding to stage 1 always needs a
separate human decision.

## Runbook

The runbook turns the protocol above into commands. It changes no
pre-registered setup, rubric, or decision rule. Run everything from the
repository root on the pilot branch.

### 0. Setup (once per session)

```bash
conda activate <EnvName>        # env bound to this worktree (scripts/conda-worktree-env)
scripts/version tools            # ruff 0.15.12, black 26.3.1, Python >= 3.11.4
experimental/local_agent/test    # fake-backend suite must pass
export LCATS=<path-to-LCATS-checkout>
```

In a separate terminal, start the inference service and leave it running:

```bash
OLLAMA_NO_CLOUD=1 OLLAMA_HOST=127.0.0.1:11434 ollama serve
```

The adapter's preflight enforces the local-only checks on every run. Runs use
the private store (`~/.local/share/lrh/local-agent/`) unless `--store` is
passed.

### 1. Build a task's packet

```bash
experimental/local_agent/run task T01 --lrh-repo . --lcats-repo "$LCATS" --show
```

This builds the packet from the task's pinned commit in `tasks.yaml`, prints
the sources and diagnostics, and prints the packet sha256 (`<sha>` below).
Skim the manifest for anything that should not be sent to the model. Build
each task's packet **once** and reuse that sha for B0 and for every B1 run of
that task, including later prompt versions. Rebuilding changes the sha, because
the packet records the LRH commit it was built at.

### 2. Smoke check (not counted)

For T01, T06, and T11, build the packet (step 1), then:

```bash
experimental/local_agent/run run --packet <sha> --approve <sha> --task-id SMOKE-T01
```

Smoke runs use `SMOKE-` task ids, and the aggregation rule in step 4 excludes
them from the decision. If they
show a setup problem, fix it before tuning. Do not score or export smoke runs.

### 3. Run both conditions for a task

Use this order table, which applies the pre-registered B0-first / B1-first /
B1-first / B0-first pattern in task-id order:

| First | Tasks |
|---|---|
| B0 first | T01, T04, T05, T08, T09, T12 |
| B1 first | T02, T03, T06, T07, T10, T11 |

**B0 (owner-written).** Time only the active work: reading the packet
(`task ... --show`) and writing the briefing to a file. Then record it:

```bash
experimental/local_agent/run b0 --packet <sha> --task-id T01 \
    --briefing-file <b0-T01.md> --minutes <active-minutes>
```

**B1 (single local call).**

```bash
experimental/local_agent/run run --packet <sha> --approve <sha> --task-id T01 \
    [--prompt-version briefing_vN]
experimental/local_agent/run inspect <run-id>
```

Review and correct the briefing, timing that work.

For B1-first tasks, B0 is written after seeing the model's briefing. This is a
known limitation of the pre-registered counterbalancing; the table above records
the order.

### 4. Score each run

Copy `scores_template.json` and give every field a value, using the rubric
definitions above. The one exception is `miss_cause`, which stays `null` when
the run is not a miss. `evaluate` rejects a scores file with any field missing,
any other `null`, or a negative or non-finite count. For B0 records, set
`total_human_minutes` to the same value as `b0 --minutes`, and use 0 for
B1-only fields such as `correction_minutes`. Then record it:

```bash
experimental/local_agent/run evaluate <run-id> --scores <scores-T01-B1.json>
```

Score every B1 attempt, including failed ones. A failed run scores
`usefulness: 0` with a note, so it stays in the denominator.

**Aggregation rule for the decision:**

- **Unit of count:** the floor and targets are per task. Each of `T01`–`T12`
  has exactly one counted B1 run, so "N of 12" always has 12 in the
  denominator. Every other attempt is still recorded and reported separately:
  tuning iterations, smoke runs, and retries.
- **B1 floor and targets:** count only `condition: B1` runs whose `task_id` is
  one of the pre-registered `T01`–`T12`. `SMOKE-*` runs are excluded.
- **Several B1 runs for one task:** use the run made with the frozen prompt
  version. If several runs used the frozen version (for example a retry after a
  failure or timeout), the **first** one counts. Later retries are reported
  alongside it but never replace it, so a failed attempt stays in the
  denominator.
- **Effort comparisons:** use `condition: B0` records for the same `T##` ids.
  B0 records have outcome `manual` and are never model completions.

### 5. Tuning loop (tuning tasks only)

- Run steps 1–4 for the 8 tuning tasks with `briefing_v1`.
- To iterate, add `experimental/local_agent/prompts/briefing_v2.md` (then `v3`),
  never editing an earlier version. Each run records `prompt_version` and
  `prompt_template_sha256`, which identify the exact template. Commit each new
  version on the pilot branch before running it, so that hash is traceable in
  Git. Keep reusing the task's original packet sha (step 1).
- Allow at most 3 versions (`v1`–`v3`). Re-run tuning tasks with
  `--prompt-version briefing_vN` as needed. Every attempt stays recorded.

### 6. Freeze, then held-out

Record the frozen version here and commit it **before** any held-out run:

**Frozen prompt:** _pending_

Then, before any held-out run, give every tuning task (T01–T08) that does not
yet have a frozen-version B1 run one such run, and score it. This ensures all 12
tasks have a counted run.

Then run steps 1–4 once for T09–T12 with `--prompt-version <frozen>`. Retry a
held-out task only after a backend failure (`missing_prerequisite`,
`backend_error`, or `timeout`). The first frozen-version run still counts, and
the retry is reported alongside it. Do not change the prompt after seeing
held-out output.

### 7. Export sanitized results

Export every scored run. Files are written as `results/<T##>/<run-id>.json`,
with the condition recorded inside each file. `export` does not know a run's
split or prompt status, so choose the command by kind of run:

**Frozen-prompt B1 runs** (any task, run with the frozen version) **and all B0
records.** Include the text, after a clean sensitivity scan; unscored runs are
refused:

```bash
experimental/local_agent/run export <run-id> \
    --out experiments/01_local_agent_briefing/results/<T##> --include-output
```

**Tuning-iteration B1 runs** (any non-frozen prompt version). Metrics only;
the text stays private, per the storage rules:

```bash
experimental/local_agent/run export <run-id> \
    --out experiments/01_local_agent_briefing/results/<T##>
```

### 8. Abort

Stop on 3 consecutive backend errors or timeouts, memory pressure that makes the
Mac unusable, or any sign of non-local routing. Leave the runs as recorded,
export them without `--include-output`, and write the abort into Results.
`recover <run-id>` marks an interrupted run as `incomplete`.

### 9. Report

Fill in **Results** with the per-task scores and the floor/target table, then
record the **Decision**. Commit the results, exports, and any prompt versions
together in the results PR.

## Results

Pending.

## Decision

Pending. The owner records stop, revise, or proceed.
