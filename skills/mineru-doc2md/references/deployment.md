# MinerU Deployment Reference

Deployment options for MinerU: local install, Docker, multi-GPU, and domestic AI chips.

## Hardware Requirements

| Backend         | OS              | CPU    | GPU                     | VRAM | RAM               | Disk      |
| --------------- | --------------- | ------ | ----------------------- | ---- | ----------------- | --------- |
| `pipeline`      | Linux/Win/macOS | ✅ any | optional                | —    | ≥16GB (32GB rec.) | ≥20GB SSD |
| `vlm-engine`    | Linux/Win/macOS | ✅     | Volta+ or Apple Silicon | ≥8GB | ≥16GB             | ≥2GB      |
| `hybrid-engine` | Linux/Win/macOS | ✅     | Volta+ or Apple Silicon | ≥2GB | ≥16GB             | ≥2GB      |
| `*-http-client` | any             | ✅     | none (remote)           | —    | minimal           | minimal   |

**Python:** 3.10–3.13 (Windows: 3.10–3.12, since `ray` doesn't support 3.13 on Windows).
**macOS:** 14.0+ (Apple Silicon for VLM/hybrid; Intel Macs use `pipeline` only).

## Local Installation

```bash
# Recommended: uv (fast dependency resolution)
pip install --upgrade pip
pip install uv
uv pip install -U "mineru[all]"

# Or pip
pip install -U "mineru[all]"

# From source
git clone https://github.com/opendatalab/MinerU.git
cd MinerU
uv pip install -e .[all]
```

### Verify install

```bash
mineru --version
mineru-models-download auto   # pre-download models
```

### Windows CUDA

If CUDA acceleration doesn't work after install, see the [Windows CUDA FAQ](https://github.com/opendatalab/MinerU). Typically requires matching CUDA toolkit + PyTorch build.

## Docker Deployment

> Docker is supported on **Linux** and **Windows with WSL2** only. macOS users should use pip/uv install.

### Pull and run

```bash
docker pull opendatalab/mineru:latest

# CPU-only
docker run --rm -v $(pwd):/app -w /app opendatalab/mineru:latest \
    mineru -p /app/doc.pdf -o /app/out -b pipeline

# GPU (NVIDIA)
docker run --rm --gpus all -v $(pwd):/app -w /app opendatalab/mineru:latest \
    mineru -p /app/doc.pdf -o /app/out -b hybrid-engine
```

### Build from source

```dockerfile
FROM opendatalab/mineru:latest
COPY . /app
WORKDIR /app
RUN pip install -U "mineru[all]"
CMD ["mineru-api", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose (persistent API server)

```yaml
version: "3.8"
services:
  mineru:
    image: opendatalab/mineru:latest
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - mineru-cache:/root/.cache
    command: ["mineru-api", "--host", "0.0.0.0", "--port", "8000"]
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

volumes:
  mineru-cache:
```

## Multi-GPU Deployment with `mineru-router`

`mineru-router` is a load balancer that distributes parsing tasks across multiple `mineru-api` instances (each typically on a separate GPU). Its API is fully compatible with `mineru-api`.

### Architecture

```
Client → mineru-router (port 8000)
            ├── mineru-api @ gpu-1:8001
            ├── mineru-api @ gpu-2:8002
            └── mineru-api @ gpu-3:8003
```

### Start worker API servers (one per GPU)

```bash
# On gpu-1
CUDA_VISIBLE_DEVICES=0 mineru-api --host 0.0.0.0 --port 8001

# On gpu-2
CUDA_VISIBLE_DEVICES=1 mineru-api --host 0.0.0.0 --port 8002
```

### Configure and start the router

`router.yaml`:

```yaml
host: 0.0.0.0
port: 8000
strategy: round-robin # or least-connections
upstreams:
  - url: http://gpu-1:8001
    weight: 1
  - url: http://gpu-2:8002
    weight: 1
  - url: http://gpu-3:8003
    weight: 1
```

```bash
mineru-router --config router.yaml
```

Clients now talk to `http://router-host:8000` exactly as if it were a single `mineru-api`. The router forwards tasks and balances load.

## Thread-Safety & Concurrency (v3.0+)

- Pipeline backend: **fully thread-safe**, supports multi-threaded concurrent inference.
- Combined with `mineru-router`, enables one-click multi-GPU deployment.
- Long-document parsing uses a sliding-window mechanism, so peak memory stays low even for 10k+ page documents.
- Pipeline batch inference streams writes to disk, so completed results are written out promptly.

## Domestic AI Chip Support

MinerU supports domestic AI chips for the VLM/hybrid backends:

| Chip          | Vendor |
| ------------- | ------ |
| Ascend        | Huawei |
| Cambricon     | —      |
| Enflame       | —      |
| MetaX         | —      |
| Moore Threads | —      |
| Kunlunxin     | —      |
| Iluvatar      | —      |
| Hygon         | —      |
| Biren         | —      |
| T-Head        | —      |

See the [chip-specific docs](https://github.com/opendatalab/MinerU/tree/master/docs) for per-vendor setup.

## Environment Variables for Deployment

| Variable                                  | Purpose                                           |
| ----------------------------------------- | ------------------------------------------------- |
| `MINERU_MODEL_SOURCE`                     | Model source (`huggingface`/`modelscope`/`local`) |
| `LOCAL_MODEL_DIR`                         | Local model directory                             |
| `MINERU_DEVICE`                           | Default device (`cuda`/`cpu`/`mps`)               |
| `CUDA_VISIBLE_DEVICES`                    | GPU selection (multi-GPU)                         |
| `TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL` | AMD ROCm (`1`)                                    |
| `HF_ENDPOINT`                             | HuggingFace mirror (`https://hf-mirror.com`)      |

## Production Checklist

- [ ] Models pre-downloaded (`mineru-models-download`) — don't download on first request.
- [ ] Persistent `mineru-api` running (not the auto-start temp service).
- [ ] Reverse proxy (nginx/caddy) in front for TLS + auth.
- [ ] Volume mounts for `~/.cache` (models) and output directory.
- [ ] Health check endpoint (`GET /health`) monitored.
- [ ] For multi-GPU: `mineru-router` with ≥2 worker API servers.
- [ ] Sufficient disk: 20GB+ for models, plus output space.
- [ ] Python version pinned (3.10–3.12 for Windows).
