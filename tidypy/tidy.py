from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

import pandas as pd


DataFrame = pd.DataFrame
Series = pd.Series


# =====
# 核心数据结构
# =====

@dataclass(frozen=True)
class ColSelector:
    """延迟解析列选择规则，直到拿到具体 DataFrame 才展开。"""

    func: Callable[[DataFrame], list[str]]

    def resolve(self, df: DataFrame) -> list[str]:
        cols = self.func(df)
        if not isinstance(cols, list):
            cols = list(cols)
        # selector 必须只返回当前 df 中真实存在的列，避免静默失败。
        missing = [col for col in cols if col not in df.columns]
        if missing:
            raise KeyError(f"Unknown columns from selector: {missing}")
        return list(dict.fromkeys(cols))

    def __or__(self, other: "ColSelector") -> "ColSelector":
        _ensure_selector(other)
        return ColSelector(
            lambda df: list(dict.fromkeys(self.resolve(df) + other.resolve(df)))
        )

    def __sub__(self, other: "ColSelector") -> "ColSelector":
        _ensure_selector(other)
        return ColSelector(
            lambda df: [col for col in self.resolve(df) if col not in other.resolve(df)]
        )


@dataclass(frozen=True)
class SortSpec:
    """描述排序列和方向，给 arrange 提供更稳的排序表达。"""

    column: str
    ascending: bool = True


# =====
# 内部辅助函数
# =====

def _ensure_selector(value: Any) -> None:
    if not isinstance(value, ColSelector):
        raise TypeError(f"Expected ColSelector, got {type(value).__name__}")


def _flatten_column_args(df: DataFrame, *args: Any, allow_empty: bool = True) -> list[str]:
    # 所有“传列参数”的入口都走这里，统一顺序、去重和报错策略。
    cols: list[str] = []
    for arg in args:
        if arg is None:
            continue
        if isinstance(arg, ColSelector):
            cols.extend(arg.resolve(df))
            continue
        if isinstance(arg, str):
            cols.append(arg)
            continue
        if isinstance(arg, pd.Index):
            cols.extend(arg.tolist())
            continue
        if isinstance(arg, Iterable) and not isinstance(arg, (bytes, bytearray, dict)):
            for item in arg:
                if not isinstance(item, str):
                    raise TypeError(
                        "Column iterables must contain only strings; "
                        f"got {type(item).__name__}"
                    )
                cols.append(item)
            continue
        raise TypeError(f"Unsupported column argument: {type(arg).__name__}")

    unique_cols = list(dict.fromkeys(cols))
    missing = [col for col in unique_cols if col not in df.columns]
    if missing:
        raise KeyError(f"Unknown columns: {missing}")
    if not allow_empty and not unique_cols:
        raise ValueError("No columns resolved")
    return unique_cols


def _resolve_single_column(df: DataFrame, arg: Any, *, param_name: str) -> str:
    cols = _flatten_column_args(df, arg, allow_empty=False)
    if len(cols) != 1:
        raise ValueError(f"{param_name} must resolve to exactly one column")
    return cols[0]


def _normalize_arrange_specs(df: DataFrame, *cols: Any) -> tuple[list[str], list[bool]]:
    by: list[str] = []
    ascending: list[bool] = []
    for col in cols:
        if isinstance(col, SortSpec):
            if col.column not in df.columns:
                raise KeyError(f"Unknown columns: [{col.column!r}]")
            by.append(col.column)
            ascending.append(col.ascending)
            continue
        if isinstance(col, str):
            if col not in df.columns:
                raise KeyError(f"Unknown columns: [{col!r}]")
            by.append(col)
            ascending.append(True)
            continue
        raise TypeError("arrange columns must be strings or SortSpec")
    return by, ascending


def _format_glimpse_value(value: Any, *, max_length: int = 24) -> str:
    if pd.isna(value):
        return "NA"
    text = repr(value)
    if len(text) > max_length:
        return f"{text[: max_length - 3]}..."
    return text


