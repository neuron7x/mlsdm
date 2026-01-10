# Structural Debt Register

This register tracks architecture-level debt. It is **not** a feature backlog;
it captures risks that degrade structural integrity, correctness, or maintainability.

## Entry template

```
- id: SD-YYYY-NNN
  title: <short description>
  area: <module/path>
  risk: <low|medium|high>
  symptoms: <how the debt is observed>
  impact: <what breaks or drifts>
  remediation: <concrete fix>
  owner: <role/team>
  status: <open|in-progress|resolved>
  opened: <YYYY-MM-DD>
  updated: <YYYY-MM-DD>
```

## Governance

- New entries require evidence (link to issue/PR/test failure).
- Resolved entries must cite remediation commit.
- High-risk entries require mitigation plan and target date.

## Entries

_No entries yet._

