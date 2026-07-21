from __future__ import annotations

import csv
import gzip
import importlib.util
import json
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


ROOT = Path(__file__).resolve().parents[1]
BUILD_SITE = load_module("build_site", ROOT / "scripts" / "build_site.py")


class BuildSiteTests(unittest.TestCase):
    def test_load_streets_joins_tags_and_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            dataset = base / "dataset.csv"
            categories = base / "categories.csv"
            osm = base / "osm.csv"
            canonical = base / "canonical.csv"

            with open(dataset, "w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["street_name", "category", "polyline"])
                writer.writeheader()
                writer.writerow(
                    {
                        "street_name": "Orchard Road",
                        "category": "Trade & Industry",
                        "polyline": "abc",
                    }
                )

            with open(categories, "w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["street_name", "primary_category", "category", "tags"],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "street_name": "Orchard Road",
                        "primary_category": "trade_industry",
                        "category": "Trade & Industry",
                        "tags": "market|estate",
                    }
                )

            with open(osm, "w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle, fieldnames=["name", "polyline", "osm_source", "aliases"]
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "name": "Orchard Road",
                        "polyline": "abc",
                        "osm_source": "highway_name",
                        "aliases": "乌节路",
                    }
                )

            with open(canonical, "w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle, fieldnames=["canonical_name", "display_name", "aliases"]
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "canonical_name": "Orchard Road",
                        "display_name": "Orchard Road",
                        "aliases": "",
                    }
                )

            streets = BUILD_SITE.load_streets(dataset, categories, osm, canonical)
            self.assertEqual(len(streets), 1)
            self.assertEqual(streets[0]["name"], "Orchard Road")
            self.assertEqual(streets[0]["tags"], ["market", "estate"])
            self.assertIn("乌节路", streets[0]["aliases"])

    def test_build_site_writes_dist_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            dataset = base / "dataset.csv"
            categories = base / "categories.csv"
            osm = base / "osm.csv"
            canonical = base / "canonical.csv"
            static = ROOT / "site" / "static"
            dist = base / "dist"

            with open(dataset, "w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["street_name", "category", "polyline"])
                writer.writeheader()
                writer.writerow(
                    {
                        "street_name": "Stamford Road",
                        "category": "Colonial & British",
                        "polyline": "",
                    }
                )

            for path, fields, row in (
                (
                    categories,
                    ["street_name", "category", "tags"],
                    {
                        "street_name": "Stamford Road",
                        "category": "Colonial & British",
                        "tags": "",
                    },
                ),
                (
                    osm,
                    ["name", "polyline", "osm_source", "aliases"],
                    {
                        "name": "Stamford Road",
                        "polyline": "",
                        "osm_source": "highway_name",
                        "aliases": "",
                    },
                ),
                (
                    canonical,
                    ["canonical_name", "display_name", "aliases"],
                    {
                        "canonical_name": "Stamford Road",
                        "display_name": "Stamford Road",
                        "aliases": "",
                    },
                ),
            ):
                with open(path, "w", encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=fields)
                    writer.writeheader()
                    writer.writerow(row)

            meta = BUILD_SITE.build_site(
                dataset_path=dataset,
                categories_path=categories,
                osm_path=osm,
                canonical_path=canonical,
                static_path=static,
                dist_path=dist,
                base_path="/singapore-streets/",
            )
            self.assertEqual(meta["count"], 1)
            self.assertTrue((dist / "index.html").exists())
            self.assertTrue((dist / "app.js").exists())
            self.assertTrue((dist / "style.css").exists())
            self.assertTrue((dist / ".nojekyll").exists())

            gz_path = dist / "data" / "streets.json.gz"
            self.assertTrue(gz_path.exists())
            streets = json.loads(gzip.decompress(gz_path.read_bytes()).decode("utf-8"))
            self.assertEqual(streets[0]["name"], "Stamford Road")

            html = (dist / "index.html").read_text(encoding="utf-8")
            self.assertIn("/singapore-streets/app.js", html)


if __name__ == "__main__":
    unittest.main()
