# AI Programming Helpers

This directory contains maintainer-only AI-assisted programming helpers for this repository.

- These scripts are **not** part of the supported `lrh` package API.
- Supported package code lives under `src/lrh/`.
- If a helper becomes reusable harness functionality, promote it into `src/lrh/...` in a separate change.

Current helpers include:

- `request.py` for template-based request generation
- `templates/context/` for deterministic context/snapshot guide templates
- `templates/request/` for agent-facing request templates consumed by `request.py`
- `snapshot.py` for automated control-plane context packet generation
- `sourcetree_surveyor.py` for Python source-tree inventory

Usage examples:

```bash
lrh request --help
lrh request assessment --scope project
lrh request assessment --scope current_focus
lrh request assessment --scope work_item --target WI-0003
lrh snapshot --help
python scripts/aiprog/sourcetree_surveyor.py --help
```

Legacy wrappers remain available for compatibility during migration:

```bash
python scripts/aiprog/request.py --help
python scripts/aiprog/snapshot.py --help
```
