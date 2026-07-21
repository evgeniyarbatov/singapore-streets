#!/usr/bin/env python3

from __future__ import annotations

import csv
import math
import re
import sys
from pathlib import Path
from typing import Any

import osmium
import polyline

# Tags consulted (in priority order) when a way/relation has no plain "name".
# Also merged as aliases of the primary name when present.
ALIAS_TAGS = ["name:en", "name:ms", "name:zh", "alt_name", "old_name"]


def resolve_name_and_aliases(tags: dict[str, str]) -> tuple[str | None, list[str]]:
    """
    Pick a primary name and a set of aliases from an OSM tags mapping.

    Falls back through ALIAS_TAGS when "name" is missing (e.g. a way only
    tagged with alt_name/old_name), so streets are not silently dropped.
    """
    alias_values = [tags[t] for t in ALIAS_TAGS if t in tags]

    if "name" in tags:
        name = tags["name"]
    elif alias_values:
        name = alias_values[0]
        alias_values = alias_values[1:]
    else:
        return None, []

    aliases = sorted({value for value in alias_values if value and value != name})
    return name, aliases


# Separator between independent Google-encoded polylines for one street.
# Google polyline characters are ASCII 63–126 (?..~); ';' (59) cannot appear.
POLYLINE_SEP = ";"


def encode_polyline(coords: list[tuple[float, float]]) -> str | None:
    """
    Encode coordinates as polyline string using Google's polyline algorithm
    """
    if not coords:
        return ""
    if len(coords) == 1:
        return None
    result: str = polyline.encode(coords)
    return result


def encode_polylines(paths: list[list[tuple[float, float]]]) -> str:
    """Encode one or more coordinate paths; join independent paths with POLYLINE_SEP."""
    parts: list[str] = []
    for coords in paths:
        encoded = encode_polyline(coords)
        if encoded:
            parts.append(encoded)
    return POLYLINE_SEP.join(parts)


class StreetHandler(osmium.SimpleHandler):
    """OSM handler to extract street names from various sources"""

    def __init__(self) -> None:
        osmium.SimpleHandler.__init__(self)
        self.streets: list[dict[str, Any]] = []
        self.nodes: dict[int, tuple[float, float]] = {}
        self.ways_by_id: dict[int, list[tuple[float, float]]] = {}

    def node(self, n: Any) -> None:
        # Store node coordinates
        self.nodes[n.id] = (n.location.lat, n.location.lon)

    def _way_coords(self, w: Any) -> list[tuple[float, float]]:
        coords = []
        for node_ref in w.nodes:
            if node_ref.ref in self.nodes:
                coords.append(self.nodes[node_ref.ref])
        return coords

    def way(self, w: Any) -> None:
        coords = self._way_coords(w)
        # Keep every way's coords so named relations can stitch member
        # geometries together once all ways have been seen.
        self.ways_by_id[w.id] = coords

        name, aliases = resolve_name_and_aliases(w.tags)
        if name is None:
            return

        if "highway" in w.tags:
            self.streets.append(
                {
                    "name": name,
                    "coords": coords,
                    "osm_source": "highway_name",
                    "aliases": aliases,
                }
            )
        elif is_street_pattern(name):
            self.streets.append(
                {
                    "name": name,
                    "coords": coords,
                    "osm_source": "name_pattern",
                    "aliases": aliases,
                }
            )

    def relation(self, r: Any) -> None:
        # Named relations: route=road (expressways, major roads tagged as
        # routes) or any relation carrying a highway tag directly.
        is_road_route = r.tags.get("type") == "route" and r.tags.get("route") == "road"
        if not (is_road_route or "highway" in r.tags):
            return

        name, aliases = resolve_name_and_aliases(r.tags)
        if name is None:
            return

        for member in r.members:
            if member.type != "w" or member.ref not in self.ways_by_id:
                continue
            coords = self.ways_by_id[member.ref]
            if not coords:
                continue
            self.streets.append(
                {
                    "name": name,
                    "coords": coords,
                    "osm_source": "relation_name",
                    "aliases": aliases,
                }
            )


