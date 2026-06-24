#!/usr/bin/env python3
"""One-time migration from free-form LLM labels to the stable taxonomy."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from taxonomy import format_tags, get_taxonomy, parse_tags

OUTPUT_FIELDS = [
    "street_name",
    "primary_category",
    "category",
    "tags",
    "source",
    "prompt_version",
    "model",
    "legacy_category",
]


def _load_legacy_categories(path: Path) -> dict[str, str]:
    legacy: dict[str, str] = {}
    with open(path, "r", encoding="utf-8", newline="") as handle:
        first_line = handle.readline()
        if not first_line:
            return legacy

        if first_line.startswith("street_name,"):
            handle.seek(0)
            for row in csv.DictReader(handle):
                name = (row.get("street_name") or "").strip()
                category = (row.get("legacy_category") or row.get("category") or "").strip()
                if name and category:
                    legacy[name] = category
            return legacy

        for line in [first_line, *handle]:
            line = line.strip()
            if not line or "," not in line:
                continue
            name, category = line.split(",", 1)
            name = name.strip()
            category = category.strip()
            if name:
                legacy[name] = category
    return legacy


def _load_reviewed(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8", newline="") as handle:
        return {
            (row.get("street_name") or "").strip(): row
            for row in csv.DictReader(handle)
            if (row.get("street_name") or "").strip()
        }


def migrate(
    names_path: Path,
    legacy_path: Path,
    output_path: Path,
    reviewed_path: Path,
) -> dict[str, int]:
    taxonomy = get_taxonomy()
    names = [
        line.strip()
        for line in names_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    legacy_categories = _load_legacy_categories(legacy_path)
    reviewed = _load_reviewed(reviewed_path)

    stats: dict[str, int] = {
        "total": len(names),
        "reviewed": 0,
        "rule": 0,
        "legacy": 0,
        "uncategorized": 0,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()

        for name in names:
            legacy_label = legacy_categories.get(name, "")

            if name in reviewed:
                row = reviewed[name]
                primary = taxonomy.validate_category_id(
                    (row.get("primary_category") or "").strip()
                )
                tags = parse_tags(row.get("tags") or "")
                source = "reviewed"
                stats["reviewed"] += 1
            else:
                rule_match = taxonomy.classify_by_rules(name)
                if rule_match:
                    primary = rule_match.category_id
                    tags = rule_match.tags
                    source = "rule"
                    stats["rule"] += 1
                elif legacy_label:
                    mapped = taxonomy.classify_legacy_label(legacy_label)
                    if mapped:
                        primary = mapped.category_id
                        tags = mapped.tags
                        source = "legacy"
                        stats["legacy"] += 1
                    else:
                        primary = "abstract_modern"
                        tags = ()
                        source = "legacy_fallback"
                        stats["legacy"] += 1
                else:
                    primary = "uncategorized"
                    tags = ()
                    source = "uncategorized"
                    stats["uncategorized"] += 1

            writer.writerow(
                {
                    "street_name": name,
                    "primary_category": primary,
                    "category": taxonomy.category_name(primary),
                    "tags": format_tags(tags),
                    "source": source,
                    "prompt_version": "",
                    "model": "",
                    "legacy_category": legacy_label,
                }
            )

    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--names",
        default="data/street-names.txt",
        help="Street names list (one per line)",
    )
    parser.add_argument(
        "--legacy",
        default="data/street_categories.csv",
        help="Legacy name,category CSV",
    )
    parser.add_argument(
        "--output",
        default="data/street_categories.csv",
        help="Output path for migrated categories",
    )
    parser.add_argument(
        "--reviewed",
        default="data/categories-reviewed.csv",
        help="Human-reviewed overrides",
    )
    args = parser.parse_args()

    stats = migrate(
        Path(args.names),
        Path(args.legacy),
        Path(args.output),
        Path(args.reviewed),
    )

    categorized = stats["total"] - stats["uncategorized"]
    coverage = 100.0 * categorized / stats["total"] if stats["total"] else 0.0

    print(f"Migrated {stats['total']} streets to stable taxonomy.", file=sys.stderr)
    print(
        f"  reviewed={stats['reviewed']} rule={stats['rule']} "
        f"legacy={stats['legacy']} uncategorized={stats['uncategorized']}",
        file=sys.stderr,
    )
    print(f"  coverage={coverage:.1f}%", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())