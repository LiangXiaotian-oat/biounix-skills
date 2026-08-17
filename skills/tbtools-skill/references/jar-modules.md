# TBtools-II JAR 包模块结构

> 基于 TBtools_JRE1.6.jar（v2.515）反编译分析，共 6989 个 class

## 核心模块

### biocjava/bioDoer（核心功能实现）
- `BLAST/` — BLAST 比对引擎（含全基因组 BLAST、双向 BLAST、PPI 预测）
- `ComparativeGenomics/MCScanX/` — 共线性分析（MCScanX 实现 + 图形化）
- `Fasta/` — FASTA 序列处理（SequenceZone + Tools）
- `Fastq/` — FASTQ 处理（FastqCollapser）
- `GXFUtils/` — GFF3/GTF 文件处理（含 GXFfixer）
- `GeneOntology/` — GO 分析（注释 + 图形化 + 小工具）
- `Kegg/` — KEGG 分析（富集分析 + 通路图）
- `MEME/` — Motif 分析（绘制 + 序列提取 + 基因结构）
- `NCBI/` — NCBI 数据下载（含 Taxonomy）
- `NGSDataAnalysis/BwaMem2/` — NGS 比对（BWA-MEM2 封装）
- `ExpressionLevelCalculator/` — 表达量计算
- `JIGplotToolkit/` — 可视化工具集（见下文）
- `miRNA/` — miRNA 分析
- `SSH/` — SSH 远程工具
- `GWAS/` — GWAS 可视化
- `eRaceOrGenomeWalking/` — 基因组步移

### biocjava/bioDoer/JIGplotToolkit（可视化引擎）
- `Circos/SuperCircos/` — Circos 圈图
- `HeatMap/` — 热图引擎
- `Synteny/` — 共线性可视化（BloomSynteny, SyntenyBrowser, MultipleGffViewer）
- `DotPlot/` — 点阵图
- `MSA/` — 多序列比对可视化
- `VocanoPlot/` — 火山图
- `PCAanalysis/` — PCA 分析
- `UpSetPloter/` — UpSet 图
- `RNAseqViz/` — RNA-seq 可视化
- `MicroGenomeViz/` — 微基因组可视化
- `MotifStack/` — Motif 堆叠图
- `GelImage/` — 凝胶图像
- `GeneLocation/` — 基因位置图
- `ColorSchemeGenerator/` — 颜色方案生成器
- `PopulationGenetics/` — 群体遗传学
- `newickParser/` — Newick 树解析（含 PhyloTreeUtils, TreePileUp, TreeTreeTree）
- `BlastVisulization/` — BLAST 结果可视化
- `EnrichmentAnalysisGraph/` — 富集分析图形化
- `qPCRBarPlot/` — qPCR 柱状图
- `miRCoverage/` — miRNA 覆盖度
- `Paf/` — PAF 格式处理
- `MACS2viz/` — MACS2 结果可视化
- `Hclust/` — 层次聚类
- `Dist/` — 距离计算
- `Funny/` + `Game/` — 趣味功能（贪吃蛇、俄罗斯方块等彩蛋）

### biocjava/bioIO（文件 I/O 引擎）
- `FastX/FastaIndex/` — FASTA 索引与随机访问
- `GFF/` + `GTF/` + `GXF/` — 基因结构注释解析
- `HTSData/SAMBAM/` — SAM/BAM 文件处理
- `HTSData/VCF/` — VCF 变异文件处理
- `BlastXml/` — BLAST XML 解析（含 PileupShower, ShowAlignment）
- `SeqFormatConvert/` — 序列格式转换（Clustal, Fasta, MEGA, Nexus, PAML, Phylip）
- `KaKs/` — Ka/Ks 计算
- `ORF/` — ORF 预测
- `Primer/` — 引物设计
- `RNAfold/` — RNA 二级结构
- `SRAtools/` — SRA 工具
- `miRbase/` — miRbase 数据解析
- `GeneOntology/EnrichMent/` — GO 富集计算引擎
- `Ab1Parser/` — Sanger 测序 ab1 文件解析
- `TrimMSA/` — MSA 修剪
- `Embl/` + `GBff/` — EMBL/GenBank 格式解析
- `Region/` — 区域处理
- `ScreenShot/` — 截图工具

### biocjava/bioWeb（网络工具）
- `EntrezUtils/` — NCBI Entrez 查询
- `NCBITaxonomy/` — NCBI 分类学
- `Pubmed/` — PubMed 文献搜索
- `APGIV/` — APG IV 分类系统
- `PoreWalker/` — 孔道预测
- `TMSprediction/` — 跨膜区预测

### biocjava/GUIexcutors（GUI 执行器）
- `Blast/` — BLAST GUI
- `CommonTools/` — 通用工具 GUI
- `FastaExtractor/` — 序列提取 GUI
- `Gff3GUI/` — GFF3 操作 GUI
- `GoAnanlysis/` — GO 分析 GUI
- `HTSDataGUI/` — NGS 数据 GUI
- `KeggAnalysis/` — KEGG 分析 GUI
- `MEMEGUI/` — MEME 分析 GUI
- `NCBIdownLoadSeqGUI/` — NCBI 下载 GUI
- `RNAfoldGUI/` — RNAfold GUI
- `SRAtoolsGUI/` — SRA 工具 GUI
- `TableManipulatorGUI/` — 表格操作 GUI
- `sRNAGUI/` — sRNA 分析 GUI
- `SuperHeatMapBrowser/` — 热图浏览器
- `LevelGrapherGUI/` — 层级图 GUI
- `BioFileViewer/` — 生物文件查看器
- `BioSoftPipeWrapper/` — 生物软件管道封装

### JJpolt2（绘图引擎）
- `Clustering/` — 聚类算法（距离计算、层次聚类、k-means、系统发育树）
- `dataframe/` — 数据帧处理
- `Object/` + `Setting/` — 图形对象与设置
- `Tools/` — 绘图工具

### toolsKit（工具包）
- `DataStructure/DataFrame/` — 数据结构（DataFrame、WonderfulTree）
- `FileReader/` — 文件读取器
- `GUItools/` — GUI 工具

### 第三方库
- `jsat/` — Java Statistical Analysis Tool (ML 库，用于聚类/分类)
- `org/apache/` — Apache HTTP/ Commons 网络库
- `org/jdom/` — XML 解析
- `org/jfree/` — SVG 图形输出
- `org/xerial/snappy/` — Snappy 压缩