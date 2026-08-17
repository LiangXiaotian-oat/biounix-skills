# TBtools 功能目录

> 基于 TBtools-II v2.515 源码分析与官方文档整理

## 一、Sequence Toolkits（序列工具集）

菜单路径：Main menubar → Sequence Toolkits

### 1.1 Fasta Tools
| 功能 | 菜单路径 | 输入 | 输出 |
|------|----------|------|------|
| Amazing Fasta Extractor | Sequence Toolkits → Fasta Tools → Amazing Fasta Extractor | ① FASTA 序列文件 ② 基因 ID 列表或区域（ChrID Start End） | 提取的序列文件 |
| Fasta Statistics | Sequence Toolkits → Fasta Tools → Fasta Statistics | FASTA 文件 | 序列长度/GC 含量统计 |
| Fasta Merge | Sequence Toolkits → Fasta Tools → Fasta Merge | 多个 FASTA 文件 | 合并后的 FASTA |
| Fasta Split | Sequence Toolkits → Fasta Tools → Fasta Split | FASTA 文件 | 按条拆分的 FASTA 文件 |
| Sequence Format Convert | Sequence Toolkits → Fasta Tools → Sequence Format Convert | FASTA/Clustal/MEGA/Nexus/PAML/Phylip 格式 | 目标格式文件 |

### 1.2 Gff3/GTF Manipulator
| 功能 | 菜单路径 | 输入 | 输出 |
|------|----------|------|------|
| Gtf/Gff3 Sequences Extractor | Sequence Toolkits → Gff3/GTF Manipulator → Gtf/Gff3 Sequences Extractor | ① 基因组 FASTA ② GFF3/GTF 注释文件 ③ 可选：基因 ID 列表 | CDS/Protein/Exon/Intron/UTR 序列 |
| Gff3/Gtf Merge | Sequence Toolkits → Gff3/GTF Manipulator → Gff3/Gtf Merge | 多个 GFF3/GTF 文件 | 合并后的注释文件 |
| Gff3/Gtf Sort | Sequence Toolkits → Gff3/GTF Manipulator → Gff3/Gtf Sort | GFF3/GTF 文件 | 按染色体和位置排序的文件 |
| Gff3/Gtf Filter | Sequence Toolkits → Gff3/GTF Manipulator → Gff3/Gtf Filter | GFF3/GTF 文件 | 按特征类型过滤的文件 |
| Gxf Gene Structure Fixer | Sequence Toolkits → Gff3/GTF Manipulator → Gxf Gene Structure Fixer | GFF3/GTF 文件 | 修正基因结构后的文件 |

### 1.3 其他序列工具
| 功能 | 菜单路径 | 说明 |
|------|----------|------|
| ORF Predictor | Sequence Toolkits → ORF Predictor | 预测开放阅读框 |
| Sequence Reverse Complement | Sequence Toolkits → Sequence Tools → Reverse Complement | 反向互补序列 |
| Sequence Translate | Sequence Toolkits → Sequence Tools → Translate | DNA 翻译为蛋白质 |
| Primer Design | Sequence Toolkits → Primer Tools | 引物设计 |
| Ab1 File Parser | Sequence Toolkits → Ab1 Parser | 解析 Sanger 测序 .ab1 文件 |

## 二、BLAST 工具集

菜单路径：Main menubar → BLAST

| 功能 | 菜单路径 | 输入 | 输出 |
|------|----------|------|------|
| Local BLAST | BLAST → Local BLAST | ① Query FASTA ② Database（或 FASTA 建 DB） ③ BLAST 程序（blastn/blastp/blastx/tblastn） | BLAST 结果表格/XML |
| Whole Genome BLAST | BLAST → Whole Genome BLAST | ① Query 基因组 FASTA ② Subject 基因组 FASTA | 全基因组比对结果 |
| Reciprocal BLAST | BLAST → Reciprocal BLAST | 两个物种的蛋白质序列 | 双向最佳匹配对 |
| BLAST Visualization | BLAST → BLAST Visualization | BLAST 结果 + 基因组坐标 | 比对可视化图 |
| Fq BLAST | BLAST → Fq BLAST | FASTQ 文件 + 数据库 | BLAST 结果 |

