#!/usr/bin/env python3
"""
run_blast2msa.py — BLAST→提取→方向校正→MUSCLE 多序列比对（通用版）
- 自动检测 conda 并通过 conda run --no-capture-output -n <env> 调用 BLAST/MUSCLE
- 不硬编码任何服务器路径，适用于任意 conda 环境
- 默认输出 MSF 格式，支持 fasta/clw/html
- 从 BLAST outfmt 6 sseq 字段直接提取比对序列（13列，sseq 在 fields[12]）
- 支持并发比对多个基因组，断点续跑
"""

import argparse
import os
import shutil
import subprocess
import sys
import glob
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed


def detect_conda_prefix(conda_env):
    """自动检测 conda 路径并构建调用前缀。优先用 which conda，找不到则报错。"""
    conda_bin = shutil.which("conda")
    if conda_bin:
        return [conda_bin, "run", "--no-capture-output", "-n", conda_env]

    # 常见 conda 安装路径兜底
    candidates = [
        os.path.expanduser("~/miniconda3/bin/conda"),
        os.path.expanduser("~/anaconda3/bin/conda"),
        "/soft/miniconda3/bin/conda",
        "/opt/conda/bin/conda",
    ]
    for c in candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return [c, "run", "--no-capture-output", "-n", conda_env]

    print(f"[ERROR] 未找到 conda 可执行文件。请确保 conda 在 PATH 中，或通过 --conda-bin 指定路径。", file=sys.stderr)
    sys.exit(1)


def run_cmd(cmd, timeout=7200):
    """执行命令，返回 (stdout, success)"""
    print(f"  [CMD] {' '.join(str(c) for c in cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            print(f"  [ERROR] {result.stderr[:500]}", file=sys.stderr)
        return result.stdout, result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"  [ERROR] 超时", file=sys.stderr)
        return "", False


def find_genomes(genome_dir):
    """查找目录下所有 *_genome.fasta 文件"""
    pattern = os.path.join(genome_dir, "*_genome.fasta")
    return sorted(glob.glob(pattern))


def blast_single_genome(query, db_fasta, outdir, threads, prefix, conda_prefix):
    """对单个基因组执行 blastn，提取最佳命中。"""
    blast_out = os.path.join(outdir, f"{prefix}_blast.tsv")

    # 断点续跑
    if os.path.exists(blast_out) and os.path.getsize(blast_out) > 0:
        print(f"  [SKIP] {prefix} 已有结果，跳过")
        return prefix, True, blast_out

    cmd = conda_prefix + [
        "blastn",
        "-query", query,
        "-db", db_fasta,
        "-outfmt", "6 qseqid sseqid pident length mismatch gapopen qstart qend sstart send evalue bitscore sseq",
        "-num_threads", str(threads),
        "-evalue", "1e-5",
        "-max_target_seqs", "50",
        "-out", blast_out
    ]
    _, success = run_cmd(cmd, timeout=7200)
    return prefix, success, blast_out


def extract_best_hits(blast_tsv_list, outdir):
    """从多个 BLAST TSV 中提取每个基因组最佳命中，合并 FASTA。"""
    all_seqs = []
    hit_summary = []

    for tsv_path in sorted(blast_tsv_list):
        genome_name = Path(tsv_path).stem.replace("_blast.tsv", "")
        best_hit = None
        best_bitscore = -1

        if not os.path.exists(tsv_path) or os.path.getsize(tsv_path) == 0:
            print(f"  [WARN] {genome_name}: 无 BLAST 结果")
            hit_summary.append((genome_name, "no hit", 0, 0))
            continue

        with open(tsv_path, 'r') as f:
            for line in f:
                fields = line.strip().split('\t')
                if len(fields) < 13:
                    continue
                bitscore = float(fields[11])
                sseq = fields[12]
                pident = float(fields[2])
                length = int(fields[3])
                if bitscore > best_bitscore:
                    best_bitscore = bitscore
                    best_hit = (fields[1], sseq, pident, length, bitscore)

        if best_hit:
            sseqid, sseq, pident, length, bitscore = best_hit
            seq_id = f"{genome_name}|{sseqid}|pid{pident:.1f}|len{length}"
            all_seqs.append((seq_id, sseq))
            hit_summary.append((genome_name, sseqid, pident, length))
            print(f"  [HIT] {genome_name}: {sseqid} pid={pident:.1f}% len={length}")
        else:
            hit_summary.append((genome_name, "no hit", 0, 0))

    out_fasta = os.path.join(outdir, "all_extracted_seqs.fasta")
    with open(out_fasta, 'w') as fout:
        for seq_id, seq in all_seqs:
            fout.write(f">{seq_id}\n")
            for i in range(0, len(seq), 70):
                fout.write(seq[i:i + 70] + '\n')

    summary_file = os.path.join(outdir, "blast_summary.tsv")
    with open(summary_file, 'w') as fout:
        fout.write("genome\tsseqid\tpident\tlength\n")
        for genome, sseqid, pident, length in hit_summary:
            fout.write(f"{genome}\t{sseqid}\t{pident:.1f}\t{length}\n")

    print(f"\n[INFO] 提取完成: {len(all_seqs)} 条序列 -> {out_fasta}")
    print(f"[INFO] 汇总表: {summary_file}")
    return out_fasta, len(all_seqs)


