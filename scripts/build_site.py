#!/usr/bin/env python3
"""Build the static catalog site under site/dist/ for local serve and GitHub Pages."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "dataset" / "singapore-streets.csv"
DEFAULT_CATEGORIES = ROOT / "data" / "street_categories.csv"
DEFAULT_OSM = ROOT / "data" / "osm-streets.csv"
DEFAULT_CANONICAL = ROOT / "data" / "canonical-streets.csv"
DEFAULT_STATIC = ROOT / "site" / "static"
DEFAULT_DIST = ROOT / "site" / "dist"

CATEGORY_COLORS: dict[str, str] = {
    "Colonial & British": "#8B4513",
    "Malay & Archipelago": "#2E8B57",
    "Chinese Dialect & Clan": "#C41E3A",
    "Tamil & South Asian": "#DAA520",
    "Nature & Geography": "#228B22",
    "Trade & Industry": "#4682B4",
    "Institutions & Public": "#6A5ACD",
    "Housing & Development": "#20B2AA",
    "Commemorative & Persons": "#B8860B",
    "Abstract & Modern": "#FF6B6B",
    "Numeric & Functional": "#708090",
    "Uncategorized": "#A0A0A0",
}


def _split_pipe(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [part.strip() for part in raw.split("|") if part.strip()]


def load_tags_by_name(path: Path) -> dict[str, list[str]]:
    if not path.exists():
        return {}
    out: dict[str, list[str]] = {}
    with open(path, encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            name = (row.get("street_name") or "").strip()
            if not name:
                continue
            out[name] = _split_pipe(row.get("tags"))
    return out


def load_aliases_by_name(osm_path: Path, canonical_path: Path) -> dict[str, list[str]]:
    aliases: dict[str, set[str]] = {}

    def add(name: str, values: list[str]) -> None:
        if not name:
            return
        bucket = aliases.setdefault(name, set())
        for value in values:
            if value and value != name:
                bucket.add(value)

    if osm_path.exists():
        with open(osm_path, encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                name = (row.get("name") or "").strip()
                add(name, _split_pipe(row.get("aliases")))

    if canonical_path.exists():
        with open(canonical_path, encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                display = (row.get("display_name") or "").strip()
                canonical = (row.get("canonical_name") or "").strip()
                related = _split_pipe(row.get("aliases"))
                group = {display, canonical, *related}
                group.discard("")
                for name in group:
                    add(name, sorted(group))

    return {name: sorted(values) for name, values in aliases.items()}


def load_streets(
    dataset_path: Path,
    categories_path: Path,
    osm_path: Path,
    canonical_path: Path,
) -> list[dict[str, Any]]:
    tags_by_name = load_tags_by_name(categories_path)
    aliases_by_name = load_aliases_by_name(osm_path, canonical_path)

    streets: list[dict[str, Any]] = []
    with open(dataset_path, encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            name = (row.get("street_name") or "").strip()
            if not name:
                continue
            category = (row.get("category") or "Uncategorized").strip() or "Uncategorized"
            polyline = (row.get("polyline") or "").strip()
            streets.append(
                {
                    "name": name,
                    "category": category,
                    "tags": tags_by_name.get(name, []),
                    "aliases": aliases_by_name.get(name, []),
                    "polyline": polyline,
                    "district": (row.get("district") or "").strip(),
                    "etymology": (
                        row.get("etymology_short") or row.get("etymology") or ""
                    ).strip(),
                    "memory_note": (row.get("memory_note") or "").strip(),
                }
            )

    streets.sort(key=lambda item: item["name"].casefold())
    return streets


def build_meta(streets: list[dict[str, Any]], base_path: str) -> dict[str, Any]:
    categories = sorted({street["category"] for street in streets})
    tag_counts: Counter[str] = Counter()
    for street in streets:
        for tag in street["tags"]:
            tag_counts[tag] += 1
    return {
        "title": "Singapore Streets",
        "count": len(streets),
        "base_path": base_path,
        "categories": categories,
        "category_colors": {
            category: CATEGORY_COLORS.get(category, "#666666") for category in categories
        },
        "tags": [tag for tag, _ in tag_counts.most_common()],
        "has_district": any(street["district"] for street in streets),
    }


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
        handle.write("\n")


def write_json_gzip(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    with gzip.open(path, "wb", compresslevel=9) as handle:
        handle.write(raw)


def write_index_html(path: Path, meta: dict[str, Any]) -> None:
    base = meta["base_path"]
    if not base.endswith("/"):
        base = base + "/"
    count = int(meta["count"])
    site_base_js = json.dumps(base)
    html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Singapore Streets</title>
  <meta name="description" content="Browsable catalog of Singapore street names from OpenStreetMap." />
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
    integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="" />
  <link rel="stylesheet" href="__BASE__style.css" />
</head>
<body>
  <header class="site-header">
    <div class="brand">
      <h1><a href="__BASE__">Singapore Streets</a></h1>
      <p class="subtitle"><span id="street-count">__COUNT__</span> named streets · OSM catalog</p>
    </div>
    <nav class="tabs" role="tablist">
      <button type="button" class="tab active" data-view="map" role="tab" aria-selected="true">Map</button>
      <button type="button" class="tab" data-view="list" role="tab" aria-selected="false">List</button>
    </nav>
  </header>

  <section class="filters" aria-label="Filters">
    <label class="field search-field">
      <span class="label">Search</span>
      <input id="search" type="search" placeholder="Street name…" autocomplete="off" />
    </label>
    <label class="field">
      <span class="label">Category</span>
      <select id="category">
        <option value="">All categories</option>
      </select>
    </label>
    <label class="field">
      <span class="label">Tag</span>
      <select id="tag">
        <option value="">All tags</option>
      </select>
    </label>
    <label class="field district-field hidden">
      <span class="label">District</span>
      <select id="district">
        <option value="">All districts</option>
      </select>
    </label>
    <p class="filter-status"><span id="match-count">0</span> shown</p>
  </section>

  <main>
    <section id="view-map" class="view view-map" aria-label="Map view">
      <div id="map"></div>
      <aside id="map-legend" class="legend" aria-label="Category legend"></aside>
    </section>

    <section id="view-list" class="view view-list hidden" aria-label="List view">
      <div id="list" class="street-list"></div>
    </section>
  </main>

  <aside id="detail" class="detail hidden" aria-live="polite">
    <button type="button" id="detail-close" class="detail-close" aria-label="Close detail">×</button>
    <div id="detail-body"></div>
    <div id="detail-map" class="detail-map"></div>
  </aside>
  <div id="detail-backdrop" class="detail-backdrop hidden"></div>

  <footer class="site-footer">
    <p>
      Built from
      <a href="https://github.com/evgeniyarbatov/singapore-streets">evgeniyarbatov/singapore-streets</a>.
      Map data © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>.
    </p>
  </footer>

  <script>
    window.SITE_BASE = __SITE_BASE_JS__;
  </script>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
    integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
  <script src="__BASE__app.js"></script>
</body>
</html>
"""
    html = (
        html.replace("__BASE__", base)
        .replace("__COUNT__", f"{count:,}")
        .replace("__SITE_BASE_JS__", site_base_js)
    )
    path.write_text(html, encoding="utf-8")


