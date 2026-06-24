import importlib.util
import csv
import os
import sys
import tempfile
import unittest
from pathlib import Path


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
MIGRATE_MODULE = load_module("migrate_categories", SCRIPT_DIR / "migrate_categories.py")
TAXONOMY_PATH = Path(__file__).resolve().parents[1] / "data" / "taxonomy.yaml"


class TestMigrateCategories(unittest.TestCase):
    def setUp(self):
        MIGRATE_MODULE.get_taxonomy(TAXONOMY_PATH)

    def test_migrate_maps_rules_and_legacy_labels(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            names_path = Path(tmp_dir) / "names.txt"
            legacy_path = Path(tmp_dir) / "legacy.csv"
            output_path = Path(tmp_dir) / "output.csv"
            reviewed_path = Path(tmp_dir) / "reviewed.csv"

            names_path.write_text(
                "Jalan Besar\nRaffles Avenue\nUnknown Lane\n",
                encoding="utf-8",
            )
            legacy_path.write_text(
                "Raffles Avenue,Historical Figures\nUnknown Lane,Mystery Label\n",
                encoding="utf-8",
            )
            reviewed_path.write_text(
                "street_name,primary_category,tags,notes\n",
                encoding="utf-8",
            )

            stats = MIGRATE_MODULE.migrate(
                names_path,
                legacy_path,
                output_path,
                reviewed_path,
            )

            with open(output_path, "r", encoding="utf-8", newline="") as handle:
                rows = {row["street_name"]: row for row in csv.DictReader(handle)}

            self.assertEqual(rows["Jalan Besar"]["source"], "rule")
            self.assertEqual(rows["Jalan Besar"]["primary_category"], "malay_archipelago")
            self.assertEqual(rows["Raffles Avenue"]["source"], "rule")
            self.assertEqual(rows["Raffles Avenue"]["primary_category"], "colonial_british")
            self.assertEqual(rows["Unknown Lane"]["source"], "legacy_fallback")
            self.assertEqual(rows["Unknown Lane"]["primary_category"], "abstract_modern")
            self.assertEqual(stats["total"], 3)


if __name__ == "__main__":
    unittest.main()