---
name: file-type-detector
description: 通过后缀、文件头魔数、内容特征三层方法识别文件真实类型，覆盖办公文档、生物信息（FASTQ/FASTA/BAM/VCF/CRAM/BED/GFF）、图片、音视频、压缩包、数据库等。
triggers:
  - 文件类型
  - 识别文件
  - 文件格式
  - magic number
  - 文件头
  - 文件后缀
  - detect file type
  - 文件签名
  - 判断文件
  - file signature
always_active: false
version: 2.0.0
category: foundation
author: biounix
---

# 文件类型识别

三层递进策略判定文件真实类型，**每层有命中即停止**，但 gzip 容器需解压后重新嗅探。

## 识别流程

1. **第一层 · 魔数签名**：读文件头 16 字节（部分格式需 offset 257，如 tar）。按**最长前缀优先**匹配。
   - 完整魔数表见 `references/magic-bytes.md`，覆盖办公文档、生信、图片、音视频、压缩包、数据库。
   - **需要时调用** `skill_read_resource(skill_name="file-type-detector", relative_path="references/magic-bytes.md")` 加载。
   - 关键提示：BAM/BCF/VCF.gz 都是 `1f 8b 08`（BGZF/gzip），**不能仅凭 gzip 头判定**，需结合后缀或解压后嗅探。

2. **第二层 · 扩展名推断**：魔数无命中或纯文本时启用。
   - 完整后缀表见 `references/extensions.md`，**需要时调用** `skill_read_resource(...)` 加载。
   - 二进制格式魔数优先于后缀；文本格式扩展名优先但需内容嗅探验证。

3. **第三层 · 内容嗅探**：纯文本格式（无魔数）读前 2KB 按首行模式判定。
   - 完整嗅探表见 `references/content-sniffing.md`，**需要时调用** `skill_read_resource(...)` 加载。
   - fasta 首字符 `>`；fastq 首字符 `@`（4 行一组）；SAM header `@HD`/`@SQ`；VCF 首行 `##fileformat=VCF`；BED ≥3 列坐标为整数。

## gzip 容器处理（重要）

`.gz` 文件**必须解压后重新嗅探**，不能直接判定为 gzip：

- `.vcf.gz` → 解压后首行 `##fileformat=VCF` → `vcf.gz`
- `.bam` → 解压后首四字节 `BAM\1` → `bam`
- `.fa.gz`/`.bed.gz` → 解压后按内容嗅探

## 输出格式

返回 JSON：

```json
{
  "file": "example.bam",
  "type": "bam",
  "mime": "application/octet-stream",
  "method": "magic", // magic | extension | sniffing
  "confidence": "high", // high | medium | low
  "note": "BGZF 压缩的 BAM，解压后首四字节 BAM\\1"
}
```

## 使用建议

- 本 SKILL.md 只含识别流程，完整魔数表/后缀表/嗅探表在 `references/` 下。
- 遇到不确定的魔数或需完整签名表时，**主动调用** `skill_read_resource(skill_name="file-type-detector", relative_path="references/magic-bytes.md")` 按需加载。
- 对 `.gz`/`.bam`/`.bcf` 等 BGZF 容器，务必走"解压重试"分支。
