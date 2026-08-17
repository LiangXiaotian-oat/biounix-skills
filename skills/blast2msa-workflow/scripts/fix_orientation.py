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


# ---------------------------------------------------------------------------
# DNA 序列操作
# ---------------------------------------------------------------------------

COMPLEMENT = str.maketrans("ACGTNacgtn", "TGCANtgcan")


def reverse_complement(seq):
    """返回反向互补链"""
    return seq.translate(COMPLEMENT)[::-1]


def extract_kmers(seq, k):
    """提取序列中所有 k-mer（跳过含 N 的 k-mer）"""
    kmers = []
    seq = seq.upper()
    for i in range(len(seq) - k + 1):
        kmer = seq[i:i + k]
        if 'N' not in kmer:
            kmers.append(kmer)
    return kmers


def kmer_counter(seq, k):
    """返回序列的 k-mer 频率 Counter"""
    return Counter(extract_kmers(seq, k))


# ---------------------------------------------------------------------------
# 相似度计算
# ---------------------------------------------------------------------------

def cosine_similarity(counter_a, counter_b):
    """计算两个 k-mer 频率 Counter 的余弦相似度"""
    # 获取所有 k-mer 的并集
    all_kmers = set(counter_a.keys()) | set(counter_b.keys())
    if not all_kmers:
        return 0.0
    dot_product = sum(counter_a.get(km, 0) * counter_b.get(km, 0) for km in all_kmers)
    norm_a = math.sqrt(sum(v * v for v in counter_a.values()))
    norm_b = math.sqrt(sum(v * v for v in counter_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


# ---------------------------------------------------------------------------
# FASTA 解析与写出
# ---------------------------------------------------------------------------

def parse_fasta(fasta_path):
    """解析 FASTA，返回 [(id, header, seq), ...] 列表"""
    records = []
    current_id = None
    current_header = None
    current_seq = []
    with open(fasta_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('>'):
                if current_id is not None:
                    records.append((current_id, current_header, ''.join(current_seq)))
                current_header = line[1:]
                current_id = line[1:].split()[0]
                current_seq = []
            else:
                current_seq.append(line)
    if current_id is not None:
        records.append((current_id, current_header, ''.join(current_seq)))
    return records


def write_fasta(records, out_path, line_width=70):
    """写出 FASTA 文件"""
    with open(out_path, 'w') as f:
        for seq_id, header, seq in records:
            f.write(f">{header}\n")
            for i in range(0, len(seq), line_width):
                f.write(seq[i:i + line_width] + '\n')


# ---------------------------------------------------------------------------
# 核心逻辑
# ---------------------------------------------------------------------------

def fix_orientations(records, k):
    """
    对每条序列进行方向校正。
    策略:
      1. 构建全局 k-mer 频率（所有序列正链合并）作为"共识方向"
      2. 对每条序列，分别计算正链/反链与共识的余弦相似度
      3. 选择相似度更高的方向
    """
    # 构建全局共识 k-mer 频率
    print(f"[INFO] 构建全局 k-mer (k={k}) 频率统计...")
    global_kmers = Counter()
    for _, _, seq in records:
        global_kmers.update(extract_kmers(seq.upper(), k))
    print(f"[INFO] 全局 k-mer 种类数: {len(global_kmers)}")

    # 逐条校正
    fixed_records = []
    flipped_count = 0
    for seq_id, header, seq in records:
        seq_upper = seq.upper()
        fwd_kmers = kmer_counter(seq_upper, k)
        rev_seq = reverse_complement(seq_upper)
        rev_kmers = kmer_counter(rev_seq, k)

        fwd_sim = cosine_similarity(fwd_kmers, global_kmers)
        rev_sim = cosine_similarity(rev_kmers, global_kmers)

        if rev_sim > fwd_sim:
            # 反链更接近共识方向，翻转
            fixed_seq = rev_seq
            flipped_count += 1
            print(f"  [FLIP] {seq_id}: fwd_sim={fwd_sim:.4f} < rev_sim={rev_sim:.4f}")
        else:
            fixed_seq = seq_upper
            if fwd_sim == rev_sim and fwd_sim == 0:
                print(f"  [WARN] {seq_id}: 无法确定方向 (sim=0)，保持正链")

        fixed_records.append((seq_id, header, fixed_seq))

    print(f"[INFO] 方向校正完成: {flipped_count}/{len(records)} 条序列被翻转")
    return fixed_records


def main():
    parser = argparse.ArgumentParser(
        description="基于 k-mer 频率的序列方向校正工具"
    )
    parser.add_argument("input", help="输入 FASTA 文件")
    parser.add_argument("output", help="输出 FASTA 文件")
    parser.add_argument("--kmer", type=int, default=20,
                        help="k-mer 长度 (默认: 20)")
    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"[ERROR] 输入文件不存在: {args.input}", file=sys.stderr)
        sys.exit(1)

    # 读取序列
    print(f"[INFO] 读取序列: {args.input}")
    records = parse_fasta(args.input)
    print(f"[INFO] 序列数: {len(records)}")

    if len(records) < 2:
        print("[WARN] 序列数不足 2 条，方向校正可能无意义，直接输出。")
        write_fasta(records, args.output)
        sys.exit(0)

    # 校正方向
    fixed = fix_orientations(records, args.kmer)

    # 写出
    write_fasta(fixed, args.output)
    print(f"[DONE] 校正后序列已写出: {args.output}")


if __name__ == "__main__":
    main()
