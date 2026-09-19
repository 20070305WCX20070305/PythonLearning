# 项目：实验数据文件整理 CLI

## 背景

实验室仪器导出的文件往往长这样：

```text
run1.csv
RUN_02.CSV
扫描记录 温度 2026-03-15.txt
temp_data_copy.csv
scan1.txt
measurement_2026-03-14.json
temp_data.csv          （与 temp_data_copy.csv 内容完全相同）
untitled.txt
data.csv.bak
```

命名混乱、大小写不统一、含空格、同一份数据复制多份、不同仪器格式混杂。
手工整理既慢又容易出错，本项目用 Python 写一个命令行工具自动完成：
扫描、分类、去重、复制或移动、生成报告、记录日志，并提供 dry-run 预览保证安全。

## 学习目标

把阶段 01 学到的全部内容用起来：

- Shell/Linux：目录结构、权限、`tar`/`grep` 辅助检查
- Git：全程版本控制，按里程碑提交，最后打 tag
- venv + requirements.txt：隔离环境
- pathlib / shutil / hashlib：文件遍历、复制、去重
- argparse / logging / 异常处理：规范的 CLI
- pytest：核心函数测试
- tmux：跑长时间整理任务不中断（可选，数据量大时）

## MVP（必须完成）

输入一个源目录，工具按顺序完成：

1. **扫描**：递归找出所有文件，忽略临时文件（如以 `~$`、`.` 开头，或 `.bak` 结尾，可配置）。
2. **分类**：先按扩展名映射分类，再支持关键词规则（文件名含"温度/temp"归入 temperature 等）。
3. **去重**：用 SHA-256 内容哈希判断完全相同的文件，重复文件只保留一份，
   其余记录在报告的重复列表中（默认不删除，只跳过）。
4. **执行**：按 `--mode copy|move` 把文件放入 `目标目录/分类/` 下，默认 copy；
   名称冲突时自动加 `_1`、`_2` 后缀，绝不覆盖已有文件。
5. **报告**：输出 CSV（每个文件的明细）与 JSON（按分类汇总、重复列表、错误列表）。
6. **日志**：INFO 写控制台与文件，`-v` 时输出 DEBUG。
7. **dry-run**：`--dry-run` 只打印/记录将执行的操作，不真正动文件。

### CLI 设计

```text
用法: data_organizer.py --source 源目录 [--dest 目标目录] [选项]

必选参数:
  --source DIR      待整理的源目录

可选参数:
  --dest DIR        输出目录（默认 organized）
  --mode {copy,move}  处理方式，默认 copy
  --dry-run         只预览，不实际复制/移动
  --report PREFIX   报告文件名前缀（默认 report，生成 PREFIX.csv 与 PREFIX.json）
  --log FILE        日志文件路径（默认 organizer.log）
  --verbose, -v     输出 DEBUG 日志
```

### 报告格式约定

`report.csv` 每个文件一行：

```csv
name,category,size_bytes,sha256,action,dest,status
run1.csv,tables,1024,3a7f...,copy,organized/tables/run1.csv,ok
temp_data_copy.csv,tables,1024,3a7f...,skip,,duplicate
```

`report.json`：

```json
{
  "source": "/home/you/sample-data",
  "total_files": 20,
  "processed": 17,
  "duplicates": 2,
  "errors": 1,
  "by_category": {"tables": 8, "text": 5, "structured": 2, "other": 2},
  "duplicate_files": [{"name": "temp_data_copy.csv", "same_as": "temp_data.csv"}]
}
```

字段名可以微调，但报告必须包含：总数、成功数、重复数、错误数、按分类统计、重复文件对照。

## 里程碑

