# AI Programming Helpers

This directory contains maintainer-only AI-assisted programming helpers for this repository.

- These scripts are **not** part of the supported `lrh` package API.
- Supported package code lives under `src/lrh/`.
- If a helper becomes reusable harness functionality, promote it into `src/lrh/...` in a separate change.

Current helpers include:

- `create_request.py` for template-based request generation
- `sourcetree_surveyor.py` for Python source-tree inventory
- `templates/` for reusable prompt/request templates
- `generate_context.py` for control-plane context packet generation

Usage examples:

```bash
python scripts/aiprog/create_request.py --help
python scripts/aiprog/sourcetree_surveyor.py --help
python scripts/aiprog/generate_context.py --help
```
