from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from types import ModuleType


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "name_elements.py"
MODULE = load_module("name_elements", SCRIPT_PATH)

ROWS = [
    {"street_name": n, "category": c}
    for n, c in [
        ("Lorong 1 Geylang", "numeric_functional"),
        ("Lorong 2 Geylang", "numeric_functional"),
        ("Tampines Avenue 1", "housing_development"),
        ("Tampines Road", "housing_development"),
        ("Bedok North Road", "housing_development"),
        ("Bedok Road", "housing_development"),
        ("Jalan Besar", "malay_archipelago"),
        ("Jalan Road", "malay_archipelago"),
        ("Jurong West Avenue 1", "housing_development"),
    ]
]


class TestNameElements(unittest.TestCase):
    def setUp(self) -> None:
        self.facts = MODULE.build_facts(ROWS, generic_min=2)

    def test_elements_skip_numbers(self) -> None:
        self.assertEqual(self.facts["elements"]["Lorong"]["count"], 2)
        self.assertNotIn("1", self.facts["elements"])

    def test_series_group_numbered_templates(self) -> None:
        self.assertEqual(
            self.facts["series"]["Lorong N Geylang"], ["Lorong 1 Geylang", "Lorong 2 Geylang"]
        )

    def test_families_need_generic_suffix_and_distinct_forms(self) -> None:
        families = self.facts["families"]
        self.assertEqual(families["Tampines"], ["Tampines Avenue 1", "Tampines Road"])
        self.assertNotIn("Bedok", families)
        self.assertNotIn("Jalan", families)
        self.assertNotIn("Jurong", families)


if __name__ == "__main__":
    unittest.main()
