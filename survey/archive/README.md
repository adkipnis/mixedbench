# Archive

- `deposits.py` drew the Tier D papers into `deposits.csv`, `resolve.py` resolved their deposits into `deposit_files.csv` and the help pages, `discover.md` briefed the discovery agent and `net.py` ran the Tier O keyword net into `net_hits.csv`.
- `verify.py` wrote the keyword scan (`scan_hits.csv`), the seeded hand sample (`sample.csv`) and the agreement table (`agreement.csv`), and `v05_datasets.csv` listed metabeta v0.5's 36 R datasets for the closing check; the two tests belong to these scripts.
- `verified.py` (`verify.py` in `survey/` until then) filled the registry's `verified` column (#26), `slopes.py` its `random_slopes` (#27) and `factors.py` regrouped the nested grouping factors (#45), each once through its shard; `test_verified.py`, `test_slopes.py` and `test_factors.py` belong to them.
- The first two items run at tag `survey-archive` (7c780a6), the third at tag `survey-archive-2` (2d386fd), where these files still sit in `survey/`. Nothing here is maintained after its tag.
