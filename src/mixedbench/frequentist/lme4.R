# lme4.R fits a mixed model's formula as written by lme4 and computes its variance components.
#
# Usage: Rscript lme4.R <dir>
# <dir> holds what Python hands over:
#   table.csv    the table
#   input.json   the formula, the family, the seconds after which the fit stops,
#                each categorical column's levels in order and the ordered ones
# lme4.R prints sessionInfo() first. Then it writes back into <dir>:
#   output.json  how the fit ended, its seconds, warnings or error and observations,
#                the fixed effects with their Wald standard errors,
#                per random term its factor, columns, variances and correlations, sigma,
#                per factor the random variance, the fixed predictor's variance,
#                the sd of the linear predictor and the distribution variance
#
# pipeline:
# ---------
# <dir>
# -> the table, its categorical columns coded     readTable
# -> lme4's fit of the formula, within the limit  fitWithin, fitModel
# -> its estimates and variance components        describeFit
# -> how it ended, output.json                    fitWithin

suppressPackageStartupMessages(library(lme4))

# =====================================================================================
# the families, and the description of a fit that ended without one
# =====================================================================================

FAMILY <- list(bernoulli = binomial(), poisson = poisson())

UNFITTED <- list(
  n_obs = NA, fixed = setNames(list(), character()), terms = list(), sigma = NA,
  variances = setNames(list(), character()), sigma2_fixed = NA, sd_eta = NA,
  sigma2_distribution = NA
)

# =====================================================================================
# the steps
# =====================================================================================

# a categorical column is read as text, then coded by its levels;
# a value that is no level would be lost as a missing value.
# Other text is read as a factor, as a formula's terms take it: glmer takes a text response only so
readTable <- function(dir, input) {
  columns <- names(input$levels)
  classes <- setNames(rep("character", length(columns)), columns)
  table <- read.csv(
    file.path(dir, "table.csv"), check.names = FALSE, colClasses = classes, na.strings = "",
    stringsAsFactors = TRUE
  )
  for (column in columns) {
    levels <- unlist(input$levels[[column]])
    coded <- factor(table[[column]], levels = levels, ordered = column %in% unlist(input$ordered))
    stopifnot(identical(is.na(coded), is.na(table[[column]])))
    table[[column]] <- coded
  }
  table
}

# the fit and its description within the time limit, its warnings kept, and how it ended:
# the worst of ok, singular, warning, timeout and error
fitWithin <- function(table, input) {
  warnings <- character()
  start <- Sys.time()
  # within this call: set at the script's top level, the limit would end with its own line
  setTimeLimit(elapsed = input$timeout, transient = TRUE)
  on.exit(setTimeLimit())
  result <- withCallingHandlers(
    tryCatch(
      {
        model <- suppressMessages(fitModel(table, input))
        described <- describeFit(model, table, input$family)
        list(described = described, singular = isSingular(model), error = character())
      },
      error = function(e) list(described = UNFITTED, singular = NA, error = conditionMessage(e))
    ),
    warning = function(w) {
      warnings <<- c(warnings, conditionMessage(w))
      invokeRestart("muffleWarning")
    }
  )
  seconds <- as.numeric(Sys.time() - start, units = "secs")
  status <- "ok"
  if (isTRUE(result$singular)) status <- "singular"
  if (length(warnings) > 0) status <- "warning"
  if (length(result$error) > 0) status <- if (seconds >= input$timeout) "timeout" else "error"
  # one line, for a cell of a table: a parse error points at the formula over three
  message <- gsub("\\s*\n\\s*", " ", paste(c(unique(warnings), result$error), collapse = "; "))
  c(list(status = status, seconds = seconds, message = message), result$described)
}

fitModel <- function(table, input) {
  formula <- as.formula(input$formula)
  if (input$family == "gaussian") {
    return(lmer(formula, data = table))
  }
  glmer(formula, data = table, family = FAMILY[[input$family]])
}

describeFit <- function(model, table, family) {
  estimates <- fixef(model)
  errors <- sqrt(diag(as.matrix(vcov(model))))
  fixed <- setNames(list(), character())  # named, so that no fixed effect writes `{}`
  for (name in names(estimates)) {
    fixed[[name]] <- c(estimates[[name]], errors[[name]])
  }
  list(
    n_obs = nobs(model), fixed = fixed, terms = describeTerms(model),
    sigma = if (family == "gaussian") sigma(model) else NA,
    variances = randomVariances(model),
    sigma2_fixed = var(as.vector(getME(model, "X") %*% estimates)),
    sd_eta = sd(predict(model, type = "link")),
    sigma2_distribution = distributionVariance(model, table, family)
  )
}

