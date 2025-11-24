import json
import os
from typing import Any

import numpy as np
from numpy.typing import NDArray
from tenacity import retry, stop_after_attempt


def _save_numpy_arrays(filepath: str, arrays: dict[str, NDArray[Any]]) -> None:
    """Save arrays to .npz file with proper typing.

    This wrapper provides type safety for np.savez which has incorrect
    type stubs for **kwargs expansion.
    """
    # Call np.savez with unpacked dict - runtime is correct, stubs are wrong
    np.savez(filepath, **arrays)


@retry(stop=stop_after_attempt(3))
def _save_data(data: dict[str, Any], filepath: str) -> None:
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".json":
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    elif ext == ".npz":
        processed = {k: np.asarray(v) for k, v in data.items()}
        _save_numpy_arrays(filepath, processed)
    else:
        raise ValueError(f"Unsupported format: {ext}")


@retry(stop=stop_after_attempt(3))
def _load_data(filepath: str) -> dict[str, Any]:
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".json":
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)
    elif ext == ".npz":
        arrs = np.load(filepath, allow_pickle=True)
        return {k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in arrs.items()}
    else:
        raise ValueError(f"Unsupported format: {ext}")


class DataSerializer:
    @staticmethod
    def save(data: dict[str, Any], filepath: str) -> None:
        if not isinstance(filepath, str):
            raise TypeError("Filepath must be a string.")
        _save_data(data, filepath)

    @staticmethod
    def load(filepath: str) -> dict[str, Any]:
        if not isinstance(filepath, str):
            raise TypeError("Filepath must be a string.")
        return _load_data(filepath)
