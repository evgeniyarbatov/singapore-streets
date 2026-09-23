from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from name_precision import fold_orthographic_variants, reject_reason

DIRECTION_RE = re.compile(r"\b(East|West|North|South)(\s*\d+[A-Za-z]?)?$", re.IGNORECASE)

BUILDING_KEYWORDS = [
    "mall",
    "plaza",
    "centre",
    "center",
    "building",
    "tower",
    "complex",
    "hub",
    "junction",
    "interchange",
    "station",
    "terminal",
    "hotel",
    "condominium",
    "condo",
    "residences",
    "apartments",
    "flats",
    "food court",
    "foodcourt",
]

STREET_PATTERN = re.compile(
    r"\b("
    r"Avenue|"
    r"Boulevard|"
    r"Central|"
    r"Circle|"
    r"Close|"
    r"Crescent|"
    r"Drive|"
    r"Expressway|"
    r"Farmway|"
    r"Gardens|"
    r"Heights|"
    r"Hill|"
    r"Lane|"
    r"Link|"
    r"Loop|"
    r"Parkway|"
    r"Place|"
    r"Quay|"
    r"Ring|"
    r"Rise|"
    r"Road|"
    r"Square|"
    r"Street|"
    r"Terrace|"
    r"View|"
    r"Walk|"
    r"Way"
    r")(\s*\d+[A-Za-z]?)?$",
    re.IGNORECASE,
)
LORONG_RE = re.compile(r"\bLorong(\s*\d+[A-Za-z]?)?\s*", re.IGNORECASE)
JALAN_RE = re.compile(r"^Jalan\s*", re.IGNORECASE)
PREFIX_RE = re.compile(r"^(Bukit|Kampong|Mount)\s", re.IGNORECASE)


def _is_building(line: str) -> bool:
    return any(
        re.search(r"\b" + keyword + r"\b", line, re.IGNORECASE) for keyword in BUILDING_KEYWORDS
    )


def _matches_street_pattern(line: str) -> bool:
    return bool(
        STREET_PATTERN.search(line)
        or LORONG_RE.search(line)
        or JALAN_RE.search(line)
        or PREFIX_RE.search(line)
    )


def select_street_names(
    lines: list[str], allowlist: set[str]
) -> tuple[list[str], list[tuple[str, str]]]:
    """Keep street-shaped names, then fold hyphen/space spellings of one road."""
    kept: list[str] = []
    rejected: list[tuple[str, str]] = []
    pending_direction: list[str] = []

    for line in lines:
        if line in allowlist:
            kept.append(line)
            continue
        reason = reject_reason(line)
        if reason:
            rejected.append((line, reason))
            continue
        if _is_building(line):
            rejected.append((line, "building/mall"))
            continue
        if "/" in line:
            rejected.append((line, "contains slash"))
            continue
        if _matches_street_pattern(line):
            kept.append(line)
            continue
        if DIRECTION_RE.search(line):
            pending_direction.append(line)
            continue
        rejected.append((line, "not street pattern"))

    for line in pending_direction:
        # The suffix regex anchors at end-of-string, so "Foo Road East" is not a
        # street pattern. Keep it when the unsuffixed road is already kept.
        base = DIRECTION_RE.sub("", line).strip()
        if base and any(re.search(r"\b" + re.escape(base) + r"\b", seen) for seen in kept):
            kept.append(line)
        else:
            rejected.append((line, "not street pattern"))

    return fold_orthographic_variants(kept), rejected


def load_allowlist(path: str) -> set[str]:
    if not path or not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip() and not line.startswith("#")}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Keep only names that look like real Singapore streets."
    )
    parser.add_argument(
        "--reject-log",
        default="filtered/not-street-names.txt",
        help="Where to write rejected lines (default: filtered/not-street-names.txt)",
    )
    parser.add_argument(
        "--allowlist",
        default="data/allowlist.txt",
        help="Names that always pass, bypassing the building/slash filters "
        "(default: data/allowlist.txt)",
    )
    args = parser.parse_args()

    allowlist = load_allowlist(args.allowlist)
    lines = [line.rstrip() for line in sys.stdin]
    kept, rejected = select_street_names(lines, allowlist)

    reject_dir = os.path.dirname(args.reject_log)
    if reject_dir:
        os.makedirs(reject_dir, exist_ok=True)

    with open(args.reject_log, "w", encoding="utf-8") as handle:
        for line, reason in rejected:
            handle.write(f"{line} # Filtered: {reason}\n")

    for name in kept:
        print(name)


if __name__ == "__main__":
    main()
