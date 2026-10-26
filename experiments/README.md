# Experiments

These are the studies/experiments on which an architectural decision is based, or which are reported elsewhere.
In each directory, `run.py` writes the outputs; the notebook reads them.

Reproducibility: A rerun from the repository root matches them at the commit on which they were run originally.

| experiment | question | finding |
|---|---|---|
| [`kfold`](kfold/kfold.ipynb) | Does a single seeded 10% split rank models alike across seeds? | No, so [grouped K-fold replaced it](https://github.com/adkipnis/mixedbench/issues/87). |
| [`flat`](flat/flat.ipynb) | Do grouped tables differ from flat ones beyond the grouping? | They differ in [size, type mix and how distinct their values are](https://github.com/adkipnis/mixedbench/issues/123). No substantial difference in their columns' distributions. |
