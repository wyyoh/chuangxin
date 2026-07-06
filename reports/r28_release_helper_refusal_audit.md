# R28 Release Helper Refusal Audit

## Objective

Verify that `tools/r28_release_package.py` refuses formal packaging before
overwriting `submit/` or `submit_sharecone.zip` when required guards are not
satisfied.

## Commands

Missing confirmation token:

```powershell
py -3 tools\r28_release_package.py --mode formal --execute > reports\r28_release_helper_refuse_no_token.log 2>&1
```

Dirty worktree without `--allow-dirty`:

```powershell
py -3 tools\r28_release_package.py --mode formal --execute --confirm-overwrite-submit R28_RELEASE_MT_FORMAL_20260625 > reports\r28_release_helper_refuse_dirty.log 2>&1
```

## Results

| Check | Exit Code | Expected Refusal | Log |
| --- | --- | --- | --- |
| Formal without confirmation token | `1` | `formal mode requires --confirm-overwrite-submit R28_RELEASE_MT_FORMAL_20260625` | `reports\r28_release_helper_refuse_no_token.log` |
| Formal with token but dirty worktree | `1` | `formal mode requires a clean worktree or --allow-dirty` | `reports\r28_release_helper_refuse_dirty.log` |

## Protection Verification

After both refusal tests:

- `submit_sharecone.zip` SHA256 remained
  `057963D73132E7752922C707F5348A184BE8D00256522D0C80CFC40061295D0C`
- `submit\bin\abc.exe` SHA256 remained
  `85F59E6291A1C4B10B757BF163D14D2152EAA974B21BC6F4E13F44EC49969805`
- `reports\r28_formal_release_summary.json` was not created
- Git reported no modifications to protected formal paths:
  `submit/`, `submit_sharecone.zip`, `configs/final_selector.yaml`,
  `configs/pipelines.yaml`, `current_final_manifest.json`,
  `reports/final_metrics.csv`, and `logs/final_cec.log`

## Conclusion

Decision label: `continue`.

The formal helper guard behavior is correct. It validates existing candidate
evidence, prints the formal plan, then refuses before packaging when either the
confirmation token is missing or the worktree is dirty without explicit
`--allow-dirty`.

Formal release remains blocked only by the expected management decision:
explicit approval to overwrite formal artifacts and either a clean worktree or
an explicit `--allow-dirty` release note.
