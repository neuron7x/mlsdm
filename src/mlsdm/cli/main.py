"""
DEPRECATED: Legacy CLI for running memory simulation.

For the canonical MLSDM CLI, use:
    mlsdm --help
    mlsdm serve --help
    mlsdm check --help

This module provides a legacy interface for running standalone memory simulation.
It is not the recommended way to interact with MLSDM.
"""

import argparse
import json
import logging
import sys
import warnings

from mlsdm.core.memory_manager import MemoryManager
from mlsdm.utils.config_loader import ConfigLoader


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        return json.dumps(log_record)


handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.getLogger().addHandler(handler)
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    """Run legacy memory simulation.

    DEPRECATED: Use 'mlsdm serve' for HTTP API or 'mlsdm demo' for interactive demo.
    """
    warnings.warn(
        "mlsdm.cli.main is deprecated. Use 'mlsdm serve' for HTTP API "
        "or 'mlsdm demo' for interactive demo. See 'mlsdm --help' for options.",
        DeprecationWarning,
        stacklevel=2,
    )
    print(
        "NOTICE: This CLI is deprecated. Use 'mlsdm serve' or 'mlsdm demo' instead.",
        file=sys.stderr,
    )

    parser = argparse.ArgumentParser(
        description="[DEPRECATED] mlsdm memory simulation. Use 'mlsdm serve' instead."
    )
    parser.add_argument("--config", type=str, default="config/default_config.yaml")
    parser.add_argument("--steps", type=int, default=100)
    args = parser.parse_args()

    config = ConfigLoader.load_config(args.config)
    manager = MemoryManager(config)
    logger.info("Running simulation...")
    manager.run_simulation(args.steps)
    logger.info("Done.")


if __name__ == "__main__":
    main()
