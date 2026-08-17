#!/usr/bin/env python3
"""Parse a document via a remote MinerU API server (mineru-api or mineru-router).

Submits a file to `POST /tasks`, polls `GET /tasks/{id}` until done, then
downloads the result zip and extracts it. Uses only stdlib + httpx (or urllib
fallback) so it runs anywhere without the full MinerU install.

Usage:
    python api_parse.py <input_file> <output_dir> --api-url <url> [options]

Examples:
    python api_parse.py doc.pdf ./out --api-url http://localhost:8000
    python api_parse.py scan.png ./out --api-url http://mineru.local:8000 \\
        --backend vlm-engine --effort high
    python api_parse.py report.pdf ./out --api-url https://mineru.example.com \\
        --timeout 600 --poll-interval 5
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import zipfile
from pathlib import Path
from typing import Any
from urllib.parse import urljoin


# ---------------------------------------------------------------------------
# HTTP layer — prefer httpx, fall back to urllib.request
# ---------------------------------------------------------------------------
try:
    import httpx  # type: ignore
    _HAVE_HTTPX = True
except ImportError:
    import urllib.request
    import urllib.error
    _HAVE_HTTPX = False


class HttpClient:
    """Tiny wrapper that uses httpx if available, else urllib."""

    def __init__(self, base_url: str, timeout: float = 300.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        if _HAVE_HTTPX:
            self._client = httpx.Client(timeout=timeout)

    def get(self, path: str) -> tuple[int, Any]:
        url = urljoin(self.base_url + "/", path.lstrip("/"))
        if _HAVE_HTTPX:
            r = self._client.get(url)
            return r.status_code, _parse_body(r)
        else:
            req = urllib.request.Request(url, method="GET")
            return _urllib_send(req)

    def post_multipart(self, path: str, fields: dict[str, Any],
                       file_path: Path) -> tuple[int, Any]:
        url = urljoin(self.base_url + "/", path.lstrip("/"))
        if _HAVE_HTTPX:
            with file_path.open("rb") as f:
                files = {"file": (file_path.name, f, "application/octet-stream")}
                data = {k: (v if v is not None else "") for k, v in fields.items()}
                r = self._client.post(url, data=data, files=files)
            return r.status_code, _parse_body(r)
        else:
            return _urllib_post_multipart(url, fields, file_path, self.timeout)

    def download(self, path: str, dest: Path) -> None:
        url = urljoin(self.base_url + "/", path.lstrip("/"))
        if _HAVE_HTTPX:
            with self._client.stream("GET", url) as r:
                r.raise_for_status()
                with dest.open("wb") as f:
                    for chunk in r.iter_bytes():
                        f.write(chunk)
        else:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310
                with dest.open("wb") as f:
                    f.write(resp.read())


def _parse_body(response: Any) -> Any:
    try:
        return response.json()
    except Exception:
        return {"raw": getattr(response, "text", str(response))}


def _urllib_send(req: urllib.request.Request) -> tuple[int, Any]:
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:  # noqa: S310
            body = resp.read().decode("utf-8", errors="replace")
            try:
                return resp.status, json.loads(body)
            except json.JSONDecodeError:
                return resp.status, {"raw": body}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(body)
        except json.JSONDecodeError:
            return e.code, {"raw": body}


def _urllib_post_multipart(url: str, fields: dict[str, Any], file_path: Path,
                           timeout: float) -> tuple[int, Any]:
    """Build a multipart/form-data body by hand (urllib has no helper)."""
    boundary = "----MinerUBoundary" + str(int(time.time() * 1000))
    lines: list[bytes] = []
    for k, v in fields.items():
        if v is None:
            continue
        lines.append(f"--{boundary}\r\n".encode())
        lines.append(
            f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode()
        )
        lines.append(f"{v}\r\n".encode())
    # File part
    lines.append(f"--{boundary}\r\n".encode())
    lines.append(
        f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'
        .encode()
    )
    lines.append(b"Content-Type: application/octet-stream\r\n\r\n")
    lines.append(file_path.read_bytes())
    lines.append(f"\r\n--{boundary}--\r\n".encode())
    body = b"".join(lines)
    req = urllib.request.Request(  # noqa: S310
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    return _urllib_send(req)


# ---------------------------------------------------------------------------
# MinerU API client
# ---------------------------------------------------------------------------
BACKEND_CHOICES = ["pipeline", "vlm-engine", "hybrid-engine",
                   "vlm-http-client", "hybrid-http-client"]
METHOD_CHOICES = ["auto", "txt", "ocr"]
EFFORT_CHOICES = ["medium", "high"]


def wait_for_task(client: HttpClient, task_id: str, poll_interval: float,
                  timeout: float) -> dict[str, Any]:
    """Poll GET /tasks/{id} until state is done or timeout."""
    deadline = time.time() + timeout
    last_status: dict[str, Any] = {}
    while time.time() < deadline:
        code, body = client.get(f"/tasks/{task_id}")
        if code != 200:
            raise RuntimeError(f"GET /tasks/{task_id} → HTTP {code}: {body}")
        last_status = body if isinstance(body, dict) else {"raw": body}
        state = last_status.get("state") or last_status.get("status") or ""
        # MinerU uses states: pending / running / done / failed
        if state in ("done", "succeed", "success", "completed"):
            return last_status
        if state in ("failed", "error"):
            raise RuntimeError(
                f"Task {task_id} failed: {last_status.get('error', last_status)}"
            )
        elapsed = int(time.time() - (deadline - timeout))
        print(f"  ... state={state} ({elapsed}s elapsed)", flush=True)
        time.sleep(poll_interval)
    raise TimeoutError(
        f"Task {task_id} did not finish within {timeout}s. Last: {last_status}"
    )


def download_result(client: HttpClient, task_id: str, output_dir: Path) -> Path:
    """Download the result zip and extract it into output_dir."""
    zip_path = output_dir / f"{task_id}.zip"
    client.download(f"/tasks/{task_id}/result", zip_path)
    if not zipfile.is_zipfile(zip_path):
        # Maybe the server returned JSON directly
        print(f"  Note: result is not a zip; saved as {zip_path}")
        return zip_path
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(output_dir)
    zip_path.unlink()
    return output_dir


def run(args: argparse.Namespace) -> int:
    input_file = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve()
    if not input_file.is_file():
        print(f"Error: input not found: {input_file}", file=sys.stderr)
        return 1
    output_dir.mkdir(parents=True, exist_ok=True)

    client = HttpClient(args.api_url, timeout=args.timeout)

    # 1. Health check
    code, body = client.get("/health")
    if code != 200:
        print(f"Error: API server unhealthy (HTTP {code}): {body}",
              file=sys.stderr)
        return 1
    print(f"✓ API server reachable: {args.api_url}")

    # 2. Build form fields (only non-None are sent)
    fields: dict[str, Any] = {"backend": args.backend}
    if args.method:
        fields["parse_method"] = args.method
    if args.effort and args.backend.startswith("hybrid"):
        fields["effort"] = args.effort
    if args.lang and args.backend == "pipeline":
        fields["language"] = args.lang
    if args.start is not None:
        fields["start_page"] = args.start
    if args.end is not None:
        fields["end_page"] = args.end
    if args.formula is not None:
        fields["enable_formula"] = "true" if args.formula else "false"
    if args.table is not None:
        fields["enable_table"] = "true" if args.table else "false"
    # Default: request md + content_list + images
    fields["return_md"] = "true"
    fields["return_content_list"] = "true"
    fields["return_images"] = "true"
    fields["return_middle_json"] = "true"

    # 3. Submit
    print(f"Submitting {input_file.name} ({input_file.stat().st_size} bytes)...")
    code, body = client.post_multipart("/tasks", fields, input_file)
    if code not in (200, 201, 202):
        print(f"Error: POST /tasks → HTTP {code}: {body}", file=sys.stderr)
        return 1
    task_id = (body or {}).get("task_id") or (body or {}).get("id")
    if not task_id:
        print(f"Error: no task_id in response: {body}", file=sys.stderr)
        return 1
    print(f"✓ Task submitted: {task_id}")

    # 4. Poll
    print("Waiting for completion...")
    final = wait_for_task(client, task_id, args.poll_interval, args.timeout)
    print(f"✓ Task done: {final.get('state', 'done')}")

    # 5. Download + extract
    print("Downloading result...")
    download_result(client, task_id, output_dir)

    # 6. Report
    md_files = list(output_dir.rglob("*.md"))
    if md_files:
        print(f"\n✓ Markdown output(s):")
        for md in md_files:
            print(f"  {md}")
    else:
        print(f"\n✓ Done. Output in: {output_dir}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Parse a document via a remote MinerU API server.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("input", help="Input file")
    parser.add_argument("output", help="Output directory")
    parser.add_argument("--api-url", required=True,
                        help="MinerU API base URL (e.g. http://localhost:8000)")
    parser.add_argument("--backend", choices=BACKEND_CHOICES,
                        default="pipeline")
    parser.add_argument("--method", choices=METHOD_CHOICES, default=None)
    parser.add_argument("--effort", choices=EFFORT_CHOICES, default=None)
    parser.add_argument("--lang", default=None,
                        help="OCR language (pipeline only)")
    parser.add_argument("-s", "--start", type=int, default=None)
    parser.add_argument("-e", "--end", type=int, default=None)
    parser.add_argument("-f", "--formula", dest="formula",
                        type=lambda x: x.lower() in ("true", "1", "yes"),
                        default=None)
    parser.add_argument("-t", "--table", dest="table",
                        type=lambda x: x.lower() in ("true", "1", "yes"),
                        default=None)
    parser.add_argument("--timeout", type=float, default=1800.0,
                        help="Total wait timeout in seconds (default 1800)")
    parser.add_argument("--poll-interval", type=float, default=3.0,
                        help="Seconds between status polls (default 3)")
    return run(parser.parse_args())


if __name__ == "__main__":
    sys.exit(main())
