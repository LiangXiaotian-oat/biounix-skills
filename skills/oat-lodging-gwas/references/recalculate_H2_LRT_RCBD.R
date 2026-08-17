# Recalculate entry-mean broad-sense heritability and genotype-variance LRT
# from Supplementary Table S1 (sheet: 24_25_blup_pehno).
#
# Usage:
# Rscript recalculate_H2_LRT_RCBD.R input_TableS1.xlsx output_results.xlsx
#
# Required packages: readxl, lme4, dplyr, writexl

required_packages <- c("readxl", "lme4", "dplyr", "writexl")
missing_packages <- required_packages[!vapply(required_packages, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing_packages) > 0) {
  stop(
    "Missing required packages: ", paste(missing_packages, collapse = ", "),
    ". Install them before running this script."
  )
}

suppressPackageStartupMessages({
  library(readxl)
  library(lme4)
  library(dplyr)
  library(writexl)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) {
  stop("Usage: Rscript recalculate_H2_LRT_RCBD.R input_TableS1.xlsx output_results.xlsx")
}

input_file <- normalizePath(args[[1]], mustWork = TRUE)
output_file <- args[[2]]
sheet_name <- "24_25_blup_pehno"
environments <- c("24WJ", "24BC", "25WJ", "25BC", "25CZ")
traits <- c("LS", "TIL", "TID", "TIBR", "TIPS", "TIWT")
e_nominal <- length(environments)
r_nominal <- 3L

wide <- read_excel(input_file, sheet = sheet_name, na = c("NA", ""))
wide$Sample <- as.character(wide$Sample)

build_long <- function(wide, trait) {
  rows <- list()
  k <- 1L
  for (env in environments) {
    if (trait == "LS") {
      columns <- paste0(env, "_", trait)
      reps <- NA_integer_
    } else {
      columns <- paste0(env, "_", trait, "_", 1:3)
      reps <- 1:3
    }
    for (j in seq_along(columns)) {
      column <- columns[[j]]
      if (!column %in% names(wide)) next
      value <- suppressWarnings(as.numeric(wide[[column]]))
      keep <- !is.na(value)
      if (!any(keep)) next
      rows[[k]] <- data.frame(
        Genotype = wide$Sample[keep],
        Environment = env,
        Replicate = if (trait == "LS") "Mean" else as.character(reps[[j]]),
        Trait = trait,
        Value = value[keep],
        stringsAsFactors = FALSE
      )
      k <- k + 1L
    }
  }
  bind_rows(rows) %>%
    mutate(
      Genotype = factor(Genotype),
      Environment = factor(Environment, levels = environments),
      Replicate = factor(Replicate),
      GE = interaction(Genotype, Environment, drop = TRUE),
      RepEnv = interaction(Environment, Replicate, drop = TRUE)
    )
}

get_variance <- function(model, group_name) {
  vc <- as.data.frame(VarCorr(model))
  value <- vc$vcov[vc$grp == group_name]
  if (length(value) == 0L) return(NA_real_)
  as.numeric(value[[1]])
}

control <- lmerControl(
  optimizer = "bobyqa",
  optCtrl = list(maxfun = 200000),
  check.conv.singular = .makeCC(action = "message", tol = 1e-4)
)

result_rows <- list()
blup_rows <- list()

for (trait in traits) {
  message("Fitting ", trait, "...")
  dat <- build_long(wide, trait)

  if (trait == "LS") {
    full_formula <- Value ~ 1 + (1 | Genotype) + (1 | Environment)
    null_formula <- Value ~ 1 + (1 | Environment)
    analysis <- "two-stage environment-mean model"
    note <- paste0(
      "LS replicate records are not present in Table S1; residual combines GxE ",
      "and within-environment plot error after averaging."
    )
  } else {
    full_formula <- Value ~ 1 + (1 | Genotype) + (1 | Environment) +
      (1 | RepEnv) + (1 | GE)
    null_formula <- Value ~ 1 + (1 | Environment) + (1 | RepEnv) + (1 | GE)
    analysis <- "replicate-level RCBD model"
    note <- "H2 = Vg / (Vg + Vge/5 + Ve/(5*3))."
  }

  full_reml <- lmer(full_formula, data = dat, REML = TRUE, control = control)
  full_ml <- lmer(full_formula, data = dat, REML = FALSE, control = control)
  null_ml <- lmer(null_formula, data = dat, REML = FALSE, control = control)

  vg <- get_variance(full_reml, "Genotype")
  ve <- get_variance(full_reml, "Residual")
  venv <- get_variance(full_reml, "Environment")
  vrep <- get_variance(full_reml, "RepEnv")
  vge <- get_variance(full_reml, "GE")

  if (trait == "LS") {
    h2 <- vg / (vg + ve / e_nominal)
  } else {
    h2 <- vg / (vg + vge / e_nominal + ve / (e_nominal * r_nominal))
  }

  lrt_chisq <- max(0, 2 * (as.numeric(logLik(full_ml)) - as.numeric(logLik(null_ml))))
  lrt_p <- pchisq(lrt_chisq, df = 1, lower.tail = FALSE)
  lrt_p_boundary <- 0.5 * lrt_p

  env_counts <- dat %>% distinct(Genotype, Environment) %>% count(Genotype, name = "n_env")
  old_blup_column <- paste0("BLUP_", trait)
  new_blup <- ranef(full_reml)$Genotype[, 1]
  names(new_blup) <- rownames(ranef(full_reml)$Genotype)
  old_blup <- suppressWarnings(as.numeric(wide[[old_blup_column]]))
  names(old_blup) <- wide$Sample
  common <- intersect(names(new_blup), names(old_blup)[!is.na(old_blup)])
  blup_correlation <- cor(new_blup[common], old_blup[common], use = "complete.obs")

  result_rows[[trait]] <- data.frame(
    Trait = trait,
    Analysis = analysis,
    N_observations = nrow(dat),
    N_genotypes = nlevels(dat$Genotype),
    N_environments = nlevels(droplevels(dat$Environment)),
    Median_environments_per_genotype = median(env_counts$n_env),
    Min_environments_per_genotype = min(env_counts$n_env),
    Max_environments_per_genotype = max(env_counts$n_env),
    Variance_G = vg,
    Variance_E = venv,
    Variance_RepE = vrep,
    Variance_GE = vge,
    Variance_Residual = ve,
    H2_entry_mean = h2,
    LRT_ChiSq = lrt_chisq,
    LRT_df = 1L,
    LRT_P_chi1 = lrt_p,
    LRT_P_boundary_mixture = lrt_p_boundary,
    REML_singular = isSingular(full_reml, tol = 1e-4),
    Existing_vs_RCBD_BLUP_r = blup_correlation,
    Model_note = note,
    stringsAsFactors = FALSE
  )

  blup_rows[[trait]] <- data.frame(
    Trait = trait,
    Genotype = names(new_blup),
    BLUP_RCBD = as.numeric(new_blup),
    Existing_BLUP = as.numeric(old_blup[names(new_blup)]),
    stringsAsFactors = FALSE
  )
}

results <- bind_rows(result_rows)
blups <- bind_rows(blup_rows)
software <- data.frame(
  Item = c("R", "lme4", "readxl", "dplyr", "writexl", "Input workbook", "Input sheet"),
  Version_or_value = c(
    R.version.string,
    as.character(packageVersion("lme4")),
    as.character(packageVersion("readxl")),
    as.character(packageVersion("dplyr")),
    as.character(packageVersion("writexl")),
    input_file,
    sheet_name
  ),
  stringsAsFactors = FALSE
)

dir.create(dirname(output_file), recursive = TRUE, showWarnings = FALSE)
write_xlsx(
  list(
    H2_LRT = results,
    BLUP_QC = blups,
    Software = software
  ),
  path = output_file
)
message("Saved: ", normalizePath(output_file, mustWork = FALSE))