# run.R fits one level of a problem's reference with brms through cmdstanr.
#
# Usage: Rscript run.R <dir>
# <dir> holds what Python hands over:
#   table.csv           the aliased standardized table
#   input.json          the formula, family, link, prior per class, the level's settings, the seed
#                       and the factors to summarize
# run.R prints sessionInfo() first.
# Then it writes back into <dir>, one data frame per file, since pyreadr reads no R lists:
#   draws.rds           chain, iteration, the global variables brms keeps and the random
#                       effects of every factor not summarized
#   locals_summary.rds  per random effect of a summarized factor its mean, sd and 5/25/50/75/95%
#                       quantiles, written only where a factor is summarized
#   summary.rds         per global variable its rank-normalized R-hat, bulk and tail ESS
#   meta.rds            the largest R-hat and the smallest bulk and tail ESS over the random
#                       effects
#   chains.rds          per chain its metric, divergences, tree-depth hits, E-BFMI, step size,
#                       leapfrog steps, mean acceptance statistic and warmup and sampling seconds
#   model.stan          brms's Stan program
#   standata.json       its Stan data, as CmdStan reads it
# The draws are thinned as the level's settings say; chains.rds alone counts every iteration.
# Python judges the bar on these files.
#
# pipeline:
# ---------
# <dir>
# -> brms's model, fitted at the level's settings    fitModel
# -> its global and local draws, thinned             extractDraws
# -> draws.rds, locals_summary.rds                   writeDraws
# -> summary.rds, meta.rds                           writeSummary
# -> chains.rds                                      writeChains
# -> model.stan, standata.json                       writeProgram

suppressPackageStartupMessages({
  library(brms)
  library(cmdstanr)
  library(posterior)
})

# =====================================================================================
# the variables brms labels
# =====================================================================================

# the global variables: the fixed effects, the random-effect sds and correlations, sigma
globalsOf <- function(x) grep("^(b_|sd_|cor_)|^sigma$", variables(x), value = TRUE)

# the random effects, each labeled r_<factor>[<group>,<effect>]
localsOf <- function(x) grep("^r_", variables(x), value = TRUE)

# =====================================================================================
# the steps
# =====================================================================================

fitModel <- function(dir, input) {
  table <- read.csv(file.path(dir, "table.csv"))
  prior <- set_prior(unlist(input$prior), class = names(input$prior))
  family <- brmsfamily(input$family, link = input$link)
  settings <- input$settings
  # cmdstanr compiles into <dir>, which lives across the levels, so a later level reuses the program
  options(cmdstanr_write_stan_file_dir = dir)
  brm(
    as.formula(input$formula), data = table, family = family, prior = prior, backend = "cmdstanr",
    chains = settings$chains, cores = settings$cores, warmup = settings$warmup,
    iter = settings$warmup + settings$draws,
    control = list(
      adapt_delta = settings$adapt_delta, max_treedepth = settings$max_treedepth,
      metric = settings$metric
    ),
    seed = input$seed, refresh = 0, silent = 2
  )
}

extractDraws <- function(model, thin) {
  draws <- as_draws_df(model, variable = c(globalsOf(model), localsOf(model)))
  # thinned here, not by brm(), so that chains.rds counts every iteration
  thin_draws(draws, thin)
}

# `factors` are the aliases of the factors to summarize
writeDraws <- function(draws, factors, dir) {
  local <- localsOf(draws)
  factor_of <- sub("^r_([^[]+)\\[.*$", "\\1", local)
  summarized <- local[factor_of %in% unlist(factors)]
  keep <- c(globalsOf(draws), setdiff(local, summarized))
  kept <- as.data.frame(draws)[keep]
  saveRDS(
    data.frame(chain = draws$.chain, iteration = draws$.iteration, kept, check.names = FALSE),
    file.path(dir, "draws.rds")
  )
  if (length(summarized) > 0) {
    quantiles <- function(x) quantile2(x, probs = c(0.05, 0.25, 0.5, 0.75, 0.95))
    effects <- summarise_draws(subset_draws(draws, variable = summarized), "mean", "sd", quantiles)
    saveRDS(as.data.frame(effects), file.path(dir, "locals_summary.rds"))
  }
}

writeSummary <- function(draws, dir) {
  global <- subset_draws(draws, variable = globalsOf(draws))
  summary <- summarise_draws(global, "rhat", "ess_bulk", "ess_tail")
  saveRDS(as.data.frame(summary), file.path(dir, "summary.rds"))
  local <- subset_draws(draws, variable = localsOf(draws))
  effects <- summarise_draws(local, "rhat", "ess_bulk", "ess_tail")
  # the worst over the random effects, NA where posterior could not compute one
  meta <- data.frame(
    rhat_locals = max(effects$rhat),
    ess_bulk_locals = min(effects$ess_bulk),
    ess_tail_locals = min(effects$ess_tail)
  )
  saveRDS(meta, file.path(dir, "meta.rds"))
}

writeChains <- function(model, max_treedepth, dir) {
  # per chain, the sampler's parameters at every iteration after warmup
  sampler <- rstan::get_sampler_params(model$fit, inc_warmup = FALSE)
  divergences <- function(chain) sum(chain[, "divergent__"])
  treedepth_hits <- function(chain) sum(chain[, "treedepth__"] >= max_treedepth)
  # adaptation ends with warmup, so every later iteration takes the same step size
  step_size <- function(chain) chain[1, "stepsize__"]
  leapfrog_steps <- function(chain) sum(chain[, "n_leapfrog__"])
  acceptance <- function(chain) mean(chain[, "accept_stat__"])
  seconds <- rstan::get_elapsed_time(model$fit)  # a row per chain, a column per phase
  chains <- data.frame(
    chain = seq_along(sampler),
    # as CmdStan ran it, from the header of its output
    metric = sapply(model$fit@stan_args, function(args) args$metric),
    divergences = sapply(sampler, divergences),
    treedepth_hits = sapply(sampler, treedepth_hits),
    ebfmi = rstan::get_bfmi(model$fit),
    step_size = sapply(sampler, step_size),
    leapfrog_steps = sapply(sampler, leapfrog_steps),
    acceptance = sapply(sampler, acceptance),
    warmup_seconds = seconds[, "warmup"],
    sampling_seconds = seconds[, "sample"]
  )
  saveRDS(chains, file.path(dir, "chains.rds"))
}

writeProgram <- function(model, dir) {
  writeLines(stancode(model), file.path(dir, "model.stan"))
  cmdstanr::write_stan_json(standata(model), file.path(dir, "standata.json"))
}

# =====================================================================================
# main
# =====================================================================================

# first, so that R.log names the session however the level ends
print(sessionInfo())
dir <- commandArgs(trailingOnly = TRUE)[[1]]
input <- jsonlite::read_json(file.path(dir, "input.json"))
model <- fitModel(dir, input)
draws <- extractDraws(model, input$settings$thin)
writeDraws(draws, input$summarized, dir)
writeSummary(draws, dir)
writeChains(model, input$settings$max_treedepth, dir)
writeProgram(model, dir)
