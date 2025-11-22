"""
Aphasia-Broca Evaluation Suite.

Використовує AphasiaBrocaDetector для оцінки:
- true_positive_rate для телеграфної мови
- true_negative_rate для нормальної мови
- середньої severity для телеграфних випадків
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mlsdm.extensions.neuro_lang_extension import AphasiaBrocaDetector


@dataclass
class AphasiaEvalResult:
    true_positive_rate: float
    true_negative_rate: float
    mean_severity_telegraphic: float
    telegraphic_samples: int
    normal_samples: int


class AphasiaEvalSuite:
    def __init__(self, corpus_path: str | Path) -> None:
        self.corpus_path = Path(corpus_path)
        self.detector = AphasiaBrocaDetector()

    def load_corpus(self) -> dict[str, list[str]]:
        data = json.loads(self.corpus_path.read_text(encoding="utf-8"))
        return {
            "telegraphic": list(data.get("telegraphic", [])),
            "normal": list(data.get("normal", [])),
        }

    def run(self) -> AphasiaEvalResult:
        corpus = self.load_corpus()
        tele = corpus["telegraphic"]
        norm = corpus["normal"]

        tp = 0
        tn = 0
        sev_sum = 0.0

        for text in tele:
            report = self.detector.analyze(text)
            if report["is_aphasic"]:
                tp += 1
            sev_sum += float(report["severity"])

        for text in norm:
            report = self.detector.analyze(text)
            if not report["is_aphasic"]:
                tn += 1

        tele_n = max(len(tele), 1)
        norm_n = max(len(norm), 1)

        return AphasiaEvalResult(
            true_positive_rate=tp / tele_n,
            true_negative_rate=tn / norm_n,
            mean_severity_telegraphic=sev_sum / tele_n,
            telegraphic_samples=len(tele),
            normal_samples=len(norm),
        )
