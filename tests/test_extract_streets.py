import sys
import types
import unittest
from pathlib import Path
import importlib.util

try:
    import polyline
except ModuleNotFoundError:
    def _encode(coords):
        return "|".join(f"{lat},{lon}" for lat, lon in coords)

    def _decode(value):
        if not value:
            return []
        return [tuple(map(float, pair.split(","))) for pair in value.split("|")]

    polyline = types.SimpleNamespace(encode=_encode, decode=_decode)
    sys.modules["polyline"] = polyline


def load_module(name, path):
    if "osmium" not in sys.modules:
        class SimpleHandler:
            def __init__(self):
                pass

        sys.modules["osmium"] = types.SimpleNamespace(SimpleHandler=SimpleHandler)

    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "extract_streets.py"
MODULE = load_module("extract_streets", SCRIPT_PATH)


class TestExtractStreets(unittest.TestCase):
    def test_is_street_pattern(self):
        self.assertTrue(MODULE.is_street_pattern("Orchard Road"))
        self.assertFalse(MODULE.is_street_pattern("Sunset Valley"))

    def test_merge_street_polylines(self):
        streets = [
            {
                "name": "Test Street",
                "coords": [(1.0, 1.0), (1.0, 1.001)],
                "osm_source": "highway_name",
            },
            {
                "name": "Test Street",
                "coords": [(1.0, 1.001), (1.0, 1.002)],
                "osm_source": "highway_name",
            },
        ]

        merged = MODULE.merge_street_polylines(streets, max_link_meters=200)

        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["name"], "Test Street")

        decoded = polyline.decode(merged[0]["polyline"])
        self.assertEqual(decoded, [(1.0, 1.0), (1.0, 1.001), (1.0, 1.002)])

    def test_detect_polyline_issues(self):
        streets = [
            {"name": "Alpha", "polyline": "abc"},
            {"name": "Beta", "polyline": "abc"},
            {"name": "Gamma", "polyline": None},
        ]

        duplicates, non_streets = MODULE.detect_polyline_issues(streets)

        self.assertEqual(duplicates["abc"], {"Alpha", "Beta"})
        self.assertEqual(set(non_streets), {"Gamma"})


if __name__ == "__main__":
    unittest.main()