def _glimpse_summary(df: DataFrame, *, width: int = 3, max_width: int = 24) -> DataFrame:
    rows = []
    for col in df.columns:
        series = df[col]
        preview = ", ".join(
            _format_glimpse_value(value, max_length=max_width)
            for value in series.head(width).tolist()
        )
        rows.append(
            {
                "column": col,
                "dtype": str(series.dtype),
                "non_null": int(series.notna().sum()),
                "nulls": int(series.isna().sum()),
                "n_unique": int(series.nunique(dropna=True)),
                "preview": preview,
            }
        )
    return pd.DataFrame(rows)


def _glimpse_text(summary: DataFrame, *, rows: int, cols: int) -> str:
    lines = [f"Rows: {rows}", f"Columns: {cols}"]
    for _, row in summary.iterrows():
        lines.append(
            f"$ {row['column']} <{row['dtype']}> "
            f"[non-null={row['non_null']}, nulls={row['nulls']}, unique={row['n_unique']}] "
            f"{row['preview']}"
        )
    return "\n".join(lines)


def _coerce_case_when_piece(value: Any, index: pd.Index) -> Series:
    if isinstance(value, Series):
        return value.reindex(index)
    if isinstance(value, pd.Index):
        value = value.tolist()
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes, bytearray, dict)):
        series = pd.Series(list(value), index=index)
        if len(series) != len(index):
            raise ValueError("Iterable values in case_when must have the same length")
        return series
    return pd.Series([value] * len(index), index=index)


def _infer_case_when_index(cases: tuple[tuple[Any, Any], ...], default: Any) -> pd.Index:
    for mask, value in cases:
        for candidate in (mask, value):
            if isinstance(candidate, Series):
                return candidate.index
            if isinstance(candidate, pd.Index):
                return pd.RangeIndex(len(candidate))
            if isinstance(candidate, Iterable) and not isinstance(
                candidate, (str, bytes, bytearray, dict)
            ):
                return pd.RangeIndex(len(list(candidate)))
    if isinstance(default, Series):
        return default.index
    if isinstance(default, pd.Index):
        return pd.RangeIndex(len(default))
    if isinstance(default, Iterable) and not isinstance(default, (str, bytes, bytearray, dict)):
        return pd.RangeIndex(len(list(default)))
    raise ValueError("case_when needs at least one Series/list-like mask or value to infer length")