| 里程碑 | 内容 | 完成标志 |
| --- | --- | --- |
| M1 扫描与分类 | 实现 scan_files、classify_by_extension、关键词规则；用 make_sample_data.py 的数据验证 | 能打印「分类: 数量」的统计，pytest 中分类用例通过 |
| M2 哈希与去重 | 实现 hash_file、find_duplicates；报告重复文件对照 | 对含重复文件的样本，重复列表正确且原文件保留 |
| M3 CLI 与报告 | argparse、logging、CSV/JSON 报告、dry-run 安全执行 | 一条命令跑通全流程，dry-run 与实际执行结果一致 |
| M4 测试与收尾 | pytest 覆盖核心函数（含 tmp_path）、README 更新、Git tag `v0.1.0` | `pytest -q` 全绿，GitHub 上有 tag |
| M5 进阶（可选） | 配置文件驱动规则、按规则重命名、undo 撤销 | 配置文件改动规则生效；undo 后目录恢复整理前状态 |

建议每个里程碑一个 Git 分支，合并后打 tag（如 `v0.1.0`~`v0.4.0`）。

## 建议目录结构

```text
data-organizer/
├── .gitignore
├── README.md
├── requirements.txt
├── starter/
│   ├── make_sample_data.py      # 生成模拟数据（已提供）
│   └── data_organizer.py        # 主程序骨架（已提供，补全 TODO）
├── tests/
│   └── test_data_organizer.py   # 测试骨架（已提供，补全 TODO）
├── sample-data/                 # 生成的测试数据（gitignore）
├── organized/                   # 输出目录（gitignore）
└── logs/                        # 日志与操作记录（gitignore）
```

## 运行方法

```bash
cd ~/projects/data-organizer
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt          # 至少包含 pytest

# 1. 生成模拟数据
python starter/make_sample_data.py --target sample-data --seed 42

# 2. 预览（不动文件）
python starter/data_organizer.py --source sample-data --dest organized --dry-run -v

# 3. 正式执行并生成报告
python starter/data_organizer.py --source sample-data --dest organized \
    --report reports/run1 --mode copy

# 4. 测试
pytest -q
```

## 技术约束

- 只用阶段 00~01 学过的知识：标准库 + pytest，不使用任何其他第三方库
- 不使用 class/面向对象写法，全部用函数组织（阶段 05 再学 class）
- 不使用 numpy/pandas（阶段 02）、subprocess/多进程/异步（阶段 02）
- 所有命令在 WSL2 Ubuntu 24.04 中执行
- 破坏性操作必须有 dry-run，且默认不覆盖已有文件

## 验收标准

- [ ] `python starter/data_organizer.py --help` 显示完整参数说明
- [ ] 对 `make_sample_data.py` 生成的混乱数据，MVP 全流程可跑通
- [ ] 重复文件被识别且只处理一份，报告中能看到重复对照
- [ ] `--dry-run` 输出与实际执行结果一致，且 dry-run 后源目录未变化
- [ ] 目标目录名冲突时文件不丢失、不覆盖
- [ ] 报告 CSV 与 JSON 字段齐全、可用 Excel/编辑器打开
- [ ] 日志文件包含时间、级别、关键操作，出错时有可定位信息
- [ ] `pytest -q` 全部通过（测试用例至少 10 个，覆盖分类、哈希、去重、报告、参数解析）
- [ ] 项目在 Git 中管理：多个有意义提交、至少一个分支合并、打了 tag
- [ ] README 写清运行方法与报告示例

## 进阶功能（选做）

1. **配置驱动规则**：用 JSON 配置扩展名映射与关键词规则，默认配置内置，`--config` 覆盖。
2. **按规则重命名**：如 `scan1.csv` → `scan_001.csv`、统一小写扩展名；
   重命名同样要写进操作记录，支持 undo。
3. **undo 撤销**：每次执行把操作写入 `logs/operations_时间戳.json`（记录 from/to/action），
   `--undo 操作文件` 反向执行（copy 的删除副本，move 的搬回去）。
4. **性能与体验**：`--exclude` 排除目录、进度输出、`--yes` 跳过确认等。

## 提示

- 先写测试再补实现（针对骨架里的 TODO），最容易拿到正反馈
- 每次只实现一个函数，运行、提交、再继续
- 处理真实数据前，一定先用 `--dry-run` 和样本数据验证
- 遇到文件名含空格、中文、大小写混用，优先用 `Path` 对象而不是字符串运算
