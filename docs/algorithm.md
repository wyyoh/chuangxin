# Algorithm Design

## Final Strategy

The final submitted optimizer uses an offline-tuned ABC pipeline portfolio plus a lightweight coarse feature selector. It does not run the full portfolio per case during final execution.

The final selector uses only general BLIF structure features:

- network scale grade
- high-fanin SOP flag
- near-two-input-AIG flag
- PI/PO/name/cube bins available from the feature extractor
- coarse runtime-size bin derived from name/cube count buckets

It does not use file names, directory names, hashes, exact line counts, exact public-case PI/PO/name/cube fingerprints, or exact port combinations.

Current final selector v2:

- default: `dc2_fast`
- large runtime-size near-two-input-AIG structures: `high_aig_three_round`
- tiny/small high-fanin SOP: `sop_fx`
- medium non-near-two-input-AIG: `rewrite2`

## Verification and Fallback

Every candidate output is checked by ABC `cec` before it can be selected. The fallback policy is:

- candidate crash or timeout -> best verified baseline
- candidate CEC failure -> best verified baseline
- candidate metric regression -> best verified baseline
- original/identity -> last-resort fallback only

Final public metrics are generated from real run logs:

- `reports/final_metrics.csv`
- `logs/final_cec.log`
- `reports/final_scoreboard.xlsx`
- `reports/failure_cases.md`

## ShareCone Status

`sharecone` is implemented as a candidate ABC command and is included in the source tree. The current candidate versions are:

- `sharecone` / v1: small-budget functional sweep using ABC's existing `fraig`
- `sharecone -2` / v2: v1 plus bounded `resub -K 6 -N 1 -M 1 -F 0`

ShareCone is not enabled in the final selector because public-set aggregate metrics were worse than the final selector. The latest recorded public totals were:

- selector v2 final: 45870 AIG nodes, max level 25
- phase_a_hardened final: 47338 AIG nodes, max level 25
- sharecone_v1: 49825 AIG nodes, max level 22, 11 fallback cases
- sharecone_v2: 48832 AIG nodes, max level 22, 8 fallback cases

This means ShareCone is kept as a candidate and diagnostic path, not claimed as the final winning algorithm.

## Multi-Output Sharing Plan

The next ShareCone iteration should first add diagnostics before changing optimization behavior:

- candidate count
- accepted/rejected rewrite count
- gain and level deltas
- cleanup before/after deltas
- runtime and memory
- per-output cone overlap statistics
- MFFC overlap histogram

ShareCone should only enter final selection if diagnostics identify a coarse, non-fingerprint structure class where it reliably improves nodes without CEC, level, runtime, or memory regressions.

## Single-Thread Build Note

The hardened ABC binary is built with `ABC_USE_NO_PTHREADS=1`. Two ABC source guards were added so the no-pthread build does not reference pthread declarations or link UFAR's concurrent solver entry point.

The no-pthread build was re-evaluated on the 30 public cases and matched the frozen Phase A metrics exactly before Selector v2 promotion:

- selected AIG nodes: 47338
- max selected level: 25
- CEC: 30/30 passed
- selected pipeline / nodes / levels / fallback status: no differences versus the frozen CSV

Selector v2 keeps the same no-pthread ABC binary and promotes only a coarse selector/pipeline configuration change. The final promoted public metrics are:

- selected AIG nodes: 45870
- max selected level: 25
- CEC: 30/30 passed
- fallback: 0

The recovery point remains `phase_a_hardened_20260526`.
