# ShareCone Algorithm Notes

Phase 5A was intentionally behavior-preserving: `sharecone -n` only prints `PI`, `PO`, AIG node count, level count, and whether the current network is strashed.

Phase 5B v1 keeps the implementation conservative by delegating the actual equivalent-node merge to ABC's existing small-budget `fraig` command (`-R 256 -D 256 -C 16`). This is a functional sweep candidate, not a final acceptance decision: the outer evaluator still runs CEC and rejects crash, CEC failure, or metric regression against the verified baseline.

Phase 5C v2 is exposed as `sharecone -2`. It runs v1 and then a bounded ABC `resub` pass (`-K 6 -N 1 -M 1 -F 0`), which limits cut size, allows at most one added node per step, and requires positive node savings. This is a low-risk implementation of the planned small cut divisor resub stage.

The final selector currently does not enable ShareCone by default. Public-set metrics showed that `sharecone_v2` was better than the final selector on one case but worse in aggregate, so ShareCone remains a candidate and diagnostic path until a coarse non-fingerprint class can be identified.

Implementation constraints for later phases:

- Keep all candidates inside the existing ABC network lifecycle; never hold stale `Abc_Obj_t *` pointers across structural rewrites.
- Treat complemented edges explicitly when hashing or comparing AIG subgraphs.
- Accept a rewrite only when CEC passes in the outer evaluation loop and the local estimate improves AIG nodes, or ties nodes while not increasing levels.
- Bound enumeration by node count, cut size, and wall-time budget; hidden cases should prefer no-op over runaway optimization.
- Use coarse structural features only for selector decisions; no file names, hashes, exact public-case fingerprints, or exact PI/PO/names combinations.
- Keep ShareCone source, binary command registration, and documentation consistent. If the command is documented, `src/opt/sharecone/` must be tracked or the final package must explicitly state that ShareCone is excluded.

Low-risk algorithm path:

1. v1: structural sweep after `strash`, plus small-budget functional sweep for cheap equivalent-node candidates.
2. v2: small cut/divisor resubstitution with explicit budgets, limited fanin cut size, and conservative positive-gain acceptance.
3. Always run a light ABC cleanup after accepted changes, then rely on the outer `cec` gate before selecting the result.

Required diagnostics before v3:

- candidate count and accepted/rejected rewrite counts
- rejected-by-gain, rejected-by-level, and rejected-by-budget counts
- node gain and level delta before and after cleanup
- runtime and peak memory
- per-output cone overlap statistics
- MFFC overlap histogram

References used for implementation framing:

- Berkeley ABC project documentation and command model: https://people.eecs.berkeley.edu/~alanmi/abc/
- Mishchenko, Chatterjee, Brayton, "DAG-aware AIG rewriting: a fresh look at combinational logic synthesis", DAC 2006.
- ABC synthesis flow papers and documentation on AIG rewriting, refactoring, MFFC, cut enumeration, and technology-independent optimization.
