import numpy as np

from mlsdm.core.cognitive_controller import CognitiveController


def test_phase_check_happens_before_rhythm_advance() -> None:
    """Events should be processed using the current phase, not the next step."""
    controller = CognitiveController(dim=10)
    wake_duration = controller.rhythm.wake_duration

    for i in range(wake_duration):
        vec = np.ones(10, dtype=np.float32)
        result = controller.process_event(vec, moral_value=0.9)

        assert not result["rejected"], (
            f"Event {i + 1}/{wake_duration} should be accepted in wake phase, "
            f"but got: {result}"
        )

    sleep_duration = controller.rhythm.sleep_duration
    for i in range(sleep_duration):
        vec = np.ones(10, dtype=np.float32)
        result = controller.process_event(vec, moral_value=0.9)

        assert result["rejected"], (
            f"Event {wake_duration + i + 1} should be rejected in sleep phase"
        )
        assert "sleep phase" in result["note"].lower(), (
            f"Expected 'sleep phase' rejection, got: {result['note']}"
        )


def test_phase_transition_boundary() -> None:
    """Verify wake/sleep boundaries follow the configured 8+3 cadence."""
    controller = CognitiveController(dim=10)

    results = []
    for i in range(20):
        vec = np.random.randn(10).astype(np.float32)
        result = controller.process_event(vec, moral_value=0.9)
        results.append(result)

    expected_pattern = ["wake"] * 8 + ["sleep"] * 3 + ["wake"] * 8 + ["sleep"] * 1
    actual_pattern = []
    for result in results:
        if result["rejected"] and "sleep phase" in result["note"].lower():
            actual_pattern.append("sleep")
        elif not result["rejected"]:
            actual_pattern.append("wake")
        else:
            actual_pattern.append(f"rejected:{result['note']}")

    assert actual_pattern == expected_pattern, (
        f"\nExpected: {expected_pattern}\n"
        f"Actual:   {actual_pattern}"
    )
