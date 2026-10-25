# Experiments

The studies a decision or the paper rests on.
In each directory, `run.py` writes the outputs and the notebook reads them.
A rerun from the repository root matches them at the commit that wrote them.

| experiment | question | finding |
|---|---|---|
| [`kfold`](kfold/kfold.ipynb) | Does a single seeded 10% split rank models alike across seeds? | No, so [grouped K-fold replaced it](https://github.com/adkipnis/mixedbench/issues/87). |
| [`flat`](flat/flat.ipynb) | Do grouped tables differ from flat ones beyond the grouping? | [In size, type mix and how distinct their values are](https://github.com/adkipnis/mixedbench/issues/123), little in their columns' distributions. |
