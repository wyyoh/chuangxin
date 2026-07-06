# R28 Formal Release Draft

## Status

Decision label: `candidate-ready`.

This is a draft only. It does not promote R28 and does not prove that
`submit/` or `submit_sharecone.zip` have been overwritten. Formal release still
requires explicit approval and a successful formal helper run.

## Candidate

- Candidate branch: `candidate/r28-gated-r27`
- Candidate helper-ready tag: `candidate_r28_release_helper_ready_20260625`
- Candidate helper-ready commit: `6437099`
- Proposed formal tag: `final_selector_v6_20260625`
- Previous formal tag: `final_selector_v5_20260624`
- Previous formal commit: `2722491e9079052e63073344c69eb5c2e10d50a4`
- Previous formal zip SHA256:
  `057963D73132E7752922C707F5348A184BE8D00256522D0C80CFC40061295D0C`

## Important Worktree Note

The candidate worktree `C:\Users\yy257\cpipc_r28_candidate` contains the v5
formal zip recorded above. The main workspace currently has an older
`submit_sharecone.zip` hash
`7B6C53463B2095B828DBCC1161FB403C737543448EA603F8AD6F7F8D60D151DA`.

Do not run formal R28 packaging from the main workspace unless the intended
release target is explicitly confirmed. The prepared R28 formal helper is in
the candidate worktree.

## Metrics

| Item | Value |
| --- | --- |
| Public cases | `30` |
| Selected AIG nodes | `37464` |
| Total selected levels | `278` |
| Max selected level | `20` |
| CEC | `30/30` |
| Fallback | `0` |
| Crash/timeout/CEC fail | `0/0/0` |
| Total opt runtime | `76.225724s` |
| Max per-case opt runtime | `20.505702s` |
| Peak RSS | `47.309 MB` |

## Delta Versus V5 Under Same Release ABC

| Item | Value |
| --- | --- |
| v5 Release ABC nodes | `37568` |
| R28 Release ABC nodes | `37464` |
| Total node gain | `104` |
| Wins / ties / losses | `4 / 26 / 0` |
| Gain excluding best case | `21` |
| Gain excluding top two cases | `10` |
| Winning cases for audit | `tc_public_14`, `tc_public_15`, `tc_public_26`, `tc_public_30` |

The selector and post-pass gates are coarse-structural and do not use filenames,
hashes, public case IDs, exact public fingerprints, or port-name fingerprints.

## ABC Binary

- Release ABC path:
  `C:\Users\yy257\abc_r7b_candidate_release_r28_20260625\abc.exe`
- Release ABC SHA256:
  `C21C9F2B28F2669D8F99D7587CBBC496672F5D01E45248D7D028B37FDFFF2E3F`
- Build: `/MT Release`
- Debug CRT strings: none
- Dynamic VC CRT strings: none
- `r7win` support: present

## Dry-Run Package Evidence

The guarded helper dry-run passed:

- package root CEC: `30/30`
- package inside CEC: `30/30`
- zip extract root CEC: `30/30`
- zip extract inside CEC: `30/30`
- hidden-entry smoke `tc_public_14`: R28 post-pass accepted, `2073` nodes,
  level `15`, CEC equivalent
- helper dry-run zip SHA256:
  `EE8E970089B96B9F60EA6D6C1EFBEC8A674A9125B92F37DCA72746C77359DC7E`

## Formal Release Command

Run only after explicit approval to overwrite formal artifacts:

```powershell
py -3 tools\r28_release_package.py --mode formal --execute --confirm-overwrite-submit R28_RELEASE_MT_FORMAL_20260625
```

The helper will refuse formal mode without the confirmation token. It will also
refuse an unexpected ABC SHA256 or any Debug CRT / dynamic VC CRT binary.

If the worktree contains untracked generated evidence, either clean it after
confirming it has been archived, or use `--allow-dirty` only with an explicit
release-management note.

Guard audit evidence:

- without the confirmation token, formal mode exits `1` before packaging
- with the token but a dirty worktree, formal mode exits `1` before packaging
  unless `--allow-dirty` is explicitly supplied
- both refusal tests left `submit/` and `submit_sharecone.zip` unchanged

## Formal Fields To Fill After Packaging

- Formal release commit: `TBD_AFTER_FORMAL_PACKAGING`
- Formal zip SHA256: `TBD_AFTER_FORMAL_PACKAGING`
- Formal package root CEC: `TBD_AFTER_FORMAL_PACKAGING`
- Formal package inside CEC: `TBD_AFTER_FORMAL_PACKAGING`
- Formal zip extract root CEC: `TBD_AFTER_FORMAL_PACKAGING`
- Formal zip extract inside CEC: `TBD_AFTER_FORMAL_PACKAGING`
- Formal hidden-entry smoke: `TBD_AFTER_FORMAL_PACKAGING`
- Formal tag: `TBD_AFTER_FORMAL_PACKAGING`

## Stop Conditions

Stop and do not tag if any formal check differs from dry-run evidence:

- packaged ABC SHA256 differs from
  `C21C9F2B28F2669D8F99D7587CBBC496672F5D01E45248D7D028B37FDFFF2E3F`
- package root or inside CEC is below `30/30`
- zip extract root or inside CEC is below `30/30`
- hidden-entry smoke fails, crashes, or does not load the R28 wrapper/config
- fallback, crash, timeout, or CEC fail count becomes nonzero
- formal zip SHA256 is not recorded
