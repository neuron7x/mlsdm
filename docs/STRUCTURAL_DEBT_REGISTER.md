# Structural Debt Register

This register tracks architecture-level debt. It is **not** a backlog for feature
work; it captures risks that degrade structural integrity.

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

## Entries

_No entries yet._

