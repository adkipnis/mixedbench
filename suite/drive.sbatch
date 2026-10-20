#!/bin/bash
# one reference run of suite 1.1 per array task: the task's index into the candidate list.
# submit from the repo root, the cache warm and the log directory made:
#   mkdir -p references/logs
#   sbatch --array=0-$(( $(wc -l < suite/1.1/candidates.csv) - 2 )) suite/drive.sbatch
# a task Slurm kills leaves its work directory in references/tmp, cleared once the array has ended
# a CPU per chain (references.LEVELS), the cap (references.CAP) plus 15 minutes for the record
#SBATCH --job-name=references
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=12:15:00
#SBATCH --output=references/logs/%A_%a.log

# CmdStan's draws of a large problem reach gigabytes,
# kept beside the run directories rather than on the node's /tmp or in the home quota
export TMPDIR="$PWD/references/tmp"
mkdir -p "$TMPDIR"
uv run python suite/drive.py run "$SLURM_ARRAY_TASK_ID"
