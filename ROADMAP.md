# Singapore Streets — Roadmap

A plan to grow this repo from an OSM extraction pipeline into a **comprehensive, browsable catalog** of Singapore street names — with meaningful categories, stories, and a way to wander back through the island one name at a time.

---

## Vision

Singapore streets are rare and oddly specific. A single name can carry colonial history, a Malay place-word, a clan association, a rubber estate, a kampung that no longer exists, or a developer's poetic flourish from the 2010s. The goal is not just a count (~4,926 today) but a **living catalog** where every name can be found, understood, and revisited.

Success looks like:

- **Complete** — every officially named street in Singapore is represented, with confidence scores for edge cases
- **Categorized** — names sit in a clear, stable taxonomy (not thousands of one-off LLM labels)
- **Enriched** — etymology, language, era, district, and a short human note where possible
- **Explorable** — map, search, filters, and “memory lane” features that make recall feel personal
- **Maintainable** — reproducible pipeline, tests, and incremental updates when OSM or official sources change

---

## Where We Are Today

The pipeline is solid through categorization and dataset publish:

```
OSM (Geofabrik) → clip to Singapore → extract names + polylines → clean/filter
  → canonical names → rules + Ollama + overrides → category report → Kaggle dataset
```

| Stage | What works | What limits us |
|-------|------------|----------------|
| **Extract** (`extract_streets.py`) | Highway + relation names; `name` / `name:en` / `name:ms` / `name:zh` / `alt_name` / `old_name`; polyline merge; review queue | OSM-only; no official-source completeness check |
| **Clean** (`format-address`, `invalid-address`, `street-names`) | Explicit reject logs; allowlist; smarter `Lorong` handling | Still regex-driven; gray-zone confidence not modeled |
| **Canonical** (`canonical_streets.py`) | Directional variants linked (`canonical_name`, `display_name`, `aliases`) | Not yet joined into the published dataset |
| **Categorize** (`categorize_streets.py`) | Fixed taxonomy; rules → LLM → overrides; resumable; prompt/model logged | Inter-rater audit not done; a few uncategorized names remain |
| **Report** (`category_report.py`) | Coverage, by-category / by-source / by-tag stats → `category-stats.json` | No confidence distribution chart beyond raw counters |
| **Dataset** (`create-dataset.py`) | `street_name`, `category`, `polyline` | Inner join drops uncategorized; no district / etymology / aliases columns |
| **Tooling** | `make all` / `fresh` / `fresh-all`; uv; pre-commit + ruff + mypy; unit tests | No CI; not an installable package; no golden-file OSM regression |

**Phase 2 outcome (current numbers):** ~4,926 streets; **99.8%** in the fixed taxonomy (10 uncategorized); sources roughly half rules / half LLM plus a handful of manual overrides.

