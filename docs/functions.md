# 函数说明

本文档按模块整理 `TidyPy4DS` 当前已实现的函数，适合作为 README 之外的详细查阅入口。

代码实现见 [tidypy/tidy.py](/Users/xuzhiyuan/code/research/TidyPy4DS/tidypy/tidy.py)。

## 通用约定

### 列参数

大多数需要“传列”的参数都支持以下三种形式：

- 单个列名字符串
- 列名列表
- `ColSelector`

例如：

```python
select(df, "id")
select(df, ["id", "dept"])
select(df, numeric())
```

### selector 组合

```python
numeric() | starts_with("id")
everything() - contains("tmp")
```

- `|` 表示并集
- `-` 表示排除
- 结果会去重并保持顺序

### 错误处理

- 列不存在时抛 `KeyError`
- 参数类型不合法时抛 `TypeError`
- 必须解析出列但结果为空时抛 `ValueError`

### selector 支持范围

支持 selector 的常见参数：

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

当前仅支持字符串列名的参数：

- `arrange(df, *cols)` 中普通列名形式和 `desc(col)`
- `desc(col)`
- `pivot_wider(..., names_from=..., values_from=...)`
- `separate(df, col=...)`

## Selector

### `ColSelector`

作用：延迟描述“怎么选列”，直到函数真正拿到 DataFrame 时再解析。

常见来源：

- `starts_with("score_")`
- `numeric()`
- `where(lambda s: s.isnull().any())`

支持的组合：

```python
numeric() | starts_with("id")
everything() - contains("tmp")
```

说明：

- `resolve(df)` 会把规则展开成真实列名列表
- 展开结果必须都是 `df.columns` 中存在的列
- 结果会去重并保持顺序

### `starts_with(prefix)`

作用：选择列名以指定前缀开头的列。

参数：

- `prefix`: 字符串前缀

返回值：

- `ColSelector`

示例：

```python
starts_with("score_")
select(df, starts_with("score_"))
```

### `ends_with(suffix)`

作用：选择列名以指定后缀结尾的列。

参数：

- `suffix`: 字符串后缀

返回值：

- `ColSelector`

示例：

```python
ends_with("_id")
```

### `contains(pat)`

作用：选择列名中包含指定子串的列。

参数：

- `pat`: 子串

返回值：

- `ColSelector`

示例：

```python
contains("score")
```

### `matches(regex)`

作用：用正则表达式匹配列名。

参数：

- `regex`: 正则表达式字符串或已编译正则对象

返回值：

- `ColSelector`

示例：

```python
matches(r"^score_(math|eng)$")
```

### `everything()`

作用：选择全部列。

返回值：

- `ColSelector`

示例：

```python
select(df, everything())
```

### `last_col()`

作用：选择最后一列。

返回值：

- `ColSelector`

示例：

```python
select(df, last_col())
```

### `numeric()`

作用：选择数值列。

实现基础：

- `df.select_dtypes(include="number")`

返回值：

- `ColSelector`

示例：

```python
select(df, numeric())
mutate_across(df, numeric(), lambda s: s.fillna(0))
```

### `categorical()`

作用：选择 `object` 和 `category` 类型的列。

注意：

- 这是 tidypy 提供的 helper，不是 pandas 原生函数
- 这是偏易用的命名
- 它不等价于严格意义上的“类别变量”
- 当前实现更接近“字符串 / 类别类字段”

返回值：

- `ColSelector`

示例：

```python
select(df, everything() - categorical())
```

### `boolean()`

作用：选择布尔列。

返回值：

- `ColSelector`

### `datetime()`

作用：选择日期时间列。

返回值：

- `ColSelector`

### `where(func)`

作用：按自定义条件选择列。

参数：

- `func`: 接收单列 `Series`，返回布尔值

返回值：

- `ColSelector`

示例：

```python
where(lambda s: s.isnull().any())
where(lambda s: s.nunique() < 10)
```

### `make_clean_names(names, case="snake")`

作用：把一组名称清理成稳定、统一的蛇形命名。

参数：

- `names`: 任意可迭代名称
- `case`: 当前只支持 `"snake"`

返回值：

- `list[str]`

规则：

- Unicode 字符会先做规范化，再尽量转成 ASCII
- 非字母数字字符会转成下划线
- 连续下划线会压缩成一个
- 首尾下划线会去掉
- 空结果会回退为 `"x"`
- 重名会自动补后缀，如 `_2`、`_3`

示例：

```python
make_clean_names(["Patient ID", "Age (Years)", "score math", "score-math"])
```

### `clean_names(df, case="snake")`

