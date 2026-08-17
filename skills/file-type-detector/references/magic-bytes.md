# 魔数签名表（Magic Bytes）

读取文件头 **16 字节**（部分格式需 512 字节偏移，见注）即可覆盖绝大多数二进制格式。下表按 magic 前缀排序，比对时按**最长前缀优先**匹配，避免短前缀误命中。

## 办公文档

| type                 | magic (hex)                                                            | offset | mime                                                                        | 说明                                            |
| -------------------- | ---------------------------------------------------------------------- | ------ | --------------------------------------------------------------------------- | ----------------------------------------------- |
| `pdf`                | `25 50 44 46 2d` (`%PDF-`)                                             | 0      | `application/pdf`                                                           | PDF，版本 1.4–2.0                               |
| `ole2` (doc/xls/ppt) | `d0 cf 11 e0 a1 b1 1a e1`                                              | 0      | `application/x-ole-storage`                                                 | OLE2 复合文档，需进一步看内部流区分 doc/xls/ppt |
| `doc`                | OLE2 + 内含 `WordDocument` 流                                          | 0      | `application/msword`                                                        | 旧版 Word .doc                                  |
| `xls`                | OLE2 + 内含 `Workbook` 流                                              | 0      | `application/vnd.ms-excel`                                                  | 旧版 Excel .xls                                 |
| `ppt`                | OLE2 + 内含 `PowerPoint Document` 流                                   | 0      | `application/vnd.ms-powerpoint`                                             | 旧版 PowerPoint .ppt                            |
| `docx`               | `50 4b 03 04` + 内含 `word/document.xml`                               | 0      | `application/vnd.openxmlformats-officedocument.wordprocessingml.document`   | OOXML，ZIP 容器                                 |
| `xlsx`               | `50 4b 03 04` + 内含 `xl/workbook.xml`                                 | 0      | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`         | OOXML                                           |
| `pptx`               | `50 4b 03 04` + 内含 `ppt/presentation.xml`                            | 0      | `application/vnd.openxmlformats-officedocument.presentationml.presentation` | OOXML                                           |
| `odt`                | `50 4b 03 04` + 内含 `mimetypeapplication/vnd.oasis.opendocument.text` | 0      | `application/vnd.oasis.opendocument.text`                                   | ODF，mimetype 文件位于 ZIP 首项                 |
| `ods`                | 同上 + `...opendocument.spreadsheet`                                   | 0      | `application/vnd.oasis.opendocument.spreadsheet`                            | ODF 表格                                        |
| `odp`                | 同上 + `...opendocument.presentation`                                  | 0      | `application/vnd.oasis.opendocument.presentation`                           | ODF 演示                                        |
| `rtf`                | `7b 5c 72 74 66` (`{\rtf`)                                             | 0      | `application/rtf`                                                           | Rich Text Format                                |
| `wps`/`et`/`dps`     | OLE2 或 OOXML 变体                                                     | 0      | —                                                                           | WPS Office，按容器归入 doc/xls/ppt 族           |

**OOXML vs ODF 区分要点**：两者都是 ZIP（`50 4b 03 04`）容器，必须解压查看内部 `mimetype` 文件或 `word/`/`xl/`/`ppt/` 目录才能确定具体类型，不能仅凭 ZIP 头判定为 zip。

## 生物信息

| type                              | magic (hex)                             | offset | mime                       | 说明                                         |
| --------------------------------- | --------------------------------------- | ------ | -------------------------- | -------------------------------------------- |
| `bam`                             | `1f 8b 08` (BGZF/gzip)                  | 0      | `application/octet-stream` | BAM 是 BGZF 压缩，需解压后看首四字节 `BAM\1` |
| `bam-raw`                         | `42 41 4d 01` (`BAM\1`)                 | 0      | `application/octet-stream` | 未压缩 BAM（罕见）                           |
| `cram`                            | `43 52 41 4d` (`CRAM`)                  | 0      | `application/octet-stream` | CRAM v3                                      |
| `bcf`                             | `42 43 46` (`BCF`) + BGZF               | 0      | `application/octet-stream` | BCF = BGZF 压缩的 BCF2，解压后首三字节 `BCF` |
| `bcf2-raw`                        | `42 43 46 02` (`BCF\2`)                 | 0      | `application/octet-stream` | 未压缩 BCF2                                  |
| `bed.gz`/`vcf.gz`/`fa.gz`/`fq.gz` | `1f 8b 08`                              | 0      | `application/gzip`         | gzip 容器，需结合后缀或解压内容判定内部格式  |
| `bigwig`                          | `bb 01 07 00` (v1) / `bb 02 07 00` (v2) | 0      | `application/octet-stream` | bigWig                                       |
| `bigbed`                          | `bb 08 07 00` (v1) / `bb 09 07 00` (v2) | 0      | `application/octet-stream` | bigBed                                       |
| `2bit`                            | `5e 76 32 62 69 74` (`.2bit`)           | 0      | `application/octet-stream` | UCSC 2bit                                    |
| `cram-bam`                        | `43 52 41 4d`                           | 0      | —                          | 见 cram                                      |
| `fasta-index`                     | —                                       | —      | —                          | `.fai` 纯文本，由后缀判定                    |

**注意**：BAM/BCF/VCF.gz 都可能是 gzip（`1f 8b 08`），此时**不能仅凭 gzip 头判定为 gzip**，应优先结合后缀，或解压后嗅探内部魔数。识别策略：gzip 头命中时，进入"解压重试"分支。

## 图片

| type          | magic (hex)                                                                 | mime                        | 说明                                                           |
| ------------- | --------------------------------------------------------------------------- | --------------------------- | -------------------------------------------------------------- |
| `png`         | `89 50 4e 47 0d 0a 1a 0a`                                                   | `image/png`                 | PNG 8 字节签名                                                 |
| `jpg`/`jpeg`  | `ff d8 ff`                                                                  | `image/jpeg`                | JPEG SOI；后跟 `e0`(JFIF)/`e1`(EXIF)/`db`(原始)                |
| `gif`         | `47 49 46 38 37 61` / `47 49 46 38 39 61` (`GIF87a`/`GIF89a`)               | `image/gif`                 |                                                                |
| `bmp`         | `42 4d` (`BM`)                                                              | `image/bmp`                 |                                                                |
| `tiff`        | `49 49 2a 00` (LE) / `4d 4d 00 2a` (BE)                                     | `image/tiff`                | 小端/大端                                                      |
| `webp`        | `52 49 46 46 ?? ?? ?? ?? 57 45 42 50` (`RIFF....WEBP`)                      | `image/webp`                | RIFF 容器，offset 8 处 `WEBP`                                  |
| `ico`         | `00 00 01 00`                                                               | `image/x-icon`              |                                                                |
| `cur`         | `00 00 02 00`                                                               | `image/x-icon`              | 光标                                                           |
| `heic`/`heif` | `?? ?? ?? ?? 66 74 79 70 68 65 69 63` / `...68 65 69 78` / `...6d 69 66 31` | `image/heic`                | ISO BMFF 容器，offset 4 处 `ftyp` + brand `heic`/`heix`/`mif1` |
| `avif`        | `?? ?? ?? ?? 66 74 79 70 61 76 69 66` / `...61 76 69 73`                    | `image/avif`                | brand `avif`/`avis`                                            |
| `svg`         | —                                                                           | `image/svg+xml`             | 纯文本，由内容嗅探 `<?xml`/`<svg`                              |
| `psd`         | `38 42 50 53` (`8BPS`)                                                      | `image/vnd.adobe.photoshop` |                                                                |

## 音频

| type              | magic (hex)                                            | mime             | 说明                           |
| ----------------- | ------------------------------------------------------ | ---------------- | ------------------------------ |
| `mp3`             | `49 44 33` (`ID3`) 或 `ff fb`/`ff f3`/`ff f2` (帧同步) | `audio/mpeg`     | ID3v2 标签或 MPEG 帧头         |
| `wav`             | `52 49 46 46 ?? ?? ?? ?? 57 41 56 45` (`RIFF....WAVE`) | `audio/wav`      | RIFF + `WAVE`                  |
| `flac`            | `66 4c 61 43` (`fLaC`)                                 | `audio/flac`     |                                |
| `ogg`             | `4f 67 67 53` (`OggS`)                                 | `audio/ogg`      | Ogg 容器（可能含 Vorbis/Opus） |
| `aac`             | `ff f1` / `ff f9` (ADTS)                               | `audio/aac`      |                                |
| `m4a`/`mp4-audio` | `?? ?? ?? ?? 66 74 79 70 4d 34 41 20` (brand `M4A `)   | `audio/mp4`      | ISO BMFF                       |
| `aiff`            | `46 4f 52 4d` (`FORM`) + `41 49 46 46` (`AIFF`)        | `audio/aiff`     |                                |
| `wma`             | `30 26 b2 75 8e 66 cf 11` (ASF)                        | `audio/x-ms-wma` | ASF 容器                       |

## 视频

| type         | magic (hex)                                                                 | mime                              | 说明                                          |
| ------------ | --------------------------------------------------------------------------- | --------------------------------- | --------------------------------------------- |
| `mp4`        | `?? ?? ?? ?? 66 74 79 70 69 73 6f 6d` / `...6d 70 34 32` / `...66 34 76 31` | `video/mp4`                       | ISO BMFF，brand `isom`/`mp42`/`f4v`/`M4V ` 等 |
| `mkv`/`webm` | `1a 45 df a3` (EBML)                                                        | `video/x-matroska` / `video/webm` | EBML 容器，需查 `DocType` 元素区分 mkv/webm   |
| `avi`        | `52 49 46 46 ?? ?? ?? ?? 41 56 49 20` (`RIFF....AVI `)                      | `video/x-msvideo`                 |                                               |
| `mov`        | `?? ?? ?? ?? 6d 6f 6f 76` / `...66 72 65 65` / `...6d 64 61 74`             | `video/quicktime`                 | QuickTime 容器                                |
| `flv`        | `46 4c 56 01` (`FLV`)                                                       | `video/x-flv`                     |                                               |
| `wmv`        | `30 26 b2 75 8e 66 cf 11` (ASF)                                             | `video/x-ms-wmv`                  | 同 ASF                                        |
| `mpeg`/`mpg` | `00 00 01 ba` / `00 00 01 b3`                                               | `video/mpeg`                      | MPEG-PS/ES                                    |
| `webm`       | EBML + DocType `webm`                                                       | `video/webm`                      | 见 mkv                                        |

## 压缩包 / 归档

| type          | magic (hex)                                                      | mime                          | 说明                          |
| ------------- | ---------------------------------------------------------------- | ----------------------------- | ----------------------------- |
| `zip`         | `50 4b 03 04` / `50 4b 05 06` (空) / `50 4b 07 08` (跨段)        | `application/zip`             | 也是 OOXML/ODF/JAR/APK 的容器 |
| `gzip`        | `1f 8b 08`                                                       | `application/gzip`            | 也是 BAM/BCF.gz 的容器        |
| `rar`         | `52 61 72 21 1a 07 00` (RAR5) / `52 61 72 21 1a 07 01 00` (RAR4) | `application/vnd.rar`         |                               |
| `7z`          | `37 7a bc af 27 1c`                                              | `application/x-7z-compressed` |                               |
| `tar`         | `75 73 74 61 72` (`ustar`)                                       | `application/x-tar`           | offset **257** 处 `ustar`     |
| `bz2`         | `42 5a 68` (`BZh`)                                               | `application/x-bzip2`         |                               |
| `xz`          | `fd 37 7a 58 5a 00`                                              | `application/x-xz`            |                               |
| `zst`         | `28 b5 2f fd`                                                    | `application/zstd`            |                               |
| `lz4`         | `04 22 4d 18`                                                    | `application/x-lz4`           |                               |
| `lzma`/`lzip` | `4c 5a 49 50` (`LZIP`)                                           | —                             |                               |

## 数据库 / 二进制数据

| type      | magic (hex)                    | mime                             | 说明                                  |
| --------- | ------------------------------ | -------------------------------- | ------------------------------------- |
| `sqlite`  | `53 51 4c 69 74 65` (`SQLite`) | `application/vnd.sqlite3`        | offset 16 处版本                      |
| `parquet` | `50 41 52 31` (`PAR1`)         | `application/vnd.apache.parquet` |                                       |
| `duckdb`  | `44 55 43 4b` (`DUCK`)         | —                                | DuckDB 数据库文件                     |
| `leveldb` | —                              | —                                | 无固定魔数，按目录 `.ldb`/`.log` 判定 |
| `hdf5`    | `89 48 44 46 0d 0a 1a 0a`      | `application/x-hdf5`             |                                       |
