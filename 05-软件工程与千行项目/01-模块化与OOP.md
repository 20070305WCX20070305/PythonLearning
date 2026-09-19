# 01 模块化与面向对象

## 学习目标

学完本篇后，你应该能够：

- 把单文件脚本拆分成职责清晰的模块与包，并解释 `import` 到底做了什么；
- 给函数与类写类型注解，让编辑器与静态检查工具帮你提前发现错误；
- 用 `class` 定义自己的数据类型：`__init__`、`self`、属性、方法、`@property`、`@dataclass`；
- 用继承与多态统一处理"不同来源的实验数据解析器"，并说清"组合优于继承"的含义；
- 实现常用魔术方法（`__repr__`、`__len__`、`__iter__`、`__eq__`）让对象行为自然；
- 用朴素依赖注入把配置、解析、存储解耦，为下一篇的测试做准备；
- 完成一次真实重构：把阶段 02 的批处理脚本改造成一个小包。

## 前置知识

- 阶段 01：Linux/Shell、venv、Git、pytest 入门、logging、argparse；
- 阶段 02：NumPy/Pandas、HDF5、SQLite、multiprocessing、tqdm；
- 阶段 03：对"程序 = 数据 + 指令"、内存与进程有基本直觉；
- 注意：前四个阶段的代码都是函数式写法，本篇是你第一次正式使用 `class`。

## 建议用时

3 周左右，每周 6~10 小时：第 1 周读 1.1~1.4，第 2 周读 1.5~1.8，第 3 周完成 1.9 与练习。

## 正文

### 1.1 从单文件脚本到模块化小包

阶段 02 的 `process_data.py` 把"读取、清洗、统计、写库"塞进一个 400 行的文件：改一处要上下翻找，
想在别处复用只能复制粘贴。**模块化的目标：让修改和复用只发生在一个地方。**

- **模块**：一个 `.py` 文件，本身是一个命名空间；
- **包**：含 `__init__.py` 的目录，是模块的集合；
- `import` 做三件事：按搜索路径（脚本目录 → `PYTHONPATH` → 安装目录）找到文件 →
  执行顶层代码（每进程一次，结果存入 `sys.modules`）→ 把名字绑定到当前命名空间。

```python
# analysis/io.py：只负责把磁盘文件变成 DataFrame
import pandas as pd

def read_spectrum_csv(path) -> pd.DataFrame:
    """读取两列 CSV（波长, 强度），统一列名。"""
    df = pd.read_csv(path)
    df.columns = ["wavelength", "intensity"]  # 屏蔽不同仪器的表头差异
    return df
```

包外使用绝对导入 `from analysis.io import read_spectrum_csv`；包内互相引用用相对导入
（`from .io import ...`），它只在包内有效，不能被直接 `python x.py` 运行。
`__init__.py` 的作用是标记包、控制导入时执行什么、定义对外接口：

```python
# analysis/__init__.py
"""实验数据处理小包。"""
from analysis.config import AnalysisConfig
from analysis.pipeline import Pipeline

__all__ = ["AnalysisConfig", "Pipeline"]  # 使用者只需要知道这两个名字
```

**常见错误**

- 在 `__init__.py` 顶层写耗时/有副作用的代码（打印、连数据库），一 `import` 就执行；
- 循环导入（a 导入 b，b 又导入 a）：公共部分下沉到第三个模块，或在函数内部延迟导入；
- 忘记 `if __name__ == "__main__":`，导入模块时入口逻辑也跟着执行。

### 1.2 类型注解：让编辑器替你检查

类型注解是写给人和工具的"接口契约"，**运行时不会强制检查**。

```python
from __future__ import annotations   # 3.10 也能安全使用 X | None 等写法
import pandas as pd

def normalize(df: pd.DataFrame, column: str, *, method: str = "minmax") -> pd.DataFrame:
    """对 column 做归一化；method 只能按关键字传入。"""

def load_many(paths: list[str]) -> dict[str, pd.DataFrame]:
    """批量读取，键为文件名。"""
```

- 常用写法：`list[int]`、`dict[str, float]`、`float | None`、`Callable[[float], float]`；
- 参数列表中 `*` 之后是"只能用关键字传入"的参数，防止传参顺序错误；
- 可选静态检查：`pip install mypy`，然后 `mypy src/`（本阶段知道即可）。

**常见错误**

