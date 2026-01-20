#!/usr/bin/env python3

import sys
import csv
import re
import osmium
import polyline


def encode_polyline(coords):
    """
    Encode coordinates as polyline string using Google's polyline algorithm
    """
    if not coords:
        return ""
    if len(coords) == 1:
        # Single point - just return lat,lon
        return None
    # Multiple points - encode as polyline
    return polyline.encode(coords)


class StreetHandler(osmium.SimpleHandler):
    """OSM handler to extract street names from various sources"""

    def __init__(self):
        osmium.SimpleHandler.__init__(self)
        self.streets = []
        self.nodes = {}

    def node(self, n):
        # Store node coordinates
        self.nodes[n.id] = (n.location.lat, n.location.lon)

    def way(self, w):
        # Check for highway with name
        if "highway" in w.tags and "name" in w.tags:
            name = w.tags["name"]
            coords = []
            for node_ref in w.nodes:
                if node_ref.ref in self.nodes:
                    coords.append(self.nodes[node_ref.ref])

            self.streets.append(
                {"name": name, "coords": coords, "osm_source": "highway_name"}
            )

        # Check for general name tags with street patterns
        elif "name" in w.tags and is_street_pattern(w.tags["name"]):
            name = w.tags["name"]
            coords = []
            for node_ref in w.nodes:
                if node_ref.ref in self.nodes:
                    coords.append(self.nodes[node_ref.ref])

            self.streets.append(
                {"name": name, "coords": coords, "osm_source": "name_pattern"}
            )


import math


def merge_street_polylines(streets, max_link_meters=25, precision=6):
    """
    Faster merge: uses a local meters approximation (no geopy),
    precomputes endpoints, and avoids repeated heavy distance calls.
    """

    def key(pt):
        return (round(pt[0], precision), round(pt[1], precision))

    def dedupe(coords):
        out = []
        seen = set()
        for pt in coords:
            k = key(pt)
            if k not in seen:
                seen.add(k)
                out.append(pt)
        return out

    def merge_segments(segments):
        segments = [s for s in segments if s and len(s) > 1]
        if not segments:
            return []

        # Use mean latitude to scale lon degrees -> meters
        # (good enough for local nearest-neighbor decisions)
        all_lats = []
        for s in segments:
            all_lats.append(s[0][0])
            all_lats.append(s[-1][0])
        mean_lat = sum(all_lats) / len(all_lats)
        cos_lat = math.cos(math.radians(mean_lat))

        # Fast approximate meters distance on lat/lon
        # 1 deg lat ~= 111_320m; 1 deg lon ~= 111_320m * cos(lat)
        def dist_m(a, b):
            dlat = (a[0] - b[0]) * 111_320.0
            dlon = (a[1] - b[1]) * 111_320.0 * cos_lat
            return math.hypot(dlat, dlon)

        # Precompute segment records
        segs = [{"coords": s, "start": s[0], "end": s[-1]} for s in segments]

        # Start from the longest segment
        start_i = max(range(len(segs)), key=lambda i: len(segs[i]["coords"]))
        path = list(segs[start_i]["coords"])
        segs.pop(start_i)

        while segs:
            head, tail = path[0], path[-1]
            best = None  # (d, idx, mode)

            for i, sg in enumerate(segs):
                s0, s1 = sg["start"], sg["end"]

                # 4 ways to connect, comparing endpoints only
                # mode implies whether to reverse segment and whether to prepend/append
                candidates = [
                    (dist_m(tail, s0), i, "append_fwd"),
                    (dist_m(tail, s1), i, "append_rev"),
                    (dist_m(head, s1), i, "prepend_fwd"),  # seg end meets head
                    (dist_m(head, s0), i, "prepend_rev"),
                ]
                c = min(candidates, key=lambda x: x[0])
                if best is None or c[0] < best[0]:
                    best = c

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
            else:  # prepend_rev
                path = list(reversed(coords)) + path

        return dedupe(path)

    # ---- group streets by name ----
    groups = {}
    for street in streets:
        name = street["name"]
        groups.setdefault(
            name, {"name": name, "coords_list": [], "osm_source": street["osm_source"]}
        )["coords_list"].append(street["coords"])

    # ---- merge per group ----
    merged = []
    for g in groups.values():
        coords = merge_segments(g["coords_list"])
        merged.append(
            {"name": g["name"], "polyline": encode_polyline(coords), "osm_source": g["osm_source"]}
        )

    return merged


def detect_polyline_issues(streets):
    """
    Detect duplicate geometries with different names and entries with no polyline.
    """
    polyline_to_names = {}
    non_streets = []

    for street in streets:
        polyline_str = street["polyline"]
        if not polyline_str:
            non_streets.append(street["name"])
            continue

        names = polyline_to_names.setdefault(polyline_str, set())
        names.add(street["name"])

    duplicate_polylines = {
        polyline_str: names
        for polyline_str, names in polyline_to_names.items()
        if len(names) > 1
    }

    return duplicate_polylines, non_streets


def extract_streets_from_osm(osm_file_path, output_csv_path):
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

    # Write to CSV
    with open(output_csv_path, "w", newline="", encoding="utf-8") as csv_file:
        fieldnames = ["name", "polyline", "osm_source"]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for street in merged_streets:
            writer.writerow(street)

    print(f"Saved to {output_csv_path}")


def is_street_pattern(name):
    """Check if name matches street patterns"""
    street_pattern = re.compile(
        r"\b("
        r"avenue|boulevard|central|circle|close|crescent|drive|expressway|"
        r"farmway|gardens|green|grove|heights|hill|lane|link|loop|parkway|"
        r"ring|rise|road|square|street|terrace|walk|way|jalan|lorong"
        r")\b",
        re.IGNORECASE,
    )
    return bool(street_pattern.search(name))


def main():
    osm_file = sys.argv[1]
    csv_file = sys.argv[2]

    extract_streets_from_osm(osm_file, csv_file)


if __name__ == "__main__":
    main()
