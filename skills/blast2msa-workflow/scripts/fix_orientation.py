#!/usr/bin/env python3
"""
fix_orientation.py — 基于 k-mer 频率的序列方向校正工具

原理:
  1. 从所有输入序列中统计 k-mer 频率，构建"共识方向"特征
  2. 对每条序列，比较其正链与反链互补链的 k-mer 频率分布相似度
  3. 将序列校正到与共识方向一致的方向

使用余弦相似度 (cosine similarity) 衡量 k-mer 频率分布的相似程度。
纯 Python 实现，不依赖任何外部工具。
"""

import argparse
import sys
from pathlib import Path
from collections import Counter
import math

COMPLEMENT = str.maketrans("ACGTNacgtn", "TGCANtgcan")


def reverse_complement(seq):
    return seq.translate(COMPLEMENT)[::-1]


def extract_kmers(seq, k):
    seq = seq.upper()
    return [seq[i:i+k] for i in range(len(seq)-k+1) if 'N' not in seq[i:i+k]]


def kmer_counter(seq, k):
    return Counter(extract_kmers(seq, k))


def cosine_similarity(a, b):
    all_kmers = set(a.keys()) | set(b.keys())
    if not all_kmers:
        return 0.0
    dot = sum(a.get(km, 0) * b.get(km, 0) for km in all_kmers)
    na = math.sqrt(sum(v*v for v in a.values()))
    nb = math.sqrt(sum(v*v for v in b.values()))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def parse_fasta(path):
    records = []
    cur_id = cur_hdr = None
    cur_seq = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('>'):
                if cur_id is not None:
                    records.append((cur_id, cur_hdr, ''.join(cur_seq)))
                cur_hdr = line[1:]
                cur_id = line[1:].split()[0]
                cur_seq = []
            else:
                cur_seq.append(line)
    if cur_id is not None:
        records.append((cur_id, cur_hdr, ''.join(cur_seq)))
    return records


def write_fasta(records, out_path, width=70):
    with open(out_path, 'w') as f:
        for sid, hdr, seq in records:
            f.write(f">{hdr}\n")
            for i in range(0, len(seq), width):
                f.write(seq[i:i+width] + '\n')


def fix_orientations(records, k):
    print(f"[INFO] 构建全局 k-mer (k={k}) 频率统计...")
    global_kmers = Counter()
    for _, _, seq in records:
        global_kmers.update(extract_kmers(seq.upper(), k))
    print(f"[INFO] 全局 k-mer 种类数: {len(global_kmers)}")
    fixed_records = []
    flipped = 0
    for sid, hdr, seq in records:
        s = seq.upper()
        fwd = kmer_counter(s, k)
        rev = kmer_counter(reverse_complement(s), k)
        fwd_sim = cosine_similarity(fwd, global_kmers)
        rev_sim = cosine_similarity(rev, global_kmers)
        if rev_sim > fwd_sim:
            fixed_seq = reverse_complement(s)
            flipped += 1
            print(f"  [FLIP] {sid}: fwd={fwd_sim:.4f} < rev={rev_sim:.4f}")
        else:
            fixed_seq = s
        fixed_records.append((sid, hdr, fixed_seq))
    print(f"[INFO] 方向校正完成: {flipped}/{len(records)} 条被翻转")
    return fixed_records


def main():
    parser = argparse.ArgumentParser(description="k-mer 频率方向校正")
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--kmer", type=int, default=20)
    args = parser.parse_args()
    if not Path(args.input).exists():
        print(f"[ERROR] 输入文件不存在: {args.input}", file=sys.stderr)
        sys.exit(1)
    records = parse_fasta(args.input)
    print(f"[INFO] 序列数: {len(records)}")
    if len(records) < 2:
        print("[WARN] 序列数不足 2 条，直接输出")
        write_fasta(records, args.output)
        sys.exit(0)
    fixed = fix_orientations(records, args.kmer)
    write_fasta(fixed, args.output)
    print(f"[DONE] 校正后序列: {args.output}")


if __name__ == "__main__":
    main()
