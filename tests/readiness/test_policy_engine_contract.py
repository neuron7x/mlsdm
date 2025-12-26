from __future__ import annotations

import scripts.readiness.policy_engine as pe


def _base_change(paths, max_risk="high"):
    return {
        "max_risk": max_risk,
        "files": [{"path": p} for p in paths],
        "counts": {"categories": {}, "risks": {}},
    }


def _empty_evidence():
    return {
        "sources": {"junit": {"found": False}},
        "tests": {"totals": {"passed": 0, "failed": 0, "skipped": 0}},
        "security": {"tools": [], "measured": False},
    }


def test_core_changes_require_tests():
    change = _base_change(["src/mlsdm/core/module.py"], max_risk="critical")
    evidence = _empty_evidence()
    policy = pe.evaluate_policy(change, evidence)
    assert policy["verdict"] in ("reject", "manual_review")
    assert any(rule["rule_id"] == "CORE-001" for rule in policy["matched_rules"])
    assert policy["max_risk"] in ("high", "critical")


def test_infra_security_rejects_when_findings_present():
    change = _base_change([".github/workflows/readiness.yml"], max_risk="medium")
    evidence = {
        "sources": {"junit": {"found": True}},
        "tests": {"totals": {"passed": 1, "failed": 0, "skipped": 0}},
        "security": {
            "measured": True,
            "tools": [{"tool": "bandit", "high": 1, "medium": 0, "low": 0, "measured": True}],
        },
    }
    policy = pe.evaluate_policy(change, evidence)
    assert policy["verdict"] == "reject"
    assert any(rule["rule_id"] == "INFRA-001" for rule in policy["matched_rules"])
    assert policy["max_risk"] in ("high", "medium", "critical")
