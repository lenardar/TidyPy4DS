# TidyPy4DS

`TidyPy4DS` 是一组基于 `pandas` 的 tidyverse 数据清洗函数。

English README: [README_EN.md](/Users/xuzhiyuan/code/research/TidyPy4DS/README_EN.md)

它专注解决 pandas 在日常整理流程里最容易写得啰嗦的部分：列选择、批量变换、字符串处理、宽长表转换，以及更顺手的 `.pipe()` 链式调用。

## 设计目标

- 函数名尽量贴近 tidyverse
- 接口保持 Python / pandas 风格
- 只补 pandas 不够顺手的部分
- 所有函数第一个参数都是 `df`
- 默认返回新对象，不原地修改输入

## 适用场景

- 需要频繁做数据清洗和特征整理
- 习惯 `df.pipe(...)` 风格
- 从 tidyverse 迁移到 pandas，希望保留熟悉的操作方式
- 想把“选哪些列”和“怎么变换”拆开表达

## 当前实现

代码位于 [tidypy/tidy.py](/Users/xuzhiyuan/code/research/TidyPy4DS/tidypy/tidy.py)。

详细函数说明：
中文版 [docs/functions.md](/Users/xuzhiyuan/code/research/TidyPy4DS/docs/functions.md)
英文版 [docs/functions_en.md](/Users/xuzhiyuan/code/research/TidyPy4DS/docs/functions_en.md)

Notebook 说明：
中文版 [docs/notebook.md](/Users/xuzhiyuan/code/research/TidyPy4DS/docs/notebook.md)
英文版 [docs/notebook_en.md](/Users/xuzhiyuan/code/research/TidyPy4DS/docs/notebook_en.md)

Jupyter 演示：

- 为什么用 tidypy：
  中文版 [examples/01-why-tidypy.zh.ipynb](/Users/xuzhiyuan/code/research/TidyPy4DS/examples/01-why-tidypy.zh.ipynb)
  英文版 [examples/01-why-tidypy.en.ipynb](/Users/xuzhiyuan/code/research/TidyPy4DS/examples/01-why-tidypy.en.ipynb)
- 核心 API 用法：
  中文版 [examples/02-core-apis.zh.ipynb](/Users/xuzhiyuan/code/research/TidyPy4DS/examples/02-core-apis.zh.ipynb)
  英文版 [examples/02-core-apis.en.ipynb](/Users/xuzhiyuan/code/research/TidyPy4DS/examples/02-core-apis.en.ipynb)
- 整形与缺失值处理：
  中文版 [examples/03-reshape-and-missing-values.zh.ipynb](/Users/xuzhiyuan/code/research/TidyPy4DS/examples/03-reshape-and-missing-values.zh.ipynb)
  英文版 [examples/03-reshape-and-missing-values.en.ipynb](/Users/xuzhiyuan/code/research/TidyPy4DS/examples/03-reshape-and-missing-values.en.ipynb)

已提供：

- selector 系统：`ColSelector`
- 列 helper：`starts_with`、`ends_with`、`contains`、`matches`、`everything`、`last_col`
- 类型 helper：`numeric`、`categorical`、`boolean`、`datetime`、`where`
- 列名清理：`make_clean_names`、`clean_names`
- dplyr 风格函数：`glimpse`、`select`、`filter_rows`、`mutate_across`、`arrange`、`desc`、`rename_with`、`summarize`、`relocate`、`distinct`、`count`、`add_count`
- 条件与缺失值辅助：`case_when`、`coalesce`、`na_if`
- stringr 风格函数：常用 `str_*`
- tidyr 风格函数：`pivot_longer`、`pivot_wider`、`separate`、`unite`、`drop_na`、`fill_na`、`replace_na`

暂未包含：

- `nest`
- `unnest`

## 运行要求

- Python 3.10+
- pandas 2.2+

## 安装

在项目根目录执行：

```bash
pip install -e .
```

CI 会在 Python 3.10、3.11、3.12 上自动运行 `unittest`，配置见 [.github/workflows/tests.yml](/Users/xuzhiyuan/code/research/TidyPy4DS/.github/workflows/tests.yml)。

## 快速开始

```python
import pandas as pd
from tidypy.tidy import *

df = pd.DataFrame({
    "id": [1, 2, 3],
    "dept": ["A", "A", "B"],
    "score_math": [90.0, None, 88.0],
    "score_eng": [85.0, 91.0, None],
    "name": [" Alice ", "Bob", "Anna"],
})
```

### 选列

```python
select(df, "id", numeric())
select(df, numeric() | starts_with("dept"))
select(df, everything() - categorical())
```

### 批量变换

```python
result = (
    df
    .pipe(
        mutate_across,
        starts_with("score_"),
        lambda s: s.fillna(0),
    )
    .pipe(
        rename_with,
        lambda c: c.replace("score_", ""),
        starts_with("score_"),
    )
)
```

