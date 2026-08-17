# MinerU CLI Reference

Full command-line reference for the `mineru` orchestration client and `mineru-api` server.

## `mineru` — Document Parsing Client

```
Usage: mineru [OPTIONS]

Options:
  -v, --version                   Show version and exit
  -p, --path PATH                 Input file path or directory (required)
  -o, --output PATH               Output directory (required)
  --api-url TEXT                  MinerU FastAPI base URL; if omitted, `mineru`
                                  starts a temporary local `mineru-api`
  -m, --method [auto|txt|ocr]     Parsing method: auto (default), txt, ocr
                                  (pipeline and hybrid* backend only)
  -b, --backend [pipeline|vlm-engine|hybrid-engine|vlm-http-client|hybrid-http-client]
                                  Parsing backend (default: hybrid-engine)
  --effort [medium|high]          Hybrid parsing effort (default: medium)
  -l, --lang [ch|ch_server|korean|ta|te|ka|th|el|arabic|east_slavic|cyrillic|devanagari]
                                  Specify document language (improves OCR
                                  accuracy, pipeline backend only)
  -u, --url TEXT                  OpenAI-compatible backend URL passed through
                                  to the server when using http-client
  -s, --start INTEGER             Starting page number for parsing (0-based)
  -e, --end INTEGER               Ending page number for parsing (0-based)
  -f, --formula BOOLEAN           Enable formula parsing (default: enabled)
  -t, --table BOOLEAN             Enable table parsing (default: enabled)
  -d, --device TEXT               Device override: cpu / cuda / mps / cuda:0
  --source [auto|huggingface|modelscope|local]
                                  Model source override (default: auto)
  --enable-vlm-preload BOOLEAN    Preload local VLM model when gradio starts
                                  a local mineru-api service
  --help                          Show this message and exit
```

## Backends in Detail

### `pipeline`

- **Accuracy:** 86.4 (OmniDocBench v1.6)
- **Hardware:** CPU or GPU, ≥16GB RAM, ≥20GB disk (models)
- **Pure CPU:** ✅ supported
- **Use when:** No GPU, fast batch processing, no hallucination tolerance, scanned/OCR-heavy docs
- **OCR model:** PP-OCRv6 (v3.4+), 109 languages

### `vlm-engine`

- **Accuracy:** 95.3
- **Hardware:** GPU ≥8GB VRAM (Volta+) or Apple Silicon (MPS)
- **Pure CPU:** ❌ not supported
- **Use when:** Maximum accuracy, complex layouts, charts/images, scientific docs
- **Model:** MinerU2.5-Pro-2605-1.2B

### `hybrid-engine` (default)

- **Accuracy:** 95.3 (high) / 95.2 (medium)
- **Hardware:** GPU ≥2GB VRAM or Apple Silicon
- **Pure CPU:** ❌ (needs GPU/MPS)
- **Use when:** Balanced accuracy + speed; most use cases
- **Effort:** `medium` (default, faster) or `high` (max accuracy + image analysis)

### `vlm-http-client` / `hybrid-http-client`

- **Use when:** Calling a remote OpenAI-compatible server (vLLM/SGLang/LMDeploy)
- **Requires:** `-u <server_url>` (e.g., `http://127.0.0.1:30000`)

## Language Codes (`-l` / `--lang`)

Only applies to the `pipeline` backend. Hybrid and VLM backends ignore this (multilingual by default).

| Code             | Languages                                          | OCR Model               |
| ---------------- | -------------------------------------------------- | ----------------------- |
| `ch` _(default)_ | Chinese / English / Japanese / Traditional Chinese | PP-OCRv4_server_rec_doc |
| `ch_server`      | Same as `ch` + **handwriting**                     | PP-OCRv5_rec_server     |
| `ch_lite`        | Same as `ch` + handwriting (mobile)                | PP-OCRv5_rec_mobile     |
| `korean`         | Korean                                             | —                       |
| `ta`             | Tamil                                              | —                       |
| `te`             | Telugu                                             | —                       |
| `ka`             | Georgian                                           | —                       |
| `th`             | Thai                                               | —                       |
| `el`             | Greek                                              | —                       |
| `arabic`         | Arabic                                             | —                       |
| `east_slavic`    | East Slavic (Russian, Ukrainian, Belarusian)       | —                       |
| `cyrillic`       | Cyrillic-script languages                          | —                       |
| `devanagari`     | Hindi, Marathi, Nepali, etc.                       | —                       |