- 以为注解会在运行时校验：传错类型照样执行，要校验得自己写 `isinstance` / `raise`；
- 注解里的类型导致循环导入，用 `from __future__ import annotations` 规避。

### 1.3 类与对象：给实验数据一个"身份"

函数式写法里，"一条光谱"是一堆散落的变量（`wavelength`、`intensity`、`name`），传递时必须整组传递。
类的思路：**把数据和对数据的操作绑在一起。**

```python
"""spectrum.py：用类封装一条实验光谱。"""
import numpy as np

class Spectrum:
    """一条实验光谱：波长与强度数组。"""
    def __init__(self, wavelength, intensity, name: str = "spectrum") -> None:
        # self 就是正在创建的实例，由 Python 自动传入
        if len(wavelength) != len(intensity):
            raise ValueError("波长与强度长度不一致")
        self.wavelength = np.asarray(wavelength, dtype=float)
        self.intensity = np.asarray(intensity, dtype=float)
        self.name = name

    def __repr__(self) -> str:  # 调试与日志：开发者视角
        return f"Spectrum(name={self.name!r}, n={len(self.wavelength)})"

    @property
    def peak_intensity(self) -> float:
        """最大光强；像字段一样访问：spec.peak_intensity。"""
        return float(self.intensity.max())

    def crop(self, lo: float, hi: float) -> "Spectrum":
        """返回波长在 [lo, hi] 内的新对象，不修改原对象。"""
        mask = (self.wavelength >= lo) & (self.wavelength <= hi)
        return Spectrum(self.wavelength[mask], self.intensity[mask], f"{self.name}|crop")
```

用法：`spec = Spectrum(x, y, name="Ne lamp")`，`spec.peak_intensity` 像字段一样读取，
`spec.crop(500, 600)` 返回新对象。类属性（如 `instrument = "unknown"`）所有实例共享，
`self.xxx` 才是各实例独立的数据。`@property` 适合"由已有属性算出来"的只读量。

类主要用来"装数据"时，用 `@dataclass` 自动生成 `__init__`、`__repr__`、`__eq__`：

```python
from dataclasses import dataclass, field

@dataclass
class Peak:
    """一个谱峰：中心位置、高度与宽度。"""
    center: float
    height: float
    sigma: float = 1.0
    labels: list[str] = field(default_factory=list)  # 可变默认值必须用 field
```

**常见错误**

- 方法定义漏写 `self`，或调用时多写 `self`；
- 用可变对象作类属性（如 `label = []`），所有实例共享同一个列表；
- `__init__` 里做耗时 IO（读文件、连数据库），应只保存参数，动作交给方法。

### 1.4 继承与多态：多来源数据解析器

数据可能来自 CSV、SQLite、HDF5；差异只在"怎么读"，之后的清洗统计完全一样。
继承让调用方只认一个统一接口：

```python
"""sources.py：不同数据源的统一接口。"""
from abc import ABC, abstractmethod
import pandas as pd

class DataSource(ABC):
    """数据源抽象基类：输入路径，输出统一格式的表。"""

    @abstractmethod
    def load(self, path):
        """子类必须实现；返回列名为 wavelength / intensity 的表。"""

class CsvSource(DataSource):
    def load(self, path):
        df = pd.read_csv(path)
        df.columns = ["wavelength", "intensity"]
        return df

class SqliteSource(DataSource):
    def __init__(self, table: str) -> None:
        self.table = table

    def load(self, path):
        import sqlite3  # 延迟导入：可选依赖不影响模块本身的导入
        with sqlite3.connect(path) as conn:
            return pd.read_sql_query(f"SELECT wavelength, intensity FROM {self.table}", conn)
```

多态：调用方只写 `source.load(path)`，不关心是哪个子类；新增格式只加子类，调用方零修改。
子类必须能替换父类而不出问题（里氏替换原则）：不要偷偷改变参数含义或返回格式。

**常见错误**

- 为了"复用"而继承：`is-a` 不成立时应该用组合（下一节）；
- 父类里塞进太多与子类无关的方法，继承链越理越乱。

### 1.5 组合优于继承

`Pipeline` 与 `DataSource` 的关系是"**有一个**"（has-a），不是"是一个"（is-a），应该用组合：

