from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from types import ModuleType


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "canonical_streets.py"
MODULE = load_module("canonical_streets", SCRIPT_PATH)


class TestCanonicalStreets(unittest.TestCase):
    def test_canonicalize_strips_direction(self) -> None:
        self.assertEqual(MODULE.canonicalize("Joo Chiat Road East"), "Joo Chiat Road")
        self.assertEqual(MODULE.canonicalize("Joo Chiat Road"), "Joo Chiat Road")

    def test_build_canonical_table_groups_direction_variants(self) -> None:
        names = ["Joo Chiat Road", "Joo Chiat Road East", "Joo Chiat Road West", "Orchard Road"]

        rows = MODULE.build_canonical_table(names)
        by_canonical = {row["canonical_name"]: row for row in rows}

        self.assertEqual(by_canonical["Joo Chiat Road"]["display_name"], "Joo Chiat Road")
        self.assertEqual(
            by_canonical["Joo Chiat Road"]["aliases"],
            "Joo Chiat Road East|Joo Chiat Road West",
        )
        self.assertEqual(by_canonical["Orchard Road"]["display_name"], "Orchard Road")
        self.assertEqual(by_canonical["Orchard Road"]["aliases"], "")

    def test_build_canonical_table_without_bare_form(self) -> None:
        names = ["Foo Road East", "Foo Road West"]

        rows = MODULE.build_canonical_table(names)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["canonical_name"], "Foo Road")
        self.assertEqual(rows[0]["display_name"], "Foo Road East")
        self.assertEqual(rows[0]["aliases"], "Foo Road West")

    def test_write_canonical_table(self) -> None:
        rows = [{"canonical_name": "Orchard Road", "display_name": "Orchard Road", "aliases": ""}]

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "canonical-streets.csv"
            MODULE.write_canonical_table(rows, output_path)
            content = output_path.read_text(encoding="utf-8")

        self.assertIn("canonical_name,display_name,aliases", content)
        self.assertIn("Orchard Road,Orchard Road,", content)


if __name__ == "__main__":
    unittest.main()
