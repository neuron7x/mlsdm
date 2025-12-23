#!/usr/bin/env python3
"""Cloud wrapper delegating to the canonical serve entrypoint."""

from __future__ import annotations

from typing import Any


def main(*, profile: str = "cloud", **kwargs: Any) -> int:
    from mlsdm.entrypoints.serve import serve

    return serve(profile=profile, **kwargs)
