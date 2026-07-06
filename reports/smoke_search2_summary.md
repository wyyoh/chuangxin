# Smoke Search 2 Summary

Usage note: `SMOKE_ONLY_FILTER_NOT_FINAL_CONCLUSION`. These data are only for eliminating unsafe or clearly weak candidates; they are not final performance conclusions.

## Family Summary

| family | attempted candidates | passed candidates | crash | timeout | CEC fail | avg node delta vs final | level regressions | runtime warnings | RSS warnings | recommended | action |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| aig_resyn_family | 5 | 5 | 0 | 0 | 0 | 148.860 | 5 | 0 | 0 | 1 | keep_for_full_candidates |
| choice_perturb_family | 4 | 4 | 0 | 0 | 0 | -131.650 | 6 | 1 | 0 | 3 | keep_for_full_candidates |
| dc2_dch_family | 4 | 4 | 0 | 0 | 0 | -103.600 | 5 | 2 | 0 | 2 | keep_for_full_candidates |
| high_effort_small_case_family | 2 | 1 | 7 | 0 | 0 | -1.429 | 0 | 0 | 0 | 1 | keep_for_full_candidates |
| lut_mfs_roundtrip_family | 3 | 1 | 20 | 0 | 0 | 43.433 | 3 | 0 | 0 | 0 | eliminate_for_full_search |
| sop_fx_family | 4 | 3 | 10 | 0 | 0 | 86.300 | 3 | 0 | 0 | 0 | eliminate_for_full_search |

## Recommended Full Candidates

| family | pipeline | avg node delta | wins/ties/losses | level regressions | recommendation |
| --- | --- | ---: | --- | ---: | --- |
| aig_resyn_family | aig_resyn_resub_zero | -32.500 | 2/8/0 | 1 | full_search_recommended |
| choice_perturb_family | choice_fraig_clean | -149.300 | 1/7/2 | 2 | full_search_recommended |
| choice_perturb_family | choice_fraig_ifraig_recover | -94.100 | 4/4/2 | 2 | full_search_recommended |
| choice_perturb_family | choice_ifraig_clean | -149.300 | 1/7/2 | 2 | full_search_recommended |
| dc2_dch_family | dc2_fraig_cleanup | -94.100 | 4/4/2 | 2 | full_search_recommended |
| dc2_dch_family | dc2_ifraig_cleanup | -94.100 | 4/4/2 | 2 | full_search_recommended |
| high_effort_small_case_family | high_aig_three_round | -2.857 | 2/5/0 | 0 | full_search_recommended |

## Eliminated Commands

- `compress2rs`: disabled by capability inventory as unavailable.
- `mfs2`: disabled by capability inventory because the probe crashed.

## Stop Point

Phase 4 completed. Phase 5 full search has not been run.