def merge_street_polylines(
    streets: list[dict[str, Any]], max_link_meters: float = 25, precision: int = 6
) -> list[dict[str, Any]]:
    """
    Group ways by name and stitch collinear segments into paths.

    Segments whose endpoints are within max_link_meters are chained into one
    path. When a name has forks (Y-junctions), dual carriageways, or other
    geometry that cannot form a single chain, remaining segments become
    additional paths. The CSV field is one or more Google polylines joined by
    POLYLINE_SEP — nothing is dropped just because it is not on the first chain.
    """

    def key(pt: tuple[float, float]) -> tuple[float, float]:
        return (round(pt[0], precision), round(pt[1], precision))

    def dedupe(coords: list[tuple[float, float]]) -> list[tuple[float, float]]:
        out = []
        seen = set()
        for pt in coords:
            k = key(pt)
            if k not in seen:
                seen.add(k)
                out.append(pt)
        return out

    def merge_segments(
        segments: list[list[tuple[float, float]]],
    ) -> list[list[tuple[float, float]]]:
        segments = [s for s in segments if s and len(s) > 1]
        if not segments:
            return []

        all_lats = []
        for s in segments:
            all_lats.append(s[0][0])
            all_lats.append(s[-1][0])
        mean_lat = sum(all_lats) / len(all_lats)
        cos_lat = math.cos(math.radians(mean_lat))

        def dist_m(a: tuple[float, float], b: tuple[float, float]) -> float:
            dlat = (a[0] - b[0]) * 111_320.0
            dlon = (a[1] - b[1]) * 111_320.0 * cos_lat
            return math.hypot(dlat, dlon)

        segs: list[dict[str, Any]] = [{"coords": s, "start": s[0], "end": s[-1]} for s in segments]
        paths: list[list[tuple[float, float]]] = []

        while segs:
            start_i = max(range(len(segs)), key=lambda i: len(segs[i]["coords"]))
            path = list(segs[start_i]["coords"])
            segs.pop(start_i)

            while segs:
                head, tail = path[0], path[-1]
                best: tuple[float, int, str] | None = None

                for i, sg in enumerate(segs):
                    s0, s1 = sg["start"], sg["end"]
                    candidates = [
                        (dist_m(tail, s0), i, "append_fwd"),
                        (dist_m(tail, s1), i, "append_rev"),
                        (dist_m(head, s1), i, "prepend_fwd"),
                        (dist_m(head, s0), i, "prepend_rev"),
                    ]
                    c = min(candidates, key=lambda x: x[0])
                    if best is None or c[0] < best[0]:
                        best = c

                assert best is not None
                d, idx, mode = best
                if d > max_link_meters:
                    break

                sg = segs.pop(idx)
                coords = sg["coords"]

                if mode == "append_fwd":
                    path.extend(coords)
                elif mode == "append_rev":
                    path.extend(reversed(coords))
                elif mode == "prepend_fwd":
                    path = coords + path
                else:
                    path = list(reversed(coords)) + path

            paths.append(dedupe(path))

        return paths

    groups: dict[str, dict[str, Any]] = {}
    for street in streets:
        name = street["name"]
        group = groups.setdefault(
            name,
            {
                "name": name,
                "coords_list": [],
                "osm_source": street["osm_source"],
                "aliases": set(),
            },
        )
        group["coords_list"].append(street["coords"])
        group["aliases"].update(street.get("aliases", []))

    merged: list[dict[str, Any]] = []
    for g in groups.values():
        paths = merge_segments(g["coords_list"])
        merged.append(
            {
                "name": g["name"],
                "polyline": encode_polylines(paths),
                "osm_source": g["osm_source"],
                "aliases": "|".join(sorted(g["aliases"])),
            }
        )

    return merged


