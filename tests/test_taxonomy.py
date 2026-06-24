import importlib.util
import unittest
from pathlib import Path


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
TAXONOMY_MODULE = load_module("taxonomy", SCRIPT_DIR / "taxonomy.py")
TAXONOMY_PATH = Path(__file__).resolve().parents[1] / "data" / "taxonomy.yaml"


class TestTaxonomy(unittest.TestCase):
    def setUp(self):
        self.taxonomy = TAXONOMY_MODULE.load_taxonomy(TAXONOMY_PATH)

    def test_loads_primary_categories(self):
        self.assertIn("colonial_british", self.taxonomy.categories)
        self.assertIn("uncategorized", self.taxonomy.categories)
        self.assertLessEqual(len(self.taxonomy.categories), 20)

    def test_classify_jalan_as_malay(self):
        result = self.taxonomy.classify_by_rules("Jalan Besar")
        self.assertIsNotNone(result)
        self.assertEqual(result.category_id, "malay_archipelago")

    def test_classify_numbered_avenue(self):
        result = self.taxonomy.classify_by_rules("Ang Mo Kio Avenue 1")
        self.assertIsNotNone(result)
        self.assertEqual(result.category_id, "numeric_functional")

    def test_classify_colonial_surname(self):
        result = self.taxonomy.classify_by_rules("Raffles Avenue")
        self.assertIsNotNone(result)
        self.assertEqual(result.category_id, "colonial_british")

    def test_legacy_historical_figures_maps_to_commemorative(self):
        result = self.taxonomy.classify_legacy_label("Historical Figures")
        self.assertIsNotNone(result)
        self.assertEqual(result.category_id, "commemorative_persons")

    def test_legacy_botanical_maps_to_nature(self):
        result = self.taxonomy.classify_legacy_label("Botanical")
        self.assertIsNotNone(result)
        self.assertEqual(result.category_id, "nature_geography")


if __name__ == "__main__":
    unittest.main()