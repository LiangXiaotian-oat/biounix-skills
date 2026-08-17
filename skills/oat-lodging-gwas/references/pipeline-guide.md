# OatLodgingGWAS 分析流程指南

> 基于 GitHub 仓库 [LiangXiaotian-oat/OatLodgingGWAS](https://github.com/LiangXiaotian-oat/OatLodgingGWAS)
> 论文：Multi-environment GWAS identifies stable QTLs and candidate genes for lodging resistance-related traits in oat (Avena sativa L.)
> 作者：liangxiaotian+BioUnix+GLM5.2

## 一、流程概览

```
表型数据 → 描述统计 → 相关性分析 → 核心性状筛选(XGBoost) → 正态性检验
    → 遗传力/BLUP(方案A或B) → GWAS(FarmCPU) → 曼哈顿/QQ图 → SNP可视化 → 单倍型验证
```

## 二、环境准备

### R 依赖 (≥ 4.0)
```r
install.packages(c("lme4", "emmeans", "ggplot2", "CMplot",
                    "tidyverse", "data.table", "GGally", "PerformanceAnalytics",
                    "readxl", "writexl"))
devtools::install_github("jiabowang/GAPIT3")
```

### Python 依赖 (≥ 3.8)
```bash
pip install pandas numpy scipy matplotlib seaborn statsmodels scikit-learn xgboost
```

## 三、输入数据要求

用户只需准备**一个表型文件**，即可选择方案A或方案B进行遗传力计算。

### 表型文件
| 项目 | 说明 |
|------|------|
| 格式 | CSV 或 XLSX（若 XLSX 需指定 sheet 名） |
| 第 1 列 | Sample / SampleID（基因型名称） |
| 数据列 | `{环境}_{性状}` 或 `{环境}_{性状}_{重复}` |
| 环境代码 | 24WJ, 24BC, 25WJ, 25BC, 25CZ（5 个环境） |
| 性状代码 | LS, TIL, TID, TIBR, TIPS, TIWT（6 个性状） |
| LS 特殊 | LS 仅有环境均值（无重复），列名为 `{环境}_LS` |
| 其他性状 | 有 3 个重复，列名为 `{环境}_{性状}_{1~3}` |
| 已有 BLUP 列（可选） | `BLUP_{性状}`，用于方案B的 BLUP QC 对比 |

### 其他数据（GWAS/单倍型分析阶段需要）
| 数据类型 | 格式 | 说明 |
|----------|------|------|
| 基因型数据 | HMP/Tassel | 用于 GAPIT GWAS 的基因型矩阵 |
| VCF 文件 | VCF | 标准 VCF，含目标基因区域 SNP（单倍型分析用） |

## 四、两种遗传力计算方案

用户上传**同一个表型文件**后，根据田间试验设计选择方案A或方案B。两种方案是**算法层面**的区别，对应不同的重复情况。

### 田间试验设计与方案对应关系

#### 情况1：3 plots × 3 plants = 9株/品种/环境 → 选方案A

- 每个品种×每个环境有 3 个独立小区，每个小区选 3 株测量
- 理论上每环境每品种有 3 plots × 3 plants = 9 株
- 数据预处理：先取小区内 3 株均值，再取 3 个小区均值 → 每品种×每环境得到 1 个环境均值
- 方案A使用环境均值级别数据进行分析

#### 情况2：3 plots × 1 plant = 3个值/品种/环境 → 选方案B

- 每个品种×每个环境有 3 个独立小区，每个小区只取 1 株/得到 1 个性状值
- 每环境每品种有 3 个独立重复值
- 方案B直接利用 3 个重复值，保留重复间变异信息

### 方案A：标准 entry-mean 模型（`06_Heritability_BLUP_Calculation.R`）

- **适用田间设计**：情况1（3 plots × 3 plants = 9株，取均值后分析）
- **数据级别**：环境均值（每品种×每环境 1 个值）
- **模型**：`Value ~ (1|Genotype) + (1|Environment)`
- **H² 公式**：H² = Vg / (Vg + Ve/e)
  - 不区分性状有无重复数据
  - 残差 Ve 包含了 G×E 和小区内误差
- **特点**：计算简单快速，数据已预平均
- **输出**：遗传力表 + BLUP 值表

### 方案B：RCBD 分层模型 + LRT + BLUP QC（`recalculate_H2_LRT_RCBD.R`）

- **适用田间设计**：情况2（3 plots × 1 plant = 3个值，保留重复）
- **数据级别**：重复级（每品种×每环境 3 个值）
- **模型**：按性状有无重复数据分两种子模型
  - **LS（无重复）→ 环境均值模型**：`Value ~ (1|Genotype) + (1|Environment)`
    - H² = Vg / (Vg + Ve/e)
  - **其他性状（有重复）→ RCBD 重复级模型**：`Value ~ (1|Genotype) + (1|Environment) + (1|RepEnv) + (1|GE)`
    - H² = Vg / (Vg + Vge/e + Ve/(e×r))，e=5, r=3
    - 显式分解 G×E 方差（Vge）和重复间方差
- **LRT 检验**：似然比检验基因型方差是否显著（含边界混合模型 p 值校正）
- **BLUP QC**：比较新计算 BLUP 与已有 BLUP 的 Pearson 相关系数
- **特点**：方差分解更精细，提供显著性检验和质量控制
- **输出**：XLSX（H2_LRT + BLUP_QC + Software 三 sheet）

### 方案对比表

| 维度 | 方案A | 方案B |
|------|-------|-------|
| 田间设计 | 情况1（3×3=9株，取均值） | 情况2（3×1=3个值，保留重复） |
| 输入文件 | 同一个表型文件 | 同一个表型文件 |
| 数据级别 | 环境均值（1值/品种/环境） | 重复级（3值/品种/环境） |
| 模型类型 | 标准 LMM（不区分性状） | 分性状双模型（RCBD + 环境均值） |
| H² 公式 | Vg/(Vg+Ve/e) | LS: Vg/(Vg+Ve/e)；其他: Vg/(Vg+Vge/e+Ve/(e×r)) |
| Vge 分解 | 不区分（混入残差） | 显式分解 G×E 方差 |
| LRT 检验 | 无 | 有（含边界混合模型校正） |
| BLUP QC | 无 | 有（与已有 BLUP 对比验证） |
| 适用场景 | 初步分析、数据已预平均 | 精确估算、返修验证、审稿人要求 |
| 依赖包 | lme4, emmeans | lme4, readxl, dplyr, writexl |

## 五、分步流程

### Step 01: 表型描述统计 (`01_phenotype_stats.R`)
- **功能**：计算 Mean、SD、CV、Range

### Step 02: 相关性分析-PerformanceAnalytics (`02_correlation_visualization_PerformanceAnalytics.R`)
- **功能**：跨环境表型相关性矩阵 + 显著性标注

### Step 03: 相关性分析-GGally (`03_correlation_visualization_GGally.R`)
- **功能**：按环境分组的成对相关性矩阵 + 分布图

### Step 04: XGBoost 核心性状筛选 (`04_xgboost_feature_importance.py`)
- **功能**：计算农艺性状对倒伏指数(LS)的特征重要性

### Step 05: 正态性检验 (`05_normality_checks_visualization.R`)
- **功能**：频率分布直方图 + 拟合正态曲线

### Step 06: 遗传力与 BLUP 计算

用户在此步骤根据田间设计选择方案A或方案B（上传同一个表型文件）：

- **情况1（3×3=9株，取均值）→ 方案A** (`06_Heritability_BLUP_Calculation.R`)：标准 entry-mean H²
- **情况2（3×1=3个值，保留重复）→ 方案B** (`recalculate_H2_LRT_RCBD.R`)：RCBD 分层模型 + LRT + BLUP QC
  - 用法：`Rscript recalculate_H2_LRT_RCBD.R input_TableS1.xlsx output_results.xlsx`
  - 详见 [recalculate_H2_LRT_RCBD.R](./recalculate_H2_LRT_RCBD.R)

### Step 07: GWAS 分析 (`07_gapit_gwas.R`)
- **功能**：GAPIT FarmCPU 模型多环境 GWAS

### Step 08: 曼哈顿图与 QQ 图 (`08_Manhattan_QQ_Plots.R`)
- **功能**：各环境 + BLUP 值的 Manhattan 图和 Q-Q 图

### Step 09: SNP 基因型可视化 (`09_SNP_genotype_visualization.py`)
- **功能**：KASP 基因型散点图 + 基因结构标注

### Step 10: 单倍型验证 (`10_haplotype_verification.py`)
- **功能**：单 SNP 效应箱线图 + 基因聚合效应回归分析

## 六、运行方式

```bash
git clone https://github.com/LiangXiaotian-oat/OatLodgingGWAS.git
cd OatLodgingGWAS

Rscript 01_phenotype_stats.R
Rscript 02_correlation_visualization_PerformanceAnalytics.R
Rscript 03_correlation_visualization_GGally.R
Rscript 05_normality_checks_visualization.R

# Step 06：根据田间设计选择方案A或方案B（同一表型文件）
Rscript 06_Heritability_BLUP_Calculation.R              # 方案A
# 或
Rscript recalculate_H2_LRT_RCBD.R input.xlsx out.xlsx   # 方案B

Rscript 07_gapit_gwas.R
Rscript 08_Manhattan_QQ_Plots.R

python 04_xgboost_feature_importance.py
python 09_SNP_genotype_visualization.py
python 10_haplotype_verification.py
```

## 七、引用

Liang Xiaotian, et al. (2025). Multi-environment genome-wide association study identifies stable QTLs and candidate genes for lodging resistance-related traits in oat (Avena sativa L.).