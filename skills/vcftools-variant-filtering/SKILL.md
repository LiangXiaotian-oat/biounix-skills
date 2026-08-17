---
name: vcftools-variant-filtering
description: 使用 vcftools 对 VCF 变异位点进行标准化过滤的完整流程，覆盖质量过滤、缺失率、MAF、HWE、SNP/Indel分离、去重、区间过滤、样本过滤共8种操作。当用户需要对 VCF/VCF.gz 文件进行变异位点质量控制、 genotype filtering、variant QC、或提到 vcftools、max-missing、maf、hwe、minQ 等关键词时触发。
triggers:
  - vcftools
  - VCF过滤
  - vcf过滤
  - 变异过滤
  - variant filtering
  - max-missing
  - maf
  - hwe
  - minQ
  - 变异质量控制
  - variant QC
  - bgzip
  - tabix
always_active: false
version: null
category: other
author: GLM-5.2 + BioUnix
---
# vcftools VCF Variant Filtering Pipeline

## Core Principles
- Default output mode: pipe through bgzip to produce compressed VCF.gz
- Command pattern: `vcftools --gzvcf <input.vcf.gz> [filter params] --recode --recode-INFO-all --stdout | bgzip -c > <output.vcf.gz>`
- Use `--gzvcf` for compressed input, `--vcf` for plain VCF
- Always include `--recode --recode-INFO-all` to preserve all INFO fields
- Embed filter parameters in output filename for traceability, e.g. `sample1_snp_M2m2_dp2_50het5miss20maf005.vcf.gz`

## 8 Filter Operations

### 1. Quality Filtering
```
vcftools --gzvcf input.vcf.gz --minQ 30 --min-meanDP 2 --max-meanDP 50 --recode --recode-INFO-all --stdout | bgzip -c > output_q30_dp2_50.vcf.gz
```

### 2. Missing Rate Filtering
- Use `--max-missing 0.8` (recommended range 0.8–0.9)
- Value is proportion of samples with data (0.8 = allow up to 20% missing)
```
vcftools --gzvcf input.vcf.gz --max-missing 0.8 --recode --recode-INFO-all --stdout | bgzip -c > output_miss08.vcf.gz
```

### 3. MAF Filtering
```
vcftools --gzvcf input.vcf.gz --maf 0.05 --max-maf 0.95 --recode --recode-INFO-all --stdout | bgzip -c > output_maf005.vcf.gz
```

### 4. HWE Filtering
- Use `--hwe 0.001`
- Only effective for biallelic SNPs; run AFTER MAF filtering (low-frequency sites cause spurious HWE deviation)
```
vcftools --gzvcf input.vcf.gz --hwe 0.001 --recode --recode-INFO-all --stdout | bgzip -c > output_hwe001.vcf.gz
```

### 5. SNP / Indel Separation
- Keep SNPs only: `--remove-indels`
- Keep Indels only: `--keep-only-indels`
```
vcftools --gzvcf input.vcf.gz --remove-indels --recode --recode-INFO-all --stdout | bgzip -c > output_snp.vcf.gz
```

### 6. Remove Duplicate Variants
```
vcftools --gzvcf input.vcf.gz --remove-duplicates --recode --recode-INFO-all --stdout | bgzip -c > output_dedup.vcf.gz
```

### 7. Region / Chromosome Filtering
- By chromosome: `--chr <chr>` or `--not-chr <chr>`
- By range: `--chr <chr> --from-bp <start> --to-bp <end>`
- By BED file: `--bed <regions.bed>`
```
vcftools --gzvcf input.vcf.gz --chr 1 --from-bp 1000000 --to-bp 2000000 --recode --recode-INFO-all --stdout | bgzip -c > output_chr1_1Mb_2Mb.vcf.gz
```

### 8. Sample Filtering
- Keep samples: `--keep <sample_list.txt>` (one sample per line)
- Remove samples: `--remove <sample_list.txt>`
```
vcftools --gzvcf input.vcf.gz --keep samples_to_keep.txt --recode --recode-INFO-all --stdout | bgzip -c > output_keepsamples.vcf.gz
```

## Combined Filtering Pipeline (Recommended Order)
1. Remove duplicates → 2. SNP/Indel separation → 3. Quality filtering → 4. Depth filtering → 5. Missing rate → 6. MAF → 7. HWE

Rationale: HWE runs last (after MAF) because low-frequency variants produce false HWE deviations.

### Example Combined Command
```
vcftools --gzvcf input.vcf.gz \
  --remove-duplicates \
  --remove-indels \
  --minQ 30 --min-meanDP 2 --max-meanDP 50 \
  --max-missing 0.8 \
  --maf 0.05 --max-maf 0.95 \
  --hwe 0.001 \
  --recode --recode-INFO-all --stdout | bgzip -c > sample1_snp_q30_dp2_50_miss08_maf005_hwe001.vcf.gz
```

## Post-Processing: Index
```
tabix -p vcf output.vcf.gz
```

## Key Notes
- `--max-missing` ranges 0–1; higher = stricter (fewer missing allowed)
- `--maf 0.05` removes variants with minor allele frequency below 5%
- `--max-maf 0.95` is equivalent to removing fixed variants (MAF > 0.95 means major allele freq < 0.05)
- HWE filtering only works on biallelic SNPs; multi-allelic sites are ignored
- Always run `tabix -p vcf` after generating the final VCF.gz for downstream tools