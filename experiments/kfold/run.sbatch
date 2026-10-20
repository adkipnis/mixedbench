#!/bin/bash
# the experiment's fits on one CPU node, a worker per core; extra arguments go to run.py.
# submit from the repo root, the cache warm, since the nodes need not reach the sources;
# experiments/kfold/work holds the per-problem runs and the logs:
#   mkdir -p experiments/kfold/work ~/tmp
#   sbatch experiments/kfold/run.sbatch --pilot 26   # every 26th problem, 21 in all
#   sbatch experiments/kfold/run.sbatch
# a resubmission skips the problems already summarized
#SBATCH --job-name=kfold
#SBATCH --cpus-per-task=32
#SBATCH --mem=48G
#SBATCH --time=1-00:00:00
#SBATCH --output=experiments/kfold/work/%j.log

export TMPDIR=~/tmp
uv run python -u experiments/kfold/run.py --workers "$SLURM_CPUS_PER_TASK" "$@"
