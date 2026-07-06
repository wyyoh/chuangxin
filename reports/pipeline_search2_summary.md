# Pipeline Search 2.0 Full Summary

Usage note: `FULL_SEARCH_PHASE5_NOT_FINAL_DECISION`. This is Phase 5 full pipeline search only; Phase 6/7/8 were not run.

| candidate | family | selected nodes | raw nodes | max level | CEC | fallback | crash | timeout | CEC fail | W/T/L | gain excl best | gain excl top2 | Phase 6? |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |
| aig_resyn_resub_zero | aig_resyn_family | 47031 | 47095 | 25 | 30/30 | 2 | 0 | 0 | 0 | 3/24/3 | -40 | -82 | True |
| choice_fraig_clean | choice_perturb_family | 45850 | 45916 | 21 | 30/30 | 2 | 0 | 0 | 0 | 3/21/6 | -77 | -92 | True |
| choice_fraig_ifraig_recover | choice_perturb_family | 45462 | 46233 | 21 | 30/30 | 2 | 0 | 0 | 0 | 10/14/6 | -327 | -558 | True |
| choice_ifraig_clean | choice_perturb_family | 45850 | 45916 | 21 | 30/30 | 2 | 0 | 0 | 0 | 3/21/6 | -77 | -92 | True |
| dc2_fraig_cleanup | dc2_dch_family | 45462 | 46233 | 21 | 30/30 | 2 | 0 | 0 | 0 | 10/14/6 | -327 | -558 | True |
| dc2_ifraig_cleanup | dc2_dch_family | 45462 | 46233 | 21 | 30/30 | 2 | 0 | 0 | 0 | 10/14/6 | -327 | -558 | True |
| high_aig_three_round | high_effort_small_case_family | 45884 | 45919 | 25 | 30/30 | 1 | 0 | 0 | 0 | 11/15/4 | 227 | 38 | True |

## Findings

- Candidates with selected total nodes < 47338: aig_resyn_resub_zero, choice_fraig_clean, choice_fraig_ifraig_recover, choice_ifraig_clean, dc2_fraig_cleanup, dc2_ifraig_cleanup, high_aig_three_round.
- Candidates worth Phase 6 anti-overfit review: aig_resyn_resub_zero, choice_fraig_clean, choice_fraig_ifraig_recover, choice_ifraig_clean, dc2_fraig_cleanup, dc2_ifraig_cleanup, high_aig_three_round.
- Runtime/RSS warning thresholds: runtime ratio > 2.5x or RSS ratio > 2.0x vs current final per case.

## Stop Point

Phase 5 completed. Phase 6 anti-overfit, Phase 7 selector, and Phase 8 decision were not run.