```python
class Cleaner:
    """清洗器：去掉 NaN、按阈值剔除坏点。"""
    def __init__(self, snr_threshold: float = 3.0) -> None:
        self.snr_threshold = snr_threshold

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.dropna()
        return df[df["intensity"] > self.snr_threshold]

class Pipeline:
    """流水线：由任意的 source 与 cleaner 组合而成。"""
    def __init__(self, source: DataSource, cleaner: Cleaner) -> None:
        self.source = source      # 依赖以对象形式保存
        self.cleaner = cleaner

    def run(self, path) -> pd.DataFrame:
        return self.cleaner.clean(self.source.load(path))
```

好处：换解析器不用写子类；测试时可传入返回假数据的 `FakeSource`；运行期按配置决定用哪个 cleaner。

**常见错误**

- 继承层次超过两层就开始痛苦，此时几乎都应该改用组合；
- 把"参数不同"当成"类型不同"（`CsvSourceWithTab` 这类名字是坏味道）。

### 1.6 常用魔术方法

魔术方法（双下划线方法）让自定义对象拥有内建类型一样的行为：

```python
class Run:
    """一次实验运行：包含若干条 Spectrum。"""
    def __init__(self, name: str, spectra: list[Spectrum] | None = None) -> None:
        self.name = name
        self.spectra = list(spectra or [])

    def __repr__(self) -> str:        # 调试与日志：开发者视角
        return f"Run(name={self.name!r}, n={len(self.spectra)})"

    def __len__(self) -> int:         # len(run)
        return len(self.spectra)

    def __iter__(self):               # for spec in run
        return iter(self.spectra)

    def __eq__(self, other) -> bool:  # run1 == run2
        if not isinstance(other, Run):
            return NotImplemented
        return self.name == other.name and self.spectra == other.spectra
```

上下文管理器（`with`）也是魔术方法：实现 `__enter__` / `__exit__` 后，
`with Timer() as t:` 就能自动计时；`__exit__` 返回 `False` 表示不吞掉异常。

**常见错误**

- `__repr__` 里做 IO 或复杂计算（日志、调试器会频繁调用它）；
- 定义了 `__eq__` 却指望对象还能当字典键（需要时补 `__hash__`）；
- `__eq__` 对其他类型直接 `raise`，正确做法是返回 `NotImplemented`。

### 1.7 单一职责与依赖注入

单一职责：一个类只有一个"变化的原因"。依赖注入（DI）的朴素版本就一句话：
**不要在自己内部创建依赖，从构造函数传进来。**

```python
class Analyzer:
    """计算统计量；repository 与 config 由外部注入。"""
    def __init__(self, repository, config) -> None:
        self.repository = repository
        self.config = config

    def analyze(self, spectrum_id: int) -> dict[str, float]:
        spectrum = self.repository.get(spectrum_id)
        mask = (spectrum.wavelength >= self.config.lo) & (spectrum.wavelength <= self.config.hi)
        return {"mean": float(spectrum.intensity[mask].mean())}
```

测试时传入内存版假仓库（只实现 `get`）即可；换存储只换注入的对象。

**常见错误**

- 在 `__init__` 里 `sqlite3.connect(...)` 或 `json.load(open("config.json"))`：无法测试、路径写死；
- 用全局变量当"依赖"，谁都能改，测试之间互相污染。

### 1.8 配置管理：json 与 toml

路径、阈值、并发数这些"会变的东西"不要硬编码：

```python
"""config.py：配置的读取与校验。"""
import json
from dataclasses import dataclass
from pathlib import Path

@dataclass
class AnalysisConfig:
    """分析流水线的配置。"""
    input_dir: str
    workers: int = 4
    snr_threshold: float = 3.0

    @classmethod
    def from_json(cls, path: str | Path) -> "AnalysisConfig":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(**data)
```

TOML 更适合人写（支持注释，JSON 不支持）：

```toml
# config.toml
input_dir = "data/raw"
workers = 8
```

Python 3.11+ 用标准库 `tomllib` 读取；3.10 需先 `pip install tomli`，再用 `import tomli as tomllib`。

**常见错误**

- 配置文件路径硬编码，换台机器就找不到；
- 忘记 `encoding="utf-8"`，Windows 上中文配置读成乱码；
- 把密钥/token 写进配置文件并提交到 Git（应排除或用环境变量）。

### 1.9 综合案例：把阶段 02 脚本重构成小包

重构前：`process_data.py` 约 400 行，读取、清洗、统计、写库、argparse 全在一个文件。重构后：