作用：清理整张表的列名。

参数：

- `df`: 输入 DataFrame
- `case`: 当前只支持 `"snake"`

返回值：

- 新 DataFrame

示例：

```python
clean_names(df)
```

## dplyr 风格

### `glimpse(df, cols=None, width=3, max_width=24, as_text=False, display=True, return_df=True)`

作用：快速查看 DataFrame 结构，适合在 Jupyter 中做初步检查。

参数：

- `df`: 输入 DataFrame
- `cols`: 可选，只查看部分列
- `width`: 每列预览多少个样本值
- `max_width`: 单个预览值的最大显示宽度
- `as_text`: 是否输出更接近 R `glimpse()` 的文本格式
- `display`: 是否立即输出结果
- `return_df`: 是否返回概览 DataFrame

返回值：

- `DataFrame` 或 `None`

输出字段：

- `column`
- `dtype`
- `non_null`
- `nulls`
- `n_unique`
- `preview`

示例：

```python
glimpse(df)

summary = glimpse(df, display=False)
summary.sort_values("nulls", ascending=False)

text = glimpse(df, cols=starts_with("score_"), as_text=True, display=False)
print(text)

summary = glimpse(df, cols=["name"], width=2, max_width=12, display=False)
```

说明：

- 在 IPython / Jupyter 中会优先用 `display(...)`
- 在普通终端里会回退为文本打印
- `as_text=True` 时会返回字符串

### `select(df, *args)`

作用：按列名、列列表或 selector 选择列。

参数：

- `df`: 输入 DataFrame
- `*args`: 列名、列名列表或 `ColSelector`

返回值：

- 选列后的 DataFrame

示例：

```python
select(df, "id", "dept")
select(df, numeric() | starts_with("id"))
```

说明：

- 结果去重且保序
- 遇到不存在列会直接报错

### `filter_rows(df, func)`

作用：按布尔条件过滤行。

参数：

- `df`: 输入 DataFrame
- `func`: 接收 `df`，返回布尔索引

返回值：

- 过滤后的 DataFrame

示例：

```python
filter_rows(df, lambda x: x["age"] > 25)
filter_rows(df, lambda x: str_detect(x["name"], r"^A"))
```

### `mutate_across(df, selector, func)`

作用：对选中的每一列应用同一个函数。

参数：

- `df`: 输入 DataFrame
- `selector`: 列名、列列表或 `ColSelector`
- `func`: 接收单列 `Series` 的函数

返回值：

- 新 DataFrame

示例：

```python
mutate_across(df, numeric(), lambda s: s.fillna(0))
mutate_across(df, starts_with("score_"), lambda s: s.round(2))
```

说明：

- 只更新选中的列
- 其他列保持不变

### `arrange(df, *cols)`

作用：按列排序。

参数：

- `df`: 输入 DataFrame
- `*cols`: 排序列；降序请使用 `desc("col")`

返回值：

- 排序后的 DataFrame

示例：

```python
arrange(df, "dept", desc("salary"))
```

说明：

- 普通字符串列名一律表示升序
- 降序请显式写成 `desc("salary")`
- 不传列时返回 `df.copy()`

### `desc(col)`

作用：生成降序排序描述，供 `arrange()` 使用。

参数：

- `col`: 列名

返回值：

- `SortSpec`

示例：

```python
arrange(df, "dept", desc("salary"))
```

### `rename_with(df, func, selector=None)`

作用：批量修改列名。

参数：

- `df`: 输入 DataFrame
- `func`: 接收列名字符串，返回新列名
- `selector`: 不传时对全部列生效

返回值：

- 新 DataFrame

示例：

```python
rename_with(df, str.lower)
rename_with(df, lambda c: c.replace("score_", ""), starts_with("score_"))
```

### `summarize(df, by=None, **kwargs)`

作用：做全局聚合或分组聚合。

参数：

- `df`: 输入 DataFrame
- `by`: 分组列，可为字符串、列表或 selector
- `**kwargs`: pandas 命名聚合参数

返回值：

- 聚合结果 DataFrame

示例：

```python
summarize(df, avg=("salary", "mean"))
summarize(df, by="dept", avg=("salary", "mean"), n=("id", "count"))
```

说明：

- 分组聚合时内部使用 `sort=False`
- 返回结果会 `reset_index()`

### `relocate(df, *cols, before=None, after=None)`

作用：移动列的位置。

参数：

- `df`: 输入 DataFrame
- `*cols`: 需要移动的列
- `before`: 移动到某列之前
- `after`: 移动到某列之后

返回值：

- 调整列顺序后的 DataFrame

示例：

