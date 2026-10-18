#!/bin/bash
# one reference run of suite 1.1 per array task: the task's index into the candidate list.
# submit from the repo root, the cache warm and the log directory made:
#   mkdir -p references/logs ~/tmp
#   sbatch --array=0-$(( $(wc -l < suite/1.1/candidates.csv) - 2 )) suite/drive.sbatch
# a CPU per chain (references.LEVELS), the cap (references.CAP) plus 15 minutes for the record
#SBATCH --job-name=references
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=12:15:00
#SBATCH --output=references/logs/%A_%a.log

# CmdStan's draws of a large problem reach gigabytes, kept off the node's /tmp
export TMPDIR=~/tmp
uv run python suite/drive.py run "$SLURM_ARRAY_TASK_ID"
