---
name: oat-lodging-gwas
description: 燕麦抗倒伏多环境 GWAS 分析完整流程，基于 GitHub 仓库 LiangXiaotian-oat/OatLodgingGWAS。涵盖表型统计、相关性可视化、XGBoost 核心性状筛选、正态性检验、广义遗传力与 BLUP 计算、GAPIT FarmCPU GWAS、Manhattan/QQ 图、SNP 基因型可视化、单倍型验证共 10 步分析。当用户需要执行燕麦 GWAS 分析、抗倒伏性状遗传解析、单倍型分析、FarmCPU 模型 GWAS、BLUP 遗传力计算、KASP 基因型可视化或复现该论文分析流程时触发。
triggers:
  - 燕麦GWAS
  - oat GWAS
  - 抗倒伏
  - lodging resistance
  - FarmCPU
  - GAPIT
  - BLUP遗传力
  - 单倍型分析
  - haplotype
  - XGBoost性状筛选
  - Manhattan图
  - QQ图
  - OatLodgingGWAS
  - 多环境GWAS
  - KASP基因型
always_active: false
version: 0.2.1
category: other
author: liangxiaotian+BioUnix+GLM5.2
---
# OatLodgingGWAS Analysis Pipeline

Multi-environment GWAS pipeline for lodging resistance traits in oat, based on the GitHub repository [LiangXiaotian-oat/OatLodgingGWAS](https://github.com/LiangXiaotian-oat/OatLodgingGWAS) and the associated publication.

## Prerequisites

Clone the repository and install dependencies:

```bash
git clone https://github.com/LiangXiaotian-oat/OatLodgingGWAS.git
cd OatLodgingGWAS