> **注意**：使用 BLAST 功能需先安装 NCBI BLAST+ 并将 bin 目录添加到系统 PATH 环境变量。

## 三、Graphics（可视化工具）

菜单路径：Main menubar → Graphics

### 3.1 HeatMap（热图）
- **菜单路径**：Graphics → HeatMap → Interactive HeatMap
- **输入**：表达量矩阵（Tab 分隔，行为基因，列为样本）
- **可选输入**：行注释文件、列注释文件、Newick 树文件
- **输出**：交互式热图，可导出 PNG/SVG/PDF
- **功能**：聚类分析（层次聚类/k-means）、颜色方案调整、注释轨道叠加

### 3.2 BioSequence Structure Illustrator（基因结构可视化）
- **菜单路径**：Graphics → BioSequence Structure Illustrator → Amazing Optional Gene Viewer
- **输入（均为可选）**：
  - Newick 树字符串或基因 ID 列表
  - MEME/MAST XML 结果文件（motif）
  - GFF/GTF 基因结构注释文件
  - 蛋白质坐标的 domain 信息（如 NCBI-CDD 结果）
  - mRNA 坐标的 domain 信息（如 miRNA 靶位点）
  - 基因重命名文件
- **输出**：同时展示系统发育树 + motif/domain 模式 + 基因结构 + miRNA 靶位点的综合图

### 3.3 Circos（共线性圈图）
- **菜单路径**：Graphics → Circos → SuperCircos
- **输入**：基因组 FASTA + GFF3 + 共线性区块数据
- **输出**：Circos 圈图，展示染色体、基因密度、共线性区域

### 3.4 Synteny Visualization（共线性可视化）
- **菜单路径**：Graphics → Synteny → Synteny Browser / Multiple Gff Viewer / Bloom Synteny
- **输入**：共线性区块文件（如 MCScanX 输出）+ GFF3
- **输出**：共线性区块可视化图

### 3.5 Venn Diagram（Venn 图）
- **菜单路径**：Graphics → Venn Diagram → Wonderful Venn
- **输入**：2~6 个基因/元素 ID 列表
- **输出**：交互式 Venn 图，可导出图片和交集列表

### 3.6 其他可视化工具
| 功能 | 菜单路径 | 说明 |
|------|----------|------|
| Volcano Plot | Graphics → Volcano Plot | 火山图（差异基因表达） |
| PCA Analysis | Graphics → PCA Analysis | 主成分分析图 |
| Dot Plot | Graphics → Dot Plot | 点阵图（序列比对可视化） |
| MSA Viewer | Graphics → MSA Viewer | 多序列比对可视化 |
| Motif Stack | Graphics → Motif Stack | Motif 堆叠图 |
| Gene Location | Graphics → Gene Location | 基因染色体位置图 |
| UpSet Plot | Graphics → UpSet Plot | UpSet 图（多集合交集） |
| qPCR Bar Plot | Graphics → qPCR Bar Plot | qPCR 柱状图 |
| Gel Image | Graphics → Gel Image | 凝胶电泳模拟图 |
| RNA-seq Viz | Graphics → RNA-seq Viz | RNA-seq 数据可视化 |
| MicroGenomeViz | Graphics → MicroGenomeViz | 微基因组可视化 |
| Color Scheme Generator | Graphics → Color Scheme Generator | 颜色方案生成器 |

## 四、GO & KEGG 富集分析

### 4.1 GO Enrichment
- **菜单路径**：Main menubar → GO → GO Enrichment
- **输入**：
  - 目标基因 ID 列表
  - 背景基因 ID 列表（可选，默认全基因组）
  - GO 注释文件（TBtools 格式或标准 GAF）
- **输出**：GO 富集结果表格（含 p-value、FDR）、GO 有向无环图（DAG）

### 4.2 KEGG Enrichment
- **菜单路径**：Main menubar → KEGG → KEGG Enrichment
- **输入**：
  - 目标基因 ID 列表
  - KEGG 注释文件
- **输出**：KEGG 富集结果表格、KEGG 通路图（标注差异基因）

### 4.3 KEGG Pathway Map
- **菜单路径**：Main menubar → KEGG → KEGG PathMap
- **输入**：基因 ID + KEGG 注释
- **输出**：标注了目标基因的 KEGG 通路图

