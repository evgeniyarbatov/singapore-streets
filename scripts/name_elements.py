from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

NUMBER_RE = re.compile(r"^\d+[A-Za-z]?$")
DIRECTIONS = {"East", "West", "North", "South", "Central", "Upper", "Lower"}


def words(name: str) -> list[str]:
    return [w for w in name.split() if not NUMBER_RE.match(w)]


def template(name: str) -> str:
    return " ".join("N" if NUMBER_RE.match(w) else w for w in name.split())


def core(name: str) -> list[str]:
    """Words with numbers and direction words removed, e.g. "Bedok North Avenue 3" -> Bedok Avenue."""
    return [w for w in words(name) if w not in DIRECTIONS]


def build_facts(rows: list[dict[str, str]], generic_min: int) -> dict[str, object]:
    names = sorted({r["street_name"] for r in rows})
    category = {r["street_name"]: r["category"] for r in rows}

    element_names: dict[str, list[str]] = defaultdict(list)
    for name in names:
        for w in set(words(name)):
            element_names[w].append(name)

    firsts = Counter(core(n)[0] for n in names if core(n))
    lasts = Counter(core(n)[-1] for n in names if core(n))
    generics = {w for w, c in lasts.items() if c >= generic_min}

    series: dict[str, list[str]] = defaultdict(list)
    for name in names:
        t = template(name)
        if "N" in t.split():
            series[t].append(name)

    # A family shares a stem before a generic suffix (Tampines Avenue/Road/Street), so
    # "Jalan Besar" is not grouped under "Jalan" because "Besar" is not a generic suffix.
    families: dict[str, list[str]] = defaultdict(list)
    for name in names:
        c = core(name)
        if len(c) >= 2 and c[-1] in generics:
            families[" ".join(c[:-1])].append(name)

    return {
        "streets": len(names),
        "categories": dict(Counter(category[n] for n in names).most_common()),
        "first_words": dict(firsts.most_common()),
        "last_words": dict(lasts.most_common()),
        "elements": {
            w: {
                "count": len(ns),
                "categories": dict(Counter(category[n] for n in ns).most_common()),
                "streets": ns,
            }
            for w, ns in sorted(element_names.items(), key=lambda kv: (-len(kv[1]), kv[0]))
        },
        "series": {
            t: ns
            for t, ns in sorted(series.items(), key=lambda kv: (-len(kv[1]), kv[0]))
            if len(ns) >= 2
        },
        "families": {
            s: ns
            for s, ns in sorted(families.items(), key=lambda kv: (-len(kv[1]), kv[0]))
            if len({tuple(core(n)) for n in ns}) >= 2
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Count name elements, series and families.")
    parser.add_argument("dataset", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--generic-min", type=int, default=10)
    args = parser.parse_args()

    with args.dataset.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    facts = build_facts(rows, args.generic_min)
    args.output.write_text(json.dumps(facts, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
