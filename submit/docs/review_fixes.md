# CodeRabbit Review Status

CodeRabbit CLI capability check:

- `coderabbit` command was not found on `PATH`.
- No CodeRabbit review was run.
- No CodeRabbit result is claimed for the current ABC C/C++ diff.

Safety decision:

- Keep `sharecone_v1` and `sharecone_v2` as evaluated candidates only.
- Final strategy should prefer the verified coarse selector unless CodeRabbit/auth becomes available and the C/C++ changes pass review.

Substitute review to run when CodeRabbit is unavailable:

- `git diff --check` in the ABC repository and root repository.
- Manual C/C++ checklist for command registration, null network handling, ABC object lifetime, complemented-edge assumptions, fanin/fanout updates, and Windows compatibility patches.
- Confirm `src/opt/sharecone/` is tracked if the binary and documentation expose the command.

Substitute review result for this hardened package:

- `logs/coderabbit_review.ndjson` records the CodeRabbit blocker: CLI not found on `PATH`; no CodeRabbit review is claimed.
- `logs/root_diff_check.txt` and `logs/abc_diff_check.txt` contain only Git line-ending normalization warnings; no whitespace error lines were reported.
- The no-pthread ABC changes are limited to guarding pthread-only declarations in `cecProve.c` and returning `-1` from UFAR's concurrent solver shim when `ABC_USE_PTHREADS` is disabled.
- The final selector does not enable ShareCone. ShareCone remains compiled and documented as a candidate command; its source directory is tracked in the ABC repository.
