---
name: admixture-pca-visualization
description: 读取 ADMIXTURE Q matrix（指定 K 值）和 smartpca eigenvectors/eigenvalues，将每个样本按 admixture 最大 ancestry 比例归入对应群体（which.max 分群），在 PCA 散点图上按分群着色并输出分群归属 CSV。适用于群体遗传学分析中需要将 ADMIXTURE 群体结构结果与 PCA 降维结果整合可视化的场景。触发关键词：admixture、Q matrix、smartpca、PCA、群体结构、ancestry proportion、分群着色、eigenvectors、eigenvalues。
triggers:
  - admixture
  - Q matrix
  - smartpca
  - PCA可视化
  - 群体结构
  - ancestry
  - 分群着色
  - eigenvectors
  - eigenvalues
  - admixture pca
  - Q矩阵
  - 主成分分析着色
always_active: false
version: null
category: null
author: GLM-5.2 + BioUnix
created_at: "2026-07-29T14:45:47.890Z"
updated_at: "2026-07-29T14:45:47.890Z"
match_count: 0
use_count: 0
---
# ADMIXTURE + PCA Visualization Pipeline

## Prerequisites
- ADMIXTURE Q matrix file (e.g., `*.Q` with K columns)
- smartpca eigenvectors file (e.g., `*.evec`)
- smartpca eigenvalues file (e.g., `*.eval`)
- R with ggplot2 installed

## Step 1: Explore File Formats
- Inspect Q matrix: `head -5 <Q_file>` — confirm it has K numeric columns, no header, sample order matches fam file
- Inspect eigenvectors: `head -5 <evec_file>` — note comment lines (starting with `#`), sample name format (e.g., `NAME:NAME`), and PC columns
- Inspect eigenvalues: `cat <eval_file>` — extract variance explained per PC

## Step 2: Verify Sample Count Consistency
- Count rows in Q matrix: `wc -l <Q_file>`
- Count data rows in eigenvectors (excluding comment lines): `grep -v '^#' <evec_file> | wc -l`
- Confirm both match; if not, investigate sample ordering or missing samples

## Step 3: Parse Eigenvectors
- Read evec file, skip comment lines (lines starting with `#`)
- Extract sample names: if format is `NAME:NAME`, use `sub(":.*", "", sample_col)` to get clean names
- Extract PC1–PC6 (or as many as needed) as numeric columns
- Store as data frame with columns: `Sample`, `PC1`, `PC2`, ..., `PCn`

## Step 4: Parse Q Matrix
- Read Q matrix (no header, whitespace-separated)
- Assign column names: `K1`, `K2`, ..., `Kk` based on specified K value
- Add Sample column matching eigenvectors order (verify alignment)

## Step 5: Assign Clusters via which.max
- For each sample, find column index with maximum ancestry proportion: `apply(q_matrix, 1, which.max)`
- Convert to factor with levels `K1`...`Kk`: `factor(paste0("K", cluster_idx), levels = paste0("K", 1:K))`
- Merge with eigenvectors data frame by Sample name

## Step 6: Calculate Variance Explained
- Read eigenvalues file
- Compute variance explained per PC: `eval_i / sum(eval) * 100`
- Format as percentage strings for axis labels, e.g., `"PC1 (41.39%)"`

## Step 7: Plot PCA with Cluster Colors (ggplot2)
- Create multi-panel scatter plots for PC1×PC2, PC1×PC3, PC2×PC3, etc.
- Use `aes(x=PCi, y=PCj, color=Cluster)`
- Apply `scale_color_manual` with `values` and `names` matching Cluster factor levels exactly (e.g., `K1`–`K6`)
- Set axis labels with variance explained percentages
- Save as both PDF and PNG (300 dpi)
- Output to `01_pca_plot/` folder

## Step 8: Output Cluster Assignment CSV
- Write sample-to-cluster mapping: columns `Sample`, `Cluster`, `K1`...`Kk` ancestry proportions
- Save to `02_pca_data/` folder

## Key Pitfalls
- **scale_color_manual mismatch**: `names` must exactly match Cluster factor levels; otherwise colors won't map correctly
- **Sample name format**: smartpca outputs `NAME:NAME`; must strip with `sub(":.*", "", ...)` before merging
- **Sample order**: Q matrix and evec must have same sample order; always verify with row count and spot-check
- **Comment lines in evec**: first line may start with `#` (e.g., `#eigvals:`); use `skip` or `grep -v '^#'`
- **Variance calculation**: eigenvalues file may have different formats; confirm whether values are already normalized or raw

## Output Organization
- `01_pca_plot/` — PDF and PNG scatter plots
- `02_pca_data/` — cluster assignment CSV and any intermediate data files