"""SQLite-backed MemoryStore implementation for persistent LTM.

This module provides a SQLite-based implementation of the MemoryStore protocol
with support for:
- TTL-based retention and eviction
- Optional encryption-at-rest using AESGCM
- PII scrubbing before persistence
- Content hashing for deduplication
- Efficient indexing for queries

Security properties:
- PII scrubbed by default (unless store_raw=True)
- Optional encryption (enabled only when explicitly configured)
- Never crashes on import (lazy initialization)
- Clear ConfigurationError if encryption enabled but unavailable
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
from typing import Any, cast

from mlsdm.memory.provenance import MemoryProvenance, get_policy_hash
from mlsdm.memory.store import MemoryItem
from mlsdm.security.payload_scrubber import scrub_text
from mlsdm.utils.errors import ConfigurationError

logger = logging.getLogger(__name__)

# Optional cryptography import - only used when encryption is enabled
_CRYPTOGRAPHY_AVAILABLE = False
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM as _AESGCM

    AESGCM: type[Any] | None = _AESGCM
    _CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    AESGCM = None


class SQLiteMemoryStore:
    """SQLite-backed long-term memory store with optional encryption.

    Features:
    - Persistent storage with SQLite backend
    - TTL-based automatic eviction
    - Optional encryption-at-rest (AESGCM)
    - PII scrubbing before storage
    - Content hashing for deduplication
    - LIKE-based text search (v1)

    Args:
        db_path: Path to SQLite database file
        encryption_key: Optional encryption key (32 bytes). If provided,
            content will be encrypted at rest. Requires cryptography package.
        store_raw: If True, store content without PII scrubbing (default: False)

    Raises:
        ConfigurationError: If encryption enabled but cryptography unavailable
    """

    def __init__(
        self,
        db_path: str,
        *,
        encryption_key: bytes | None = None,
        store_raw: bool = False,
    ) -> None:
        """Initialize SQLite memory store.

        Note: No SQLite IO happens during init. Database is opened lazily
        on first use to avoid import-time side effects.
        """
        self.db_path = db_path
        self.store_raw = store_raw
        self._conn: sqlite3.Connection | None = None

        # Encryption setup
        self._encryption_key = encryption_key
        self._cipher: Any = None  # AESGCM instance or None

        if encryption_key is not None:
            if not _CRYPTOGRAPHY_AVAILABLE:
                raise ConfigurationError(
                    message=(
                        "Encryption-at-rest is enabled but cryptography package "
                        "is not installed. Install with: pip install "
                        "mlsdm-governed-cognitive-memory[ltm]"
                    )
                )
            if len(encryption_key) != 32:
                raise ConfigurationError(
                    message=f"Encryption key must be exactly 32 bytes, got {len(encryption_key)}"
                )
            # Initialize cipher
            assert AESGCM is not None  # Type narrowing
            self._cipher = AESGCM(encryption_key)
            logger.info("LTM encryption-at-rest enabled")

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection (lazy initialization)."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row  # Enable dict-like access
            self._init_schema()
        return self._conn

    def _init_schema(self) -> None:
        """Initialize database schema if not exists."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Create main memories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                ts REAL NOT NULL,
                ttl_s REAL,
                content TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                pii_flags TEXT,
                provenance_json TEXT,
                ciphertext BLOB,
                nonce BLOB,
                alg TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS provenance_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id TEXT NOT NULL,
                ts REAL NOT NULL,
                provenance_json TEXT NOT NULL,
                prev_hash TEXT,
                entry_hash TEXT NOT NULL
            )
        """)

        # Create indexes for efficient queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_ts
            ON memories(ts)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_content_hash
            ON memories(content_hash)
        """)

        conn.commit()
        logger.debug("SQLite LTM schema initialized at %s", self.db_path)

    def _encrypt_content(self, content: str) -> tuple[bytes, bytes]:
        """Encrypt content using AESGCM.

        Args:
            content: Plaintext content to encrypt

        Returns:
            Tuple of (ciphertext, nonce)
        """
        if self._cipher is None:
            raise RuntimeError("Encryption not configured")

        # Generate random nonce (12 bytes for GCM)
        nonce = os.urandom(12)

        # Encrypt
        ciphertext = self._cipher.encrypt(nonce, content.encode("utf-8"), None)

        return ciphertext, nonce

    def _decrypt_content(self, ciphertext: bytes, nonce: bytes) -> str:
        """Decrypt content using AESGCM.

        Args:
            ciphertext: Encrypted content
            nonce: Nonce used during encryption

        Returns:
            Decrypted plaintext content
        """
        if self._cipher is None:
            raise RuntimeError("Encryption not configured")

        plaintext_bytes = cast("bytes", self._cipher.decrypt(nonce, ciphertext, None))
        return plaintext_bytes.decode("utf-8")

    def put(self, item: MemoryItem) -> str:
        """Store a memory item in SQLite.

        The content is:
        1. Scrubbed for PII (unless store_raw=True)
        2. Optionally encrypted (if encryption_key provided)
        3. Stored with metadata and content hash

        Args:
            item: Memory item to store

        Returns:
            The ID of the stored item
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        if item.provenance is None:
            raise ValueError("provenance is required for memory persistence.")
        if item.provenance.content_hash != item.content_hash:
            raise ValueError("provenance content_hash does not match item content_hash.")
        if item.provenance.policy_hash != get_policy_hash():
            raise ValueError("provenance policy_hash does not match active policy hash.")

        # Prepare content
        content_to_store = item.content
        if not self.store_raw:
            # Scrub PII before storing
            content_to_store = scrub_text(content_to_store, scrub_emails=True)

        # Prepare encryption fields
        ciphertext: bytes | None = None
        nonce: bytes | None = None
        alg: str | None = None
        stored_content = content_to_store

        if self._cipher is not None:
            # Encrypt the (possibly scrubbed) content
            ciphertext, nonce = self._encrypt_content(content_to_store)
            alg = "AESGCM"
            # Store encrypted version in content field too for consistency
            stored_content = "<encrypted>"

        # Serialize JSON fields
        pii_flags_json = json.dumps(item.pii_flags) if item.pii_flags else None
        provenance_json = json.dumps(item.provenance.to_dict(), sort_keys=True)

        # Insert or replace
        cursor.execute("""
            INSERT OR REPLACE INTO memories
            (id, ts, ttl_s, content, content_hash, pii_flags, provenance_json,
             ciphertext, nonce, alg)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item.id,
            item.ts,
            item.ttl_s,
            stored_content,
            item.content_hash,
            pii_flags_json,
            provenance_json,
            ciphertext,
            nonce,
            alg,
        ))

        conn.commit()
        logger.debug("Stored memory item %s (encrypted=%s)", item.id, alg is not None)

        self._append_provenance_log(cursor, item.id, item.ts, provenance_json)
        conn.commit()

        return item.id

    def get(self, item_id: str) -> MemoryItem | None:
        """Retrieve a memory item by ID.

        If the content was encrypted, it will be decrypted before returning.

        Args:
            item_id: Unique identifier of the memory

        Returns:
            MemoryItem if found, None otherwise
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, ts, ttl_s, content, content_hash, pii_flags,
                   provenance_json, ciphertext, nonce, alg
            FROM memories
            WHERE id = ?
        """, (item_id,))

        row = cursor.fetchone()
        if row is None:
            return None

        # Decrypt content if encrypted
        content = row["content"]
        if row["ciphertext"] is not None and row["nonce"] is not None:
            content = self._decrypt_content(row["ciphertext"], row["nonce"])

        # Parse JSON fields
        pii_flags: dict[str, Any] = {}
        if row["pii_flags"]:
            pii_flags = json.loads(row["pii_flags"])

        provenance: MemoryProvenance | None = None
        if row["provenance_json"]:
            prov_data = json.loads(row["provenance_json"])
            try:
                provenance = MemoryProvenance.from_dict(prov_data)
            except Exception as exc:
                logger.warning("Invalid provenance for memory %s: %s", row["id"], exc)

        return MemoryItem(
            id=row["id"],
            ts=row["ts"],
            content=content,
            content_hash=row["content_hash"],
            ttl_s=row["ttl_s"],
            pii_flags=pii_flags,
            provenance=provenance,
        )

    def query(
        self,
        text: str,
        *,
        limit: int = 10,
        since_ts: float | None = None,
        tags: list[str] | None = None,
    ) -> list[MemoryItem]:
        """Query memories by text content using LIKE search.

        Note: This does not search encrypted content in v1.
        Future versions may support semantic search.

        Args:
            text: Text to search for in content
            limit: Maximum number of results to return
            since_ts: Only return memories created after this timestamp
            tags: Reserved for future use

        Returns:
            List of matching MemoryItem objects, ordered by recency
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build query
        query_sql = """
            SELECT id, ts, ttl_s, content, content_hash, pii_flags,
                   provenance_json, ciphertext, nonce, alg
            FROM memories
            WHERE content LIKE ?
        """
        params: list[Any] = [f"%{text}%"]

        if since_ts is not None:
            query_sql += " AND ts >= ?"
            params.append(since_ts)

        query_sql += " ORDER BY ts DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query_sql, params)
        rows = cursor.fetchall()

        # Convert rows to MemoryItem objects
        items: list[MemoryItem] = []
        for row in rows:
            # Decrypt content if encrypted
            content = row["content"]
            if row["ciphertext"] is not None and row["nonce"] is not None:
                try:
                    content = self._decrypt_content(row["ciphertext"], row["nonce"])
                except Exception as e:
                    logger.warning("Failed to decrypt memory %s: %s", row["id"], e)
                    continue

            # Parse JSON fields
            pii_flags: dict[str, Any] = {}
            if row["pii_flags"]:
                pii_flags = json.loads(row["pii_flags"])

            provenance: MemoryProvenance | None = None
            if row["provenance_json"]:
                prov_data = json.loads(row["provenance_json"])
                try:
                    provenance = MemoryProvenance.from_dict(prov_data)
                except Exception as exc:
                    logger.warning("Invalid provenance for memory %s: %s", row["id"], exc)

            items.append(MemoryItem(
                id=row["id"],
                ts=row["ts"],
                content=content,
                content_hash=row["content_hash"],
                ttl_s=row["ttl_s"],
                pii_flags=pii_flags,
                provenance=provenance,
            ))

        return items

    def evict_expired(self, now_ts: float) -> int:
        """Remove expired memories based on TTL.

        Deletes all memories where ts + ttl_s < now_ts.

        Args:
            now_ts: Current timestamp for comparison

        Returns:
            Number of items evicted
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Delete expired items (those with TTL where ts + ttl_s < now_ts)
        cursor.execute("""
            DELETE FROM memories
            WHERE ttl_s IS NOT NULL
              AND (ts + ttl_s) < ?
        """, (now_ts,))

        deleted_count = cursor.rowcount
        conn.commit()

        if deleted_count > 0:
            logger.info("Evicted %d expired memories", deleted_count)

        return deleted_count

    def compact(self) -> None:
        """Perform VACUUM to reclaim space from deleted rows."""
        conn = self._get_connection()

        # Get size before vacuum
        cursor = conn.cursor()
        cursor.execute("PRAGMA page_count")
        page_count_before = cursor.fetchone()[0]

        # VACUUM must be run outside transaction
        conn.execute("VACUUM")

        cursor.execute("PRAGMA page_count")
        page_count_after = cursor.fetchone()[0]

        logger.info(
            "LTM compaction complete (pages: %d -> %d)",
            page_count_before,
            page_count_after,
        )

    def stats(self) -> dict[str, Any]:
        """Get storage statistics.

        Returns:
            Dictionary with:
            - total_items: Number of stored items
            - db_size_bytes: Database file size
            - oldest_ts: Timestamp of oldest item
            - newest_ts: Timestamp of newest item
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Count total items
        cursor.execute("SELECT COUNT(*) FROM memories")
        total_items = cursor.fetchone()[0]

        # Get timestamp range
        cursor.execute("SELECT MIN(ts), MAX(ts) FROM memories")
        row = cursor.fetchone()
        oldest_ts = row[0] if row[0] is not None else None
        newest_ts = row[1] if row[1] is not None else None

        # Get database size
        db_size_bytes = 0
        if os.path.exists(self.db_path):
            db_size_bytes = os.path.getsize(self.db_path)

        return {
            "total_items": total_items,
            "db_size_bytes": db_size_bytes,
            "oldest_ts": oldest_ts,
            "newest_ts": newest_ts,
        }

    def close(self) -> None:
        """Close database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
            logger.debug("Closed LTM database connection")

    def _append_provenance_log(
        self,
        cursor: sqlite3.Cursor,
        memory_id: str,
        ts: float,
        provenance_json: str,
    ) -> None:
        cursor.execute("SELECT entry_hash FROM provenance_log ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        prev_hash = row[0] if row is not None else None
        hash_payload = f"{prev_hash or ''}|{memory_id}|{ts}|{provenance_json}".encode("utf-8")
        entry_hash = hashlib.sha256(hash_payload).hexdigest()
        cursor.execute(
            """
            INSERT INTO provenance_log (memory_id, ts, provenance_json, prev_hash, entry_hash)
            VALUES (?, ?, ?, ?, ?)
            """,
            (memory_id, ts, provenance_json, prev_hash, entry_hash),
        )

    def __del__(self) -> None:
        """Ensure connection is closed on cleanup."""
        self.close()
