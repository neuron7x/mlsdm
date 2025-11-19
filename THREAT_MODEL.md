Threat Model (STRIDE)

- Spoofing: OAuth2-style bearer tokens, TLS termination.
- Tampering: Input validation, immutable audit logs.
- Repudiation: Correlation IDs and structured logs.
- Information Disclosure: No PII stored; pseudonymized vectors.
- Denial of Service: 5 RPS limit per client + K8s resource limits.
- Elevation of Privilege: Non-root containers, least-privilege runtime.

Attack Tree root: API compromise → injection, brute-force, DoS.