> **v3.4 change:** Japanese, Traditional Chinese, English, and Latin were removed as separate options — they now route through the `ch` model.

## Examples

### Basic conversions

```bash
# PDF → Markdown (auto backend)
mineru -p paper.pdf -o ./out

# Image → Markdown
mineru -p scan.png -o ./out -b pipeline

# DOCX → Markdown (native, fast)
mineru -p report.docx -o ./out

# PPTX → Markdown
mineru -p slides.pptx -o ./out

# XLSX → Markdown
mineru -p data.xlsx -o ./out
```

### Page range & method

```bash
# Parse only pages 5–10 (0-based: pages 6–11)
mineru -p big.pdf -o ./out -s 5 -e 10

# Force OCR on a scanned PDF
mineru -p scanned.pdf -o ./out -b pipeline -m ocr

# Force text extraction (skip OCR)
mineru -p digital.pdf -o ./out -b pipeline -m txt
```

### Language & device

```bash
# Korean document on CPU
mineru -p korean.pdf -o ./out -b pipeline -l korean -d cpu

# Handwritten Chinese on GPU
mineru -p handwritten.pdf -o ./out -b pipeline -l ch_server -d cuda
```

### Formula & table control

```bash
# Disable formula parsing (faster, no LaTeX)
mineru -p text.pdf -o ./out -b pipeline -f false

# Disable table parsing
mineru -p no_tables.pdf -o ./out -b pipeline -t false
```

### Remote API client

```bash
# Use a running mineru-api server
mineru -p doc.pdf -o ./out --api-url http://127.0.0.1:8000

# Use a remote OpenAI-compatible VLM server
mineru -p doc.pdf -o ./out -b vlm-http-client -u http://gpu-server:30000
```

## `mineru-api` — FastAPI Server

```
Usage: mineru-api [OPTIONS]

Options:
  --host TEXT                     Bind host (default: 127.0.0.1)
  --port INTEGER                  Bind port (default: 8000)
  --enable-vlm-preload BOOLEAN    Preload local VLM model on startup
  --help                          Show this message and exit
```

Start a persistent server:

```bash
mineru-api --host 0.0.0.0 --port 8000
```

## `mineru-models-download` — Pre-download Models

```bash
# Download from HuggingFace (default)
mineru-models-download huggingface

# Download from ModelScope (China mirror)
export MINERU_MODEL_SOURCE=modelscope
mineru-models-download modelscope

# Auto-select best source by network
mineru-models-download auto
```

## `mineru-router` — Multi-GPU Load Balancer

For production multi-GPU deployment. Interfaces are fully compatible with `mineru-api` and support automatic task load balancing across multiple services and GPUs.

```bash
mineru-router --config router.yaml
```

See [deployment.md](deployment.md) for router configuration.

## Environment Variables

| Variable                                  | Purpose               | Example                |
| ----------------------------------------- | --------------------- | ---------------------- |
| `MINERU_MODEL_SOURCE`                     | Model source override | `modelscope`           |
| `LOCAL_MODEL_DIR`                         | Local model directory | `~/.cache/mineru`      |
| `MINERU_DEVICE`                           | Default device        | `cuda` / `cpu` / `mps` |
| `TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL` | AMD ROCm support      | `1`                    |

## Exit Codes

| Code | Meaning                            |
| ---- | ---------------------------------- |
| 0    | Success                            |
| 1    | Invalid arguments / file not found |
| 2    | Model download failure             |
| 3    | Parsing error (backend crash)      |
| 4    | Out of memory                      |
