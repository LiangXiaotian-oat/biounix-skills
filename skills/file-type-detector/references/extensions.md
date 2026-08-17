# 扩展名推断表（Extension Mapping）

当魔数嗅探无结果时（纯文本格式无固定魔数），按文件扩展名推断。**仅当魔数无命中或文件为纯文本时启用此分支**，避免对二进制文件误判。

## 文本格式（无魔数，依赖扩展名或内容）

| 扩展名                                    | type        | mime                                     | 备注                        |
| ----------------------------------------- | ----------- | ---------------------------------------- | --------------------------- |
| `.fa`/`.fasta`/`.fa.gz`/`.fna`            | `fasta`     | `application/fasta`                      |                             |
| `.fq`/`.fastq`/`.fq.gz`                   | `fastq`     | `application/fastq`                      |                             |
| `.sam`                                    | `sam`       | `text/x-sam`                             |                             |
| `.bed`                                    | `bed`       | `text/x-bed`                             |                             |
| `.bedpe`/`.bed12`                         | `bed`       | `text/x-bed`                             |                             |
| `.gff`/`.gff3`                            | `gff`       | `text/x-gff`                             |                             |
| `.gtf`                                    | `gff`       | `text/x-gff`                             | 按父类归 gff                |
| `.vcf`                                    | `vcf`       | `text/x-vcf`                             |                             |
| `.maf`                                    | `maf`       | `text/x-maf`                             | Mutation Annotation Format  |
| `.csv`                                    | `csv`       | `text/csv`                               |                             |
| `.tsv`/`.tab`/`.txt`                      | `tsv`/`txt` | `text/tab-separated-values`/`text/plain` | `.txt` 时需内容嗅探判定结构 |
| `.json`                                   | `json`      | `application/json`                       |                             |
| `.jsonl`/`.ndjson`                        | `jsonl`     | `application/x-ndjson`                   |                             |
| `.xml`                                    | `xml`       | `application/xml`                        |                             |
| `.yaml`/`.yml`                            | `yaml`      | `application/x-yaml`                     |                             |
| `.toml`                                   | `toml`      | `application/toml`                       |                             |
| `.ini`/`.cfg`/`.conf`                     | `ini`       | `text/plain`                             |                             |
| `.md`/`.markdown`                         | `markdown`  | `text/markdown`                          |                             |
| `.html`/`.htm`                            | `html`      | `text/html`                              |                             |
| `.css`/`.js`/`.ts`/`.py`/`.r`/`.sh`/`.pl` | `code`      | `text/x-script`                          | 编程语言源码                |
| `.sam`/`.bam`/`.cram`                     | 见上        | —                                        |                             |

## 后缀回退时的优先级

1. **若已解压 gzip**：按内部流的首行/魔数重新判定，**不要**直接用 `.gz` 去除后的后缀，因为 `.vcf.gz`/`.bed.gz`/`fa.gz` 内部格式不同。
2. **大小写不敏感**：`.FASTA` == `.fasta`。
3. **复合扩展名**：`.tar.gz` → `gzip` 容器，解压后再按 `tar` 处理；`.vcf.gz` → 先 gzip 再 vcf。

## 后缀与魔数冲突时

- **二进制格式**（bam/bcf/cram/png/jpg...）：**魔数优先**，后缀仅作辅助。例如 `.bam` 但魔数非 BGZF → 报告"可能是损坏的 BAM 或非 BAM"。
- **文本格式**（fasta/fastq/sam/vcf/bed/gff）：**扩展名优先**（因无魔数），但需用内容嗅探验证首行是否合法（如 FASTA 首行是否以 `>` 开头）。
- **gzip 容器**：必须解压后重新嗅探，**不能**仅凭 `.gz` 后缀判定内部格式。
