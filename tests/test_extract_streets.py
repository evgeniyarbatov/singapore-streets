import csv
import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path

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

    def test_is_street_pattern_expanded_suffixes(self):
        for name in [
            "Marina Quay",
            "Raffles Place",
            "Bukit Timah",
            "Faber Mount",
            "Kampong Glam",
            "Harbour View",
        ]:
            self.assertTrue(MODULE.is_street_pattern(name), name)

    def test_resolve_name_and_aliases_prefers_name_tag(self):
        name, aliases = MODULE.resolve_name_and_aliases(
            {"name": "Orchard Road", "name:en": "Orchard Road", "alt_name": "Orchard Rd"}
        )
        self.assertEqual(name, "Orchard Road")
        self.assertEqual(aliases, ["Orchard Rd"])

    def test_resolve_name_and_aliases_falls_back_without_name_tag(self):
        name, aliases = MODULE.resolve_name_and_aliases(
            {"alt_name": "Old Holland Road", "old_name": "Holland Road"}
        )
        self.assertEqual(name, "Old Holland Road")
        self.assertEqual(aliases, ["Holland Road"])

    def test_resolve_name_and_aliases_no_name_at_all(self):
        name, aliases = MODULE.resolve_name_and_aliases({"highway": "residential"})
        self.assertIsNone(name)
        self.assertEqual(aliases, [])

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

    def test_merge_street_polylines_merges_aliases(self):
        streets = [
            {
                "name": "Test Street",
                "coords": [(1.0, 1.0), (1.0, 1.001)],
                "osm_source": "highway_name",
                "aliases": ["Old Test Street"],
            },
            {
                "name": "Test Street",
                "coords": [(1.0, 1.001), (1.0, 1.002)],
                "osm_source": "highway_name",
                "aliases": ["Test St"],
            },
        ]

        merged = MODULE.merge_street_polylines(streets, max_link_meters=200)

        self.assertEqual(merged[0]["aliases"], "Old Test Street|Test St")

    def test_write_review_queue(self):
        duplicate_polylines = {"abc": {"Alpha", "Beta"}}
        non_streets = ["Gamma"]

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "review-queue.csv"
            MODULE.write_review_queue(duplicate_polylines, non_streets, output_path)

            with open(output_path, newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))

        self.assertEqual(
            rows,
            [
                {"issue_type": "duplicate_polyline", "names": "Alpha|Beta", "polyline": "abc"},
                {"issue_type": "missing_polyline", "names": "Gamma", "polyline": ""},
            ],
        )


class FakeNodeRef:
    def __init__(self, ref):
        self.ref = ref


class FakeWay:
    def __init__(self, way_id, tags, node_refs):
        self.id = way_id
        self.tags = tags
        self.nodes = [FakeNodeRef(ref) for ref in node_refs]


class FakeMember:
    def __init__(self, member_type, ref):
        self.type = member_type
        self.ref = ref


class FakeRelation:
    def __init__(self, tags, members):
        self.tags = tags
        self.members = members


class TestStreetHandlerRelations(unittest.TestCase):
    def test_named_relation_stitches_member_way_coords(self):
        handler = MODULE.StreetHandler()
        handler.nodes = {1: (1.0, 1.0), 2: (1.0, 1.001)}

        # Member way carries no name of its own (common for relation-tagged
        # expressways split across many unnamed segments).
        handler.way(FakeWay(10, {"highway": "trunk"}, [1, 2]))

        handler.relation(
            FakeRelation(
                {"type": "route", "route": "road", "name": "Pan Island Expressway"},
                [FakeMember("w", 10)],
            )
        )

        self.assertEqual(len(handler.streets), 1)
        street = handler.streets[0]
        self.assertEqual(street["name"], "Pan Island Expressway")
        self.assertEqual(street["osm_source"], "relation_name")
        self.assertEqual(street["coords"], [(1.0, 1.0), (1.0, 1.001)])

    def test_unrelated_relation_is_ignored(self):
        handler = MODULE.StreetHandler()
        handler.nodes = {1: (1.0, 1.0), 2: (1.0, 1.001)}
        handler.way(FakeWay(10, {"highway": "trunk"}, [1, 2]))

        handler.relation(FakeRelation({"type": "multipolygon"}, [FakeMember("w", 10)]))

        self.assertEqual(len(handler.streets), 0)


if __name__ == "__main__":
    unittest.main()
