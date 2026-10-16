# run.R fits one level of a problem's reference with brms through cmdstanr.
#
# Usage: Rscript run.R <dir>
# <dir> holds the handoff from Python: table.csv (the aliased standardised table) and input.json
# (formula, family, link, prior per class, the level's settings, seed, the factors to
# summarise). It prints sessionInfo() first, then writes back, one data frame per file since
# pyreadr reads no R lists, every draw thinned as the level's settings say:
#   draws.rds           chain, iteration, the global variables brms keeps and the random
#                       effects of every factor not summarised
#   locals_summary.rds  per random effect of a summarised factor its mean, sd and 5/25/50/75/95%
#                       quantiles, where a factor is summarised
#   chains.rds          per chain its divergences, tree-depth hits and E-BFMI, over every iteration
#   summary.rds         per global variable its rank-normalised R-hat, bulk and tail ESS
#   meta.rds            the largest R-hat over the random effects
#   model.stan          brms's Stan program
#   standata.json       its Stan data, as CmdStan reads it
# Python judges the bar on them.

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
# the compiled program in <dir>, which lives across the levels, so a later level reuses it
options(cmdstanr_write_stan_file_dir = dir)

prior <- do.call(c, lapply(names(input$prior), function(k) set_prior(input$prior[[k]], class = k)))
family <- get(input$family, mode = "function")(link = input$link)
model <- brm(
  as.formula(input$formula), data = table, family = family, prior = prior, backend = "cmdstanr",
  chains = settings$chains, cores = settings$cores, warmup = settings$warmup,
  iter = settings$warmup + settings$draws,
  control = list(adapt_delta = settings$adapt_delta, max_treedepth = settings$max_treedepth),
  seed = input$seed, refresh = 0, silent = 2
)

global <- grep(GLOBAL, variables(model), value = TRUE)
local <- grep("^r_", variables(model), value = TRUE)
# a random effect r_<factor>[<group>,<effect>] of a factor to summarise
summarised <- local[sub("^r_([^[]+)\\[.*$", "\\1", local) %in% unlist(input$summarised)]
keep <- c(global, setdiff(local, summarised))
# thinned after sampling, so that the sampler's checks below see every iteration
draws <- thin_draws(as_draws_df(model, variable = c(global, local)), settings$thin)
saveRDS(
  data.frame(
    chain = draws$.chain, iteration = draws$.iteration, as.data.frame(draws)[keep],
    check.names = FALSE
  ),
  file.path(dir, "draws.rds")
)
quantiles <- function(x) quantile2(x, probs = c(0.05, 0.25, 0.5, 0.75, 0.95))
effects <- summarise_draws(subset_draws(draws, variable = local), "mean", "sd", quantiles, "rhat")
if (length(summarised) > 0) {
  rows <- effects$variable %in% summarised
  saveRDS(as.data.frame(effects[rows, names(effects) != "rhat"]), file.path(dir, "locals_summary.rds"))
}

nuts <- nuts_params(model)
divergent <- nuts[nuts$Parameter == "divergent__", ]
treedepth <- nuts[nuts$Parameter == "treedepth__", ]
chains <- data.frame(
  chain = seq_len(settings$chains),
  divergences = as.vector(tapply(divergent$Value, divergent$Chain, sum)),
  treedepth_hits = as.vector(tapply(treedepth$Value >= settings$max_treedepth, treedepth$Chain, sum)),
  ebfmi = rstan::get_bfmi(model$fit)
)
saveRDS(chains, file.path(dir, "chains.rds"))

summary <- summarise_draws(subset_draws(draws, variable = global), "rhat", "ess_bulk", "ess_tail")
saveRDS(as.data.frame(summary), file.path(dir, "summary.rds"))
saveRDS(data.frame(rhat_locals = max(effects$rhat)), file.path(dir, "meta.rds"))

writeLines(stancode(model), file.path(dir, "model.stan"))
cmdstanr::write_stan_json(unclass(standata(model)), file.path(dir, "standata.json"))
