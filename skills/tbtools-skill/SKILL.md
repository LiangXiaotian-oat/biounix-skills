---
name: tbtools-skill
description: TBtools 集成式生物信息学 GUI 软件完整使用指南。涵盖安装配置（三平台安装步骤、BLAST+/BWA-MEM2 依赖）、12 大类 200+ 工具功能目录、JAR 包模块结构分析、7 个常见工作流模板。当用户需要使用 TBtools 进行序列提取、基因结构可视化、热图绘制、BLAST 比对、GO/KEGG 富集、Venn 图、共线性分析、GFF 操作、Ka/Ks 计算、NGS 数据分析或比较基因组学任务时触发。
triggers:
  - TBtools
  - tbtools
  - 序列提取
  - 基因结构可视化
  - 热图绘制
  - BLAST比对
  - GO富集
  - KEGG富集
  - Venn图
  - 共线性分析
  - GFF操作
  - Ka/Ks计算
  - NGS数据分析
  - 比较基因组学
  - gene structure visualization
  - heatmap
  - synteny analysis
  - Ka/Ks
  - GO enrichment
  - KEGG enrichment
always_active: false
version: null
category: other
author: Liangxiaotian+BioUnix+GLM5.2
---
TBtools-II is an integrated bioinformatics GUI tool (Java-based) for sequence analysis, genomics, and visualization. Use this skill when users need to perform tasks in TBtools such as sequence extraction, gene structure visualization, heatmap plotting, BLAST, GO/KEGG enrichment, Venn diagrams, synteny analysis, GFF manipulation, Ka/Ks calculation, or NGS data analysis.

## Installation

1. Verify Java 8+ is installed (`java -version`).
2. Download TBtools-II JAR from [GitHub Releases](https://github.com/CJ-Chen/TBtools/releases) or the mirror link.
3. Launch: `java -jar TBtools.jar` (or double-click on Windows/macOS).
4. Install optional dependencies as needed: BLAST+, BWA-MEM2, MEME Suite, SRA Toolkit, Samtools.

For detailed platform-specific steps, dependency installation, and troubleshooting, see [📋 Installation Guide](./references/installation-guide.md).

## Function Catalog

TBtools organizes 200+ tools across 12 categories. Key categories:

| Category | Common Tasks |
|----------|-------------|
| Sequence Manipulation | Extract, reverse-complement, translate, format conversion |
| GFF/GTF Processing | Extract features, convert formats, filter by attribute |
| BLAST | Local BLAST, batch extraction, result parsing |
| Visualization | Gene structure, heatmap, synteny, chromosome mapping |
| Enrichment | GO enrichment, KEGG pathway enrichment |
| Comparative Genomics | Synteny analysis, Ka/Ks calculation, collinearity |
| NGS Analysis | RNA-seq, ChIP-seq, VCF processing |
| Statistics | Venn diagrams, bar charts, PCA, correlation |

For the full menu paths and input/output formats, see [📋 Function Catalog](./references/function-catalog.md).

For JAR internal module structure (6989 classes), see [📋 JAR Modules](./references/jar-modules.md).

## Common Workflows

### 1. Sequence Extraction from Genome
1. Load genome FASTA via `File → Load Genome Sequence`.
2. Load GFF annotation via `File → Load Genome Annotation`.
3. Use `Sequence → Extract Sequence (by GFF)` to pull gene/CDS/protein sequences.
4. Select feature type (gene, mRNA, CDS, exon) and output format.

### 2. Gene Structure Visualization
1. Prepare GFF file and optional CDS/protein sequences.
2. Use `Graphic → Gene Structure Display`.
3. Load GFF, select target gene IDs.
4. Customize intron/exon colors, scale, and output format (PDF/PNG/SVG).

### 3. Heatmap Drawing
1. Prepare expression matrix (TSV/CSV: rows = genes, columns = samples).
2. Use `Graphic → HeatMap`.
3. Load matrix, configure clustering method (average linkage, complete, etc.).
4. Set color scheme, row/column labels, and export.

### 4. BLAST + Batch Sequence Extraction
1. Use `Blast → Local BLAST` or `Blast → Batch Sequence Extraction`.
2. Set query FASTA and database (or build with `makeblastdb`).
3. Configure e-value, word size, output format.
4. Extract hit sequences with flanking regions if needed.

### 5. GO/KEGG Enrichment
1. Prepare gene list (one ID per line) and background annotation.
2. Use `Functional Genomics → GO Enrichment` or `KEGG Enrichment`.
3. Load gene list and annotation file (GO terms or KEGG pathways).
4. Set p-value cutoff, correction method (BH/FDR).
5. Export bar plot, dot plot, or table.

### 6. Synteny Analysis
1. Prepare GFF files for both species and BLAST results (protein-protein).
2. Use `Comparative Genomics → Synteny Analysis (MCScanX)`.
3. Load GFF and BLAST pairwise results.
4. Configure block size, gap, and e-value thresholds.
5. Visualize with `Graphic → Dual Synteny Plot`.

### 7. Ka/Ks Calculation
1. Prepare CDS sequences for pairs of orthologous genes.
2. Use `Comparative Genomics → Simple Ka/Ks Calculation`.
3. Load paired CDS sequences (or generate pairs from synteny).
4. Select substitution model (YN00, NG, etc.).
5. Export results table with Ka, Ks, Ka/Ks values.

## When to Use

Trigger this skill when users mention TBtools or need GUI-based bioinformatics tasks including: sequence extraction, gene structure plots, heatmaps, BLAST, GO/KEGG enrichment, Venn diagrams, synteny/collinearity analysis, GFF manipulation, Ka/Ks, or NGS data processing.