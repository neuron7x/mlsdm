# Memory Provenance Schema and Lifecycle

## Schema (required fields)

Each memory record **must** include a provenance payload with the following required fields:

| Field | Type | Description |
| --- | --- | --- |
| `source` | enum | Origin of the memory (e.g., user input, LLM generation, system prompt). |
| `confidence` | float | Reliability score in `[0.0, 1.0]`. |
| `timestamp` | datetime | Creation/ingestion time of the memory record. |
| `source_id` | string | Identifier of the originating source (user id, service id, model id). |
| `ingestion_path` | string | Pipeline or subsystem path that ingested the memory. |
| `content_hash` | string | SHA256 hash of the memory content at ingestion. |
| `policy_hash` | string | SHA256 hash of the active policy bundle at ingestion. |
| `trust_tier` | int | Trust tier in `[0, 3]` (`0` = untrusted, `3` = highest trust). |
| `llm_model` | string \| null | Model identifier when `source` is LLM-generated. |
| `parent_id` | string \| null | Optional parent memory id for lineage chains. |

### Validation requirements

All provenance fields above are validated on creation/ingestion:

* `source_id` and `ingestion_path` must be non-empty strings.
* `content_hash` and `policy_hash` must be 64-character lowercase SHA256 hex digests.
* `trust_tier` must be an integer in `[0, 3]`.
* `content_hash` **must** match the canonical hash of the stored memory content.
* `policy_hash` **must** match the active policy bundle hash at ingestion time.

## Lifecycle and immutability

1. **Creation/ingestion**: Every memory write is rejected unless a valid provenance payload is provided.
2. **Integrity enforcement**: Content/policy hash validation occurs at ingestion time, not at retrieval.
3. **Immutable storage**:
   * **PELM**: Each entangle operation appends a provenance log entry to an in-memory, hash-chained ledger.
   * **SQLite LTM**: Each write appends to a `provenance_log` table with a hash chain (`prev_hash` ➜ `entry_hash`).
4. **Retrieval**: Returned memories include provenance fields for lineage inspection and trust-tier gating.

This schema and lifecycle are mandatory for all memory backends and ingestion paths.
