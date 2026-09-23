from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from name_precision import normalize_display_name


def format(text: str) -> str:
    return normalize_display_name(text)


def main() -> None:
    for line in sys.stdin:
        line = line.rstrip()
        print(format(line))


if __name__ == "__main__":
    main()
