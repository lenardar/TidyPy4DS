# Function Reference

This document organizes the current `TidyPy4DS` API by module and is meant to be the detailed reference next to the README.

Implementation: [tidypy/tidy.py](/Users/xuzhiyuan/code/research/TidyPy4DS/tidypy/tidy.py)

## General Rules

### Column Arguments

Most column-oriented parameters support:

- a single column name
- a list of column names
- a `ColSelector`

Examples:

```python
select(df, "id")
select(df, ["id", "dept"])
select(df, numeric())
```

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

### Selector Support

Common parameters that support selectors:

- `select(df, *args)`
- `mutate_across(df, selector, func)`
- `rename_with(df, func, selector=...)`
- `summarize(df, by=...)`
- `relocate(df, *cols, before=..., after=...)`
- `distinct(df, *cols)`
- `count(df, *cols)`
- `add_count(df, *cols)`
- `pivot_longer(df, cols=...)`
- `pivot_wider(df, id_cols=...)`
- `glimpse(df, cols=...)`
- `drop_na(df, *cols)`
- `fill_na(df, *cols)`
- `unite(df, *cols)`

String-only column parameters:

- `arrange(df, *cols)` with plain column names and `desc(col)`
- `desc(col)`
- `pivot_wider(..., names_from=..., values_from=...)`
- `separate(df, col=...)`

## Selectors

### `ColSelector`

Describes how to select columns and resolves lazily against a concrete DataFrame.

Typical sources:

- `starts_with("score_")`
- `numeric()`
- `where(lambda s: s.isnull().any())`

Rules:

- `resolve(df)` expands to real column names
- expanded names must exist in `df.columns`
- results are deduplicated and order-preserving

### `starts_with(prefix)`

Select columns whose names start with `prefix`.

### `ends_with(suffix)`

Select columns whose names end with `suffix`.

### `contains(pat)`

Select columns whose names contain `pat`.

### `matches(regex)`

Select columns using a regex match.

### `everything()`

Select all columns.

### `last_col()`

Select the last column.

### `numeric()`

Select numeric columns.

Implementation is based on:

```python
df.select_dtypes(include="number")
```

### `categorical()`

Select `object` and `category` columns.

Notes:

- this is a tidypy helper, not a pandas built-in
- it is an ergonomic name, not a strict statistical category definition
- in practice it is closer to “string/category-like fields”

### `boolean()`

Select boolean columns.

### `datetime()`

Select datetime columns.

### `where(func)`

Select columns using a custom predicate on each `Series`.

Examples:

```python
where(lambda s: s.isnull().any())
where(lambda s: s.nunique() < 10)
```

### `make_clean_names(names, case="snake")`

Clean a sequence of names into a stable snake_case style.

Parameters:

- `names`: any iterable of names
- `case`: currently only supports `"snake"`

Returns:

- `list[str]`

Rules:

- Unicode text is normalized and folded to ASCII when possible
- non-alphanumeric characters become underscores
- repeated underscores are collapsed
- leading and trailing underscores are removed
- empty results fall back to `"x"`
- duplicate names get suffixes such as `_2`, `_3`

Example:

```python
make_clean_names(["Patient ID", "Age (Years)", "score math", "score-math"])
```

### `clean_names(df, case="snake")`

Clean the column names of a whole DataFrame.

Parameters:

- `df`: input DataFrame
- `case`: currently only supports `"snake"`

Returns:

- new DataFrame

Example:

```python
clean_names(df)
```

## dplyr-style

### `glimpse(df, cols=None, width=3, max_width=24, as_text=False, display=True, return_df=True)`

Quick structural preview for notebooks and interactive work.

Parameters:

- `cols`: optional subset of columns
- `width`: number of sample values to preview per column
- `max_width`: max width of each previewed value
- `as_text`: return a text-style output closer to R `glimpse()`
- `display`: print/display immediately
- `return_df`: return the summary DataFrame

Returned columns:

- `column`
- `dtype`
- `non_null`
- `nulls`
- `n_unique`
- `preview`

Examples:

```python
glimpse(df)
summary = glimpse(df, display=False)
text = glimpse(df, cols=starts_with("score_"), as_text=True, display=False)
```

### `select(df, *args)`

Select columns by names, lists of names, or selectors.

```python
select(df, "id", "dept")
select(df, numeric() | starts_with("id"))
```

### `filter_rows(df, func)`

Filter rows with a boolean condition built from `df`.

### `mutate_across(df, selector, func)`

Apply one function to each selected column.

```python
mutate_across(df, numeric(), lambda s: s.fillna(0))
mutate_across(df, starts_with("score_"), lambda s: s.round(2))
```

### `arrange(df, *cols)`

Sort by columns.

Descending order must be expressed explicitly with `desc("col")`.

```python
arrange(df, "dept", desc("salary"))
```

Rules:

- plain strings always mean ascending order
- descending order must be written with `desc(...)`
- `arrange(df)` returns `df.copy()`

### `desc(col)`

Build a descending sort specification for `arrange()`.

### `rename_with(df, func, selector=None)`

Rename columns in bulk.

```python
rename_with(df, str.lower)
rename_with(df, lambda c: c.replace("score_", ""), starts_with("score_"))
```

### `summarize(df, by=None, **kwargs)`

Global or grouped aggregation.

