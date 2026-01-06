# Mutation Testing for MLSDM

## Overview

This directory contains mutation tests that validate the quality of the MLSDM test suite by introducing small bugs (mutants) into critical code paths and verifying that existing tests catch them.

**Target Mutation Score**: ≥80% for critical paths

## What is Mutation Testing?

Mutation testing measures test effectiveness by:
1. Introducing small code changes (mutations) like:
   - Changing `>=` to `>` in boundary checks
   - Modifying constants (`0.05` → `0.06`)
   - Altering boolean conditions (`and` → `or`)
2. Running the test suite against each mutant
3. Verifying that tests **fail** for mutated code (killed mutant)
4. Calculating mutation score = (killed mutants / total mutants) × 100%

A high mutation score indicates tests actually detect bugs, not just execute code.

## Critical Paths Tested

### 1. MoralFilterV2 (`test_moral_filter_mutations.py`)
**Module**: `src/mlsdm/cognition/moral_filter_v2.py`

**Critical Mutations**:
- Boundary conditions: `>=` vs `>` in `evaluate()`
- Threshold comparisons: `moral_value >= self.threshold`
- Adaptation delta: `_ADAPT_DELTA = 0.05`
- Clamping logic: `MIN_THRESHOLD` and `MAX_THRESHOLD` bounds
- EMA calculation: `EMA_ALPHA * signal + _ONE_MINUS_ALPHA * ema`

**Invariants Validated**:
- INV-MF-M1: Threshold stays in [MIN_THRESHOLD, MAX_THRESHOLD]
- INV-MF-M2: Smooth adaptation (no sudden jumps)
- INV-MF-M3: Bounded drift under adversarial attack

### 2. PhaseEntangledLatticeMemory (`test_pelm_mutations.py`)
**Module**: `src/mlsdm/memory/phase_entangled_lattice_memory.py`

**Critical Mutations**:
- Capacity overflow: `self.size >= self.capacity`
- Phase validation: `0.0 <= phase <= 1.0`
- Dimension matching: `len(vector) != self.dimension`
- Confidence threshold: `confidence < self._confidence_threshold`
- NaN/inf checks: `math.isnan(val) or math.isinf(val)`

**Invariants Validated**:
- INV-LLM-S1: Memory bounds (≤1.4 GB)
- INV-LLM-S2: Capacity constraint
- INV-LLM-L3: Memory overflow handling

### 3. CognitiveController (`test_cognitive_controller_mutations.py`)
**Module**: `src/mlsdm/core/cognitive_controller.py`

**Critical Mutations**:
- Emergency shutdown: `self.emergency_shutdown` state transitions
- Memory threshold: `memory_mb > self.memory_threshold_mb`
- Process event flow: moral rejection, sleep phase checks
- Recovery cooldown: auto-recovery timing logic
- Step counter: `self.step_counter += 1`

**Invariants Validated**:
- Emergency shutdown blocks processing
- Memory limits are enforced
- Recovery respects cooldown period

## Running Mutation Tests

### Prerequisites
```bash
pip install mutmut>=2.4.0
```

### Run All Mutation Tests
```bash
# Run tests normally first (should pass)
pytest tests/mutation/ -v

# Run mutation testing on critical modules
mutmut run --paths-to-mutate=src/mlsdm/cognition/moral_filter_v2.py
mutmut run --paths-to-mutate=src/mlsdm/memory/phase_entangled_lattice_memory.py
mutmut run --paths-to-mutate=src/mlsdm/core/cognitive_controller.py
```

### View Mutation Results
```bash
# Show summary
mutmut results

# Show specific mutant
mutmut show <mutant_id>

# Generate HTML report
mutmut html
```

### Configuration
Mutation testing is configured in `conftest.py` and `pyproject.toml`:
- Target paths for mutation
- Mutation score thresholds
- Timeout per mutant

## Interpreting Results

### Mutation Score Metrics
- **Killed**: Test detected the mutant (✅ good)
- **Survived**: Mutant passed all tests (❌ test gap)
- **Timeout**: Mutant caused infinite loop (⚠️ investigate)
- **Suspicious**: Mutant behavior anomalous (⚠️ investigate)

### Target Scores
| Module | Target | Current |
|--------|--------|---------|
| MoralFilterV2 | ≥80% | TBD |
| PELM | ≥80% | TBD |
| CognitiveController | ≥80% | TBD |

### What to Do About Survivors
If mutants survive (mutation score < 80%):
1. **Analyze the mutant**: `mutmut show <id>`
2. **Identify test gap**: What boundary case is missing?
3. **Add targeted test**: Cover the specific mutation
4. **Re-run**: Verify mutant is now killed

## CI Integration

Mutation tests run on a **weekly schedule** (not blocking PRs) via `.github/workflows/mutation-tests.yml`:
- Runs every Sunday at 00:00 UTC
- Reports mutation scores as artifacts
- Creates GitHub issue if score drops below 80%

## Best Practices

### Do:
- ✅ Focus on critical paths (safety, security, boundaries)
- ✅ Test boundary conditions thoroughly
- ✅ Validate invariants under adversarial input
- ✅ Add tests for survived mutants

### Don't:
- ❌ Aim for 100% mutation score (diminishing returns)
- ❌ Mutate trivial code (getters, logging)
- ❌ Block PRs on mutation test failures
- ❌ Ignore timeout mutants (may indicate real issues)

## References

- [Mutation Testing Overview](https://en.wikipedia.org/wiki/Mutation_testing)
- [mutmut Documentation](https://mutmut.readthedocs.io/)
- `docs/TEST_STRATEGY.md` - Testing strategy
- `docs/FORMAL_INVARIANTS.md` - Invariants to validate

## Support

For questions or issues with mutation testing:
1. Check mutmut documentation
2. Review existing mutant results
3. Consult `docs/TEST_STRATEGY.md`
4. Open an issue with `[mutation-test]` tag