The [Kaggle dataset](https://www.kaggle.com/datasets/evgenyarbatov/singapore-street-names) remains the public publish target. Next high-value gaps: official-source completeness (Phase 1.1), enrichment (Phase 3), and a browsable map (Phase 4).

---

## Guiding Principles

1. **Incremental discovery** — small PR-sized improvements; each run should teach something new (duplicate geometries, a missed `Jalan`, a street that is really a building).
2. **Ground truth over vibes** — cross-check OSM against official Singapore sources; use LLMs for suggestions, not as the sole authority.
3. **Stable categories, rich tags** — one primary category per street; optional secondary tags for nuance (e.g. `British colonial` + `named after person`).
4. **Keep the fun** — etymology notes, “streets I’ve run past”, photo pins, and oddities are first-class data, not polish for later.
5. **Reproducible nostalgia** — when you re-run the pipeline after a trip home, you should see what changed and what you still remember.

---

## Phase 1 — Completeness: Every Real Street Name

**Goal:** Maximize recall and precision of the street name list; know exactly what we have and what we lack.

### 1.1 Establish a completeness baseline

- [ ] Download and snapshot **reference lists** for diffing:
  - [OneMap](https://www.onemap.gov.sg/) / SLA geospatial layers
  - [data.gov.sg](https://data.gov.sg/) road-related datasets (e.g. street directory / road network where available)
  - URA [*Singapore Street, Building and Place Names*](https://www.ura.gov.sg/Corporate/Resources/Publications/Books/Book-Details/Singapore-Street-Building-Place-Names) (PDF, 2020) — manual spot-check sample, not full OCR initially
- [ ] Add `scripts/compare_sources.py` — output three sets: **in both**, **OSM only**, **official only**
- [ ] Track metrics in `data/stats.json`: total count, delta vs last run, source breakdown

### 1.2 Improve OSM extraction

- [x] Merge multilingual and alias tags: `name`, `name:en`, `name:ms`, `name:zh`, `alt_name`, `old_name`
- [x] Include **named relations** (some expressways and major roads are relation-tagged)
- [x] Expand street-type regex using [Remember Singapore suffix guide](https://remembersingapore.org/2018/08/15/singapore-street-suffixes/) and Wikipedia [road naming conventions](https://en.wikipedia.org/wiki/Road_names_in_Singapore) — e.g. `Quay`, `Place`, `View`, `Mount`, `Bukit`, `Kampong`, `Lorong` variants
- [x] Handle **directional variants** systematically (`Foo Road East` vs `Foo Road`) — keep both when official; link as aliases in metadata (see `data/canonical-streets.csv`, Phase 1.3)
- [x] Log and review `detect_polyline_issues` output: duplicate polylines, null polylines → `data/review-queue.csv`

### 1.3 Tighten the cleaning pipeline

- [x] Replace silent `filtered/*.txt` side effects with explicit `--reject-log` CLI flags
- [x] Revisit `Lorong \d+` exclusion — many valid Singapore streets are exactly that; use context (paired with named roads) instead of blanket drop
- [x] Add **allowlist** for known edge cases (e.g. legitimate slash names if they exist officially)
- [x] Canonical name table: `canonical_name`, `display_name`, `aliases[]` — one row per logical street

### 1.4 Definition of “street”

- [x] Document in [`docs/street-definition.md`](docs/street-definition.md):
  - Included: named public thoroughfares (highways, road-route relations, street-pattern names) after cleaning
  - Excluded: buildings/malls, MRT/bus labels, blocks, slash compounds, unnamed connectors
  - Gray zone: private estates, orphan lorongs, expressway scope — keep vs reject log today; low-confidence tag planned, not implemented

**Phase 1 done when:** Reference diff shows &lt;1% unexplained gaps vs best official source, and every gap is ticketed in `data/review-queue.csv`.

---

## Phase 2 — Categorization: A Real Taxonomy ✅

**Goal:** Replace open-ended LLM labels with a **stable, browsable category system** that still captures Singapore’s weirdness.

**Status:** Complete for practical purposes — fixed taxonomy, rules → LLM → human overrides, 99.8% coverage, review queue of 10 names.

### 2.1 Design the taxonomy

Primary categories live in `data/taxonomy.yaml` (12 categories; Japanese/wartime dropped as not useful in practice):

| Category | Examples | Notes |
|----------|----------|-------|
| **Colonial & British** | Stamford Road, Raffles Avenue | Officials, institutions, British places |
| **Malay & Archipelago** | Jalan Besar, Lorong Halus, Kampong Bahru | Indigenous place-words, geography |
| **Chinese dialect & clan** | Teochew, Hokkien, Cantonese transliterations | Often market, temple, clan links |
| **Tamil & South Asian** | Serangoon, Race Course Road area names | Includes Hindu / Muslim heritage |
| **Nature & geography** | Mount Pleasant, Sungei, Bukit, Bay | Hills, rivers, flora, fauna |
| **Trade & industry** | Market Street, Timberland... | Occupations, goods, economic activity |
| **Institutions & public** | Hospital Drive, School zones | Schools, hospitals, civic buildings |
| **Housing & development** | Named after estates, HDB phases | 1960s–present new towns |
| **Commemorative & persons** | Named after people (local or foreign) | Sub-tag: politician, philanthropist, etc. |
| **Abstract & modern** | Compassvale, Spring, Vision | Developer/commercial naming era |
| **Numeric & functional** | `Lorong 1`, `Street 11` | Still catalog; tag separately |
| **Uncategorized / unknown** | Honest bucket | Shrinks over time |

- [x] Store taxonomy in `data/taxonomy.yaml` with descriptions and example streets
- [x] Add optional **secondary tags** (multi-value): `person`, `tree`, `sea`, `estate`, `extinct_place`, `running_route`, plus `military`, `market`, `temple`, `clan`

### 2.2 Categorization workflow

- [x] **Rules first** — regex/lookup in taxonomy (`^Jalan`, `^Lorong`, `Bukit`, `Sungei`, colonial surnames list, …)
- [x] **LLM second** — constrained classification via Ollama; JSON schema (`primary_category`, `tags`, `confidence`) in `prompts/categorize-v1.md`
- [x] **Human review third** — `data/categories-override.csv` (git-tracked) wins over rules and model; never overwritten on re-run
- [x] Version prompts in `prompts/categorize-v1.md`; log model + prompt version per row in `street_categories.csv`

### 2.3 Quality controls

- [x] Normalize legacy categories: free-form LLM labels mapped via `legacy_label_mappings` in taxonomy (one-time migrate script removed after use)
- [ ] Inter-rater check: sample 100 streets, compare two models or model vs manual notes
- [x] Report: streets per category / source / tag, uncategorized review queue → `make category-report` / `data/category-stats.json`

**Phase 2 done when:** ≥95% of streets have a primary category from the fixed taxonomy; review queue for the rest is &lt;200 names. **Met** (99.8% / 10 names). Optional polish: inter-rater sample and clearing the last uncategorized streets via overrides.

---

## Phase 3 — Enrichment: Stories Behind the Names

**Goal:** Turn rows into **memories** — the reason you open this project after being away from Singapore.

### 3.1 Core metadata columns

Extend dataset schema:

```
street_name, canonical_name, category, tags[], polyline,
district, planning_area, postal_sector,
language_origin, name_type (descriptive|commemorative|toponym|...),
etymology_short, etymology_source, confidence,
first_known_year, old_names[], osm_id, last_osm_sync
```

- [ ] Join **district / planning area** from OneMap or URA boundaries (point-in-polygon from polyline centroid)
- [ ] Add `etymology_short` (1–2 sentences) from curated sources + LLM draft + manual edit
- [ ] Link to external refs: NLB BiblioAsia articles, Roots.gov.sg, Remember Singapore, Victor Savage & Brenda Yeoh’s work
- [ ] Publish canonical aliases and secondary tags in the dataset (data already produced earlier in the pipeline)

### 3.2 Personal layer (optional but encouraged)

- [ ] `data/personal/` gitignored or separate branch: `visited.yaml`, `runs.yaml`, `favorites.yaml`
- [ ] `memory_note` field — your own sentence per street (“Ran here during 2022 marathon training”)
- [ ] Merge personal fields at dataset build time without publishing to Kaggle

### 3.3 Notable streets sub-catalog

- [ ] `data/curated/notable.yaml` — hand-picked lists: longest names, funniest, most colonial, best for running, streets that no longer exist
- [ ] Generate `dataset/notable-streets.csv` for sharing

**Phase 3 done when:** Every street has district; ≥50% have a sourced etymology or explicit “unknown”; personal notes work locally.

---

## Phase 4 — Exploration: Browse, Map, Recall

**Goal:** Make the catalog **pleasant to use**, not only a CSV on Kaggle.

### 4.1 Static site (lowest friction) ✅

- [x] `site/` — Python generator (`scripts/build_site.py`) → `site/dist/`
- [x] **Map view** — Leaflet, polylines from dataset, category-colored
- [x] **List view** — filter by category, tag, search by substring (district filter ready when data exists)
- [x] **Street detail** — name, map snippet, aliases/tags; etymology / memory note / district when present
- [x] Deploy to GitHub Pages — `make site` / `make site-deploy`; workflow `.github/workflows/pages.yml`

Local: `make site-serve`. After push to `main`, site is at https://evgeniyarbatov.github.io/singapore-streets/

### 4.2 “Memory lane” features

- [ ] **Random street** — one click, one story (good for nostalgia)
- [ ] **Quiz mode** — “Colonial or nature?” using category labels
- [ ] **Compare eras** — streets with `old_name` vs current name
- [ ] **Running map** — overlay streets you’ve tagged `running-route`

### 4.3 Optional app ideas (later)

- Mobile-friendly PWA for use in Singapore
- “Streets near me” using geolocation
- Export to Anki flashcards for learning names before a trip home

**Phase 4 done when:** You can send a friend one URL and they can explore categories on a map without cloning the repo.

---

## Phase 5 — Pipeline Hardening & Community

**Goal:** Keep the project fresh with minimal pain.

### 5.1 Engineering

- [x] Single entrypoint: `make all` (also `make fresh` / `make fresh-all` for rebuilds)
- [ ] Package scripts as installable module (`src/singapore_streets/`) — reduces `runpy` / path hacks
- [ ] Golden-file test: small checked-in OSM snippet → expected `street-names.txt`
- [ ] CI (GitHub Actions): `make test` on every push
- [x] Local quality gates: pre-commit + ruff + mypy (`--strict`)
- [x] Dependency management via **uv** (`pyproject.toml` + `uv.lock`; Makefile uses `uv run`)
- [ ] Pin OSM download date in dataset metadata; changelog in `CHANGELOG.md`
- [ ] Structured logging instead of stderr prints for review queues

### 5.2 Data publishing

- [ ] Semantic versioning for dataset (`2026.06.1`)
- [ ] Kaggle release notes auto-generated from stats + changelog
- [ ] Consider Open Data release on GitHub Releases (CSV + GeoJSON)

### 5.3 Community & contributions

- [ ] `CONTRIBUTING.md` — how to propose taxonomy changes or etymology corrections
- [ ] Issue templates: “Missing street”, “Wrong category”, “Etymology source”
- [ ] Acknowledge URA/SLA/OSM licenses clearly

**Phase 5 done when:** A fresh clone + `make all` reproduces the published dataset; contributors can fix a category without touching Python (overrides already enable the latter).

---

## Suggested Order of Work

Highest joy per hour from here:

1. **Phase 1.1** — diff against official source (immediate “what are we missing?”)
2. **Phase 3.2** — personal memory notes (makes it *yours*; site already surfaces them)
3. **Phase 3.1** — district join + a first batch of etymologies (list filters + detail light up)
4. **Phase 4.2** — random street / quiz / running map on the existing site
5. **Phase 5** CI / packaging as friction shows up
6. Optional Phase 2 polish: inter-rater sample, clear remaining uncategorized via overrides

---

## Milestones

| Milestone | Target | Status | Celebration |
|-----------|--------|--------|-------------|
| **M1: Complete list** | ≤50 streets gap vs official | Open — needs Phase 1.1 | Print the count; compare to your son’s original question |
| **M2: Stable taxonomy** | &lt;20 primary categories, &gt;95% coverage | **Done** (12 categories, 99.8%) | Category pie chart poster |
| **M3: Story-ready** | 500 streets with etymology | Open | Pick 10 favorites for a “trip down memory lane” post |
| **M4: Explorable** | Public map site | **Done** (Phase 4.1) | Walk Singapore virtually before your next visit |
| **M5: Living catalog** | Quarterly OSM refresh automated | Open | New streets since last visit surfaced automatically |

---

## Open Questions

- **Scope:** Include expressways (`PIE`, `ECP`) and major bridges as named ways, or only traditional “streets”?
- **Historical streets:** Track renamed and extinct streets (e.g. from `old_name` OSM tags and NLB) as a separate `historical` table?
- **Languages:** Store Chinese/Malay/Tamil official forms even when English is primary for display?
- **Kaggle vs GitHub:** Is Kaggle still the primary publish target, or shift to GitHub Releases + static site?
- **Privacy:** Keep personal running/visited notes entirely local?

Capture decisions in `docs/decisions/` as you go (ADR-style, one paragraph each).

---

## References & Inspiration

- [URA — Singapore Street, Building and Place Names (PDF)](https://www.ura.gov.sg/Corporate/Resources/Publications/Books/Book-Details/Singapore-Street-Building-Place-Names)
- [NLB — History of street names in Singapore](https://www.nlb.gov.sg/main/article-detail?cmsuuid=4d8269aa-4464-40f5-8193-10b16a13eeea)
- [Roots.gov.sg — Street names in Singapore](https://www.roots.gov.sg/stories-landing/stories/street-names-in-singapore/story)
- [Remember Singapore — Street suffixes](https://remembersingapore.org/2018/08/15/singapore-street-suffixes/)
- [Wikipedia — Road names in Singapore](https://en.wikipedia.org/wiki/Road_names_in_Singapore)
- [OpenStreetMap Wiki — Singapore](https://wiki.openstreetmap.org/wiki/Singapore)
- Victor R. Savage & Brenda S. A. Yeoh, *Singapore Street Names: A Study of Toponymics* (ethnography-rich reference for Phase 3)

---

*This is a fun project. The roadmap is a compass, not a contract — pick the phases that pull you back to Singapore fastest.*
