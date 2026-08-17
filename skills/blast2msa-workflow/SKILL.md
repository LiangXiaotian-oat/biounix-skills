---
name: blast2msa-workflow
description: BLAST 提取 + 方向校正 + MUSCLE 多序列比对的标准化流程。当用户需要将查询序列 BLAST 到多个目标基因组、提取最佳命中、校正序列方向并做多序列比对时使用。涉及 select_directory/select_file 弹窗选择路径、select_option 选择参数，然后调用 Python 脚本执行 BLAST、提取和比对。
triggers:
  - BLAST
  - MUSCLE
  - 多序列比对
  - MSA
  - multiple sequence alignment
  - BLAST提取
  - 序列比对
  - blast2msa
  - 方向校正
  - 多基因组序列提取并比对
  - orientation fix
always_active: false
version: null
category: other
author: GLM-5.2 + BioUnix
---
Cross-platform pipeline: BLAST query sequences against multiple target genomes → extract best hits → fix orientation → MUSCLE multiple sequence alignment.

## Prerequisites
- BLAST+ installed and in PATH (`makeblastdb`, `blastn`)
- MUSCLE installed and in PATH
- Python 3 with Biopython

## Steps

1. **Select working directory** — Use `select_directory` to let user choose an output folder. All intermediate and final files go here.

2. **Select query sequences** — Use `select_file` for the query FASTA file.

3. **Select target genomes** — Use `select_file` (multiple) or `select_directory` for target genome FASTA files.

4. **Choose parameters via `select_option`:**
   - E-value threshold (default 1e-5)
   - Identity threshold (default 70%)
   - Coverage threshold (default 50%)
   - Number of threads

5. **Build BLAST databases** — For each target genome, run `makeblastdb` to create local databases.

6. **Run BLAST** — Execute `blastn` with chosen parameters against all target databases. Use `scripts/blast2msa_pipeline.py` to orchestrate the full pipeline.

7. **Extract best hits** — Run `scripts/blast_best_extract.py` to parse BLAST results and extract the best hit per query per target, applying identity/coverage filters.

8. **Fix orientation** — Run `scripts/fix_orientation.py` to check and correct sequence orientation based on BLAST hit strand information, ensuring all sequences are on the same strand.

9. **Run MUSCLE MSA** — Feed the extracted, orientation-corrected sequences into MUSCLE for multiple sequence alignment.

10. **Report results** — Summarize: number of queries, hits found per target, alignment length, and output file paths.

## When to use
- User wants to BLAST query sequences against multiple genomes and build an MSA from the hits.
- User mentions BLAST + MUSCLE / MSA in the same request.
- User needs orientation correction before alignment (common with BLAST hits from both strands).

## Notes
- The three Python scripts (`blast2msa_pipeline.py`, `blast_best_extract.py`, `fix_orientation.py`) should be in `scripts/` under the skill directory.
- On Windows, ensure BLAST+ and MUSCLE are accessible via PATH or provide full paths.
- For large genomes, `makeblastdb` can take significant time; warn the user.