def detect_polyline_issues(
    streets: list[dict[str, Any]],
) -> tuple[dict[str, set[str]], list[str]]:
    """
    Detect duplicate geometries with different names and entries with no polyline.
    """
    polyline_to_names: dict[str, set[str]] = {}
    non_streets: list[str] = []

    for street in streets:
        polyline_str = street["polyline"]
        if not polyline_str:
            non_streets.append(street["name"])
            continue

        names = polyline_to_names.setdefault(polyline_str, set())
        names.add(street["name"])

    duplicate_polylines = {
        polyline_str: names for polyline_str, names in polyline_to_names.items() if len(names) > 1
    }

    return duplicate_polylines, non_streets


def write_street_names(streets: list[dict[str, Any]], output_path: str | Path) -> None:
    names = sorted({street["name"] for street in streets})
    with open(output_path, "w", encoding="utf-8") as names_file:
        for name in names:
            names_file.write(f"{name}\n")


def write_review_queue(
    duplicate_polylines: dict[str, set[str]],
    non_streets: list[str],
    output_path: str | Path,
) -> None:
    """
    Write polyline issues (duplicate geometries, missing polylines) to a CSV
    so they can be triaged instead of only scrolling past on stderr.
    """
    with open(output_path, "w", newline="", encoding="utf-8") as review_file:
        writer = csv.writer(review_file)
        writer.writerow(["issue_type", "names", "polyline"])

        for polyline_str, names in duplicate_polylines.items():
            writer.writerow(["duplicate_polyline", "|".join(sorted(names)), polyline_str])

        for name in sorted(set(non_streets)):
            writer.writerow(["missing_polyline", name, ""])


def extract_streets_from_osm(
    osm_file_path: str,
    output_csv_path: str,
    street_names_path: str | None = None,
    review_queue_path: str | None = None,
) -> None:
    """
    Extract street names, coordinates, and source tags from OSM file using osmium
    """

    print("Processing OSM file with osmium...")

    handler = StreetHandler()
    handler.apply_file(osm_file_path)

    print(f"Extracted {len(handler.streets)} street entries")

    # Group streets by name and merge polylines
    merged_streets = merge_street_polylines(handler.streets)

    print(f"Merged into {len(merged_streets)} unique streets")

    duplicate_polylines, non_streets = detect_polyline_issues(merged_streets)

    if non_streets:
        print(
            f"Found {len(non_streets)} entries with no polyline (likely not streets)",
            file=sys.stderr,
        )
        for name in sorted(set(non_streets)):
            print(f"  {name}", file=sys.stderr)

    if duplicate_polylines:
        print(
            f"Found {len(duplicate_polylines)} duplicate polylines with different names",
            file=sys.stderr,
        )
        for names in duplicate_polylines.values():
            print(f"  {', '.join(sorted(names))}", file=sys.stderr)

    if review_queue_path:
        write_review_queue(duplicate_polylines, non_streets, review_queue_path)
        print(f"Saved review queue to {review_queue_path}")

    # Write to CSV
    with open(output_csv_path, "w", newline="", encoding="utf-8") as csv_file:
        fieldnames = ["name", "polyline", "osm_source", "aliases"]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for street in merged_streets:
            writer.writerow(street)

    print(f"Saved to {output_csv_path}")

    if street_names_path:
        write_street_names(merged_streets, street_names_path)
        print(f"Saved to {street_names_path}")


def is_street_pattern(name: str) -> bool:
    """Check if name matches street patterns"""
    street_pattern = re.compile(
        r"\b("
        r"avenue|boulevard|bukit|central|circle|close|crescent|drive|expressway|"
        r"farmway|gardens|green|grove|heights|hill|jalan|kampong|lane|link|loop|"
        r"lorong|mount|parkway|place|quay|rise|ring|road|square|street|"
        r"terrace|view|walk|way"
        r")\b",
        re.IGNORECASE,
    )
    return bool(street_pattern.search(name))


def main() -> None:
    osm_file = sys.argv[1]
    csv_file = sys.argv[2]
    street_names_file = sys.argv[3] if len(sys.argv) > 3 else None
    review_queue_file = sys.argv[4] if len(sys.argv) > 4 else None

    extract_streets_from_osm(osm_file, csv_file, street_names_file, review_queue_file)


if __name__ == "__main__":
    main()
