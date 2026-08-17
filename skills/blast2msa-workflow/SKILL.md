---
name: blast2msa-workflow
description: BLAST 提取 + 方向校正 + MUSCLE 多序列比对的标准化流程。当用户需要将查询序列 BLAST 到多个目标基因组、提取最佳命中、校正序列方向并做多序列比对时使用。使用 conda 自动检测环境（不硬编码路径），默认输出 MSF 格式，MUSCLE 优先比对。涉及 select_directory/select_file 弹窗选择路径、select_option 选择参数，然后调用 run_blast2msa.py 执行全流程。
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
  - msf格式
  - conda blast
  - run_blast2msa
always_active: false
version: null
category: null
author: GLM-5.2 + BioUnix
---
Cross-platform pipeline: BLAST query sequences against multiple target genomes → extract best hits → fix orientation → MUSCLE multiple sequence alignment.

## Prerequisites
- conda environment with BLAST+ (`makeblastdb`, `blastn`) and MUSCLE v3 installed
- Python 3 (no extra packages required for the pipeline itself)
- The pipeline auto-detects conda via `which conda` and calls tools through `conda run --no-capture-output -n <env>`. No hardcoded paths.

## Steps

1. **Select working directory** — Use `select_directory` to let user choose an output folder. All intermediate and final files go here.

2. **Select query sequences** — Use `select_file` for the query FASTA file.

3. **Select target genomes directory** — Use `select_directory` for the folder containing target genome FASTA files (pattern: `*_genome.fasta`).

4. **Choose parameters via `select_option`:**
   - MUSCLE output format — default `msf`; alternatives: `fasta`, `clw`, `html`
   - Threads per BLAST task — default 4
   - Concurrent genome count — default 4
   - conda environment name — default `bwa`

5. **Run the pipeline** — Execute `scripts/run_blast2msa.py` with the chosen parameters. This single script orchestrates the entire workflow:
   - Scans target directory for `*_genome.fasta` files
   - Concurrent BLAST against all genomes (with resume support — skips completed TSVs)
   - Extracts best hits from BLAST outfmt 6 `sseq` field (13-column format, direct sequence extraction)
   - k-mer based orientation correction via `scripts/fix_orientation.py`
   - MUSCLE v3 multiple sequence alignment (MSF format by default)

   Example command:
   ```bash
   python scripts/run_blast2msa.py \
     -q <query.fasta> \
     -d <genome_dir> \
     -o <output_dir> \
     -f msf \
     -t 4 \
     -j 4 \
     --conda-env bwa
   ```

6. **Report results** — Summarize: number of genomes scanned, hits found, sequences in alignment, and output file paths. Key outputs:
   - `final_alignment_muscle.msf` — MUSCLE alignment (MSF format, default)
   - `blast_summary.tsv` — per-genome best hit summary (sseqid, pident, length)
   - `all_extracted_oriented.fasta` — orientation-corrected sequences

## When to use
- User wants to BLAST query sequences against multiple genomes and build an MSA from the hits.
- User mentions BLAST + MUSCLE / MSA in the same request.
- User needs orientation correction before alignment (common with BLAST hits from both strands).

## Notes
- The pipeline uses `run_blast2msa.py` as the sole orchestrator and `fix_orientation.py` for orientation correction. No other scripts are needed.
- conda is auto-detected; use `--conda-bin` to override the conda executable path if needed.
- MUSCLE v3 syntax is used (`-in`/`-out`/`-msf`). If MUSCLE v5 is installed, adjust the `build_muscle_cmd` function in the script.
- For large genomes, BLAST can take significant time; the pipeline supports resume by skipping non-empty existing BLAST TSV files.