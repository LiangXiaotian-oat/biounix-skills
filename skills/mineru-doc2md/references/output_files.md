# MinerU Output Files Reference

MinerU produces several output files per input document. The structure differs between the **pipeline** backend and the **VLM/hybrid** backends (v2.5+). Read this carefully before building downstream applications on the JSON outputs.

## Directory Structure

After parsing `report.pdf` into `./output`:

```
output/
└── report/                        # One subfolder per input file
    ├── report.md                  # ← Main Markdown output
    ├── report_content_list.json   # Structured content list (RAG chunking)
    ├── report_middle.json         # Layout / intermediate JSON
    ├── report_origin.pdf          # (optional) original file copy
    └── images/                    # Extracted figures
        ├── img_0_0.png
        ├── img_1_2.png
        └── ...
```

For the API (`/tasks`), all of the above are zipped into `result.zip`.

## `*.md` — Markdown Output

The primary human-readable output. Key properties:

- **Reading order:** Follows human reading order (multi-column, complex layouts handled).
- **Headings:** `#`, `##`, `###` preserve document hierarchy.
- **Paragraphs:** Plain text; truncated paragraphs across pages are merged.
- **Formulas:** Inline as `$...$`, display as `$$...$$` in LaTeX.
- **Tables:** HTML `<table>` blocks (richer than Markdown pipe tables).
- **Images:** Referenced as `![](images/img_0_0.png)` with relative paths.
- **Lists:** Standard Markdown `-` / `1.` syntax.
- **Headers/footers/page numbers:** Automatically removed for semantic coherence.

Example:

```markdown
# Introduction

This paper presents a method for...

## Method

The equation $E = mc^2$ is fundamental. The system satisfies:

$$\nabla \cdot \mathbf{E} = \frac{\rho}{\varepsilon_0}$$

<table>
<thead><tr><th>Method</th><th>Accuracy</th></tr></thead>
<tbody>
<tr><td>Baseline</td><td>82.3%</td></tr>
<tr><td>Ours</td><td>95.1%</td></tr>
</tbody>
</table>

![Figure 1](images/img_0_0.png)
```

## `*_content_list.json` — Structured Content List

A JSON array of content blocks in reading order. **Format differs between backends in v2.5+.**

### Pipeline backend format

```json
[
  {
    "type": "text",
    "text": "Introduction",
    "text_level": 1,
    "page_idx": 0
  },
  {
    "type": "text",
    "text": "This paper presents...",
    "page_idx": 0
  },
  {
    "type": "image",
    "img_path": "images/img_0_0.png",
    "img_caption": ["Figure 1: System overview"],
    "img_footnote": [],
    "page_idx": 0
  },
  {
    "type": "table",
    "img_path": "images/img_0_1.png",
    "table_body": "<table>...</table>",
    "table_caption": ["Table 1: Results"],
    "table_footnote": [],
    "page_idx": 1
  },
  {
    "type": "equation",
    "text": "E = mc^2",
    "text_format": "latex",
    "page_idx": 0
  }
]
```

**Block types:** `text` · `image` · `table` · `equation` · `list`

### VLM / hybrid backend format (v2.5+)

The structure is similar but field names and nesting differ. **Not backward-compatible with pipeline.** Key differences:

- `type` values expanded (`title`, `image`, `table`, `formula`, `text`, `list`, `index`).
- Some fields renamed (e.g., `img_path` → `image_path` in some versions).
- Layout blocks include richer metadata (bbox, reading order index).

Always check the version-specific schema by parsing one sample file and inspecting keys before bulk processing.

## `*_middle.json` — Intermediate Layout JSON

The full layout analysis result, including:

- Page-level bounding boxes for every block
- Block types and confidence scores
- Reading order indices
- Span-level (text run) details
- Pre-OCR text and post-OCR text

Used for:

- Building custom visualization (layout/span visualization)
- Secondary development requiring layout geometry
- Debugging parsing quality

> **Warning:** The `middle.json` schema changed in v2.5 for VLM backends and is not backward-compatible. Pin your MinerU version if downstream code depends on it.

## `images/` — Extracted Figures

- Named `img_{page_idx}_{block_idx}.png`.
- Includes figures, charts, and table screenshots.
- Referenced by relative path in `.md`.
- For API, include `return_images=true` to get this folder.

## Visualization Outputs

When running locally (CLI/SDK), MinerU can also generate:

- `layout.pdf` — Layout visualization (colored boxes over each block type)
- `span.pdf` — Span visualization (text runs colored by type)
- `model_output.json` — Raw VLM model output (with `return_model_output=true`)

These are useful for quality confirmation but optional.

## Selecting Which Outputs to Return (API)

| Form field                  | Includes                 |
| --------------------------- | ------------------------ |
| `return_md=true`            | `*.md`                   |
| `return_content_list=true`  | `*_content_list.json`    |
| `return_middle_json=true`   | `*_middle.json`          |
| `return_model_output=true`  | `model_output.json`      |
| `return_images=true`        | `images/` folder         |
| `return_original_file=true` | Original input file copy |

Minimize transfers by requesting only what you need. For RAG, `return_md=true` + `return_content_list=true` + `return_images=true` is typical.

## File Naming Convention

All per-file outputs use the pattern `{original_filename_without_extension}_*`:

- `report.pdf` → `report.md`, `report_content_list.json`, `report_middle.json`
- `data.xlsx` → `data.md`, `data_content_list.json`, ...

For Office formats (DOCX/PPTX/XLSX), each sheet/slide/page becomes a section in the Markdown, but the output is still a single `.md` per input file.
