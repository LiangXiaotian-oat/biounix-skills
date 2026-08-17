---
name: oatbio-gene-search
description: 在 OatBioDB (www.waooat.cn) 上查找燕麦基因组基因的标准化流程，包括导航到 GENE 页面、搜索基因 ID、进入详情页提取基因基本信息（染色体位置、链、长度）、NR/KOG/KEGG/GO/Pfam 注释、直系同源基因，以及获取蛋白/CDS 序列。当用户需要查询燕麦基因信息、获取燕麦基因注释或序列时使用。触发关键词：OatBioDB、燕麦基因、oat gene、waooat、AVESA 基因 ID 查询。
triggers:
  - OatBioDB
  - 燕麦基因
  - oat gene
  - waooat
  - AVESA
  - 燕麦基因组
  - oat genome gene search
always_active: false
version: null
category: null
author: GLM-5.2 + BioUnix
---
Search and extract gene information from OatBioDB (www.waooat.cn), the oat genome database.

## Steps

1. **Navigate to the site**: Open `https://www.waooat.cn` with `browser_navigate`.

2. **Click the GENE nav link**: The GENE link in the navigation bar has an empty `href`, so use `browser_eval` to find and click it via JS:
   ```js
   var links = document.querySelectorAll('a');
   for (var l of links) { if (l.textContent.trim() === 'GENE') { l.click(); break; } }
   ```
   This navigates to `/gene/` page.

3. **Search for a gene ID**: In the search box `input[type="text"]` (placeholder="Gene name"), enter the gene ID (e.g., `AVESA.00400a.r2.1Ag0006977`). Use `browser_fill` or `browser_eval` to set the value, then click the search button `button[aria-label="search"]`.

4. **Click the gene in the results table**: Use `browser_click` with selector `span.css-1awq8d1`, or locate a `td` containing the AVESA text and click it. This navigates to `/gene/{id}/` detail page.

5. **Extract gene details**: Use `browser_extract` on the detail page. The page contains:
   - Gene basic info: gene name, genome, chromosome position, strand, length
   - Annotations: NR, KOG, KEGG pathway, GO terms, Pfam domains
   - Orthologous genes list

6. **Get protein or CDS sequence (optional)**: On the detail page:
   - Select a transcript from the transcript dropdown (e.g., `AVESA.00400a.r2.1Ag0006977.1`)
   - Select sequence type from the Type dropdown (`Protein` or `CDS`)
   - Click the `Get` button (`button.MuiButton-containedError` or similar)
   - Extract the sequence from the `textarea` element via `browser_eval`:
     ```js
     document.querySelectorAll('textarea')[0].value;
     ```
   - The sequence is in FASTA format (header line starting with `>` followed by sequence).

## When to use

Use when a user asks to look up an oat gene on OatBioDB, retrieve oat gene annotations, or fetch oat protein/CDS sequences by gene ID (AVESA.* format).