```python
relocate(df, "id", "name")
relocate(df, "bonus", after="salary")
```

说明：

- `before` 和 `after` 不能同时传
- 默认移动到最前面

### `distinct(df, *cols, keep="first")`

作用：按指定列去重。

参数：

- `df`: 输入 DataFrame
- `*cols`: 去重依据列；不传时按整表去重
- `keep`: 传给 `drop_duplicates` 的 `keep` 参数

返回值：

- 去重后的 DataFrame

示例：

```python
distinct(df)
distinct(df, "dept")
```

### `count(df, *cols, sort=False, name="n")`

作用：按列分组计数。

参数：

- `df`: 输入 DataFrame
- `*cols`: 分组列
- `sort`: 是否按计数降序排列
- `name`: 计数字段名

返回值：

- 计数结果 DataFrame

示例：

```python
count(df, "dept")
count(df, "dept", sort=True, name="rows")
```

### `add_count(df, *cols, sort=False, name="n")`

作用：按列分组计数，并把计数结果追加回原表。

参数：

- `df`: 输入 DataFrame
- `*cols`: 分组列
- `sort`: 是否先对计数表按计数降序排列
- `name`: 计数字段名

返回值：

- 带计数字段的新 DataFrame

示例：

```python
add_count(df, "dept")
```

### `coalesce(*values)`

作用：按行返回第一个非缺失值。

参数：

- `values`: 一组 `Series` 或标量，至少要先传一个 `Series`

返回值：

- `Series`

示例：

```python
coalesce(df["score_math"], df["score_eng"], 0)
```

说明：

- 会按第一个 `Series` 的索引对齐
- 标量会自动扩展成同长度的 `Series`
- 当前实现要求标量不能放在第一个位置

### `if_else(condition, true, false)`

作用：按条件逐行选择两个分支中的值。

参数：

- `condition`: 布尔条件，可为 `Series`、列表或标量
- `true`: 条件为真时返回的值
- `false`: 条件为假时返回的值

返回值：

- `Series`

示例：

```python
if_else(df["score_math"] >= 90, "top", "other")
```

### `recode(s, mapping, default=None)`

作用：按映射表重编码一列的值。

参数：

- `s`: 输入 `Series`
- `mapping`: 旧值到新值的字典
- `default`: 映射不到时的默认值；不传时保留原值

返回值：

- `Series`

示例：

```python
recode(df["dept"], {"A": "Alpha", "B": "Beta"})
recode(df["dept"], {"A": "Alpha"}, default="Other")
```

### `case_when(*cases, default=None)`

作用：按条件依次选择值，适合构造分类列。

参数：

- `*cases`: 一组 `(condition, value)` 元组
- `default`: 默认值

返回值：

- `Series`

示例：

```python
case_when(
    (df["score_math"] >= 90, "A"),
    (df["score_math"] >= 80, "B"),
    default="C",
)
```

说明：

- 条件按书写顺序匹配
- 后匹配到的条件不会覆盖先匹配到的条件
- 至少需要一组条件或可推断长度的默认值

## stringr 风格

### `str_detect(s, pat, regex=True)`

作用：判断每个字符串是否匹配指定模式。

参数：

- `s`: 字符串 Series
- `pat`: 匹配模式
- `regex`: 是否按正则处理

返回值：

- 布尔 Series

示例：

```python
str_detect(df["name"], r"^A")
```

说明：

- 缺失值默认返回 `False`

### `str_extract(s, pat)`

作用：提取每个字符串中第一个匹配到的子串。

返回值：

- Series

### `str_replace(s, pat, repl)`

作用：替换每个字符串中第一个匹配项。

返回值：

- Series

### `str_replace_all(s, pat, repl)`

作用：替换每个字符串中的全部匹配项。

返回值：

- Series

### `str_remove(s, pat)`

作用：删除每个字符串中的匹配内容。

返回值：

- Series

### `str_split(s, pat)`

作用：按模式拆分字符串。

返回值：

- Series，每个元素通常是列表

### `str_trim(s)`

作用：去掉字符串首尾空白。

返回值：

- Series

### `str_pad(s, width, side="left", fillchar=" ")`

作用：把字符串补齐到指定宽度。

返回值：

- Series

### `str_to_lower(s)`

作用：转成小写。

返回值：

- Series

### `str_to_upper(s)`

作用：转成大写。

返回值：

- Series

### `str_to_title(s)`

作用：转成标题格式。

返回值：

- Series

### `str_count(s, pat)`

作用：统计每个字符串中模式出现的次数。

返回值：

- Series

### `str_length(s)`

作用：计算字符串长度。

