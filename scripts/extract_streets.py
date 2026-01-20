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


def merge_street_polylines(streets):
    """
    Group streets by name and merge their coordinate lists
    """
    street_groups = {}

    # Group by name
    for street in streets:
        name = street["name"]
        if name not in street_groups:
            street_groups[name] = {
                "name": name,
                "coords_list": [],
                "osm_source": street["osm_source"],
            }
        street_groups[name]["coords_list"].append(street["coords"])

    # Merge coordinates and encode as polylines
    merged_streets = []
    for street_data in street_groups.values():
        # Flatten all coordinate lists for this street
        all_coords = []
        for coords in street_data["coords_list"]:
            all_coords.extend(coords)

        # Remove duplicates while preserving order
        unique_coords = []
        seen = set()
        for coord in all_coords:
            coord_key = (round(coord[0], 6), round(coord[1], 6))
            if coord_key not in seen:
                seen.add(coord_key)
                unique_coords.append(coord)

        polyline_str = encode_polyline(unique_coords)
        merged_streets.append(
            {
                "name": street_data["name"],
                "polyline": polyline_str,
                "osm_source": street_data["osm_source"],
            }
        )

    return merged_streets


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
