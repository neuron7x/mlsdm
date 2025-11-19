import numpy as np
from typing import Dict, Tuple, Any


class MultiLevelSynapticMemory:
    def __init__(
        self,
        dimension: int,
        lambda_l1: float = 0.5,
        lambda_l2: float = 0.1,
        lambda_l3: float = 0.01,
        theta_l1: float = 1.0,
        theta_l2: float = 2.0,
        gating12: float = 0.5,
        gating23: float = 0.3,
    ) -> None:
        self.dim = int(dimension)
        self.lambda_l1 = float(lambda_l1)
        self.lambda_l2 = float(lambda_l2)
        self.lambda_l3 = float(lambda_l3)
        self.theta_l1 = float(theta_l1)
        self.theta_l2 = float(theta_l2)
        self.gating12 = float(gating12)
        self.gating23 = float(gating23)

        self.state_L1 = np.zeros(self.dim, dtype=float)
        self.state_L2 = np.zeros(self.dim, dtype=float)
        self.state_L3 = np.zeros(self.dim, dtype=float)

    def update(self, event_vector: np.ndarray) -> None:
        if not isinstance(event_vector, np.ndarray) or event_vector.shape[0] != self.dim:
            raise ValueError(f"Event vector must be a NumPy array of dimension {self.dim}.")

        self.state_L1 += event_vector
        self.state_L1 *= 1.0 - self.lambda_l1
        self.state_L2 *= 1.0 - self.lambda_l2
        self.state_L3 *= 1.0 - self.lambda_l3

        mask_L1 = self.state_L1 > self.theta_l1
        transfer_L1 = self.state_L1 * mask_L1 * self.gating12
        self.state_L2 += transfer_L1
        self.state_L1 -= transfer_L1

        mask_L2 = self.state_L2 > self.theta_l2
        transfer_L2 = self.state_L2 * mask_L2 * self.gating23
        self.state_L3 += transfer_L2
        self.state_L2 -= transfer_L2

    def get_state(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        return self.state_L1.copy(), self.state_L2.copy(), self.state_L3.copy()

    def reset_all(self) -> None:
        self.state_L1.fill(0.0)
        self.state_L2.fill(0.0)
        self.state_L3.fill(0.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dim,
            "lambda_l1": self.lambda_l1,
            "lambda_l2": self.lambda_l2,
            "lambda_l3": self.lambda_l3,
            "theta_l1": self.theta_l1,
            "theta_l2": self.theta_l2,
            "gating12": self.gating12,
            "gating23": self.gating23,
            "state_L1": self.state_L1.tolist(),
            "state_L2": self.state_L2.tolist(),
            "state_L3": self.state_L3.tolist(),
        }
