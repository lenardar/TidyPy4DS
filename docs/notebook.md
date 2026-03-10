# Notebook 示例

本文档放一些适合在 Jupyter / VS Code Notebook 中直接使用的例子。

## `glimpse()`

```python
import pandas as pd
from tidypy.tidy import glimpse, starts_with

df = pd.DataFrame({
    "id": [1, 2, 3],
    "dept": ["A", "A", "B"],
    "score_math": [90.0, None, 88.0],
    "score_eng": [85.0, 91.0, None],
    "name": [" Alice ", "Bob", "Anna"],
})
```

### 查看整张表结构

```python
glimpse(df)
```

### 只看一部分列

```python
glimpse(df, cols=starts_with("score_"))
```

### 文本模式

```python
print(glimpse(df, cols=["name", "score_math"], as_text=True, display=False))
```

### 控制预览宽度

```python
glimpse(df, cols=["name"], width=2, max_width=10)
```

## `summarize()`

```python
from tidypy.tidy import summarize
```

### 全局聚合

```python
summarize(
    df,
    avg_math=("score_math", "mean"),
    avg_eng=("score_eng", "mean"),
)
```

### 单列分组聚合

```python
summarize(
    df,
    by="dept",
    avg_math=("score_math", "mean"),
    n=("id", "count"),
)
```

### 多列分组聚合

```python
df2 = df.assign(grp=["X", "Y", "X"])

summarize(
    df2,
    by=["dept", "grp"],
    avg_math=("score_math", "mean"),
    n=("id", "count"),
)
```
