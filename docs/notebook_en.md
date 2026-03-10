# Notebook Notes

This document collects a few notebook-friendly usage patterns for `TidyPy4DS`.

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

### Inspect the whole table

```python
glimpse(df)
```

### Inspect only part of the table

```python
glimpse(df, cols=starts_with("score_"))
```

### Text mode

```python
print(glimpse(df, cols=["name", "score_math"], as_text=True, display=False))
```

### Control preview width

```python
glimpse(df, cols=["name"], width=2, max_width=10)
```

## `summarize()`

```python
from tidypy.tidy import summarize
```

### Global summary

```python
summarize(
    df,
    avg_math=("score_math", "mean"),
    avg_eng=("score_eng", "mean"),
)
```

### Grouped by one column

```python
summarize(
    df,
    by="dept",
    avg_math=("score_math", "mean"),
    n=("id", "count"),
)
```

### Grouped by multiple columns

```python
df2 = df.assign(grp=["X", "Y", "X"])

summarize(
    df2,
    by=["dept", "grp"],
    avg_math=("score_math", "mean"),
    n=("id", "count"),
)
```
