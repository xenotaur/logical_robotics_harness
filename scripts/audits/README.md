# Audit Scripts

## `audit-chatgpt-pdf-dataset`

Runs a rerunnable audit over an external ChatGPT PDF dogfood dataset and compares
independent PDF-text probing with `lrh conversation convert-pdf` outcomes.

```bash
scripts/audits/audit-chatgpt-pdf-dataset \
  --dataset-root "$HOME/Workspace/LogicalRoboticsHarness/Datasets/ChatSessions" \
  --out tmp/chatgpt-pdf-audit
```