### 链式清洗

```python
result = (
    df
    .pipe(
        select,
        "id",
        "dept",
        starts_with("score_"),
        "name",
    )
    .pipe(
        mutate_across,
        starts_with("score_"),
        lambda s: s.fillna(0),
    )
    .pipe(
        filter_rows,
        lambda x: str_detect(x["name"], r"^A"),
    )
    .pipe(
        arrange,
        "dept",
        desc("score_math"),
    )
)
```

### 列名清理与缺失值辅助

```python
clean_df = clean_names(
    pd.DataFrame(columns=["Patient ID", "Age (Years)", "score math"])
)

label = coalesce(
    df["score_math"],
    df["score_eng"],
    0,
)

name = na_if(
    pd.Series(["A", "N/A", "B"]),
    "N/A",
)
```

### 宽长表转换

```python
long_df = pivot_longer(
    df,
    starts_with("score_"),
    names_to="metric",
    values_to="value",
)

wide_df = pivot_wider(
    long_df,
    id_cols="id",
    names_from="metric",
    values_from="value",
)
```

### Jupyter 中看表结构

```python
glimpse(df)
```

`glimpse(df)` 会显示：

- 行数和列数
- 每列的 dtype
- 非空值数量
- 缺失值数量
- 唯一值数量
- 前几条样本值预览

它默认也会返回一个概览 DataFrame：

```python
summary = glimpse(df, display=False)
summary.sort_values("nulls", ascending=False)
```

### 计数

```python
count(df, "dept")
add_count(df, "dept")
```

## API

### Selector

- `ColSelector`
- `starts_with`
- `ends_with`
- `contains`
- `matches`
- `everything`
- `last_col`
- `numeric`
- `categorical`
- `boolean`
- `datetime`
- `where`
- `make_clean_names`

### dplyr 风格

- `clean_names`
- `glimpse`
- `select`
- `filter_rows`
- `mutate_across`
- `arrange`
- `desc`
- `rename_with`
- `summarize`
- `relocate`
- `distinct`
- `count`
- `add_count`
- `case_when`
- `coalesce`

### stringr 风格

- `str_detect`
- `str_extract`
- `str_replace`
- `str_replace_all`
- `str_remove`
- `str_split`
- `str_trim`
- `str_pad`
- `str_to_lower`
- `str_to_upper`
- `str_to_title`
- `str_count`
- `str_length`
- `str_glue`

### tidyr 风格

- `na_if`
- `pivot_longer`
- `pivot_wider`
- `separate`
- `unite`
- `drop_na`
- `fill_na`
- `replace_na`

## 主要约定

### 列参数

大多数需要传列的参数都支持：

- 单个列名字符串
- 列名列表
- `ColSelector`

### selector 组合

```python
numeric() | starts_with("id")
everything() - contains("tmp")
```

- `|` 表示并集
- `-` 表示排除
- 结果去重且保序

### 错误处理

- 列不存在时抛 `KeyError`
- 参数类型不合法时抛 `TypeError`
- 必须解析出列但结果为空时抛 `ValueError`

### 复制语义

函数返回新对象，但不承诺深拷贝；底层数据是否共享由 pandas 自身决定。

### `arrange`

降序排序请使用 `desc("salary")`。

### `categorical`

`categorical()` 是 tidypy 提供的 helper，不是 pandas 原生函数。当前实现会选择 `object` 和 `category` 类型的列，主要用于方便处理字符串 / 类别类字段。

### `str_detect`

`str_detect()` 默认使用 `na=False`。

## 测试

运行：

```bash
python3 -m unittest discover -s tests -v
```

测试文件在 [tests/test_tidy.py](/Users/xuzhiyuan/code/research/TidyPy4DS/tests/test_tidy.py)。

## 项目结构

```text
TidyPy4DS/
├── .github/
│   └── workflows/
│       └── tests.yml
├── docs/
│   ├── functions.md
│   ├── functions_en.md
│   ├── notebook.md
│   └── notebook_en.md
├── examples/
│   ├── 01-why-tidypy.en.ipynb
│   ├── 01-why-tidypy.zh.ipynb
│   ├── 02-core-apis.en.ipynb
│   ├── 02-core-apis.zh.ipynb
│   ├── 03-reshape-and-missing-values.en.ipynb
│   └── 03-reshape-and-missing-values.zh.ipynb
├── pyproject.toml
├── README.md
├── README_EN.md
├── tests/
│   └── test_tidy.py
└── tidypy/
    ├── __init__.py
    └── tidy.py
```

## 鸣谢

感谢 OpenAI Codex 在项目早期帮忙搭骨架、补测试、打磨文档。很多零碎但必要的活，它都替我狠狠干了，哈哈。
