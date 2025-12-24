"""Thin wrapper to the canonical MLSDM CLI."""

from __future__ import annotations

import sys
from typing import List, Optional

from mlsdm.cli import main as _canonical_main


def main(argv: Optional[List[str]] = None) -> int:
    """Delegate to the canonical CLI entrypoint."""
    if argv is not None:
        sys.argv = ["mlsdm", *argv]
    return _canonical_main()


if __name__ == "__main__":
    sys.exit(main())
