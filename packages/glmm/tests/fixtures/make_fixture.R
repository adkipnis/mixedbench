# Builds the CRAN-shaped fixture tarball for test_datasets.py. Rerun from the repo root:
#   Rscript packages/glmm/tests/fixtures/make_fixture.R <build dir> $PWD/packages/glmm/tests/fixtures/fixture_1.0.tar.gz
args <- commandArgs(trailingOnly = TRUE)
build <- args[1]; out <- args[2]
pkg <- file.path(build, 'fixture')
dir.create(file.path(pkg, 'data'), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(pkg, 'man'), showWarnings = FALSE)
writeLines(c('Package: fixture', 'Version: 1.0', 'Title: Loader Test Fixture',
             'Description: Three tiny data objects.', 'License: CC0'),
           file.path(pkg, 'DESCRIPTION'))
set.seed(1)
pets <- data.frame(
  species = factor(c('dog', 'cat', 'fish', 'dog', 'cat', 'dog'), levels = c('dog', 'cat', 'fish', 'bird')),  # 'bird' unused on purpose
  age = c(3L, 5L, 1L, 7L, 2L, 4L),
  weight = c(12.5, 4.2, 0.1, 20.0, 3.8, 9.9)
)
save(pets, file = file.path(pkg, 'data', 'pets.rda'))
scores <- data.frame(
  grade = factor(c('low', 'high', 'mid', 'low'), levels = c('low', 'mid', 'high')),
  score = c(10.5, 30.1, 20.2, 11.0)
)
saveRDS(scores, file.path(pkg, 'data', 'scores.rds'))
# R's data() reads a .csv in data/ with read.table(header = TRUE, sep = ';', as.is = FALSE).
writeLines(c('arm;outcome', 'control;0', 'treated;1', 'control;1', 'treated;1', 'control;0'),
           file.path(pkg, 'data', 'trials.csv'))
writeLines(c('\\name{pets}', '\\alias{pets}', '\\docType{data}', '\\title{Six pets}',
             '\\description{Species, age in years and weight in kg of six pets.}',
             '\\usage{data(pets)}', '\\format{A data frame with 6 rows and 3 columns.}',
             '\\keyword{datasets}'),
           file.path(pkg, 'man', 'pets.Rd'))
old <- setwd(build)
tar(out, 'fixture', compression = 'gzip', tar = 'internal')
setwd(old)
