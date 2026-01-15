from pathlib import Path

from mlsdm.config.architecture_manifest import ARCHITECTURE_MANIFEST, KNOWN_LAYERS


def test_manifest_layers_and_paths_exist() -> None:
    for module in ARCHITECTURE_MANIFEST:
        assert module.layer in KNOWN_LAYERS
        assert module.absolute_path().exists()
        for interface_path in module.interface_paths():
            assert interface_path.exists(), f"Missing interface file: {interface_path}"


def test_manifest_public_interfaces_are_relative() -> None:
    for module in ARCHITECTURE_MANIFEST:
        for interface in module.public_interfaces:
            assert not Path(interface).is_absolute()
