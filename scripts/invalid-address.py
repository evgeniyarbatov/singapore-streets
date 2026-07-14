from __future__ import annotations

import argparse
import os
import re
import sys

LORONG_NUMBER_RE = re.compile(r"^Lorong\s+(\d+[A-Za-z]?)\b", re.IGNORECASE)
BARE_LORONG_RE = re.compile(r"^Lorong\s+\d+[A-Za-z]?$", re.IGNORECASE)


def find_named_lorong_numbers(lines: list[str]) -> set[str]:
    """
    Numbers that appear in a Lorong name alongside other words, e.g.
    "Lorong 12 Geylang". A bare "Lorong 12" is kept when its number shows
    up here, since that's evidence it's a real, named lane rather than a
    stray numeric fragment.
    """
    numbers: set[str] = set()
    for line in lines:
        if BARE_LORONG_RE.match(line):
            continue
        match = LORONG_NUMBER_RE.match(line)
        if match:
            numbers.add(match.group(1).lower())
    return numbers


def is_invalid(line: str, named_lorong_numbers: set[str]) -> bool:
    starts_with_letter = bool(re.match(r"^[A-Z]", line))
    is_block = bool(re.match(r"^Blk", line, re.IGNORECASE))
    contains_punctuation = bool(re.search(r"[;,:#()]", line))
    has_stop_words = bool(
        re.search(
            r"(^After|^Before|Opposite|^Entrance|Bus Station|MRT Station|Temple$|Playground|Fitness Centre|Wet Market$|Food Centre$|Bus Terminal$)",
            line,
        )
    )
    has_special_characters = bool(re.search(r"@", line))

    bare_lorong_match = BARE_LORONG_RE.match(line)
    has_invalid_lorongs = bare_lorong_match is not None and (
        bare_lorong_match.group(0).split()[1].lower() not in named_lorong_numbers
    )

    return (
        not starts_with_letter
        or is_block
        or contains_punctuation
        or has_stop_words
        or has_special_characters
        or has_invalid_lorongs
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Drop lines that are clearly not street names.")
    parser.add_argument(
        "--reject-log",
        default="filtered/invalid-address.txt",
        help="Where to write rejected lines (default: filtered/invalid-address.txt)",
    )
    args = parser.parse_args()

    lines = [line.rstrip() for line in sys.stdin]
    named_lorong_numbers = find_named_lorong_numbers(lines)

    reject_dir = os.path.dirname(args.reject_log)
    if reject_dir:
        os.makedirs(reject_dir, exist_ok=True)

    with open(args.reject_log, "w") as f:
        for line in lines:
            if is_invalid(line, named_lorong_numbers):
                f.write(line + "\n")
            else:
                print(line)


if __name__ == "__main__":
    main()
