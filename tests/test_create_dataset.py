import csv
import os
import runpy
import sys
import tempfile
import unittest
from pathlib import Path


class DataFrame:
    def __init__(self, rows, columns):
        self._rows = rows
        self._columns = columns

    def merge(self, other, on, how):
        right_index = {}
        for row in other._rows:
            right_index.setdefault(row.get(on), []).append(row)

        rows = []
        for left_row in self._rows:
            matches = right_index.get(left_row.get(on))
            if matches:
                for match in matches:
                    merged = dict(left_row)
                    for key, value in match.items():
                        if key not in merged:
                            merged[key] = value
                    rows.append(merged)
            elif how == "left":
                merged = dict(left_row)
                for key in other._columns:
                    if key != on:
                        merged.setdefault(key, None)
                rows.append(merged)

        columns = list(self._columns)
        for key in other._columns:
            if key not in columns:
                columns.append(key)
        return DataFrame(rows, columns)

    def rename(self, columns):
        mapping = columns or {}
        self._columns = [mapping.get(col, col) for col in self._columns]
        self._rows = [
            {mapping.get(col, col): value for col, value in row.items()}
            for row in self._rows
        ]
        return self

    def __getitem__(self, columns):
        rows = [
            {col: row.get(col) for col in columns}
            for row in self._rows
        ]
        return DataFrame(rows, list(columns))

    @property
    def columns(self):
        return self._columns

    @columns.setter
    def columns(self, values):
        mapping = dict(zip(self._columns, values))
        self._columns = list(values)
        self._rows = [
            {mapping.get(col, col): value for col, value in row.items()}
            for row in self._rows
        ]

    def to_csv(self, path, index=False):
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=self._columns)
            writer.writeheader()
            for row in self._rows:
                writer.writerow({col: row.get(col) for col in self._columns})


def read_csv(path, header="infer"):
    with open(path, "r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        rows = list(reader)

    if not rows:
        return DataFrame([], [])

    if header is None:
        columns = list(range(len(rows[0])))
        data = [
            {columns[i]: value for i, value in enumerate(row)}
            for row in rows
        ]
    else:
        columns = rows[0]
        data = [
            {columns[i]: value for i, value in enumerate(row)}
            for row in rows[1:]
        ]
    return DataFrame(data, columns)


class PandasStub:
    @staticmethod
    def read_csv(path, header="infer"):
        return read_csv(path, header=header)


def run_script(path):
    try:
        import pandas  # noqa: F401
        runpy.run_path(str(path), run_name="__main__")
    except ModuleNotFoundError:
        sys.modules["pandas"] = PandasStub()
        runpy.run_path(str(path), run_name="__main__")
        sys.modules.pop("pandas", None)


class TestCreateDataset(unittest.TestCase):
    def test_creates_dataset_csv(self):
        script_path = Path(__file__).resolve().parents[1] / "scripts" / "create-dataset.py"
        with tempfile.TemporaryDirectory() as tmp_dir:
            data_dir = Path(tmp_dir) / "data"
            data_dir.mkdir(parents=True, exist_ok=True)

            (Path(tmp_dir) / "singapore-streets.txt").write_text(
                "Alpha Street\nBeta Street\n",
                encoding="utf-8",
            )
            (Path(tmp_dir) / "street_categories.csv").write_text(
                "Alpha Street,Category A\nGamma Street,Category C\n",
                encoding="utf-8",
            )
            (data_dir / "singapore-streets.csv").write_text(
                "name,polyline\nAlpha Street,abc\n",
                encoding="utf-8",
            )

            old_cwd = os.getcwd()
            os.chdir(tmp_dir)
            try:
                run_script(script_path)
            finally:
                os.chdir(old_cwd)

            output_path = Path(tmp_dir) / "dataset" / "singapore-streets.csv"
            with open(output_path, "r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))

            self.assertEqual(rows, [{
                "street_name": "Alpha Street",
                "category": "Category A",
                "polyline": "abc",
            }])


if __name__ == "__main__":
    unittest.main()
