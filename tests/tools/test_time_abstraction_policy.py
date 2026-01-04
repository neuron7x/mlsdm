from __future__ import annotations

import re
import tokenize
from io import StringIO
from pathlib import Path


def _has_injection_indicator(text: str) -> bool:
    lowered = text.lower()
    return ("now:" in lowered or "clock:" in lowered) and (
        "self._now" in lowered or "self._clock" in lowered
    )


def _is_allowed_time_time(line: str) -> bool:
    lowered = line.lower()
    return (
        "else time.time(" in line
        or bool(re.search(r"\bor\s+time\.time\b", line))
        or "or time.time(" in line
        or ("time.time" in line and "default" in lowered)
    )


def _is_allowed_perf_counter(line: str) -> bool:
    lowered = line.lower()
    return (
        bool(re.search(r"\bor\s+time\.perf_counter\b", line))
        or "or time.perf_counter(" in line
        or "else time.perf_counter" in line
        or ("time.perf_counter" in line and "default" in lowered)
    )


def _find_disallowed_calls(path: Path, text: str, repo_root: Path) -> list[str]:
    offenders: list[str] = []
    skip_lines: set[int] = set()

    for token in tokenize.generate_tokens(StringIO(text).readline):
        if token.type in {tokenize.STRING, tokenize.COMMENT}:
            skip_lines.update(range(token.start[0], token.end[0] + 1))

    for lineno, line in enumerate(text.splitlines(), start=1):
        if lineno in skip_lines:
            continue

        stripped = line.strip()
        if "time.time(" in line and not _is_allowed_time_time(line):
            offenders.append(f"{path.relative_to(repo_root)}:{lineno} -> {stripped}")
        if "time.perf_counter(" in line and not _is_allowed_perf_counter(line):
            offenders.append(f"{path.relative_to(repo_root)}:{lineno} -> {stripped}")

    return offenders


def test_time_abstraction_policy() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    target_files = [
        repo_root / "src/mlsdm/utils/cache.py",
        repo_root / "src/mlsdm/utils/config_loader.py",
        repo_root / "src/mlsdm/utils/rate_limiter.py",
        repo_root / "src/mlsdm/utils/circuit_breaker.py",
        repo_root / "src/mlsdm/utils/bulkhead.py",
    ]

    missing_injection: list[str] = []
    wall_clock_offenders: list[str] = []

    for path in target_files:
        text = path.read_text(encoding="utf-8")
        if not _has_injection_indicator(text):
            missing_injection.append(str(path.relative_to(repo_root)))
        wall_clock_offenders.extend(_find_disallowed_calls(path, text, repo_root))

    messages: list[str] = []
    if missing_injection:
        messages.append(
            "Rule A violated (inject time source and store as self._now/self._clock):\n"
            + "\n".join(sorted(missing_injection))
        )
    if wall_clock_offenders:
        messages.append(
            "Rule B violated (direct wall-clock calls beyond fallback):\n"
            + "\n".join(sorted(wall_clock_offenders))
            + "\nIntroduce injected clock/now callable and use self._now()/self._clock()."
        )

    assert not messages, "\n\n".join(messages)
