import logging

from mlsdm.cognition.moral_filter_v2 import MoralFilterV2


def test_threshold_adaptation_logging(caplog):
    caplog.set_level(logging.DEBUG)
    moral_filter = MoralFilterV2(initial_threshold=0.5)

    moral_filter.adapt(True)
    moral_filter.adapt(True)

    assert any(
        "threshold adapted" in record.getMessage().lower() for record in caplog.records
    )
