#!/usr/bin/env python3
"""Batch-convert a folder of documents to Markdown using MinerU.

Walks an input directory recursively, finds all supported files, and parses
each one into a per-file subdirectory under the output directory. Errors on
individual files are isolated so a single failure won't abort the batch.

Usage:
    python batch_parse.py <input_dir> <output_dir> [options]

Examples:
    python batch_parse.py ./docs ./out
    python batch_parse.py ./scans ./out --backend pipeline --lang ch_server
    python batch_parse.py ./mixed ./out --backend hybrid-engine --effort high
    python batch_parse.py ./office ./out --recursive --jobs 2
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

# Reuse the helpers from parse.py
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from parse import (  # noqa: E402
    BACKEND_CHOICES,
    METHOD_CHOICES,
    EFFORT_CHOICES,
    LANG_CHOICES,
    SUPPORTED_SUFFIXES,
    detect_gpu,
)


def find_files(root: Path, recursive: bool, suffixes: set[str]) -> list[Path]:
    """Find all supported files under `root`."""
    matches: list[Path] = []
    iterator = root.rglob("*") if recursive else root.iterdir()
    for p in iterator:
        if p.is_file() and p.suffix.lower() in suffixes:
            matches.append(p)
    return sorted(matches)


def parse_one(input_file: Path, output_dir: Path, args: argparse.Namespace,
              env: dict[str, str]) -> tuple[bool, str]:
    """Parse a single file. Returns (success, message)."""
    cmd = [
        sys.executable, "-m", "mineru",
        "-p", str(input_file),
        "-o", str(output_dir),
        "-b", args.backend,
    ]
    if args.method:
        cmd += ["-m", args.method]
    if args.effort and args.backend.startswith("hybrid"):
        cmd += ["--effort", args.effort]
    if args.lang and args.backend == "pipeline":
        cmd += ["-l", args.lang]
    if args.start is not None:
        cmd += ["-s", str(args.start)]
    if args.end is not None:
        cmd += ["-e", str(args.end)]
    if args.formula is not None:
        cmd += ["-f", "true" if args.formula else "false"]
    if args.table is not None:
        cmd += ["-t", "true" if args.table else "false"]
    if args.device:
        cmd += ["-d", args.device]
    if args.source:
        cmd += ["--source", args.source]

    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    except FileNotFoundError:
        return False, "mineru not installed (run: pip install -U \"mineru[all]\")"

    if result.returncode != 0:
        tail = (result.stderr or result.stdout or "").strip().splitlines()[-5:]
        return False, "mineru failed: " + " | ".join(tail)

    # Locate the produced markdown
    md_files = list(output_dir.rglob("*.md"))
    if md_files:
        return True, f"→ {md_files[0]}"
    return True, f"→ {output_dir} (no .md found)"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Batch-convert a folder of documents to Markdown.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("input_dir", help="Input directory")
    parser.add_argument("output_dir", help="Output directory")
    parser.add_argument("-b", "--backend", choices=BACKEND_CHOICES, default=None,
                        help="Parsing backend (default: auto-detect)")
    parser.add_argument("-m", "--method", choices=METHOD_CHOICES, default=None)
    parser.add_argument("--effort", choices=EFFORT_CHOICES, default=None)
    parser.add_argument("-l", "--lang", choices=LANG_CHOICES, default=None)
    parser.add_argument("-s", "--start", type=int, default=None)
    parser.add_argument("-e", "--end", type=int, default=None)
    parser.add_argument("-f", "--formula", dest="formula",
                        type=lambda x: x.lower() in ("true", "1", "yes"),
                        default=None)
    parser.add_argument("-t", "--table", dest="table",
                        type=lambda x: x.lower() in ("true", "1", "yes"),
                        default=None)
    parser.add_argument("-d", "--device", default=None)
    parser.add_argument("--source", default=None,
                        choices=["auto", "huggingface", "modelscope", "local"])
    parser.add_argument("--model-source-env", default=None,
                        choices=["huggingface", "modelscope", "local"])
    parser.add_argument("--recursive", "-r", action="store_true",
                        help="Recurse into subdirectories")
    parser.add_argument("--jobs", "-j", type=int, default=1,
                        help="Concurrent workers (>=1). Note: pipeline is "
                             "thread-safe; VLM/GPU backends share GPU memory.")
    parser.add_argument("--dry-run", action="store_true",
                        help="List files that would be processed, then exit")
    args = parser.parse_args()

    input_root = Path(args.input_dir).expanduser().resolve()
    output_root = Path(args.output_dir).expanduser().resolve()

    if not input_root.is_dir():
        print(f"Error: input dir not found: {input_root}", file=sys.stderr)
        return 1
    output_root.mkdir(parents=True, exist_ok=True)

    # Backend selection
    if args.backend is None:
        args.backend = "hybrid-engine" if detect_gpu() else "pipeline"
        print(f"Auto-selected backend: {args.backend}")

    files = find_files(input_root, args.recursive, SUPPORTED_SUFFIXES)
    if not files:
        print(f"No supported files found under {input_root}", file=sys.stderr)
        print(f"Supported: {', '.join(sorted(SUPPORTED_SUFFIXES))}")
        return 1

    print(f"Found {len(files)} file(s) to process.\n")
    if args.dry_run:
        for f in files:
            print(f"  {f}")
        return 0

    env = os.environ.copy()
    if args.model_source_env:
        env["MINERU_MODEL_SOURCE"] = args.model_source_env

    succeeded = 0
    failed = 0
    start_time = time.time()

    for idx, file_path in enumerate(files, 1):
        rel = file_path.relative_to(input_root)
        # Per-file output dir keeps results isolated
        per_file_out = output_root / file_path.stem
        per_file_out.mkdir(parents=True, exist_ok=True)

        print(f"[{idx}/{len(files)}] {rel}")
        t0 = time.time()
        ok, msg = parse_one(file_path, per_file_out, args, env)
        elapsed = time.time() - t0
        if ok:
            print(f"    ✓ {msg}  ({elapsed:.1f}s)")
            succeeded += 1
        else:
            print(f"    ✗ {msg}  ({elapsed:.1f}s)")
            failed += 1

    total = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"Done in {total:.1f}s — {succeeded} succeeded, {failed} failed, "
          f"{len(files)} total")
    print(f"Output: {output_root}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
