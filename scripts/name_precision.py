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


# str.title() would turn these into King'S, Mcnair, Amk, One-North, Prince Of.
# OSM already stores the form on the right; keep it, and repair a title()-damaged copy.
CANONICAL_TOKENS = {
    "one-north": "one-north",
    "macpherson": "MacPherson",
    "mactaggart": "MacTaggart",
    "mcnair": "McNair",
    "mccallum": "McCallum",
    "mcnally": "McNally",
    "amk": "AMK",
    "bbq": "BBQ",
    "gpl": "GPL",
    "hpl": "HPL",
    "hsbc": "HSBC",
    "ite": "ITE",
    "ns": "NS",
    "nus": "NUS",
    "ocbc": "OCBC",
    "oue": "OUE",
    "sfa": "SFA",
    "spc": "SPC",
    "ue": "UE",
}
SMALL_WORDS = frozenset({"of", "the", "and"})
ABBREVIATIONS = (
    ("Rd", "Road"),
    ("St", "Street"),
    ("Dr", "Drive"),
    ("Jln", "Jalan"),
    ("Lor", "Lorong"),
    ("Ave", "Avenue"),
    ("Blvd", "Boulevard"),
    ("Bt", "Bukit"),
    ("Aft", "After"),
    ("Bef", "Before"),
)


def _cap_first_letter(token: str) -> str:
    for index, char in enumerate(token):
        if char.isalpha():
            return token[:index] + char.upper() + token[index + 1 :]
    return token


def _repair_title_damage(token: str) -> str:
    # title() capitalizes the possessive ("King'S") and the letter after Mc ("Mcnair").
    token = re.sub(r"'S\b", "'s", token)
    return re.sub(r"^Mc([a-z])", lambda match: "Mc" + match.group(1).upper(), token)


def _recase_token(token: str, *, first: bool) -> str:
    canonical = CANONICAL_TOKENS.get(token.casefold())
    if canonical is not None:
        return canonical
    if token.casefold() in SMALL_WORDS and not first:
        return token.casefold()
    if any(char.isupper() for char in token):
        return _repair_title_damage(token)
    if "-" in token:
        parts = token.split("-")
        return "-".join(
            _recase_token(part, first=first and index == 0) for index, part in enumerate(parts)
        )
    return _cap_first_letter(token)


def normalize_display_name(text: str) -> str:
    """Collapse spacing and dashes, expand abbreviations, keep OSM casing.

    Does not use str.title(): that capitalizes after apostrophes and hyphens
    and lowercases the rest, so King's, McNair, and AMK no longer match the
    row that holds the polyline.
    """
    text = text.replace("\u2013", "-").replace("\u2014", "-").replace("\u2212", "-")
    text = re.sub(r"&apos;", "'", text, flags=re.IGNORECASE)
    text = re.sub(r"[’‘ʼ]", "'", text)
    text = re.sub(r"[ \t]+", " ", text).strip()
    for source, replacement in ABBREVIATIONS:
        text = re.sub(rf"\b{source}\b", replacement, text, flags=re.IGNORECASE)
    text = re.sub(r"\bCostal\b", "Coastal", text, flags=re.IGNORECASE)
    tokens = text.split(" ")
    recased = [_recase_token(token, first=index == 0) for index, token in enumerate(tokens)]
    return " ".join(recased)


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
