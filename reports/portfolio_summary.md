# Portfolio Summary

This report is generated from real `tools/run_portfolio.py` runs. Portfolio search is offline tuning only; final submission must not run all pipelines per case.

| pipeline | cases | selected_nodes_sum | max_level | fallbacks | cec_failures | runtime_sec_sum | peak_mem_mb_max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| aig_fast | 30 | 51875 | 26 | 12 | 0 | 8.914 | 30.2 |
| baseline | 30 | 52423 | 26 | 0 | 0 | 9.615 | 30.1 |
| dc2_fast | 30 | 47430 | 25 | 0 | 0 | 15.379 | 31.4 |
| rewrite2 | 30 | 49510 | 24 | 3 | 0 | 10.047 | 32.1 |
| sop_fx | 30 | 51743 | 26 | 8 | 0 | 9.221 | 30.6 |
