from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mlsdm.policy.loader import PolicyLoadError, load_policy_bundle
from mlsdm.policy.registry import (
    REGISTRY_FILENAME,
    PolicyRegistryError,
    build_policy_registry,
    load_policy_registry,
    verify_policy_registry,
    write_policy_registry,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def _resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else (REPO_ROOT / path).resolve()


def run_policy_registry_check(
    *,
    policy_dir: Path,
    registry_path: Path | None,
) -> int:
    resolved_policy_dir = _resolve_path(policy_dir)
    resolved_registry_path = _resolve_path(registry_path) if registry_path else None
    registry_file = resolved_registry_path or (resolved_policy_dir / REGISTRY_FILENAME)

    try:
        bundle = load_policy_bundle(resolved_policy_dir, enforce_registry=False)
        registry = load_policy_registry(registry_file)
        verify_policy_registry(
            policy_hash=bundle.policy_hash,
            policy_contract_version=bundle.security_baseline.policy_contract_version,
            registry=registry,
        )
    except (PolicyLoadError, PolicyRegistryError) as exc:
        print(f"ERROR: {exc}")
        return 1

    print("✓ Policy registry hash matches canonical policy bundle.")
    return 0


def run_policy_registry_export(
    *,
    policy_dir: Path,
    registry_path: Path | None,
) -> int:
    resolved_policy_dir = _resolve_path(policy_dir)
    resolved_registry_path = _resolve_path(registry_path) if registry_path else None
    registry_file = resolved_registry_path or (resolved_policy_dir / REGISTRY_FILENAME)

    try:
        bundle = load_policy_bundle(resolved_policy_dir, enforce_registry=False)
        registry = build_policy_registry(
            policy_hash=bundle.policy_hash,
            policy_contract_version=bundle.security_baseline.policy_contract_version,
        )
        write_policy_registry(registry_file, registry)
    except (PolicyLoadError, PolicyRegistryError) as exc:
        print(f"ERROR: {exc}")
        return 1

    print(f"✓ Wrote policy registry to {registry_file}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify or export the policy registry")
    parser.add_argument(
        "--policy-dir",
        type=Path,
        default=Path("policy"),
        help="Path to policy directory (default: policy/)",
    )
    parser.add_argument(
        "--registry-path",
        type=Path,
        default=None,
        help="Path to policy registry JSON (default: policy/registry.json)",
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="Export a registry file instead of verifying",
    )
    args = parser.parse_args()

    if args.export:
        return run_policy_registry_export(
            policy_dir=args.policy_dir,
            registry_path=args.registry_path,
        )

    return run_policy_registry_check(
        policy_dir=args.policy_dir,
        registry_path=args.registry_path,
    )


if __name__ == "__main__":
    sys.exit(main())
