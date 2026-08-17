# TBtools 安装指南

> 本指南帮助新用户从零安装 TBtools-II 及其依赖环境

## 一、系统要求

| 项目 | 最低要求 | 推荐 |
|------|----------|------|
| 操作系统 | Windows 7+ / macOS 10.12+ / Linux | Windows 10/11 64位 |
| Java | JRE 1.6+（安装包已内置） | JRE 17+ |
| 内存 | 2 GB | 8 GB+（处理大基因组时） |
| 磁盘 | 500 MB（软件本身） | 10 GB+（含数据文件） |

## 二、下载

### 方式一：GitHub Releases（推荐）
1. 打开 https://github.com/CJ-Chen/TBtools/releases
2. 选择最新版本，根据操作系统下载对应安装包：

| 操作系统 | 文件名示例 | 说明 |
|----------|-----------|------|
| Windows 64位 | `TBTOOLS-LL_WINDOWS-X64_2_025.EXE` | 推荐稳定版 |
| Windows 64位（含最新JDK） | `TBTOOLS-LL_WINDOWS-X64_2_025_LATESTJDK.EXE` | 稳定版安装失败时用此版 |
| Windows ARM | `TBTOOLS-LL_WINDOWS-ARM64_2_025_ARM.EXE` | ARM 架构芯片专用 |
| Windows 32位 | `TBTOOLS-LL_WINDOWS-X32_2_025.EXE` | Win7 32位 / XP |
| macOS | `TBTOOLS-LL_MACOS_2_025.DMG` | macOS 专用 |

### 方式二：小飞机网盘（国内高速下载）
1. 打开 https://share.feijipan.com/s/DAeLabKy
2. 无需登录，直接下载对应版本

## 三、安装步骤

### Windows
1. 双击下载的 `.exe` 安装包
2. 一路点击 **Next**（默认选项即可）
3. 等待安装完成，桌面会出现 TBtools 图标
4. 双击桌面图标启动

> **常见问题**：安装进度条卡住 → 改用 `LATESTJDK` 版本安装包

### macOS
1. 双击 `.dmg` 文件
2. 将 TBtools 拖入 Applications 文件夹
3. 首次打开时如提示"无法验证开发者"，右键点击 → **打开**
4. 如仍无法打开：系统偏好设置 → 安全性与隐私 → 点击"仍要打开"

### Linux / 跨平台（JAR 方式）
1. 下载 `TBtools-crossplatform_XXX.rar` 并解压，获得 `.jar` 文件
2. 确保已安装 Java（`java -version` 检查）
3. 终端运行：
   ```bash
   java -Xmx4G -jar /path/to/TBtools.jar
   ```
   - `-Xmx4G` 表示分配 4GB 内存，处理大基因组建议设为 8G 或更高

## 四、可选依赖安装

### 4.1 BLAST+（使用 BLAST 功能必装）

TBtools 的 BLAST 相关功能（Local BLAST、Whole Genome BLAST、Reciprocal BLAST 等）依赖 NCBI BLAST+。

#### Windows
1. 下载 ftp://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/ntblast-*.exe
2. 运行安装程序，记录安装路径（如 `C:\Program Files\NCBI\blast-2.x.x+\bin`）
3. 将 `bin` 目录添加到系统环境变量 PATH：
   - 右键"此电脑" → 属性 → 高级系统设置 → 环境变量
   - 在"系统变量"中找到 `Path` → 编辑 → 新建 → 粘贴 BLAST bin 目录路径
   - 确定保存

#### macOS / Linux
```bash
# 使用 conda 安装（推荐）
conda install -c bioconda blast

# 或手动下载
wget ftp://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/ncbi-blast-2.x.x+-x64-linux.tar.gz
tar xzf ncbi-blast-*.tar.gz
export PATH=$PATH:/path/to/ncbi-blast-*/bin  # 加入 ~/.bashrc 持久化
```

#### 验证安装
```bash
makeblastdb -version
blastn -version
```

### 4.2 BWA-MEM2（使用 NGS 比对功能必装）

```bash
# conda 安装
conda install -c bioconda bwa-mem2

# 或源码编译
git clone https://github.com/bwa-mem2/bwa-mem2.git
cd bwa-mem2 && make
export PATH=$PATH:$(pwd)
```

### 4.3 其他可选工具
| 工具 | 用途 | 安装方式 |
|------|------|----------|
| MEME Suite | Motif 分析 | http://meme-suite.org/ |
| SRA Toolkit | SRA 数据下载 | `conda install -c bioconda sra-tools` |
| Samtools | SAM/BAM 处理 | `conda install -c bioconda samtools` |

## 五、首次启动验证

1. 双击桌面 TBtools 图标启动
2. 主界面出现后，点击菜单栏 **Version** 按钮检查是否为最新版本
3. 如有新版本，按提示更新
4. 点击 **Citation** 按钮可查看引用信息

## 六、常见安装问题

| 问题 | 解决方案 |
|------|----------|
| Windows 安装卡住 | 使用 `LATESTJDK` 版本安装包 |
| macOS 无法打开 | 右键 → 打开；或系统设置 → 安全性与隐私 → 仍要打开 |
| Java 报错 | 确保安装了 64 位 Java；或使用自带 JRE 的安装包 |
| BLAST 功能不可用 | 检查 BLAST+ 是否安装并已加入 PATH 环境变量 |
| 内存不足 | 启动时增加 `-Xmx` 参数值（如 `-Xmx8G`） |
| 拖拽文件卡死 | 这是已知 Java 问题，改用"…"按钮选择文件 |

## 七、引用方式

Chen C., Wu Y., Li J., Wang X., Zeng Z., Xu J., Liu Y., Feng J., Chen H., He Y., and Xia R. (2023). TBtools-II: A "one for all, all for one" bioinformatics platform for biological big-data mining. Mol. Plant. 16, 1733–1742.