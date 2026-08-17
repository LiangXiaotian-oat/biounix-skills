#!/usr/bin/env python3
"""
blast_best_extract.py — BLAST 最佳匹配序列提取工具
对每条查询序列，从 BLAST 结果中提取最佳匹配的目标序列。

依赖: makeblastdb, blastn (NCBI BLAST+)
纯 Python 解析 FASTA，不依赖外部 sed/awk。
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from collections import defaultdict


def parse_fasta(fasta_path):
    """解析 FASTA 文件，返回 {seq_id: sequence} 字典"""
    seqs = {}
    current_id = None
    current_seq = []
    with open(fasta_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('>'):
                if current_id is not None:
                    seqs[current_id] = ''.join(current_seq)
                # 取 > 后第一个空格前的部分作为 ID
                current_id = line[1:].split()[0]
                current_seq = []
            else:
                current_seq.append(line)
    if current_id is not None:
        seqs[current_id] = ''.join(current_seq)
    return seqs


def make_blast_db(db_fasta):
    """如果 BLAST 库不存在则自动创建"""
    db_path = Path(db_fasta)
    ndb_file = db_path.with_suffix('.ndb')
    nhr_file = db_path.with_suffix('.nhr')
    if not ndb_file.exists() and not nhr_file.exists():
        print(f"[INFO] 正在建库: {db_path.name}")
        cmd = ["makeblastdb", "-in", str(db_path), "-dbtype", "nucl", "-parse_seqids"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[ERROR] 建库失败: {result.stderr}", file=sys.stderr)
            sys.exit(1)


def run_blast(query, db_fasta, threads, outdir, prefix):
    """执行 blastn，返回 outfmt 6 结果文件路径"""
    blast_out = Path(outdir) / f"{prefix}_blast.tsv"
    cmd = [
        "blastn",
        "-query", query,
        "-db", str(db_fasta),
        "-outfmt", "6",
        "-num_threads", str(threads),
        "-evalue", "1e-5",
        "-max_target_seqs", "50",
        "-out", str(blast_out)
    ]
    print(f"[CMD] {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] BLAST 失败: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return blast_out


def extract_best_matches(blast_tsv, target_seqs, outdir, prefix):
    """
    从 BLAST outfmt 6 结果中提取每个 query 的最佳匹配序列。
    outfmt 6 列: qseqid sseqid pident length mismatch gapopen
                  qstart qend sstart send evalue bitscore
    """
    best_hits = {}  # qseqid -> (sseqid, bitscore, evalue)
    with open(blast_tsv, 'r') as f:
        for line in f:
            fields = line.strip().split('\t')
            if len(fields) < 12:
                continue
            qseqid = fields[0]
            sseqid = fields[1]
            evalue = float(fields[10])
            bitscore = float(fields[11])
            if qseqid not in best_hits:
                best_hits[qseqid] = (sseqid, bitscore, evalue)
            else:
                # 保留 bitscore 最高的
                if bitscore > best_hits[qseqid][1]:
                    best_hits[qseqid] = (sseqid, bitscore, evalue)

    # 写出最佳匹配序列
    out_file = Path(outdir) / f"{prefix}_best_match.fasta"
    extracted_count = 0
    with open(out_file, 'w') as fout:
        for qseqid, (sseqid, bitscore, evalue) in best_hits.items():
            # 尝试精确匹配 sseqid，否则尝试去版本号匹配
            if sseqid in target_seqs:
                seq = target_seqs[sseqid]
            else:
                # 尝试匹配 sseqid 的前缀（BLAST parse_seqids 可能截断）
                matched = False
                for tid, tseq in target_seqs.items():
                    if tid == sseqid or tid.startswith(sseqid) or sseqid.startswith(tid):
                        seq = tseq
                        matched = True
                        break
                if not matched:
                    print(f"[WARN] 未找到目标序列: {sseqid}，跳过。")
                    continue
            fout.write(f">{sseqid}\n")
            # 每行 70 个字符
            for i in range(0, len(seq), 70):
                fout.write(seq[i:i+70] + '\n')
            extracted_count += 1

    print(f"[INFO] 提取完成: {extracted_count} 条最佳匹配序列 -> {out_file}")
    return out_file


def main():
    parser = argparse.ArgumentParser(
        description="BLAST 最佳匹配序列提取工具"
    )
    parser.add_argument("-q", "--query", required=True, help="查询序列 FASTA")
    parser.add_argument("-d", "--db", required=True, help="BLAST 数据库 FASTA")
    parser.add_argument("-r", "--ref", required=True,
                        help="参考序列 FASTA（用于提取匹配序列，通常与 -d 相同）")
    parser.add_argument("-o", "--outdir", default=".", help="输出目录")
    parser.add_argument("-t", "--threads", type=int, default=4,
                        help="BLAST 线程数 (默认: 4)")
    parser.add_argument("--keep-intermediate", action="store_true",
                        help="保留中间文件 (BLAST TSV 等)")
    parser.add_argument("--prefix", default="blast_result",
                        help="输出文件前缀 (默认: blast_result)")
    args = parser.parse_args()

    Path(args.outdir).mkdir(parents=True, exist_ok=True)

    # 1. 建库
    make_blast_db(args.db)

    # 2. 运行 BLAST
    blast_tsv = run_blast(args.query, args.db, args.threads, args.outdir, args.prefix)

    # 3. 解析参考序列
    print(f"[INFO] 解析参考序列: {args.ref}")
    target_seqs = parse_fasta(args.ref)
    print(f"[INFO] 参考序列数: {len(target_seqs)}")

    # 4. 提取最佳匹配
    extract_best_matches(blast_tsv, target_seqs, args.outdir, args.prefix)

    # 5. 清理中间文件
    if not args.keep_intermediate:
        blast_tsv.unlink(missing_ok=True)
        print(f"[INFO] 已清理中间文件: {blast_tsv}")


if __name__ == "__main__":
    main()