def fix_orientation(input_fasta, output_fasta):
    """调用同目录下 fix_orientation.py 进行方向校正"""
    script_dir = Path(__file__).resolve().parent
    orient_script = os.path.join(script_dir, "fix_orientation.py")
    if not os.path.exists(orient_script):
        print(f"[ERROR] 找不到 fix_orientation.py: {orient_script}", file=sys.stderr)
        return False
    cmd = [sys.executable, orient_script, input_fasta, output_fasta, "--kmer", "20"]
    _, success = run_cmd(cmd)
    return success


def build_muscle_cmd(conda_prefix, input_fasta, output_aln, fmt):
    """构建 MUSCLE v3 命令（支持 fasta/msf/clw/html 格式）"""
    cmd = conda_prefix + ["muscle", "-in", input_fasta, "-out", output_aln]
    if fmt == "msf":
        cmd.append("-msf")
    elif fmt == "clw":
        cmd.append("-clw")
    elif fmt == "html":
        cmd.append("-html")
    return cmd


def main():
    parser = argparse.ArgumentParser(
        description="BLAST→提取→方向校正→MUSCLE 多序列比对流程"
    )
    parser.add_argument("-q", "--query", required=True, help="查询序列 FASTA")
    parser.add_argument("-d", "--genome-dir", required=True, help="基因组 FASTA 目录")
    parser.add_argument("-o", "--outdir", default="blast2msa_result", help="输出目录")
    parser.add_argument("-f", "--format", default="msf",
                        choices=["fasta", "msf", "clw", "html"],
                        help="MUSCLE 输出格式 (默认: msf)")
    parser.add_argument("-t", "--threads", type=int, default=4,
                        help="每个 BLAST 线程数 (默认: 4)")
    parser.add_argument("-j", "--jobs", type=int, default=4,
                        help="并发基因组数 (默认: 4)")
    parser.add_argument("--conda-env", default="bwa",
                        help="conda 环境名 (默认: bwa)")
    parser.add_argument("--conda-bin", default=None,
                        help="conda 可执行文件路径 (默认: 自动检测)")
    args = parser.parse_args()

    start_time = time.time()
    os.makedirs(args.outdir, exist_ok=True)

    # 检测 conda
    if args.conda_bin:
        conda_prefix = [args.conda_bin, "run", "--no-capture-output", "-n", args.conda_env]
    else:
        conda_prefix = detect_conda_prefix(args.conda_env)
    print(f"[INFO] conda 调用前缀: {' '.join(conda_prefix)}")

    # Step 0: 查找基因组
    print("=" * 60)
    print("[Step 0] 扫描目标基因组")
    print("=" * 60)
    genomes = find_genomes(args.genome_dir)
    print(f"[INFO] 找到 {len(genomes)} 个基因组")
    if not genomes:
        print("[ERROR] 未找到基因组文件")
        sys.exit(1)

    # Step 1: 并发 BLAST
    print("\n" + "=" * 60)
    print(f"[Step 1] 并发 BLAST ({len(genomes)} 基因组, 并发 {args.jobs})")
    print("=" * 60)

    blast_tsvs = []
    completed = 0
    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        future_to_genome = {}
        for gf in genomes:
            gname = Path(gf).stem.replace("_genome", "")
            future = executor.submit(blast_single_genome, args.query, gf,
                                     args.outdir, args.threads, gname, conda_prefix)
            future_to_genome[future] = gname

        for future in as_completed(future_to_genome):
            gname = future_to_genome[future]
            try:
                prefix, success, blast_tsv = future.result()
                completed += 1
                if success:
                    blast_tsvs.append(blast_tsv)
                print(f"  [{completed}/{len(genomes)}] {gname}: {'OK' if success else 'FAIL'}")
            except Exception as e:
                print(f"  [ERROR] {gname}: {e}")
                completed += 1

    print(f"\n[INFO] BLAST 完成: {len(blast_tsvs)}/{len(genomes)} 成功")

    # Step 2: 提取最佳命中
    print("\n" + "=" * 60)
    print("[Step 2] 提取最佳命中序列")
    print("=" * 60)
    all_fasta, n_seqs = extract_best_hits(blast_tsvs, args.outdir)
    if n_seqs < 2:
        print("[ERROR] 提取序列不足 2 条，无法做 MSA")
        sys.exit(1)

    # Step 3: 方向校正
    print("\n" + "=" * 60)
    print("[Step 3] 序列方向校正 (k-mer 法)")
    print("=" * 60)
    oriented_fasta = os.path.join(args.outdir, "all_extracted_oriented.fasta")
    fix_orientation(all_fasta, oriented_fasta)
    if not os.path.exists(oriented_fasta):
        print("[ERROR] 方向校正失败")
        sys.exit(1)

    # Step 4: MUSCLE MSA
    print("\n" + "=" * 60)
    print(f"[Step 4] MUSCLE 多序列比对 (格式: {args.format})")
    print("=" * 60)
    ext = args.format
    aln_out = os.path.join(args.outdir, f"final_alignment_muscle.{ext}")

    muscle_cmd = build_muscle_cmd(conda_prefix, oriented_fasta, aln_out, args.format)
    _, muscle_ok = run_cmd(muscle_cmd, timeout=7200)

    if muscle_ok and os.path.exists(aln_out) and os.path.getsize(aln_out) > 0:
        elapsed = time.time() - start_time
        print("\n" + "=" * 60)
        print(f"[DONE] 流程完成！耗时 {elapsed:.0f} 秒 ({elapsed/60:.1f} 分钟)")
        print(f"  最终比对文件: {aln_out}")
        print(f"  序列数: {n_seqs}")
        print(f"  汇总表: {os.path.join(args.outdir, 'blast_summary.tsv')}")
        print("=" * 60)
    else:
        print("[ERROR] MUSCLE 比对失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
