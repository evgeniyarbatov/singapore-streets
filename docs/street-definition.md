# What counts as a street

This project catalogs **named public thoroughfares in Singapore** that a person would treat as a street name on a map or signboard — not every OSM way or every place label.

The pipeline is OSM-only today. “Official” here means *tagged as a highway or road-route name in OpenStreetMap*, not yet cross-checked against SLA / OneMap / URA.

## Included

A name is in scope when it is:

1. **Named** — carries an OSM `name` (or fallback `name:en` / `name:ms` / `name:zh` / `alt_name` / `old_name`)
2. **On a road-like geometry** — one of:
   - a way with a `highway` tag
   - a named relation that is `type=route` + `route=road`, or carries a `highway` tag
   - a non-highway way whose name still matches a Singapore street-type pattern (suffix safety net)
3. **Street-shaped after cleaning** — survives the clean chain (`format-address` → `invalid-address` → `street-names`)

Examples of included forms:

| Kind | Examples |
|------|----------|
| Standard English suffixes | Orchard Road, East Coast Parkway, Boat Quay |
| Malay types | Jalan Besar, Lorong 12 Geylang, Kampong Bahru |
| Prefix place-words | Bukit Timah Road area names starting with Bukit / Kampong / Mount |
| Links, walks, terraces | named Links, Walks, Terraces, Closes when they pass the pattern filter |
| Expressways / major routes | named expressways when present as highway ways or road-route relations |
| Numbered estate streets | Ang Mo Kio Avenue 1, Tampines Street 11 |
| Directional variants | Foo Road East kept when the base name is already in the list (also linked in `canonical-streets.csv`) |
| Bare numbered lorongs | `Lorong 12` kept only when a fuller name with the same number exists (e.g. Lorong 12 Geylang) |

Allowlisted edge cases in `data/allowlist.txt` always pass the building/slash filters.

## Excluded

Dropped during extract or clean (reject logs under `filtered/`):

| Kind | How it is rejected |
|------|--------------------|
| Buildings, malls, hotels, condos | Keyword filter in `street-names.py` (mall, plaza, tower, condo, station, terminal, …) |
| Address / POI fragments | Blocks (`Blk …`), punctuation-heavy labels, `@` handles (`invalid-address.py`) |
| Transit and amenity labels | Stop words such as After/Before/Opposite, MRT Station, Bus Terminal, Food Centre, Wet Market, … |
| Slash compound labels | Names containing `/` (unless allowlisted) |
| Names with no street pattern | No recognized suffix/prefix and not Jalan/Lorong |
| Unnamed connectors | No name tag → never extracted |
| Geometry-only junk | Missing or unusable polylines go to `data/review-queue.csv` for triage; they are not silently invented |

Condo internal drives and private estate paths appear only if OSM names them and the name still looks like a street after filters. There is no separate “public vs private” flag yet.

## Gray zone

Not every borderline case is cleanly include-or-exclude. Current treatment:

| Situation | Current behavior | Intended policy |
|-----------|------------------|-----------------|
| Private estate / condo drive with a street-like name | Kept if it passes patterns and keyword filters | Prefer keep with low confidence once a confidence field exists |
| Named pedestrian links / walks | Kept when suffix matches (Link, Walk, …) | Keep — named public paths are in catalog |
| Bare `Lorong N` with no fuller sibling | Dropped | Keep only with external evidence (allowlist or official source) |
| Slash names, odd official forms | Dropped unless allowlisted | Allowlist after confirming against an official source |
| Duplicate / missing polylines | Listed in `data/review-queue.csv` | Fix or ticket; do not invent geometry |
| Expressways and bridges | Included when named as highway/route | Product decision still open (see ROADMAP open questions) |

**Confidence scoring is not implemented yet.** Until it is, gray-zone decisions are binary (keep vs reject log / review queue). The long-term rule is: **prefer explicit low confidence over silent drop** for names that might be real streets.

## How the pipeline applies this

```
OSM ways/relations (named highways + road routes + pattern matches)
        │
        ▼
extract_streets.py     → data/osm-streets.csv, data/street-names.txt, data/review-queue.csv
        │
        ▼
format-address.py      → normalize Rd/St/Jln/… abbreviations
        │
        ▼
invalid-address.py     → drop blocks, POI labels, orphan bare Lorongs  → filtered/invalid-address.txt
        │
        ▼
street-names.py        → keep street patterns; drop buildings/slashes  → filtered/not-street-names.txt
        │                  (allowlist bypass)
        ▼
data/street-names.txt  → catalog name list (~count in category-stats / dataset)
```

Canonical grouping (`canonical_streets.py`) does not change inclusion; it only links directional variants after the name list is fixed.

## Changing the definition

- **Pattern or keyword change** → edit the extract/clean scripts and add a unit test; re-run `make all` (or `make fresh`).
- **One-off keep** → add the exact display name to `data/allowlist.txt`.
- **Policy change** (e.g. drop expressways, add confidence) → update this doc and ROADMAP open questions together so the catalog and the written definition stay aligned.
