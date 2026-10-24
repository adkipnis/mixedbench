#!/bin/bash
# one fit of the fits pass per array task: the task's index among the rows fitted (survey/fits.py),
# n the registry rows with a continuous, binary or count response.
# submit from the repo root, the cache warm and the log directory made, the site's partition and
# QOS on the command line:
#   mkdir -p fits/logs
#   sbatch -p <partition> -q <qos> --array=0-$(( n - 1 )) survey/fits.sbatch
# then, once the array has ended: uv run python survey/fits.py collect
# a CPU per fit; twice the hour of fits.TIMEOUT, a backstop for a fit R cannot interrupt
#SBATCH --job-name=fits
#SBATCH --cpus-per-task=1
#SBATCH --mem=16G
#SBATCH --time=2:00:00
#SBATCH --output=fits/logs/%A_%a.log

# no sync per task, which concurrent tasks would race on in the shared .venv: run `uv sync` once
# through Slurm first
export UV_NO_SYNC=1
# R's session directory beside the run directories: a node whose /tmp is broken fails every task
export TMPDIR="$PWD/fits/tmp"
mkdir -p "$TMPDIR"
uv run python survey/fits.py run "$SLURM_ARRAY_TASK_ID"