describeTerms <- function(model) {
  terms <- model@cnms  # per random term, its factor (the name) and its columns
  covariances <- VarCorr(model)  # per term, in the order of cnms
  described <- list()
  for (i in seq_along(terms)) {
    covariance <- covariances[[i]]
    stopifnot(identical(rownames(covariance), terms[[i]]))
    described[[i]] <- list(
      factor = names(terms)[i], columns = I(terms[[i]]),
      variances = I(unname(diag(covariance))),
      correlations = unname(attr(covariance, "correlation"))
    )
  }
  described
}

# Johnson (2014): per factor, its terms' variance on the linear predictor, averaged over rows.
# A term's columns per row are read off Z, in the order lme4 fits the terms:
# mmList orders them by the columns as loaded, where an integer `a:b` is a sequence, not a factor
randomVariances <- function(model) {
  factors <- names(model@cnms)
  covariances <- VarCorr(model)  # per term, in the order of cnms
  zt <- getME(model, "Zt")  # Z's transpose: per term in turn, per level its columns
  starts <- getME(model, "Gp")  # where each term's rows start in zt
  variances <- list()
  for (i in seq_along(factors)) {
    columns <- length(model@cnms[[i]])
    block <- zt[(starts[i] + 1):starts[i + 1], , drop = FALSE]
    levels <- nrow(block) / columns
    # a row lies in one level, so the sum over levels leaves the row's own columns
    z <- as.matrix(t(block) %*% kronecker(matrix(1, levels, 1), diag(columns)))
    v <- mean(rowSums((z %*% covariances[[i]]) * z))
    factor <- factors[i]
    variances[[factor]] <- if (is.null(variances[[factor]])) v else variances[[factor]] + v
  }
  variances
}

# Nakagawa, Johnson and Schielzeth (2017): the variance the family adds on the link scale.
# The Poisson's lognormal approximation takes λ = exp(β₀ + σ²₀ / 2) from the model of the same rows
# with an intercept and the same random effects, σ²₀ the sum of its random-intercept variances,
# as performance computes it: its random slopes have no fixed column to vary with.
distributionVariance <- function(model, table, family) {
  if (family == "gaussian") {
    return(0)
  }
  if (family == "bernoulli") {
    return(pi^2 / 3)
  }
  rows <- table[rownames(model.frame(model)), , drop = FALSE]
  null <- glmer(nullFormula(model), data = rows, family = poisson())
  interceptVariance <- function(covariance) {
    if (!("(Intercept)" %in% rownames(covariance))) {
      return(0)  # a term of slopes alone
    }
    covariance["(Intercept)", "(Intercept)"]
  }
  intercepts <- vapply(VarCorr(null), interceptVariance, numeric(1))
  lambda <- exp(fixef(null)[["(Intercept)"]] + sum(intercepts) / 2)
  log1p(1 / lambda)
}

# the response, an intercept, the random terms and the offsets of the model's formula
nullFormula <- function(model) {
  formula <- formula(model)
  bracket <- function(bar) paste0("(", deparse1(bar), ")")
  bars <- vapply(reformulas::findbars(formula), bracket, character(1))
  fixed <- terms(reformulas::nobars(formula))
  variables <- as.list(attr(fixed, "variables"))[-1]  # the response first
  offsets <- vapply(variables[attr(fixed, "offset")], deparse1, character(1))
  reformulate(c("1", bars, offsets), response = formula[[2]])
}

# =====================================================================================
# main
# =====================================================================================

# first, so that R.log names the R and lme4 versions
print(sessionInfo())
dir <- commandArgs(trailingOnly = TRUE)[[1]]
input <- jsonlite::read_json(file.path(dir, "input.json"))
table <- readTable(dir, input)
output <- c(fitWithin(table, input), list(lme4 = as.character(packageVersion("lme4"))))
jsonlite::write_json(
  output, file.path(dir, "output.json"), auto_unbox = TRUE, digits = NA, na = "null"
)