返回值：

- Series

### `str_glue(template, df)`

作用：按模板把每一行格式化为字符串。

参数：

- `template`: `str.format(...)` 模板
- `df`: 输入 DataFrame

返回值：

- Series

示例：

```python
str_glue("{dept}-{id}", df)
```

说明：

- 当前实现基于逐行 `apply(...)`
- 表非常大时不适合高频调用

## tidyr 风格

### `pivot_longer(df, cols, names_to="name", values_to="value")`

作用：把宽表转成长表。

参数：

- `df`: 输入 DataFrame
- `cols`: 需要拉长的列
- `names_to`: 原列名写入的新列名
- `values_to`: 原值写入的新列名

返回值：

- 长表 DataFrame

示例：

```python
pivot_longer(df, starts_with("score_"), names_to="metric", values_to="value")
```

说明：

- 未被选中的列会自动作为 `id_vars`

### `pivot_wider(df, id_cols, names_from, values_from, aggfunc="first")`

作用：把长表转成宽表。

参数：

- `df`: 输入 DataFrame
- `id_cols`: 标识列
- `names_from`: 展开为列名的列
- `values_from`: 填入单元格值的列
- `aggfunc`: 重复键的聚合方式

返回值：

- 宽表 DataFrame

示例：

```python
pivot_wider(long_df, "id", "metric", "value")
```

### `separate(df, col, into, sep=r"[^a-zA-Z0-9]+")`

作用：把一列拆成多列。

参数：

- `df`: 输入 DataFrame
- `col`: 源列
- `into`: 目标列名列表
- `sep`: 分隔规则

返回值：

- 新 DataFrame

示例：

```python
separate(df, "code", ["letter", "num"], sep="-")
```

说明：

- 当前版本是严格模式
- 拆分段数和 `into` 长度不一致时会报错

### `unite(df, new_col, *cols, sep="_", remove=True, na_rm=False)`

作用：把多列合并成一列。

参数：

- `df`: 输入 DataFrame
- `new_col`: 新列名
- `*cols`: 需要合并的列
- `sep`: 分隔符
- `remove`: 是否删除原列
- `na_rm`: 是否在拼接前移除缺失值

返回值：

- 新 DataFrame

示例：

```python
unite(df, "code", "letter", "num", sep="-")
```

说明：

- 默认不会产生字符串 `"nan"`
- 缺失值会被转成空字符串

### `drop_na(df, *cols)`

作用：删除含缺失值的行。

参数：

- `df`: 输入 DataFrame
- `*cols`: 检查哪些列；不传时检查全部列

返回值：

- 新 DataFrame

示例：

```python
drop_na(df)
drop_na(df, "score_math")
```

### `na_if(s, value)`

作用：把指定值替换成缺失值。

参数：

- `s`: 输入 `Series`
- `value`: 要替换的目标值

返回值：

- `Series`

示例：

```python
na_if(pd.Series(["A", "N/A", "B"]), "N/A")
```

### `fill_na(df, *cols, direction="down")`

作用：按方向填充缺失值。

参数：

- `df`: 输入 DataFrame
- `*cols`: 需要填充的列；不传时对全部列生效
- `direction`: `"down"` 或 `"up"`

返回值：

- 新 DataFrame

示例：

```python
fill_na(df, "score_math", direction="down")
fill_na(df, direction="up")
```

说明：

- `"down"` 对应 `ffill`
- `"up"` 对应 `bfill`

### `replace_na(df, value)`

作用：用固定值替换缺失值。

参数：

- `df`: 输入 DataFrame
- `value`: 替换值

返回值：

- 新 DataFrame

示例：

```python
replace_na(df, 0)
replace_na(df, {"score_math": 0, "score_eng": 0})
```

### `remove_empty(df, axis="both")`

作用：删除全空行、全空列，或两者都删。

参数：

- `df`: 输入 DataFrame
- `axis`: `"rows"`、`"cols"` 或 `"both"`

返回值：

- 新 DataFrame

示例：

```python
remove_empty(df, axis="rows")
remove_empty(df, axis="both")
```

### `row_to_names(df, row=0, remove_row=True, reset_index=True)`

作用：把某一行提升为列名，适合清理脏 Excel 表头。

参数：

- `df`: 输入 DataFrame
- `row`: 作为表头的行号
- `remove_row`: 是否删除原始表头行
- `reset_index`: 是否重置索引

返回值：

- 新 DataFrame

示例：

```python
row_to_names(df, row=0)
```

说明：

- 新列名会自动经过 `make_clean_names(...)`
- `row` 超出范围时会抛 `IndexError`
