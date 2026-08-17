# MinerU Model Source Configuration

MinerU auto-downloads models on first run. This document covers model sources, download commands, local cache, and offline use.

## Model Sources

| Source      | Value                     | Use when                             |
| ----------- | ------------------------- | ------------------------------------ |
| HuggingFace | `huggingface` _(default)_ | Default; global access               |
| ModelScope  | `modelscope`              | China network (no proxy needed)      |
| Local       | `local`                   | Fully offline, pre-downloaded models |
| Auto        | `auto` _(unset)_          | MinerU picks best by network         |

## Setting the Source

### Via environment variable (highest priority)

```bash
export MINERU_MODEL_SOURCE=modelscope
mineru -p doc.pdf -o ./out
```

The env var overrides `mineru.json` and applies to all CLI/API calls in the session.

### Via `mineru.json` config file

Located at `~/.mineru/mineru.json` (or `%USERPROFILE%\.mineru\mineru.json` on Windows):

```json
{
  "model-source": "modelscope",
  "device": "cuda",
  "local-model-dir": "~/.cache/mineru"
}
```

### Via CLI `--source` flag

```bash
mineru -p doc.pdf -o ./out --source modelscope
```

## Pre-downloading Models

### `mineru-models-download` command

```bash
# From HuggingFace (default)
mineru-models-download huggingface

# From ModelScope (China)
export MINERU_MODEL_SOURCE=modelscope
mineru-models-download modelscope

# Auto-select by network
mineru-models-download auto
```

> `mineru-models-download` always downloads from a **remote** source (ignores `MINERU_MODEL_SOURCE=local` for this command; temporarily uses your chosen `auto`/`huggingface`/`modelscope`).

### Download location

- Default: `~/.cache/huggingface/hub/` (HuggingFace) or `~/.cache/modelscope/hub/` (ModelScope)
- Custom: set `local-model-dir` in `mineru.json` or `LOCAL_MODEL_DIR` env var

## Using Local Models (offline)

After downloading, you can run fully offline:

```bash
# Point to local cache
export MINERU_MODEL_SOURCE=local

# Or set in mineru.json
# { "model-source": "local", "local-model-dir": "/path/to/models" }

mineru -p doc.pdf -o ./out -b pipeline
```

### Moving model files

- You can move the model folder to any location.
- Update `local-model-dir` in `~/.mineru/mineru.json` to the new path.
- To deploy to another server, copy both the model folder **and** `mineru.json`.

### Updating models

```bash
mineru-models-download huggingface   # incremental if folder unchanged
```

If you moved the folder, the update re-downloads to the default location and updates `mineru.json`.

## Cache Reuse (v3.4+)

Before downloading, MinerU checks the local cache first:

- Cache hits → reuse directly (no remote request)
- This reduces repeated downloads across environments

## Model Sizes (approximate)

| Backend              | Model                               | Size   |
| -------------------- | ----------------------------------- | ------ |
| pipeline             | PP-OCRv6 + layout + formula + table | ~2GB   |
| vlm-engine / hybrid  | MinerU2.5-Pro-2605-1.2B             | ~2.5GB |
| Total (all backends) | —                                   | ~5GB   |

Disk: min 20GB recommended (models + temp + output).

## Troubleshooting

### "Failed to download model from huggingface"

- Switch to ModelScope: `export MINERU_MODEL_SOURCE=modelscope`
- Or use a HuggingFace mirror: `export HF_ENDPOINT=https://hf-mirror.com`
- Pre-download on a network-accessible machine, then copy the `~/.cache` folder.

### "Model not found at local path"

- Verify `local-model-dir` in `mineru.json` points to the right folder.
- Run `mineru-models-download` to populate, then switch to `local`.

### Slow first run

- First run downloads models (~2–5GB). Subsequent runs use cache.
- Use `modelscope` in China for faster mirrors.
- Pre-download with `mineru-models-download` to separate download from parsing.

### "CUDA out of memory" during model load

- Use `pipeline` backend (smaller memory footprint).
- Reduce `device` batch size or use `-d cpu`.
