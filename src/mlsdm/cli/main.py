import argparse
import json
import logging

from mlsdm.config.defaults import DEFAULT_CONFIG_PATH
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
    parser = argparse.ArgumentParser(description="mlsdm-governed-cognitive-memory CLI")
    parser.add_argument("--config", type=str, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--steps", type=int, default=100)
    args = parser.parse_args()

    config = ConfigLoader.load_config(args.config)
    manager = MemoryManager(config)
    logger.info("Running simulation...")
    manager.run_simulation(args.steps)
    logger.info("Done.")


if __name__ == "__main__":
    main()
