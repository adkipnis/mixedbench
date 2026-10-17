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
#   meta.rds            the largest R-hat over the random effects
#   chains.rds          per chain its divergences, tree-depth hits and E-BFMI
#   model.stan          brms's Stan program
#   standata.json       its Stan data, as CmdStan reads it
# The draws are thinned as the level's settings say; chains.rds alone counts every iteration.
# Python judges the bar on these files.

suppressPackageStartupMessages({
  library(brms)
  library(cmdstanr)
  library(posterior)
})
# first, so that R.log names the session however the level ends
print(sessionInfo())

# the global variables: the fixed effects, the random-effect sds and correlations, sigma
GLOBAL <- "^(b_|sd_|cor_)|^sigma$"

dir <- commandArgs(trailingOnly = TRUE)[[1]]
input <- jsonlite::read_json(file.path(dir, "input.json"))
table <- read.csv(file.path(dir, "table.csv"))
settings <- input$settings
# cmdstanr compiles into <dir>, which lives across the levels, so a later level reuses the program
options(cmdstanr_write_stan_file_dir = dir)

prior <- set_prior(unlist(input$prior), class = names(input$prior))
family <- brmsfamily(input$family, link = input$link)
model <- brm(
  as.formula(input$formula), data = table, family = family, prior = prior, backend = "cmdstanr",
  chains = settings$chains, cores = settings$cores, warmup = settings$warmup,
  iter = settings$warmup + settings$draws,
  control = list(adapt_delta = settings$adapt_delta, max_treedepth = settings$max_treedepth),
  seed = input$seed, refresh = 0, silent = 2
)

global <- grep(GLOBAL, variables(model), value = TRUE)
local <- grep("^r_", variables(model), value = TRUE)
# brms labels a random effect r_<factor>[<group>,<effect>]
factors <- sub("^r_([^[]+)\\[.*$", "\\1", local)
summarized <- local[factors %in% unlist(input$summarized)]
keep <- c(global, setdiff(local, summarized))
draws <- as_draws_df(model, variable = c(global, local))
# thinned here, not by brm(), so that chains.rds counts every iteration
draws <- thin_draws(draws, settings$thin)

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

summary <- summarise_draws(subset_draws(draws, variable = global), "rhat", "ess_bulk", "ess_tail")
saveRDS(as.data.frame(summary), file.path(dir, "summary.rds"))
locals <- summarise_draws(subset_draws(draws, variable = local), "rhat")
saveRDS(data.frame(rhat_locals = max(locals$rhat)), file.path(dir, "meta.rds"))

# per chain, the sampler's parameters at every iteration after warmup
sampler <- rstan::get_sampler_params(model$fit, inc_warmup = FALSE)
divergences <- function(chain) sum(chain[, "divergent__"])
treedepth_hits <- function(chain) sum(chain[, "treedepth__"] >= settings$max_treedepth)
chains <- data.frame(
  chain = seq_along(sampler),
  divergences = sapply(sampler, divergences),
  treedepth_hits = sapply(sampler, treedepth_hits),
  ebfmi = rstan::get_bfmi(model$fit)
)
saveRDS(chains, file.path(dir, "chains.rds"))

writeLines(stancode(model), file.path(dir, "model.stan"))
cmdstanr::write_stan_json(standata(model), file.path(dir, "standata.json"))
