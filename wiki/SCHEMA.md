# Wiki schema

Rules for the `/wiki` skill. The wiki is for learning Singapore street names and exploring the patterns among them; `index.md` is the page a reader opens first.

## Layout

| Path | What |
|---|---|
| `index.md` | start-here links, then every page grouped by type |
| `log.md` | append-only record of ingest, query and lint runs |
| `elements/<slug>.md` | one word used in names (Jalan, Bukit, Crescent): meaning, language, how it is used |
| `patterns/<slug>.md` | a pattern across streets: a series, a family, a themed estate, a naming era, renamings |
| `people/<slug>.md` | a person streets are named after |
| `categories/<id>.md` | one per primary category in `data/taxonomy.yaml`, `<id>` as the slug |
| `streets/<slug>.md` | a street with a sourced history: namesake, origin, renaming, or vanished place |

The page types are closed; only a human adds one by editing this table.

## Pages

- Slug is the kebab-case title (`bukit-timah-road`); the H1 is the title.
- Frontmatter holds `type` (the folder name) and `aliases` (other spellings, so Obsidian resolves them).
- Link with Obsidian wikilinks: `[[bukit-timah-road|Bukit Timah Road]]`. Link every element, pattern, person, category or street that has a page; leave names without a page as plain text.
- A street page exists only for a street with sourced history; never write a stub. A street without one appears only as a name on element, pattern and category pages.
- Each element, pattern, person and category page lists the streets it covers, linking those that have a page.

## Facts and sources

- Every count, list of streets and category share comes from `wiki-facts.json` (written by `make wiki-facts`); never count by reading names.
- Every claim about meaning, origin, namesake, date or renaming carries a footnote `[^n]` whose definition at the page bottom is a URL with its title. Prefer NLB Infopedia, the National Archives, Roots.gov.sg and URA; Wikipedia is acceptable when it cites one of these.
- A claim without a source is not written. Put a plausible but unsourced reading under an `## Open questions` heading.
- When two sources disagree, state both with their footnotes; do not pick one silently.

## Boundaries

Write only under `wiki/`. Never edit `data/`, `scripts/`, `site/`, or anything in the data dir.
