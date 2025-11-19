Security Policy

- Input Validation: strict type and range checks at API boundary.
- Rate Limiting: 5 RPS per client (per API key or IP) via leaky-bucket.
- Auth: Bearer token (env API_KEY).
- Logs: Structured JSON, no PII.
- Secrets: Environment variables only.
- Audit: Important state changes are logged with correlation IDs.
- Scans: `pip-audit` in CI for dependency vulnerabilities.
