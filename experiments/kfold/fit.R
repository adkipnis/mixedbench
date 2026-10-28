# fit.R scores a GLM and a mixed model on every fold of a problem's splits.
#
# Usage: Rscript fit.R <dir>
# <dir> holds what run.py hands over:
#   table.csv    the aliased standardized table (Handoff)
#   input.json   the formula and family (Handoff)
#   folds.csv    one column per split, a row's fold or -1 where the row is never held out
# fit.R prints sessionInfo() first. Then it writes back into <dir>:
#   scores.csv   per split, fold and held-out row, each line's log predictive density
#   fits.csv     per split, fold and line, its seconds, error, warnings and singularity
#
# pipeline:
# ---------
# <dir>
# -> per split and fold, both lines fitted to the seen rows    fitLine
# -> the held-out rows' log predictive densities               scoreGlm, scoreMixed
# -> scores.csv, fits.csv

suppressPackageStartupMessages(library(lme4))

# =====================================================================================
# the lines
# =====================================================================================

FAMILY <- list(gaussian = gaussian(), bernoulli = binomial(), binomial = binomial(), poisson = poisson())

# the checks would refuse a training set where a factor has a group per row
CONTROL <- list(check.nobs.vs.nlev = "ignore", check.nobs.vs.nRE = "ignore", calc.derivs = FALSE)

fitGlm <- function(formula, data, family) {
  glm(reformulas::nobars(formula), data = data, family = FAMILY[[family]])
}

fitMixed <- function(formula, data, family) {
  if (family == "gaussian") {
    return(lmer(formula, data = data, REML = TRUE, control = do.call(lmerControl, CONTROL)))
  }
  glmer(formula, data = data, family = FAMILY[[family]], control = do.call(glmerControl, CONTROL))
}

# =====================================================================================
# the scores
# =====================================================================================

# the log density of the response given the linear predictor, for the families without a scale;
# from the logit itself, since a mean rounded to 1 would score a failure -Inf instead of -η
logDensity <- function(family, test, eta) {
  switch(family,
    bernoulli = test$y * plogis(eta, log.p = TRUE) + (1 - test$y) * plogis(-eta, log.p = TRUE),
    binomial = lchoose(test$n, test$y) + test$y * plogis(eta, log.p = TRUE) +
      (test$n - test$y) * plogis(-eta, log.p = TRUE),
    poisson = dpois(test$y, exp(eta), log = TRUE)
  )
}

scoreGlm <- function(fit, test, family) {
  eta <- predict(fit, newdata = test, type = "link")
  if (family == "gaussian") {
    return(dnorm(test$y, eta, sigma(fit), log = TRUE))
  }
  logDensity(family, test, eta)
}

# a seen group adds its predicted random effects to the linear predictor;
# a new group's random effects are integrated out, with variance z' Σ z on the linear predictor
scoreMixed <- function(fit, train, test, family) {
  eta <- predict(fit, newdata = test, re.form = NULL, allow.new.levels = TRUE, type = "link")
  v <- newGroupVariance(fit, train, test)
  if (family == "gaussian") {
    return(dnorm(test$y, eta, sqrt(sigma(fit)^2 + v), log = TRUE))
  }
  integrateEffect(family, test, eta, sqrt(v))
}

# log ∫ p(y | η + s t) φ(t) dt per row, by adaptive Gauss-Kronrod quadrature (R's integrate) on
# either side of the integrand's mode. The links are canonical, so the integrand's log l(t) has
# l''(t) = -s² Var(y | η + s t) - 1 <= -1: the integrand lies below exp(l(mode) - (t - mode)² / 2),
# and mode ± 10 holds all but e^-50 of it. Gauss-Hermite nodes, placed by the curvature at the
# mode, miss most of the mass when s is large and p(y | η + s t) falls steeply on one side.
integrateEffect <- function(family, test, eta, s) {
  mode <- findMode(family, test, eta, s)
  scores <- numeric(nrow(test))
  for (i in seq_len(nrow(test))) {
    row <- test[i, ]
    logIntegrand <- function(t) logDensity(family, row, eta[i] + s[i] * t) + dnorm(t, log = TRUE)
    peak <- logIntegrand(mode[i])
    integrand <- function(t) exp(logIntegrand(t) - peak)
    left <- integrate(integrand, mode[i] - 10, mode[i], rel.tol = 1e-10)$value
    right <- integrate(integrand, mode[i], mode[i] + 10, rel.tol = 1e-10)$value
    scores[i] <- peak + log(left + right)
  }
  scores
}

