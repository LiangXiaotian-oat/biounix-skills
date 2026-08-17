#!/usr/bin/env python3
"""
blast2msa_pipeline.py — 跨平台一键式 BLAST 提取 + 方向校正 + MUSCLE 比对
支持 Windows, Linux, macOS。使用 Python 原生多线程加速多库比对。
自动检测 MUSCLE v3 (-in) 与 v5 (-align) 命令行差异。
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed


# ---------------------------------------------------------------------------
# 通用工具
# ---------------------------------------------------------------------------

def run_cmd(cmd):
    """跨平台执行命令，返回 (stdout, success)"""
    print(f"\n[CMD] {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] {result.stderr}", file=sys.stderr)
    return result.stdout, result.returncode == 0


def check_dependencies():
    """检查必要的命令行工具是否安装"""
    deps = ["makeblastdb", "blastn", "muscle"]
    missing = []
    for dep in deps:
        check = subprocess.run(
            ["where" if os.name == "nt" else "which", dep],
            capture_output=True, text=True
        )
        if check.returncode != 0:
            missing.append(dep)
    if missing:
        print(f"[ERROR] 缺少必要的依赖工具: {', '.join(missing)}")
        print("请确保它们已安装并添加到系统 PATH 环境变量中。")
        sys.exit(1)
    # samtools 可选（部分流程用到）
    check_sam = subprocess.run(
        ["where" if os.name == "nt" else "which", "samtools"],
        capture_output=True, text=True
    )
    if check_sam.returncode != 0:
        print("[WARN] 未检测到 samtools，部分功能可能受限。")


def detect_muscle_version():
    """
    检测 MUSCLE 主版本号。
    v3.x: muscle -version 输出含 "3." 或 "MUSCLE v3"
    v5.x: muscle -version 输出含 "5." 或 "muscle5"
    返回: 3 或 5
    """
    try:
        result = subprocess.run(
            ["muscle", "-version"],
            capture_output=True, text=True, timeout=10
        )
        output = (result.stdout + result.stderr).lower()
        # v5 输出示例: "muscle 5.1.linux64"
        if re.search(r'(?:muscle\s+)?5\.', output):
            print("[INFO] 检测到 MUSCLE v5")
            return 5
        # v3 输出示例: "MUSCLE v3.8.31" 或 "3.8.31"
        if re.search(r'(?:muscle\s+)?3\.', output):
            print("[INFO] 检测到 MUSCLE v3")
            return 3
        # 某些版本用 --version
        result2 = subprocess.run(
            ["muscle", "--version"],
            capture_output=True, text=True, timeout=10
        )
        output2 = (result2.stdout + result2.stderr).lower()
        if re.search(r'5\.', output2):
            print("[INFO] 检测到 MUSCLE v5")
            return 5
        if re.search(r'3\.', output2):
            print("[INFO] 检测到 MUSCLE v3")
            return 3
    except Exception as e:
        print(f"[WARN] 无法检测 MUSCLE 版本: {e}")
    # 默认用 v3 语法
    print("[WARN] 无法确定 MUSCLE 版本，默认使用 v3 语法 (-in)")
    return 3


def build_muscle_cmd(muscle_version, input_fasta, output_aln, fmt):
    """
    根据 MUSCLE 版本构建比对命令。
    v3: muscle -in <input> -out <output> [-msf|-clw|-html]
    v5: muscle -align <input> -output <output> [-format <fmt>]
    """
    cmd = ["muscle"]
    if muscle_version >= 5:
        cmd.extend(["-align", str(input_fasta), "-output", str(output_aln)])
        # v5 格式参数
        fmt_map = {
            "fasta": "fasta",
            "msf": "msf",
            "clw": "clustal",
            "html": "html",
        }
        cmd.extend(["-format", fmt_map.get(fmt, "fasta")])
    else:
        cmd.extend(["-in", str(input_fasta), "-out", str(output_aln)])
        if fmt == "msf":
            cmd.append("-msf")
        elif fmt == "clw":
            cmd.append("-clw")
        elif fmt == "html":
            cmd.append("-html")
    return cmd


# ---------------------------------------------------------------------------
# 脚本路径自动定位
# ---------------------------------------------------------------------------

def get_script_dir():
    """获取此脚本所在目录（blast_best_extract.py / fix_orientation.py 应在同目录）"""
    return Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# 核心处理
# ---------------------------------------------------------------------------

def process_single_db(query, db_fasta, outdir, threads, prefix, script_dir):
    """处理单个数据库：建库 -> BLAST -> 提取"""
    db_path = Path(db_fasta)

    # 1. 自动建库（如果 .ndb 或 .nhr 不存在）
    ndb_file = db_path.with_suffix('.ndb')
    nhr_file = db_path.with_suffix('.nhr')
    if not ndb_file.exists() and not nhr_file.exists():
        print(f"[INFO] 正在为 {db_path.name} 建 BLAST 库...")
        run_cmd(["makeblastdb", "-in", str(db_path), "-dbtype", "nucl", "-parse_seqids"])

    # 2. 调用 blast_best_extract.py
    extract_script = script_dir / "blast_best_extract.py"
    extract_cmd = [
        sys.executable, str(extract_script),
        "-q", query,
        "-d", str(db_path),
        "-r", str(db_path),
        "-o", outdir,
        "-t", str(threads),
        "--keep-intermediate",
        "--prefix", prefix
    ]
    _, success = run_cmd(extract_cmd)
    return prefix, success


# ---------------------------------------------------------------------------
# 主函数
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="跨平台 BLAST 提取 + 方向校正 + MUSCLE 比对"
    )
    parser.add_argument("-q", "--query", required=True, help="查询序列 FASTA")
    parser.add_argument("-d", "--dbs", required=True,
                        help="BLAST 库的原始 FASTA 路径，多个用逗号分隔")
    parser.add_argument("-o", "--outdir", default="blast2msa_result",
                        help="输出目录 (默认: blast2msa_result)")
    parser.add_argument("-f", "--format", default="fasta",
                        choices=["fasta", "msf", "clw", "html"],
                        help="MUSCLE 输出格式 (默认: fasta)")
    parser.add_argument("-t", "--threads", type=int, default=4,
                        help="每个 BLAST 任务的线程数 (默认: 4)")
    parser.add_argument("-j", "--jobs", type=int, default=4,
                        help="同时比对的数据库并发数 (默认: 4)")
    args = parser.parse_args()

    # 前置检查
    check_dependencies()
    muscle_version = detect_muscle_version()
    script_dir = get_script_dir()

    Path(args.outdir).mkdir(parents=True, exist_ok=True)

    dbs = [db.strip() for db in args.dbs.split(",") if db.strip()]
    all_extracted_seqs = Path(args.outdir) / "all_extracted_seqs.fasta"

    if all_extracted_seqs.exists():
        all_extracted_seqs.unlink()

    # Step 1: 并发处理多个 BLAST 库
    print("=" * 60)
    print(f"[Step 1] 并发 BLAST 比对与提取 (并发数: {args.jobs})")
    print("=" * 60)

    results = {}
    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        future_to_db = {}
        for db_fasta in dbs:
            if not Path(db_fasta).exists():
                print(f"[WARN] 找不到数据库文件: {db_fasta}，跳过。")
                continue
            db_name = Path(db_fasta).stem
            prefix = f"target_{db_name}"
            future = executor.submit(
                process_single_db, args.query, db_fasta,
                args.outdir, args.threads, prefix, script_dir
            )
            future_to_db[future] = db_name

        for future in as_completed(future_to_db):
            db_name = future_to_db[future]
            try:
                prefix, success = future.result()
                if success:
                    extracted_file = Path(args.outdir) / f"{prefix}_best_match.fasta"
                    if extracted_file.exists():
                        with open(extracted_file, 'r') as fin, \
                             open(all_extracted_seqs, 'a') as fout:
                            for line in fin:
                                if line.startswith('>'):
                                    fout.write(f">{db_name}_{line[1:]}")
                                else:
                                    fout.write(line)
                results[db_name] = success
            except Exception as e:
                print(f"[ERROR] 处理 {db_name} 时发生异常: {e}")
                results[db_name] = False

    if not all_extracted_seqs.exists() or all_extracted_seqs.stat().st_size == 0:
        print("[ERROR] 未提取到任何序列，流程终止。")
        sys.exit(1)

    print(f"\n[INFO] 提取完成，成功: {sum(results.values())}/{len(results)} 个库")

    # Step 2: 方向校正
    print("=" * 60)
    print("[Step 2] 序列方向校正 (k-mer 法)")
    print("=" * 60)
    oriented_fasta = Path(args.outdir) / "all_extracted_oriented.fasta"
    orient_script = script_dir / "fix_orientation.py"
    run_cmd([
        sys.executable, str(orient_script),
        str(all_extracted_seqs),
        str(oriented_fasta),
        "--kmer", "20"
    ])

    if not oriented_fasta.exists():
        print("[ERROR] 方向校正失败，流程终止。")
        sys.exit(1)

    # Step 3: MUSCLE 多序列比对
    print("=" * 60)
    print(f"[Step 3] MUSCLE v{muscle_version} 多序列比对 (格式: {args.format})")
    print("=" * 60)
    aln_out = Path(args.outdir) / f"final_alignment.{args.format}"

    muscle_cmd = build_muscle_cmd(muscle_version, oriented_fasta, aln_out, args.format)
    _, muscle_ok = run_cmd(muscle_cmd)

    if muscle_ok and aln_out.exists():
        print("=" * 60)
        print(f"[DONE] 流程完成！最终比对文件: {aln_out}")
        print(f"       序列数: {sum(1 for l in open(oriented_fasta) if l.startswith('>'))}")
        print(f"       MUSCLE 版本: v{muscle_version}")
        print("=" * 60)
    else:
        print("[ERROR] MUSCLE 比对失败，请检查序列格式和 MUSCLE 安装。")
        sys.exit(1)


if __name__ == "__main__":
    main()
