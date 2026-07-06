---
research_id: R17-R11S-RELEASE-HELPER
status: candidate-ready
baseline_tag: final_selector_v3_20260622
baseline_commit: 7b20c8c4904682cd905f7afb68d5a4a822c4f8d6
branch: release/r11-preflight
created: 2026-06-23
updated: 2026-06-23
affects_final: false
supersedes: []
superseded_by: []
primary_data:
  - tools/r11s_release_package.py
  - docs/reproduce.md
---

# R17 R11S Release Helper Audit

## Objective

Add a guarded helper for the final R11S release packaging flow while keeping the
default path non-destructive.

## Baseline

- Primary release-ready candidate: R11S
- Expected metrics: `41004` nodes, max level `20`, CEC `30/30`, fallback `0`
- Protected formal archive hash remains:
  `4B6236AF057009318EA50E39FFC43FFA3A74708B49A07C2F08FD386AB6D1AF8A`

## Commands

Syntax check:

```powershell
python -m py_compile tools\r11s_release_package.py
```

Help check:

```powershell
python tools\r11s_release_package.py --help
```

Non-destructive dry-run plan:

```powershell
python tools\r11s_release_package.py --plan-only
```

Formal-mode plan:

```powershell
python tools\r11s_release_package.py --mode formal --plan-only
```

Formal-mode guard check:

```powershell
python tools\r11s_release_package.py --mode formal
```

Expected guard behavior:

```text
formal mode requires --confirm-overwrite-submit
```

## Input Data

- `tools/r11s_release_package.py`
- `docs/reproduce.md`

## Results

The helper exposes two modes:

| Mode | Writes protected `submit/` or `submit_sharecone.zip` | Confirmation required |
| --- | --- | --- |
| `dry-run` | no | no |
| `formal` | yes | yes, `--confirm-overwrite-submit` |

Validation performed:

- `py_compile`: pass
- `--help`: pass
- `--plan-only`: pass, prints scratch paths under `scratch/r11s_release_package_dryrun`
- `--mode formal --plan-only`: pass, prints protected formal paths and
  `requires_confirmation: true`
- `--mode formal` without confirmation: fails before packaging, as intended

## Correctness

No optimization or CEC run was executed by this audit. Correctness remains based
on R16 zip/extract evidence. This step only improves release repeatability and
operator safety.

## Risk

The helper can overwrite protected artifacts only in formal mode with
`--confirm-overwrite-submit`. Formal mode also requires a clean worktree unless
`--allow-dirty` is passed.

## Selector Eligibility

Unchanged. This helper does not modify selector rules.

## Conclusion

promote-to-candidate

The R11S release path now has a guarded one-command packaging helper. It is
ready for explicit formal release packaging.

## Next Action

Run the helper in formal mode only when the release phase is explicitly approved:

```powershell
python tools\r11s_release_package.py --mode formal --cases local_data\tc_public --confirm-overwrite-submit
```
