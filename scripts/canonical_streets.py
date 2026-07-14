from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

DIRECTION_RE = re.compile(r"\s+(East|West|North|South)(\s+\d+[A-Za-z]?)?$", re.IGNORECASE)


def canonicalize(name: str) -> str:
    """
    Strip a trailing directional suffix to get the canonical identity for a
    street, e.g. "Joo Chiat Road East" and "Joo Chiat Road" both canonicalize
    to "Joo Chiat Road".
    """
    return DIRECTION_RE.sub("", name).strip()


def build_canonical_table(names: list[str]) -> list[dict[str, str]]:
    """
    Group names sharing a canonical identity into one row each:
    canonical_name, display_name, aliases (pipe-separated, may be empty).

    display_name prefers the bare canonical form when it is itself one of
    the input names; otherwise the shortest variant is used.
    """
    groups: dict[str, list[str]] = {}
    for name in names:
        canonical = canonicalize(name)
        groups.setdefault(canonical, []).append(name)

    rows: list[dict[str, str]] = []
    for canonical, variants in groups.items():
        variants = sorted(set(variants))
        display_name = canonical if canonical in variants else min(variants, key=len)
        aliases = sorted(v for v in variants if v != display_name)
        rows.append(
            {
                "canonical_name": canonical,
                "display_name": display_name,
                "aliases": "|".join(aliases),
            }
        )

    rows.sort(key=lambda row: row["canonical_name"])
    return rows


def write_canonical_table(rows: list[dict[str, str]], output_path: str | Path) -> None:
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["canonical_name", "display_name", "aliases"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Group directional street name variants into a canonical name table."
    )
    parser.add_argument("street_names_file", help="Path to data/street-names.txt")
    parser.add_argument("output_csv", help="Path to write the canonical name table")
    args = parser.parse_args()

    with open(args.street_names_file, encoding="utf-8") as f:
        names = [line.rstrip() for line in f if line.rstrip()]

    rows = build_canonical_table(names)
    write_canonical_table(rows, args.output_csv)
    print(f"Saved {len(rows)} canonical rows to {args.output_csv}", file=sys.stderr)


if __name__ == "__main__":
    main()
