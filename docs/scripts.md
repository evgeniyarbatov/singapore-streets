# Scripts reference

All pipeline scripts live in `scripts/`. Most are invoked via `Makefile` targets; each can also be run directly.

## Extraction

### `extract_streets.py`

Reads a clipped Singapore OSM XML file and produces street names with map polylines.

```bash
python scripts/extract_streets.py osm/singapore.osm data/osm-streets.csv data/street-names.txt data/review-queue.csv
```

**What it does:**

1. Walks OSM nodes, ways, and relations with **osmium**
2. Collects ways that are either:
   - `highway` + name tag, or
   - name tag matching a street suffix pattern (`Road`, `Jalan`, `Lorong`, `Quay`, `Bukit`, `Kampong`, `Mount`, etc.)
3. Also collects named relations (`type=route, route=road`, or any relation with a `highway` tag — e.g. expressways split across many unnamed member ways), stitching their member ways' geometry
4. Resolves a primary name with fallback through `name`, `name:en`, `name:ms`, `name:zh`, `alt_name`, `old_name` — a way with no `name` tag but an `alt_name`/`old_name` is still captured instead of silently dropped. The other tag values become aliases.
5. Groups segments by name and **merges polylines** when endpoints are within 25 m; aliases are unioned per group
6. Flags duplicate geometries and null polylines to stderr, and writes them to `data/review-queue.csv` when a path is given
7. Writes `data/osm-streets.csv` (with `name`, `polyline`, `osm_source`, `aliases` columns) and optionally `data/street-names.txt`

**Key functions:** `StreetHandler`, `resolve_name_and_aliases()`, `merge_street_polylines()`, `detect_polyline_issues()`, `write_review_queue()`, `is_street_pattern()`

**Makefile target:** `make streets`

---

## Cleaning chain

`make clean` pipes three scripts together. Each reads stdin and writes stdout; rejects are logged under `filtered/`.

### `format-address.py`

Normalizes spelling and abbreviations.

- Title-cases names
- Expands abbreviations: `Rd` → `Road`, `St` → `Street`, `Jln` → `Jalan`, `Bt` → `Bukit`, etc.
- Fixes common encoding artifacts (`&apos;`, curly quotes)

```bash
cat data/street-names.txt | python scripts/format-address.py
```

### `invalid-address.py`

Drops lines that are clearly not street names.

**Keeps** lines that:
- Start with a capital letter
- Are not block addresses (`Blk …`)
- Have no punctuation (`;,:#()`)
- Match no stop-word patterns (bus stops, MRT, temples, food centres, etc.)
- Are not a bare numbered lorong (`Lorong 5` alone) **unless** the same number also appears in a named variant elsewhere in the batch (e.g. `Lorong 5 Geylang`) — that's evidence it's a real, officially named lane rather than a stray fragment

**Rejects** everything else → reject log path (default `filtered/invalid-address.txt`, override with `--reject-log`)

```bash
cat data/street-names.txt | python scripts/format-address.py | python scripts/invalid-address.py --reject-log filtered/invalid-address.txt
```

### `street-names.py`

Final street-name filter. Keeps names that look like real streets; rejects buildings, malls, and slash-names.

**Keeps** names matching:
- Street suffix patterns (`Road`, `Avenue`, `Crescent`, `Quay`, `Place`, `View`, …)
- `Jalan …` or `Lorong …` prefixes, or `Bukit …` / `Kampong …` / `Mount …` prefixes
- Directional variants (`Foo Road East`) when the base name already exists
- Any name listed in the allowlist file (default `data/allowlist.txt`, override with `--allowlist`) — bypasses the building/mall and slash filters for confirmed official edge cases

**Rejects** → reject log path (default `filtered/not-street-names.txt`, override with `--reject-log`; includes a reason comment)

```bash
# Full clean pipeline (as Makefile runs it):
cat data/street-names.txt \
  | python scripts/format-address.py \
  | python scripts/invalid-address.py --reject-log filtered/invalid-address.txt \
  | python scripts/street-names.py --reject-log filtered/not-street-names.txt --allowlist data/allowlist.txt \
  | sort | uniq > data/street-names.txt
```

**Makefile target:** `make clean`

### `canonical_streets.py`

