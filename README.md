# TidyPy4DS

`TidyPy4DS` is a tidyverse-inspired data cleaning helper layer built on top of `pandas`.

Chinese README: [README_ZH.md](/Users/xuzhiyuan/code/research/TidyPy4DS/README_ZH.md)

It focuses on the parts of day-to-day pandas work that tend to become repetitive or noisy: column selection, batch mutation, string handling, reshaping, and more readable `.pipe()` workflows.

## Goals

- Keep function names close to tidyverse
- Keep interfaces aligned with Python / pandas
- Only wrap the parts that are genuinely awkward in pandas
- Make every function start with `df`
- Return new objects instead of mutating in place

## Good Fit

- You do a lot of cleaning and feature preparation
- You already like `df.pipe(...)`
- You are moving from tidyverse to pandas and want familiar verbs
- You want to separate “which columns” from “what rule to apply”

## Current State

Implementation lives in [tidypy/tidy.py](/Users/xuzhiyuan/code/research/TidyPy4DS/tidypy/tidy.py).

Detailed function notes:
Chinese [docs/functions.md](/Users/xuzhiyuan/code/research/TidyPy4DS/docs/functions.md)
English [docs/functions_en.md](/Users/xuzhiyuan/code/research/TidyPy4DS/docs/functions_en.md)

Notebook notes:
Chinese [docs/notebook.md](/Users/xuzhiyuan/code/research/TidyPy4DS/docs/notebook.md)
English [docs/notebook_en.md](/Users/xuzhiyuan/code/research/TidyPy4DS/docs/notebook_en.md)

Jupyter examples:

- Why tidypy:
  Chinese [examples/01-why-tidypy.zh.ipynb](/Users/xuzhiyuan/code/research/TidyPy4DS/examples/01-why-tidypy.zh.ipynb)
  English [examples/01-why-tidypy.en.ipynb](/Users/xuzhiyuan/code/research/TidyPy4DS/examples/01-why-tidypy.en.ipynb)
- Core APIs:
  Chinese [examples/02-core-apis.zh.ipynb](/Users/xuzhiyuan/code/research/TidyPy4DS/examples/02-core-apis.zh.ipynb)
  English [examples/02-core-apis.en.ipynb](/Users/xuzhiyuan/code/research/TidyPy4DS/examples/02-core-apis.en.ipynb)
- Reshape and missing values:
  Chinese [examples/03-reshape-and-missing-values.zh.ipynb](/Users/xuzhiyuan/code/research/TidyPy4DS/examples/03-reshape-and-missing-values.zh.ipynb)
  English [examples/03-reshape-and-missing-values.en.ipynb](/Users/xuzhiyuan/code/research/TidyPy4DS/examples/03-reshape-and-missing-values.en.ipynb)

Implemented so far:

- selector system: `ColSelector`
- name helpers: `starts_with`, `ends_with`, `contains`, `matches`, `everything`, `last_col`
- type helpers: `numeric`, `categorical`, `boolean`, `datetime`, `where`
- name cleaning helpers: `make_clean_names`, `clean_names`
- dplyr-style helpers: `glimpse`, `select`, `filter_rows`, `mutate_across`, `arrange`, `desc`, `rename_with`, `summarize`, `relocate`, `distinct`, `count`, `add_count`
- conditional and missing-value helpers: `case_when`, `if_else`, `recode`, `coalesce`, `na_if`
- stringr-style helpers: common `str_*`
- tidyr-style helpers: `pivot_longer`, `pivot_wider`, `separate`, `unite`, `drop_na`, `fill_na`, `replace_na`, `remove_empty`, `row_to_names`

Not included yet:

- `nest`
- `unnest`

## Requirements

- Python 3.10+
- pandas 2.2+

## Install

From the project root:

```bash
pip install -e .
```

CI runs `unittest` on Python 3.10, 3.11, and 3.12. See [.github/workflows/tests.yml](/Users/xuzhiyuan/code/research/TidyPy4DS/.github/workflows/tests.yml).

## Quick Start

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

### Select Columns

```python
select(df, "id", numeric())
select(df, numeric() | starts_with("dept"))
select(df, everything() - categorical())
```

### Batch Mutation

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

### Chained Cleaning

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

### Name Cleaning And Missing-Value Helpers

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

### Conditional Mapping And Messy Header Cleanup

```python
label = if_else(
    df["score_math"] >= 90,
    "top",
    "other",
)

dept_name = recode(
    df["dept"],
    {"A": "Alpha", "B": "Beta"},
)

header_df = row_to_names(raw_excel_df, row=0)
compact_df = remove_empty(header_df, axis="both")
```

### Reshaping

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

### Inspecting Structure

```python
glimpse(df)
```

`glimpse(df)` shows:

- row and column counts
- dtype per column
- non-null counts
- null counts
- unique value counts
- a short preview of sample values

It also returns a summary DataFrame by default:

```python
summary = glimpse(df, display=False)
summary.sort_values("nulls", ascending=False)
```

### Counting

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

### dplyr-style

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
- `if_else`
- `recode`
- `coalesce`

### stringr-style

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

### tidyr-style

- `na_if`
- `pivot_longer`
- `pivot_wider`
- `separate`
- `unite`
- `drop_na`
- `fill_na`
- `replace_na`
- `remove_empty`
- `row_to_names`

## Conventions

### Column Arguments

Most column-oriented parameters support:

- a single column name
- a list of column names
- a `ColSelector`

### Selector Composition

```python
numeric() | starts_with("id")
everything() - contains("tmp")
```

- `|` means union
- `-` means exclusion
- results are deduplicated and order-preserving

### Errors

- missing columns raise `KeyError`
- invalid parameter types raise `TypeError`
- “must resolve at least one column” cases raise `ValueError`

### Copy Semantics

Functions return new objects, but they do not guarantee deep copies. Underlying memory sharing is still up to pandas.

### `arrange`

Use `desc("salary")` for descending sorts.

### `categorical`

`categorical()` is a tidypy helper, not a pandas built-in. The current implementation selects `object` and `category` columns and is mainly meant for string/category-like fields.

### `str_detect`

`str_detect()` defaults to `na=False`.

## Tests

Run:

```bash
python3 -m unittest discover -s tests -v
```

Test file: [tests/test_tidy.py](/Users/xuzhiyuan/code/research/TidyPy4DS/tests/test_tidy.py)

## Project Structure

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
├── README_ZH.md
├── tests/
│   └── test_tidy.py
└── tidypy/
    ├── __init__.py
    └── tidy.py
```

## Acknowledgement

Thanks to OpenAI Codex for helping bootstrap the project, fill in tests, and polish the docs during the early stage.