# per row, the integrand's mode: the root of l'(t) = s (y - E(y | η + s t)) - t, found by bisection,
# since l' falls in t; Newton jumps back and forth across an l' that falls steeply, when s is large.
# The root lies in [-s E(y | η), s y], since the mean is at least 0 and rises in t.
findMode <- function(family, test, eta, s) {
  linkinv <- FAMILY[[family]]$linkinv
  lower <- -s * meanOf(family, test, linkinv(eta))
  upper <- s * test$y
  for (iteration in 1:100) {
    t <- (lower + upper) / 2
    gradient <- s * (test$y - meanOf(family, test, linkinv(eta + s * t))) - t
    lower <- ifelse(gradient > 0, t, lower)
    upper <- ifelse(gradient > 0, upper, t)
  }
  stopifnot(max(abs(gradient)) < 1e-6)
  t
}

# the response's mean given the mean of one trial
meanOf <- function(family, test, mu) {
  switch(family,
    bernoulli = mu,
    binomial = test$n * mu,
    poisson = mu
  )
}

# per row, the variance on the linear predictor of the random effects of groups the fit never saw
newGroupVariance <- function(fit, train, test) {
  terms <- fit@cnms  # per random-effect term, its factor (the name) and its columns
  covariances <- VarCorr(fit)  # per term, in the order of cnms
  stopifnot(length(terms) == length(covariances))
  v <- rep(0, nrow(test))
  for (i in seq_along(terms)) {
    factor <- names(terms)[i]
    columns <- terms[[i]]
    stopifnot(identical(rownames(covariances[[i]]), columns))
    new <- !(test[[factor]] %in% train[[factor]])
    z <- sapply(columns, function(column) if (column == "(Intercept)") rep(1, nrow(test)) else test[[column]])
    z <- matrix(z, nrow = nrow(test))
    sigma <- as.matrix(covariances[[i]])
    v <- v + new * rowSums((z %*% sigma) * z)
  }
  v
}

# =====================================================================================
# the steps
# =====================================================================================

# fits one line to the seen rows and scores the held-out ones;
# an error leaves the scores NA, and warnings are kept beside them
fitLine <- function(line, formula, train, test, family) {
  warnings <- character()
  start <- Sys.time()
  result <- withCallingHandlers(
    tryCatch(
      {
        if (line == "glm") {
          fit <- fitGlm(formula, train, family)
          scores <- scoreGlm(fit, test, family)
          singular <- FALSE
        } else {
          fit <- suppressMessages(fitMixed(formula, train, family))
          scores <- scoreMixed(fit, train, test, family)
          singular <- isSingular(fit)
        }
        list(scores = scores, singular = singular, error = "")
      },
      error = function(e) list(scores = rep(NA_real_, nrow(test)), singular = NA, error = conditionMessage(e))
    ),
    warning = function(w) {
      warnings <<- c(warnings, conditionMessage(w))
      invokeRestart("muffleWarning")
    }
  )
  result$seconds <- as.numeric(Sys.time() - start, units = "secs")
  result$warning <- paste(unique(warnings), collapse = "; ")
  result
}

# =====================================================================================
# main
# =====================================================================================

# first, so that R.log names the R and lme4 versions
print(sessionInfo())
dir <- commandArgs(trailingOnly = TRUE)[[1]]
input <- jsonlite::read_json(file.path(dir, "input.json"))
table <- read.csv(file.path(dir, "table.csv"))
folds <- read.csv(file.path(dir, "folds.csv"))
for (factor in grep("^g[0-9]+$", names(table), value = TRUE)) {
  table[[factor]] <- factor(table[[factor]])
}
formula <- as.formula(sub("y | trials(n)", "cbind(y, n - y)", input$formula, fixed = TRUE))
family <- input$family
scores <- list()
fits <- list()
for (split in names(folds)) {
  for (fold in sort(unique(folds[[split]][folds[[split]] >= 0]))) {
    held <- folds[[split]] == fold
    train <- droplevels(table[!held, ])
    test <- table[held, ]
    lines <- list()
    for (line in c("glm", "mixed")) {
      lines[[line]] <- fitLine(line, formula, train, test, family)
      fits[[length(fits) + 1]] <- data.frame(
        split = split, fold = fold, line = line, seconds = lines[[line]]$seconds,
        error = lines[[line]]$error, warning = lines[[line]]$warning, singular = lines[[line]]$singular
      )
    }
    scores[[length(scores) + 1]] <- data.frame(
      split = split, fold = fold, row = which(held) - 1, glm = lines$glm$scores, mixed = lines$mixed$scores
    )
  }
}
write.csv(do.call(rbind, scores), file.path(dir, "scores.csv"), row.names = FALSE)
write.csv(do.call(rbind, fits), file.path(dir, "fits.csv"), row.names = FALSE)
