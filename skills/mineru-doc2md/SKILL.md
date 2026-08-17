---
name: mineru-doc2md
description: "Convert PDF, images (PNG/JPG/TIFF/BMP), DOCX, PPTX, and XLSX files into structured Markdown / JSON using the MinerU parsing engine (VLM + OCR dual engine, 109 languages). Use whenever the user wants to turn a document into Markdown, extract text/tables/formulas from PDFs or Office files, OCR scanned documents, build RAG/Agent corpora, or batch-convert a folder of documents. Triggers include: any mention of 'MinerU', 'doc to markdown', 'PDF to markdown', 'extract text from PDF/PPT/Word/Excel', 'OCR', 'document parsing', 'RAG data preparation', or referencing a .pdf/.docx/.pptx/.xlsx/.png/.jpg file that should be converted to .md/.json. Supports local CLI, Python SDK, REST API, and Docker deployment across Windows/Linux/macOS."
license: Proprietary. LICENSE.txt has complete terms
metadata: null
always_active: false
---

# MinerU Document-to-Markdown Conversion Guide

## Overview

[MinerU](https://github.com/opendatalab/MinerU) is a high-accuracy document parsing engine that converts **PDF · DOCX · PPTX · XLSX · Images · Web pages** into structured **Markdown / JSON** for LLM, RAG, and Agent workflows. It uses a **VLM + OCR dual engine** supporting 109 languages, with accurate layout reconstruction, formula → LaTeX, and tables → HTML conversion.

This skill wraps MinerU's CLI, Python SDK, and REST API into ready-to-run scripts. Pick the approach by task:

| Task | Approach |
|---|---|
| **Quick single file** | `scripts/parse.py` — wraps `mineru` CLI, auto-picks backend by hardware |
| **Batch a folder** | `scripts/batch_parse.py` — iterates files, streaming output |
| **Remote / API server** | `scripts/api_parse.py` — talks to `mineru-api` over HTTP |
| **Pure Python embedding** | `mineru.cli.common.do_parse` — see reference.md |
| **Docker deployment** | See references/deployment.md |

> Script paths below are relative to this skill's directory. Everything is plain Python or shell — no compilation.

## Supported Inputs

| Format | Extensions | Notes |
|---|---|---|
| PDF | `.pdf` | Native + scanned + garbled (auto-OCR) |
| Images | `.png` `.jpg` `.jpeg` `.bmp` `.tiff` `.webp` | Auto-converted to PDF internally |
| Word | `.docx` | Native parsing (no PDF detour), 10× faster |
| PowerPoint | `.pptx` | Native parsing since v3.1 |
| Excel | `.xlsx` | Native parsing since v3.1 |

**Output:** Markdown (`.md`), structured JSON (`content_list.json`), intermediate layout (`middle_json`), extracted images (`images/`), and visualization HTML.

## Quick Start

### 1. Install MinerU

```bash
# Recommended: use uv (fast, reproducible)
pip install --upgrade pip
pip install uv
uv pip install -U "mineru[all]"

# Or plain pip
pip install -U "mineru[all]"
```

`mineru[all]` includes all backends and works on Windows / Linux / macOS. Python 3.10–3.13 required.

### 2. Convert a single file (simplest)

```bash
# GPU available (default hybrid-engine, high accuracy)
mineru -p document.pdf -o ./output

# CPU-only (use pipeline backend, no GPU needed)
mineru -p document.pdf -o ./output -b pipeline

# Using this skill's wrapper (auto-detects CPU/GPU)
python scripts/parse.py document.pdf ./output
```

### 3. Convert a folder

```bash
python scripts/batch_parse.py ./docs ./output --backend pipeline
```

## Choosing a Backend

| Backend | Accuracy (OmniDocBench v1.6) | Hardware | Best for |
|---|---|---|---|
| `pipeline` | 86.4 | CPU or GPU, ≥16GB RAM | Fast, stable, no hallucination, pure-CPU |
| `vlm-engine` | 95.3 | GPU ≥8GB VRAM (or MPS) | Highest accuracy, complex layouts |
| `hybrid-engine` *(default)* | 95.3 (high) / 95.2 (medium) | GPU ≥2GB VRAM | Balanced — **recommended** |
| `vlm-http-client` / `hybrid-http-client` | — | Any (remote server) | Remote OpenAI-compatible servers |

> **CPU-only machine?** Always use `-b pipeline`. VLM/hybrid backends require GPU or Apple Silicon.
> **macOS?** `hybrid-engine` works on Apple Silicon (MPS). Use `pipeline` on Intel Macs.

### Parsing effort (hybrid only)

```bash
mineru -p doc.pdf -o ./out -b hybrid-engine --effort medium   # default, faster
mineru -p doc.pdf -o ./out -b hybrid-engine --effort high     # max accuracy + image analysis
```

`medium` is 35%–220% faster with only ~0.13-point accuracy loss. Use `high` when you need image/chart analysis or maximum fidelity.

## CLI Reference (key options)

```
mineru -p <input> -o <output> [options]

  -p, --path PATH                 Input file or directory (required)
  -o, --output PATH               Output directory (required)
  -b, --backend [pipeline|vlm-engine|hybrid-engine|vlm-http-client|hybrid-http-client]
                                  Parsing backend (default: hybrid-engine)
  -m, --method [auto|txt|ocr]     auto (default) | txt (force text) | ocr (force OCR)
                                  (pipeline & hybrid* only)
  --effort [medium|high]          Hybrid parsing strength (default: medium)
  -l, --lang [ch|ch_server|korean|ta|te|ka|th|el|arabic|east_slavic|cyrillic|devanagari]
                                  OCR language hint (pipeline backend only)
  -u, --url TEXT                  OpenAI-compatible server URL (http-client backends)
  -s, --start INTEGER             Start page (0-based)
  -e, --end INTEGER               End page (0-based)
  -f, --formula BOOLEAN           Enable formula parsing (default: true)
  -t, --table BOOLEAN             Enable table parsing (default: true)
  --api-url TEXT                  MinerU FastAPI base URL; omit to auto-start local service
```

See [references/cli_reference.md](references/cli_reference.md) for the full option list and examples.

## Output Files

After parsing `report.pdf` into `./output`, expect:

```
output/
└── report/
    ├── report.md                  # ← Main Markdown output (human reading order)
    ├── report_content_list.json   # Structured content list (for RAG chunking)
    ├── report_middle.json         # Layout/intermediate JSON (for 2nd-party dev)
    └── images/                    # Extracted figures (referenced by .md)
```

> VLM backend output structure differs from pipeline in v2.5+. For downstream apps reading JSON, read [references/output_files.md](references/output_files.md) before parsing.

## Model Source Configuration

MinerU auto-downloads models from HuggingFace on first run. If HuggingFace is unreachable (e.g., China), switch to ModelScope:

```bash
export MINERU_MODEL_SOURCE=modelscope   # China mirror, no proxy needed
mineru -p doc.pdf -o ./out
```

Supported values: `huggingface` (default), `modelscope`, `local`. The env var overrides `mineru.json`. For full model-source docs see [references/model_source.md](references/model_source.md).

## Python SDK (embedding in your code)

```python
import asyncio
from pathlib import Path
from mineru.cli.common import do_parse

# Synchronous (pipeline backend)
do_parse(
    output_dir="./output",
    input_file_path="document.pdf",
    parse_method="auto",
    backend="pipeline",
    f=True,   # formula enabled
    t=True,   # table enabled
)

# Async (vlm / hybrid backends) — see references/python_sdk.md
from mineru.cli.common import aio_do_parse
```

For a complete async example with the API client, see [references/python_sdk.md](references/python_sdk.md) and `scripts/api_parse.py`.

## REST API (mineru-api)

Start a local API server (it auto-starts when you run `mineru` without `--api-url`):

```bash
mineru-api --host 0.0.0.0 --port 8000
```

### Submit an async task

```bash
curl -X POST http://127.0.0.1:8000/tasks \
  -F "file=@document.pdf" \
  -F "backend=pipeline" \
  -F "parse_method=auto" \
  -F "formula_enable=true" \
  -F "table_enable=true" \
  -F "return_md=true"
# → 202 {"task_id": "...", "status": "pending"}
```

### Poll status & fetch result

```bash
curl http://127.0.0.1:8000/tasks/{task_id}        # status
curl http://127.0.0.1:8000/tasks/{task_id}/result # result zip
curl http://127.0.0.1:8000/health                 # server health
```

The legacy synchronous endpoint `POST /file_parse` is kept for backward compatibility. See [references/rest_api.md](references/rest_api.md) for full endpoint details.

## Docker Deployment

```bash
# Linux / Windows-WSL2 only (not macOS)
docker pull opendatalab/mineru:latest
docker run --gpus all -v $(pwd):/app opendatalab/mineru:latest \
    mineru -p /app/doc.pdf -o /app/out -b hybrid-engine
```

See [references/deployment.md](references/deployment.md) for Dockerfile, GPU passthrough, and multi-GPU `mineru-router` setup.

## Common Edge Cases & Gotchas

- **Scanned PDFs / garbled text:** MinerU auto-detects and enables OCR. Force OCR with `-m ocr` if auto-detection misses.
- **Handwritten or Japanese/Traditional Chinese:** Use `-l ch_server` (PP-OCRv5) on the `pipeline` backend for better handwriting accuracy.
- **Multi-column / cross-page tables:** All backends handle these; `hybrid-engine` merges cross-page tables best. Disable table merging via env var if needed.
- **Very long documents (10k+ pages):** Use `pipeline` with streaming writes — no manual splitting needed since v3.0 (sliding-window memory optimization).
- **Memory errors on GPU:** Lower batch or switch to `pipeline` (CPU). Min 2GB VRAM for hybrid, 8GB for vlm-engine.
- **First-run model download slow:** Set `MINERU_MODEL_SOURCE=modelscope` in China, or pre-download with `mineru-models-download huggingface`.
- **Office files parsing slowly via PDF detour:** Ensure you're on MinerU ≥3.0 for native DOCX, ≥3.1 for native PPTX/XLSX (10× faster, no hallucination).
- **`ray` on Windows + Python 3.13:** Unsupported — use Python 3.10–3.12 on Windows.
- **macOS Intel (no Apple Silicon):** VLM/hybrid backends won't work; use `-b pipeline`.
- **Image analysis not working on hybrid:** Only `--effort high` supports image analysis; `medium` skips it.
- **Formulas not converting to LaTeX:** Ensure `-f true` (default on). Complex nested formulas may need `--effort high`.
- **Output Markdown missing images:** Check the `images/` folder exists and paths in `.md` are relative. API mode requires `return_images=true`.

## Decision Tree: Which Script to Use

```
User has a document → convert to Markdown
│
├── Single file, want it fast
│   └── scripts/parse.py <file> <out>           # CLI wrapper
│
├── Folder of mixed documents
│   └── scripts/batch_parse.py <dir> <out>      # batch + streaming
│
├── Want to call a remote/running mineru-api
│   └── scripts/api_parse.py <file> <out> --api-url http://...
│
├── Embedding in Python app
│   └── from mineru.cli.common import do_parse  # see references/python_sdk.md
│
└── Production / multi-GPU scale-out
    └── Docker + mineru-router                   # see references/deployment.md
```

## When NOT to Use This Skill

- **Creating** a PDF/DOCX/XLSX/PPTX from scratch → use the `pdf`, `docx`, `xlsx`, or `pptx` skills instead.
- **Editing** an existing Office file's structure → use the format-specific skill (`docx`, `pptx`, `xlsx`).
- **Pure text extraction** (no layout/formulas) → `pypdf` or `markitdown` is lighter.
- **Web page → markdown** → MinerU supports it, but `markitdown` or `jina reader` may be simpler for HTML.

## Verification Checklist

Before delivering parsed output to the user, verify:

- [ ] Output `.md` file exists and is non-empty.
- [ ] Reading order in Markdown matches human reading order (check multi-column docs).
- [ ] Formulas rendered as `$...$` or `$$...$$` LaTeX, not garbled text.
- [ ] Tables converted to HTML or Markdown tables, not raw text dumps.
- [ ] Images extracted to `images/` and referenced correctly in `.md`.
- [ ] For scanned docs, OCR text is accurate (spot-check a few pages).
- [ ] No truncated paragraphs or missing sections (check `content_list.json` length).

## References

- [references/cli_reference.md](references/cli_reference.md) — Full CLI options & examples
- [references/python_sdk.md](references/python_sdk.md) — `do_parse` / `aio_do_parse` API
- [references/rest_api.md](references/rest_api.md) — `mineru-api` HTTP endpoints
- [references/output_files.md](references/output_files.md) — Output file formats (v2.5+)
- [references/model_source.md](references/model_source.md) — Model source & download config
- [references/deployment.md](references/deployment.md) — Docker, multi-GPU, router
- [Upstream README](https://github.com/opendatalab/MinerU) — Official docs
