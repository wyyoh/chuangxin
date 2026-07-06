# CPIPC Problem 10 ShareCone Engineering Workspace

This workspace implements a reproducible flow for CPIPC Problem 10:
multi-output logic cone sharing optimization on BLIF netlists using ABC.

Core rules:

- Every optimized candidate must pass ABC `cec`.
- Normal fallback is the best verified baseline.
- Original/identity output is only the last safety fallback.
- Offline portfolio search is for tuning only.
- Final submission uses either a fixed pipeline or a light feature selector.
- Feature selection must use coarse structural bins only, never file names,
  hashes, exact public-case fingerprints, or public-case directory names.
- ABC executable paths are always passed through command-line arguments.

Main phases:

1. Fetch public cases and freeze environment logs.
2. Build ABC and run smoke CEC.
3. Establish the evaluation loop and baseline metrics.
4. Run offline portfolio tuning and build a coarse selector.
5. Add ShareCone in three guarded steps: 5A empty command, 5B conservative
   sweep, 5C budgeted cut/divisor resubstitution.
6. Run CodeRabbit review when available.
7. Produce final metrics, CEC logs, failure report, and reproducibility notes.

