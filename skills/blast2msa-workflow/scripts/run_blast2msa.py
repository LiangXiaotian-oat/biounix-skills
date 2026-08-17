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
    """自动检测 conda 路径并构建调用前缀。"""
    conda_bin = shutil.which("conda")
    if conda_bin:
        return [conda_bin, "run", "--no-capture-output", "-n", conda_env]
    candidates = [
        os.path.expanduser("~/miniconda3/bin/conda"),
        os.path.expanduser("~/anaconda3/bin/conda"),
        "/soft/miniconda3/bin/conda",
        "/opt/conda/bin/conda",
    ]
    for c in candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return [c, "run", "--no-capture-output", "-n", conda_env]
    print("[ERROR] 未找到 conda，请确保在 PATH 中或用 --conda-bin 指定", file=sys.stderr)
    sys.exit(1)


def run_cmd(cmd, timeout=7200):
    print(f"  [CMD] {' '.join(str(c) for c in cmd)}")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if r.returncode != 0:
            print(f"  [ERROR] {r.stderr[:500]}", file=sys.stderr)
        return r.stdout, r.returncode == 0
    except subprocess.TimeoutExpired:
        print("  [ERROR] 超时", file=sys.stderr)
        return "", False


def find_genomes(genome_dir):
    return sorted(glob.glob(os.path.join(genome_dir, "*_genome.fasta")))


def blast_single(query, db_fasta, outdir, threads, prefix, conda_prefix):
    blast_out = os.path.join(outdir, f"{prefix}_blast.tsv")
    if os.path.exists(blast_out) and os.path.getsize(blast_out) > 0:
        print(f"  [SKIP] {prefix} 已有结果")
        return prefix, True, blast_out
    cmd = conda_prefix + ["blastn", "-query", query, "-db", db_fasta,
        "-outfmt", "6 qseqid sseqid pident length mismatch gapopen qstart qend sstart send evalue bitscore sseq",
        "-num_threads", str(threads), "-evalue", "1e-5", "-max_target_seqs", "50", "-out", blast_out]
    _, ok = run_cmd(cmd)
    return prefix, ok, blast_out


def extract_best_hits(blast_tsv_list, outdir):
    all_seqs, hit_summary = [], []
    for tsv in sorted(blast_tsv_list):
        gname = Path(tsv).stem.replace("_blast.tsv", "")
        best, best_bit = None, -1
        if not os.path.exists(tsv) or os.path.getsize(tsv) == 0:
            hit_summary.append((gname, "no hit", 0, 0)); continue
        with open(tsv) as f:
            for line in f:
                fields = line.strip().split('\t')
                if len(fields) < 13: continue
                bit = float(fields[11]); sseq = fields[12]
                if bit > best_bit:
                    best_bit = bit; best = (fields[1], sseq, float(fields[2]), int(fields[3]))
        if best:
            sid, sseq, pid, ln = best
            all_seqs.append((f"{gname}|{sid}|pid{pid:.1f}|len{ln}", sseq))
            hit_summary.append((gname, sid, pid, ln))
            print(f"  [HIT] {gname}: {sid} pid={pid:.1f}% len={ln}")
        else:
            hit_summary.append((gname, "no hit", 0, 0))
    out_fasta = os.path.join(outdir, "all_extracted_seqs.fasta")
    with open(out_fasta, 'w') as fout:
        for sid, seq in all_seqs:
            fout.write(f">{sid}\n")
            for i in range(0, len(seq), 70): fout.write(seq[i:i+70] + '\n')
    sf = os.path.join(outdir, "blast_summary.tsv")
    with open(sf, 'w') as fout:
        fout.write("genome\tsseqid\tpident\tlength\n")
        for g, s, p, l in hit_summary: fout.write(f"{g}\t{s}\t{p:.1f}\t{l}\n")
    print(f"\n[INFO] 提取完成: {len(all_seqs)} 条序列 -> {out_fasta}")
    return out_fasta, len(all_seqs)


def fix_orientation(input_fasta, output_fasta):
    sd = Path(__file__).resolve().parent
    script = os.path.join(sd, "fix_orientation.py")
    if not os.path.exists(script):
        print(f"[ERROR] 找不到 fix_orientation.py: {script}", file=sys.stderr)
        return False
    _, ok = run_cmd([sys.executable, script, input_fasta, output_fasta, "--kmer", "20"])
    return ok


def build_muscle_cmd(conda_prefix, input_fasta, output_aln, fmt):
    cmd = conda_prefix + ["muscle", "-in", input_fasta, "-out", output_aln]
    if fmt == "msf": cmd.append("-msf")
    elif fmt == "clw": cmd.append("-clw")
    elif fmt == "html": cmd.append("-html")
    return cmd


def main():
    parser = argparse.ArgumentParser(description="BLAST→提取→方向校正→MUSCLE MSA")
    parser.add_argument("-q", "--query", required=True)
    parser.add_argument("-d", "--genome-dir", required=True)
    parser.add_argument("-o", "--outdir", default="blast2msa_result")
    parser.add_argument("-f", "--format", default="msf", choices=["fasta", "msf", "clw", "html"])
    parser.add_argument("-t", "--threads", type=int, default=4)
    parser.add_argument("-j", "--jobs", type=int, default=4)
    parser.add_argument("--conda-env", default="bwa")
    parser.add_argument("--conda-bin", default=None)
    args = parser.parse_args()
    t0 = time.time(); os.makedirs(args.outdir, exist_ok=True)
    conda_prefix = [args.conda_bin, "run", "--no-capture-output", "-n", args.conda_env] if args.conda_bin else detect_conda_prefix(args.conda_env)
    print(f"[INFO] conda: {' '.join(conda_prefix)}")
    genomes = find_genomes(args.genome_dir)
    print(f"[INFO] 找到 {len(genomes)} 个基因组")
    if not genomes: sys.exit(1)
    # BLAST
    blast_tsvs = []; done = 0
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = {}
        for gf in genomes:
            gn = Path(gf).stem.replace("_genome", "")
            futs[ex.submit(blast_single, args.query, gf, args.outdir, args.threads, gn, conda_prefix)] = gn
        for fut in as_completed(futs):
            gn = futs[fut]; done += 1
            try:
                _, ok, tsv = fut.result()
                if ok: blast_tsvs.append(tsv)
                print(f"  [{done}/{len(genomes)}] {gn}: {'OK' if ok else 'FAIL'}")
            except Exception as e: print(f"  [ERROR] {gn}: {e}")
    # 提取
    all_fasta, n = extract_best_hits(blast_tsvs, args.outdir)
    if n < 2: print("[ERROR] 序列不足"); sys.exit(1)
    # 方向校正
    oriented = os.path.join(args.outdir, "all_extracted_oriented.fasta")
    fix_orientation(all_fasta, oriented)
    # MUSCLE
    aln = os.path.join(args.outdir, f"final_alignment_muscle.{args.format}")
    run_cmd(build_muscle_cmd(conda_prefix, oriented, aln, args.format))
    if os.path.exists(aln) and os.path.getsize(aln) > 0:
        print(f"\n[DONE] 耗时 {time.time()-t0:.0f}s | 序列数: {n} | 比对文件: {aln}")
    else: print("[ERROR] MUSCLE 失败"); sys.exit(1)

if __name__ == "__main__": main()