```text
analysis/
├── __init__.py      # 对外导出 Pipeline 与 AnalysisConfig
├── config.py        # AnalysisConfig（1.8）
├── io.py            # read_spectrum_csv（1.1）
├── cleaning.py      # Cleaner（1.5）
├── stats.py         # compute_stats(df)：纯函数，保持函数式
├── storage.py       # SqliteStorage：持有数据库连接，用类
├── pipeline.py      # Pipeline：组装流程（1.5）
└── cli.py           # argparse 入口，只做参数解析与调用
```

```python
# analysis/pipeline.py
from analysis.cleaning import Cleaner
from analysis.sources import DataSource
from analysis.stats import compute_stats
from analysis.storage import SqliteStorage

class Pipeline:
    """端到端流程：读取 -> 清洗 -> 统计 -> 入库；持有协作对象与存储连接。"""
    def __init__(self, source: DataSource, cleaner: Cleaner, storage: SqliteStorage) -> None:
        self.source = source
        self.cleaner = cleaner
        self.storage = storage

    def run(self, path) -> None:
        df = self.cleaner.clean(self.source.load(path))
        stats = compute_stats(df)  # 纯函数直接调用，不必包成类
        self.storage.write(path.name, stats)
```

CLI 的 `main()` 只做组装：读配置 → 建 `CsvSource` / `Cleaner` / `SqliteStorage` → 构造 `Pipeline`
→ 逐个 `pipeline.run(path)`，返回 0。

重构的合理边界：纯计算、无状态的逻辑保持函数；持有资源/连接、有生命周期、需要多态替换、
由多个协作对象组成的才用类。

**常见错误**

- 过度设计：给每个纯函数都套一个 `XxxManager` 类，代码更难读；
- `__init__.py` 导出全部内部函数，接口和使用者一起失控；
- 重构时一次改太多：先搬动、功能不变、测试通过，再优化。

## 练习

1. **拆模块**：选一个阶段 02 的单文件脚本，按"读 / 算 / 写"拆成 3 个模块。
   提示：先画调用关系图再搬代码。验收：`python -c "import 你的包"` 无输出无副作用。
2. **完善 Spectrum 类**：给 1.3 的 `Spectrum` 添加 `normalize()` 与 `__eq__`，`normalize()` 返回新对象。
   提示：参考"返回新对象"惯例。验收：5 条断言，覆盖归一化、原对象不变、相等判断。
3. **多态解析器**：在 1.4 基础上增加 `JsonlSource` 和工厂函数 `make_source(suffix) -> DataSource`。
   提示：用字典分派。验收：新增格式调用方零修改；未知后缀报错信息清晰。
4. **组合重写**：找一个继承实现（或按 1.4 造一个），判断哪些其实是 has-a，用组合重写。
   提示：检查子类是否只是"换了参数/换了对象"。验收：画 before/after 类图并说明改进点。
5. **配置化**：为练习 1 的包设计 `@dataclass` 配置并从 JSON 读取。
   提示：每个字段给默认值；对 `workers <= 0` 抛 `ValueError`。验收：改配置不改代码。

## 自测清单

- [ ] 我能解释 `import` 的三个步骤，以及绝对导入与相对导入的适用场景
- [ ] 我知道 `__init__.py` 的作用，并知道为什么不应在里面写副作用代码
- [ ] 我能给函数与类写类型注解，并说明它不会在运行时校验
- [ ] 我能写出一个含 `__init__`、方法、`@property`、`__repr__` 的类
- [ ] 我能用 `@dataclass` 简化数据类，并解释 `field(default_factory=...)`
- [ ] 我能举出一个必须用继承（或抽象基类）的例子，和一个应该用组合的例子
- [ ] 我能解释依赖注入如何让代码更容易测试
- [ ] 我能说出本阶段"什么代码该用类、什么代码保持函数"的边界

## 参考资料

- Python 官方教程：模块 <https://docs.python.org/zh-cn/3/tutorial/modules.html>
- Python 官方教程：类 <https://docs.python.org/zh-cn/3/tutorial/classes.html>
- Python 官方教程：虚拟环境与包 <https://docs.python.org/zh-cn/3/tutorial/venv.html>
- 标准库 dataclasses <https://docs.python.org/zh-cn/3/library/dataclasses.html>
- 标准库 typing <https://docs.python.org/zh-cn/3/library/typing.html>
- 标准库 tomllib <https://docs.python.org/zh-cn/3/library/tomllib.html>
