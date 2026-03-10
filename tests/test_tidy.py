import unittest

import pandas as pd

from tidypy.tidy import (
    add_count,
    arrange,
    case_when,
    count,
    desc,
    drop_na,
    fill_na,
    glimpse,
    mutate_across,
    numeric,
    pivot_longer,
    pivot_wider,
    relocate,
    rename_with,
    replace_na,
    select,
    separate,
    starts_with,
    str_detect,
    summarize,
    unite,
    where,
)


class TidyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.df = pd.DataFrame(
            {
                "id": [1, 2, 3],
                "dept": ["A", "A", "B"],
                "grp": ["X", "Y", "X"],
                "score_math": [90.0, None, 88.0],
                "score_eng": [85.0, 91.0, None],
                "name": [" Alice ", "Bob", "Anna"],
                "code": ["x-1", "y-2", "z-3"],
            }
        )

    def test_selector_union_preserves_order(self) -> None:
        result = select(self.df, "id", numeric() | starts_with("dept"))
        self.assertEqual(
            result.columns.tolist(),
            ["id", "score_math", "score_eng", "dept"],
        )

    def test_mutate_across_only_updates_target_columns(self) -> None:
        result = mutate_across(self.df, where(lambda s: s.isnull().any()), lambda s: s.fillna(0))
        self.assertEqual(result["score_math"].tolist(), [90.0, 0.0, 88.0])
        self.assertEqual(result["score_eng"].tolist(), [85.0, 91.0, 0.0])
        self.assertEqual(result["dept"].tolist(), self.df["dept"].tolist())

    def test_rename_with_and_relocate(self) -> None:
        renamed = rename_with(self.df, lambda c: c.replace("score_", ""), starts_with("score_"))
        moved = relocate(renamed, "name", after="id")
        self.assertEqual(
            moved.columns.tolist(),
            ["id", "name", "dept", "grp", "math", "eng", "code"],
        )

    def test_summarize_grouped(self) -> None:
        result = summarize(self.df, by="dept", avg=("score_math", "mean"))
        self.assertEqual(result.to_dict("records"), [{"dept": "A", "avg": 90.0}, {"dept": "B", "avg": 88.0}])

    def test_string_and_pivot_helpers(self) -> None:
        self.assertEqual(str_detect(self.df["name"], r"^A").tolist(), [False, False, True])
        longer = pivot_longer(self.df, starts_with("score_"), names_to="metric", values_to="value")
        wider = pivot_wider(longer, "id", "metric", "value")
        self.assertEqual(set(wider.columns), {"id", "score_math", "score_eng"})

    def test_summarize_and_pivot_multi_column_cases(self) -> None:
        summary = summarize(
            self.df,
            by=["dept", "grp"],
            avg=("score_math", "mean"),
            n=("id", "count"),
        )
        records = summary.to_dict("records")
        self.assertEqual(records[0], {"dept": "A", "grp": "X", "avg": 90.0, "n": 1})
        self.assertTrue(pd.isna(records[1]["avg"]))
        self.assertEqual(records[1]["dept"], "A")
        self.assertEqual(records[1]["grp"], "Y")
        self.assertEqual(records[1]["n"], 1)
        self.assertEqual(records[2], {"dept": "B", "grp": "X", "avg": 88.0, "n": 1})

        long_df = pivot_longer(
            self.df,
            ["score_math", "score_eng"],
            names_to="metric",
            values_to="value",
        )
        wide_df = pivot_wider(long_df, ["id", "dept"], "metric", "value")
        self.assertEqual(set(wide_df.columns), {"id", "dept", "score_math", "score_eng"})

    def test_separate_and_unite(self) -> None:
        separated = separate(self.df, "code", ["letter", "num"], sep="-")
        self.assertEqual(separated[["letter", "num"]].to_dict("records")[0], {"letter": "x", "num": "1"})

        reunited = unite(separated, "code2", "letter", "num", sep="-", remove=False)
        self.assertEqual(reunited["code2"].tolist(), ["x-1", "y-2", "z-3"])

    def test_na_helpers(self) -> None:
        dropped = drop_na(self.df, "score_math")
        self.assertEqual(dropped["id"].tolist(), [1, 3])

        filled = fill_na(self.df, "score_math", direction="down")
        self.assertEqual(filled["score_math"].tolist(), [90.0, 90.0, 88.0])

        replaced = replace_na(self.df, 0)
        self.assertEqual(replaced["score_eng"].tolist(), [85.0, 91.0, 0.0])

    def test_arrange_without_columns_returns_copy(self) -> None:
        result = arrange(self.df)
        self.assertTrue(result.equals(self.df))
        self.assertIsNot(result, self.df)

    def test_glimpse_returns_summary_dataframe(self) -> None:
        summary = glimpse(self.df, width=2, display=False)
        self.assertEqual(
            summary.columns.tolist(),
            ["column", "dtype", "non_null", "nulls", "n_unique", "preview"],
        )
        first_row = summary.iloc[0].to_dict()
        self.assertEqual(first_row["column"], "id")
        self.assertEqual(first_row["dtype"], str(self.df["id"].dtype))
        self.assertEqual(first_row["non_null"], 3)
        self.assertIn("1", first_row["preview"])

    def test_glimpse_supports_selector_and_text_mode(self) -> None:
        text = glimpse(self.df, cols=starts_with("score_"), width=1, as_text=True, display=False)
        self.assertIn("Rows: 3", text)
        self.assertIn("Columns: 2", text)
        self.assertIn("$ score_math", text)

    def test_glimpse_respects_max_width(self) -> None:
        summary = glimpse(self.df.assign(long_text=["abcdefghijklmnop"] * 3), cols=["long_text"], width=1, max_width=8, display=False)
        self.assertEqual(summary.iloc[0]["preview"], "'abcd...")

    def test_count_and_add_count(self) -> None:
        counted = count(self.df, "dept", sort=True)
        self.assertEqual(counted.to_dict("records"), [{"dept": "A", "n": 2}, {"dept": "B", "n": 1}])

        augmented = add_count(self.df, "dept")
        self.assertEqual(augmented["n"].tolist(), [2, 2, 1])

    def test_arrange_supports_desc_helper(self) -> None:
        result = arrange(self.df, desc("score_math"))
        self.assertEqual(result["id"].tolist(), [1, 3, 2])

    def test_arrange_treats_dash_prefixed_strings_as_literal_column_names(self) -> None:
        odd_df = self.df.rename(columns={"score_math": "-score_math"})
        result = arrange(odd_df, "-score_math")
        self.assertEqual(result["id"].tolist(), [3, 1, 2])

        result = arrange(odd_df, desc("-score_math"))
        self.assertEqual(result["id"].tolist(), [1, 3, 2])

        with self.assertRaises(KeyError):
            arrange(self.df, "-score_math")

    def test_case_when(self) -> None:
        result = case_when(
            (self.df["score_math"] >= 90, "A"),
            (self.df["score_math"] >= 80, "B"),
            default="C",
        )
        self.assertEqual(result.tolist(), ["A", "C", "B"])

    def test_errors_for_missing_and_invalid_arguments(self) -> None:
        with self.assertRaises(KeyError):
            select(self.df, "missing")
        with self.assertRaises(KeyError):
            pivot_wider(self.df, "id", "missing", "score_math")
        with self.assertRaises(ValueError):
            mutate_across(self.df, [], lambda s: s)
        with self.assertRaises(ValueError):
            separate(self.df, "code", ["a", "b", "c"], sep="-")
        with self.assertRaises(ValueError):
            fill_na(self.df, "score_math", direction="sideways")
        with self.assertRaises(ValueError):
            case_when(default="x")


if __name__ == "__main__":
    unittest.main()
