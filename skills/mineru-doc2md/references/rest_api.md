# MinerU REST API Reference

`mineru-api` is a FastAPI server that exposes MinerU parsing over HTTP. It supports both async tasks (`POST /tasks`, since v3.0) and a legacy synchronous endpoint (`POST /file_parse`).

## Starting the Server

```bash
# Foreground, localhost only
mineru-api

# Bind to all interfaces, custom port
mineru-api --host 0.0.0.0 --port 8000

# Preload VLM model at startup (faster first request)
mineru-api --enable-vlm-preload true
```

When you run `mineru -p ... -o ...` without `--api-url`, a temporary local `mineru-api` is auto-started and torn down after parsing. For repeated calls, run a persistent server.

## Authentication

No built-in auth. Put behind a reverse proxy (nginx/caddy) with auth for production. The API is designed for trusted-network or localhost use.

## Endpoints

### `GET /health`

Server health & capacity.

```bash
curl http://127.0.0.1:8000/health
```

Response:

```json
{
  "protocol_version": "1.0",
  "processing_window_size": 4,
  "max_concurrent_requests": 8,
  "task_stats": {
    "pending": 0,
    "running": 1,
    "completed": 12,
    "failed": 0
  }
}
```

### `POST /tasks` — Submit Async Task (recommended)

Submit a document for asynchronous parsing. Returns `202 Accepted` with a `task_id`.

```bash
curl -X POST http://127.0.0.1:8000/tasks \
  -F "file=@document.pdf" \
  -F "backend=pipeline" \
  -F "parse_method=auto" \
  -F "lang=ch" \
  -F "formula_enable=true" \
  -F "table_enable=true" \
  -F "start_page_id=0" \
  -F "return_md=true" \
  -F "return_images=true" \
  -F "response_format_zip=true"
```

**Form fields:**

| Field                  | Type      | Default         | Description                                                   |
| ---------------------- | --------- | --------------- | ------------------------------------------------------------- |
| `file`                 | file      | —               | One or more upload files (required)                           |
| `backend`              | string    | `hybrid-engine` | `pipeline` / `vlm-engine` / `hybrid-engine` / `*-http-client` |
| `parse_method`         | string    | `auto`          | `auto` / `txt` / `ocr`                                        |
| `effort`               | string    | `medium`        | `medium` / `high` (hybrid only)                               |
| `lang`                 | string    | `ch`            | OCR language (pipeline only)                                  |
| `formula_enable`       | bool      | `true`          | Formula → LaTeX                                               |
| `table_enable`         | bool      | `true`          | Table → HTML                                                  |
| `image_analysis`       | bool      | `true`          | Image/chart analysis (vlm/hybrid)                             |
| `start_page_id`        | int       | `0`             | 0-based start page                                            |
| `end_page_id`          | int\|null | `null`          | End page (null = to end)                                      |
| `server_url`           | string    | `null`          | OpenAI-compatible URL (http-client)                           |
| `return_md`            | bool      | `true`          | Include `.md` in result                                       |
| `return_middle_json`   | bool      | `false`         | Include layout JSON                                           |
| `return_model_output`  | bool      | `false`         | Include raw model output                                      |
| `return_content_list`  | bool      | `false`         | Include `content_list.json`                                   |
| `return_images`        | bool      | `true`          | Include `images/`                                             |
| `return_original_file` | bool      | `false`         | Include original file                                         |
| `response_format_zip`  | bool      | `true`          | Return as zip (else tar)                                      |

Response (202):

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Task submitted successfully",
  "queued_ahead": 0
}
```

### `GET /tasks/{task_id}` — Poll Status

```bash
curl http://127.0.0.1:8000/tasks/550e8400-e29b-41d4-a716-446655440000
```

Response:

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "progress": 0.65,
  "queued_ahead": null
}
```

**Statuses:** `pending` → `running` → `completed` | `failed`

### `GET /tasks/{task_id}/result` — Fetch Result

```bash
curl -o result.zip http://127.0.0.1:8000/tasks/550e8400-e29b-41d4-a716-446655440000/result
unzip result.zip -d ./output
```

Returns a zip (or tar) containing the parsed output files. Structure:

```
result.zip
├── document/
│   ├── document.md
│   ├── document_content_list.json
│   ├── document_middle.json
│   └── images/
│       ├── img_0_0.png
│       └── ...
```

### `POST /file_parse` — Synchronous (legacy)

Kept for backward compatibility with older plugins. Blocks until parsing completes, then returns the result. Not recommended for large files or production (use `/tasks`).

```bash
curl -X POST http://127.0.0.1:8000/file_parse \
  -F "file=@document.pdf" \
  -F "backend=pipeline" \
  -F "parse_method=auto" \
  -F "return_md=true"
```

### `DELETE /tasks/{task_id}` — Cancel Task

```bash
curl -X DELETE http://127.0.0.1:8000/tasks/550e8400-e29b-41d4-a716-446655440000
```

Cancels a pending or running task.

## Full Python Example

```python
import asyncio
from pathlib import Path
import httpx

async def parse_document(file_path: str, output_dir: str, api_url: str):
    output_path = Path(output_dir).resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as client:
        # 1. Submit task
        with open(file_path, "rb") as f:
            response = await client.post(
                f"{api_url}/tasks",
                data={
                    "backend": "pipeline",
                    "parse_method": "auto",
                    "return_md": "true",
                    "return_images": "true",
                    "response_format_zip": "true",
                },
                files={"file": (Path(file_path).name, f)},
            )
        response.raise_for_status()
        task_id = response.json()["task_id"]
        print(f"Submitted task: {task_id}")

        # 2. Poll until complete
        import time
        while True:
            status_resp = await client.get(f"{api_url}/tasks/{task_id}")
            status_resp.raise_for_status()
            status = status_resp.json()["status"]
            print(f"Status: {status}")
            if status in ("completed", "failed"):
                break
            await asyncio.sleep(2)

        if status == "failed":
            raise RuntimeError("Parsing failed")

        # 3. Download result
        result_resp = await client.get(f"{api_url}/tasks/{task_id}/result")
        result_resp.raise_for_status()
        zip_path = output_path / "result.zip"
        zip_path.write_bytes(result_resp.content)

        # 4. Extract
        import zipfile
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(output_path)
        zip_path.unlink()
        print(f"Done: {output_path}")

asyncio.run(parse_document("doc.pdf", "./out", "http://127.0.0.1:8000"))
```

## `mineru-router` — Multi-Service Load Balancer

For scaling across multiple GPUs/servers. API-compatible with `mineru-api`.

```bash
mineru-router --config router.yaml --port 8000
```

Example `router.yaml`:

```yaml
upstreams:
  - url: http://gpu-1:8000
    weight: 1
  - url: http://gpu-2:8000
    weight: 1
strategy: round-robin # or least-connections
```

Clients talk to the router as if it were a single `mineru-api`; the router forwards tasks and balances load automatically.

## Rate Limiting & Concurrency

- `mineru-api` processes up to `max_concurrent_requests` tasks in parallel (configurable).
- Excess tasks queue (`pending` state with `queued_ahead` count).
- For high throughput, deploy `mineru-router` across multiple GPU nodes.
- Pipeline backend supports multi-threaded concurrent inference (thread-safe since v3.0).