def _normalize_name_piece(name: Any, *, case: str = "snake") -> str:
    text = "" if pd.isna(name) else str(name)
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    if case == "snake":
        text = text.lower()
    text = re.sub(r"[^0-9A-Za-z]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "x"


def _dedupe_names(names: Iterable[str]) -> list[str]:
    seen: dict[str, int] = {}
    cleaned: list[str] = []
    for name in names:
        count = seen.get(name, 0)
        seen[name] = count + 1
        cleaned.append(name if count == 0 else f"{name}_{count + 1}")
    return cleaned


# =====
# selector helper
# =====

def starts_with(prefix: str) -> ColSelector:
    """选择列名以指定前缀开头的列。"""
    return ColSelector(lambda df: [col for col in df.columns if col.startswith(prefix)])


def ends_with(suffix: str) -> ColSelector:
    """选择列名以指定后缀结尾的列。"""
    return ColSelector(lambda df: [col for col in df.columns if col.endswith(suffix)])


def contains(pat: str) -> ColSelector:
    """选择列名中包含指定子串的列。"""
    return ColSelector(lambda df: [col for col in df.columns if pat in col])


def matches(regex: str | re.Pattern[str]) -> ColSelector:
    """使用正则表达式匹配列名。"""
    rx = re.compile(regex)
    return ColSelector(lambda df: [col for col in df.columns if rx.search(col)])


def everything() -> ColSelector:
    """选择全部列。"""
    return ColSelector(lambda df: df.columns.tolist())


def last_col() -> ColSelector:
    """选择最后一列。"""
    return ColSelector(lambda df: [df.columns[-1]] if len(df.columns) else [])


def numeric() -> ColSelector:
    """选择数值列。"""
    return ColSelector(lambda df: df.select_dtypes(include="number").columns.tolist())


def categorical() -> ColSelector:
    """选择 object 和 category 类型的列。"""
    return ColSelector(
        lambda df: df.select_dtypes(include=["object", "category"]).columns.tolist()
    )


def boolean() -> ColSelector:
    """选择布尔列。"""
    return ColSelector(lambda df: df.select_dtypes(include=["bool"]).columns.tolist())


def datetime() -> ColSelector:
    """选择日期时间列。"""
    return ColSelector(
        lambda df: df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()
    )


def where(func: Callable[[Series], bool]) -> ColSelector:
    """按自定义条件选择列，func 接收单列 Series。"""
    return ColSelector(lambda df: [col for col in df.columns if func(df[col])])


def desc(col: str) -> SortSpec:
    """生成降序排序描述，适合和 arrange 一起使用。"""
    return SortSpec(column=col, ascending=False)


# =====
# janitor 风格
# =====

def make_clean_names(names: Iterable[Any], case: str = "snake") -> list[str]:
    """把一组列名清理成稳定、可用的格式。"""
    if case != "snake":
        raise ValueError("case currently only supports 'snake'")
    normalized = [_normalize_name_piece(name, case=case) for name in names]
    return _dedupe_names(normalized)


def clean_names(df: DataFrame, case: str = "snake") -> DataFrame:
    """清理整张表的列名。"""
    return df.set_axis(make_clean_names(df.columns, case=case), axis=1)


# =====
# dplyr 风格
# =====

def select(df: DataFrame, *args: Any) -> DataFrame:
    """按列名、列列表或 selector 选择列。"""
    cols = _flatten_column_args(df, *args)
    return df.loc[:, cols]


def filter_rows(df: DataFrame, func: Callable[[DataFrame], Any]) -> DataFrame:
    """按布尔条件过滤行。"""
    mask = func(df)
    return df.loc[mask]


def mutate_across(
    df: DataFrame, selector: ColSelector | Iterable[str] | str, func: Callable[[Series], Any]
) -> DataFrame:
    """对选中的每一列应用同一个函数，并返回新 DataFrame。"""
    cols = _flatten_column_args(df, selector, allow_empty=False)
    return df.assign(**{col: func(df[col]) for col in cols})


def arrange(df: DataFrame, *cols: Any) -> DataFrame:
    """按列排序；降序请显式使用 desc('col')。"""
    if not cols:
        return df.copy()
    by, ascending = _normalize_arrange_specs(df, *cols)
    return df.sort_values(by=by, ascending=ascending)


def rename_with(
    df: DataFrame,
    func: Callable[[str], str],
    selector: ColSelector | Iterable[str] | str | None = None,
) -> DataFrame:
    """批量修改列名，不传 selector 时对全部列生效。"""
    cols = df.columns.tolist() if selector is None else _flatten_column_args(df, selector)
    return df.rename(columns={col: func(col) for col in cols})


def summarize(df: DataFrame, by: Any = None, **kwargs: Any) -> DataFrame:
    """做全局聚合或分组聚合，返回整理后的结果表。"""
    if by is not None:
        group_cols = _flatten_column_args(df, by, allow_empty=False)
        return df.groupby(group_cols, sort=False).agg(**kwargs).reset_index()
    return df.agg(**kwargs).to_frame().T.reset_index(drop=True)


def relocate(
    df: DataFrame,
    *cols: Any,
    before: Any = None,
    after: Any = None,
) -> DataFrame:
    """移动列的位置，可放到最前、某列之前或某列之后。"""
    if before is not None and after is not None:
        raise ValueError("Pass only one of before or after")

    move_cols = _flatten_column_args(df, *cols, allow_empty=False)
    rest = [col for col in df.columns if col not in move_cols]

    if before is not None:
        anchor = _resolve_single_column(df.loc[:, rest], before, param_name="before")
        idx = rest.index(anchor)
    elif after is not None:
        anchor = _resolve_single_column(df.loc[:, rest], after, param_name="after")
        idx = rest.index(anchor) + 1
    else:
        idx = 0

    return df.loc[:, rest[:idx] + move_cols + rest[idx:]]


def distinct(df: DataFrame, *cols: Any, keep: str = "first") -> DataFrame:
    """按指定列去重；不传列时按整表去重。"""
    subset = _flatten_column_args(df, *cols) or None
    return df.drop_duplicates(subset=subset, keep=keep)


def count(df: DataFrame, *cols: Any, sort: bool = False, name: str = "n") -> DataFrame:
    """按列分组计数。"""
    group_cols = _flatten_column_args(df, *cols, allow_empty=False)
    result = (
        df.groupby(group_cols, sort=False, dropna=False)
        .size()
        .reset_index(name=name)
    )
    if sort:
        result = result.sort_values(name, ascending=False)
    return result.reset_index(drop=True)


def add_count(df: DataFrame, *cols: Any, sort: bool = False, name: str = "n") -> DataFrame:
    """按列分组计数，并把计数结果回填到原表。"""
    counts = count(df, *cols, sort=sort, name=name)
    join_cols = _flatten_column_args(df, *cols, allow_empty=False)
    return df.merge(counts, on=join_cols, how="left", sort=False)


def coalesce(*values: Any) -> Series:
    """按行返回第一个非缺失值。"""
    if not values:
        raise ValueError("coalesce requires at least one Series or scalar")

    series_list: list[Series] = []
    index: pd.Index | None = None
    for value in values:
        if isinstance(value, Series):
            if index is None:
                index = value.index
            series_list.append(value if index is value.index else value.reindex(index))
        else:
            if index is None:
                raise ValueError("coalesce needs a Series before scalar values")
            series_list.append(pd.Series([value] * len(index), index=index))

    result = series_list[0].copy()
    for series in series_list[1:]:
        result = result.where(result.notna(), series)
    return result


def na_if(s: Series, value: Any) -> Series:
    """把指定值转换为缺失值。"""
    return s.mask(s == value)


# =====
# 条件与映射
# =====

def if_else(condition: Any, true: Any, false: Any) -> Series:
    """按条件逐行选择两个分支中的值。"""
    index = _infer_case_when_index(((condition, true),), false)
    mask = _coerce_case_when_piece(condition, index).astype(bool)
    true_values = _coerce_case_when_piece(true, index)
    false_values = _coerce_case_when_piece(false, index)
    return false_values.where(~mask, true_values)


def recode(s: Series, mapping: dict[Any, Any], default: Any = None) -> Series:
    """按映射表重编码 Series 的值。"""
    result = s.map(mapping)
    if default is None:
        return result.where(s.isin(mapping), s)
    return result.fillna(default)


def glimpse(
    df: DataFrame,
    *,
    cols: Any = None,
    width: int = 3,
    max_width: int = 24,
    as_text: bool = False,
    display: bool = True,
    return_df: bool = True,
) -> DataFrame | str | None:
    """快速查看 DataFrame 结构，适合在 Jupyter 中做初步检查。"""

    target_df = df if cols is None else select(df, cols)
    summary = _glimpse_summary(target_df, width=width, max_width=max_width)
    text = _glimpse_text(summary, rows=len(df), cols=target_df.shape[1])

    if display:
        if as_text:
            print(text)
        else:
            print(f"Rows: {len(df)}, Columns: {target_df.shape[1]}")
            try:
                from IPython.display import display as ipy_display

                ipy_display(summary)
            except Exception:
                print(summary.to_string(index=False))

    if as_text:
        return text
    if return_df:
        return summary
    return None


def case_when(*cases: tuple[Any, Any], default: Any = None) -> Series:
    """按条件依次选择值，适合在 mutate 或 assign 中构造分类列。"""

    if not cases:
        raise ValueError("case_when requires at least one (condition, value) pair")

    index = _infer_case_when_index(cases, default)
    result = _coerce_case_when_piece(default, index)

    for condition, value in reversed(cases):
        mask = _coerce_case_when_piece(condition, index).astype(bool)
        values = _coerce_case_when_piece(value, index)
        result = result.where(~mask, values)

    return result


# =====
# stringr 风格
# =====

def str_detect(s: Series, pat: str, *, regex: bool = True) -> Series:
    """判断每个字符串是否匹配指定模式，缺失值默认返回 False。"""
    return s.str.contains(pat, regex=regex, na=False)


def str_extract(s: Series, pat: str) -> Series:
    """提取每个字符串中第一个匹配到的子串。"""
    return s.str.extract(f"({pat})", expand=True)[0]


def str_replace(s: Series, pat: str, repl: str) -> Series:
    """只替换每个字符串中第一个匹配项。"""
    return s.str.replace(pat, repl, n=1, regex=True)


def str_replace_all(s: Series, pat: str, repl: str) -> Series:
    """替换每个字符串中的全部匹配项。"""
    return s.str.replace(pat, repl, regex=True)


def str_remove(s: Series, pat: str) -> Series:
    """删除每个字符串中的匹配内容。"""
    return s.str.replace(pat, "", regex=True)


def str_split(s: Series, pat: str) -> Series:
    """按模式拆分字符串。"""
    return s.str.split(pat)


def str_trim(s: Series) -> Series:
    """去掉字符串首尾空白。"""
    return s.str.strip()


def str_pad(s: Series, width: int, side: str = "left", fillchar: str = " ") -> Series:
    """把字符串补齐到指定宽度。"""
    return s.str.pad(width, side=side, fillchar=fillchar)


def str_to_lower(s: Series) -> Series:
    """转成小写。"""
    return s.str.lower()


def str_to_upper(s: Series) -> Series:
    """转成大写。"""
    return s.str.upper()


def str_to_title(s: Series) -> Series:
    """转成标题格式。"""
    return s.str.title()


def str_count(s: Series, pat: str) -> Series:
    """统计每个字符串中模式出现的次数。"""
    return s.str.count(pat)


def str_length(s: Series) -> Series:
    """计算字符串长度。"""
    return s.str.len()


def str_glue(template: str, df: DataFrame) -> Series:
    """按模板把每一行格式化为字符串。"""
    return df.apply(lambda row: template.format(**row.to_dict()), axis=1)


# =====
# tidyr 风格
# =====

def pivot_longer(
    df: DataFrame,
    cols: Any,
    names_to: str = "name",
    values_to: str = "value",
) -> DataFrame:
    """把宽表转成长表。"""
    value_vars = _flatten_column_args(df, cols, allow_empty=False)
    # melt 的核心是“剩余列自动作为 id_vars”，这样 selector 体验更自然。
    id_vars = [col for col in df.columns if col not in value_vars]
    return df.melt(
        id_vars=id_vars,
        value_vars=value_vars,
        var_name=names_to,
        value_name=values_to,
    )


def pivot_wider(
    df: DataFrame,
    id_cols: Any,
    names_from: str,
    values_from: str,
    *,
    aggfunc: str | Callable[[Series], Any] = "first",
) -> DataFrame:
    """把长表转成宽表。"""
    index_cols = _flatten_column_args(df, id_cols, allow_empty=False)
    for col in (names_from, values_from):
        if col not in df.columns:
            raise KeyError(f"Unknown column: {col}")
    return (
        df.pivot_table(
            index=index_cols,
            columns=names_from,
            values=values_from,
            aggfunc=aggfunc,
            sort=False,
        )
        .reset_index()
        .rename_axis(None, axis=1)
    )


def separate(
    df: DataFrame,
    col: Any,
    into: Iterable[str],
    sep: str = r"[^a-zA-Z0-9]+",
) -> DataFrame:
    """把一列按分隔规则拆成多列。"""
    source_col = _resolve_single_column(df, col, param_name="col")
    target_cols = list(into)
    if not target_cols or not all(isinstance(name, str) for name in target_cols):
        raise TypeError("into must be a non-empty iterable of strings")

    pieces = df[source_col].str.split(sep, expand=True)
    # 早期版本保持严格：拆出来的段数不匹配就直接报错。
    if pieces.shape[1] != len(target_cols):
        raise ValueError(
            f"Expected {len(target_cols)} pieces from {source_col}, got {pieces.shape[1]}"
        )
    pieces = pieces.set_axis(target_cols, axis=1)
    return df.drop(columns=[source_col]).join(pieces)


def unite(
    df: DataFrame,
    new_col: str,
    *cols: Any,
    sep: str = "_",
    remove: bool = True,
    na_rm: bool = False,
) -> DataFrame:
    """把多列合并成一列。"""
    source_cols = _flatten_column_args(df, *cols, allow_empty=False)

    def _join_row(row: Series) -> str:
        values = row.tolist()
        if na_rm:
            values = [value for value in values if pd.notna(value)]
        # 默认把缺失值变成空字符串，避免出现字符串 "nan"。
        return sep.join("" if pd.isna(value) else str(value) for value in values)

    result = df.assign(**{new_col: df[source_cols].apply(_join_row, axis=1)})
    if remove:
        return result.drop(columns=source_cols)
    return result


def drop_na(df: DataFrame, *cols: Any) -> DataFrame:
    """删除含缺失值的行；不传列时检查全部列。"""
    subset = _flatten_column_args(df, *cols) or None
    return df.dropna(subset=subset)


def fill_na(df: DataFrame, *cols: Any, direction: str = "down") -> DataFrame:
    """按向下或向上方向填充缺失值。"""
    if direction not in {"down", "up"}:
        raise ValueError("direction must be 'down' or 'up'")
    target_cols = _flatten_column_args(df, *cols) or df.columns.tolist()
    method_name = "ffill" if direction == "down" else "bfill"
    return df.assign(**{col: getattr(df[col], method_name)() for col in target_cols})


def replace_na(df: DataFrame, value: Any) -> DataFrame:
    """用固定值替换缺失值。"""
    return df.fillna(value)


# =====
# janitor 风格
# =====

def remove_empty(df: DataFrame, axis: str = "both") -> DataFrame:
    """删除全空行、全空列，或两者都删。"""
    if axis not in {"rows", "cols", "both"}:
        raise ValueError("axis must be 'rows', 'cols', or 'both'")

    result = df
    if axis in {"rows", "both"}:
        result = result.dropna(axis=0, how="all")
    if axis in {"cols", "both"}:
        result = result.dropna(axis=1, how="all")
    return result


def row_to_names(
    df: DataFrame,
    row: int = 0,
    *,
    remove_row: bool = True,
    reset_index: bool = True,
) -> DataFrame:
    """把某一行提成列名，常用于清理脏 Excel 表头。"""
    if row < 0 or row >= len(df):
        raise IndexError("row is out of range")

    names = make_clean_names(df.iloc[row].tolist())
    result = df.copy()
    result.columns = names

    if remove_row:
        result = result.drop(df.index[row])
    if reset_index:
        result = result.reset_index(drop=True)
    return result


# 按模块分组导出，方便以后平滑拆分为 selectors / dplyr / stringr / tidyr / janitor。
__all__ = [
    # 核心数据结构
    "ColSelector",
    "SortSpec",

    # selector helper
    "boolean",
    "categorical",
    "contains",
    "datetime",
    "ends_with",
    "everything",
    "last_col",
    "matches",
    "numeric",
    "starts_with",
    "where",

    # janitor 风格
    "clean_names",
    "make_clean_names",
    "remove_empty",
    "row_to_names",

    # dplyr 风格
    "add_count",
    "arrange",
    "count",
    "desc",
    "distinct",
    "filter_rows",
    "glimpse",
    "mutate_across",
    "relocate",
    "rename_with",
    "select",
    "summarize",

    # 条件与映射
    "case_when",
    "coalesce",
    "if_else",
    "na_if",
    "recode",

    # stringr 风格
    "str_count",
    "str_detect",
    "str_extract",
    "str_glue",
    "str_length",
    "str_pad",
    "str_remove",
    "str_replace",
    "str_replace_all",
    "str_split",
    "str_to_lower",
    "str_to_title",
    "str_to_upper",
    "str_trim",

    # tidyr 风格
    "drop_na",
    "fill_na",
    "pivot_longer",
    "pivot_wider",
    "replace_na",
    "separate",
    "unite",
]
