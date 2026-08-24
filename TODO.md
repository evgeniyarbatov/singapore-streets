# TODO

Near-term picks from [ROADMAP.md](ROADMAP.md)'s "Suggested Order of Work"
(items 1-2, highest joy per hour):

- [ ] **Phase 1.1** — diff the ~4,926 OSM-derived streets against an official
  source (OneMap / data.gov.sg / URA PDF) to find what's missing.
- [ ] **Phase 3.2** — personal memory notes (`data/personal/visited.yaml` etc.)
  gitignored, merged at build time, not published to Kaggle.
- [ ] No CI workflow — `pages.yml` deploys the site but nothing runs
  `make test` on push, despite a full test suite existing for every script.
- [ ] Package `scripts/` as an installable module (Phase 5.1) — reduces the
  current `runpy`/path hacks between scripts.
