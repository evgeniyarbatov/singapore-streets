#!/usr/bin/env python3
"""Report taxonomy coverage and category distribution."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from category_overrides import apply_overrides_to_rows
from taxonomy import get_taxonomy, parse_tags


def load_categories(path: Path) -> list[dict[str, str]]:
    with open(path, "r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def build_report(categories_path: Path) -> dict:
    taxonomy = get_taxonomy()
    rows = apply_overrides_to_rows(load_categories(categories_path))

    by_category: Counter[str] = Counter()
    by_source: Counter[str] = Counter()
    by_tag: Counter[str] = Counter()
    legacy_singletons: Counter[str] = Counter()
    uncategorized: list[str] = []
    review_queue: list[str] = []

    for row in rows:
        name = (row.get("street_name") or "").strip()
        primary = (row.get("primary_category") or row.get("category") or "").strip()
        if primary not in taxonomy.categories:
            for category_id, category in taxonomy.categories.items():
                if primary == category.name:
                    primary = category_id
                    break

        by_category[primary] += 1
        by_source[(row.get("source") or "unknown").strip() or "unknown"] += 1

        for tag in parse_tags(row.get("tags") or ""):
            by_tag[tag] += 1

        legacy = (row.get("legacy_category") or "").strip()
        if legacy:
            legacy_singletons[legacy] += 1

        source = (row.get("source") or "unknown").strip() or "unknown"
        if primary == "uncategorized" or source == "legacy_fallback":
            review_queue.append(name)

        if primary == "uncategorized":
            uncategorized.append(name)

    total = len(rows)
    categorized = total - len(uncategorized)
    coverage = 100.0 * categorized / total if total else 0.0

    return {
        "total_streets": total,
        "categorized": categorized,
        "uncategorized_count": len(uncategorized),
        "coverage_percent": round(coverage, 2),
        "primary_categories": len(by_category),
        "by_category": {
            taxonomy.category_name(category_id): count
            for category_id, count in by_category.most_common()
        },
        "by_source": dict(by_source.most_common()),
        "by_tag": dict(by_tag.most_common()),
        "legacy_label_count": len(legacy_singletons),
        "top_legacy_labels": dict(legacy_singletons.most_common(20)),
        "uncategorized_streets": uncategorized[:50],
        "review_queue_size": len(review_queue),
        "review_queue_streets": review_queue[:50],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default="data/street_categories.csv",
        help="Categorized streets CSV",
    )
    parser.add_argument(
        "--output",
        default="data/category-stats.json",
        help="Optional JSON output path",
    )
    args = parser.parse_args()

    report = build_report(Path(args.input))
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())