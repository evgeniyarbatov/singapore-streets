"""Street-name spelling and the line between a road and a label for something else."""

from __future__ import annotations

import re

# A name that is only one of these has no proper name ("Road", "Hill").
GENERIC_THOROUGHFARES = frozenset(
    {
        "avenue",
        "boulevard",
        "central",
        "circle",
        "close",
        "crescent",
        "drive",
        "expressway",
        "farmway",
        "gardens",
        "heights",
        "hill",
        "lane",
        "link",
        "loop",
        "parkway",
        "place",
        "quay",
        "ring",
        "rise",
        "road",
        "square",
        "street",
        "terrace",
        "view",
        "walk",
        "way",
    }
)

# The head noun is a facility or a piece of infrastructure, not a thoroughfare.
# "Jalan Stadium" is exempt: that one token is the road. "Jalan Besar Stadium" is the building.
FACILITY_LAST = re.compile(
    r"(?i)(?:^|\s)("
    r"school|hospital|church|chapel|polyclinic|clinic|home|hotel|inn|suites|"
    r"exchange|substation|gates|hall|apartment|apartments|residence|residences|"
    r"station|terminal|mall|plaza|tower|depot|cemetery|canal|connector|club|"
    r"node|camp|stadium|reservoir|court|corridor"
    r")$"
)
ONE_TOKEN_JALAN_LORONG = re.compile(r"(?i)^(Jalan|Lorong)\s+\S+$")

# Parks named after a place. "Lorong 1 Realty Park" is a street and does not match.
PLACE_PARK = re.compile(r"(?i)^(Bukit|Mount|Kampong|Jalan)\b.*\sPark$")

# Prose OSM uses to describe a route or a venue sitting on a road
# ("Plot 2 Near …", "Lush On Holland Hill", "Link Fc1 To …").
NON_STREET = re.compile(
    r"(?i)\b(?:"
    r"proposed|interim|showflat|pipeline|diversion|diameter|"
    r"drop-off|cycling lane|parking lot|"
    r"community club|community garden|park connector|"
    r"nursing home|care home|sports hall|telephone exchange|service reservoir|"
    r"driving range|lrt|mrt|exit|substation|underpass|"
    r"inn|coffee|residence|apartment|"
    r"entrance|private|plot|near|from|along|to|at|on|by"
    r")\b"
    r"| - "
)


def normalize_display_name(text: str) -> str:
    """Collapse spacing and dashes, expand abbreviations, fix the Costal typo."""
    text = text.replace("\u2013", "-").replace("\u2014", "-").replace("\u2212", "-")
    text = re.sub(r"[ \t]+", " ", text).strip()
    text = text.title()
    text = re.sub(r"&apos;", "'", text)
    text = re.sub(r"’", "'", text)
    text = re.sub(r"Rd\b", "Road", text)
    text = re.sub(r"St\b", "Street", text)
    text = re.sub(r"Dr\b", "Drive", text)
    text = re.sub(r"Jln\b", "Jalan", text)
    text = re.sub(r"Lor\b", "Lorong", text)
    text = re.sub(r"Ave\b", "Avenue", text)
    text = re.sub(r"Blvd\b", "Boulevard", text)
    text = re.sub(r"Bt\b", "Bukit", text)
    text = re.sub(r"Aft\b", "After", text)
    text = re.sub(r"Bef\b", "Before", text)
    return re.sub(r"\bCostal\b", "Coastal", text)


def orthographic_key(name: str) -> str:
    """Identity with hyphens and spacing ignored, so Pan-Island and Pan Island match."""
    folded = name.replace("-", " ")
    folded = re.sub(r"\s+", " ", folded).strip()
    return folded.casefold()


def prefer_display_name(variants: list[str]) -> str:
    """Prefer a hyphenated compound when one spelling uses a hyphen."""
    unique = sorted(set(variants))
    hyphenated = [name for name in unique if "-" in name]
    pool = hyphenated or unique
    return min(pool, key=lambda name: (len(name), name.casefold()))


def fold_orthographic_variants(names: list[str]) -> list[str]:
    groups: dict[str, list[str]] = {}
    for name in names:
        groups.setdefault(orthographic_key(name), []).append(name)
    return [prefer_display_name(variants) for variants in groups.values()]


def _venue_named_for_its_street(name: str) -> bool:
    # "Pullman Singapore Hill Street" names the hotel by the road it occupies.
    # "Malaysia–Singapore Second Link" is three tokens and is the crossing itself.
    if len(name.split()) < 4 or name.casefold().startswith("singapore "):
        return False
    return re.search(r"\bSingapore\b", name) is not None


def reject_reason(name: str) -> str | None:
    """Why this string is not a street name, or None if it might be one."""
    if name.casefold() in GENERIC_THOROUGHFARES:
        return "bare generic"
    if "." in name:
        return "dotted label"
    match = NON_STREET.search(name)
    if match:
        return f"not a street ({match.group(0).strip()})"
    if _venue_named_for_its_street(name):
        return "venue on a street"
    if PLACE_PARK.search(name):
        return "park"
    if FACILITY_LAST.search(name) and not ONE_TOKEN_JALAN_LORONG.match(name):
        return "facility"
    return None
