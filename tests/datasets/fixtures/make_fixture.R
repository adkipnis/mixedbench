# Builds the CRAN-shaped fixture tarball for test_loader.py, test_readers.py and
# survey/tests/test_help.py. Rerun from the repo root:
#   Rscript tests/datasets/fixtures/make_fixture.R <build dir> $PWD/tests/datasets/fixtures/fixture_1.0.tar.gz
args <- commandArgs(trailingOnly = TRUE)
build <- args[1]; out <- args[2]
pkg <- file.path(build, 'fixture')
dir.create(file.path(pkg, 'data'), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(pkg, 'man'), showWarnings = FALSE)
writeLines(c('Package: fixture', 'Version: 1.0', 'Title: Loader Test Fixture',
             'Description: Seven tiny data objects, each documented.', 'License: CC0'),
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
# An ASCII .rda, which librdata rejects (as it does geepack's muscatine): rdata reads it.
visits <- data.frame(clinic = factor(c('north', 'south', 'north')), count = c(2L, 5L, 1L))
save(visits, file = file.path(pkg, 'data', 'visits.rda'), ascii = TRUE)
# R's data() reads a .csv in data/ with read.table(header = TRUE, sep = ';', as.is = FALSE).
writeLines(c('arm;outcome', 'control;0', 'treated;1', 'control;1', 'treated;1', 'control;0'),
           file.path(pkg, 'data', 'trials.csv'))
# A .txt as agridat ships them: tab-separated, quoted header and strings, NA for missing;
# read.table(header = TRUE, as.is = FALSE) sorts the levels, so `variety` comes out a, b, c.
writeLines(c('"field"\t"variety"\t"plants"\t"yield"', '"north A"\t"b"\t12\t1.5',
             '"south B"\t"a"\t10\tNA', '"north A"\t"c"\t9\t2', '"west"\t"b"\tNA\t3.25'),
           file.path(pkg, 'data', 'plots.txt'))
# A .R in the deparse subset of base R's data/ files (ChickWeight.R, infert.R, sleep.R): R
# evaluates it once more and saves the frame as growth.rda beside this script, outside the
# package, so that the loader tests compare against R's own reading without needing R.
writeLines(c(
  '### Growth of four plants, in the style of base R\'s ChickWeight.R',
  '"growth" <-',
  '  structure(list(height = c(1.5, 2, NA, 3.25, -0.5, 4, 2.5, 1e-3),',
  '    pot = c(1:3, 5:9), # one pot lost',
  '    plant = ordered(rep.int(1:4, 2), levels = c(3, 1, 4, 2),',
  '      labels = c("p3", "p1", "p4", "p2")),',
  '    soil = factor(c(1, 2, 2, 1, NA, 2, 1, 2), levels = 1:2, labels = c("clay", "sand")),',
  '    block = gl(2, 4), dose = factor(rep(c(10, 2), 4)), site = c(rep("a b", 7), NA)),',
  '  row.names = 1:8, class = c("groupedData", "data.frame"),',
  '  formula = height ~ pot | plant, outer = ~ soil, labels = list(y = "Height"))',
  'environment(attr(growth, "formula")) <- emptyenv()',
  'environment(attr(growth, "outer")) <- emptyenv()'),
  file.path(pkg, 'data', 'growth.R'))
twin <- new.env()
sys.source(file.path(pkg, 'data', 'growth.R'), envir = twin)
# serialization v2: librdata rejects v3 with the formula attributes
save(growth, file = file.path(dirname(out), 'growth.rda'), envir = twin, version = 2)
# An integer column with NA (mlmRev's star) beside a string column, outside the package too
saveRDS(data.frame(score = c(1L, NA, 3L), note = c('a', 'b', 'c')),
        file.path(dirname(out), 'counts.rds'), version = 2)
# Single R files librdata rejects (ASCII), as OSF deposits serve them: a frame as an .rds, a
# list beside a frame, and a compiled function, which rdata cannot parse (a model fit's bytecode)
roster <- data.frame(ward = factor(c('b', 'a', 'b')), beds = c(4L, NA, 6L))
saveRDS(roster, file.path(dirname(out), 'roster.rds'), ascii = TRUE)
fit <- list(coef = c(a = 1, b = 2), call = quote(lm(y ~ x)))
save(fit, roster, file = file.path(dirname(out), 'fits.rda'), ascii = TRUE)
saveRDS(compiler::cmpfun(function(x) x + 1), file.path(dirname(out), 'fit.rds'), ascii = TRUE)
# The same frame twice, binary for pyreadr and ASCII for rdata, which must read it alike
twins <- data.frame(
  arm = factor(c('b', 'a', 'b', NA), levels = c('b', 'a', 'c')),
  dose = c(1L, 2L, 3L, 4L), count = c(5L, NA, 7L, 8L), weight = c(1.5, NA, 2.25, 3),
  note = c('x', 'y', NA, 'z'), flag = c(TRUE, FALSE, NA, TRUE), done = c(TRUE, FALSE, TRUE, TRUE),
  stringsAsFactors = FALSE
)
save(twins, file = file.path(dirname(out), 'twins.rda'), version = 2)
save(twins, file = file.path(dirname(out), 'twins_ascii.rda'), ascii = TRUE)
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
writeLines(c('\\name{plots}', '\\alias{plots}', '\\docType{data}', '\\title{Plots}',
             '\\description{Field, variety, plant count and yield of four plots.}',
             '\\keyword{datasets}'),
           file.path(pkg, 'man', 'plots.Rd'))
writeLines(c('\\name{growth}', '\\alias{growth}', '\\docType{data}', '\\title{Growth}',
             '\\description{Height of four plants in eight pots.}', '\\keyword{datasets}'),
           file.path(pkg, 'man', 'growth.Rd'))
writeLines(c('\\name{wide}', '\\alias{wide}', '\\docType{data}', '\\title{Wide}',
             '\\description{Three ids with a two-column matrix response.}', '\\keyword{datasets}'),
           file.path(pkg, 'man', 'wide.Rd'))
writeLines(c('\\name{visits}', '\\alias{visits}', '\\docType{data}', '\\title{Visits}',
             '\\description{Visit counts at two clinics.}', '\\keyword{datasets}'),
           file.path(pkg, 'man', 'visits.Rd'))
old <- setwd(build)
tar(out, 'fixture', compression = 'gzip', tar = 'internal')
setwd(old)