## 五、NGS 数据分析

菜单路径：Main menubar → NGS → ...

| 功能 | 菜单路径 | 输入 | 输出 |
|------|----------|------|------|
| BWA-MEM2 Wrapper | NGS → BWA-MEM2 → BWA-MEM2 | ① 参考基因组 FASTA ② FASTQ（R1/R2） | SAM/BAM 文件 |
| SAM/BAM Tools | NGS → SAM/BAM Tools | SAM/BAM 文件 | 排序/索引/统计结果 |
| VCF Tools | NGS → VCF Tools | VCF 文件 | 过滤/统计结果 |
| SRA Download | NGS → SRA Tools → SRA Download | SRA accession 号 | SRA/FASTQ 文件 |
| RNA-seq Count | NGS → RNA-seq → Expression Level Calculator | BAM + GFF3 | 基因表达量矩阵 |

## 六、Comparative Genomics（比较基因组学）

菜单路径：Main menubar → Comparative Genomics

| 功能 | 菜单路径 | 输入 | 输出 |
|------|----------|------|------|
| MCScanX | Comparative Genomics → MCScanX | ① BLAST 结果 ② GFF3 文件 | 共线性区块（collinearity 文件）|
| Ka/Ks Calculator | Comparative Genomics → Ka/Ks | ① CDS 序列对 ② 对应的比对结果 | Ka/Ks 值表格 |
| Gene Family Cluster | Comparative Genomics → Gene Family Cluster | 多物种蛋白质序列 | 基因家族聚类结果 |

## 七、MEME Motif 分析

菜单路径：Main menubar → MEME

| 功能 | 菜单路径 | 输入 | 输出 |
|------|----------|------|------|
| MEME Wrapper | MEME → MEME Suite Wrapper | 蛋白质/DNA 序列 FASTA | MEME XML 结果 |
| Motif Draw | MEME → Draw Motif Pattern | MEME XML 文件 | Motif logo 图 |
| Motif + Gene Structure | MEME → Gene Structure | MEME XML + GFF3 | Motif + 基因结构组合图 |

## 八、NCBI 数据下载

菜单路径：Main menubar → NCBI

| 功能 | 菜单路径 | 输入 | 输出 |
|------|----------|------|------|
| NCBI Sequence Download | NCBI → Download Sequences | NCBI accession 号列表 | FASTA/GFF3 文件 |
| NCBI Taxonomy | NCBI → Taxonomy | 物种名/TaxID | 分类信息 |
| PubMed Search | NCBI → PubMed | 关键词 | 文献列表 |

## 九、Table Manipulation（表格操作）

菜单路径：Main menubar → Table Manipulator

| 功能 | 说明 |
|------|------|
| 表格合并 | 按公共列合并多个表格 |
| 表格拆分 | 按列值拆分表格 |
| 表格过滤 | 按条件筛选行/列 |
| 表格转置 | 行列转置 |
| 表格计算 | 数值列计算（求和、均值等） |

## 十、miRNA 分析

菜单路径：Main menubar → miRNA

| 功能 | 说明 |
|------|------|
| miRNA Target Prediction | 预测 miRNA 靶基因 |
| miRNA Coverage Plot | miRNA 覆盖度图 |
| miRBase Parser | 解析 miRbase 数据 |

## 十一、其他工具

| 功能 | 菜单路径 | 说明 |
|------|----------|------|
| RNAfold | RNA Tools → RNAfold | RNA 二级结构预测 |
| Population Genetics | Graphics → Population Genetics | 群体遗传学分析可视化 |
| GWAS | Main menubar → GWAS | 全基因组关联分析可视化 |
| Published Plant Genome | Main menubar → Published Plant Genome | 已发表植物基因组信息查询 |
| eRace/Genome Walking | Main menubar → eRace | 基因组步移 |
| Repeat Score Compute | Main menubar → Repeat | 重复序列评分 |
| SSH Tool | Main menubar → SSH | SSH 远程连接工具 |

## 十二、插件系统

TBtools 支持插件扩展，插件开发详见：
- 菜单路径：Main menubar → Plugin
- 插件开发文档：语雀 Cookbook → TBtools 插件开发
- 插件可扩展 TBtools 功能，支持 Java 编写