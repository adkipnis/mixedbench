# Builds the CRAN-shaped fixture tarball for test_datasets.py. Rerun from the repo root:
#   Rscript tests/datasets/fixtures/make_fixture.R <build dir> $PWD/tests/datasets/fixtures/fixture_1.0.tar.gz
args <- commandArgs(trailingOnly = TRUE)
build <- args[1]; out <- args[2]
pkg <- file.path(build, 'fixture')
dir.create(file.path(pkg, 'data'), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(pkg, 'man'), showWarnings = FALSE)
writeLines(c('Package: fixture', 'Version: 1.0', 'Title: Loader Test Fixture',
             'Description: Five tiny data objects, each documented.', 'License: CC0'),
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
# A frame with a matrix column (gamlss.data's aep): pyreadr parses the file, cannot frame it.
wide <- data.frame(id = 1:3)
wide$y <- cbind(a = 1:3, b = 4:6)
save(wide, file = file.path(pkg, 'data', 'wide.rda'))
# An ASCII .rda, which librdata rejects (as it does geepack's muscatine): R re-saves it.
visits <- data.frame(clinic = factor(c('north', 'south', 'north')), count = c(2L, 5L, 1L))
save(visits, file = file.path(pkg, 'data', 'visits.rda'), ascii = TRUE)
# R's data() reads a .csv in data/ with read.table(header = TRUE, sep = ';', as.is = FALSE).
writeLines(c('arm;outcome', 'control;0', 'treated;1', 'control;1', 'treated;1', 'control;0'),
           file.path(pkg, 'data', 'trials.csv'))
writeLines(c('\\name{pets}', '\\alias{pets}', '\\docType{data}', '\\title{Six pets}',
             '\\description{Species, age in years and weight in kg of six pets.}',
             '\\usage{data(pets)}', '\\format{A data frame with 6 rows and 3 columns.}',
             '\\keyword{datasets}'),
           file.path(pkg, 'man', 'pets.Rd'))
writeLines(c('\\name{scores}', '\\alias{scores}', '\\docType{data}', '\\title{Four scores}',
             '\\description{Grade and score of four pupils.}', '\\keyword{datasets}'),
           file.path(pkg, 'man', 'scores.Rd'))
writeLines(c('\\name{trials}', '\\alias{trials}', '\\docType{data}', '\\title{Five trials}',
             '\\description{Arm and binary outcome of five trials.}', '\\keyword{datasets}'),
           file.path(pkg, 'man', 'trials.Rd'))
writeLines(c('\\name{wide}', '\\alias{wide}', '\\docType{data}', '\\title{Wide}',
             '\\description{Three ids with a two-column matrix response.}', '\\keyword{datasets}'),
           file.path(pkg, 'man', 'wide.Rd'))
writeLines(c('\\name{visits}', '\\alias{visits}', '\\docType{data}', '\\title{Visits}',
             '\\description{Visit counts at two clinics.}', '\\keyword{datasets}'),
           file.path(pkg, 'man', 'visits.Rd'))
old <- setwd(build)
tar(out, 'fixture', compression = 'gzip', tar = 'internal')
setwd(old)