def build_site(
    dataset_path: Path,
    categories_path: Path,
    osm_path: Path,
    canonical_path: Path,
    static_path: Path,
    dist_path: Path,
    base_path: str,
) -> dict[str, Any]:
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}. Run `make dataset` first.")

    streets = load_streets(dataset_path, categories_path, osm_path, canonical_path)
    meta = build_meta(streets, base_path)

    if dist_path.exists():
        shutil.rmtree(dist_path)
    dist_path.mkdir(parents=True)

    write_json_gzip(dist_path / "data" / "streets.json.gz", streets)
    write_json(dist_path / "data" / "meta.json", meta)
    write_index_html(dist_path / "index.html", meta)

    for name in ("app.js", "style.css"):
        source = static_path / name
        if not source.exists():
            raise FileNotFoundError(f"Missing static asset: {source}")
        shutil.copy2(source, dist_path / name)

    nojekyll = dist_path / ".nojekyll"
    nojekyll.write_text("", encoding="utf-8")

    return meta


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--categories", type=Path, default=DEFAULT_CATEGORIES)
    parser.add_argument("--osm", type=Path, default=DEFAULT_OSM)
    parser.add_argument("--canonical", type=Path, default=DEFAULT_CANONICAL)
    parser.add_argument("--static", type=Path, default=DEFAULT_STATIC)
    parser.add_argument("--dist", type=Path, default=DEFAULT_DIST)
    parser.add_argument(
        "--base-path",
        default="/singapore-streets/",
        help="URL prefix for GitHub Pages (use / for local root serve)",
    )
    args = parser.parse_args()

    meta = build_site(
        dataset_path=args.dataset,
        categories_path=args.categories,
        osm_path=args.osm,
        canonical_path=args.canonical,
        static_path=args.static,
        dist_path=args.dist,
        base_path=args.base_path,
    )
    print(f"Built site with {meta['count']} streets → {args.dist}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
