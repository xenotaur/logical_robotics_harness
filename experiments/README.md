# LRH Experiments

This directory holds durable, numbered records of experiments: their purpose,
setup, commands, sanitized results, and the human decision each one produced. It is evidence for later decisions, not package
code, canonical project state, or a place for raw private logs.

## Convention

Experiments are numbered in the order they start:

```text
experiments/
    01_local_agent_briefing/   <- first experiment
    02_<name>/                 <- next experiment
```

- Take the next available number. Never renumber existing experiments, so
  paths stay stable references for work items, proposals, and reports.
- Each experiment has a `README.md` covering its purpose, the work item that
  owns it, setup, pinned inputs (commits, model identifiers), exact commands,
  results, limitations, and the human decision.
- Keep the method proportionate. Dogfooding write-ups can simply summarize
  automatic run logs. When an experiment makes a comparative claim, write its
  decision criteria before the runs and commit them first, so Git history shows
  they came before any results.
- Keep sanitized results under `NN_name/results/`. Include failed and stopped
  attempts; they stay in the denominator.
- A negative result is a valid, complete outcome.

This follows the LCATS convention
([experiments](https://github.com/xenotaur/LCATS/tree/main/experiments)), with
one difference: LRH keeps experiment *code* in `experimental/`, outside the
package and default test discovery (see `experimental/README.md`). Promoting
code into `src/lrh/` needs separate reviewed work.

## What lives where

| Asset | Location |
|---|---|
| Experiment write-ups, sanitized results, decision | `experiments/NN_name/` |
| Temporary prototype code and opt-in tests | `experimental/<name>/` |
| Raw prompts, packets, model outputs, and transcripts | A private store outside Git (for example `~/.local/share/lrh/`), never committed |
| Canonical work-item, workstream, and run state | `project/` |

## Experiments

| # | Name | Work item | Description |
|---|---|---|---|
| 01 | `01_local_agent_briefing` | `WI-LOCAL-AGENT-001` | Superseded before any live run: a pre-registered stage-0 briefing pilot, replaced by the toy ladder |
