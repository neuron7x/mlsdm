from __future__ import annotations

from dataclasses import dataclass

from mlsdm.memory.provenance import MemoryProvenance, MemorySource


@dataclass(frozen=True)
class ProvenanceWriteDecision:
    quarantined: bool
    reject: bool
    reason: str | None = None


@dataclass(frozen=True)
class MemoryProvenancePolicy:
    quarantine_confidence: float = 0.7
    quarantined_sources: tuple[MemorySource, ...] = (MemorySource.LLM_GENERATION,)
    store_min_confidence: float = 0.0

    def decide_write(self, provenance: MemoryProvenance) -> ProvenanceWriteDecision:
        if provenance.confidence < self.store_min_confidence:
            return ProvenanceWriteDecision(
                quarantined=True,
                reject=True,
                reason="confidence_below_store_min",
            )

        quarantined = (
            provenance.source in self.quarantined_sources
            or provenance.confidence < self.quarantine_confidence
        )
        reason = None
        if quarantined:
            reason = (
                "llm_source" if provenance.source in self.quarantined_sources else "low_confidence"
            )
        return ProvenanceWriteDecision(quarantined=quarantined, reject=False, reason=reason)

    def allow_retrieval(
        self,
        provenance: MemoryProvenance,
        *,
        include_quarantined: bool,
        min_confidence: float,
    ) -> bool:
        if provenance.confidence < min_confidence:
            return False
        if not include_quarantined and (
            provenance.source in self.quarantined_sources
            or provenance.confidence < self.quarantine_confidence
        ):
            return False
        return True
