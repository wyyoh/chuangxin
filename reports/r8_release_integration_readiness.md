---
research_id: R8-PORT-ORDER
status: candidate-ready
baseline_tag: final_selector_v2_20260526
baseline_commit: 0b0edf4890283e36fac943166a8c84a148c120b8
branch: candidate/r7b-pure
created: 2026-06-22
updated: 2026-06-22
affects_final: false
supersedes: []
superseded_by: []
primary_data:
  - reports/r8_order_choosebest_singlecase_candidate_summary.md
  - reports/r8_order_choosebest_singlecase_hardening_summary.md
  - reports/r8_order_choosebest_singlecase_metrics.csv
  - reports/r8_order_choosebest_singlecase_compare.csv
  - reports/r8_order_choosebest_singlecase_casename_compare.csv
---

# R8 Release Integration Readiness

## Objective

Audit what would be required to promote the R8 single-case order choose-best
candidate into the formal submission path, without modifying the formal final
selector, formal pipelines, submit directory, or submit archive.

## Baseline

- Formal baseline: `final_selector_v2_20260526`
- Formal commit: `0b0edf4890283e36fac943166a8c84a148c120b8`
- Formal public result: `45870` nodes, max level `25`, CEC `30/30`,
  fallback `0`
- Current strongest candidate: R8 single-case order choose-best, commit
  `eaa3242b0b5713af3243ca73aaa1af10b7ba5965`, tag
  `candidate_r8_order_choosebest_hardened_20260622`

## Commands

Read-only audit commands:

```powershell
python - <<'PY'
import ast
from pathlib import Path
scripts = [
    'tools/optimize_one.py',
    'tools/optimize_one_r8_order_choosebest.py',
    'tools/eval_public_r8_order_choosebest_singlecase.py',
    'tools/package_submit.py',
]
local = {p.stem for p in Path('tools').glob('*.py')}
for script in scripts:
    tree = ast.parse(Path(script).read_text(encoding='utf-8'))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name.split('.')[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module.split('.')[0])
    print(script, sorted(set(i for i in imports if i in local)))
PY
git show --stat --oneline candidate_r7b_pure_abc_20260622
git diff --no-index -- configs\final_selector.yaml configs\final_selector_r7b_candidate.yaml
git diff --no-index -- configs\pipelines.yaml configs\pipelines_r7b_pure_candidate.yaml
```

## Input Data

- Formal files audited read-only:
  - `tools/optimize_one.py`
  - `tools/package_submit.py`
  - `configs/final_selector.yaml`
  - `configs/pipelines.yaml`
- Candidate files audited:
  - `tools/optimize_one_r8_order_choosebest.py`
  - `tools/eval_public_r8_order_choosebest_singlecase.py`
  - `tools/extract_r7b_features.py`
  - `tools/r7b_port_order_stress.py`
  - `configs/final_selector_r7b_candidate.yaml`
  - `configs/pipelines_r7b_pure_candidate.yaml`
- ABC candidate source:
  - `C:\Users\yy257\abc_r7b_candidate`
  - commit `9546db421c4f1b3d8736b6af2f9af875ddec8ec2`
  - tag `candidate_r7b_pure_abc_20260622`

## Results

R8 candidate result remains:

- nodes: `43775`
- max level: `21`
- public CEC: `30/30`
- fallback: `0`
- wins/ties/losses versus formal: `11/19/0`
- gain versus formal: `2095`
- gain excluding best/top2 versus formal: `737/122`
- gain versus clean R7b: `784`
- port-name, anonymous-name, and random-name stresses: exact clean-result
  reproduction with `0` node/level/variant/pipeline mismatches

Release integration file audit:

