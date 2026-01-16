from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from mlsdm.observability.policy_drift_telemetry import record_policy_registry_status
from mlsdm.policy.loader import DEFAULT_POLICY_DIR, PolicyLoadError, load_policy_bundle
from mlsdm.policy.registry import (
    REGISTRY_FILENAME,
    PolicyRegistryError,
    load_policy_registry,
    verify_policy_registry,
)

logger = logging.getLogger(__name__)


class PolicyDriftError(RuntimeError):
    """Raised when policy drift is detected or policy registry is invalid."""


@dataclass(frozen=True)
class PolicyDriftStatus:
    policy_name: str
    policy_hash: str
    policy_contract_version: str
    registry_hash: str | None
    registry_signature_valid: bool
    drift_detected: bool
    errors: tuple[str, ...]


@dataclass(frozen=True)
class PolicySnapshot:
    policy_name: str
    policy_hash: str
    policy_contract_version: str
    loaded_at: datetime


def _resolve_policy_dir(policy_dir: Path | None) -> Path:
    env_dir = os.getenv("MLSDM_POLICY_DIR")
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    return (policy_dir or DEFAULT_POLICY_DIR).resolve()


def _resolve_registry_path(policy_dir: Path, registry_path: Path | None) -> Path:
    env_path = os.getenv("MLSDM_POLICY_REGISTRY_PATH")
    if env_path:
        return Path(env_path).expanduser().resolve()
    return (registry_path or (policy_dir / REGISTRY_FILENAME)).resolve()


def check_policy_drift(
    *,
    policy_dir: Path | None = None,
    registry_path: Path | None = None,
    enforce: bool = True,
) -> PolicyDriftStatus:
    resolved_policy_dir = _resolve_policy_dir(policy_dir)
    resolved_registry_path = _resolve_registry_path(resolved_policy_dir, registry_path)
    errors: list[str] = []
    registry_hash: str | None = None
    registry_signature_valid = False

    try:
        bundle = load_policy_bundle(resolved_policy_dir, enforce_registry=False)
    except PolicyLoadError as exc:
        errors.append(str(exc))
        status = PolicyDriftStatus(
            policy_name="unknown",
            policy_hash="unavailable",
            policy_contract_version="unknown",
            registry_hash=None,
            registry_signature_valid=False,
            drift_detected=True,
            errors=tuple(errors),
        )
        record_policy_registry_status(
            policy_name=status.policy_name,
            policy_hash=status.policy_hash,
            policy_contract_version=status.policy_contract_version,
            registry_hash=None,
            registry_signature_valid=False,
            drift_detected=True,
            reason="policy_load_error",
        )
        if enforce:
            raise PolicyDriftError(str(exc)) from exc
        return status

    policy_name = bundle.security_baseline.policy_name
    policy_hash = bundle.policy_hash
    policy_contract_version = bundle.security_baseline.policy_contract_version

    try:
        registry = load_policy_registry(resolved_registry_path)
        registry_hash = registry.policy_hash
        registry_signature_valid = True
        try:
            verify_policy_registry(
                policy_hash=policy_hash,
                policy_contract_version=policy_contract_version,
                registry=registry,
            )
        except PolicyRegistryError as exc:
            errors.append(str(exc))
    except PolicyRegistryError as exc:
        errors.append(str(exc))

    drift_detected = bool(errors)
    record_policy_registry_status(
        policy_name=policy_name,
        policy_hash=policy_hash,
        policy_contract_version=policy_contract_version,
        registry_hash=registry_hash,
        registry_signature_valid=registry_signature_valid,
        drift_detected=drift_detected,
        reason=";".join(errors) if errors else None,
    )

    if drift_detected:
        logger.error("Policy drift detected: %s", "; ".join(errors))
        if enforce:
            raise PolicyDriftError("; ".join(errors))

    return PolicyDriftStatus(
        policy_name=policy_name,
        policy_hash=policy_hash,
        policy_contract_version=policy_contract_version,
        registry_hash=registry_hash,
        registry_signature_valid=registry_signature_valid,
        drift_detected=drift_detected,
        errors=tuple(errors),
    )


@lru_cache(maxsize=1)
def get_policy_snapshot(
    *,
    policy_dir: Path | None = None,
    registry_path: Path | None = None,
) -> PolicySnapshot:
    status = check_policy_drift(
        policy_dir=policy_dir,
        registry_path=registry_path,
        enforce=True,
    )
    return PolicySnapshot(
        policy_name=status.policy_name,
        policy_hash=status.policy_hash,
        policy_contract_version=status.policy_contract_version,
        loaded_at=datetime.utcnow(),
    )
