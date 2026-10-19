#!/bin/bash
# the lab note's fits on one CPU node, a worker per core; extra arguments go to run.py.
# submit from the repo root, the cache warm, since the nodes need not reach the sources:
#   mkdir -p ~/tmp/kfold
#   sbatch lab/2026-10-19-kfold/run.sbatch --pilot 26   # every 26th problem, 21 in all
#   sbatch lab/2026-10-19-kfold/run.sbatch
# a resubmission skips the problems already summarized under ~/tmp/kfold
#SBATCH --job-name=kfold
#SBATCH --cpus-per-task=32
#SBATCH --mem=48G
#SBATCH --time=04:00:00
#SBATCH --output=lab/2026-10-19-kfold/%j.log

export TMPDIR=~/tmp
uv run python -u lab/2026-10-19-kfold/run.py --work ~/tmp/kfold --workers "$SLURM_CPUS_PER_TASK" "$@"
