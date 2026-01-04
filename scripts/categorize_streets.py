#!/usr/bin/env python3
import re
import sys
from collections import defaultdict

CATEGORIES = [
    "Numerical or Lettered Names (numbered streets/avenues, alphabet-themed)",
    "Infrastructure & Transport (bridge/port/airport/rail-related)",
    "Cultural & Religious (festivals, concepts, heritage, temples)",
    "Occupational (professions, trades, industries)",
    "Nature & Geography (trees, plants, animals, landforms)",
    "International/Foreign References (countries, cities, foreign leaders)",
    "Historical Themes (colonial figures, local leaders, royalty)",
    "Modern Development (HDB-era names, planning themes, new towns)",
    "Residential/Community Themes (virtues, values, neighbourhood concepts)",
    "Descriptive (colors, shapes, directions, adjectives)",
    "Linguistic Origin (Malay, English/British, Chinese, Tamil, etc.)",
]

RULES = {
    CATEGORIES[0]: {
        "tokens": set(),
        "phrases": ["phase", "sector", "block"],
    },
    CATEGORIES[1]: {
        "tokens": {
            "expressway",
            "bridge",
            "port",
            "pier",
            "harbour",
            "airport",
            "station",
            "rail",
            "mrt",
            "lrt",
            "interchange",
            "tunnel",
            "viaduct",
            "flyover",
            "terminal",
            "ferry",
            "bus",
            "junction",
        },
        "phrases": [],
    },
    CATEGORIES[2]: {
        "tokens": {
            "temple",
            "church",
            "mosque",
            "masjid",
            "kuil",
            "vihara",
            "shrine",
            "pagoda",
            "cathedral",
            "gurdwara",
            "monastery",
            "saint",
            "st",
            "vesak",
            "deepavali",
            "hari",
            "puasa",
        },
        "phrases": [],
    },
    CATEGORIES[3]: {
        "tokens": {
            "smith",
            "carpenter",
            "fisher",
            "farmer",
            "weaver",
            "mason",
            "baker",
            "butcher",
            "merchant",
            "trader",
            "tailor",
            "miner",
            "sailor",
            "doctor",
            "nurse",
            "engineer",
            "pilot",
        },
        "phrases": [],
    },
    CATEGORIES[4]: {
        "tokens": {
            "palm",
            "pine",
            "oak",
            "orchard",
            "garden",
            "gardens",
            "river",
            "brook",
            "bay",
            "beach",
            "island",
            "valley",
            "mount",
            "hill",
            "ridge",
            "forest",
            "meadow",
            "park",
            "lake",
            "grove",
            "green",
            "heights",
        },
        "phrases": [],
    },
    CATEGORIES[5]: {
        "tokens": {
            "china",
            "india",
            "japan",
            "korea",
            "england",
            "france",
            "germany",
            "italy",
            "russia",
            "australia",
            "canada",
            "malaysia",
            "indonesia",
            "thailand",
            "vietnam",
            "arab",
            "mexico",
            "spain",
            "portugal",
            "brazil",
            "egypt",
            "paris",
            "london",
            "tokyo",
            "rome",
            "milan",
        },
        "phrases": [],
    },
    CATEGORIES[6]: {
        "tokens": {
            "king",
            "queen",
            "prince",
            "princess",
            "duke",
            "earl",
            "lord",
            "lady",
            "sir",
            "sultan",
            "raja",
        },
        "phrases": [],
    },
    CATEGORIES[7]: {
        "tokens": {
            "industrial",
            "business",
            "tech",
            "science",
            "digital",
            "enterprise",
            "innovation",
        },
        "phrases": ["one-north", "biopolis", "fusionopolis"],
    },
    CATEGORIES[8]: {
        "tokens": {
            "estate",
            "village",
            "community",
            "residence",
            "residences",
            "neighbourhood",
            "neighborhood",
        },
        "phrases": [],
    },
    CATEGORIES[9]: {
        "tokens": {
            "north",
            "south",
            "east",
            "west",
            "upper",
            "lower",
            "new",
            "old",
            "central",
            "red",
            "blue",
            "green",
            "white",
            "black",
            "gold",
            "golden",
            "silver",
            "round",
            "square",
        },
        "phrases": [],
    },
}

MALAY_TOKENS = {
    "jalan",
    "lorong",
    "bukit",
    "taman",
    "kampong",
    "kampung",
    "pulau",
    "telok",
    "teluk",
    "sungai",
    "sungei",
    "pasir",
    "ubi",
    "haji",
    "permai",
    "sentosa",
    "serangoon",
}

ENGLISH_SUFFIXES = {
    "road",
    "street",
    "avenue",
    "lane",
    "drive",
    "close",
    "crescent",
    "way",
    "walk",
    "place",
    "terrace",
    "grove",
    "green",
    "hill",
    "rise",
    "view",
    "parkway",
    "boulevard",
    "circle",
    "loop",
    "link",
    "central",
    "square",
    "heights",
    "gardens",
}


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def match_rule(name_lower: str, tokens: list[str], category: str) -> str | None:
    rules = RULES.get(category)
    if not rules:
        return None
    for phrase in rules["phrases"]:
        if phrase in name_lower:
            return phrase
    for token in tokens:
        if token in rules["tokens"]:
            return token
    return None


def categorize_name(name: str) -> tuple[str, str]:
    name_lower = name.lower()
    tokens = tokenize(name)

    if any(char.isdigit() for char in name):
        return CATEGORIES[0], "Contains a number in the name."

    for category in CATEGORIES[1:-1]:
        matched = match_rule(name_lower, tokens, category)
        if matched:
            return category, f"Matched keyword '{matched}'."

    for token in tokens:
        if token in MALAY_TOKENS:
            return CATEGORIES[-1], f"Malay marker '{token}' appears in the name."

    for token in tokens:
        if token in ENGLISH_SUFFIXES:
            return CATEGORIES[-1], f"English street-type suffix '{token}' is used."

    return CATEGORIES[-1], "Categorized by general naming style."


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: categorize_streets.py <input.txt> <output.md>")
        return 1

    input_path, output_path = sys.argv[1], sys.argv[2]
    categories = defaultdict(list)

    with open(input_path, "r", encoding="utf-8") as handle:
        for line in handle:
            name = line.strip()
            if not name:
                continue
            category, explanation = categorize_name(name)
            categories[category].append((name, explanation))

    with open(output_path, "w", encoding="utf-8") as handle:
        for category in CATEGORIES:
            entries = categories.get(category)
            if not entries:
                continue
            handle.write(f"## {category}\n")
            for name, explanation in entries:
                handle.write(f"- {name} — {explanation}\n")
            handle.write("\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
