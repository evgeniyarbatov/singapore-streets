import csv
import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
OVERRIDES_MODULE = load_module(
    "category_overrides",
    SCRIPTS_DIR / "category_overrides.py",
)
TAXONOMY_PATH = Path(__file__).resolve().parents[1] / "data" / "taxonomy.yaml"


class TestCategoryOverrides(unittest.TestCase):
    def setUp(self):
        OVERRIDES_MODULE.get_taxonomy(TAXONOMY_PATH)

    def test_load_overrides_accepts_category_ids(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            override_path = os.path.join(tmp_dir, "overrides.csv")
            with open(override_path, "w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=OVERRIDES_MODULE.OVERRIDE_FIELDS)
                writer.writeheader()
                writer.writerow(
                    {
                        "street_name": "Adam Drive",
                        "category": "commemorative_persons",
                    }
                )

            overrides = OVERRIDES_MODULE.load_overrides(override_path)

            self.assertEqual(len(overrides), 1)
            entry = overrides["Adam Drive"]
            self.assertEqual(entry.primary_category, "commemorative_persons")

    def test_load_overrides_accepts_display_names(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            override_path = os.path.join(tmp_dir, "overrides.csv")
            with open(override_path, "w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=OVERRIDES_MODULE.OVERRIDE_FIELDS)
                writer.writeheader()
                writer.writerow(
                    {
                        "street_name": "Adam Drive",
                        "category": "Commemorative & Persons",
                    }
                )

            overrides = OVERRIDES_MODULE.load_overrides(override_path)

            self.assertEqual(overrides["Adam Drive"].primary_category, "commemorative_persons")

    def test_apply_overrides_to_rows_replaces_existing_category(self):
        rows = [
            {
                "street_name": "Adam Drive",
                "primary_category": "housing_development",
                "category": "Housing & Development",
                "tags": "estate",
                "source": "llm",
            }
        ]
        overrides = {
            "Adam Drive": OVERRIDES_MODULE.CategoryOverride(
                street_name="Adam Drive",
                primary_category="commemorative_persons",
            )
        }

        merged = OVERRIDES_MODULE.apply_overrides_to_rows(rows, overrides)

        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["primary_category"], "commemorative_persons")
        self.assertEqual(merged[0]["category"], "Commemorative & Persons")
        self.assertEqual(merged[0]["source"], "override")
        self.assertEqual(merged[0]["tags"], "")


if __name__ == "__main__":
    unittest.main()