```python
summarize(df, avg=("salary", "mean"))
summarize(df, by="dept", avg=("salary", "mean"), n=("id", "count"))
```

Internally grouped summaries use `sort=False` and return a reset index.

### `relocate(df, *cols, before=None, after=None)`

Move columns to the front, before another column, or after another column.

### `distinct(df, *cols, keep="first")`

Drop duplicates by selected columns, or across the whole table if no columns are passed.

### `count(df, *cols, sort=False, name="n")`

Group and count rows.

```python
count(df, "dept")
count(df, "dept", sort=True, name="rows")
```

### `add_count(df, *cols, sort=False, name="n")`

Group and count rows, then merge the count back into the original table.

### `coalesce(*values)`

Return the first non-missing value row by row.

Parameters:

- `values`: a sequence of `Series` objects or scalars; the first argument must be a `Series`

Returns:

- `Series`

Example:

```python
coalesce(df["score_math"], df["score_eng"], 0)
```

Notes:

- values are aligned to the index of the first `Series`
- scalars are expanded to the same length automatically
- the current implementation does not allow a scalar as the first argument

### `if_else(condition, true, false)`

Choose between two branches row by row.

Parameters:

- `condition`: boolean condition, as a `Series`, list-like value, or scalar
- `true`: value used when the condition is true
- `false`: value used when the condition is false

Returns:

- `Series`

Example:

```python
if_else(df["score_math"] >= 90, "top", "other")
```

### `recode(s, mapping, default=None)`

Recode a Series with a mapping dictionary.

Parameters:

- `s`: input `Series`
- `mapping`: dictionary from old values to new values
- `default`: fallback for unmapped values; when omitted, original values are kept

Returns:

- `Series`

Example:

```python
recode(df["dept"], {"A": "Alpha", "B": "Beta"})
recode(df["dept"], {"A": "Alpha"}, default="Other")
```

### `case_when(*cases, default=None)`

Pick values from the first matching condition, useful for building label columns.

```python
case_when(
    (df["score_math"] >= 90, "A"),
    (df["score_math"] >= 80, "B"),
    default="C",
)
```

Conditions are matched in written order.

## stringr-style

### `str_detect(s, pat, regex=True)`

Boolean match per element. Missing values default to `False`.

### `str_extract(s, pat)`

Extract the first matching substring.

### `str_replace(s, pat, repl)`

Replace the first match.

### `str_replace_all(s, pat, repl)`

Replace all matches.

### `str_remove(s, pat)`

Remove matching content.

### `str_split(s, pat)`

Split strings by a pattern.

### `str_trim(s)`

Trim leading and trailing whitespace.

### `str_pad(s, width, side="left", fillchar=" ")`

Pad strings to a target width.

### `str_to_lower(s)`

Convert to lowercase.

### `str_to_upper(s)`

Convert to uppercase.

### `str_to_title(s)`

Convert to title case.

### `str_count(s, pat)`

Count matches per string.

### `str_length(s)`

Compute string length.

### `str_glue(template, df)`

Format each row into a string using `str.format(...)`.

```python
str_glue("{dept}-{id}", df)
```

Current implementation uses row-wise `apply(...)`, so it is not intended for very large tables.

## tidyr-style

### `pivot_longer(df, cols, names_to="name", values_to="value")`

Convert a wide table to long form.

Unselected columns automatically become `id_vars`.

### `pivot_wider(df, id_cols, names_from, values_from, aggfunc="first")`

Convert a long table back to wide form.

### `separate(df, col, into, sep=r"[^a-zA-Z0-9]+")`

Split one column into multiple columns.

Current behavior is strict: if the number of pieces does not match `into`, it raises an error.

### `unite(df, new_col, *cols, sep="_", remove=True, na_rm=False)`

Join multiple columns into one.

By default missing values are turned into empty strings instead of the literal string `"nan"`.

### `drop_na(df, *cols)`

Drop rows with missing values, checking either the given columns or the whole table.

### `na_if(s, value)`

Replace a specific value with missing values.

Parameters:

- `s`: input `Series`
- `value`: target value to convert to missing

Returns:

- `Series`

Example:

```python
na_if(pd.Series(["A", "N/A", "B"]), "N/A")
```

### `fill_na(df, *cols, direction="down")`

Fill missing values by direction.

- `"down"` maps to `ffill`
- `"up"` maps to `bfill`

### `replace_na(df, value)`

Replace missing values with a fixed value or mapping.

### `remove_empty(df, axis="both")`

Drop fully empty rows, fully empty columns, or both.

Parameters:

- `df`: input DataFrame
- `axis`: `"rows"`, `"cols"`, or `"both"`

Returns:

- new DataFrame

Example:

```python
remove_empty(df, axis="rows")
remove_empty(df, axis="both")
```

### `row_to_names(df, row=0, remove_row=True, reset_index=True)`

Promote one row to column names, useful for messy Excel-style headers.

Parameters:

- `df`: input DataFrame
- `row`: row index to use as the header
- `remove_row`: whether to remove the original header row
- `reset_index`: whether to reset the index afterwards

Returns:

- new DataFrame

Example:

```python
row_to_names(df, row=0)
```

Notes:

- new column names are passed through `make_clean_names(...)`
- out-of-range `row` values raise `IndexError`
