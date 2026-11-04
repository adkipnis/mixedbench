#!/bin/bash
# one registry row of the measurement per array task: the row's 0-based index in registry.csv
# (survey/measure.py), n the registry's rows.
# submit from the repo root, the cache warm and the log directory made, the site's partition and
# QOS on the command line:
#   mkdir -p measure/logs
#   sbatch -p <partition> -q <qos> --array=0-$(( n - 1 )) survey/measure.sbatch
# rerun a task that ran out of memory or time by its index, with more on the command line; then,
# once every row is measured: uv run python survey/measure.py collect
# a CPU per row; the memory and time hold all but the largest tables
#SBATCH --job-name=measure
#SBATCH --cpus-per-task=1
#SBATCH --mem=20G
#SBATCH --time=4:00:00
#SBATCH --output=measure/logs/%A_%a.log

# no sync per task, which concurrent tasks would race on in the shared .venv: run `uv sync` once
# through Slurm first
export UV_NO_SYNC=1
uv run python survey/measure.py run "$SLURM_ARRAY_TASK_ID"
