# OatLodgingGWAS 脚本概览

> 仓库地址：https://github.com/LiangXiaotian-oat/OatLodgingGWAS
> 许可证：MIT
> 作者：liangxiaotian+BioUnix+GLM5.2

## 脚本清单

| 序号 | 文件名 | 语言 | 功能 |
|------|--------|------|------|
| 01 | `01_phenotype_stats.R` | R | 表型描述统计（Mean/SD/CV/Range） |
| 02 | `02_correlation_visualization_PerformanceAnalytics.R` | R | 跨环境表型相关性（PerformanceAnalytics） |
| 03 | `03_correlation_visualization_GGally.R` | R | 分环境成对相关性矩阵（GGally） |
| 04 | `04_xgboost_feature_importance.py` | Python | XGBoost 核心性状筛选（特征重要性） |
| 05 | `05_normality_checks_visualization.R` | R | 正态性检验（直方图+正态曲线） |
| 06 | `06_Heritability_BLUP_Calculation.R` | R | 方案A：标准 entry-mean H² + BLUP |
| 06B | `recalculate_H2_LRT_RCBD.R` | R | 方案B：RCBD 分层模型 H² + LRT + BLUP QC |
| 07 | `07_gapit_gwas.R` | R | GWAS 分析（GAPIT FarmCPU 模型） |
| 08 | `08_Manhattan_QQ_Plots.R` | R | Manhattan 图 + Q-Q 图 |
| 09 | `09_SNP_genotype_visualization.py` | Python | KASP 基因型散点图 + 基因结构 |
| 10 | `10_haplotype_verification.py` | Python | 单 SNP 效应箱线图 + 聚合效应回归 |

## 两种遗传力计算方案（同一表型文件，算法不同）

### 方案A：`06_Heritability_BLUP_Calculation.R`
- **适用田间设计**：情况1（3 plots × 3 plants = 9株，取均值后分析）
- **数据级别**：环境均值（1值/品种/环境）
- **模型**：所有性状统一标准 LMM，不区分有无重复
- **H²**：Vg/(Vg+Ve/e)
- **输出**：遗传力表 + BLUP 值表
- **适用**：初步分析、数据已预平均

### 方案B：`recalculate_H2_LRT_RCBD.R`
- **适用田间设计**：情况2（3 plots × 1 plant = 3个值，保留重复）
- **数据级别**：重复级（3值/品种/环境）
- **模型**：按性状分双模型（LS 环境均值 / 其他 RCBD 重复级）
- **H²**：LS → Vg/(Vg+Ve/e)；其他 → Vg/(Vg+Vge/e+Ve/(e×r))
- **额外功能**：LRT 检验 + BLUP QC
- **输出**：XLSX（H2_LRT + BLUP_QC + Software）
- **适用**：返修验证、精确估算

## 田间设计与方案选择指南

| 田间设计 | 每品种×每环境观测数 | 推荐方案 | 原因 |
|----------|---------------------|----------|------|
| 3 plots × 3 plants = 9株 | 9（取均值后1个） | 方案A | 数据已预平均到环境均值，H²公式不体现r |
| 3 plots × 1 plant = 3个值 | 3（直接使用） | 方案B | 保留重复间变异，H²公式分解Vge和Ve |

## 依赖汇总

### R 包
| 包名 | 用途 | 对应脚本 |
|------|------|----------|
| GAPIT | GWAS (FarmCPU) | 07 |
| lme4 | 遗传力/BLUP (LMM) | 06, 06B |
| emmeans | BLUP 估算 | 06 |
| readxl | 读取 XLSX | 06B |
| writexl | 写出 XLSX | 06B |
| dplyr | 数据处理 | 06B, 多个 |
| PerformanceAnalytics | 相关性矩阵 | 02 |
| GGally | 分组相关性 | 03 |
| ggplot2 | 通用绘图 | 05, 08 |
| CMplot | Manhattan/QQ 图 | 08 |
| tidyverse | 数据处理 | 多个 |
| data.table | 数据处理 | 多个 |

### Python 包
| 包名 | 用途 | 对应脚本 |
|------|------|----------|
| pandas | 数据处理 | 04, 09, 10 |
| numpy | 数值计算 | 04, 09, 10 |
| scipy | 统计检验 | 10 |
| statsmodels | 统计建模 | 10 |
| scikit-learn | 机器学习 | 04 |
| xgboost | 特征重要性 | 04 |
| matplotlib | 绘图 | 04, 09, 10 |
| seaborn | 统计绘图 | 04, 09, 10 |

## 表型文件格式（方案A和方案B共用）

| 项目 | 说明 |
|------|------|
| 格式 | CSV 或 XLSX |
| 第 1 列 | Sample / SampleID（基因型名称） |
| 数据列命名 | `{环境}_{性状}`（LS）或 `{环境}_{性状}_{重复号}`（其他性状） |
| 环境代码 | 24WJ, 24BC, 25WJ, 25BC, 25CZ |
| 性状代码 | LS, TIL, TID, TIBR, TIPS, TIWT |
| 已有 BLUP 列（可选） | `BLUP_{性状}`，方案B 用于 QC 对比 |

### 列命名示例
```
Sample, 24WJ_LS, 24WJ_TIL_1, 24WJ_TIL_2, 24WJ_TIL_3, 24BC_LS, ..., BLUP_TIL
G001,   3.5,     45.2,       44.8,       46.1,       3.2,     ..., 44.5
G002,   4.1,     52.3,       51.7,       53.0,       3.8,     ..., 51.8
```