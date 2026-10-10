# run.R fits one level of a problem's reference with brms through cmdstanr and checks the bar.
#
# Usage: Rscript run.R <dir>
# <dir> holds the handoff from Python: table.csv (the aliased standardised table) and input.json
# (formula, family, link, prior per class, the level's settings, seed). The script writes back,
# one data frame per file since pyreadr reads no R lists:
#   draws.rds    chain, iteration and the global variables brms keeps
#   sampler.rds  chain, iteration and the sampler parameters per iteration
#   summary.rds  per global variable its mean, sd, rank-normalised R-hat, bulk and tail ESS
#   meta.rds     the brms, cmdstanr and CmdStan versions, the bar's verdict, sessionInfo()

suppressPackageStartupMessages({
  library(brms)
  library(posterior)
})

# the global variables: the fixed effects, the random-effect sds and correlations, sigma
GLOBAL <- "^(b_|sd_|cor_)|^sigma$"
# the bar on the stored draws of the global variables
RHAT <- 1.01
ESS <- 400

dir <- commandArgs(trailingOnly = TRUE)[[1]]
input <- jsonlite::read_json(file.path(dir, "input.json"))
table <- read.csv(file.path(dir, "table.csv"))
settings <- input$settings

prior <- do.call(c, lapply(names(input$prior), function(k) set_prior(input$prior[[k]], class = k)))
family <- get(input$family, mode = "function")(link = input$link)
model <- brm(
  as.formula(input$formula), data = table, family = family, prior = prior, backend = "cmdstanr",
  chains = settings$chains, cores = settings$cores, warmup = settings$warmup,
  iter = settings$warmup + settings$draws, thin = settings$thin,
  control = list(adapt_delta = settings$adapt_delta, max_treedepth = settings$max_treedepth),
  seed = input$seed, refresh = 0, silent = 2
)

keep <- grep(GLOBAL, variables(model), value = TRUE)
draws <- as_draws_df(model, variable = keep)
saveRDS(
  data.frame(
    chain = draws$.chain, iteration = draws$.iteration, as.data.frame(draws)[keep],
    check.names = FALSE
  ),
  file.path(dir, "draws.rds")
)

nuts <- nuts_params(model)
sampler <- reshape(nuts, idvar = c("Chain", "Iteration"), timevar = "Parameter", direction = "wide")
names(sampler) <- sub("^Value\\.", "", names(sampler))
names(sampler)[1:2] <- c("chain", "iteration")
rownames(sampler) <- NULL
saveRDS(sampler, file.path(dir, "sampler.rds"))

summary <- as.data.frame(summarise_draws(draws, "mean", "sd", "rhat", "ess_bulk", "ess_tail"))
saveRDS(summary, file.path(dir, "summary.rds"))

passed <- all(summary$rhat < RHAT) && all(summary$ess_bulk >= ESS) &&
  all(summary$ess_tail >= ESS) && sum(sampler$divergent__) == 0
saveRDS(
  data.frame(
    brms = as.character(packageVersion("brms")),
    cmdstanr = as.character(packageVersion("cmdstanr")),
    cmdstan = cmdstanr::cmdstan_version(),
    passed = passed,
    session = paste(capture.output(sessionInfo()), collapse = "\n")
  ),
  file.path(dir, "meta.rds")
)
