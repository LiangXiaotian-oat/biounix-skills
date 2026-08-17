# MinerU Python SDK Reference

MinerU's Python API lives in `mineru.cli.common`. The two entry points are `do_parse` (synchronous, pipeline backend) and `aio_do_parse` (async, all backends).

## `do_parse` — Synchronous Parsing

Used by the `pipeline` backend. Runs in the current thread.

```python
from mineru.cli.common import do_parse

do_parse(
    output_dir: str,              # Output directory (created if missing)
    input_file_path: str,         # Input file path
    parse_method: str = "auto",   # "auto" | "txt" | "ocr"
    backend: str = "pipeline",    # must be "pipeline" for sync
    f: bool = True,               # formula parsing enabled
    t: bool = True,               # table parsing enabled
    start_page_id: int = 0,       # 0-based start page
    end_page_id: int | None = None,  # None = to end
    lang: str = "ch",             # OCR language (pipeline only)
    model_dir: str | None = None, # custom model directory
    device: str | None = None,    # "cpu" / "cuda" / "mps"
)
```

### Example: Pipeline on CPU

```python
from mineru.cli.common import do_parse

do_parse(
    output_dir="./output",
    input_file_path="document.pdf",
    parse_method="auto",
    backend="pipeline",
    f=True,
    t=True,
    lang="ch",
    device="cpu",
)
# Output: ./output/document/document.md
```

## `aio_do_parse` — Async Parsing

Used by `vlm-engine`, `hybrid-engine`, and `*-http-client` backends. Must be awaited.

```python
import asyncio
from mineru.cli.common import aio_do_parse

async def main():
    await aio_do_parse(
        output_dir="./output",
        input_file_path="document.pdf",
        parse_method="auto",
        backend="hybrid-engine",
        effort="medium",            # "medium" | "high" (hybrid only)
        f=True,
        t=True,
        start_page_id=0,
        end_page_id=None,
        lang="ch",
        server_url=None,            # required for *-http-client backends
        model_dir=None,
        device=None,
    )

asyncio.run(main())
```

## API Client (REST)

For programmatic access to a running `mineru-api` server, use the `mineru.cli.api_client` module. This is what `demo/demo.py` uses.

```python
import asyncio
from pathlib import Path
from mineru.cli import api_client as _api_client

async def parse_via_api(input_path: str, output_dir: str, api_url: str | None = None):
    input_files = [Path(input_path).resolve()]
    output_path = Path(output_dir).resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    form_data = _api_client.build_parse_request_form_data(
        lang_list=["ch"],
        backend="pipeline",
        effort="medium",
        parse_method="auto",
        formula_enable=True,
        table_enable=True,
        image_analysis=True,
        server_url=None,
        start_page_id=0,
        end_page_id=None,
        return_md=True,
        return_middle_json=False,
        return_model_output=False,
        return_content_list=False,
        return_images=True,
        response_format_zip=True,
        return_original_file=False,
    )

    upload_assets = [
        _api_client.UploadAsset(path=f, upload_name=f.name)
        for f in input_files
    ]

    import httpx
    async with httpx.AsyncClient(
        timeout=_api_client.build_http_timeout(),
        follow_redirects=True,
    ) as http_client:
        # Use existing server or start a local one
        if api_url is None:
            local_server = _api_client.LocalAPIServer()
            base_url = local_server.start()
            await _api_client.wait_for_local_api_ready(http_client, local_server)
        else:
            server_health = await _api_client.fetch_server_health(
                http_client,
                _api_client.normalize_base_url(api_url),
            )
            base_url = server_health.base_url

        # Submit task
        submit_response = await _api_client.submit_parse_task(
            base_url=base_url,
            upload_assets=upload_assets,
            form_data=form_data,
        )
        print(f"task_id: {submit_response.task_id}")

        # Wait for completion
        await _api_client.wait_for_task_result(
            client=http_client,
            submit_response=submit_response,
            task_label=f"{len(input_files)} file(s)",
        )

        # Download & extract result
        result_zip_path = await _api_client.download_result_zip(
            client=http_client,
            submit_response=submit_response,
            task_label=f"{len(input_files)} file(s)",
        )
        _api_client.safe_extract_zip(result_zip_path, output_path)
        result_zip_path.unlink(missing_ok=True)

    print(f"Extracted result to: {output_path}")

asyncio.run(parse_via_api("document.pdf", "./output", api_url=None))
```

## Supported Input Suffixes

```python
from mineru.cli.common import image_suffixes, office_suffixes, pdf_suffixes

# pdf_suffixes:   {".pdf"}
# image_suffixes: {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}
# office_suffixes: {".docx", ".pptx", ".xlsx"}
```

## Batch Processing Pattern

```python
import asyncio
from pathlib import Path
from mineru.cli.common import image_suffixes, office_suffixes, pdf_suffixes, aio_do_parse

SUPPORTED = set(pdf_suffixes + image_suffixes + office_suffixes)

async def batch_parse(input_dir: str, output_dir: str, backend: str = "pipeline"):
    input_path = Path(input_dir).resolve()
    output_path = Path(output_dir).resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    files = sorted(
        f for f in input_path.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED
    )

    for file in files:
        print(f"Parsing {file.name}...")
        try:
            await aio_do_parse(
                output_dir=str(output_path),
                input_file_path=str(file),
                backend=backend,
                parse_method="auto",
                f=True,
                t=True,
            )
            print(f"  ✓ {file.name}")
        except Exception as e:
            print(f"  ✗ {file.name}: {e}")

asyncio.run(batch_parse("./docs", "./output", "pipeline"))
```

## Error Handling

```python
from mineru.cli.common import aio_do_parse

try:
    await aio_do_parse(
        output_dir="./out",
        input_file_path="doc.pdf",
        backend="hybrid-engine",
    )
except FileNotFoundError as e:
    # Input file missing
    print(f"File not found: {e}")
except RuntimeError as e:
    # Backend crashed (OOM, model load failure, etc.)
    print(f"Parsing failed: {e}")
except Exception as e:
    # Network error (http-client), model download, etc.
    print(f"Error: {e}")
```

## Common Parameters Reference

| Parameter              | Type           | Default           | Applies to         | Notes                             |
| ---------------------- | -------------- | ----------------- | ------------------ | --------------------------------- |
| `output_dir`           | `str`          | —                 | all                | Created if missing                |
| `input_file_path`      | `str`          | —                 | all                | File or (CLI only) directory      |
| `parse_method`         | `str`          | `"auto"`          | pipeline, hybrid\* | `auto` / `txt` / `ocr`            |
| `backend`              | `str`          | `"hybrid-engine"` | all                | See CLI reference                 |
| `effort`               | `str`          | `"medium"`        | hybrid\*           | `medium` / `high`                 |
| `f` / `formula_enable` | `bool`         | `True`            | all                | Formula → LaTeX                   |
| `t` / `table_enable`   | `bool`         | `True`            | all                | Table → HTML                      |
| `start_page_id`        | `int`          | `0`               | all                | 0-based                           |
| `end_page_id`          | `int\|None`    | `None`            | all                | None = to end                     |
| `lang` / `lang_list`   | `str` / `list` | `"ch"`            | pipeline           | OCR language hint                 |
| `device`               | `str\|None`    | `None`            | all                | `cpu` / `cuda` / `mps` / `cuda:0` |
| `server_url`           | `str\|None`    | `None`            | \*-http-client     | OpenAI-compatible URL             |
| `model_dir`            | `str\|None`    | `None`            | all                | Custom model path                 |
| `image_analysis`       | `bool`         | `True`            | vlm, hybrid        | Needs `effort=high` for hybrid    |