| Area | Current formal state | R8 candidate need | Readiness |
| --- | --- | --- | --- |
| ABC binary | formal binary lacks proven `r7win` command evidence in this package state | merge ABC commit `9546db421c4f1b3d8736b6af2f9af875ddec8ec2` and build no-pthread binary | ready after release-branch merge/build |
| ABC source delta | not in formal release branch yet | `src/base/abci/abc.c`, `src/opt/sharecone/sharecone.c`, `src/opt/sharecone/sharecone.h` | known 3-file delta |
| formal selector | no `r7b_eligible` rule | add coarse `r7b_high_overlap_guarded_fraig` rule before existing rules | ready, but requires formal-file edit approval |
| formal pipelines | no `r7b_r7win_fraig_high` pipeline | add R7b pipeline and reconcile candidate `sop_fx` command | ready, but must rerun public 30 after exact choice |
| single-case optimizer | formal `optimize_one.py` extracts only static BLIF features | integrate R8 policy: generate R7b profile features, run clean/input/output/both variants, CEC each, choose level-safe lowest-node result | ready as candidate script |
| package script list | packages only `optimize_one.py`, `run_abc_case.py`, `parse_abc_stats.py`, `eval_public.py`, `extract_blif_features.py`, `select_pipeline.py`, `verify_all_cec.py` | package must also include `extract_r7b_features.py` and `r7b_port_order_stress.py`, unless their needed code is inlined into formal `optimize_one.py` | not ready until package script list is updated |
| release output set | formal `submit/results/final_public` still v2 | generate candidate public outputs from release-like single-case interface | pending approval |
| submit archive | protected old archive | regenerate only after explicit packaging approval | blocked by policy, intentionally |

Important configuration note:

- `configs/pipelines_r7b_pure_candidate.yaml` differs from formal
  `configs/pipelines.yaml` beyond simply adding `r7b_r7win_fraig_high`.
- In particular, candidate `sop_fx` uses `sop; fx; ...`, while the formal v2
  file currently uses `sweep; fx; ...`.
- A release branch must either adopt the candidate pipeline file exactly or
  deliberately preserve formal non-R7b pipeline semantics and rerun public 30.
  No partial hand-merge should be trusted without fresh metrics and CEC.

## Correctness

Current candidate correctness evidence is strong but not a packaged-release
proof:

- R8 candidate public full 30: CEC `30/30`
- independent public CEC: `30/30`
- port-name stress independent CEC: `30/30`
- anonymous case-name stress independent CEC: `30/30`
- random case-name stress independent CEC: `30/30`
- CLI smoke direct ABC CEC: `3/3`

Formal release correctness remains unproven until the release branch runs the
actual packaged or release-like `tools/optimize_one.py` path and re-verifies
all outputs.

## Risk

Low risk after approval:

- Copying candidate evidence into a release branch.
- Updating packaging docs/checklists.
- Running release-like public 30 and independent CEC.

Medium risk after approval:

- Replacing formal `optimize_one.py` with R8 policy or wrapping it.
- Updating `package_submit.py` script list.
- Reconciling `configs/pipelines.yaml` with candidate pipelines.

High risk without approval:

- Editing `configs/final_selector.yaml`.
- Editing `configs/pipelines.yaml`.
- Regenerating `submit/` or `submit_sharecone.zip`.
- Retagging or replacing the formal final.

## Selector Eligibility

R8 remains selector-eligible. It uses the coarse `r7b_eligible` feature
generated by `r7win -profile -diag` and then an online local
CEC/node/level choose-best policy. It does not use filenames, directory names,
hashes, public case IDs, exact public fingerprints, exact port names, or public
discovery order.

## Conclusion

Decision: `promote-to-candidate`

R8 is ready for a user-approved release integration branch, but not ready for
submit packaging yet. The main unresolved item is not algorithmic performance;
it is release plumbing: formal `optimize_one.py`, `package_submit.py`, formal
selector/pipeline configs, and the ABC binary must be updated together and then
reproduced through the formal gates.

## Next Action

Ask for explicit approval before entering formal integration. If approved:

1. Create a release or candidate integration branch/worktree.
2. Merge the ABC `r7win` source change and build a no-pthread ABC binary.
3. Integrate the R8 single-case policy into the formal `tools/optimize_one.py`
   path.
4. Update packaging script dependencies.
5. Update formal selector/pipeline configs only in the release branch.
6. Run full public 30 through the release-like single-case interface.
7. Run independent full CEC.
8. Only after a separate explicit packaging approval, generate and verify a new
   submit archive.
