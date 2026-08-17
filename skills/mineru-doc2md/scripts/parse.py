#!/usr/bin/env python3
"""Convert a single document to Markdown using MinerU.

Auto-detects whether a GPU is available and picks the backend accordingly:
  - GPU / Apple Silicon present → hybrid-engine (high accuracy)
  - CPU only                    → pipeline (pure CPU, no hallucination)

Usage:
    python parse.py <input_file> <output_dir> [options]

Examples:
    python parse.py document.pdf ./output
    python parse.py scan.png ./out --backend pipeline --lang ch_server
    python parse.py slides.pptx ./out --effort high
    python parse.py data.xlsx ./out --method ocr
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


# Supported input extensions (keep in sync with mineru.cli.common)
PDF_SUFFIXES = {".pdf"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}
OFFICE_SUFFIXES = {".docx", ".pptx", ".xlsx"}
SUPPORTED_SUFFIXES = PDF_SUFFIXES | IMAGE_SUFFIXES | OFFICE_SUFFIXES

BACKEND_CHOICES = ["pipeline", "vlm-engine", "hybrid-engine",
                   "vlm-http-client", "hybrid-http-client"]
METHOD_CHOICES = ["auto", "txt", "ocr"]
EFFORT_CHOICES = ["medium", "high"]
LANG_CHOICES = ["ch", "ch_server", "korean", "ta", "te", "ka", "th", "el",
                "arabic", "east_slavic", "cyrillic", "devanagari"]


def detect_gpu() -> bool:
    """Best-effort GPU / Apple Silicon detection."""
    # 1. Apple Silicon (MPS) — macOS only
    if sys.platform == "darwin":
        try:
            mac_ver = subprocess.check_output(
                ["sw_vers", "-productVersion"], text=True
            ).strip()
            major = int(mac_ver.split(".")[0])
            if major >= 14:
                # Check for Apple Silicon via sysctl
                try:
                    cpu = subprocess.check_output(
                        ["sysctl", "-n", "machdep.cpu.brand_string"], text=True
                    ).strip()
                    if "Apple" in cpu:
                        return True
                except Exception:
                    pass
        except Exception:
            pass

    # 2. NVIDIA GPU via nvidia-smi
    if shutil.which("nvidia-smi"):
        try:
            subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                text=True, stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            pass

    # 3. CUDA via PyTorch (if installed)
    try:
        import torch
        if torch.cuda.is_available():
            return True
    except Exception:
        pass

    return False


def guess_suffix(path: Path) -> str | None:
    """Return lowercase suffix if supported, else None."""
    suffix = path.suffix.lower()
    return suffix if suffix in SUPPORTED_SUFFIXES else None


def run_mineru(args: argparse.Namespace) -> int:
    """Invoke the `mineru` CLI with the given arguments."""
    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    if not input_path.exists():
        print(f"Error: input not found: {input_path}", file=sys.stderr)
        return 1

    suffix = guess_suffix(input_path) if input_path.is_file() else None
    if input_path.is_file() and suffix is None:
        print(
            f"Error: unsupported file type '{input_path.suffix}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_SUFFIXES))}",
            file=sys.stderr,
        )
        return 1

    output_path.mkdir(parents=True, exist_ok=True)

    # Pick backend
    backend = args.backend
    if backend is None:
        backend = "hybrid-engine" if detect_gpu() else "pipeline"
        print(f"Auto-selected backend: {backend}")

    # Build command
    cmd = [
        sys.executable, "-m", "mineru",
        "-p", str(input_path),
        "-o", str(output_path),
        "-b", backend,
    ]

    if args.method:
        cmd += ["-m", args.method]
    if args.effort and backend.startswith("hybrid"):
        cmd += ["--effort", args.effort]
    if args.lang and backend == "pipeline":
        cmd += ["-l", args.lang]
    if args.start is not None:
        cmd += ["-s", str(args.start)]
    if args.end is not None:
        cmd += ["-e", str(args.end)]
    if args.formula is not None:
        cmd += ["-f", "true" if args.formula else "false"]
    if args.table is not None:
        cmd += ["-t", "true" if args.table else "false"]
    if args.api_url:
        cmd += ["--api-url", args.api_url]
    if args.server_url and backend.endswith("http-client"):
        cmd += ["-u", args.server_url]
    if args.device:
        cmd += ["-d", args.device]
    if args.source:
        cmd += ["--source", args.source]

    # Model source env var (higher priority than CLI flag)
    env = os.environ.copy()
    if args.model_source_env:
        env["MINERU_MODEL_SOURCE"] = args.model_source_env

    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, env=env, check=False)
    except FileNotFoundError:
        print(
            "Error: mineru not found. Install with: pip install -U \"mineru[all]\"",
            file=sys.stderr,
        )
        return 127

    if result.returncode == 0:
        # Find and report the output markdown
        stem = input_path.stem if input_path.is_file() else "input"
        md_candidates = list(output_path.rglob("*.md"))
        if md_candidates:
            print(f"\n✓ Markdown output(s):")
            for md in md_candidates:
                print(f"  {md}")
        else:
            print(f"\n✓ Done. Output in: {output_path}")
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert a document to Markdown using MinerU.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("input", help="Input file (PDF/image/DOCX/PPTX/XLSX)")
    parser.add_argument("output", help="Output directory")
    parser.add_argument("-b", "--backend", choices=BACKEND_CHOICES, default=None,
                        help="Parsing backend (default: auto-detect)")
    parser.add_argument("-m", "--method", choices=METHOD_CHOICES, default=None,
                        help="Parsing method (pipeline & hybrid* only)")
    parser.add_argument("--effort", choices=EFFORT_CHOICES, default=None,
                        help="Hybrid parsing effort (hybrid only)")
    parser.add_argument("-l", "--lang", choices=LANG_CHOICES, default=None,
                        help="OCR language hint (pipeline only)")
    parser.add_argument("-s", "--start", type=int, default=None,
                        help="Start page (0-based)")
    parser.add_argument("-e", "--end", type=int, default=None,
                        help="End page (0-based)")
    parser.add_argument("-f", "--formula", dest="formula",
                        type=lambda x: x.lower() in ("true", "1", "yes"),
                        default=None, help="Enable formula parsing (true/false)")
    parser.add_argument("-t", "--table", dest="table",
                        type=lambda x: x.lower() in ("true", "1", "yes"),
                        default=None, help="Enable table parsing (true/false)")
    parser.add_argument("--api-url", default=None,
                        help="MinerU FastAPI base URL (auto-start local if omitted)")
    parser.add_argument("-u", "--server-url", default=None,
                        help="OpenAI-compatible server URL (http-client backends)")
    parser.add_argument("-d", "--device", default=None,
                        help="Device: cpu / cuda / mps / cuda:0")
    parser.add_argument("--source", default=None,
                        choices=["auto", "huggingface", "modelscope", "local"],
                        help="Model source override")
    parser.add_argument("--model-source-env", default=None,
                        choices=["huggingface", "modelscope", "local"],
                        help="Set MINERU_MODEL_SOURCE env var (highest priority)")
    args = parser.parse_args()
    return run_mineru(args)


if __name__ == "__main__":
    sys.exit(main())
