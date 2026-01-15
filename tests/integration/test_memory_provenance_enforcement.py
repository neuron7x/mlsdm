from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from mlsdm.memory.phase_entangled_lattice_memory import PhaseEntangledLatticeMemory
from mlsdm.memory.provenance import MemoryProvenance, MemorySource


def test_llm_provenance_quarantined_by_default() -> None:
    pelm = PhaseEntangledLatticeMemory(dimension=4, capacity=10)
    provenance = MemoryProvenance(
        source=MemorySource.LLM_GENERATION,
        confidence=0.9,
        timestamp=datetime.now(),
        llm_model="unit-test",
    )
    idx = pelm.entangle([1.0, 2.0, 3.0, 4.0], phase=0.5, provenance=provenance)
    assert idx >= 0
    assert pelm._quarantined[0] is True

    results = pelm.retrieve([1.0, 2.0, 3.0, 4.0], current_phase=0.5, top_k=1)
    assert results == []

    results_quarantined = pelm.retrieve(
        [1.0, 2.0, 3.0, 4.0],
        current_phase=0.5,
        top_k=1,
        include_quarantined=True,
    )
    assert len(results_quarantined) == 1

    evidence = {
        "memory_id": results_quarantined[0].memory_id,
        "source": results_quarantined[0].provenance.source.value,
        "confidence": results_quarantined[0].provenance.confidence,
        "quarantined": pelm._quarantined[0],
    }
    evidence_dir = Path("artifacts") / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "provenance_integrity_report.json").write_text(
        json.dumps(evidence, indent=2), encoding="utf-8"
    )