Groups directional variants of the same street (`Foo Road`, `Foo Road East`, `Foo Road West`) into one logical row.

```bash
python scripts/canonical_streets.py data/street-names.txt data/canonical-streets.csv
```

Output columns: `canonical_name` (direction stripped), `display_name` (preferred form — the bare canonical name when present, else the shortest variant), `aliases` (pipe-separated remaining variants).

**Key functions:** `canonicalize()`, `build_canonical_table()`, `write_canonical_table()`

**Makefile target:** `make canonical`

---

## Categorization

### `taxonomy.py`

Shared library — not run directly. Loads `data/taxonomy.yaml` and exposes:

| Function / class | Purpose |
|------------------|---------|
| `load_taxonomy()` | Parse YAML into a `Taxonomy` object |
| `Taxonomy.classify_by_rules(name)` | Regex + colonial surname lookup |
| `Taxonomy.classify_legacy_label(label)` | Map old free-form labels (kept for reference) |
| `format_tags()` / `parse_tags()` | Serialize pipe-separated secondary tags |

Primary categories include `colonial_british`, `malay_archipelago`, `nature_geography`, `numeric_functional`, and others defined in the YAML file.

### `categorize_streets.py`

Assigns a stable taxonomy category to every street in `data/street-names.txt`.

```bash
python scripts/categorize_streets.py \
  data/street-names.txt \
  data/street_categories.csv \
  --model mistral-nemo:latest
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--model` | (required unless `--no-llm`) | Ollama model name |
| `--prompt` | `prompts/categorize-v1.md` | Prompt template |
| `--no-llm` | off | Rules only; no Ollama calls |

**Priority order:**

1. Rule match from taxonomy
2. Ollama with constrained JSON output (`primary_category`, `tags`, `confidence`)

Output is appended to `data/street_categories.csv`. Already-processed streets are skipped.

**Makefile target:** `make categorize`

### `category_report.py`

Summarizes categorization quality.

```bash
python scripts/category_report.py
python scripts/category_report.py --input data/street_categories.csv --output data/category-stats.json
```

Reports total streets, coverage %, counts per category/source/tag, and review-queue size (uncategorized + `legacy_fallback` sources). Writes JSON to `data/category-stats.json` by default.

**Makefile target:** `make category-report`

---

## Dataset build

### `create-dataset.py`

Joins the three data files into the publishable dataset.

```bash
python scripts/create-dataset.py
```

1. Reads `data/street-names.txt`
2. Inner-joins `data/street_categories.csv` on `street_name`
3. Left-joins `data/osm-streets.csv` for polylines
4. Writes `dataset/singapore-streets.csv` with columns: `street_name`, `category`, `polyline`

Supports both the legacy `name,category` CSV format and the new header-based format.

**Makefile target:** `make dataset`

---

## Configuration files

These are not scripts but are central to categorization:

| File | Role |
|------|------|
| `data/taxonomy.yaml` | Primary categories, secondary tags, regex rules, colonial surnames |
| `prompts/categorize-v1.md` | LLM prompt template with `{{CATEGORIES}}`, `{{TAGS}}`, `{{STREET_NAME}}` placeholders |

### Changing the taxonomy

Edit `data/taxonomy.yaml`, then re-run `make categorize --no-llm` to apply rule changes to uncategorized streets, or delete specific rows from `street_categories.csv` to force re-classification.

---

## Quick reference

| Script | Input | Output |
|--------|-------|--------|
| `extract_streets.py` | `osm/singapore.osm` | `data/osm-streets.csv`, `data/street-names.txt`, `data/review-queue.csv` |
| `format-address.py` | stdin (names) | stdout (normalized names) |
| `invalid-address.py` | stdin | stdout; reject log (`--reject-log`) |
| `street-names.py` | stdin | stdout; reject log (`--reject-log`); allowlist (`--allowlist`) |
| `canonical_streets.py` | `street-names.txt` | `data/canonical-streets.csv` |
| `categorize_streets.py` | `street-names.txt` | `data/street_categories.csv` |
| `category_report.py` | `street_categories.csv` | stdout + `category-stats.json` |
| `create-dataset.py` | names + categories + OSM CSV | `dataset/singapore-streets.csv` |
| `taxonomy.py` | `data/taxonomy.yaml` | (imported by other scripts) |